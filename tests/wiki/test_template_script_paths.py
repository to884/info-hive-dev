"""ひな形が wiki に書き出すコマンドの、スクリプトのパスの試験（wiki 0.9.1）。

`init_wiki.py` が書き出す `SCHEMA.md` と `graph/README.md` は、wiki を使う側のプロジェクトで読まれる。
そこでは、スキルのディレクトリから見た `scripts/...` も、プラグインから見た `skills/info-hive/scripts/...` も解決しない。
`${CLAUDE_PLUGIN_ROOT}` はプラグインのコマンドの中でだけ展開され、書き出したファイルの中では展開されない。
そこで、ひな形ではスクリプトを `"<skill-root>/scripts/..."` と書き、同じファイルの中で `<skill-root>` の意味を説明する。

この試験は次のことを確かめる。
- ひな形のどれにも、`<skill-root>/` の付かない `scripts/` がない。
- `<skill-root>` を使うひな形は、その意味（インストールしたスキルのディレクトリ）を説明している。
- `<skill-root>` をスキルのディレクトリに置き換えると、挙げたスクリプトがすべて実在する。
- コマンドの中のスクリプトのパスは、前後を `"` で囲んである（空白を含むパスでも分かれない）。
- 検索の例は `--wiki wiki/` で対象の wiki を指す。書き出した `SCHEMA.md` の `--no-embed` の例を、説明どおりに置き換えて
  プロジェクトのルートから実行すると、その wiki のページが見つかる（既定の名前と、別の名前で初期化した wiki の両方）。
- `--upgrade` の検出に使う見出しと行（`SCHEMA_SECTION_MARKERS`）は 0.9.0 と同じで、ひな形にすべてある。

スキルの `SKILL.md` と `references/*.md` のコマンドも、同じ書き方にそろえた（wiki 0.9.3）。こちらは文の中で
`scripts/wiki_pages.py` のようにスキルの中のファイルを指すことがあるので、`scripts/` の有無ではなくコマンドを調べる。
- `python`、`python3`、`uv run --script`、`uv sync --script` のあとのスクリプトは、どれも `"<skill-root>/scripts/<名前>.py"` で、
  そのスクリプトが実在する。JSON の `argv`（`"python3", "..."`）のスクリプトも `<skill-root>/scripts/` で始まる。
- `SKILL.md` の「スクリプトのパス」が最初のコマンドより前にあり、コマンドのある各リファレンスはそこを指している。
- `skills/info-hive/scripts/` と書くのは、プラグインのコマンドの書き方を説明する `SKILL.md` の 1 行だけである。

実行（標準ライブラリだけで動く）:
    python -X utf8 -m unittest tests/wiki/test_template_script_paths.py -v
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import shlex
import subprocess
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
# コマンド（`uv run --script` か `python` のあと）に置いた `<skill-root>` のパス。前後の `"` も拾う。
COMMAND_REF = re.compile(r"(?:uv run --script|python) (\"?)<skill-root>/scripts/[A-Za-z0-9_./-]+\.py(\"?)")
# 説明の文に必ず入れる語句。
DEFINITION = "`<skill-root>` は、インストールした info-hive スキルのディレクトリ"
# `SCHEMA.md` の、依存パッケージを使わない検索の例。
NO_EMBED_COMMAND = re.compile(r"`(python \"<skill-root>/scripts/wiki_search\.py\"[^`]*--no-embed)`")
# 0.9.0 の `SCHEMA_SECTION_MARKERS` の marker。この変更では変えない。
MARKERS_0_9_0 = [
    "## Claim destinations",
    "## Skill evolution",
    "## Optional graph metadata",
    "## Graph layer",
    "Graph lint + extract",
    "## Retrieval",
    "- Semantic backend: local FastEmbed + sqlite-vec",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def templates() -> list[Path]:
    return sorted(p for p in ASSETS.iterdir() if p.name.endswith(".template"))


SKILL_MD = SKILL / "SKILL.md"
REPO = ROOT / "info-hive-wiki"
REPO_ROOT_NOTE = "プラグインのリポジトリ（info-hive-wiki）のルートで実行する"
# 実行するコマンドのスクリプト。前後の `"` も拾う。
SKILL_COMMAND = re.compile(
    r"(?:python3?|uv (?:run|sync)(?: --?[\w-]+)* --script) +(\"?)([^\s\"`]+\.py)(\"?)"
)
JSON_ARGV = re.compile(r"\"python3?\",\s*\"([^\"]+\.py)\"")
POINTER = "書き方は `SKILL.md` の「スクリプトのパス」にある。"
SECTION = "## スクリプトのパス"


def skill_docs() -> list[Path]:
    return [SKILL_MD] + sorted((SKILL / "references").glob("*.md"))


class SkillDocsScriptPathTests(unittest.TestCase):
    """`SKILL.md` と `references/*.md` のコマンドを調べる。"""

    def test_commands_use_quoted_skill_root(self):
        for path in skill_docs():
            for number, line in enumerate(read(path).splitlines(), 1):
                for match in SKILL_COMMAND.finditer(line):
                    with self.subTest(file=path.name, line=number):
                        opening, script, closing = match.groups()
                        if script.startswith("eval/"):
                            # 評価のスクリプトはスキルではなくプラグインのリポジトリにあり、そのルートで実行する。
                            self.assertTrue((REPO / script).is_file(), script)
                            self.assertIn(REPO_ROOT_NOTE, read(path))
                            continue
                        self.assertEqual((opening, closing), ('"', '"'), line)
                        self.assertTrue(script.startswith("<skill-root>/scripts/"), line)
                        name = script.removeprefix("<skill-root>/scripts/")
                        self.assertTrue((SKILL / "scripts" / name).is_file(), name)

    def test_json_argv_uses_skill_root(self):
        found = []
        for path in skill_docs():
            for script in JSON_ARGV.findall(read(path)):
                found.append(script)
                with self.subTest(file=path.name, script=script):
                    self.assertTrue(script.startswith("<skill-root>/scripts/"))
                    self.assertTrue((SKILL / "scripts" / script.removeprefix("<skill-root>/scripts/")).is_file())
        self.assertTrue(found)

    def test_definition_and_pointers(self):
        text = read(SKILL_MD)
        self.assertIn(SECTION, text)
        first_command = min(m.start() for m in SKILL_COMMAND.finditer(text))
        self.assertLess(text.index(SECTION), first_command)
        for path in skill_docs()[1:]:
            text = read(path)
            if SKILL_COMMAND.search(text) or JSON_ARGV.search(text):
                with self.subTest(file=path.name):
                    self.assertIn(POINTER, text)

    def test_every_script_path_has_an_allowed_form(self):
        # コマンドの検出から外れる形（`python -B scripts/...`、`--script=scripts/...`、閉じ引用符のあとに続く文字、
        # JSON の `argv` の途中の引数）も捕まえるため、`scripts/<名前>.py` の出現をすべて調べる。
        # 許すのは、`"<skill-root>/scripts/<名前>.py"` と、文の中でファイルを指す `` `scripts/<名前>.py` `` だけである。
        allowed = re.compile(r"\"<skill-root>/scripts/[\w-]+\.py\"(?![\w.])|`scripts/[\w-]+\.py`")
        for path in skill_docs():
            for number, line in enumerate(read(path).splitlines(), 1):
                spans = [m.span() for m in allowed.finditer(line)]
                for match in re.finditer(r"scripts/[\w-]+\.py", line):
                    with self.subTest(file=path.name, line=number, at=match.start()):
                        self.assertTrue(any(a <= match.start() and match.end() <= b for a, b in spans), line)

    def test_runner_never_takes_a_bare_script_name(self):
        bare = re.compile(r"(?:python3?|uv (?:run|sync))\b[^`\n]*?(?<![/\w])([\w-]+\.py)")
        for path in skill_docs():
            for number, line in enumerate(read(path).splitlines(), 1):
                # `/` のあとの名前（`"<skill-root>/scripts/x.py"` や `eval/decisions/run_eval.py`）は名前だけではない。
                for match in bare.finditer(line):
                    with self.subTest(file=path.name, line=number):
                        self.fail(f"スクリプトの名前だけを実行している: {line}")

    def test_definition_body(self):
        text = read(SKILL_MD)
        body = text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        for phrase in (
            '`"<skill-root>/scripts/<名前>.py"`',
            "`<skill-root>` は、このスキルのディレクトリ（この `SKILL.md` のあるディレクトリ）の実際のパスに置き換える",
            "スキルのベースディレクトリ",
            "`\"` で囲む",
            "`commands/*.md`",
            "スキルのディレクトリから見たパスである",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)

    def test_plugin_relative_path_only_in_definition(self):
        for path in skill_docs():
            for number, line in enumerate(read(path).splitlines(), 1):
                if "skills/info-hive/scripts/" in line:
                    with self.subTest(file=path.name, line=number):
                        self.assertEqual(path, SKILL_MD)
                        self.assertIn("`commands/*.md`", line)


class TemplateScriptPathTests(unittest.TestCase):
    """`assets/` のひな形そのものを調べる。"""

    def test_no_bare_scripts_path(self):
        for path in templates():
            with self.subTest(template=path.name):
                for number, line in enumerate(read(path).splitlines(), 1):
                    self.assertIsNone(BARE_SCRIPTS.search(line), f"{path.name}:{number}: {line}")

    def test_placeholder_is_defined(self):
        users = [p for p in templates() if PLACEHOLDER in read(p)]
        self.assertEqual(
            sorted(p.name for p in users),
            ["SCHEMA.md.template", "graph_README.md.template"],
        )
        for path in users:
            with self.subTest(template=path.name):
                self.assertIn(DEFINITION, read(path))
                self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/info-hive", read(path))

    def test_referenced_scripts_exist(self):
        for path in templates():
            for name in SCRIPT_REF.findall(read(path)):
                with self.subTest(template=path.name, script=name):
                    self.assertTrue((SKILL / "scripts" / name).is_file())

    def test_command_paths_are_quoted(self):
        for path in templates():
            if PLACEHOLDER not in read(path):
                continue
            with self.subTest(template=path.name):
                quotes = COMMAND_REF.findall(read(path))
                self.assertTrue(quotes)
                self.assertEqual(quotes, [('"', '"')] * len(quotes))

    def test_search_examples_name_the_wiki(self):
        text = read(ASSETS / "SCHEMA.md.template")
        examples = re.findall(r"`([^`]*<skill-root>/scripts/wiki_search\.py[^`]*)`", text)
        self.assertEqual(len(examples), 2)
        for example in examples:
            with self.subTest(example=example):
                self.assertIn(" --wiki wiki/ ", example)

    def test_upgrade_markers_unchanged(self):
        self.assertEqual([m["marker"] for m in init_wiki.SCHEMA_SECTION_MARKERS], MARKERS_0_9_0)
        self.assertEqual(init_wiki.detect_schema_gaps(ASSETS / "SCHEMA.md.template"), [])


class WrittenWikiTests(unittest.TestCase):
    """`init_wiki` で書き出したファイルを調べる。実行環境のセットアップ（uv）は呼ばない。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)

    def init(self, wiki_dir: str) -> Path:
        root = Path(self.temp.name) / f"project-{wiki_dir}"
        root.mkdir()
        with mock.patch.object(init_wiki, "install_runtime"), contextlib.redirect_stdout(io.StringIO()):
            init_wiki.init_wiki(root, wiki_dir, "raw")
        page = root / wiki_dir / "concepts/消費税.md"
        page.write_text(
            "---\ntitle: 消費税\ntype: concept\ncreated: 2026-11-09\nupdated: 2026-11-09\n---\n\n# 消費税\n\n消費税の説明。\n",
            encoding="utf-8",
        )
        return root

    def test_written_files(self):
        wiki = self.init("wiki") / "wiki"
        for rel in ("SCHEMA.md", "graph/README.md"):
            with self.subTest(file=rel):
                text = read(wiki / rel)
                self.assertIsNone(BARE_SCRIPTS.search(text))
                self.assertIn(DEFINITION, text)
                quotes = COMMAND_REF.findall(text)
                self.assertTrue(quotes)
                self.assertEqual(quotes, [('"', '"')] * len(quotes))
                for name in SCRIPT_REF.findall(text):
                    self.assertTrue((SKILL / "scripts" / name).is_file(), name)

    def run_no_embed_example(self, wiki_dir: str) -> subprocess.CompletedProcess:
        """書き出した SCHEMA.md の `--no-embed` の例を、説明どおりに置き換えて、プロジェクトのルートから実行する。"""
        root = self.init(wiki_dir)
        match = NO_EMBED_COMMAND.search(read(root / wiki_dir / "SCHEMA.md"))
        self.assertIsNotNone(match)
        command = match.group(1).replace(PLACEHOLDER, SKILL.as_posix())
        if wiki_dir != "wiki":
            command = command.replace("--wiki wiki/", f"--wiki {wiki_dir}/")
        argv = shlex.split(command)
        self.assertEqual(argv[0], "python")
        argv[0] = sys.executable
        argv[argv.index("query")] = "消費税"
        argv.append("--json")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        # 既定の `wiki/` だけがあるときに、別の名前の wiki ではなくそちらを読まないことも確かめる。
        if wiki_dir != "wiki":
            (root / "wiki").mkdir()
        return subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)

    def test_no_embed_example_runs_default_name(self):
        result = self.run_no_embed_example("wiki")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("concepts/消費税", result.stdout)

    def test_no_embed_example_runs_other_name(self):
        result = self.run_no_embed_example("kb")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("concepts/消費税", result.stdout)


if __name__ == "__main__":
    unittest.main()
