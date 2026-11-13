"""グラフの抽出が読む frontmatter の値を、wiki の lint と同じにする試験（wiki 0.9.5）。

0.9.3 までの `wiki_graph_extract.py` は、frontmatter の全体を PyYAML で読んでいた。wiki の lint は文字列の
パーサー（`wiki_text.parse_frontmatter_text`）で読むので、引用符のない `true`、数、日付、`null` が、2 つの
道具で違う値になった。`sources: [true]` は、lint では `true.md` に解決し、グラフでは未解決になった。

確かめること（設計は docs/plans/wiki-graph-frontmatter-values-2026-11-11.md）:
- 最上位の欄は、lint と同じ値になる。`graph` の欄だけを PyYAML から取る。
- `graph:` の中の、ページやノードを指す欄は、書かれた文字で読む。`null` は値なしのまま。
- `graph:` を読めなかったページは、診断 `unreadable_graph` に挙がる。PyYAML が値を組み立てられない欄
  （`created: 2026-13-01`）が `graph` の外にあっても、`graph` は読める。
- lint のパーサーが読めない書き方の `type`・`kind`・`sources`・`raw` は、診断 `unread_field` に挙がる。
  wiki 0.9.7 でパーサーが読む書き方を広げた（docs/plans/wiki-frontmatter-parser-2026-11-11.md）。字下げの違う
  配列、複数行の `[...]`、引用符つきのキー、コロンの前の空白は、lint もグラフも読み、診断は出ない。
- オントロジーの `maps_from` の `type`・`kind` も、書かれた文字で照らす。
- 引用符で囲む規約どおりのページでは、ノードもエッジも ID も変わらない。

実行（PyYAML 6.0.3 が要る）:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_frontmatter_values.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
SCRIPTS = PLUGIN / "skills" / "info-hive" / "scripts"
TEMPLATE = PLUGIN / "skills" / "info-hive" / "assets" / "ontology.yaml.template"
FIXTURE_WIKI = PLUGIN / "eval" / "decisions" / "fixtures" / "graph_wiki"
# wiki 0.9.3 のスクリプトが CONVENTIONAL_PAGES から作った出力。作り方はファイルの note にある。
GOLDEN = Path(__file__).with_name("graph_frontmatter_values_golden.json")
sys.path.insert(0, str(SCRIPTS))

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

import wiki_lint  # noqa: E402
from wiki_text import canonical_meta  # noqa: E402

if HAS_YAML:
    import wiki_graph_extract as extract
    import wiki_graph_lint as graph_lint

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

SOURCE_PAGE = '---\ntype: "source"\ntitle: "s"\n---\n本文\n'


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def page(frontmatter: str, body: str = "本文\n") -> str:
    return "---\n" + textwrap.dedent(frontmatter).strip("\n") + "\n---\n" + body


def without_graph(meta: dict) -> dict:
    return {k: v for k, v in meta.items() if k != "graph"}


def legacy_meta(text: str) -> dict:
    """0.9.3 までの読み方。frontmatter の全体を PyYAML で読む。"""
    m = extract.FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return extract.normalize_refs(canonical_meta(meta)[0])


def dump(rows: list[dict]) -> list[str]:
    return sorted(json.dumps(extract._normalize_for_json(r), sort_keys=True, ensure_ascii=False) for r in rows)


class WikiCase(unittest.TestCase):
    def setUp(self):
        self.wiki = Path(tempfile.mkdtemp(prefix="graph-fm-values-"))
        self.addCleanup(shutil.rmtree, self.wiki, ignore_errors=True)
        (self.wiki / "graph").mkdir()
        shutil.copyfile(TEMPLATE, self.wiki / "graph" / "ontology.yaml")
        # CLI は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページに数えない。
        (self.wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
        self.ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")

    def build(self):
        pages = extract.collect_pages(self.wiki)
        diagnostics: list[dict] = []
        nodes, page_node_ids, aliases = extract.build_nodes(pages, self.ontology, diagnostics)
        edges = extract.build_edges(pages, page_node_ids, diagnostics)
        return nodes, edges, diagnostics, aliases

    def graph_meta(self, name: str) -> dict:
        pages = {p["rel_path"]: p for p in extract.collect_pages(self.wiki)}
        return pages[name]["meta"]

    def graph_findings(self) -> dict:
        return graph_lint.lint(graph_lint.collect_pages(self.wiki), self.ontology)

    def lint_findings(self) -> dict:
        pages = wiki_lint.collect_pages(self.wiki)
        return wiki_lint.lint(pages, 100, 200, [], False, 3)

    def cli(self, script: str, *args: str):
        return subprocess.run([sys.executable, str(SCRIPTS / script), str(self.wiki), *args],
                              capture_output=True, text=True, encoding="utf-8", env=ENV)


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class ReproTest(WikiCase):
    """依頼の再現。lint が解決する `sources: [true]` を、グラフも解決する。"""

    def test_sources_true_resolves_like_lint(self):
        write(self.wiki / "a.md", page('type: "concept"\nsources: [true]'))
        write(self.wiki / "true.md", page('type: "source"'))
        self.assertEqual(self.lint_findings()["unresolved_sources"], [])
        self.assertEqual(self.graph_meta("a.md")["sources"], ["true"])
        _nodes, edges, diagnostics, _aliases = self.build()
        sourced = [(e["subject"], e["object"], e["source"]) for e in edges if e["predicate"] == "sourced_from"]
        self.assertEqual(sourced, [("concept:a", "source:true", "true")])
        self.assertEqual(diagnostics, [])
        findings = self.graph_findings()
        self.assertEqual(findings["unresolved_sources"], [])

    def test_sources_null_is_unresolved_on_both_sides(self):
        write(self.wiki / "a.md", page('type: "concept"\nsources: [null]'))
        lint_unresolved = self.lint_findings()["unresolved_sources"]
        self.assertEqual([(f["path"], f["source"]) for f in lint_unresolved], [("a.md", "null")])
        _nodes, _edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [{"kind": "unresolved_source", "page": "a.md", "source": "null", "pages": []}])
        self.assertEqual([(f["page"], f["source"]) for f in self.graph_findings()["unresolved_sources"]],
                         [("a.md", "null")])

    def test_cli_extract_writes_the_edge(self):
        write(self.wiki / "a.md", page('type: "concept"\nsources: [true]'))
        write(self.wiki / "true.md", page('type: "source"'))
        proc = self.cli("wiki_graph_extract.py", "--formats", "jsonl")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("診断", proc.stderr)
        edges = [json.loads(line) for line in
                 (self.wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(e["subject"], e["predicate"], e["object"], e["source"]) for e in edges],
                         [("concept:a", "sourced_from", "source:true", "true")])


# 最上位の欄の書き方。どれも、グラフの meta（graph を除く）が lint の meta と等しくなる。
TOP_LEVEL_CASES = {
    "真偽値": "type: yes\nkind: on\nsources: [true, yes, no, on, off, false]\nraw: no",
    "null": "type: null\nkind: ~\nsources: [null, ~]\nraw: null",
    "数": "type: 1\nkind: 2024\nsources: [1, 007, 1.10, 1e3, 0x1F, 1_000, 12:30]\nraw: 1.0",
    "日付と日時": "type: 2024-01-01\nkind: 2024-1-1\nsources: [2024-01-01, 2024-01-01T10:00:00Z]\nraw: 2024-01-01",
    "引用符つき": 'type: "source"\nkind: "paper"\nsources: ["a", "b, c"]\nraw: "raw/a.md"\ntitle: "T"\ntags: ["x"]',
    "日本語の別名": "種類: 資料\n種別: 論文\n出典: [true, 007]\n原文: 2024-01-01\nタイトル: 123\nタグ: [1, yes]",
    "別名と英語のキーの衝突": 'type: "concept"\n種類: yes\nsources: [1]\n出典: [2]',
    "字下げ 2 つの配列": "sources:\n  - true\n  - 007\nraw:\n  - raw/a.md",
    "字下げのない配列": "sources:\n- paper\n- other",
    "字下げ 4 つの配列": "sources:\n    - paper",
    "複数行の配列": "sources: [paper,\n  other]",
    "同じキーを 2 度": "sources: [a]\nsources: [b]",
    "コロンのあとに空白なし": "type:source\nsources:[a]",
    "引用符つきのキー": '"type": source\nsources: [a]',
    "キーのあとに空白": "type : source\nsources: [a]",
    "ブロックのスカラー": "raw: >\n  raw/a.md\ntype: source",
    "アンカーとタグ": "sources: &s [a]\nraw: !!str true\ntype: source",
    "読めない YAML": "title: a: b\ntype: source\nsources: [true]",
    "入れ子の wikilink": "sources: [[sources/paper]]\ntype: concept",
    "値のないキー": "type:\nkind:\nsources:\nraw:\ntitle:\ntags:",
    "文字列の sources": "sources: paper\ntags: ml\ntype: concept",
    "日付の欄": "created: 2024-01-01\nupdated: 2024-1-1\ntitle: 2024",
    "graph と並ぶ": "type: yes\ngraph:\n  node_id: x\n  aliases:\n  - y\nsources: [true]",
    "コメント": 'type: source # 種類\nsources: [true] # 出典\ntitle: "a # b"',
    "NFD の参照": 'sources: ["カ\u3099", カ\u3099]\nraw: "カ\u3099.md"\ntype: concept',
    "PyYAML が組み立てられない値": "created: 2026-13-01\nupdated: 0000-01-01\ntype: source\nsources: [true]",
    # 二重引用符の中のエスケープは、lint と同じ値に読む。wiki 0.9.7 から、lint のパーサーも YAML の意味で読む。
    "エスケープ": 'title: "a\\tb caf\\u00e9"\nraw: "raw\\/a.md"\nsources: ["a\\nb", "C:\\\\x", "q\\"q"]\ntype: source',
    "引用符のない日時": "created: 2026-11-01 10:00:00\nupdated: 2026-11-01T10:00:00Z\ntitle: [a] b",
    "最上位のマージキー":"base: &b {type: source}\n<<: *b\nsources: [true]",
}


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class TopLevelMatchesLintTest(WikiCase):
    def test_top_level_fields_equal_lint(self):
        for name, frontmatter in TOP_LEVEL_CASES.items():
            with self.subTest(name):
                write(self.wiki / "p.md", page(frontmatter))
                lint_meta = {p["rel_path"]: p for p in wiki_lint.collect_pages(self.wiki)}["p.md"]["meta"]
                graph_meta = self.graph_meta("p.md")
                # lint の辞書に、グラフと同じ NFC の正規化（参照の値）をかけたものと等しい。
                self.assertEqual(without_graph(graph_meta), without_graph(extract.normalize_refs(lint_meta)))
                # graph は、PyYAML がマッピングに読めたときだけ置く。lint の形の [] は残さない。
                self.assertTrue("graph" not in graph_meta or isinstance(graph_meta["graph"], dict))
                # 抽出と lint が、この書き方で止まらない。
                self.build()
                self.graph_findings()

    def test_graph_field_comes_from_pyyaml(self):
        write(self.wiki / "p.md", page(TOP_LEVEL_CASES["graph と並ぶ"]))
        meta = self.graph_meta("p.md")
        self.assertEqual(meta["graph"], {"node_id": "x", "aliases": ["y"]})
        self.assertEqual(meta["type"], "yes")
        self.assertEqual(meta["sources"], ["true"])

    def test_ontology_maps_from_is_read_as_written(self):
        # オントロジーの maps_from に引用符のない数や真偽値を書いても、ページの同じ書き方の値に当たる（0.9.3 と同じ ID）。
        write(self.wiki / "graph" / "ontology.yaml", textwrap.dedent("""\
            node_types:
              cohort:
                maps_from: {type: entity, kind: 2024}
              flag:
                maps_from:
                  type: yes
                  kind: 007
              concept:
                maps_from: {type: concept}
            predicates:
              depends_on: {subject_types: ["*"], object_types: ["*"], requires_evidence: false}
        """))
        ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        self.assertEqual(ontology["node_types"]["cohort"]["maps_from"], {"type": "entity", "kind": "2024"})
        self.assertEqual(ontology["node_types"]["flag"]["maps_from"], {"type": "yes", "kind": "007"})
        write(self.wiki / "a.md", page('type: "entity"\nkind: 2024'))
        write(self.wiki / "b.md", page("type: yes\nkind: 007"))
        write(self.wiki / "c.md", page('type: "concept"\ngraph:\n  relationships:\n'
                                       '    - {predicate: depends_on, object: "cohort:a"}\n'
                                       '    - {predicate: depends_on, object: "flag:b"}'))
        pages = extract.collect_pages(self.wiki)
        nodes, _ids, _aliases = extract.build_nodes(pages, ontology)
        self.assertEqual(sorted(n["id"] for n in nodes), ["cohort:a", "concept:c", "flag:b"])
        self.assertEqual(graph_lint.lint(pages, ontology)["broken_object_refs"], [])

    def test_ontology_maps_from_through_merge_keys_and_anchors(self):
        # マージキー（<<）とアンカーで来た maps_from の値も、書かれた文字になる。
        write(self.wiki / "graph" / "ontology.yaml", textwrap.dedent("""\
            base: &b {type: entity, kind: 2024}
            shared: &m {type: entity, kind: 007}
            whole: &w
              maps_from: {type: entity, kind: 1.10}
            node_types:
              cohort:
                maps_from: {<<: *b}
              agent:
                maps_from: *m
              release: *w
              override:
                maps_from: {<<: *b, kind: 2025}
            predicates:
              depends_on: {subject_types: ["*"], object_types: ["*"], requires_evidence: false}
        """))
        ontology = extract.read_ontology(self.wiki / "graph" / "ontology.yaml")
        self.assertEqual({name: d["maps_from"]["kind"] for name, d in ontology["node_types"].items()},
                         {"cohort": "2024", "agent": "007", "release": "1.10", "override": "2025"})
        for slug, kind in (("a", "2024"), ("b", "007"), ("c", "1.10"), ("d", "2025")):
            write(self.wiki / f"{slug}.md", page(f'type: "entity"\nkind: {kind}'))
        write(self.wiki / "e.md", page('type: "concept"\ngraph:\n  relationships:\n'
                                       '    - {predicate: depends_on, object: "cohort:a"}'))
        pages = extract.collect_pages(self.wiki)
        nodes, _ids, _aliases = extract.build_nodes(pages, ontology)
        self.assertEqual(sorted(n["id"] for n in nodes),
                         ["agent:b", "cohort:a", "concept:e", "override:d", "release:c"])
        self.assertEqual(graph_lint.lint(pages, ontology)["broken_object_refs"], [])

    def test_ontology_with_a_value_pyyaml_cannot_construct(self):
        # PyYAML が ValueError を出すオントロジーは、止まらずに「読めない」として扱う（CLI は終了コード 2）。
        path = self.wiki / "graph" / "ontology.yaml"
        write(path, "node_types: {}\npredicates: {}\nupdated: 2026-13-01\n")
        with self.assertRaises(extract.OntologyError):
            extract.read_ontology(path)
        write(self.wiki / "a.md", page('type: "concept"'))
        for script in ("wiki_graph_extract.py", "wiki_graph_lint.py"):
            proc = self.cli(script)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("オントロジーを読めない", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_ontology_other_values_stay_typed(self):
        # maps_from の type と kind のほかは、PyYAML の値のまま。
        path = self.wiki / "graph" / "ontology.yaml"
        write(path, "node_types:\n  a:\n    maps_from: {type: 1, kind: null}\n    explicit_only: yes\n    rank: 007\n"
                    "predicates:\n  p: {requires_evidence: no, subject_types: [1]}\n")
        ontology = extract.read_ontology(path)
        self.assertEqual(ontology["node_types"]["a"], {"maps_from": {"type": "1", "kind": None},
                                                       "explicit_only": True, "rank": 7})
        self.assertEqual(ontology["predicates"]["p"], {"requires_evidence": False, "subject_types": [1]})

    def test_type_and_kind_as_written_match_the_ontology(self):
        # オントロジーの maps_from は、文字で書いた値がページの値に当たる。
        ontology = {"node_types": {"flag": {"maps_from": {"type": "yes", "kind": "2024"}},
                                   "source": {"maps_from": {"type": "source"}}}, "predicates": {}}
        write(self.wiki / "p.md", page("type: yes\nkind: 2024"))
        pages = extract.collect_pages(self.wiki)
        nodes, _ids, _aliases = extract.build_nodes(pages, ontology)
        self.assertEqual([(n["id"], n["node_type"], n["page_type"], n["kind"]) for n in nodes],
                         [("flag:p", "flag", "yes", "2024")])

    def test_source_page_written_without_quotes_is_a_source(self):
        # type: の値が何に読まれても、`type == "source"` の判定は lint と同じになる。
        write(self.wiki / "s.md", page("種類: 資料\n原文: 2024-01-01\nsources: [s]"))
        _nodes, edges, _diagnostics, _aliases = self.build()
        self.assertEqual([(e["predicate"], e["object"]) for e in edges], [("summarizes_raw", "raw:2024-01-01")])

    def test_raw_list_makes_one_edge_per_value(self):
        write(self.wiki / "s.md", page('type: "source"\nraw: ["raw/a.md", "raw/b.md"]'))
        _nodes, edges, _diagnostics, _aliases = self.build()
        self.assertEqual(sorted(e["object"] for e in edges if e["predicate"] == "summarizes_raw"),
                         ["raw:raw/a.md", "raw:raw/b.md"])

    def test_scalar_tags_is_one_tag(self):
        write(self.wiki / "p.md", page('type: "concept"\ntags: ml'))
        # 配列で書いたタグは、0.9.3 と同じく、空白も空の要素もそのまま残す（NFKC にもしない）。
        write(self.wiki / "q.md", page('type: "concept"\ntags: ["ＡＩ", " a ", "", "ml"]'))
        write(self.wiki / "r.md", page('type: "concept"\ntags:'))
        write(self.wiki / "s.md", page('type: "concept"\ntags: ""'))
        nodes, _edges, _diagnostics, _aliases = self.build()
        self.assertEqual({n["slug"]: n["tags"] for n in nodes},
                         {"p": ["ml"], "q": ["ＡＩ", " a ", "", "ml"], "r": [], "s": []})

    def test_escapes_follow_lint_and_datetimes_are_text(self):
        # wiki 0.9.7 から、lint のパーサーが YAML のエスケープを YAML の意味で読む。グラフも同じ値になる。
        write(self.wiki / "p.md", page(TOP_LEVEL_CASES["エスケープ"]))
        meta = self.graph_meta("p.md")
        self.assertEqual(meta["title"], "a\tb caf\N{LATIN SMALL LETTER E WITH ACUTE}")
        self.assertEqual(meta["raw"], "raw/a.md")
        self.assertEqual(meta["sources"], ["a\nb", "C:\\x", 'q"q'])
        # YAML にないエスケープが 1 つでもある値は、lint と同じく、書かれた文字のまま読む。
        write(self.wiki / "p.md", page('type: concept\ntitle: "\\d+\\n"\nsources: ["C:\\Users\\new"]'))
        meta = self.graph_meta("p.md")
        self.assertEqual((meta["title"], meta["sources"]), ("\\d+\\n", ["C:\\Users\\new"]))
        write(self.wiki / "p.md", page("type: concept\ncreated: 2026-11-01 10:00:00"))
        nodes, _edges, _diagnostics, _aliases = self.build()
        self.assertEqual(nodes[0]["created"], "2026-11-01 10:00:00")

    def test_title_and_dates_are_text(self):
        write(self.wiki / "p.md", page("type: concept\ntitle: 2024\ncreated: 2024-01-01\nupdated: 2024-1-1"))
        nodes, _edges, _diagnostics, _aliases = self.build()
        self.assertEqual([(n["title"], n["created"], n["updated"]) for n in nodes], [("2024", "2024-01-01", "2024-1-1")])


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class UnreadFieldTest(WikiCase):
    """lint のパーサーが読めない書き方の欄は、グラフも読まない。黙らずに診断に挙げる。

    wiki 0.9.7 で、lint のパーサーが読む書き方を広げた。読めるようになった書き方では、診断が出ず、エッジができる。
    """

    def unread(self):
        _nodes, _edges, diagnostics, _aliases = self.build()
        return [(d["page"], d["field"]) for d in diagnostics if d["kind"] == "unread_field"]

    def test_spellings_readable_since_0_9_7_make_edges(self):
        # 0.9.5 では unread_field に挙がり、sourced_from ができなかった書き方。
        write(self.wiki / "paper.md", SOURCE_PAGE)
        cases = {
            "字下げのない配列": "sources:\n- paper",
            "字下げ 4 つの配列": "sources:\n    - paper",
            "複数行の配列": "sources: [paper,\n  paper]",
            "字下げのない閉じ括弧": "sources: [\npaper,# コメント\npaper\n]",
            "引用符つきのキー": '"sources": [paper]',
            "キーのあとに空白": "sources : [paper]",
            "日本語の別名": "出典:\n- paper",
            "同じキーの 2 つ目が字下げのない配列": "sources: [paper]\nsources:\n- paper",
            "エスケープ": 'sources: ["\\u0070aper"]',
            "ブロックのスカラー": "sources: >\n  paper",
        }
        for name, frontmatter in cases.items():
            with self.subTest(name):
                write(self.wiki / "a.md", page('type: "concept"\n' + frontmatter))
                _nodes, edges, diagnostics, _aliases = self.build()
                self.assertEqual(diagnostics, [])
                self.assertEqual({(e["subject"], e["predicate"], e["object"]) for e in edges},
                                 {("concept:a", "sourced_from", "source:paper")})
                findings = self.graph_findings()
                self.assertEqual(findings["unread_fields"], [])
                # wiki の lint も、同じページに解決する。
                self.assertEqual(self.lint_findings()["unresolved_sources"], [])

    def test_items_after_an_unread_key_line_belong_to_no_one(self):
        # 0.9.5 までは、読まないキーの行（source-url:）を挟んでも配列を続け、b も sources の要素にしていた。
        # YAML では b は source-url の要素である。0.9.7 から、lint もグラフも sources を ["a"] と読む。
        write(self.wiki / "a.md", SOURCE_PAGE)
        write(self.wiki / "b.md", SOURCE_PAGE)
        write(self.wiki / "c.md", page('type: "concept"\nsources:\n  - "a"\nsource-url:\n  - "b"'))
        _nodes, edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [])
        self.assertEqual([(e["predicate"], e["object"]) for e in edges], [("sourced_from", "source:a")])
        self.assertEqual(yaml.safe_load('sources:\n  - "a"\nsource-url:\n  - "b"')["sources"], ["a"])

    def test_lists_the_lint_parser_cannot_read(self):
        write(self.wiki / "paper.md", SOURCE_PAGE)
        cases = {
            "アンカー": "sources: &s [paper]",
            "次の行に書いた配列": "sources:\n  [paper]",
            "? の形のキー": "? sources\n: [paper]",
            "エスケープを含むキー": '"s\\u006Furces": [paper]',
            "続きの行が字下げのないキーの形": "sources: [paper,\nb: c]",
            "同じキーの 2 つ目だけ読めない": "sources: [paper]\nsources:\n  [paper]",
        }
        for name, frontmatter in cases.items():
            with self.subTest(name):
                write(self.wiki / "a.md", page('type: "concept"\n' + frontmatter))
                self.assertEqual(self.unread(), [("a.md", "sources")])
                findings = self.graph_findings()
                self.assertEqual(findings["unread_fields"], [{"page": "a.md", "field": "sources"}])
                self.assertEqual(findings["summary"]["unread_fields"], 1)

    def test_field_written_twice_with_one_unreadable_key(self):
        # lint のパーサーが読めるキーと読めないキーで 2 度書くと、YAML では後の値が勝つ。読めなかった宣言を見落とさない。
        # 0.9.7 から、引用符つきのキーとコロンの前の空白は読める。読めないキーは、`? key` の形で確かめる。
        cases = {
            'type: "concept"\n? type\n: "source"': [("a.md", "type")],
            'sources: ["a"]\n? sources\n: "b"': [("a.md", "sources")],
            'sources: ["a"]\n"s\\u006Furces": ["b"]': [("a.md", "sources")],
            # 値のない宣言を lint のパーサーが読んでいても、あとの読めない宣言を隠さない。
            'sources:\n? sources\n: "s"': [("a.md", "sources")],
            'type:\n? type\n: "source"': [("a.md", "type")],
            'type: null\n? type\n: "source"': [("a.md", "type")],
            'sources: ["a"]\n? sources\n:': [("a.md", "sources")],
            # 引用符つきのキーとコロンの前の空白で 2 度書いた欄は、lint のパーサーがどちらも読むので挙げない。
            'type: "concept"\n"type": "source"': [],
            'sources: ["a"]\n"sources": "b"': [],
            'sources: ["a"]\nsources : ["b"]': [],
            'sources:\n"sources": "s"': [],
            'type: null\n\'type\' : "source"': [],
        }
        for frontmatter, expected in cases.items():
            with self.subTest(frontmatter):
                write(self.wiki / "a.md", page(frontmatter))
                self.assertEqual(self.unread(), expected)

    def test_top_level_merge_keys(self):
        # マージで来た既定値を、書いた値が上書きしているときは、YAML の値も lint の値も同じなので挙げない。
        write(self.wiki / "a.md", page('base: &b {sources: ["a"]}\n<<: *b\nsources: ["b"]\ntype: "concept"'))
        self.assertEqual(self.unread(), [])
        # マージだけで来た値は、lint のパーサーが読まないので挙げる。
        write(self.wiki / "a.md", page('base: &b {sources: ["a"], type: "source"}\n<<: *b\nkind: "x"'))
        self.assertEqual(self.unread(), [("a.md", "type"), ("a.md", "sources")])

    def test_type_kind_and_raw(self):
        write(self.wiki / "a.md", page('? type\n: source\n? kind\n: paper\nraw:\n  [raw/a.md, raw/b.md]'))
        self.assertEqual(self.unread(), [("a.md", "type"), ("a.md", "kind"), ("a.md", "raw")])
        # 0.9.7 から読める書き方では挙がらず、ノードの種類と summarizes_raw に使う。
        write(self.wiki / "a.md", page('"type": source\nkind : paper\nraw:\n- raw/a.md\n- raw/b.md'))
        nodes, edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [])
        self.assertEqual([(n["page_type"], n["kind"]) for n in nodes], [("source", "paper")])
        self.assertEqual(sorted(e["object"] for e in edges if e["predicate"] == "summarizes_raw"),
                         ["raw:raw/a.md", "raw:raw/b.md"])

    def test_readable_spellings_are_not_reported(self):
        cases = [
            'type: "concept"\nkind: "x"\nsources: ["paper", "a, b"]\nraw: "raw/a.md"',
            "type: concept\nsources:\n  - paper\n  - other\nraw:\n  - raw/a.md",
            "種類: 概念\n出典: [true, 007, null]\n原文: 2024-01-01",
            "type: yes\nkind: 2024\nsources: paper\nraw: null",
            "type:\nkind:\nsources:\nraw: []",
            "sources: [a]\nsources: [b]",
            "sources: [[sources/paper]]",
            "type: concept # 種類\nsources: [a] # 出典",
            "title: x\ntags:\n- a",   # 見ている欄ではない
            # 0.9.7 から読める書き方
            '"type": "concept"\nkind : "x"\nsources:\n- paper\n- other\nraw:\n    - raw/a.md',
            "sources: [paper,\n  other,\n]\n'raw': |\n  raw/a.md",
            '種類 : 概念\n"出典":\n- "\\u8AD6\\u6587"',
            'sources: ["a"]\nsources: "b"',          # あとの文字列が配列を置き換える。YAML も lint も "b"
            'sources: "b"\nsources: ["a", "c"]',
            'sources: ["a"]\n出典: ["b"]',            # 別名との衝突。lint のパーサーはどちらも読んでいる
            '出典: ["a", "b"]\nsources: ["c"]',
            'sources:\n"sources":',                   # 値のある宣言がない
            '"sources":\n"type": null',
        ]
        for frontmatter in cases:
            with self.subTest(frontmatter):
                write(self.wiki / "a.md", page(frontmatter))
                self.assertEqual(self.unread(), [])

    def test_cli_reports_it(self):
        write(self.wiki / "paper.md", SOURCE_PAGE)
        write(self.wiki / "a.md", page('type: "concept"\nsources:\n  [paper]'))
        proc = self.cli("wiki_graph_lint.py", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["unread_fields"], [{"page": "a.md", "field": "sources"}])
        text = self.cli("wiki_graph_lint.py").stdout
        self.assertIn("a.md  sources:", text)
        proc = self.cli("wiki_graph_extract.py", "--formats", "jsonl")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(extract.DIAGNOSTIC_LABELS["unread_field"], proc.stderr)
        # 読めなかった sources: からは、sourced_from を作らない（lint、検索、統計と同じく、値は空）。
        self.assertEqual((self.wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8"), "")

    def test_cli_reads_the_spellings_readable_since_0_9_7(self):
        write(self.wiki / "paper.md", SOURCE_PAGE)
        write(self.wiki / "a.md", page('"type": "concept"\nsources:\n- paper'))
        proc = self.cli("wiki_graph_lint.py", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["unread_fields"], [])
        proc = self.cli("wiki_graph_extract.py", "--formats", "jsonl")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(extract.DIAGNOSTIC_LABELS["unread_field"], proc.stderr)
        edges = [json.loads(line) for line in
                 (self.wiki / "graph" / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(e["subject"], e["predicate"], e["object"]) for e in edges],
                         [("concept:a", "sourced_from", "source:paper")])


CONVENTIONAL_PAGES = {
    "concepts/alpha.md": page('''
        type: "concept"
        title: "アルファ"
        tags: ["x", "y"]
        sources: ["paper", "sources/note", "[[sources/note]]"]
        created: 2026-11-01
        updated: 2026-11-02
        graph:
          node_id: "concept:alpha"
          canonical: true
          aliases: ["A", "あるふぁ"]
          relationships:
            - predicate: "depends_on"
              object: "concept:beta"
              source: "paper"
              evidence: "alpha は beta に依存する"
              confidence: "high"
              status: "current"
              valid_from: 2024-01-01
              notes: "メモ"
            - predicate: "depends_on"
              object: "concept:beta"
              source: "paper"
              evidence: "alpha は beta に依存する"
              confidence: "high"
              status: "historical"
              supersedes: "concept:gamma"
    ''', "[[beta]] と [[sources/paper]] を参照する。\n"),
    "concepts/beta.md": page('''
        type: "concept"
        title: "ベータ"
        tags: []
        sources:
          - "paper"
        created: 2026-11-01
        updated: 2026-11-02
    ''', "[[alpha]]\n"),
    "entities/taro.md": page('''
        種類: "エンティティ"
        種別: "人物"
        タイトル: "太郎"
        タグ: ["人"]
        出典: ["paper"]
        作成日: 2026-11-01
        graph:
          relationships:
            - predicate: "proposed"
              object: "concept:alpha"
              source: "paper"
              evidence: "太郎が提案した"
              confidence: "medium"
              status: "current"
    '''),
    "sources/paper.md": page('''
        type: "source"
        title: "論文"
        raw: "raw/paper.pdf"
        tags: ["x"]
        created: 2026-11-01
        updated: 2026-11-02
        ingested: 2026-11-01
    ''', "alpha は beta に依存する。太郎が提案した。\n"),
    "sources/note.md": page('''
        type: "source"
        title: "メモ"
        raw: "../raw/note.md"
        created: 2026-11-01
    '''),
}


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class ConventionalPagesUnchangedTest(unittest.TestCase):
    """引用符で囲む規約どおりのページでは、ノードもエッジも ID も、0.9.3 までの読み方と変わらない。"""

    def compare(self, wiki: Path, ontology: dict):
        pages = extract.collect_pages(wiki)
        self.assertTrue(pages)
        legacy_pages = []
        for p in pages:
            text = Path(p["path"]).read_text(encoding="utf-8-sig")
            legacy_pages.append({**p, "meta": legacy_meta(text)})
        built = []
        for current in (pages, legacy_pages):
            diagnostics: list[dict] = []
            nodes, ids, aliases = extract.build_nodes(current, ontology, diagnostics)
            edges = extract.build_edges(current, ids, diagnostics)
            built.append((dump(nodes), dump(edges), dump(aliases), dump(diagnostics)))
        self.assertTrue(built[0][1], "エッジが 1 本もない試験データでは、何も確かめられない")
        for new, old in zip(built[0], built[1]):
            self.assertEqual(new, old)
        self.assertEqual([p["fm_problems"] for p in pages if p["fm_problems"]], [])
        self.assertEqual(json.dumps(graph_lint.lint(pages, ontology), sort_keys=True, default=str, ensure_ascii=False),
                         json.dumps(graph_lint.lint(legacy_pages, ontology), sort_keys=True, default=str,
                                    ensure_ascii=False))

    def test_plugin_fixture_wiki(self):
        self.compare(FIXTURE_WIKI, extract.read_ontology(FIXTURE_WIKI / "graph" / "ontology.yaml"))

    def test_quoted_pages_match_the_output_of_0_9_3(self):
        # 0.9.3 のスクリプトそのものが作った出力と比べる（読み方だけでなく、ノードとエッジの作り方の変更も見る）。
        wiki = Path(tempfile.mkdtemp(prefix="graph-fm-conventional-"))
        self.addCleanup(shutil.rmtree, wiki, ignore_errors=True)
        for rel, text in CONVENTIONAL_PAGES.items():
            write(wiki / rel, text)
        write(wiki / "SCHEMA.md", "# スキーマ\n")
        ontology = extract.read_ontology(TEMPLATE)
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        pages = extract.collect_pages(wiki)
        diagnostics: list[dict] = []
        nodes, ids, aliases = extract.build_nodes(pages, ontology, diagnostics)
        edges = extract.build_edges(pages, ids, diagnostics)

        def plain(value):
            return json.loads(json.dumps(extract._normalize_for_json(value), sort_keys=True, ensure_ascii=False,
                                         default=str))

        self.assertEqual(sorted(plain(nodes), key=lambda n: n["id"]), golden["nodes"])
        self.assertEqual(sorted(plain(edges), key=lambda e: e["id"]), golden["edges"])
        self.assertEqual(sorted(plain(aliases), key=lambda a: (a["alias"], a["node_id"])), golden["aliases"])
        self.assertEqual(plain(diagnostics), golden["diagnostics"])
        findings = plain(graph_lint.lint(pages, ontology))
        # 0.9.5 で足した検出結果（どちらも空）を除けば、lint の結果も同じ。
        for key in ("unreadable_graph", "unread_fields"):
            self.assertEqual(findings.pop(key), [])
            self.assertEqual(findings["summary"].pop(key), 0)
        self.assertEqual(findings, golden["lint"])
        # CLI が書き出す JSONL も同じ（ID を含む）。
        (wiki / "graph").mkdir()
        shutil.copyfile(TEMPLATE, wiki / "graph" / "ontology.yaml")
        proc = subprocess.run([sys.executable, str(SCRIPTS / "wiki_graph_extract.py"), str(wiki), "--formats", "jsonl"],
                              capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("nodes", "edges"):
            rows = [json.loads(line) for line in
                    (wiki / "graph" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows, golden[name])

    def test_quoted_pages(self):
        wiki = Path(tempfile.mkdtemp(prefix="graph-fm-conventional-"))
        self.addCleanup(shutil.rmtree, wiki, ignore_errors=True)
        for rel, text in CONVENTIONAL_PAGES.items():
            write(wiki / rel, text)
        write(wiki / "SCHEMA.md", "# スキーマ\n")
        ontology = extract.read_ontology(TEMPLATE)
        self.compare(wiki, ontology)
        # 比べた中身が空でないこと（型付きの関係、sourced_from、summarizes_raw、別名がある）。
        pages = extract.collect_pages(wiki)
        nodes, ids, aliases = extract.build_nodes(pages, ontology)
        predicates = {e["predicate"] for e in extract.build_edges(pages, ids)}
        self.assertLessEqual({"depends_on", "proposed", "mentions", "sourced_from", "summarizes_raw"}, predicates)
        self.assertEqual(len(aliases), 2)


def relation(**fields) -> str:
    lines = ["    - predicate: depends_on"]
    base = {"object": "concept:other", "source": "s", "evidence": '"x"', "confidence": "high", "status": "current"}
    for key, value in {**base, **fields}.items():
        if value is not None:
            lines.append(f"      {key}: {value}")
    return "\n".join(lines)


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class GraphReferenceFieldsTest(WikiCase):
    """`graph:` の中の、ページやノードを指す欄は、書かれた文字で読む。"""

    def setUp(self):
        super().setUp()
        write(self.wiki / "other.md", page('type: "concept"'))
        write(self.wiki / "s.md", SOURCE_PAGE)

    def add(self, name: str, graph_lines: str, top: str = 'type: "concept"'):
        write(self.wiki / name, "---\n" + top + "\ngraph:\n" + graph_lines + "\n---\n本文\n")

    def typed_edges(self):
        _nodes, edges, _diagnostics, _aliases = self.build()
        return [e for e in edges if e["predicate"] == "depends_on"]

    def test_source_is_read_as_written(self):
        for value in ("007", "1.10", "true", "no", "0x1F", "1_000", "2024-01-01", "2024-01-01T10:00:00Z"):
            with self.subTest(value):
                slug = value.replace(":", "-")
                if slug != value:
                    continue  # Windows のファイル名に : は使えない。値の読み方は次の試験で確かめる。
                write(self.wiki / f"{value}.md", SOURCE_PAGE)
                self.add("a.md", "  relationships:\n" + relation(source=value))
                rel = self.graph_meta("a.md")["graph"]["relationships"][0]
                self.assertEqual(rel["source"], value)
                self.assertEqual([e["source"] for e in self.typed_edges()], [value])
                findings = self.graph_findings()
                self.assertEqual(findings["broken_source_refs"], [])
                self.assertEqual(findings["missing_source_field"], [])
                (self.wiki / f"{value}.md").unlink()

    def test_reference_fields_keep_their_text(self):
        self.add("a.md", "\n".join([
            "  node_id: no",
            "  aliases: [1.10, yes, 007, \"x\", 2024-01-01T10:00:00Z]",
            "  relationships:",
            relation(object="no", source="12:30", contradicts="1.10", supersedes="off"),
        ]))
        graph = self.graph_meta("a.md")["graph"]
        self.assertEqual(graph["node_id"], "no")
        self.assertEqual(graph["aliases"], ["1.10", "yes", "007", "x", "2024-01-01T10:00:00Z"])
        rel = graph["relationships"][0]
        self.assertEqual((rel["object"], rel["source"], rel["contradicts"], rel["supersedes"]),
                         ("no", "12:30", "1.10", "off"))
        nodes, edges, _diagnostics, aliases = self.build()
        self.assertIn("no", {n["id"] for n in nodes})
        self.assertEqual(sorted(a["alias"] for a in aliases if a["node_id"] == "no"),
                         ["007", "1.10", "2024-01-01T10:00:00Z", "x", "yes"])
        typed = [e for e in edges if e["predicate"] == "depends_on"]
        # object: no は、黙って捨てずに、文字の "no"（このページ自身のノード）へのエッジにする。
        self.assertEqual([(e["subject"], e["object"], e["source"], e["extras"]) for e in typed],
                         [("no", "no", "12:30", {"contradicts": "1.10", "supersedes": "off"})])

    def test_object_pointing_at_a_node_with_a_number_like_id(self):
        self.add("target.md", "  node_id: 007")
        self.add("a.md", "  relationships:\n" + relation(object="007"))
        self.assertEqual([(e["subject"], e["object"]) for e in self.typed_edges()], [("concept:a", "007")])
        self.assertEqual(self.graph_findings()["broken_object_refs"], [])

    def test_edge_id_reference_written_without_quotes(self):
        # 0.9.4 から、contradicts と supersedes にエッジの ID（16 進 24 桁）を書ける。数字だけの ID を引用符なしで
        # 書くと、PyYAML は数に読む（0 で始まる 0〜7 だけの並びは 8 進数）。書かれた文字で読めば、ID のまま残る。
        self.add("a.md", "  relationships:\n" + relation(contradicts="012345670123456701234567",
                                                         supersedes="123456789012345678901234"))
        rel = self.graph_meta("a.md")["graph"]["relationships"][0]
        self.assertEqual((rel["contradicts"], rel["supersedes"]),
                         ("012345670123456701234567", "123456789012345678901234"))
        self.assertTrue(extract.EDGE_ID_RE.match(rel["contradicts"]))
        findings = self.graph_findings()
        self.assertEqual([f["contradicts"] for f in findings["broken_contradicts"]], ["012345670123456701234567"])

    def test_null_stays_absent(self):
        self.add("a.md", "\n".join([
            "  node_id: null",
            "  aliases: [null, ~]",
            "  relationships:",
            relation(supersedes="null", contradicts="~", source="null"),
            relation(object="null"),
        ]))
        graph = self.graph_meta("a.md")["graph"]
        self.assertIsNone(graph["node_id"])
        self.assertEqual(graph["aliases"], [None, None])
        self.assertEqual([(r["object"], r["source"], r.get("supersedes"), r.get("contradicts"))
                          for r in graph["relationships"]],
                         [("concept:other", None, None, None), (None, "s", None, None)])
        nodes, edges, _diagnostics, _aliases = self.build()
        self.assertIn("concept:a", {n["id"] for n in nodes})
        typed = [e for e in edges if e["predicate"] == "depends_on"]
        self.assertEqual([(e["object"], e["source"], e["extras"]) for e in typed], [("concept:other", "", {})])
        findings = self.graph_findings()
        self.assertEqual(len(findings["missing_source_field"]), 1)
        self.assertEqual(findings["broken_supersedes"], [])
        self.assertEqual(findings["broken_contradicts"], [])

    def test_other_fields_keep_pyyaml_values(self):
        import datetime
        self.add("a.md", "\n".join([
            "  canonical: true",
            "  node_type: concept",
            "  relationships:",
            relation(valid_from="2024-01-01", valid_to="2025", notes="{count: 3, ok: true}", raw_ref="007",
                     evidence="123", confidence="high"),
        ]))
        graph = self.graph_meta("a.md")["graph"]
        self.assertIs(graph["canonical"], True)
        rel = graph["relationships"][0]
        self.assertEqual(rel["valid_from"], datetime.date(2024, 1, 1))
        self.assertEqual(rel["valid_to"], 2025)
        self.assertEqual(rel["notes"], {"count": 3, "ok": True})
        self.assertEqual(rel["raw_ref"], 7)
        self.assertEqual(rel["evidence"], 123)

    def test_shared_anchor_does_not_change_other_fields(self):
        # aliases と notes が同じ配列を共有していても、置き換えるのは aliases だけである。
        self.add("a.md", "\n".join([
            "  aliases: &a [007]",
            "  relationships:",
            relation(notes="*a", source="&s 007", raw_ref="*s"),
        ]))
        graph = self.graph_meta("a.md")["graph"]
        rel = graph["relationships"][0]
        self.assertEqual(graph["aliases"], ["007"])
        self.assertEqual(rel["notes"], [7])
        self.assertEqual((rel["source"], rel["raw_ref"]), ("007", 7))

    def test_self_referencing_anchor_does_not_block_the_reference_fields(self):
        # 自分を含むアンカーがあっても、参照の欄は書かれた文字になる（参照元の object: 007 と同じ ID になる）。
        self.add("target.md", "  node_id: 007\n  unused: *g", top='type: "concept"')
        text = (self.wiki / "target.md").read_text(encoding="utf-8").replace("graph:\n", "graph: &g\n")
        write(self.wiki / "target.md", text)
        self.add("a.md", "  relationships:\n" + relation(object="007"))
        self.assertEqual(self.graph_meta("target.md")["graph"]["node_id"], "007")
        _nodes, edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [])
        self.assertEqual([(e["subject"], e["object"]) for e in edges if e["predicate"] == "depends_on"],
                         [("concept:a", "007")])
        self.assertEqual(self.graph_findings()["broken_object_refs"], [])

    def test_top_level_merge_key_that_cannot_be_expanded(self):
        # 展開できない最上位のマージキーがあっても、graph は読む。
        write(self.wiki / "a.md", page('type: "concept"\n<<: 3\ngraph: {node_id: 007}'))
        self.assertEqual(self.graph_meta("a.md")["graph"], {"node_id": "007"})
        _nodes, _edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [])

    def test_values_outside_graph_do_not_block_it(self):
        # PyYAML が ValueError を出す最上位の値があっても、graph は読める（0.9.3 までは抽出が止まった）。
        write(self.wiki / "007.md", SOURCE_PAGE)
        self.add("a.md", "  node_id: 007x\n  relationships:\n" + relation(source="007"),
                 top='type: "concept"\ncreated: 2026-13-01\ncount: !!int abc')
        meta = self.graph_meta("a.md")
        self.assertEqual(meta["created"], "2026-13-01")
        self.assertEqual(meta["graph"]["relationships"][0]["source"], "007")
        _nodes, edges, diagnostics, _aliases = self.build()
        self.assertEqual(diagnostics, [])
        self.assertEqual([(e["subject"], e["source"]) for e in edges if e["predicate"] == "depends_on"],
                         [("007x", "007")])

    def test_graph_under_quoted_key_or_top_level_merge(self):
        write(self.wiki / "a.md", page('type: "concept"\n"graph":\n  node_id: 007'))
        self.assertEqual(self.graph_meta("a.md")["graph"], {"node_id": "007"})
        write(self.wiki / "a.md", page('type: "concept"\nbase: &b\n  graph: {node_id: x}\n<<: *b'))
        self.assertEqual(self.graph_meta("a.md")["graph"], {"node_id": "x"})
        write(self.wiki / "a.md", page('type: "concept"\ngraph: {node_id: x}\ngraph: {node_id: y}'))
        self.assertEqual(self.graph_meta("a.md")["graph"], {"node_id": "y"})

    def test_merge_keys_and_anchors_do_not_break(self):
        # マージキー（<<）で来た値とアンカーの値も、書かれた文字になる。止まらない。
        self.add("a.md", "\n".join([
            "  base: &base {source: 007, object: 1.10}",
            "  aliases: &names [007, x]",
            "  relationships:",
            "    - {<<: *base, predicate: depends_on, evidence: \"x\"}",
            "    - {predicate: depends_on, object: 007, source: *names, evidence: \"x\"}",
        ]))
        graph = self.graph_meta("a.md")["graph"]
        self.assertEqual(graph["aliases"], ["007", "x"])
        first, second = graph["relationships"]
        self.assertEqual((first["source"], first["object"]), ("007", "1.10"))
        self.assertEqual((second["object"], second["source"]), ("007", ["007", "x"]))
        # アンカーの元（参照の欄ではない base）は、PyYAML の値のまま残る。
        self.assertEqual(graph["base"], {"source": 7, "object": 1.1})
        self.build()
        self.graph_findings()

    def test_odd_shapes_do_not_break(self):
        shapes = [
            "  relationships: [007, [1], {object: [007, no], predicate: x, source: {b: 2}}]",
            "  relationships: [{object: 007}, {source: 007, predicate: depends_on}]",
            "  aliases: 007",
            "  aliases: {a: 007}",
            "  node_id: [007]",
            "  ? [a, b]\n  : 1\n  node_id: 007",
            "  node_id: 007\n  node_id: 1.10",
            "  relationships:\n    - predicate: depends_on\n      object: 007\n      object: 1.10",
        ]
        for lines in shapes:
            with self.subTest(lines):
                self.add("a.md", lines)
                self.graph_meta("a.md")
                self.build()
                self.graph_findings()
        self.add("a.md", "  aliases: 007")
        self.assertEqual(self.graph_meta("a.md")["graph"]["aliases"], "007")
        self.add("a.md", "  node_id: 007\n  node_id: 1.10")
        self.assertEqual(self.graph_meta("a.md")["graph"]["node_id"], "1.10")

    def test_nfd_reference_is_still_normalized(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "concept:ガ")
        self.add("a.md", "  relationships:\n" + relation(object=nfd))
        rel = self.graph_meta("a.md")["graph"]["relationships"][0]
        self.assertEqual(rel["object"], unicodedata.normalize("NFC", "concept:ガ"))


@unittest.skipUnless(HAS_YAML, "PyYAML が要る")
class UnreadableGraphTest(WikiCase):
    """`graph:` を書いたのに読めなかったページを、黙らずに診断に挙げる。"""

    GRAPH = "graph:\n  relationships:\n" + relation()

    def setUp(self):
        super().setUp()
        write(self.wiki / "other.md", page('type: "concept"'))
        write(self.wiki / "s.md", SOURCE_PAGE)

    def unreadable(self):
        _nodes, _edges, diagnostics, _aliases = self.build()
        return [d for d in diagnostics if d["kind"] == "unreadable_graph"]

    def test_yaml_error_keeps_top_level_and_reports_the_graph(self):
        write(self.wiki / "a.md", page("title: a: b\ntype: concept\nsources: [s]\n" + self.GRAPH))
        meta = self.graph_meta("a.md")
        self.assertEqual((meta["title"], meta["type"], meta["sources"]), ("a: b", "concept", ["s"]))
        self.assertNotIn("graph", meta)
        nodes, edges, diagnostics, _aliases = self.build()
        self.assertIn("concept:a", {n["id"] for n in nodes})
        self.assertEqual([(e["predicate"], e["object"]) for e in edges if e["subject"] == "concept:a"],
                         [("sourced_from", "source:s")])
        self.assertEqual(diagnostics, [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])
        findings = self.graph_findings()
        self.assertEqual(findings["unreadable_graph"], [{"page": "a.md", "reason": "yaml_error"}])
        self.assertEqual(findings["summary"]["unreadable_graph"], 1)

    def test_quoted_graph_key_in_unreadable_yaml(self):
        # lint のパーサーは "graph": のキーを読まないが、読める YAML なら graph として読む書き方なので、見落とさない。
        for key in ('"graph"', "'graph'", "graph "):
            with self.subTest(key):
                write(self.wiki / "a.md", page(f"title: a: b\ntype: concept\n{key}:\n  node_id: x"))
                self.assertEqual(self.unreadable(),
                                 [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])

    def test_values_pyyaml_cannot_construct_inside_graph(self):
        # graph の中の値を組み立てられないときは、止まらずに、読めなかったと挙げる。
        for lines in ("  node_id: !!float nope", "  relationships:\n" + relation(valid_from="2026-13-01"),
                      "  ? [a, b]\n  : 1", "  node_id: !!int x"):
            with self.subTest(lines):
                write(self.wiki / "a.md", page("type: concept\nsources: [s]\ngraph:\n" + lines))
                meta = self.graph_meta("a.md")
                self.assertEqual((meta["type"], meta["sources"]), ("concept", ["s"]))
                self.assertNotIn("graph", meta)
                self.assertEqual(self.unreadable(),
                                 [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])
                self.graph_findings()

    def test_characters_yaml_cannot_read(self):
        # YAML に書けない文字（NUL、DEL、C1 の制御文字）があると、PyYAML はローダーを作るところで失敗する。止まらない。
        for ch in ("\x00", "\x7f", "\x80"):
            with self.subTest(repr(ch)):
                write(self.wiki / "a.md", page(f'type: "concept"\ntitle: "a{ch}b"\nsources: ["s"]\ngraph: {{}}'))
                meta = self.graph_meta("a.md")
                self.assertEqual((meta["type"], meta["sources"]), ("concept", ["s"]))
                self.assertEqual(self.unreadable(),
                                 [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])
                self.graph_findings()
                write(self.wiki / "a.md", page(f'type: "concept"\ntitle: "a{ch}b"'))
                self.assertEqual(self.unreadable(), [])
                self.assertEqual(self.cli("wiki_graph_lint.py", "--json").returncode, 0)

    def test_top_level_that_is_not_a_mapping(self):
        write(self.wiki / "a.md", page("type:concept\ngraph:x"))
        self.assertEqual(self.graph_meta("a.md")["type"], "concept")
        self.assertEqual(self.unreadable(), [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])

    def test_tab_after_colon(self):
        write(self.wiki / "a.md", page("type:\tconcept\n" + self.GRAPH))
        self.assertEqual(self.graph_meta("a.md")["type"], "concept")
        self.assertEqual(self.unreadable(), [{"kind": "unreadable_graph", "page": "a.md", "reason": "yaml_error"}])

    def test_graph_that_is_not_a_mapping(self):
        for value in ("x", "[a, b]", "007", "true", '""'):
            with self.subTest(value):
                write(self.wiki / "a.md", page(f"type: concept\ngraph: {value}"))
                self.assertNotIn("graph", self.graph_meta("a.md"))
                self.assertEqual(self.unreadable(),
                                 [{"kind": "unreadable_graph", "page": "a.md", "reason": "not_mapping"}])

    def test_graph_block_list(self):
        write(self.wiki / "a.md", page("type: concept\ngraph:\n  - a\n  - b"))
        self.assertNotIn("graph", self.graph_meta("a.md"))
        self.assertEqual(self.unreadable(), [{"kind": "unreadable_graph", "page": "a.md", "reason": "not_mapping"}])

    def test_empty_or_absent_graph_is_not_reported(self):
        for frontmatter in ("type: concept\ngraph:", "type: concept\ngraph: null", "type: concept\ngraph: {}",
                            "type: concept", "title: a: b\ntype: concept"):
            with self.subTest(frontmatter):
                write(self.wiki / "a.md", page(frontmatter))
                self.assertEqual(self.unreadable(), [])
                self.assertEqual(self.graph_findings()["unreadable_graph"], [])

    def test_readable_graph_is_not_reported(self):
        write(self.wiki / "a.md", page("type: concept\n" + self.GRAPH))
        self.assertEqual(self.unreadable(), [])
        self.assertEqual(len([e for e in self.build()[1] if e["predicate"] == "depends_on"]), 1)

    def test_page_without_frontmatter(self):
        write(self.wiki / "a.md", "graph: x\n本文\n")
        self.assertEqual(self.graph_meta("a.md"), {})
        self.assertEqual(self.unreadable(), [])

    def test_cli_reports_it(self):
        write(self.wiki / "a.md", page("title: a: b\ntype: concept\n" + self.GRAPH))
        proc = self.cli("wiki_graph_lint.py", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        findings = json.loads(proc.stdout)
        self.assertEqual(findings["unreadable_graph"], [{"page": "a.md", "reason": "yaml_error"}])
        text = self.cli("wiki_graph_lint.py").stdout
        self.assertIn("a.md", text)
        self.assertIn("graph: を読めなかった", text)
        proc = self.cli("wiki_graph_extract.py", "--formats", "jsonl")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("診断", proc.stderr)
        self.assertIn(extract.DIAGNOSTIC_LABELS["unreadable_graph"], proc.stderr)


if __name__ == "__main__":
    unittest.main()
