"""グラフの lint が、contradicts と supersedes に書いたエッジの ID を参照先として認めることの試験（wiki 0.9.3）。

手順書（references/graph-workflow.md）とひな形（assets/SCHEMA.md.template）は、`contradicts` と `supersedes` に
エッジの ID を書いてよいとしている。0.9.2 で、エッジの ID の参照は自分の ID の計算に入れないことにし、2 つの関係が
互いのエッジの ID を書けるようにした。ところが 0.9.2 までの `wiki_graph_lint.py` は、参照をノード ID とソースの
スラッグとだけ照らしたので、実在するエッジの ID を書いても `broken_contradicts` と `broken_supersedes` に挙げた。

確かめること:
- 互いのエッジの ID を書いた 2 件の参照（前のページから後のページへの参照も含む）を挙げない。
- 16 進 24 桁の形でも、実在しないエッジの ID は今までどおり挙げる。
- 抽出が作る暗黙のエッジ（mentions など）の ID も認める。
- ノード ID とソースのスラッグの参照は今までどおり認め、どれにも当たらない値は挙げる。
- CLI の `wiki_graph_lint.py --json` でも同じになる。

実行（PyYAML 6.0.3 が要る）:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_lint_edge_refs.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
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

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
MISSING_EDGE_ID = "ffffffffffffffffffffffff"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class GraphLintEdgeRefsTest(unittest.TestCase):
    def setUp(self):
        self.wiki = Path(tempfile.mkdtemp(prefix="graph-lint-edge-refs-"))
        self.addCleanup(shutil.rmtree, self.wiki, ignore_errors=True)
        (self.wiki / "graph").mkdir()
        shutil.copyfile(TEMPLATE, self.wiki / "graph" / "ontology.yaml")
        # CLI は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページに数えない。
        (self.wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
        self.ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        write(self.wiki / "concepts" / "y.md", "---\ntype: concept\ntitle: y\n---\n本文\n")
        write(self.wiki / "sources" / "paper.md", "---\ntype: source\ntitle: paper\n---\ny を使う\n")

    def rel_page(self, name: str, **refs) -> None:
        # 値は引用符で囲む。数字だけのエッジの ID が、YAML で数として読まれないようにする。
        extra = "".join(f'      {k}: "{v}"\n' for k, v in refs.items())
        write(self.wiki / "concepts" / f"{name}.md", (
            "---\ntype: concept\ngraph:\n  relationships:\n"
            "    - predicate: depends_on\n      object: concept:y\n"
            '      evidence: "y を使う"\n      source: paper\n      status: disputed\n'
            f"{extra}---\n本文\n"))

    def edge_ids(self) -> dict:
        pages = extract.collect_pages(self.wiki)
        _nodes, page_node_ids, _aliases = extract.build_nodes(pages, self.ontology)
        return {e["page"]: e["id"] for e in extract.build_edges(pages, page_node_ids)
                if e["predicate"] == "depends_on"}

    def lint(self) -> dict:
        return graph_lint.lint(graph_lint.collect_pages(self.wiki), self.ontology)

    def broken(self, findings: dict) -> dict:
        return {field: sorted((f["page"], f[field]) for f in findings[f"broken_{field}"])
                for field in ("contradicts", "supersedes")}

    def mutual_pages(self) -> dict:
        self.rel_page("a")
        self.rel_page("b")
        ids = self.edge_ids()
        # a（先に読むページ）が b のエッジを、b が a のエッジを指す。
        self.rel_page("a", contradicts=ids["concepts/b.md"], supersedes=ids["concepts/b.md"])
        self.rel_page("b", contradicts=ids["concepts/a.md"], supersedes=ids["concepts/a.md"])
        # 参照を書き足しても、エッジの ID は変わらない（0.9.2 の契約）。
        self.assertEqual(self.edge_ids(), ids)
        return ids

    def test_mutual_edge_id_references_are_not_broken(self):
        self.mutual_pages()
        self.assertEqual(self.broken(self.lint()), {"contradicts": [], "supersedes": []})

    def test_missing_edge_id_is_still_broken(self):
        self.rel_page("a")
        self.assertNotIn(MISSING_EDGE_ID, self.edge_ids().values())
        self.rel_page("a", contradicts=MISSING_EDGE_ID, supersedes=MISSING_EDGE_ID)
        self.assertEqual(self.broken(self.lint()), {
            "contradicts": [("concepts/a.md", MISSING_EDGE_ID)],
            "supersedes": [("concepts/a.md", MISSING_EDGE_ID)],
        })

    def test_implicit_edge_ids_are_accepted(self):
        # 抽出が edges.jsonl に書くエッジなら、mentions のような暗黙のエッジの ID も参照先になる。
        write(self.wiki / "concepts" / "m.md", "---\ntype: concept\n---\n[[y]] を使う。\n")
        pages = extract.collect_pages(self.wiki)
        _nodes, page_node_ids, _aliases = extract.build_nodes(pages, self.ontology)
        mention = next(e["id"] for e in extract.build_edges(pages, page_node_ids)
                       if e["predicate"] == "mentions" and e["page"] == "concepts/m.md")
        self.rel_page("a", contradicts=mention)
        self.assertEqual(self.broken(self.lint()), {"contradicts": [], "supersedes": []})

    def test_node_ids_and_source_slugs_are_still_accepted(self):
        self.rel_page("a", contradicts="concept:y", supersedes="paper")
        self.rel_page("b", contradicts="concept:missing", supersedes="no-such-source")
        self.assertEqual(self.broken(self.lint()), {
            "contradicts": [("concepts/b.md", "concept:missing")],
            "supersedes": [("concepts/b.md", "no-such-source")],
        })

    def test_cli_json_accepts_edge_ids_and_flags_missing_ones(self):
        ids = self.mutual_pages()
        self.rel_page("c", contradicts=MISSING_EDGE_ID, supersedes=ids["concepts/a.md"])
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "wiki_graph_lint.py"), str(self.wiki), "--json"],
            capture_output=True, text=True, encoding="utf-8", env=ENV,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        findings = json.loads(proc.stdout)
        self.assertEqual(self.broken(findings), {
            "contradicts": [("concepts/c.md", MISSING_EDGE_ID)],
            "supersedes": [],
        })
        self.assertEqual(findings["summary"]["broken_contradicts"], 1)
        self.assertEqual(findings["summary"]["broken_supersedes"], 0)


if __name__ == "__main__":
    unittest.main()
