"""ひな形が wiki に書き出すコマンドの、スクリプトのパスの試験（wiki 0.9.1）。

`init_wiki.py` が書き出す `SCHEMA.md` と `graph/README.md` は、wiki を使う側のプロジェクトで読まれる。
そこでは、スキルのディレクトリから見た `scripts/...` も、プラグインから見た `skills/info-hive/scripts/...` も解決しない。
`${CLAUDE_PLUGIN_ROOT}` はプラグインのコマンドの中でだけ展開され、書き出したファイルの中では展開されない。
そこで、ひな形ではスクリプトを `<skill-root>/scripts/...` と書き、同じファイルの中で `<skill-root>` の意味を説明する。

この試験は次のことを確かめる。
- ひな形のどれにも、`<skill-root>/` の付かない `scripts/` がない。
- `<skill-root>` を使うひな形は、その意味（インストールしたスキルのディレクトリ）を説明している。
- `<skill-root>` をスキルのディレクトリに置き換えると、挙げたスクリプトがすべて実在する。
- コマンドの中のスクリプトのパスは `"` で囲んである（空白を含むパスでも分かれない）。
- `init_wiki` で書き出した `SCHEMA.md` と `graph/README.md` も、同じ条件を満たす。
- 本文だけを変え、`--upgrade` の検出に使う見出しは変えていない。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_template_script_paths.py -v
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "info-hive-wiki/skills/info-hive"
ASSETS = SKILL / "assets"
sys.path.insert(0, str(SKILL / "scripts"))

import init_wiki  # noqa: E402

PLACEHOLDER = "<skill-root>"
# `<skill-root>/` が前にない `scripts/`。`skills/info-hive/scripts/` もこれに当たる。
BARE_SCRIPTS = re.compile(r"(?<!<skill-root>/)scripts/")
SCRIPT_REF = re.compile(r"<skill-root>/scripts/([A-Za-z0-9_./-]+\.py)")
# コマンド（`uv run --script` か `python` のあと）に置いた `<skill-root>`。パスに空白があっても分かれないよう、`"` で囲む。
COMMAND_REF = re.compile(r"(?:uv run --script|python) (\"?)<skill-root>/")
# 説明の文に必ず入れる語句。
DEFINITION = "`<skill-root>` は、インストールした info-hive スキルのディレクトリ"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TemplateScriptPathTests(unittest.TestCase):
    """`assets/` のひな形そのものを調べる。"""

    def templates(self):
        return sorted(p for p in ASSETS.iterdir() if p.name.endswith(".template"))

    def test_no_bare_scripts_path(self):
        for path in self.templates():
            with self.subTest(template=path.name):
                for number, line in enumerate(read(path).splitlines(), 1):
                    self.assertIsNone(BARE_SCRIPTS.search(line), f"{path.name}:{number}: {line}")

    def test_placeholder_is_defined(self):
        users = [p for p in self.templates() if PLACEHOLDER in read(p)]
        self.assertEqual(
            sorted(p.name for p in users),
            ["SCHEMA.md.template", "graph_README.md.template"],
        )
        for path in users:
            with self.subTest(template=path.name):
                self.assertIn(DEFINITION, read(path))
                self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/info-hive", read(path))

    def test_referenced_scripts_exist(self):
        for path in self.templates():
            for name in SCRIPT_REF.findall(read(path)):
                with self.subTest(template=path.name, script=name):
                    self.assertTrue((SKILL / "scripts" / name).is_file())

    def test_command_paths_are_quoted(self):
        for path in self.templates():
            quotes = COMMAND_REF.findall(read(path))
            if PLACEHOLDER in read(path):
                with self.subTest(template=path.name):
                    self.assertTrue(quotes)
                    self.assertEqual(quotes, ['"'] * len(quotes))

    def test_upgrade_markers_unchanged(self):
        self.assertEqual(init_wiki.detect_schema_gaps(ASSETS / "SCHEMA.md.template"), [])


class WrittenWikiTests(unittest.TestCase):
    """`init_wiki` で書き出したファイルを調べる。実行環境のセットアップ（uv）は呼ばない。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name) / "project"
        root.mkdir()
        with mock.patch.object(init_wiki, "install_runtime"), contextlib.redirect_stdout(io.StringIO()):
            init_wiki.init_wiki(root, "wiki", "raw")
        self.wiki = root / "wiki"

    def test_written_files(self):
        for rel in ("SCHEMA.md", "graph/README.md"):
            with self.subTest(file=rel):
                text = read(self.wiki / rel)
                self.assertIsNone(BARE_SCRIPTS.search(text))
                self.assertIn(DEFINITION, text)
                names = SCRIPT_REF.findall(text)
                self.assertTrue(names)
                for name in names:
                    self.assertTrue((SKILL / "scripts" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
