"""作業領域の設定を読む部分（ADR-0008「共通の部分」）の一致テスト。

wiki、log、rag の各プラグインは、同じ規則の読み込み部分をそれぞれ持つ。食い違いを防ぐため、
`cases.json` の同じ入力に対して、見つかった実装がすべて同じ結果を返すことを確かめる。
今あるのは wiki の `wiki_workspace.py` だけである。log と rag に置いたら IMPLEMENTATIONS に足す。

各実装は、次の名前を公開する。
    WorkspaceError, find_workspace(start), default_wiki_dir(start), user_workspace_root(environ),
    expand_template(template, values), format_seq(n), dump_config(config),
    update_section(config, plugin, section)
find_workspace の戻り値は root、kind、warnings、dir(role) を持つ。

`cases.json` の cli は wiki だけの試験で、wiki のスクリプト（wiki_lint.py、wiki_search.py）が wiki を
省いたときに作業領域の設定の dirs.wiki を使うことを、スクリプトを子プロセスで動かして確かめる。
MCP のサーバーがサーバーの中で呼ぶ関数（lint、collect_pages など）は、設定を読まないことも確かめる。

実行（標準ライブラリだけで動く）:
    python -m unittest discover -s tests/workspace -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((Path(__file__).with_name("cases.json")).read_text(encoding="utf-8"))

IMPLEMENTATIONS = {
    "wiki": ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts" / "wiki_workspace.py",
    # "log": ROOT / "info-hive-log" / "scripts" / "log_workspace.py",
    # "rag": ROOT / "info-hive-rag" / "scripts" / "rag_workspace.py",
}


WIKI_SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
# wiki を省けるスクリプトと、引数の組み立て方。wiki が None なら省く。
CLI_SCRIPTS = {
    "wiki_lint.py": lambda wiki: [*([wiki] if wiki else []), "--json"],
    "wiki_search.py": lambda wiki: ["目印", "--json", "--no-embed", *(["--wiki", wiki] if wiki else [])],
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(f"workspace_impl_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass がモジュールを引けるように先に登録する
    spec.loader.exec_module(module)
    return module


def available():
    return {name: load(name, path) for name, path in IMPLEMENTATIONS.items() if path.is_file()}


def write_files(base: Path, files: dict) -> None:
    for rel, content in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, dict) and set(content) == {"$hex"}:
            target.write_bytes(bytes.fromhex(content["$hex"]))  # UTF-8 でないバイト列を置く
            continue
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
        target.write_bytes(text.encode("utf-8"))


def rel(base: Path, path) -> "str | None":
    if path is None:
        return None
    path = Path(path)
    if not path.is_absolute():
        return path.as_posix()
    relative = os.path.relpath(path.resolve(), base.resolve())
    return Path(relative).as_posix()


def observe(module, case: dict) -> dict:
    """1 つの実装に 1 つの入力を与え、比べられる形の結果を返す。"""
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        write_files(base, case["files"])
        start = base / case["start"]
        start.mkdir(parents=True, exist_ok=True)
        try:
            workspace = module.find_workspace(start)
            wiki = module.default_wiki_dir(start)
        except module.WorkspaceError:
            return {"error": True}
        if workspace is None:
            return {"found": False, "wiki": rel(base, wiki)}
        return {
            "found": True,
            "root": rel(base, workspace.root),
            "kind": workspace.kind,
            "wiki": rel(base, wiki),
            "raw": rel(base, workspace.dir("raw")),
            "adr": rel(base, workspace.dir("adr")),
            "rag": rel(base, workspace.dir("rag")),
            "warnings": len(workspace.warnings),
        }


class ConformanceTests(unittest.TestCase):
    def setUp(self):
        self.impls = available()
        self.assertIn("wiki", self.impls, "wiki の実装が見つからない。サブモジュールを初期化したか確かめる")

    def test_find_matches_expectations(self):
        for name, module in self.impls.items():
            for case in CASES["find"]:
                with self.subTest(impl=name, case=case["name"]):
                    got = observe(module, case)
                    expected = case["expect"]
                    self.assertEqual({k: got.get(k) for k in expected}, expected)

    def test_all_implementations_agree(self):
        if len(self.impls) < 2:
            self.skipTest("実装が 1 つしかない（log と rag にはまだない）")
        for case in CASES["find"]:
            results = {name: observe(module, case) for name, module in self.impls.items()}
            with self.subTest(case=case["name"]):
                self.assertEqual(len({json.dumps(r, sort_keys=True) for r in results.values()}), 1, results)

    def test_user_workspace_root(self):
        for name, module in self.impls.items():
            for case in CASES["user_home"]:
                with self.subTest(impl=name, case=case["name"]):
                    expected = Path(os.path.expanduser(case["expect"]))
                    self.assertEqual(module.user_workspace_root(case["env"]), expected)

    def test_templates(self):
        for name, module in self.impls.items():
            for case in CASES["templates"]:
                with self.subTest(impl=name, template=case["template"]):
                    if case.get("error"):
                        with self.assertRaises(module.WorkspaceError):
                            module.expand_template(case["template"], case["values"])
                    else:
                        self.assertEqual(module.expand_template(case["template"], case["values"]), case["expect"])

    def test_seq(self):
        for name, module in self.impls.items():
            for case in CASES["seq"]:
                with self.subTest(impl=name, n=case["n"]):
                    self.assertEqual(module.format_seq(case["n"]), case["expect"])

    def test_dump_keeps_order_and_unknown_keys(self):
        for name, module in self.impls.items():
            for case in CASES["dump"]:
                with self.subTest(impl=name, case=case["name"]):
                    updated = module.update_section(case["config"], case["update"]["plugin"], case["update"]["section"])
                    self.assertEqual(module.dump_config(updated), case["expect"])
                    self.assertNotIn("\r", module.dump_config(updated))
                    self.assertNotIn("browse", json.dumps(case["config"]), "元の設定を書き換えてはならない")


class WikiCliDefaultTests(unittest.TestCase):
    """wiki_lint.py と wiki_search.py が wiki を省いたときの既定（ADR-0008）。"""

    def run_script(self, script: str, case: dict) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            write_files(base, case["files"])
            cwd = base / case["cwd"]
            cwd.mkdir(parents=True, exist_ok=True)
            out = subprocess.run([sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / script),
                                  *CLI_SCRIPTS[script](case["wiki"])],
                                 cwd=cwd, capture_output=True, timeout=120, env={**os.environ, "PYTHONUTF8": "1"})
            return out.returncode, out.stdout.decode("utf-8"), out.stderr.decode("utf-8")

    def test_default_wiki(self):
        for script in CLI_SCRIPTS:
            for case in CASES["cli"]["cases"]:
                with self.subTest(script=script, case=case["name"]):
                    code, stdout, stderr = self.run_script(script, case)
                    expect = case["expect"]
                    self.assertEqual(code, expect["exit"], stderr)
                    if "stderr" in expect:
                        self.assertIn(expect["stderr"], stderr)
                    if expect["exit"] == 0:
                        self.assertIn("target-page", stdout)
                        self.assertNotIn("decoy-page", stdout)
                    else:
                        self.assertEqual(stdout, "")

    def test_search_cache_goes_under_resolved_wiki(self):
        """値を省いた --cache は、設定から決めた wiki の下に置き、2 回目はそれを使う。"""
        files = {
            ".info-hive/workspace.json": {"version": 1, "kind": "user", "dirs": {"wiki": "知識/wiki"}},
            "知識/wiki/SCHEMA.md": "# スキーマ\n",
            "知識/wiki/target-page.md": "# 目印\n\n目印の本文。\n",
            "src/wiki/SCHEMA.md": "# スキーマ\n",
            "src/wiki/decoy-page.md": "# 目印\n\n目印の本文。\n",
        }
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            write_files(base, files)
            command = [sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / "wiki_search.py"), "目印", "--json",
                       "--no-embed", "--cache"]
            outputs = []
            for _ in range(2):
                out = subprocess.run(command, cwd=base / "src", capture_output=True, timeout=120,
                                     env={**os.environ, "PYTHONUTF8": "1"})
                self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8"))
                outputs.append(json.loads(out.stdout.decode("utf-8"))["results"])
            cache = base / "知識" / "wiki" / ".wiki-cache" / "search-index.json"
            self.assertTrue(cache.is_file())
            self.assertIn("target-page.md", cache.read_text(encoding="utf-8"))
            self.assertFalse((base / "src" / "wiki" / ".wiki-cache").exists())
            self.assertFalse((base / "wiki" / ".wiki-cache").exists())
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual([row["slug"] for row in outputs[1]], ["target-page"])

    def test_help_does_not_read_workspace(self):
        case = {"files": {".info-hive/workspace.json": "{"}, "cwd": ".", "wiki": None}
        for script in CLI_SCRIPTS:
            with self.subTest(script=script):
                with tempfile.TemporaryDirectory() as temp:
                    base = Path(temp)
                    write_files(base, case["files"])
                    out = subprocess.run([sys.executable, "-X", "utf8", str(WIKI_SCRIPTS / script), "--help"],
                                         cwd=base, capture_output=True, timeout=120,
                                         env={**os.environ, "PYTHONUTF8": "1"})
                self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8"))
                self.assertIn("作業領域の設定の dirs.wiki", out.stdout.decode("utf-8"))

    def test_functions_used_by_mcp_server_do_not_read_workspace(self):
        """サーバーは wiki を引数で受け取り、lint や collect_pages を同じプロセスで呼ぶ。設定を読んではならない。

        import の時点で読む退行も見つけるため、壊れた設定の下で設定の探索を拒むようにしてから import し直す。
        """
        def refuse(*_args, **_kwargs):
            raise AssertionError("作業領域の設定を読みに行った")

        previous = Path.cwd()
        sys.path.insert(0, str(WIKI_SCRIPTS))
        saved = {name: sys.modules.pop(name, None) for name in ("wiki_lint", "wiki_search")}
        try:
            import wiki_workspace
            with tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                write_files(base, {".info-hive/workspace.json": "{", "wiki/target-page.md": "# 目印\n\n目印の本文。\n"})
                wiki = base / "wiki"
                os.chdir(wiki)
                try:
                    with mock.patch.object(wiki_workspace, "find_workspace", refuse):
                        wiki_lint = importlib.import_module("wiki_lint")
                        wiki_search = importlib.import_module("wiki_search")
                        self.assertIs(wiki_lint.wiki_workspace, wiki_workspace)
                        self.assertIs(wiki_search.wiki_workspace, wiki_workspace)
                        findings = wiki_lint.lint(wiki_lint.collect_pages(wiki), 100, 200,
                                                  list(wiki_lint.DEFAULT_REQUIRED_FM), False, 5)
                        pages = wiki_search.collect_pages(wiki)
                        sections = wiki_search.collect_sections(pages)
                finally:
                    os.chdir(previous)
        finally:
            sys.path.remove(str(WIKI_SCRIPTS))
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
        self.assertEqual(findings["summary"]["total_pages"], 1)
        self.assertEqual([page["slug"] for page in pages], ["target-page"])
        self.assertTrue(sections)


if __name__ == "__main__":
    unittest.main()
