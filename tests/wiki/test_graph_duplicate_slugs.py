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
        # CLI は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページに数えない。
        (self.wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
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

    def test_link_to_page_sharing_a_node_points_to_that_node(self):
        # 型も既定の node_id も同じ 2 つのページは、ノードを 1 つ共有する（ノードの題名とパスは前者のもの）。
        # [[b/Foo]] はページを 1 つに決めるので、そのページのノード（共有のノード）を指す。
        self.add_pair("type: concept\n", "type: concept\n", first_body="[[b/Foo]] を見る。")
        write(self.wiki / "concepts" / "user.md", "---\ntype: concept\ntitle: user\n---\n[[b/Foo]] を見る。\n")
        nodes, triples, _edges = self.build()
        self.assertEqual([n["path"] for n in nodes if n["id"] == "concept:Foo"], ["a/Foo.md"])
        self.assertIn(("concept:user", "mentions", "concept:Foo"), triples)
        # 同じノードの 2 つのページのあいだのリンクは、自分へのリンクになるので作らない。
        self.assertNotIn(("concept:Foo", "mentions", "concept:Foo"), triples)

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


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class GraphContractTest(unittest.TestCase):
    """browse の関係表がグラフの抽出に求める契約（info-hive-dev の docs/plans/wiki-browse-stage1-2026-11-09.md の 3）。"""

    def setUp(self):
        self.wiki = Path(tempfile.mkdtemp(prefix="graph-contract-"))
        self.addCleanup(shutil.rmtree, self.wiki, ignore_errors=True)
        (self.wiki / "graph").mkdir()
        shutil.copyfile(TEMPLATE, self.wiki / "graph" / "ontology.yaml")
        # CLI は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページに数えない。
        (self.wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
        self.ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        write(self.wiki / "concepts" / "y.md", "---\ntype: concept\ntitle: y\n---\n本文\n")
        write(self.wiki / "sources" / "paper.md", "---\ntype: source\ntitle: paper\n---\n本文\n")

    def relation_page(self, rel_path: str, extra: str = "", obj: str = "concept:y") -> None:
        write(self.wiki / rel_path, (
            "---\ntype: concept\n" + extra + "graph:\n  relationships:\n"
            f"    - predicate: depends_on\n      object: {obj}\n"
            '      evidence: "y を使う"\n      source: paper\n---\n本文\n'))

    def build(self):
        diagnostics: list = []
        pages = extract.collect_pages(self.wiki)
        nodes, page_node_ids, _aliases = extract.build_nodes(pages, self.ontology, diagnostics)
        edges = extract.build_edges(pages, page_node_ids, diagnostics)
        return nodes, edges, diagnostics

    def lint(self):
        return graph_lint.lint(graph_lint.collect_pages(self.wiki), self.ontology)

    def run_extract(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "wiki_graph_extract.py"), str(self.wiki)],
            capture_output=True, text=True, encoding="utf-8", env=ENV,
        )

    def typed(self, edges):
        return sorted((e["subject"], e["object"], e["page"]) for e in edges if e["predicate"] == "depends_on")

    # 契約の 2: ページの違う同じ内容の関係を 1 本にまとめない。

    def test_same_relation_on_two_pages_stays_two_edges(self):
        # どちらも type: concept なので、既定の node_id はどちらも concept:x になり、主語も同じになる。
        self.relation_page("concepts/x.md")
        self.relation_page("entities/x.md")
        _nodes, edges, _diag = self.build()
        self.assertEqual(self.typed(edges), [("concept:x", "concept:y", "concepts/x.md"),
                                             ("concept:x", "concept:y", "entities/x.md")])
        self.assertEqual(len({e["id"] for e in edges if e["predicate"] == "depends_on"}), 2)

    def test_same_node_id_on_two_slugs_keeps_both_pages_relations(self):
        # 別のスラッグのページに同じ graph.node_id を付けても、後のページの関係を捨てない。
        for rel in ("concepts/one.md", "concepts/two.md"):
            write(self.wiki / rel, (
                "---\ntype: concept\ngraph:\n  node_id: concept:shared\n  relationships:\n"
                "    - predicate: depends_on\n      object: concept:y\n"
                '      evidence: "y を使う"\n      source: paper\n---\n本文\n'))
        nodes, edges, diagnostics = self.build()
        self.assertEqual([n["path"] for n in nodes if n["id"] == "concept:shared"], ["concepts/one.md"])
        self.assertEqual(self.typed(edges), [("concept:shared", "concept:y", "concepts/one.md"),
                                             ("concept:shared", "concept:y", "concepts/two.md")])
        self.assertIn({"kind": "duplicate_node_id", "node_id": "concept:shared",
                       "pages": ["concepts/one.md", "concepts/two.md"]}, diagnostics)
        dup = self.lint()["duplicate_node_ids"]
        self.assertEqual([(f["node_id"], f["paths"]) for f in dup],
                         [("concept:shared", ["concepts/one.md", "concepts/two.md"])])

    def test_relation_to_shared_node_id_is_ambiguous(self):
        # 契約の 5: 同じ node_id のページが複数あれば、その ID を目的語にした関係はエッジにしない。
        for rel in ("concepts/one.md", "concepts/two.md"):
            write(self.wiki / rel, "---\ntype: concept\ngraph:\n  node_id: concept:shared\n---\n本文\n")
        self.relation_page("concepts/user.md", obj="concept:shared")
        self.relation_page("concepts/plain.md", obj="concept:missing")
        _nodes, edges, diagnostics = self.build()
        # ノードのない目的語は、今までどおり文字列の目的語のエッジになる（lint の broken_object_refs が挙げる）。
        self.assertEqual(self.typed(edges), [("concept:plain", "concept:missing", "concepts/plain.md")])
        ambiguous = [d for d in diagnostics if d["kind"] == "ambiguous_object"]
        self.assertEqual(ambiguous, [{"kind": "ambiguous_object", "page": "concepts/user.md", "index": 0,
                                      "predicate": "depends_on", "object": "concept:shared",
                                      "pages": ["concepts/one.md", "concepts/two.md"]}])
        found = self.lint()["ambiguous_object_refs"]
        self.assertEqual([(f["page"], f["object"]) for f in found], [("concepts/user.md", "concept:shared")])

    # 契約の 4 と 6: sources: をページに解決し、1 つなら必ず sourced_from を作る。

    def sourced(self, edges, page):
        return sorted(e["object"] for e in edges if e["predicate"] == "sourced_from" and e["page"] == page)

    def test_path_sources_make_sourced_from(self):
        write(self.wiki / "concepts" / "a.md", '---\ntype: concept\nsources: ["sources/paper"]\n---\n本文\n')
        write(self.wiki / "concepts" / "b.md", '---\ntype: concept\nsources: ["[[sources/paper]]"]\n---\n本文\n')
        write(self.wiki / "concepts" / "c.md", "---\ntype: concept\nsources: paper\n---\n本文\n")
        _nodes, edges, diagnostics = self.build()
        for page in ("concepts/a.md", "concepts/b.md", "concepts/c.md"):
            self.assertEqual(self.sourced(edges, page), ["source:paper"], page)
        self.assertEqual(diagnostics, [])

    def test_ambiguous_and_unresolved_sources_make_no_edge_and_are_reported(self):
        write(self.wiki / "sources" / "left" / "doc.md", "---\ntype: source\n---\n本文\n")
        write(self.wiki / "sources" / "right" / "doc.md", "---\ntype: source\ngraph:\n  node_id: source:doc-right\n---\n本文\n")
        write(self.wiki / "concepts" / "a.md",
              '---\ntype: concept\nsources: [doc, "sources/left/doc", nothing]\n---\n本文\n')
        _nodes, edges, diagnostics = self.build()
        # パスを付けた値は、同じスラッグのページがあっても 1 つに決まる。
        self.assertEqual(self.sourced(edges, "concepts/a.md"), ["source:doc"])
        self.assertEqual(diagnostics, [
            {"kind": "ambiguous_source", "page": "concepts/a.md", "source": "doc",
             "pages": ["sources/left/doc.md", "sources/right/doc.md"]},
            {"kind": "unresolved_source", "page": "concepts/a.md", "source": "nothing", "pages": []},
        ])
        findings = self.lint()
        self.assertEqual([f["source"] for f in findings["ambiguous_sources"]], ["doc"])
        self.assertEqual([f["source"] for f in findings["unresolved_sources"]], ["nothing"])

    # 生成物と MCP のツール graph。

    def test_outputs_and_query_keep_both_pages(self):
        for rel in ("concepts/one.md", "concepts/two.md"):
            write(self.wiki / rel, (
                "---\ntype: concept\ngraph:\n  node_id: concept:shared\n  relationships:\n"
                "    - predicate: depends_on\n      object: concept:y\n"
                '      evidence: "y を使う"\n      source: paper\n---\n本文\n'))
        proc = self.run_extract()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("同じ node_id のページ 1 件", proc.stderr)
        rows = [json.loads(line) for line in
                (self.wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(sorted(r["page"] for r in rows if r["predicate"] == "depends_on"),
                         ["concepts/one.md", "concepts/two.md"])
        graphml = (self.wiki / "graph" / "graph.graphml").read_text(encoding="utf-8")
        self.assertEqual(graphml.count('<data key="d_predicate">depends_on</data>'), 2)
        for page in ("concepts/one.md", "concepts/two.md"):
            self.assertIn(f'<data key="d_page">{page}</data>', graphml)
        result = graph_query.run_query(self.wiki, "edges", subject="concept:shared", predicate="depends_on")
        self.assertEqual(sorted(e["page"] for e in result["edges"]), ["concepts/one.md", "concepts/two.md"])
        neighbors = graph_query.run_query(self.wiki, "neighbors", node="concept:shared")
        slot = next(n for n in neighbors["neighbors"] if n["node_id"] == "concept:y")
        self.assertEqual(sorted(e["page"] for e in slot["out"]), ["concepts/one.md", "concepts/two.md"])
        path = graph_query.run_query(self.wiki, "path", start="concept:shared", goal="concept:y")
        self.assertEqual(path["path_nodes"], ["concept:shared", "concept:y"])
        self.assertEqual(len(path["path_edges"]), 1)  # 最短経路は、平行なエッジのうち 1 本を通る

    def test_same_name_in_nfc_and_nfd_keeps_both_relations(self):
        nfc_name, nfd_name = "ガ", "ガ"  # 「ガ」の NFC と NFD
        for name in (nfc_name, nfd_name):
            self.relation_page(f"concepts/{name}.md")
        if len(list((self.wiki / "concepts").glob("*.md"))) < 3:
            self.skipTest("このファイルシステムは NFC と NFD の名前を同じファイルとみなす")
        nodes, edges, diagnostics = self.build()
        typed = [e for e in edges if e["predicate"] == "depends_on"]
        # 出力の page はどちらも NFC のパスだが、関係は 2 本とも残る。
        self.assertEqual(len(typed), 2)
        self.assertEqual({e["page"] for e in typed}, {f"concepts/{nfc_name}.md"})
        self.assertEqual(len({e["id"] for e in typed}), 2)
        dup = [d for d in diagnostics if d["kind"] == "duplicate_node_id"]
        self.assertEqual(len(dup), 1)
        self.assertEqual(len(set(dup[0]["pages"])), 2)  # ディスク上のパスで、2 つのファイルを区別する

    def test_source_page_sources_are_reported_but_make_no_edge(self):
        write(self.wiki / "sources" / "left" / "doc.md", "---\ntype: source\n---\n本文\n")
        write(self.wiki / "sources" / "right" / "doc.md",
              "---\ntype: source\ngraph:\n  node_id: source:doc-right\n---\n本文\n")
        write(self.wiki / "sources" / "other.md", "---\ntype: source\nsources: [paper, missing, doc]\n---\n本文\n")
        _nodes, edges, diagnostics = self.build()
        self.assertEqual(self.sourced(edges, "sources/other.md"), [])
        self.assertEqual([(d["kind"], d["source"]) for d in diagnostics],
                         [("unresolved_source", "missing"), ("ambiguous_source", "doc")])
        findings = self.lint()
        self.assertEqual([f["source"] for f in findings["unresolved_sources"]], ["missing"])
        self.assertEqual([f["source"] for f in findings["ambiguous_sources"]], ["doc"])

    # 関係の項目 1 つから、必ず 1 本のエッジができる。

    def items_page(self, items: list[str]) -> None:
        body = "".join(
            f"    - predicate: depends_on\n      object: concept:y\n      evidence: \"y を使う\"\n"
            f"      source: paper\n{extra}" for extra in items)
        write(self.wiki / "concepts" / "x.md", "---\ntype: concept\ngraph:\n  relationships:\n" + body + "---\n本文\n")

    def test_each_relationship_item_is_its_own_edge(self):
        self.items_page(["      status: current\n", "      status: historical\n      valid_to: 2020-01-01\n",
                         "      status: current\n"])
        _nodes, edges, _diag = self.build()
        typed = [e for e in edges if e["predicate"] == "depends_on"]
        # status だけが違う 2 件も、まったく同じ 2 件も、まとめない。
        self.assertEqual(sorted(e["status"] for e in typed), ["current", "current", "historical"])
        self.assertEqual(len({e["id"] for e in typed}), 3)

    def test_edge_ids_do_not_depend_on_item_order(self):
        first, second = "      status: current\n", "      status: historical\n"
        self.items_page([first, second])
        before = {e["status"]: e["id"] for e in self.build()[1] if e["predicate"] == "depends_on"}
        self.items_page([second, first])
        after = {e["status"]: e["id"] for e in self.build()[1] if e["predicate"] == "depends_on"}
        self.assertEqual(before, after)

    def test_edge_ids_do_not_depend_on_order_of_different_items(self):
        a = "    - predicate: depends_on\n      object: concept:y\n      status: current\n"
        b = "    - predicate: works_on\n      object: concept:y\n      status: current\n"
        c = "    - predicate: depends_on\n      object: concept:y\n      status: current\n"
        ids = []
        for order in ([a, b, c], [b, c, a]):
            write(self.wiki / "concepts" / "x.md",
                  "---\ntype: concept\ngraph:\n  relationships:\n" + "".join(order) + "---\n本文\n")
            typed = [e for e in self.build()[1] if e["page"] == "concepts/x.md" and e["predicate"] != "mentions"]
            # 項目と ID の対応で比べる（同じ中身の a と c は、どちらがどちらでも区別できない）。
            ids.append({e["predicate"]: sorted(x["id"] for x in typed if x["predicate"] == e["predicate"])
                        for e in typed})
        self.assertEqual(sum(len(v) for v in ids[0].values()), 3)
        self.assertEqual(ids[0], ids[1])

    def test_omitted_and_empty_fields_stay_two_edges(self):
        a = "    - predicate: depends_on\n      object: concept:y\n      evidence: proof\n"
        b = a + '      source: ""\n'
        c = "    - predicate: depends_on\n      object: concept:y\n      source: paper\n"
        d = c + '      evidence: ""\n'
        write(self.wiki / "concepts" / "x.md",
              "---\ntype: concept\ngraph:\n  relationships:\n" + a + b + c + d + "---\n本文\n")
        _nodes, edges, _diag = self.build()
        self.assertEqual(len([e for e in edges if e["predicate"] == "depends_on"]), 4)

    def test_reordering_items_that_differ_only_in_node_references_keeps_ids(self):
        # contradicts にノード ID を書いた値は ID に入るので、それだけが違う項目を並べ替えても ID は移らない。
        base = "    - predicate: depends_on\n      object: concept:y\n      contradicts: {}\n"
        p_item, q_item = base.format("concept:p"), base.format("concept:q")
        maps = []
        for order in ([p_item, q_item], [q_item, p_item]):
            write(self.wiki / "concepts" / "x.md",
                  "---\ntype: concept\ngraph:\n  relationships:\n" + "".join(order) + "---\n本文\n")
            _nodes, edges, diagnostics = self.build()
            maps.append({e["extras"]["contradicts"]: e["id"] for e in edges if e["predicate"] == "depends_on"})
            self.assertEqual([d for d in diagnostics if d["kind"] == "order_dependent_edge_ids"], [])
        self.assertEqual(len(maps[0]), 2)
        self.assertEqual(maps[0], maps[1])

    def test_items_that_differ_only_in_edge_id_references_are_reported(self):
        # エッジの ID を書いた参照だけが違う項目は、番号で分かれ、並べ替えると ID が移りうる。黙らずに挙げる。
        base = "    - predicate: depends_on\n      object: concept:y\n      contradicts: {}\n"
        items = base.format("0123456789abcdef01234567") + base.format("76543210fedcba9876543210")
        write(self.wiki / "concepts" / "x.md", "---\ntype: concept\ngraph:\n  relationships:\n" + items + "---\n本文\n")
        _nodes, edges, diagnostics = self.build()
        self.assertEqual(len([e for e in edges if e["predicate"] == "depends_on"]), 2)
        self.assertIn({"kind": "order_dependent_edge_ids", "page": "concepts/x.md", "indexes": [0, 1]}, diagnostics)
        found = self.lint()["order_dependent_edge_ids"]
        self.assertEqual(found, [{"page": "concepts/x.md", "indexes": [0, 1]}])
        # まったく同じ 2 件は、どちらがどちらでも区別できないので挙げない。
        write(self.wiki / "concepts" / "x.md",
              "---\ntype: concept\ngraph:\n  relationships:\n" + base.format("concept:p") * 2 + "---\n本文\n")
        self.assertEqual([d for d in self.build()[2] if d["kind"] == "order_dependent_edge_ids"], [])

    def test_mixed_key_notes_are_written_by_the_cli(self):
        write(self.wiki / "concepts" / "x.md", (
            "---\ntype: concept\ngraph:\n  relationships:\n"
            "    - predicate: depends_on\n      object: concept:y\n"
            "      notes:\n        2: two\n        label: three\n        \"3\": text\n        3: number\n"
            "        true: yes\n        null: none\n---\n本文\n"))
        proc = self.run_extract()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(line) for line in
                (self.wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
        notes = [r["extras"]["notes"] for r in rows if r["predicate"] == "depends_on"]
        # キーは JSON と同じ規則でそろえ、文字列のキーとぶつかる数値のキーには型の名前を付けて、値を消さない。
        self.assertEqual(notes, [{"2": "two", "label": "three", "3": "text", "3#int": "number",
                                  "true": True, "null": "none"}])

    def test_contradicts_between_edges_keeps_their_ids(self):
        # contradicts にエッジの ID を書いても、自分の ID は変わらない。互いを指す 2 件の参照が成り立つ。
        def rel_page(name: str, ref: str | None) -> None:
            extra = f"      contradicts: {ref}\n" if ref else ""
            write(self.wiki / "concepts" / f"{name}.md", (
                "---\ntype: concept\ngraph:\n  relationships:\n"
                f"    - predicate: depends_on\n      object: concept:y\n      status: disputed\n{extra}---\n本文\n"))

        def typed_ids() -> dict:
            return {e["page"]: e["id"] for e in self.build()[1] if e["predicate"] == "depends_on"}

        rel_page("a", None)
        rel_page("b", None)
        before = typed_ids()
        rel_page("a", before["concepts/b.md"])
        rel_page("b", before["concepts/a.md"])
        _nodes, edges, _diag = self.build()
        after = {e["page"]: e for e in edges if e["predicate"] == "depends_on"}
        self.assertEqual({k: e["id"] for k, e in after.items()}, before)
        self.assertEqual(after["concepts/a.md"]["extras"]["contradicts"], after["concepts/b.md"]["id"])
        self.assertEqual(after["concepts/b.md"]["extras"]["contradicts"], after["concepts/a.md"]["id"])

    def test_nested_extension_fields_do_not_stop_extraction(self):
        write(self.wiki / "concepts" / "x.md", (
            "---\ntype: concept\ngraph:\n  relationships:\n"
            "    - predicate: depends_on\n      object: concept:y\n      extension:\n        1: one\n        label: two\n"
            "      notes:\n        2: two\n        label: three\n---\n本文\n"))
        _nodes, edges, _diag = self.build()
        self.assertEqual(self.typed(edges), [("concept:x", "concept:y", "concepts/x.md")])

    # sources: の分け方は、lint の unresolved_sources と同じ関数による。

    def test_sources_classification_matches_wiki_lint(self):
        import wiki_lint
        import wiki_pages
        write(self.wiki / "sources" / "dup.md", "---\ntype: source\n---\n本文\n")
        write(self.wiki / "concepts" / "dup.md", "---\ntype: concept\n---\n本文\n")
        write(self.wiki / "concepts" / "plain.md", "---\ntype: concept\n---\n本文\n")
        values = ["paper", "sources/paper", "[[sources/paper]]", "[[paper]]", "missing", "[[missing]]",
                  "sources/missing", "plain", "concepts/plain", "[[concepts/plain]]", "dup", "concepts/dup",
                  "sources/dup", " paper "]
        quoted = ", ".join(json.dumps(v, ensure_ascii=False) for v in values)
        write(self.wiki / "concepts" / "user.md", f"---\ntype: concept\nsources: [{quoted}]\n---\n本文\n")
        lint_pages = wiki_lint.collect_pages(self.wiki)
        findings = wiki_lint.lint(lint_pages, 100, 200, [], False, 5)
        flagged = {(f["source"], f["reason"]) for f in findings["unresolved_sources"] if f["path"] == "concepts/user.md"}
        by_path, by_slug = wiki_pages.build_page_index(lint_pages)
        classified = set()
        for ref in wiki_pages.ref_values(values):
            status, _found, _t = wiki_pages.classify_source_ref(ref, by_path, by_slug, lambda q: q["meta"].get("type"))
            if status != "ok":
                classified.add((ref, status))
        self.assertEqual(flagged, classified)
        self.assertEqual(flagged, {("missing", "missing"), ("[[missing]]", "missing"), ("sources/missing", "missing"),
                                   ("plain", "not_source"), ("concepts/plain", "not_source"),
                                   ("[[concepts/plain]]", "not_source"), ("concepts/dup", "not_source")})
        # グラフの抽出の unresolved_source は、lint の missing と同じ値になる。
        _nodes, edges, diagnostics = self.build()
        unresolved = {d["source"] for d in diagnostics if d["kind"] == "unresolved_source"}
        self.assertEqual(unresolved, {ref for ref, status in flagged if status == "missing"})
        self.assertEqual({d["source"] for d in diagnostics if d["kind"] == "ambiguous_source"}, {"dup"})
        # 1 つのページに解決する値からは、source でないページでも sourced_from ができる（lint が挙げる）。
        # " paper " は前後の空白を除くと "paper" と同じ値なので、同じエッジになる。
        self.assertEqual(sorted(e["source"] for e in edges if e["predicate"] == "sourced_from"),
                         sorted(["paper", "sources/paper", "[[sources/paper]]", "[[paper]]", "plain",
                                 "concepts/plain", "[[concepts/plain]]", "concepts/dup", "sources/dup"]))

    def test_numeric_object_matches_numeric_node_id_in_lint(self):
        write(self.wiki / "concepts" / "one.md", "---\ntype: concept\ngraph:\n  node_id: 1\n---\n本文\n")
        self.relation_page("concepts/user.md", obj="1")
        _nodes, edges, _diag = self.build()
        self.assertEqual(self.typed(edges), [("concept:user", "1", "concepts/user.md")])
        self.assertEqual(self.lint()["broken_object_refs"], [])


if __name__ == "__main__":
    unittest.main()
