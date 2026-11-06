"""作業領域の設定を読む部分（ADR-0008「共通の部分」）の一致テスト。

wiki、log、rag の各プラグインは、同じ規則の読み込み部分をそれぞれ持つ。食い違いを防ぐため、
`cases.json` の同じ入力に対して、見つかった実装がすべて同じ結果を返すことを確かめる。
今あるのは wiki の `wiki_workspace.py` だけである。log と rag に置いたら IMPLEMENTATIONS に足す。

各実装は、次の名前を公開する。
    WorkspaceError, find_workspace(start), default_wiki_dir(start), user_workspace_root(environ),
    expand_template(template, values), format_seq(n), dump_config(config),
    update_section(config, plugin, section)
find_workspace の戻り値は root、kind、warnings、dir(role) を持つ。

実行（標準ライブラリだけで動く）:
    python -m unittest discover -s tests/workspace -v
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((Path(__file__).with_name("cases.json")).read_text(encoding="utf-8"))

IMPLEMENTATIONS = {
    "wiki": ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts" / "wiki_workspace.py",
    # "log": ROOT / "info-hive-log" / "scripts" / "log_workspace.py",
    # "rag": ROOT / "info-hive-rag" / "scripts" / "rag_workspace.py",
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


if __name__ == "__main__":
    unittest.main()
