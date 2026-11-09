"""別のディレクトリに同じスラッグのページがあるときの、グラフの抽出の試験（wiki 0.9.2）。

`a/Foo.md` と `b/Foo.md` のように、別のディレクトリに同じスラッグのページがあると、0.9.1 までの
`wiki_graph_extract.py` は、スラッグからノードを引いていたので、次のことが起きた。

- 前者の `graph.relationships` の主語が、後者のノードになる（別の `graph.node_id` を付けても防げない）。
- パスを付けた `[[a/Foo]]` まで、後者のノードを指す。
- 2 つのノードが同じスラッグを持つので、`graph.sqlite` の `nodes.slug` の UNIQUE に反し、抽出が止まる。

確かめること:
- 主語は、そのページ自身のノードになる。
- パスを付けたリンクは、そのページのノードを指す。パスのないリンクと `sources:` は、同じスラッグの
  ページが複数あれば、どれにも寄せない（エッジを作らない）。スラッグが 1 つなら今までどおり。
- `a/Foo` から `[[b/Foo]]` へのリンクは、自分へのリンクとして捨てずにエッジにする。
- 既定の node_id でも型が違えば（`concept:Foo` と `product:Foo`）、CLI の抽出が sqlite まで書き終える。
- グラフの lint の `orphan_typed_nodes` が、関係を書いたページを孤立と誤らない。
- MCP のツール `graph` が使う `wiki_graph_query.run_query` が、正しい主語の関係を返す。

実行（PyYAML 6.0.3 が要る）:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_duplicate_slugs.py -v
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

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
    import wiki_graph_lint as graph_lint
    import wiki_graph_query as graph_query

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

RELATION = """\
  relationships:
    - predicate: depends_on
      object: concept:other
      evidence: "前者は other に依存する"
      source: src
      confidence: high
      status: current
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(textwrap.dedent(text).lstrip().encode("utf-8"))


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class DuplicateSlugGraphTest(unittest.TestCase):
    def setUp(self):
        self.wiki = Path(tempfile.mkdtemp(prefix="graph-dup-slug-"))
        self.addCleanup(shutil.rmtree, self.wiki, ignore_errors=True)
        (self.wiki / "graph").mkdir()
        shutil.copyfile(TEMPLATE, self.wiki / "graph" / "ontology.yaml")
        self.ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        write(self.wiki / "concepts" / "other.md", """
            ---
            type: concept
            title: other
            ---
            [[Foo]] と [[a/Foo]] を参照する。
        """)
        write(self.wiki / "sources" / "src.md", """
            ---
            type: source
            title: src
            ---
            前者は other に依存する。
        """)

    def add_pair(self, first_meta: str, second_meta: str, first_body: str = "本文", second_body: str = "本文"):
        write(self.wiki / "a" / "Foo.md", f"---\n{first_meta}---\n{first_body}\n")
        write(self.wiki / "b" / "Foo.md", f"---\n{second_meta}---\n{second_body}\n")

    def add_repro_pair(self, first_body: str = "本文"):
        # 前者だけに関係を書き、2 つに別の node_id を付ける。
        self.add_pair(
            "type: concept\ngraph:\n  node_id: concept:first\n" + RELATION,
            "type: concept\ngraph:\n  node_id: concept:second\n",
            first_body=first_body,
        )

    def build(self):
        pages = extract.collect_pages(self.wiki)
        nodes, page_node_ids, _aliases = extract.build_nodes(pages, self.ontology)
        edges = extract.build_edges(pages, page_node_ids)
        return nodes, {(e["subject"], e["predicate"], e["object"]) for e in edges}, edges

    def run_extract(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "wiki_graph_extract.py"), str(self.wiki)],
            capture_output=True, text=True, encoding="utf-8", env=ENV,
        )

    def test_relationship_subject_is_the_declaring_page(self):
        self.add_repro_pair()
        _nodes, triples, edges = self.build()
        self.assertIn(("concept:first", "depends_on", "concept:other"), triples)
        self.assertNotIn(("concept:second", "depends_on", "concept:other"), triples)
        typed = [e for e in edges if e["predicate"] == "depends_on"]
        self.assertEqual([(e["subject"], e["page"]) for e in typed], [("concept:first", "a/Foo.md")])

    def test_path_link_points_to_that_page_and_bare_link_to_neither(self):
        self.add_repro_pair()
        _nodes, triples, _edges = self.build()
        mentions = {o for s, p, o in triples if s == "concept:other" and p == "mentions"}
        # [[a/Foo]] は前者だけを指し、[[Foo]] はどちらにも寄せない。
        self.assertEqual(mentions, {"concept:first"})

    def test_bare_link_alone_points_to_neither(self):
        # パスを付けたリンクと同居させると、パスのないリンクを先頭のページに寄せても結果に隠れるので、単独で確かめる。
        self.add_repro_pair()
        write(self.wiki / "concepts" / "bare.md", "---\ntype: concept\ntitle: bare\n---\n[[Foo]] だけを書く。\n")
        _nodes, triples, _edges = self.build()
        self.assertEqual({o for s, p, o in triples if s == "concept:bare" and p == "mentions"}, set())

    def test_link_to_page_without_its_own_node_makes_no_edge(self):
        # 型も既定の node_id も同じ 2 つのページは、後者がノードにならない。[[b/Foo]] を前者のノードに寄せない。
        self.add_pair("type: concept\n", "type: concept\n", first_body="[[b/Foo]] を見る。")
        write(self.wiki / "concepts" / "user.md", "---\ntype: concept\ntitle: user\n---\n[[b/Foo]] を見る。\n")
        nodes, triples, _edges = self.build()
        self.assertEqual([n["path"] for n in nodes if n["id"] == "concept:Foo"], ["a/Foo.md"])
        mentions = {(s, o) for s, p, o in triples if p == "mentions" and s in ("concept:Foo", "concept:user")}
        self.assertEqual(mentions, set())
        # 前者そのものへのパスのリンク（concepts/other.md の [[a/Foo]]）は、今までどおりエッジになる。
        self.assertIn(("concept:other", "mentions", "concept:Foo"), triples)

    def test_link_between_same_slug_pages_is_not_a_self_link(self):
        self.add_repro_pair(first_body="[[b/Foo]] と [[Foo]] を見る。")
        _nodes, triples, _edges = self.build()
        self.assertIn(("concept:first", "mentions", "concept:second"), triples)
        self.assertNotIn(("concept:first", "mentions", "concept:first"), triples)

    def test_unique_slug_still_resolves_bare_links_and_sources(self):
        write(self.wiki / "concepts" / "user.md", """
            ---
            type: concept
            title: user
            sources: [src]
            ---
            [[other]] を使う。
        """)
        _nodes, triples, _edges = self.build()
        self.assertIn(("concept:user", "mentions", "concept:other"), triples)
        self.assertIn(("concept:user", "sourced_from", "source:src"), triples)

    def test_sources_with_duplicate_slug_points_to_neither(self):
        write(self.wiki / "sources" / "dup.md", "---\ntype: source\ntitle: dup\n---\n本文\n")
        write(self.wiki / "more" / "dup.md", "---\ntype: source\ntitle: dup2\ngraph:\n  node_id: source:dup2\n---\n本文\n")
        write(self.wiki / "concepts" / "user.md", "---\ntype: concept\ntitle: user\nsources: [dup, src]\n---\n本文\n")
        _nodes, triples, _edges = self.build()
        sourced = {o for s, p, o in triples if s == "concept:user" and p == "sourced_from"}
        self.assertEqual(sourced, {"source:src"})

    def test_default_ids_of_different_types_extract_to_sqlite(self):
        # 型が違えば、既定の node_id でも 2 つのノードになり、同じスラッグを持つ。
        self.add_pair("type: concept\n", "type: entity\nkind: product\n")
        proc = self.run_extract()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        conn = sqlite3.connect(self.wiki / "graph" / "graph.sqlite")
        try:
            rows = conn.execute("SELECT id, path FROM nodes WHERE slug = 'Foo' ORDER BY id").fetchall()
        finally:
            conn.close()
        self.assertEqual(rows, [("concept:Foo", "a/Foo.md"), ("product:Foo", "b/Foo.md")])

    def test_graph_lint_orphans_follow_the_declaring_page(self):
        self.add_repro_pair()
        findings = graph_lint.lint(graph_lint.collect_pages(self.wiki), self.ontology)
        orphans = {f["node_id"] for f in findings["orphan_typed_nodes"]}
        self.assertNotIn("concept:first", orphans)
        self.assertIn("concept:second", orphans)

    def test_query_used_by_mcp_graph_returns_the_right_subject(self):
        self.add_repro_pair()
        proc = self.run_extract()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        first = graph_query.run_query(self.wiki, "edges", subject="concept:first", predicate="depends_on")
        second = graph_query.run_query(self.wiki, "edges", subject="concept:second", predicate="depends_on")
        self.assertEqual([(e["object"], e["page"]) for e in first["edges"]], [("concept:other", "a/Foo.md")])
        self.assertEqual(second["edges"], [])
        facts = graph_query.run_query(self.wiki, "facts", about="concept:other")
        inbound = {(e["subject"], e["predicate"]) for e in facts["inbound"]}
        self.assertEqual(inbound, {("concept:first", "depends_on")})
        json.dumps(facts, default=str, ensure_ascii=False)  # MCP は JSON にして返す


if __name__ == "__main__":
    unittest.main()
