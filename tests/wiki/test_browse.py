"""閲覧（browse）の中核と静的の書き出しの試験。

設計は `docs/plans/wiki-browse-stage1-2026-11-09.md`。試験は設計の「守ること」に沿って並べる。関係表の試験は
PyYAML がなければ飛ばす。Linux でしか作れない名前（NFC と NFD、`x.md` と `x.MD`、`a\\b.md`）の試験は、
その OS でだけ流す。サーバーの試験は `tests/wiki/test_browse_server.py` にある。

実行:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py -v
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
CORPUS = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import wiki_browse  # noqa: E402
import wiki_browse_core as core  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402
import wiki_lint  # noqa: E402
import wiki_pages  # noqa: E402

HAS_YAML = core.wiki_graph_extract is not None
LINUX = sys.platform.startswith("linux")


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def page(body: str, **meta) -> str:
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()] + ["---", "", body, ""]
    return "\n".join(lines)


def tree_state(root: Path) -> dict:
    state = {}
    for p in sorted(root.rglob("*")):
        state[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return state


def lint_broken(root: Path) -> list:
    pages = [p for p in wiki_lint.collect_pages(root) if "read_error" not in p]
    findings = wiki_lint.lint(pages, 10000, 25000, [], False, 3)
    return sorted((f["from_path"], f["to"]) for f in findings["broken_links"])


def build_core(root: Path) -> core.Core:
    return core.Core(core.take_snapshot(root))


class TempWiki(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.wiki = self.base / "work" / "Wiki"
        self.wiki.mkdir(parents=True)
        self.data = self.base / "data"
        self._env = mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.data)})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def build(self, out=None, raw=None) -> dict:
        with redirect_stderr(io.StringIO()):
            return wiki_browse.build(self.wiki, None if out is None else str(out), raw)


# ---------------------------------------------------------------------------
# 守ること 2: lint と同じ判定
# ---------------------------------------------------------------------------

class LintAgreementTest(TempWiki):
    def test_unresolved_matches_lint_broken_links(self):
        write(self.wiki, "concepts/a.md", page("# A\n\n[[b]] [[missing]] [[concepts/b]] [[entities/b]] [[]] [[b#x]]",
                                               type="concept"))
        write(self.wiki, "concepts/b.md", page("# B\n\n[[a|エー]] [[nowhere|どこ]]", type="concept"))
        write(self.wiki, "entities/b.md", page("# B2", type="entity"))
        write(self.wiki, "index.md", "# 索引\n\n- [[a]]\n")
        c = build_core(self.wiki)
        self.assertEqual(c.unresolved(), lint_broken(self.wiki))

    def test_corpus_matches_lint(self):
        if not CORPUS.is_dir():
            self.skipTest("評価のコーパスがない")
        c = build_core(CORPUS)
        self.assertEqual(c.unresolved(), lint_broken(CORPUS))
        for pid, disk in c.drawn.items():
            self.assertEqual(c.link_targets(pid), wiki_pages.extract_wikilinks(c.pages[disk]["body"]), pid)

    def test_drawn_links_equal_extract_wikilinks(self):
        body = ("# 見出し [[h]]\n\n| a | b |\n| --- | --- |\n| [[t\\|別名]] | `[[code]]` |\n\n"
                "```\n[[fence]]\n```\n\n\\[\\[escaped]] [[R&amp;D]] [文字 [[inlink]]](https://example.invalid/) "
                "![画像 [[alt]]](x.png)\n\n    [[indented]]\n")
        write(self.wiki, "a.md", page(body, type="concept"))
        c = build_core(self.wiki)
        expected = wiki_pages.extract_wikilinks(c.pages["a.md"]["body"])
        self.assertEqual(c.link_targets("a"), expected)
        html = c.render_page("a")
        drawn = html.count('class="wl')
        self.assertEqual(drawn, len(expected))
        self.assertNotIn("<a href=\"https://example.invalid/\"", html)   # 中に wikilink のある外部リンクはリンクにしない
        self.assertEqual(html.count("<a "), html.count("</a>"))

    def test_cr_only_newlines_are_read_like_lint(self):
        text = '---\rtype: "concept"\rsources: ["[[missing]]"]\r---\rbody [[existing]]\r'
        (self.wiki / "a.md").write_bytes(text.encode("utf-8"))
        write(self.wiki, "existing.md", page("# E"))
        c = build_core(self.wiki)
        self.assertEqual(c.link_targets("a"), ["existing"])
        self.assertEqual(c.page("a")["meta"].get("type"), "concept")
        self.assertEqual(c.unresolved(), lint_broken(self.wiki))

    def test_same_slug_is_ambiguous_but_path_resolves(self):
        write(self.wiki, "concepts/x.md", page("# X1"))
        write(self.wiki, "entities/x.md", page("# X2"))
        write(self.wiki, "a.md", page("[[x]] [[concepts/x]]"))
        c = build_core(self.wiki)
        states = [r["state"] for r in c.links["a"]]
        self.assertEqual(states, ["ambiguous", "resolved"])
        self.assertIn("concepts/x", c.drawn)
        self.assertIn("entities/x", c.drawn)

    def test_sources_forms_resolve_like_lint(self):
        write(self.wiki, "sources/paper.md", page("# P", type="source"))
        for i, ref in enumerate(["paper", "sources/paper", "[[sources/paper]]"]):
            write(self.wiki, f"c{i}.md", page("# C", type="concept", sources=[ref]))
        c = build_core(self.wiki)
        for i in range(3):
            html = c.render_page(f"c{i}")
            self.assertIn('href="sources/paper.html"', html, i)

    @unittest.skipUnless(LINUX, "Linux でだけ同時に置ける名前")
    def test_id_collisions(self):
        write(self.wiki, "concepts/x.md", page("# lower"))
        write(self.wiki, "concepts/x.MD", page("# upper"))
        write(self.wiki, "concepts/a\\b.md", page("# backslash"))
        write(self.wiki, "concepts/a/b.md", page("# slash"))
        nfd = unicodedata.normalize("NFD", "concepts/が")
        write(self.wiki, "concepts/が.md", page("# nfc"))
        write(self.wiki, nfd + ".md", page("# nfd"))
        write(self.wiki, "r.md", page("[[concepts/x]] [[b]] [[concepts/が]]"))
        write(self.wiki, "concepts/x.md", page("# lower\n\n[[missing-from-hidden]]"))
        c = build_core(self.wiki)
        self.assertEqual(c.unresolved(), lint_broken(self.wiki))
        self.assertIn(("concepts/x.md", "missing-from-hidden"), c.unresolved())
        for pid in ("concepts/x", "concepts/a/b", "concepts/が"):
            self.assertNotIn(pid, c.drawn)
        self.assertEqual([r["state"] for r in c.links["r"]], ["ambiguous"] * 3)
        kinds = [d for d in c.diagnostics if d["kind"] == "id_collision"]
        self.assertEqual(len(kinds), 3)
        self.assertNotIn("a/b.html", c.render_page("r"))

    @unittest.skipUnless(LINUX, "Linux でだけ置けるファイル名")
    def test_backslash_filename_stays_inside_output(self):
        site1 = self.base / "site1"
        site1.mkdir()
        (site1 / "a.html").write_bytes(b"keep")
        write(self.wiki, "\\" + str(site1).lstrip("/").replace("/", "\\") + "\\a.md", page("# evil"))
        with redirect_stderr(io.StringIO()):
            report = wiki_browse.build(self.wiki, str(self.base / "site2"), None)
        self.assertEqual((site1 / "a.html").read_bytes(), b"keep")
        self.assertEqual(sorted(p.name for p in site1.iterdir()), ["a.html"])
        out = Path(report["out"])
        for f in out.rglob("*.html"):
            self.assertTrue(fs.is_within(f, out))

    @unittest.skipUnless(LINUX and hasattr(os, "geteuid") and os.geteuid() != 0, "読めないファイルを作れる環境だけ")
    def test_unreadable_collision_member_is_ignored(self):
        write(self.wiki, "concepts/x.md", page("# lower"))
        upper = write(self.wiki, "concepts/x.MD", page("# upper"))
        write(self.wiki, "r.md", page("[[concepts/x]]"))
        upper.chmod(0)
        try:
            c = build_core(self.wiki)
            self.assertIn("concepts/x", c.drawn)
            self.assertEqual(c.links["r"][0]["state"], "resolved")
            self.assertEqual(c.unresolved(), lint_broken(self.wiki))
        finally:
            upper.chmod(0o644)


# ---------------------------------------------------------------------------
# 中核の規則（出力の名前、見出し、描画、ナビゲーション、raw）
# ---------------------------------------------------------------------------

class NamesTest(unittest.TestCase):
    def test_reserved_names(self):
        for name in ("CON", "con", "COM0", "COM¹", "LPT²", "CONIN$", "CONOUT$", "nul.txt", "COM9 "):
            out = core.export_name(f"x/{name}")
            last = out.split("/")[-1]
            self.assertFalse(core.is_reserved_windows(last[:-len(".html")]), (name, out))
            self.assertIn("~", last, name)

    def test_generator_names_are_avoided(self):
        for pid in ("index", "data/x", "assets/x", ".browse-generation/a", "x/.browse-work/b"):
            out = core.export_name(pid)
            self.assertNotEqual(out, pid + ".html", pid)
        names = core.assign_names(["index", "nav", "data/x", "assets/x"])
        self.assertEqual(len(set(n.casefold() for n in names.values())), 4)
        self.assertFalse({"index.html", "nav.js"} & set(names.values()))

    def test_names_stay_relative(self):
        # Linux の `\\tmp\\x\\a.md` は、/ にそろえると先頭が空の要素になる（実装のレビュー 1 の致命 1）。
        for pid in ("/tmp/x/a", "a/../b", "a/./b", "..", "a//b", "./a"):
            name = core.export_name(pid)
            self.assertTrue(core.is_safe_relative(name), (pid, name))
        names = core.assign_names(["/tmp/x/a", "tmp/x/a"])
        self.assertEqual(len(set(names.values())), 2)
        self.assertTrue(all(core.is_safe_relative(n) for n in names.values()))

    def test_case_only_collisions_get_suffixes(self):
        names = core.assign_names(["a/Foo", "a/foo"])
        self.assertNotEqual(names["a/Foo"].casefold(), names["a/foo"].casefold())

    def test_eight_digit_suffix_collision_extends_digits(self):
        a = "concepts/" + "p" * 186 + "-23280"
        b = "concepts/" + "p" * 186 + "-87547"
        self.assertEqual(core.short_hash(a + ""), core.short_hash(a))
        names = core.assign_names([a, b])
        self.assertNotEqual(names[a].casefold(), names[b].casefold())
        for n in names.values():
            for part in n.split("/"):
                self.assertLessEqual(len(part.encode("utf-8")), core.NAME_LIMIT, n)


class RenderTest(TempWiki):
    def test_headings(self):
        write(self.wiki, "a.md", page("# nav\n\n## **Definition**\n\n## [[other|Definition]]\n\n"
                                      "## ![Definition](d.png)\n\n## 例\n\n## 例\n\n## 例-1\n"))
        write(self.wiki, "other.md", page("# O"))
        write(self.wiki, "r.md", page("[[a#Definition]] [[a#例-1]] [[a#ない]]"))
        c = build_core(self.wiki)
        ids = [hid for _k, hid, _t in c.headings["a"]]
        self.assertEqual(ids, ["nav", "definition", "definition-1", "definition-2", "例", "例-1", "例-1-1"])
        links = c.links["r"]
        self.assertEqual(links[0]["anchor"], "definition")
        self.assertEqual(links[1]["anchor"], "例-1-1")
        self.assertEqual(links[2].get("missing_heading"), "ない")
        html = c.render_page("a")
        self.assertEqual(html.count('id="nav"'), 1)
        self.assertIn('id="_nav"', html)

    def test_heading_with_markdown_link(self):
        write(self.wiki, "a.md", page("## [X](target)\n\n## [外](https://example.invalid/)\n"))
        write(self.wiki, "r.md", page("[[a#X（target）]] [[a#外]]"))
        c = build_core(self.wiki)
        self.assertEqual([r.get("anchor") for r in c.links["r"]], ["x（target）", "外"])   # 全角の括弧は鍵に残る
        self.assertIn("X（target）", c.render_page("a"))

    def test_unparsable_raw_url_renders(self):
        write(self.wiki, "a.md", page("# A", type="source", raw="http://["))
        c = build_core(self.wiki)
        for mode in core.RAW_MODES:
            c.render_page("a", mode)
        self.assertEqual(core.classify_raw("http://[")["kind"], "url")

    def test_links_and_escaping(self):
        write(self.wiki, "a.md", page("[外](https://example.invalid/) [内](rel/x.md) <https://auto.invalid/> "
                                      "[ [[missing]] ](https://example.invalid/) <script>alert(1)</script>\n\n"
                                      "| l | r |\n| :--- | ---: |\n| 1 | 2 |\n",
                                      title="<script>t</script>", tags=["<b>"]))
        c = build_core(self.wiki)
        html = c.render_page("a")
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertNotIn('href="rel/x.md"', html)
        self.assertIn("（rel/x.md）", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<script>t", html)
        self.assertNotIn("<b>", html)
        self.assertNotIn("style=", html)
        self.assertIn('class="ta-right"', html)
        self.assertIn('<meta name="referrer" content="no-referrer">', html)
        # 未解決の wikilink が外側のリンクでクリックできるようにならない
        start = html.index("wl-unresolved")
        self.assertGreater(html.rfind("</a>", 0, start), html.rfind("<a ", 0, start))

    def test_raw_kinds_and_modes(self):
        self.assertEqual(core.classify_raw("file:///C:/Books/private.pdf"),
                         {"kind": "absolute", "value": "C:/Books/private.pdf"})
        self.assertEqual(core.classify_raw("~/x.pdf")["kind"], "absolute")
        self.assertEqual(core.classify_raw("/home/u/x.pdf")["kind"], "absolute")
        self.assertEqual(core.classify_raw("https://e.invalid/x")["kind"], "url")
        self.assertEqual(core.classify_raw("../raw/x.md")["kind"], "relative")
        write(self.wiki, "s.md", page("# S", type="source", raw="file:///C:/Books/private.pdf", raw_sha256="ab" * 32))
        c = build_core(self.wiki)
        self.assertNotIn("C:/Books", c.render_page("s", "basename"))
        self.assertIn("private.pdf", c.render_page("s", "basename"))
        self.assertNotIn("private.pdf", c.render_page("s", "none"))
        self.assertIn('href="file:///C:/Books/private.pdf"', c.render_page("s", "link"))
        self.assertIn("<code>C:/Books/private.pdf</code>", c.render_page("s", "text"))

    def test_navigation(self):
        write(self.wiki, "index.md", "- [[pre]]\n\n# 上\n\n## 概念\n\n- [[a]] — 説明 [[b]]\n  - [[b]]\n"
                                     "- [[missing]] — 関連：[[a]]\n- [[indexes/people]]\n- 説明だけ\n")
        write(self.wiki, "indexes/people.md", page("- [[p]]", title="人物"))
        for name in ("pre", "a", "b", "p", "lone"):
            write(self.wiki, f"{name}.md", page(f"# {name}", type="concept"))
        c = build_core(self.wiki)
        nav = c._nav_json()["groups"]
        top = nav[0]
        self.assertEqual(top["items"][0]["path"], "pre.html")
        concepts = top["children"][0]["children"][0]
        self.assertEqual(concepts["title"], "概念")
        states = [(i["state"], i["label"]) for i in concepts["items"]]
        self.assertEqual(states, [("resolved", "a"), ("resolved", "b"), ("unresolved", "missing"),
                                  ("group", "indexes/people")])
        people = nav[1]
        self.assertEqual(people["title"], "人物")
        rest = nav[-1]
        self.assertEqual(rest["title"], "索引にないページ")
        self.assertEqual([i["path"] for g in rest["children"] for i in g["items"]], ["lone.html"])


# ---------------------------------------------------------------------------
# 関係表（PyYAML が要る）
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_YAML, "PyYAML がない")
class RelationsTest(TempWiki):
    ONTOLOGY = "node_types:\n  concept: {}\n  source: {}\npredicates:\n  uses: {}\n"

    def setUp(self):
        super().setUp()
        write(self.wiki, "graph/ontology.yaml", self.ONTOLOGY)

    def rel(self, c, pid, direction):
        return [(r["predicate"], r["other_id"] or r["other_text"], r.get("status")) for r in c.relations[pid][direction]]

    def test_same_slug_pages_keep_their_own_relations(self):
        rel = {"graph": {"relationships": [{"predicate": "uses", "object": "concept:y"}]}}
        write(self.wiki, "concepts/x.md", "---\ntype: concept\ngraph:\n  relationships:\n"
                                         "    - predicate: uses\n      object: concept:y\n---\n# X\n")
        write(self.wiki, "entities/x.md", "---\ntype: concept\ngraph:\n  node_id: person:x\n---\n# EX\n")
        write(self.wiki, "concepts/y.md", "---\ntype: concept\n---\n# Y\n")
        c = build_core(self.wiki)
        self.assertEqual(c.relations_state, "ok")
        self.assertEqual(self.rel(c, "concepts/x", "out"), [("uses", "concepts/y", "")])
        self.assertEqual(self.rel(c, "entities/x", "out"), [])
        self.assertEqual(self.rel(c, "concepts/y", "in"), [("uses", "concepts/x", "")])
        self.assertTrue(rel)

    def test_period_variants_and_duplicate_node_id(self):
        write(self.wiki, "a.md", "---\ntype: concept\ngraph:\n  relationships:\n"
                                 "    - {predicate: uses, object: 'concept:y', status: historical, valid_from: 2020-01-01}\n"
                                 "    - {predicate: uses, object: 'concept:y', status: current, valid_from: 2024-01-01}\n"
                                 "    - {predicate: uses, object: 'concept:shared'}\n---\n# A\n")
        write(self.wiki, "y.md", "---\ntype: concept\n---\n# Y\n")
        write(self.wiki, "s1.md", "---\ntype: concept\ngraph:\n  node_id: concept:shared\n---\n# S1\n")
        write(self.wiki, "s2.md", "---\ntype: concept\ngraph:\n  node_id: concept:shared\n---\n# S2\n")
        c = build_core(self.wiki)
        self.assertEqual(sorted(s for _p, _o, s in self.rel(c, "y", "in")), ["current", "historical"])
        self.assertEqual(c.relations["s1"]["in"], [])
        self.assertEqual(c.relations["s2"]["in"], [])
        for pid in ("s1", "s2"):
            self.assertIn("duplicate_node_id", [d["kind"] for d in c.page_diagnostics(pid)])

    def test_sources_ambiguity_and_yaml_typed_values(self):
        # 既定のノード ID はどちらも source:paper になり、同じノードを共有する。入ってくる関係はどちらにも出ない。
        write(self.wiki, "sources/left/paper.md", page("# L", type="source"))
        write(self.wiki, "sources/right/paper.md", page("# R", type="source"))
        write(self.wiki, "sources/own/doc.md", "---\ntype: source\ngraph:\n  node_id: source:own\n---\n# O\n")
        write(self.wiki, "sources/other/doc.md", "---\ntype: source\ngraph:\n  node_id: source:other\n---\n# O2\n")
        write(self.wiki, "d.md", page("# D", type="concept", sources=["sources/own/doc"]))
        write(self.wiki, "true.md", page("# T", type="source"))
        write(self.wiki, "a.md", page("# A", type="concept", sources=["paper"]))
        write(self.wiki, "b.md", page("# B", type="concept", sources=["sources/left/paper"]))
        (self.wiki / "c.md").write_bytes(b'---\ntype: "concept"\nsources: [true]\n---\n# C\n')
        c = build_core(self.wiki)
        self.assertIn("ambiguous_source", [d["kind"] for d in c.page_diagnostics("a")])
        self.assertEqual(c.relations["sources/left/paper"]["in"], [])
        self.assertEqual(c.relations["sources/right/paper"]["in"], [])
        self.assertIn("duplicate_node_id", [d["kind"] for d in c.page_diagnostics("sources/left/paper")])
        self.assertEqual([r["predicate"] for r in c.relations["b"]["out"]], ["sourced_from"])
        self.assertEqual([r["other_id"] for r in c.relations["sources/own/doc"]["in"]], ["d"])
        self.assertEqual(c.relations["sources/other/doc"]["in"], [])
        self.assertEqual([r["other_id"] for r in c.relations["true"]["in"]], ["c"])
        self.assertNotIn("unresolved_source", [d["kind"] for d in c.page_diagnostics("c")])
        self.assertIn('href="true.html"', c.render_page("c"))

    def test_relation_source_is_linked(self):
        write(self.wiki, "a.md", "---\ntype: concept\ngraph:\n  relationships:\n"
                                 "    - {predicate: uses, object: 'concept:y', source: paper}\n---\n# A\n")
        write(self.wiki, "y.md", "---\ntype: concept\n---\n# Y\n")
        write(self.wiki, "sources/paper.md", page("# P", type="source", title="論文"))
        html = build_core(self.wiki).render_page("a")
        self.assertIn('href="sources/paper.html">論文</a>', html)

    def test_states(self):
        write(self.wiki, "a.md", page("# A", type="concept"))
        self.assertIn("関係はない", build_core(self.wiki).render_page("a"))
        write(self.wiki, "graph/ontology.yaml", "- not a mapping\n")
        c = build_core(self.wiki)
        self.assertEqual(c.relations_state, "error")
        self.assertIn("オントロジーを読めない", c.render_page("a"))
        write(self.wiki, "graph/ontology.yaml", "node_types: []\npredicates: {}\n")
        c = build_core(self.wiki)   # 中の形が誤っていても、中核は組み立てられ、関係表だけが使えない
        self.assertEqual(c.relations_state, "error")
        self.assertIn("オントロジーを読めない", c.render_page("a"))
        (self.wiki / "graph/ontology.yaml").unlink()
        c = build_core(self.wiki)
        self.assertEqual(c.relations_state, "none")
        self.assertNotIn("_relations", c.render_page("a"))


# ---------------------------------------------------------------------------
# 静的の書き出し（守ること 1、4、8）
# ---------------------------------------------------------------------------

class BuildTest(TempWiki):
    def setUp(self):
        super().setUp()
        write(self.wiki, "concepts/a.md", page("# A\n\n[[b]]", type="concept"))
        write(self.wiki, "concepts/b.md", page("# B", type="concept"))

    def test_default_build_and_read_only(self):
        before = tree_state(self.wiki)
        report = self.build()
        out = Path(report["out"])
        self.assertTrue((out / "concepts/a.html").is_file())
        self.assertTrue((out / fs.GENERATION_MARKER).is_file())
        self.assertTrue((out / "assets/app.js").is_file())
        self.assertEqual(tree_state(self.wiki), before)
        # 2 度目は前の世代と入れ替わる
        (self.wiki / "concepts/b.md").unlink()
        report2 = self.build()
        self.assertFalse((out / "concepts/b.html").exists())
        self.assertNotEqual(report["generation"], report2["generation"])
        self.assertEqual(wiki_browse._generation_dirs(Path(str(out) + ".browse-work"), "old-"), [])

    def test_refused_destinations(self):
        before = tree_state(self.wiki)
        for out in (self.wiki / "preview", self.wiki, self.base / "work", self.data / "browse" / "x"):
            with self.assertRaises((fs.Refused, wiki_browse.Failed), msg=str(out)):
                self.build(out)
        stray = self.base / "stray"
        stray.mkdir()
        (stray / "x.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(fs.Refused):
            self.build(stray)
        with self.assertRaises(wiki_browse.Failed):
            self.build(self.base / "no-parent" / "out")
        self.assertEqual(tree_state(self.wiki), before)

    def test_sibling_and_empty_destination(self):
        view = self.base / "work" / "view"
        view.mkdir()
        report = self.build(view)
        self.assertTrue((view / "index.html").is_file())
        self.assertEqual(report["raw"], "basename")

    def test_nested_outputs_are_refused(self):
        site = self.base / "exports" / "site"
        site.parent.mkdir()
        self.build(site)
        with self.assertRaises(fs.Refused):
            self.build(site / "nested")
        with self.assertRaises(fs.Refused):
            self.build(self.base / "exports")

    def test_recovery_picks_highest_published_seq(self):
        out = self.base / "site"
        self.build(out)
        self.build(out)
        work = Path(str(out) + ".browse-work")
        first = (out / ".browse-generation").read_text(encoding="utf-8")
        self.assertEqual(json.loads(first)["published_seq"], 2)
        # 入れ替えの途中で止まった形を作る: 出力先がなく、old が 3 つ、tmp が 1 つある。
        os.rename(out, work / "old-5")
        for seq in (0, 1):
            (work / f"old-{seq}").mkdir()
            (work / f"old-{seq}" / fs.GENERATION_MARKER).write_text(json.dumps({"published_seq": seq}),
                                                                    encoding="utf-8")
        (work / "tmp-9").mkdir()
        (work / "tmp-9" / fs.GENERATION_MARKER).write_text("{}", encoding="utf-8")
        (work / "old-x").mkdir()   # 目印のないものは戻さず、消さない
        json.loads(first)
        with redirect_stderr(io.StringIO()):
            wiki_browse.cleanup(fs.Guard([self.wiki]), out, work)
        self.assertEqual((out / ".browse-generation").read_text(encoding="utf-8"), first)
        self.assertEqual(sorted(p.name for p in work.iterdir() if p.is_dir()), ["old-x"])

    def test_recovery_into_empty_output_dir(self):
        out = self.base / "site"
        self.build(out)
        work = Path(str(out) + ".browse-work")
        first = (out / ".browse-generation").read_text(encoding="utf-8")
        os.rename(out, work / "old-1")
        out.mkdir()   # 再実行するラッパーなどが、空の出力先を作り直した
        with redirect_stderr(io.StringIO()):
            wiki_browse.cleanup(fs.Guard([self.wiki]), out, work)
        self.assertEqual((out / ".browse-generation").read_text(encoding="utf-8"), first)
        self.assertEqual(wiki_browse._generation_dirs(work, "old-"), [])

    def test_failed_core_leaves_no_tmp_and_keeps_error(self):
        out = self.base / "site"
        self.build(out)
        before = (out / "index.html").read_bytes()
        with mock.patch.object(core.Core, "__init__", side_effect=core.NameCollision("x")):
            with self.assertRaises(core.NameCollision):
                self.build(out)
        self.assertEqual((out / "index.html").read_bytes(), before)
        work = Path(str(out) + ".browse-work")
        self.assertEqual([p.name for p in work.iterdir() if p.is_dir()], [])

    def test_empty_seq_file_continues_from_markers(self):
        out = self.base / "site"
        self.build(out)
        work = Path(str(out) + ".browse-work")
        (work / "seq").write_bytes(b"")
        self.build(out)
        self.assertEqual(json.loads((out / ".browse-generation").read_text(encoding="utf-8"))["published_seq"], 2)

    def test_generator_leak_fails_and_keeps_previous(self):
        out = self.base / "site"
        self.build(out)
        before = (out / "index.html").read_bytes()
        original = core.Core.render_index

        def leaky(self_, stale=None):
            return original(self_, stale) + f"<!-- {self_.snapshot.root} -->"
        with mock.patch.object(core.Core, "render_index", leaky):
            write(self.wiki, "concepts/c.md", page("# C"))
            with self.assertRaises(wiki_browse.Failed):
                self.build(out)
        self.assertEqual((out / "index.html").read_bytes(), before)
        self.assertEqual(wiki_browse._generation_dirs(Path(str(out) + ".browse-work"), "tmp-"), [])

    def test_leak_forms_are_detected(self):
        root = "C:\\Users\\Alice\\Wiki"
        for leak in (root, root.replace("\\", "/"), json.dumps(root)[1:-1], "C%3A%2FUsers%2FAlice%2FWiki"):
            leaks, _w = core.find_leaks({"a.html": f"x {leak} y"}, [root], core.Recorder())
            self.assertEqual(leaks, ["a.html"], leak)

    def test_each_needle_is_judged(self):
        rec = core.Recorder()
        rec.add("a.html", "C:/private-WIKI")
        leaks, warnings = core.find_leaks({"a.html": "C:/private-WIKI D:/private-HOME"},
                                          ["C:/private-WIKI", "D:/private-HOME"], rec)
        self.assertEqual(leaks, ["a.html"])
        self.assertEqual(warnings, [])

    def test_generator_reason_is_not_user_content(self):
        write(self.wiki, "graph/ontology.yaml", "- x\n")
        original = core.Core._relations

        def leaky(self_):
            original(self_)
            self_.diagnostics.append({"kind": "relations_error", "reason": str(self_.snapshot.root)})
        with mock.patch.object(core.Core, "_relations", leaky):
            with self.assertRaises(wiki_browse.Failed):
                self.build(self.base / "site")

    def test_title_with_home_path_is_a_warning(self):
        home = str(Path.home())
        write(self.wiki, "sources/s.md", page("# S", type="source", title=home))
        write(self.wiki, "concepts/r.md", page("# R", type="concept", sources=["s"]))
        report = self.build(self.base / "site")
        self.assertEqual(report["leaks"], [])
        self.assertIn("concepts/r.html", report["warnings"])

    def test_tilde_raw_builds_with_default_link_mode(self):
        write(self.wiki, "sources/s.md", page("# S", type="source", raw="~/papers/x.pdf"))
        report = self.build()   # 既定の書き出し先は link（~ をホームに展開した file:/// のリンク）
        self.assertEqual(report["leaks"], [])
        html = (Path(report["out"]) / "sources/s.html").read_text(encoding="utf-8")
        self.assertIn("file://", html)

    def test_user_written_path_is_a_warning(self):
        home = str(Path.home())
        write(self.wiki, "concepts/h.md", page(f"# H\n\nホームは `{home}` にある。\n"))
        report = self.build(self.base / "site")
        self.assertEqual(report["leaks"], [])
        self.assertEqual(report["warnings"], ["concepts/h.html"])

    def test_no_absolute_paths_in_output(self):
        write(self.wiki, "concepts/s.md", page("# S", type="source", raw="../raw/x.pdf"))
        report = self.build(self.base / "site")
        out = Path(report["out"])
        needles = [str(self.wiki), self.wiki.as_posix(), str(self.data), self.data.as_posix()]
        for p in out.rglob("*"):
            if p.is_file():
                text = p.read_text(encoding="utf-8", errors="replace")
                for n in needles:
                    self.assertNotIn(n, text, p)

    def test_bytecode_is_not_written_inside_wiki(self):
        plugin = self.wiki / "tools" / "scripts"
        shutil.copytree(SCRIPTS, plugin, ignore=shutil.ignore_patterns("__pycache__"))
        before = tree_state(self.wiki)
        env = {**os.environ, "INFO_HIVE_DATA_DIR": str(self.data)}
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        result = subprocess.run([sys.executable, "-X", "utf8", str(plugin / "wiki_browse.py"), "build",
                                 str(self.wiki), "--out", str(self.base / "site")],
                                capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_state(self.wiki), before)


# ---------------------------------------------------------------------------
# 中核の子プロセスの入出力
# ---------------------------------------------------------------------------

class CoreLoopTest(TempWiki):
    def run_loop(self, *requests) -> list:
        out = io.StringIO()
        wiki_browse.core_loop(io.StringIO("".join(json.dumps(r) + "\n" for r in requests)), out)
        return [json.loads(line) for line in out.getvalue().splitlines()]

    def test_manifest_and_page(self):
        write(self.wiki, "a.md", page("# A"))
        res = self.run_loop({"op": "manifest", "wiki": str(self.wiki)},
                            {"op": "page", "wiki": str(self.wiki), "id": "a", "raw": "text"},
                            {"op": "page", "wiki": str(self.wiki), "id": "nope"},
                            {"op": "x", "wiki": str(self.base / "none")})
        self.assertTrue(res[0]["ok"])
        self.assertEqual(res[0]["pages"][0]["id"], "a")
        self.assertIn("<h1", res[1]["html"])
        self.assertEqual(res[2]["error"], "unknown_page")
        self.assertEqual(res[3]["error"], "no_wiki")
        self.assertNotIn(str(self.wiki), json.dumps(res, ensure_ascii=False))

    def test_unreadable_page_recovers_without_change(self):
        target = write(self.wiki, "a.md", page("# A"))
        real = Path.read_bytes

        def flaky(self_):
            if Path(self_) == target:
                raise PermissionError("busy")
            return real(self_)
        state = {"busy": True}

        def lines():
            line = json.dumps({"op": "manifest", "wiki": str(self.wiki)}) + "\n"
            yield line
            state["busy"] = False   # ファイルを変えずに、読めるようにする
            yield line

        def maybe(self_):
            return flaky(self_) if state["busy"] else real(self_)
        out = io.StringIO()
        with mock.patch.object(Path, "read_bytes", maybe):
            wiki_browse.core_loop(lines(), out)   # 同じプロセス（同じ写しの使い回し）の中で確かめる
        first, second = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(first["pages"], [])
        self.assertEqual([p["id"] for p in second["pages"]], ["a"])


if __name__ == "__main__":
    unittest.main()
