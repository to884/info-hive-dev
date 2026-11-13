"""同梱のスクリプトの Python の版の扱い（3.12 以上。ADR-0018、wiki 0.11.2）の試験。

- 標準ライブラリだけのスクリプトは、利用者の python で直接動く。wiki のモジュールを読み込む入口は、どれも最初に
  読み込まれる wiki_text.py で版を確かめ、今までの対象だった 3.10 と 3.11 では理由を書いて止まる。入口の一覧は、
  ファイルから機械的に作り（entry_scripts()）、本物の 3.10 と 3.11 で各入口を動かして確かめる。構文、読み込みの順、
  3.10 にない標準ライブラリのどれで先に止まっても、この試験で分かる。
  手元に 3.10 や 3.11 がなければ飛ばす。環境変数 WIKI_TEST_REQUIRE_OLD_PYTHON=1 のとき（CI）は、飛ばさずに失敗する。
- 古い版を真似て（sys.version_info を差し替えて）wiki_text.py を読み込むと止まり、3.12 では止まらないこと。
- uv で動くスクリプトの PEP 723 の宣言が、どれも 3.12 以上を求めること。

3.9 以前は対象にしない（3.6 以前では、wiki_text.py の `from __future__ import annotations` が構文の誤りになり、
版の確かめより先に止まる）。

実行（標準ライブラリだけで動く。古い版の Python は uv で探す）:
    python -X utf8 -B -m unittest tests/wiki/test_python_version.py -v
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
GUARD = "Python 3.12 以上が必要である"
OLD_VERSIONS = ("3.10", "3.11")
# PEP 723 の宣言があっても、文書が `python` で直接動かす入口（README の「語彙ベースの wiki_search.py --no-embed」）
DIRECT_WITH_HEADER = ("wiki_search.py",)


def has_header(source):
    return "# /// script" in source


def is_entry(tree):
    """最上位に `if __name__ == "__main__":` がある。"""
    return any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
               and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__" for node in tree.body)


def imports_wiki_at_load(tree):
    """読み込んだときに走る文（関数の本体の外）で、wiki のモジュールを読み込む。"""
    stack = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Import) and any(alias.name.startswith("wiki_") for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("wiki_"):
            return True
        stack.extend(ast.iter_child_nodes(node))
    return False


def entry_scripts():
    """(読み込んだときに版を確かめる入口, そうでない入口)。入口は、最上位に `__main__` の分岐を持つスクリプトのうち、
    PEP 723 の宣言がないもの（利用者の python で動く）と DIRECT_WITH_HEADER。uv で動くスクリプトは、uv が 3.12 以上を選ぶ。
    wiki のモジュールを読み込まない入口（wiki_workspace.py）と、関数の中で読み込む入口（wiki_evolve_claude.py は、
    標準入力の要求を読んでから読み込み、そこで止まる）は、`--help` では確かめに届かないので、この試験の外である。"""
    guarded, plain = [], []
    for path in sorted(SCRIPTS.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        if not is_entry(tree) or (has_header(source) and path.name not in DIRECT_WITH_HEADER):
            continue
        (guarded if imports_wiki_at_load(tree) else plain).append(path)
    return guarded, plain


def find_python(version):
    try:
        done = subprocess.run(["uv", "python", "find", "--no-project", version], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = done.stdout.strip()
    return path if done.returncode == 0 and path else None


class GuardTests(unittest.TestCase):
    def run_with_version(self, version):
        code = (f"import sys; sys.version_info = {version!r}; sys.path.insert(0, {str(SCRIPTS)!r}); "
                "import wiki_text; print('読み込めた')")
        return subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code], capture_output=True,
                              encoding="utf-8", errors="replace")

    def test_old_python_stops_with_a_reason(self):
        for version in ((3, 11, 9, "final", 0), (3, 10, 11, "final", 0)):
            with self.subTest(version=version[:2]):
                done = self.run_with_version(version)
                self.assertEqual(done.returncode, 1, done.stderr)
                self.assertIn(GUARD, done.stderr)
                self.assertNotIn("読み込めた", done.stdout)

    def test_supported_python_passes(self):
        done = self.run_with_version((3, 12, 0, "final", 0))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("読み込めた", done.stdout)


class OldPythonTests(unittest.TestCase):
    def test_entry_scripts_stop_on_old_python(self):
        """本物の 3.10 と 3.11 で、版を確かめる入口を `--help` つきで動かすと、どれも理由を書いて終了コード 1 で止まる。"""
        guarded, _ = entry_scripts()
        names = {path.name for path in guarded}
        # 一覧の作り方が壊れて、何も確かめなくなるのを防ぐ
        self.assertTrue({"wiki_lint.py", "wiki_stats.py", "wiki_search.py", "wiki_decide.py", "wiki_evolve.py"} <= names,
                        sorted(names))
        required = os.environ.get("WIKI_TEST_REQUIRE_OLD_PYTHON") == "1"
        for version in OLD_VERSIONS:
            python = find_python(version)
            if python is None:
                if required:
                    self.fail(f"Python {version} が見つからない（WIKI_TEST_REQUIRE_OLD_PYTHON=1）")
                continue
            with tempfile.TemporaryDirectory() as cwd:
                for path in guarded:
                    with self.subTest(version=version, script=path.name):
                        # 確かめが効かなかったときに wiki を書き換えないよう、空のディレクトリで --help をつけて動かす
                        done = subprocess.run([python, "-X", "utf8", "-B", str(path), "--help"], cwd=cwd,
                                              capture_output=True, encoding="utf-8", errors="replace", timeout=120)
                        self.assertEqual(done.returncode, 1, done.stderr[-2000:])
                        self.assertIn(GUARD, done.stderr)
                        self.assertNotIn("Traceback", done.stderr)
        if not required and all(find_python(v) is None for v in OLD_VERSIONS):
            self.skipTest("Python 3.10 と 3.11 が見つからない")


class SourceTests(unittest.TestCase):
    def test_pep723_headers_require_312(self):
        pattern = re.compile(r'^# requires-python = "(.+)"$', re.MULTILINE)
        found = {}
        for path in sorted(SCRIPTS.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            if not has_header(source):
                continue
            match = pattern.search(source)
            found[path.name] = match.group(1) if match else None
        self.assertGreaterEqual(len(found), 8)
        self.assertEqual({name: value for name, value in found.items() if value != ">=3.12"}, {})


if __name__ == "__main__":
    unittest.main()
