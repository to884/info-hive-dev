"""wiki のグラフ層（extract、lint、query）の回帰試験。ADR-0009 の「回帰テストを足す」にあたる。

確かめること:
- オントロジーがないときは、3 つの入口とも何も書き出さずに終了コード 1 で止まる。
- 本文の wikilink や `sources:` を変えただけでもグラフが変わる（extract を省けない）。
- graph.sqlite の作り直しが途中で止まっても、前の DB が壊れずに残る。
- 日本語のノード、NFC と NFD、独自のオントロジー、暗黙のエッジ、4 種類の問い合わせ。

実行（PyYAML 6.0.3 が要る）:
    uv run --with pyyaml==6.0.3 python -m unittest discover -s tests/graph -v
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
TEMPLATE = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "assets" / "ontology.yaml.template"
sys.path.insert(0, str(SCRIPTS))

try:
    import yaml  # noqa: F401
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

if HAS_YAML:
    import wiki_graph_extract as extract
import wiki_graph_common as common

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run(script, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", env=ENV, cwd=cwd,
    )


def page(path: Path, frontmatter: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "---\n" + textwrap.dedent(frontmatter).strip() + "\n---\n\n" + textwrap.dedent(body).strip() + "\n"
    path.write_bytes(text.encode("utf-8"))


def edge_set(wiki: Path) -> set[tuple[str, str, str]]:
    rows = (wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8").splitlines()
    return {(e["subject"], e["predicate"], e["object"]) for e in map(json.loads, rows)}


class WikiCase(unittest.TestCase):
    """日本語のページを持つ小さな wiki を一時ディレクトリに作る。"""

    with_ontology = True

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.wiki = Path(self.temp.name) / "wiki"
        self.wiki.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# 検証用\n", encoding="utf-8")
        page(self.wiki / "sources" / "山田太郎インタビュー.md", """
            type: source
            title: 山田太郎インタビュー
            raw: raw/山田太郎インタビュー.md
        """, "2015 年に、やまだ製作所を一人で立ち上げた。")
        page(self.wiki / "entities" / "山田太郎.md", """
            type: entity
            kind: person
            title: 山田太郎
            sources: [山田太郎インタビュー]
            graph:
              aliases: [山田, やまだたろう]
              relationships:
                - predicate: founded
                  object: organization:やまだ製作所
                  source: 山田太郎インタビュー
                  evidence: "2015 年に、やまだ製作所を一人で立ち上げた。"
                  confidence: high
                  status: current
        """, "[[やまだ製作所]] の創業者。")
        page(self.wiki / "entities" / "やまだ製作所.md", """
            type: entity
            kind: organization
            title: やまだ製作所
            sources: [山田太郎インタビュー]
        """, "町工場。")
        page(self.wiki / "concepts" / "消費税.md", """
            type: concept
            title: 消費税
        """, "税の一種。")
        if self.with_ontology:
            (self.wiki / "graph").mkdir()
            (self.wiki / "graph" / "ontology.yaml").write_bytes(TEMPLATE.read_bytes())

    def extract(self, *args):
        proc = run("wiki_graph_extract.py", self.wiki, *args)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc


class NoOntologyTests(WikiCase):
    """オントロジーがないときの扱いを 3 つの入口でそろえた（ADR-0009）。"""

    with_ontology = False

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_extract_stops_without_writing_anything(self):
        proc = run("wiki_graph_extract.py", self.wiki)
        self.assertEqual(proc.returncode, common.EXIT_GRAPH_DISABLED)
        self.assertEqual(proc.stdout, "")
        self.assertIn("オントロジーが見つからない", proc.stderr)
        self.assertFalse((self.wiki / "graph").exists(), "graph/ を作ってはならない")

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_extract_with_out_dir_also_stops(self):
        out = Path(self.temp.name) / "out"
        proc = run("wiki_graph_extract.py", self.wiki, "--out", out)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(out.exists())

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_lint_stops_with_same_code_and_message(self):
        lint = run("wiki_graph_lint.py", self.wiki)
        ext = run("wiki_graph_extract.py", self.wiki)
        self.assertEqual(lint.returncode, 1)
        self.assertEqual(lint.stdout, "")
        self.assertEqual(lint.stderr, ext.stderr)

    def test_query_ignores_stale_db_when_ontology_is_gone(self):
        # 以前に作った graph.sqlite が残っていても、オントロジーがなければ答えない。
        graph = self.wiki / "graph"
        graph.mkdir()
        sqlite3.connect(graph / "graph.sqlite").close()
        proc = run("wiki_graph_query.py", self.wiki, "facts", "--about", "concept:消費税")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("オントロジーが見つからない", proc.stderr)
        self.assertIn("何もしない", proc.stderr)

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_three_entry_points_share_one_message(self):
        messages = {
            run("wiki_graph_extract.py", self.wiki).stderr,
            run("wiki_graph_lint.py", self.wiki).stderr,
            run("wiki_graph_query.py", self.wiki, "neighbors", "--node", "x").stderr,
        }
        self.assertEqual(len(messages), 1, messages)

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_explicit_ontology_and_db_are_honoured(self):
        ontology = Path(self.temp.name) / "my-ontology.yaml"
        ontology.write_bytes(TEMPLATE.read_bytes())
        out = Path(self.temp.name) / "out"
        proc = run("wiki_graph_extract.py", self.wiki, "--ontology", ontology, "--out", out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.wiki / "graph").exists())
        lint = run("wiki_graph_lint.py", self.wiki, "--ontology", ontology, "--json")
        self.assertEqual(lint.returncode, 0, lint.stderr)
        query = run("wiki_graph_query.py", self.wiki, "--db", out / "graph.sqlite",
                    "facts", "--about", "concept:消費税")
        self.assertEqual(query.returncode, 0, query.stderr)
        missing = run("wiki_graph_lint.py", self.wiki, "--ontology", Path(self.temp.name) / "none.yaml")
        self.assertEqual(missing.returncode, 1)


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class BrokenOntologyTests(WikiCase):
    def test_unreadable_ontology_exits_2_in_extract_and_lint(self):
        (self.wiki / "graph" / "ontology.yaml").write_text("node_types: [\n", encoding="utf-8")
        for script in ("wiki_graph_extract.py", "wiki_graph_lint.py"):
            proc = run(script, self.wiki)
            self.assertEqual(proc.returncode, common.EXIT_BAD_ONTOLOGY, (script, proc.stderr))
            self.assertIn("オントロジーを読めない", proc.stderr)
        self.assertFalse((self.wiki / "graph" / "graph.sqlite").exists())

    def test_empty_sections_are_treated_as_empty(self):
        (self.wiki / "graph" / "ontology.yaml").write_text("node_types:\npredicates:\n", encoding="utf-8")
        self.extract()
        lint = run("wiki_graph_lint.py", self.wiki, "--json")
        self.assertEqual(lint.returncode, 0, lint.stderr)
        self.assertEqual(len(json.loads(lint.stdout)["unknown_predicates"]), 1)


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class ImplicitEdgeTests(WikiCase):
    """型付きの関係を足さない変更でも、グラフが変わる（extract を省く条件の修正）。"""

    def test_implicit_edges_are_extracted(self):
        self.extract()
        edges = edge_set(self.wiki)
        self.assertIn(("person:山田太郎", "founded", "organization:やまだ製作所"), edges)
        self.assertIn(("person:山田太郎", "mentions", "organization:やまだ製作所"), edges)
        self.assertIn(("person:山田太郎", "sourced_from", "source:山田太郎インタビュー"), edges)
        self.assertIn(("source:山田太郎インタビュー", "summarizes_raw", "raw:raw/山田太郎インタビュー.md"), edges)

    def test_body_wikilink_change_alone_changes_graph(self):
        self.extract()
        before = edge_set(self.wiki)
        page(self.wiki / "concepts" / "消費税.md", """
            type: concept
            title: 消費税
        """, "[[やまだ製作所]] も納める税。")
        self.extract()
        after = edge_set(self.wiki)
        self.assertEqual(after - before, {("concept:消費税", "mentions", "organization:やまだ製作所")})

    def test_sources_change_alone_changes_graph(self):
        self.extract()
        before = edge_set(self.wiki)
        page(self.wiki / "concepts" / "消費税.md", """
            type: concept
            title: 消費税
            sources: [山田太郎インタビュー]
        """, "税の一種。")
        self.extract()
        self.assertEqual(edge_set(self.wiki) - before,
                         {("concept:消費税", "sourced_from", "source:山田太郎インタビュー")})


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class JapaneseAndQueryTests(WikiCase):
    def test_nfd_file_name_and_link_resolve_to_nfc_node(self):
        nfd_name = unicodedata.normalize("NFD", "データベース")
        page(self.wiki / "concepts" / f"{nfd_name}.md", """
            type: concept
            title: データベース
        """, "[[消費税]] とは関係ない。")
        page(self.wiki / "concepts" / "検索.md", """
            type: concept
            title: 検索
        """, f"[[{nfd_name}]] を使う。")
        self.extract()
        edges = edge_set(self.wiki)
        self.assertIn(("concept:検索", "mentions", "concept:データベース"), edges)
        nfd_query = run("wiki_graph_query.py", self.wiki, "--json", "facts", "--about",
                        unicodedata.normalize("NFD", "concept:データベース"))
        self.assertEqual(nfd_query.returncode, 0, nfd_query.stderr)
        self.assertEqual(json.loads(nfd_query.stdout)["node"]["id"], "concept:データベース")

    def test_four_query_kinds(self):
        self.extract()
        def q(*args):
            proc = run("wiki_graph_query.py", self.wiki, "--json", *args)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)
        neighbors = q("neighbors", "--node", "organization:やまだ製作所")
        self.assertIn("person:山田太郎", [n["node_id"] for n in neighbors["neighbors"]])
        edges = q("edges", "--subject", "person:山田太郎", "--predicate", "founded")
        self.assertEqual([e["object"] for e in edges["edges"]], ["organization:やまだ製作所"])
        path = q("path", "--from", "person:山田太郎", "--to", "source:山田太郎インタビュー")
        self.assertEqual(path["path_nodes"], ["person:山田太郎", "source:山田太郎インタビュー"])
        facts = q("facts", "--about", "organization:やまだ製作所")
        self.assertIn(("person:山田太郎", "founded"),
                      {(e["subject"], e["predicate"]) for e in facts["inbound"]})

    def test_custom_ontology(self):
        (self.wiki / "graph" / "ontology.yaml").write_text(textwrap.dedent("""
            node_types:
              税目:
                maps_from: {type: concept}
              person:
                maps_from: {type: entity, kind: person}
              organization:
                maps_from: {type: entity, kind: organization}
              source:
                maps_from: {type: source}
            predicates:
              founded:
                subject_types: [person]
                object_types: [organization]
              課税する:
                subject_types: [税目]
                object_types: [organization]
                requires_evidence: false
        """), encoding="utf-8")
        page(self.wiki / "concepts" / "消費税.md", """
            type: concept
            title: 消費税
            graph:
              relationships:
                - predicate: 課税する
                  object: organization:やまだ製作所
                  confidence: medium
                  status: current
        """, "税の一種。")
        self.extract()
        self.assertIn(("税目:消費税", "課税する", "organization:やまだ製作所"), edge_set(self.wiki))
        lint = json.loads(run("wiki_graph_lint.py", self.wiki, "--json").stdout)
        self.assertEqual(lint["unknown_predicates"], [])
        self.assertEqual(lint["subject_type_mismatch"], [])
        self.assertEqual(lint["missing_evidence"], [])


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class InterruptedRebuildTests(WikiCase):
    """graph.sqlite の作り直しが途中で止まっても、前の DB が残る（ADR-0009）。"""

    def node_count(self):
        conn = sqlite3.connect(self.wiki / "graph" / "graph.sqlite")
        try:
            return conn.execute("SELECT count(*) FROM nodes").fetchone()[0]
        finally:
            conn.close()

    def temps(self):
        return sorted(p.name for p in (self.wiki / "graph").glob("*.tmp*"))

    def add_page(self):
        page(self.wiki / "concepts" / "所得税.md", """
            type: concept
            title: 所得税
        """, "[[消費税]] とは別の税。")

    def test_exception_during_build_keeps_previous_db(self):
        self.extract()
        before = self.node_count()
        self.add_page()

        def broken_build(db_path, nodes, aliases, edges):
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE nodes (id TEXT)")
            conn.commit()
            conn.close()
            raise KeyboardInterrupt("途中で止めた")

        pages = extract.collect_pages(self.wiki)
        ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        nodes, slug_to_id, aliases = extract.build_nodes(pages, ontology)
        edges = extract.build_edges(pages, slug_to_id)
        with patch.object(extract, "build_sqlite", broken_build):
            with self.assertRaises(KeyboardInterrupt):
                extract.write_sqlite(self.wiki / "graph", nodes, aliases, edges)
        self.assertEqual(self.node_count(), before)
        self.assertEqual(self.temps(), [])
        query = run("wiki_graph_query.py", self.wiki, "facts", "--about", "concept:消費税")
        self.assertEqual(query.returncode, 0, query.stderr)

    def test_killed_process_keeps_previous_db_and_next_run_cleans_up(self):
        self.extract()
        before = self.node_count()
        self.add_page()
        # 後始末の処理も動かないように、DB を作っている途中でプロセスごと止める。
        code = textwrap.dedent(f"""
            import os, sqlite3, sys
            sys.path.insert(0, {str(SCRIPTS)!r})
            import wiki_graph_extract as extract
            def killed(db_path, *args):
                conn = sqlite3.connect(db_path)
                conn.execute("CREATE TABLE nodes (id TEXT)")
                conn.commit()
                conn.close()
                os._exit(9)
            extract.build_sqlite = killed
            sys.argv = ["wiki_graph_extract.py", {str(self.wiki)!r}, "--formats", "sqlite"]
            extract.main()
        """)
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              encoding="utf-8", env=ENV)
        self.assertEqual(proc.returncode, 9, proc.stderr)
        self.assertEqual(self.node_count(), before)
        leftovers = list((self.wiki / "graph").glob("graph.sqlite.*.tmp"))
        self.assertEqual(len(leftovers), 1)
        # 古くなった一時ファイルは、次の extract が消す。
        old = time.time() - common.STALE_TEMP_SECONDS - 60
        os.utime(leftovers[0], (old, old))
        self.extract()
        self.assertEqual(self.node_count(), before + 1)
        self.assertEqual(self.temps(), [])

    def test_failed_replace_keeps_previous_db_and_removes_temp(self):
        self.extract()
        before = self.node_count()
        self.add_page()
        pages = extract.collect_pages(self.wiki)
        ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        nodes, slug_to_id, aliases = extract.build_nodes(pages, ontology)
        edges = extract.build_edges(pages, slug_to_id)
        with patch.object(common.os, "replace", side_effect=PermissionError("使用中")), \
                patch.object(common, "REPLACE_WAIT_SECONDS", 0):
            with self.assertRaises(PermissionError):
                extract.write_sqlite(self.wiki / "graph", nodes, aliases, edges)
        self.assertEqual(self.node_count(), before)
        self.assertEqual(self.temps(), [])

    def test_replace_retries_transient_permission_error(self):
        target = Path(self.temp.name) / "target.txt"
        target.write_text("before", encoding="utf-8")
        temp = common.temp_path_for(target)
        temp.write_text("after", encoding="utf-8")
        real = os.replace
        calls = []

        def flaky(src, dst):
            calls.append(src)
            if len(calls) < 3:
                raise PermissionError("使用中")
            return real(src, dst)

        with patch.object(common.os, "replace", flaky), patch.object(common, "REPLACE_WAIT_SECONDS", 0):
            common.replace_atomically(temp, target)
        self.assertEqual(target.read_text(encoding="utf-8"), "after")
        self.assertEqual(len(calls), 3)
        self.assertFalse(temp.exists())

    def test_rebuild_while_reader_holds_db_open(self):
        # Windows では開いているファイルを置き換えられないことがある。成功するか、
        # 失敗しても前の DB と一時ファイルの後始末が正しいかのどちらかであること。
        self.extract()
        before = self.node_count()
        self.add_page()
        reader = sqlite3.connect(self.wiki / "graph" / "graph.sqlite")
        try:
            reader.execute("SELECT count(*) FROM nodes").fetchone()
            proc = run("wiki_graph_extract.py", self.wiki)
        finally:
            reader.close()
        if proc.returncode == 0:
            self.assertEqual(self.node_count(), before + 1)
        else:
            self.assertEqual(self.node_count(), before)
        self.assertEqual([t for t in self.temps() if t.startswith("graph.sqlite")], [])
        # 読み手が閉じたあとなら、必ず作り直せる。
        self.extract()
        self.assertEqual(self.node_count(), before + 1)

    def test_gitignore_template_ignores_temp_files(self):
        template = (SCRIPTS.parent / "assets" / "graph_gitignore.template").read_text(encoding="utf-8")
        self.assertIn("*.tmp", template.splitlines())


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class WorkspaceDefaultTests(WikiCase):
    """`wiki_graph_lint.py` で `<wiki>` を省くと、作業領域の設定の dirs.wiki を使う（ADR-0008）。"""

    def test_lint_uses_dirs_wiki(self):
        workspace = Path(self.temp.name)
        (workspace / ".info-hive").mkdir()
        renamed = workspace / "知識"
        self.wiki.rename(renamed)
        (workspace / ".info-hive" / "workspace.json").write_text(json.dumps({
            "version": 1, "kind": "project", "id": "test", "dirs": {"wiki": "知識"},
        }, ensure_ascii=False), encoding="utf-8")
        sub = workspace / "code" / "sub"
        sub.mkdir(parents=True)
        (sub / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")  # サブモジュールで止まらない
        proc = run("wiki_graph_lint.py", "--json", cwd=sub)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["summary"]["pages_scanned"], 4)


if __name__ == "__main__":
    unittest.main()
