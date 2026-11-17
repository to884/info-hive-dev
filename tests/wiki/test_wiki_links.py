"""ADR-0029（wiki と raw の記事にリンクを置かない）の段階 1 の試験。

- wiki_links: リンクの判定（link_kind）、find_links、CLI の check。
- lint の指摘 links と links_unchecked。リンクなので読まなかったページへの wikilink を、リンク切れにしない。
- 読む側の link_warnings（検索の CLI、統計、MCP の索引の検索、get_page、list_index）と、「ない」ではなく
  「リンクなので読まない」を返すこと。索引を作ったあとでページをリンクに替えても、そのページを返さないこと。
- MCP のサーバーの版（SERVER_FILES）が、サーバーが関数の中で遅れて読み込むものも含め、同梱のモジュールをすべて含むこと。

設計は info-hive-dev の `docs/plans/wiki-links-2026-11-16.md` にある。リンクを作れない環境では、その試験を飛ばす。

実行:
    python -X utf8 -B -m unittest tests/wiki/test_wiki_links.py -v
"""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_links  # noqa: E402
import wiki_lint  # noqa: E402
import wiki_mcp_common  # noqa: E402
import wiki_pages  # noqa: E402
import wiki_stats  # noqa: E402

NT = os.name == "nt"


def page(title: str, body: str = "") -> str:
    return "\n".join(["---", 'type: "concept"', f'title: "{title}"', 'tags: ["t"]', "created: 2026-11-17",
                      "updated: 2026-11-17", "---", "", f"# {title}", "", body, ""])


def junction(path: Path, target: Path) -> bool:
    if NT:
        return subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], capture_output=True).returncode == 0
    try:
        os.symlink(target, path, target_is_directory=True)
        return True
    except OSError:
        return False


def symlink(path: Path, target: Path) -> bool:
    try:
        os.symlink(target, path)
        return True
    except (OSError, NotImplementedError):
        return False


def remove_links(base: Path):
    for directory, dirs, files in os.walk(base, topdown=True):
        for name in list(dirs) + list(files):
            p = os.path.join(directory, name)
            if os.path.islink(p) or getattr(os.lstat(p), "st_reparse_tag", 0):
                if name in dirs:
                    dirs.remove(name)
                try:
                    os.unlink(p)
                except OSError:
                    os.rmdir(p)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="links-"))
        self.wiki = self.tmp / "wiki"
        self.ext = self.tmp / "ext"
        self.wiki.mkdir()
        self.ext.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# s\n", encoding="utf-8")
        self.addCleanup(self.cleanup)

    def cleanup(self):
        import shutil
        remove_links(self.tmp)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, text: str, base: "Path | None" = None) -> Path:
        path = (base or self.wiki) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path


class AssetIntegrationTests(Base):
    """ADR-0030 の図も、共通のリンク判定を使い、記事とは対象を分ける。"""

    def test_regular_and_hardlinked_svg_are_assets(self):
        a = self.write("assets/a.svg", "<svg/>")
        os.link(a, self.wiki / "assets/b.svg")
        found = wiki_pages.walk_assets(self.wiki)
        self.assertEqual([f.rel for f in found.files], ["assets/a.svg", "assets/b.svg"])
        self.assertEqual((found.unlistable, found.unknown), ([], []))

    def test_linked_assets_directory_is_not_descended(self):
        self.write("figures/a.svg", "<svg/>", base=self.ext)
        if not junction(self.wiki / "assets", self.ext / "figures"):
            self.skipTest("リンクを作れない")
        with mock.patch.object(wiki_pages, "_list_dir", wraps=wiki_pages._list_dir) as listing:
            self.assertEqual(wiki_pages.walk_assets(self.wiki).files, [])
        self.assertEqual([os.fspath(c.args[0]) for c in listing.call_args_list], [str(self.wiki)])

    def test_unverified_assets_directory_is_reported(self):
        self.write("assets/a.svg", "<svg/>")
        with mock.patch.object(wiki_pages, "_stat_entry", return_value=("denied", None)):
            found = wiki_pages.walk_assets(self.wiki)
        self.assertEqual((found.files, found.unknown), ([], ["assets"]))


class IntegrationReviewTests(Base):
    def test_external_alias_never_resolves_through_a_forbidden_wiki_directory(self):
        self.write("outside/a.md", "OUTSIDE", base=self.ext)
        jump = self.wiki / "concepts/jump"
        jump.parent.mkdir()
        if not junction(jump, self.ext / "outside"):
            self.skipTest("リンクを作れない")
        view = self.tmp / "view"
        if not junction(view, jump):
            self.skipTest("リンクを作れない")
        for path in (jump / "a.md", view / "a.md"):
            with self.subTest(path=str(path)), self.assertRaisesRegex(ValueError, "リンクなので読まない"):
                wiki_pages.read_user_bytes(path, self.wiki)
        self.assertEqual(wiki_pages.source_wiki_root(view, self.wiki), self.wiki)

    def test_external_file_aliases_inherit_the_wiki_checks(self):
        self.write("outside/a.md", "OUTSIDE", base=self.ext)
        jump = self.wiki / "concepts/jump"
        jump.parent.mkdir()
        if not junction(jump, self.ext / "outside"):
            self.skipTest("リンクを作れない")
        h = self.write("concepts/h.md", "HARDLINKED")
        os.link(h, self.ext / "h-copy.md")
        for name, target in (("x.md", jump / "a.md"), ("y.md", h)):
            alias = self.tmp / name
            if not symlink(alias, target):
                self.skipTest("ファイルのシンボリックリンクを作れない")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "リンクなので読まない"):
                wiki_pages.read_user_bytes(alias, self.wiki)

    @unittest.skipIf(NT, "POSIX の相対的なリンクの行き先を使う")
    def test_relative_alias_targets_and_cycles(self):
        self.write("concepts/a.md", page("a"))
        (self.tmp / "aliases").mkdir()
        alias = self.tmp / "aliases/view"
        os.symlink("../wiki/concepts", alias, target_is_directory=True)
        self.assertEqual(wiki_pages.read_user_bytes(alias / "a.md", self.wiki),
                         (self.wiki / "concepts/a.md").read_bytes())
        os.symlink("loop-b", self.tmp / "loop-a", target_is_directory=True)
        os.symlink("loop-a", self.tmp / "loop-b", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "循環"):
            wiki_pages.read_user_bytes(self.tmp / "loop-a/a.md", self.wiki)

    def test_case_variant_root_still_checks_articles(self):
        alias = self.wiki.with_name("WIKI")
        try:
            if not os.path.samefile(alias, self.wiki):
                self.skipTest("大小文字を区別するファイルシステム")
        except OSError:
            self.skipTest("大小文字を区別するファイルシステム")
        a = self.write("concepts/a.md", page("a"))
        os.link(a, self.ext / "a.md")
        with self.assertRaisesRegex(ValueError, "リンクなので読まない"):
            wiki_pages.read_user_bytes(alias / "concepts/a.md", self.wiki)
        self.assertEqual(wiki_pages.source_wiki_root(alias / "concepts", self.wiki), self.wiki)
        view = self.tmp / "view"
        if not junction(view, alias / "concepts"):
            self.skipTest("リンクを作れない")
        with self.assertRaisesRegex(ValueError, "リンクなので読まない"):
            wiki_pages.read_user_bytes(view / "a.md", self.wiki)
        self.assertEqual(wiki_pages.source_wiki_root(view, self.wiki), self.wiki)

    def test_refused_targets_match_without_reading_the_directory(self):
        warnings = [{"path": "concepts/jump", "kind": "junction"},
                    {"path": "concepts/secret.md", "kind": "hardlink"}]
        for target in ("concepts/jump/x", "concepts/jump/x.md#見出し|別名", "secret", "concepts/secret"):
            self.assertIsNotNone(wiki_pages.refused_link(target, warnings), target)
        for target in ("x", "concepts/jump", "concepts/jumper/x", "other/secret"):
            self.assertIsNone(wiki_pages.refused_link(target, warnings), target)
        # 読み取りの実パスとは分け、索引と同じ鍵で照合する。
        physical = [{"path": "concepts/a\\b.md", "kind": "hardlink"}]
        self.assertIsNotNone(wiki_pages.refused_link("concepts/a/b", physical))

    def test_refused_sources_and_duplicate_slugs_do_not_become_missing_or_retargeted(self):
        import wiki_browse_core as core
        a = self.write("sources/s.md", page("s"))
        os.link(a, self.ext / "s.md")
        self.write("entities/s.md", page("other"))
        self.write("concepts/a.md", page("a", "[[s]]").replace('tags: ["t"]', 'tags: ["t"]\nsources: ["[[s]]"]'))
        findings = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, ["type"], False, 5,
                                  index_entries=[], wiki_root=self.wiki)
        self.assertEqual(findings["unresolved_sources"], [])
        c = core.Core(core.take_snapshot(self.wiki))
        self.assertEqual(c.resolve("s")["state"], "refused")
        self.assertEqual(c.resolve("entities/s")["state"], "resolved")
        self.assertIn('title="リンクなので読まない">[[s]]', c.render_page("concepts/a"))
        self.assertTrue(any(f["path"] == "entities/s.md" for f in findings["orphans"]))
        import wiki_graph_extract as graph
        pages = graph.collect_pages(self.wiki)
        _nodes, ids, _aliases = graph.build_nodes(pages, {"node_types": {}, "predicates": {}})
        diagnostics = []
        edges = graph.build_edges(pages, ids, diagnostics)
        self.assertFalse(any(e["predicate"] == "sourced_from" for e in edges))
        self.assertFalse(any(d["kind"] == "unresolved_source" for d in diagnostics))

    def test_browse_and_lint_report_refusals_instead_of_missing_pages(self):
        import wiki_browse
        import wiki_browse_core as core
        wiki_browse._load()
        self.write("concepts/a.md", page("a", "[[secret]] [[concepts/jump/x]] [[missing]]"))
        secret = self.write("concepts/secret.md", page("secret"))
        os.link(secret, self.ext / "secret-copy.md")
        self.write("store/x.md", page("x"), base=self.ext)
        if not junction(self.wiki / "concepts/jump", self.ext / "store"):
            self.skipTest("リンクを作れない")
        found = wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, ["type"], False, 5,
                               index_entries=[], wiki_root=self.wiki)
        self.assertEqual([f["to"] for f in found["broken_links"]], ["missing"])
        c = core.Core(core.take_snapshot(self.wiki))
        self.assertEqual(c.unresolved(), [("concepts/a.md", "missing")])
        self.assertEqual([r["state"] for r in c.links["concepts/a"]], ["refused", "refused", "unresolved"])
        html = c.render_index()
        self.assertIn("concepts/secret.md", html)
        self.assertIn("link_kind: hardlink", html)
        self.assertIn("リンクなので読まない", c.render_page("concepts/a"))
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.tmp / "data")}):
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                report = wiki_browse.build(self.wiki, str(self.tmp / "site"), None)
        self.assertEqual(report["link_warnings"], found["links"])


class LinkKindTests(Base):
    def test_kinds(self):
        a = self.write("a.md", "a")
        os.link(a, self.wiki / "h.md")
        self.assertEqual(wiki_links.is_link(a), ("ok", "hardlink"))
        self.assertEqual(wiki_links.is_link(self.wiki / "SCHEMA.md"), ("ok", None))
        self.assertEqual(wiki_links.is_link(self.wiki / "none.md"), ("absent", None))
        self.write("d/x.md", "x", base=self.ext)
        if junction(self.wiki / "j", self.ext / "d"):
            self.assertEqual(wiki_links.is_link(self.wiki / "j"), ("ok", "junction" if NT else "symlink"))
        if symlink(self.wiki / "s.md", self.ext / "d" / "x.md"):
            self.assertEqual(wiki_links.is_link(self.wiki / "s.md"), ("ok", "symlink"))

    def test_name_surrogate_bit(self):
        """名前の代理のビットが立つ、知らないタグは reparse。立たないタグ（クラウドの置き換えなど）はリンクでない。"""
        def st(tag, mode=0o100644, nlink=1):
            fake = mock.Mock(st_mode=mode, st_nlink=nlink, st_file_attributes=0x400, st_reparse_tag=tag)
            return fake
        self.assertEqual(wiki_links.link_kind(st(0xA0000003, 0o040755)), "junction")
        self.assertEqual(wiki_links.link_kind(st(0xA000000C)), "symlink")
        self.assertEqual(wiki_links.link_kind(st(0xA0001234)), "reparse")
        self.assertIsNone(wiki_links.link_kind(st(0x9000001A)))       # IO_REPARSE_TAG_CLOUD_1 など。名前の代理でない
        self.assertEqual(wiki_links.link_kind(st(0, nlink=2)), "hardlink")
        self.assertIsNone(wiki_links.link_kind(st(0, nlink=2), nlink_known=False))
        self.assertIsNone(wiki_links.link_kind(st(0, 0o040755, nlink=5)))  # ディレクトリのリンクの数は見ない

    def test_find_links_and_check(self):
        a = self.write("raw/a.md", "a")
        os.link(a, self.wiki / "raw" / "b.md")
        self.write("raw/.hidden/x.md", "x")
        os.link(self.wiki / "raw" / ".hidden" / "x.md", self.wiki / "raw" / ".hidden" / "y.md")
        found = wiki_links.find_links(self.wiki / "raw")
        self.assertEqual(found["links"], [(".hidden/x.md", "hardlink"), (".hidden/y.md", "hardlink"),
                                          ("a.md", "hardlink"), ("b.md", "hardlink")])
        only = wiki_links.find_links(self.wiki / "raw", articles_only=True)
        self.assertEqual(only["links"], [("a.md", "hardlink"), ("b.md", "hardlink")])
        clean = self.write("clean/c.md", "c")
        self.assertEqual(wiki_links.find_links(clean.parent), {"links": [], "unchecked": []})
        # 起点そのものと祖先は調べない（根と祖先のリンクは許す）
        if junction(self.tmp / "view", self.wiki / "clean"):
            self.assertEqual(wiki_links.find_links(self.tmp / "view")["links"], [(".", "junction" if NT else "symlink")])
            self.assertEqual(wiki_links.find_links(self.tmp / "view", origin=self.tmp / "view")["links"], [])
        done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_links.py"), "check", str(clean.parent)],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(json.loads(done.stdout)["ok"])
        done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_links.py"), "check", str(self.wiki / "raw")],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 1)
        self.assertFalse(json.loads(done.stdout)["ok"])


class LintTests(Base):
    def lint(self):
        pages = wiki_lint.collect_pages(self.wiki)
        return wiki_lint.lint(pages, 100, 200, ["type"], False, 5, index_entries=wiki_lint.collect_index_entries(self.wiki),
                              wiki_root=self.wiki)

    def test_links_in_lint(self):
        self.write("concepts/a.md", page("a", "[[h]] と [[concepts/h]] と [[none]]"))
        os.link(self.wiki / "concepts" / "a.md", self.wiki / "concepts" / "h.md")
        self.write("concepts/b.md", page("b", "[[a]]"))
        self.write(".wiki-cache/x.md", "x")
        os.link(self.wiki / ".wiki-cache" / "x.md", self.wiki / ".wiki-cache" / "y.md")  # 記事でない。挙げない
        self.write(".git/info/notes.md", "n")
        log = self.write("log.md", "# log\n")
        os.link(log, self.tmp / "log-copy.md")
        findings = self.lint()
        self.assertEqual(findings["links"], [{"path": "concepts/a.md", "kind": "hardlink"},
                                             {"path": "concepts/h.md", "kind": "hardlink"},
                                             {"path": "log.md", "kind": "hardlink"}])
        self.assertEqual(findings["summary"]["links"], 3)
        self.assertIsNone(findings["summary"]["links_raw"])
        # リンクなので読まなかったページへの wikilink は、リンク切れにしない（b から a へのリンク）
        self.assertEqual([b["to"] for b in findings["broken_links"]], [])
        text = wiki_lint.render_text(findings)
        self.assertIn("concepts/h.md  （ハードリンク）", text)
        self.assertIn("raw の側のリンク", text)

    def test_junction_and_index(self):
        self.write("concepts/a.md", page("a"))
        self.write("x/c.md", page("c"), base=self.ext)
        self.write("ix/s.md", "# s\n", base=self.ext)
        if not junction(self.wiki / "jx", self.ext / "x") or not junction(self.wiki / "indexes", self.ext / "ix"):
            self.skipTest("リンクを作れない")
        findings = self.lint()
        kind = "junction" if NT else "symlink"
        self.assertEqual(findings["links"], [{"path": "indexes", "kind": kind}, {"path": "jx", "kind": kind}])

    def test_lint_writes_nothing(self):
        self.write("concepts/a.md", page("a"))
        os.link(self.wiki / "concepts" / "a.md", self.wiki / "concepts" / "h.md")
        before = sorted((p.relative_to(self.wiki).as_posix(), p.stat().st_size, p.stat().st_mtime_ns)
                        for p in self.wiki.rglob("*") if p.is_file())
        self.lint()
        after = sorted((p.relative_to(self.wiki).as_posix(), p.stat().st_size, p.stat().st_mtime_ns)
                       for p in self.wiki.rglob("*") if p.is_file())
        self.assertEqual(before, after)
        self.assertEqual(os.stat(self.wiki / "concepts" / "h.md").st_nlink, 2)


class ReaderTests(Base):
    def setUp(self):
        super().setUp()
        self.write("concepts/a.md", page("a", "本文 a"))
        self.write("concepts/b.md", page("b", "本文 b"))
        self.write("index.md", "# 索引\n")
        self.write("indexes/c.md", "# c\n")
        os.link(self.wiki / "concepts" / "b.md", self.tmp / "b-elsewhere.md")
        os.link(self.wiki / "indexes" / "c.md", self.tmp / "c-elsewhere.md")

    def test_stats_and_search_cli(self):
        stats = wiki_stats.compute_stats(self.wiki)
        self.assertEqual(stats["link_warnings"], [{"path": "concepts/b.md", "kind": "hardlink"}])
        self.assertEqual(stats["pages"], 1)
        done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_search.py"), "本文", "--wiki",
                               str(self.wiki), "--json", "--no-embed"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        payload = json.loads(done.stdout)
        self.assertEqual(payload["link_warnings"], [{"path": "concepts/b.md", "kind": "hardlink"}])
        self.assertEqual([r["rel_path"] for r in payload["results"]], ["concepts/a.md"])
        self.assertIn("リンクなので読まない: concepts/b.md", done.stderr)

    def test_list_index(self):
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        listed = wiki_index.list_index(self.wiki)
        self.assertEqual(listed["indexes"], [])
        self.assertEqual(listed["index"], "# 索引\n")
        self.assertEqual(listed["link_warnings"], [{"path": "indexes/c.md", "kind": "hardlink"}])
        with self.assertRaises(wiki_index.LinkRefused):
            wiki_index.list_index(self.wiki, "c")
        with self.assertRaises(FileNotFoundError):
            wiki_index.list_index(self.wiki, "none")
        for bad in ("../concepts/a", "C:/x", "/etc/x"):
            with self.subTest(name=bad), self.assertRaises(FileNotFoundError):
                wiki_index.list_index(self.wiki, bad)

    def test_mcp_index_refuses_link_pages(self):
        try:
            import numpy  # noqa: F401
            import tantivy  # noqa: F401
            import usearch  # noqa: F401
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.tmp / "data")}):
            index = wiki_index.WikiIndex(self.wiki)
            try:
                index.refresh()
                self.assertEqual(index.link_warnings, [{"path": "concepts/b.md", "kind": "hardlink"}])
                self.assertEqual(index.get_page("a")["rel_path"], "concepts/a.md")
                with self.assertRaises(wiki_index.LinkRefused):
                    index.get_page("b")
                with self.assertRaises(wiki_index.LinkRefused):
                    index.get_page("concepts/b.md")
                self.assertIsNone(index.get_page("none"))
                found = index.search("本文", top=5)
                self.assertEqual(found["link_warnings"], [{"path": "concepts/b.md", "kind": "hardlink"}])
                self.assertEqual([r["rel_path"] for r in found["results"]], ["concepts/a.md"])
                # 索引を作ったあとで a をリンクに替えると、索引から消え、get_page は「リンクなので読まない」を返す
                os.link(self.wiki / "concepts" / "a.md", self.tmp / "a-elsewhere.md")
                index.refresh()
                with self.assertRaises(wiki_index.LinkRefused):
                    index.get_page("a")
                self.assertEqual(index.search("本文", top=5)["results"], [])
            finally:
                index.close()


class ReviewOneTests(Base):
    """実装の 1 回目のレビュー（docs/agent-runs/2026-11-17-adr-0029-stage1-review/review-1.md）の反例。"""

    def test_allowed_link_root_is_searched_below(self):
        """許した根（起点）がリンクでも、その下のリンクを調べる（重大 3）。"""
        a = self.write("store/a.md", "a", base=self.ext)
        os.link(a, self.ext / "store" / "b.md")
        if not junction(self.tmp / "view", self.ext / "store"):
            self.skipTest("リンクを作れない")
        found = wiki_links.find_links(self.tmp / "view", origin=self.tmp / "view")
        self.assertEqual(found["links"], [("a.md", "hardlink"), ("b.md", "hardlink")])

    def test_get_page_under_a_link_directory(self):
        """リンクのディレクトリの下を、パスで引くと「リンクなので読まない」（重大 2）。"""
        try:
            import numpy  # noqa: F401
            import tantivy  # noqa: F401
            import usearch  # noqa: F401
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        self.write("x/a.md", page("a"), base=self.ext)
        self.write("b.md", page("b"))
        if not junction(self.wiki / "concepts", self.ext / "x"):
            self.skipTest("リンクを作れない")
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.tmp / "data")}):
            index = wiki_index.WikiIndex(self.wiki)
            try:
                index.refresh()
                with self.assertRaises(wiki_index.LinkRefused) as caught:
                    index.get_page("concepts/a.md")
                self.assertEqual(caught.exception.path, "concepts")
                with self.assertRaises(wiki_index.LinkRefused):
                    index.get_page("concepts/a")
                self.assertIsNone(index.get_page("a"))  # スラッグだけでは場所が分からない。ツールの誤りの文に場所を添える
            finally:
                index.close()

    def test_unverifiable_is_not_absent(self):
        """調べられない記事は、「ない」ではなく「調べられない」（重大 2 の後半）。"""
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        self.write("indexes/c.md", "# c\n")
        with mock.patch.object(wiki_index.wiki_pages, "article_path", return_value=wiki_pages.ArticlePath("denied")):
            with self.assertRaises(wiki_index.Unverifiable):
                wiki_index.list_index(self.wiki, "c")

    def test_stats_keeps_top_index_link(self):
        """統計は、最上位の index.md のリンクも知らせる（重大 4）。"""
        self.write("concepts/a.md", page("a"))
        top = self.write("index.md", "# 索引\n\n- [[a]]\n")
        os.link(top, self.tmp / "index-copy.md")
        stats = wiki_stats.compute_stats(self.wiki)
        self.assertIn({"path": "index.md", "kind": "hardlink"}, stats["link_warnings"])
        self.assertEqual(stats["index_lines"], 0)

    def test_readme_directory_link(self):
        """最上位の README.md という名前のディレクトリのリンクは、記事までの道として挙げる（重大 5）。"""
        self.write("x.md", page("x"), base=self.ext)
        if not junction(self.wiki / "README.md", self.ext):
            self.skipTest("リンクを作れない")
        kind = "junction" if NT else "symlink"
        self.assertEqual(list(wiki_pages.walk_pages(self.wiki).links), [("README.md", kind)])
        self.assertEqual(wiki_lint.link_report(self.wiki)["links"], [{"path": "README.md", "kind": kind}])

    def test_cli_readers_print_warnings(self):
        """統計とグラフの CLI も、標準エラーに知らせる（重大 6）。"""
        self.write("concepts/a.md", page("a"))
        os.link(self.wiki / "concepts" / "a.md", self.tmp / "a-copy.md")
        done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_stats.py"), str(self.wiki)],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("リンクなので読まない: concepts/a.md", done.stderr)

    def test_directory_replaced_before_descending(self):
        """一覧で見たディレクトリが、降りる前にリンクに替わっても、その下を読まない（重大 7）。"""
        self.write("d/x.md", page("x"))
        real = wiki_pages._stat_entry
        target = str(self.wiki / "d")

        class Junction:
            st_mode = 0o040755
            st_nlink = 1
            st_file_attributes = 0x410
            st_reparse_tag = 0xA0000003
        with mock.patch.object(wiki_pages, "_stat_entry",
                               side_effect=lambda path: ("ok", Junction()) if os.fspath(path) == target else real(path)):
            found = wiki_pages.walk_pages(self.wiki)
        self.assertEqual(([f.rel for f in found.files], list(found.links)), ([], [("d", "junction")]))

    def test_indexes_hardlinked_file_is_not_a_link(self):
        """最上位の indexes がふつうのファイルのハードリンクなら、記事でも記事までの道でもない（軽微 1）。"""
        f = self.write("indexes", "x")
        os.link(f, self.tmp / "indexes-copy")
        self.assertEqual(list(wiki_pages.walk_index_files(self.wiki).links), [])

    def test_search_json_when_every_page_is_refused(self):
        """すべてのページを拒んでも、--json は link_warnings を返す（軽微 2）。"""
        self.write("concepts/a.md", page("a", "本文"))
        os.link(self.wiki / "concepts" / "a.md", self.tmp / "a-copy.md")
        done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_search.py"), "本文", "--wiki",
                               str(self.wiki), "--json", "--no-embed"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["link_warnings"], [{"path": "concepts/a.md", "kind": "hardlink"}])

    def test_upgrade_does_not_read_a_linked_schema(self):
        """アップグレードのスキーマの検査は、リンクの SCHEMA.md を読まない（重大 1）。"""
        import init_wiki
        os.link(self.wiki / "SCHEMA.md", self.tmp / "schema-copy.md")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), mock.patch("pathlib.Path.read_text", side_effect=AssertionError("読んだ")):
            self.assertIsNone(init_wiki.detect_schema_gaps(self.wiki / "SCHEMA.md"))  # 調べていない（「不足なし」でない）
        self.assertIn("SCHEMA.md はリンクなので読まない（hardlink）", err.getvalue())

    def test_evolve_evidence_refuses_links(self):
        """evolve の根拠のページも、記事を読む口を通す（重大 1）。"""
        import wiki_evolve
        self.write("concepts/a.md", page("a"))
        os.link(self.wiki / "concepts" / "a.md", self.tmp / "a-copy.md")
        opened = wiki_pages.article_path(self.wiki, "concepts/a.md")
        self.assertEqual(opened.state, "link")
        source = (SCRIPTS / "wiki_evolve.py").read_text(encoding="utf-8")
        self.assertIn("article_path(args.wiki", source)
        self.assertNotIn("evidence[name] = path.read_text", source)


class NoticeTests(Base):
    """知らせは、拒んだその場で受け皿に入る（実装の 2 回目のレビュー。使う側の付け忘れで「ない」にならない）。"""

    def test_capture_collects_walks_and_reads(self):
        self.write("concepts/a.md", page("a"))
        os.link(self.wiki / "concepts" / "a.md", self.tmp / "a-copy.md")
        with wiki_pages.capture_notices() as notes:
            wiki_pages.walk_pages(self.wiki)
            wiki_pages.walk_pages(self.wiki)
            wiki_pages.article_path(self.wiki, "concepts/a.md")
        self.assertEqual(notes.items, [{"path": "concepts/a.md", "kind": "hardlink"}])
        self.assertEqual(wiki_pages.notice_lines(notes.items), ["リンクなので読まない: concepts/a.md（hardlink）"])

    def test_unverified_top_index_is_reported(self):
        """最上位の index.md を調べられないことは、一覧でも消さない（重大 2）。"""
        try:
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        self.write("index.md", "# 索引\n")
        real = wiki_pages._stat_entry
        top = str(self.wiki / "index.md")
        with mock.patch.object(wiki_pages, "_stat_entry",
                               side_effect=lambda path: ("denied", None) if os.fspath(path) == top else real(path)):
            with wiki_pages.capture_notices() as notes:
                listed = wiki_index.list_index(self.wiki)
        self.assertIsNone(listed["index"])
        self.assertIn({"path": "index.md", "kind": "unknown"}, notes.items)

    def test_md_named_directory_link_is_reported_for_slug_lookup(self):
        """.md で終わる名前のディレクトリのリンクも、スラッグで引いたときの知らせに入る（重大 5）。"""
        try:
            import numpy  # noqa: F401
            import tantivy  # noqa: F401
            import usearch  # noqa: F401
            import wiki_index
        except (ImportError, SystemExit) as exc:
            self.skipTest(f"索引の依存がない: {exc}")
        self.write("x/a.md", page("a"), base=self.ext)
        if not junction(self.wiki / "topics.md", self.ext / "x"):
            self.skipTest("リンクを作れない")
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.tmp / "data")}):
            index = wiki_index.WikiIndex(self.wiki)
            try:
                with wiki_pages.capture_notices() as notes:
                    index.refresh()
                    self.assertIsNone(index.get_page("a"))
                self.assertIn({"path": "topics.md", "kind": "junction" if NT else "symlink"}, notes.items)
            finally:
                index.close()

    def test_schema_unverified_is_not_read(self):
        """SCHEMA.md がリンクかを調べられなければ、読まない（重大 3）。"""
        import init_wiki
        err = io.StringIO()
        with mock.patch("wiki_links.is_link", return_value=("denied", None)), contextlib.redirect_stderr(err), \
                mock.patch("pathlib.Path.read_text", side_effect=AssertionError("読んだ")):
            self.assertIsNone(init_wiki.detect_schema_gaps(self.wiki / "SCHEMA.md"))  # 調べていない（「不足なし」でない）
        self.assertIn("調べられない", err.getvalue())

    def test_decide_forwards_search_notices(self):
        """判定のレイヤーは、検索の子プロセスの知らせを捨てない（重大 4）。"""
        import wiki_decide
        done = subprocess.CompletedProcess([], 0, stdout='{"results": [], "link_warnings": []}',
                                           stderr="リンクなので読まない: concepts/a.md（hardlink）\n雑音\n")
        err = io.StringIO()
        with mock.patch("subprocess.run", return_value=done), contextlib.redirect_stderr(err):
            wiki_decide.search_candidates("q", self.wiki, 5, True)
        self.assertEqual(err.getvalue(), "リンクなので読まない: concepts/a.md（hardlink）\n")

    def test_readme_hardlink_is_not_reported(self):
        """最上位の README.md のハードリンクは、記事でないので挙げない（軽微 1）。"""
        readme = self.write("README.md", "r")
        os.link(readme, self.tmp / "readme-copy.md")
        self.assertEqual(list(wiki_pages.walk_pages(self.wiki).links), [])

    def test_evolve_loop_refuses_before_reading(self):
        """評価ループは、パターンのページ、索引、ログのどれかがリンクなら、どれも読まず、書かない（3 回目の重大 1）。"""
        import types
        import wiki_evolve_loop
        target = self.write("concepts/evolution-pattern-x.md", page("x"))
        os.link(target, self.tmp / "pattern-copy.md")
        args = types.SimpleNamespace(wiki=self.wiki, id="run1", raw=self.tmp / "raw")
        patterns = {"x": {"run": "run1", "iteration": 1, "claim": "c", "scope": "s", "counterexamples": "n", "sources": []}}
        with mock.patch("pathlib.Path.read_text", side_effect=AssertionError("読んだ")), \
                mock.patch.object(wiki_evolve_loop, "atomic", side_effect=AssertionError("書いた")):
            with self.assertRaises(ValueError) as caught:
                wiki_evolve_loop.publish_learning(args, [], patterns, 1)
        self.assertIn("concepts/evolution-pattern-x.md", str(caught.exception))
        self.assertFalse((self.tmp / "raw").exists())  # raw も作らない


class ReviewThreeTests(Base):
    """実装の 3 回目のレビュー（review-3.md）の反例。"""

    def test_shortlist_source_inside_wiki_uses_the_gateway(self):
        """判定のレイヤーの入力が wiki の中のリンクの記事なら、読まない（重大 2）。"""
        p = self.write("concepts/p.md", page("p"))
        os.link(p, self.tmp / "p-copy.md")
        with self.assertRaises(ValueError) as caught:
            wiki_pages.read_user_file(self.wiki / "concepts" / "p.md", self.wiki)
        self.assertIn("リンクなので読まない", str(caught.exception))
        outside = self.write("outside.md", "外", base=self.ext)
        self.assertEqual(wiki_pages.read_user_file(outside, self.wiki), "外")

    def test_upgrade_does_not_claim_up_to_date(self):
        """スキーマを調べなかったら、「追いついている」と言わない（重大 3）。"""
        import init_wiki
        os.link(self.wiki / "SCHEMA.md", self.tmp / "schema-copy.md")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertIsNone(init_wiki.detect_schema_gaps(self.wiki / "SCHEMA.md"))
        self.assertEqual(init_wiki.detect_schema_gaps(self.tmp / "none" / "SCHEMA.md"), [])
        source = (SCRIPTS / "init_wiki.py").read_text(encoding="utf-8")
        self.assertIn("if gaps is None:", source)

    def test_is_link_reads_block_device_as_unverified(self):
        """Windows の S_IFBLK の読み替えを、判定の部品も走査と同じにする（重大 4）。"""
        block = os.stat_result((0x6000, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        with mock.patch.object(wiki_pages, "NT", True), mock.patch("os.lstat", return_value=block):
            self.assertEqual(wiki_links.is_link(self.wiki / "SCHEMA.md"), ("denied", None))
            self.assertEqual(wiki_links.find_links(self.wiki / "SCHEMA.md"), {"links": [], "unchecked": ["."]})

    def test_search_json_uses_the_collecting_walk(self):
        """検索の JSON は、ページを集めた走査の知らせを使う（重大 5）。"""
        source = (SCRIPTS / "wiki_search.py").read_text(encoding="utf-8")
        self.assertIn("with capture_notices() as notes:\n        pages = collect_pages(", source)
        self.assertNotIn("args.link_warnings = link_warnings(walk_pages(args.wiki))", source)

    def test_process_notices_do_not_grow(self):
        """プロセスの知らせは、同じものを重ねて貯めない（軽微 1）。"""
        a = self.write("concepts/a.md", page("a"))
        os.link(a, self.tmp / "a-copy.md")
        with mock.patch.object(wiki_pages, "_CLI", True), mock.patch.dict(wiki_pages._PROCESS_NOTICES, clear=True):
            for _ in range(50):
                wiki_pages.walk_pages(self.wiki)
            self.assertEqual(len(wiki_pages._PROCESS_NOTICES), 1)


class ReviewFourTests(Base):
    """実装の 4 回目のレビュー（review-4.md）の反例。"""

    def test_user_file_through_a_root_alias(self):
        """根の別名（リンクの根）の実体の側のパスで渡しても、記事を読む口を通す（重大 1）。"""
        store = self.tmp / "store"
        store.mkdir()
        (store / "SCHEMA.md").write_text("s", encoding="utf-8")
        p = self.write("concepts/p.md", page("p"), base=store)
        os.link(p, self.tmp / "p-copy.md")
        if not junction(self.tmp / "view", store):
            self.skipTest("リンクを作れない")
        with self.assertRaises(ValueError):
            wiki_pages.read_user_file(store / "concepts" / "p.md", self.tmp / "view")
        with self.assertRaises(ValueError):
            wiki_pages.read_user_file(self.tmp / "view" / "concepts" / "p.md", store)
        with self.assertRaises(ValueError):
            wiki_pages.read_user_file(Path(str(store / "concepts" / "p.md").upper()) if NT else store / "concepts" / "p.md",
                                      self.tmp / "view")

    def test_youtube_page_argument_uses_the_gateway(self):
        """字幕の検証の --page の右辺が wiki の中のリンクの記事なら、読まない（重大 2）。"""
        import wiki_youtube
        p = self.write("concepts/p.md", page("p"))
        os.link(p, self.tmp / "p-copy.md")
        with self.assertRaises(wiki_youtube.Fail):
            wiki_youtube.parse_page_args([f"concepts/x.md={self.wiki / 'concepts' / 'p.md'}"], self.wiki)

    def test_evolve_loop_refuses_a_corpus_with_links(self):
        """評価ループは、リンクのあるコーパスを読まない（重大 3）。"""
        import wiki_evolve_loop as loop
        linked = self.write("concepts/p.md", page("p"))
        os.link(linked, self.ext / "copy.md")
        skill = self.ext / "skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("before", encoding="utf-8")
        suite = self.tmp / "suite.json"
        suite.write_text(json.dumps({"corpus": "wiki"}), encoding="utf-8")
        args = SimpleNamespace(id="run", skill=skill, wiki=self.wiki, suite=suite)
        state = self.wiki / ".evolution"
        state.mkdir()
        with mock.patch.object(loop, "contract") as contract:
            with self.assertRaisesRegex(ValueError, "リンク"):
                loop.run(args, state)
        contract.assert_not_called()

    def test_cli_detection_ignores_case(self):
        """CLI の判定は、パスの大文字と小文字の違いに左右されない（重大 4）。"""
        here = str(SCRIPTS / "wiki_stats.py")
        self.assertTrue(wiki_pages._same_dir(here.lower() if NT else here, wiki_pages.__file__))


class ReviewFiveTests(Base):
    """第5回の反例を、実ファイルと入口の実行で検査する。"""

    def setUp(self):
        super().setUp()
        self.skill = self.ext / "skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text("before", encoding="utf-8")
        self.state = self.wiki / ".evolution"
        self.state.mkdir()
        self.write("concepts/evidence.md", page("evidence"))

    def args(self, candidate, **values):
        return SimpleNamespace(**dict(dict(id="sample", skill=self.skill, candidate=candidate,
                                          target="SKILL.md", wiki=self.wiki, reason="回帰の確認",
                                          evidence=["concepts/evidence.md"]), **values))

    def record_reads(self, reads):
        original = Path.read_bytes
        def read(path):
            reads.append(path)
            return original(path)
        return mock.patch.object(Path, "read_bytes", read)

    def directory_case(self):
        directory = self.wiki / "concepts/candidate"
        directory.mkdir()
        (directory / "SKILL.md").write_text("after", encoding="utf-8")
        linked = directory / "p.md"
        linked.write_text("refused", encoding="utf-8")
        os.link(linked, self.ext / "copy.md")
        return directory, linked

    def assert_directory_refused(self, directory, linked):
        import wiki_evolve
        reads = []
        with self.record_reads(reads), wiki_pages.capture_notices() as notices:
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.propose(self.args(directory, target=None), self.state)
        self.assertNotIn(linked, reads, "拒むべき記事の本文を読んだ")
        self.assertIn({"path": "concepts/candidate/p.md", "kind": "hardlink"}, notices.items)
        self.assertFalse((self.state / "sample").exists())

    def test_directory_candidate_refuses_before_reading(self):
        self.assert_directory_refused(*self.directory_case())

    def test_regression_catches_tree_that_drops_the_wiki(self):
        """読む口の呼び出し名が残っていても、wiki の引き渡しを欠く実装を検出する。"""
        import wiki_evolve
        directory, linked = self.directory_case()
        original = wiki_evolve.tree
        with mock.patch.object(wiki_evolve, "tree", side_effect=lambda root, wiki_root=None: original(root)):
            with self.assertRaises(AssertionError):
                self.assert_directory_refused(directory, linked)

    def test_installed_skill_under_wiki_is_also_checked(self):
        import wiki_evolve
        source, linked = self.directory_case()
        candidate = self.write("candidate.md", "after", self.ext)
        reads = []
        with self.record_reads(reads):
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.propose(self.args(candidate, skill=source), self.state)
        self.assertNotIn(linked, reads)

    def test_single_candidates_preserve_bytes_and_article_scope(self):
        import wiki_evolve
        data = b"after\r\nwith CRLF\r\n"
        cases = [(self.ext, "outside.md"), (self.wiki, "concepts/candidate.md"),
                 (self.wiki, "assets/candidate.md"), (self.wiki, "candidate.txt"),
                 (self.wiki, ".hidden/candidate.md")]
        for number, (root, name) in enumerate(cases):
            with self.subTest(path=name):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                result = wiki_evolve.propose(self.args(path, id=f"case-{number}"), self.state)
                self.assertEqual(result["status"], "proposed")
                self.assertEqual((self.state / f"case-{number}/candidate/SKILL.md").read_bytes(), data)

    def test_single_linked_article_is_not_read(self):
        import wiki_evolve
        linked = self.write("concepts/candidate.md", "refused")
        os.link(linked, self.ext / "copy.md")
        reads = []
        with self.record_reads(reads):
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.propose(self.args(linked), self.state)
        self.assertNotIn(linked, reads)

    def proposal(self):
        import wiki_evolve
        candidate = self.write("candidate.md", "after", self.ext)
        wiki_evolve.propose(self.args(candidate), self.state)
        return self.state / "sample"

    def test_evaluate_refuses_original_corpus_before_reading(self):
        import wiki_evolve
        exp = self.proposal()
        linked = self.write("concepts/p.md", "refused")
        os.link(linked, self.ext / "copy.md")
        suite = self.tmp / "suite.json"
        suite.write_text(json.dumps({"corpus": "wiki"}), encoding="utf-8")
        reads = []
        with self.record_reads(reads), mock.patch.object(wiki_evolve, "suite_contract") as contract:
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.evaluate(SimpleNamespace(suite=suite, wiki=self.wiki), exp)
        contract.assert_not_called()
        self.assertNotIn(linked, reads)
        self.assertFalse(list(exp.glob("inputs-*.json")))

    def test_nonarticle_hardlink_is_allowed_in_corpus_and_copy(self):
        import wiki_evolve
        import wiki_evolve_loop as loop
        path = self.write("assets/image.dat", "asset")
        os.link(path, self.ext / "copy.dat")
        wiki_evolve.tree(self.wiki, self.wiki)
        dest = self.ext / "snapshot"
        wiki_evolve.copy_tree(self.wiki, dest, self.wiki)
        self.assertEqual((dest / "assets/image.dat").read_text(encoding="utf-8"), "asset")
        suite = self.tmp / "suite.json"
        suite.write_text(json.dumps({"corpus": "wiki"}), encoding="utf-8")
        args = SimpleNamespace(id="run", skill=self.skill, wiki=self.wiki, suite=suite)
        class ReachedContract(Exception):
            pass
        with mock.patch.object(loop, "contract", side_effect=ReachedContract):
            with self.assertRaises(ReachedContract):
                loop.run(args, self.state)

    def test_parent_segments_are_rejected_before_reading_or_normalizing(self):
        paths = [self.wiki / "concepts/jump/../candidate.md", self.ext / "../candidate.md"]
        for path in paths:
            for reader in (wiki_pages.read_user_file, wiki_pages.read_user_bytes):
                with self.subTest(path=str(path), reader=reader.__name__):
                    with mock.patch.object(os.path, "abspath", side_effect=AssertionError("正規化してはいけない")):
                        with self.assertRaisesRegex(ValueError, r"\.\."):
                            reader(path, self.wiki)

    def test_parent_segments_in_propose_are_rejected(self):
        import wiki_evolve
        candidate = self.wiki / "concepts/jump/../candidate.md"
        with self.assertRaisesRegex(ValueError, r"\.\."):
            wiki_evolve.propose(self.args(candidate), self.state)

    @unittest.skipIf(NT, "POSIX のシンボリックリンクと .. の解決を使う")
    def test_posix_parent_after_symlink_never_reads_a_decoy(self):
        import wiki_evolve
        (self.wiki / "other/deep").mkdir(parents=True)
        os.symlink(self.wiki / "other/deep", self.wiki / "concepts/jump", target_is_directory=True)
        self.write("concepts/candidate.md", "decoy")
        linked = self.write("other/candidate.md", "refused")
        os.link(linked, self.ext / "copy.md")
        candidate = self.wiki / "concepts/jump/../candidate.md"
        for reader in (wiki_pages.read_user_file, wiki_pages.read_user_bytes):
            with self.assertRaisesRegex(ValueError, r"\.\."):
                reader(candidate, self.wiki)
        with self.assertRaisesRegex(ValueError, r"\.\."):
            wiki_evolve.propose(self.args(candidate), self.state)


    def test_cli_keeps_protection_through_root_alias_and_outgoing_junction(self):
        outside = self.write("p.md", "refused", self.ext)
        view = self.tmp / "view"
        if not junction(view, self.wiki) or not junction(self.wiki / "concepts/jump", self.ext):
            self.skipTest("ディレクトリのリンクを作れない")
        alias = view / "concepts/jump/p.md"
        for reader in (wiki_pages.read_user_file, wiki_pages.read_user_bytes):
            with wiki_pages.capture_notices() as notices:
                with self.assertRaisesRegex(ValueError, "リンク"):
                    reader(alias, self.wiki)
            self.assertTrue(notices.items)
        done = subprocess.run([sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki_evolve.py"),
                               "--wiki", str(view), "propose", "--id", "alias", "--skill", str(self.skill),
                               "--candidate", str(alias), "--target", "SKILL.md", "--reason", "回帰",
                               "--evidence", "concepts/evidence.md"],
                              capture_output=True, encoding="utf-8", timeout=20)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("リンク", done.stderr)
        self.assertFalse((self.state / "alias").exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "refused")

    def nested_corpus(self, prefix="concepts"):
        corpus = self.wiki / prefix / "corpus"
        linked = self.write(f"{prefix}/corpus/assets/p.md", "refused")
        os.link(linked, self.ext / "copy.md")
        suite = corpus.parent / "suite.json"
        suite.write_text(json.dumps({"corpus": "corpus"}), encoding="utf-8")
        return corpus, linked, suite

    def assert_nested_loop_refused(self, linked, suite):
        import wiki_evolve_loop as loop
        class ReachedContract(Exception):
            pass
        args = SimpleNamespace(id="run", wiki=self.wiki, skill=self.skill, suite=suite)
        reads = []
        with self.record_reads(reads), mock.patch.object(loop, "contract", side_effect=ReachedContract) as contract:
            with wiki_pages.capture_notices() as notices:
                try:
                    loop.run(args, self.state)
                except ValueError as exc:
                    self.assertIn("リンク", str(exc))
                except ReachedContract:
                    self.fail("リンクの記事を拒否せず contract に進んだ")
                else:
                    self.fail("リンクの記事を拒否しなかった")
        contract.assert_not_called()
        self.assertNotIn(linked, reads)
        self.assertTrue(notices.items)

    def test_nested_corpus_uses_the_original_wiki_in_both_entries(self):
        import wiki_evolve
        exp = self.proposal()
        corpus, linked, suite = self.nested_corpus()
        self.assertEqual(wiki_pages.source_wiki_root(corpus, self.wiki), self.wiki)
        self.assert_nested_loop_refused(linked, suite)
        reads = []
        with self.record_reads(reads), mock.patch.object(wiki_evolve, "suite_contract") as contract:
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.evaluate(SimpleNamespace(wiki=self.wiki, suite=suite), exp)
        contract.assert_not_called()
        self.assertNotIn(linked, reads)

    def test_regression_catches_a_wrong_corpus_root(self):
        corpus, linked, suite = self.nested_corpus()
        with mock.patch.object(wiki_pages, "source_wiki_root", side_effect=lambda path, wiki=None: path):
            with self.assertRaises(AssertionError):
                self.assert_nested_loop_refused(linked, suite)

    def test_corpus_in_excluded_tree_does_not_create_new_articles(self):
        import wiki_evolve
        corpus, linked, suite = self.nested_corpus(prefix="assets")
        root = wiki_pages.source_wiki_root(corpus, self.wiki)
        self.assertEqual(root, self.wiki)
        target = self.ext / "snapshot"
        wiki_evolve.copy_tree(corpus, target, root)
        self.assertEqual((target / "assets/p.md").read_text(encoding="utf-8"), "refused")
        self.assertEqual(wiki_pages.article_path(self.wiki, "assets/corpus/assets/p.md").state, "not_article")

    def test_linked_directory_is_rejected_before_walking(self):
        import wiki_evolve
        jump = self.wiki / "concepts/jump"
        if not junction(jump, self.ext):
            self.skipTest("ディレクトリのリンクを作れない")
        with mock.patch.object(wiki_evolve.os, "walk", side_effect=AssertionError("リンクに降りてはいけない")):
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.tree(jump, self.wiki)

    def test_posix_colon_reaches_the_same_link_check_as_other_articles(self):
        import stat
        def attributes(path):
            return "ok", SimpleNamespace(st_mode=stat.S_IFREG if str(path).endswith("a:b.md") else stat.S_IFDIR,
                                          st_nlink=2 if str(path).endswith("a:b.md") else 1)
        with mock.patch.object(wiki_pages, "NT", False), mock.patch.object(wiki_pages, "_stat_entry", side_effect=attributes) as lookup:
            for reader in (wiki_pages.read_user_file, wiki_pages.read_user_bytes):
                with self.assertRaisesRegex(ValueError, "リンク"):
                    reader(self.wiki / "concepts/a:b.md", self.wiki)
        self.assertGreater(lookup.call_count, 0)

    @unittest.skipIf(NT, "POSIX のファイル名の : を使う")
    def test_posix_colon_hardlink_is_not_read(self):
        linked = self.write("concepts/a:b.md", "refused")
        os.link(linked, self.ext / "copy.md")
        with self.assertRaisesRegex(ValueError, "リンク"):
            wiki_pages.read_user_bytes(linked, self.wiki)

    def test_case_conversion_does_not_change_relative_path_offsets(self):
        root = self.tmp / "W\u0130"
        found = wiki_pages._article_rel(root / "concepts/p.md", root)
        self.assertEqual(found, (str(root), "concepts/p.md"))

    def test_unlistable_root_and_subdirectory_never_become_empty_snapshots(self):
        import wiki_evolve
        root = self.ext / "input"
        (root / "sub").mkdir(parents=True)
        (root / "sub/p.md").write_text("data", encoding="utf-8")
        scan = os.scandir
        for blocked in (root, root / "sub"):
            def denied(path):
                if Path(path) == blocked:
                    raise PermissionError(13, "denied", str(blocked))
                return scan(path)
            for copy in (False, True):
                with self.subTest(blocked=str(blocked), copy=copy):
                    dest = self.ext / "snapshot"
                    with mock.patch.object(os, "scandir", side_effect=denied):
                        with self.assertRaises(PermissionError) as error:
                            if copy:
                                wiki_evolve.copy_tree(root, dest, root)
                            else:
                                wiki_evolve.tree(root, root)
                    self.assertEqual(error.exception.filename, str(blocked))
                    self.assertFalse(dest.exists())

    def test_both_corpus_entries_stop_before_contract_on_listing_error(self):
        import wiki_evolve
        import wiki_evolve_loop as loop
        exp = self.proposal()
        corpus = self.wiki / "concepts/corpus"
        corpus.mkdir()
        suite = self.tmp / "suite.json"
        suite.write_text(json.dumps({"corpus": "wiki/concepts/corpus"}), encoding="utf-8")
        scan = os.scandir
        # suite の親は解決済みのパスになる。macOS の /var と /private/var など、
        # 一時ディレクトリの別名でも、同じ実体への走査に障害を入れる。
        blocked = corpus.resolve()
        failures = []
        def denied(path):
            if Path(path).resolve() == blocked:
                failures.append(path)
                raise PermissionError(13, "denied", str(corpus))
            return scan(path)
        args = SimpleNamespace(id="run", wiki=self.wiki, skill=self.skill, suite=suite)
        with mock.patch.object(os, "scandir", side_effect=denied):
            with mock.patch.object(wiki_evolve, "suite_contract") as contract:
                with self.assertRaises(PermissionError):
                    wiki_evolve.evaluate(args, exp)
            contract.assert_not_called()
            self.assertTrue(failures)
            failures.clear()
            with mock.patch.object(loop, "contract") as contract:
                with self.assertRaises(PermissionError):
                    loop.run(args, self.state)
            contract.assert_not_called()
        self.assertTrue(failures)
        self.assertFalse(list(exp.glob("inputs-*.json")))
        self.assertFalse((self.state / "run").exists())

    def test_native_posix_names_preserve_backslash_and_check_the_requested_file(self):
        import posixpath
        import stat
        from pathlib import PurePosixPath
        for relative in ("concepts/a\\b.md", "assets\\p.md"):
            requested = "/W/" + relative
            reads = []
            class ModelPath(PurePosixPath):
                def read_bytes(path):
                    reads.append(str(path))
                    return b"ORIGINAL" if str(path) == requested else b"DECOY"
                def read_text(path, **kwargs):
                    return path.read_bytes().decode("utf-8")
            proxy = SimpleNamespace(path=SimpleNamespace(abspath=posixpath.abspath, normcase=posixpath.normcase,
                                                         realpath=lambda path: str(path), join=posixpath.join,
                                                         samefile=lambda a, b: str(a) == str(b)),
                                    fspath=os.fspath)
            linked = False
            def attributes(path):
                return "ok", SimpleNamespace(st_mode=stat.S_IFREG if str(path).endswith(".md") else stat.S_IFDIR,
                                              st_nlink=2 if linked and str(path) == requested else 1)
            with mock.patch.object(wiki_pages, "os", proxy), mock.patch.object(wiki_pages, "Path", ModelPath), \
                 mock.patch.object(wiki_pages, "NT", False), mock.patch.object(wiki_pages, "_stat_entry", side_effect=attributes):
                with self.subTest(path=relative):
                    found = wiki_pages.Walk([SimpleNamespace(rel=relative)], [], [], [])
                    with mock.patch.object(wiki_pages, "walk_markdown", return_value=found):
                        self.assertEqual([f.rel for f in wiki_pages.walk_pages(ModelPath("/W")).files], [relative])
                    self.assertEqual(wiki_pages.read_user_bytes(ModelPath(requested), ModelPath("/W")), b"ORIGINAL")
                    self.assertEqual(wiki_pages.read_user_file(ModelPath(requested), ModelPath("/W")), "ORIGINAL")
                    self.assertEqual(reads, [requested, requested])
                    linked = True
                    for reader in (wiki_pages.read_user_file, wiki_pages.read_user_bytes):
                        with self.assertRaisesRegex(ValueError, "リンク"):
                            reader(ModelPath(requested), ModelPath("/W"))
                    self.assertEqual(reads, [requested, requested])

    def test_physical_evidence_and_index_page_keep_the_native_name(self):
        import posixpath
        import stat
        import wiki_evolve
        import wiki_index
        from pathlib import PurePosixPath
        relative = "concepts/a\\b.md"
        requested = "/W/" + relative
        reads = []
        class ModelPath(PurePosixPath):
            def resolve(path): return path
            def exists(path): return str(path) != "/STATE/sample"
            def is_dir(path): return str(path) in ("/S", "/W", "/STATE")
            def is_file(path): return not path.is_dir()
            def is_symlink(path): return False
            def read_bytes(path): return b"candidate"
            def read_text(path, **kwargs):
                reads.append(str(path))
                return "ORIGINAL" if str(path) == requested else "DECOY"
        proxy = SimpleNamespace(path=SimpleNamespace(abspath=posixpath.abspath, normcase=posixpath.normcase,
                                                     realpath=lambda path: str(path), join=posixpath.join,
                                                         samefile=lambda a, b: str(a) == str(b)),
                                fspath=os.fspath)
        linked = False
        def attributes(path):
            return "ok", SimpleNamespace(st_mode=stat.S_IFREG if str(path).endswith(".md") else stat.S_IFDIR,
                                          st_nlink=2 if linked and str(path) == requested else 1)
        class BeforeStaging(Exception):
            pass
        args = SimpleNamespace(id="sample", skill=ModelPath("/S"), candidate=ModelPath("/candidate.md"),
                               target="SKILL.md", wiki=ModelPath("/W"), reason="回帰", evidence=[relative])
        with mock.patch.object(wiki_pages, "os", proxy), mock.patch.object(wiki_pages, "Path", ModelPath), \
             mock.patch.object(wiki_pages, "NT", False), mock.patch.object(wiki_pages, "_stat_entry", side_effect=attributes), \
             mock.patch.object(wiki_evolve, "inside", side_effect=lambda root, name: ModelPath(str(root) + "/" + name)), \
             mock.patch.object(wiki_evolve.tempfile, "TemporaryDirectory", side_effect=BeforeStaging):
            with self.assertRaises(BeforeStaging):
                wiki_evolve.propose(args, ModelPath("/STATE"))
            self.assertEqual(reads, [requested])
            linked = True
            with self.assertRaisesRegex(ValueError, "リンク"):
                wiki_evolve.propose(args, ModelPath("/STATE"))
            self.assertEqual(reads, [requested])
            linked = False
            index = object.__new__(wiki_index.WikiIndex)
            index.root = ModelPath("/W")
            index.link_warnings = []
            index.pages = [{"rel_path": relative, "path": requested, "slug": "literal", "meta": {}, "links": [], "sections": []}]
            with mock.patch.object(wiki_index, "Path", ModelPath):
                result = index.get_page("literal")
                self.assertEqual(result["body"], "ORIGINAL")
                self.assertEqual(reads, [requested, requested])
                linked = True
                with self.assertRaises(wiki_index.LinkRefused):
                    index.get_page("literal")
                self.assertEqual(reads, [requested, requested])

    @unittest.skipIf(NT, "POSIX のファイル名のバックスラッシュを使う")
    def test_posix_candidate_bytes_are_from_the_named_file(self):
        import wiki_evolve
        candidate = self.write("concepts/a\\b.md", "ORIGINAL")
        self.write("concepts/a/b.md", "DECOY")
        wiki_evolve.propose(self.args(candidate), self.state)
        self.assertEqual((self.state / "sample/candidate/SKILL.md").read_bytes(), b"ORIGINAL")
        outside = self.write("candidate.md", "after", self.ext)
        wiki_evolve.propose(self.args(outside, id="evidence", evidence=["concepts/a\\b.md"]), self.state)
        proposal = json.loads((self.state / "evidence/proposal.json").read_text(encoding="utf-8"))
        self.assertEqual(proposal["evidence"]["concepts/a\\b.md"], "ORIGINAL")
        import wiki_index
        self.write("indexes/a\\b.md", "# ORIGINAL")
        self.write("indexes/a/b.md", "# DECOY")
        rows = {row["name"]: row["title"] for row in wiki_index.list_index(self.wiki)["indexes"]}
        self.assertEqual(rows["a\\b.md"], "ORIGINAL")
        self.assertEqual(rows["a/b.md"], "DECOY")
        os.link(candidate, self.ext / "copy.md")
        with self.assertRaisesRegex(ValueError, "リンク"):
            wiki_evolve.propose(self.args(candidate, id="linked"), self.state)
        with self.assertRaisesRegex(ValueError, "リンク"):
            wiki_evolve.propose(self.args(outside, id="linked-evidence", evidence=["concepts/a\\b.md"]), self.state)


class ReadSiteInventoryTests(unittest.TestCase):
    """スクリプトの中のファイルの読み取り（read_text、read_bytes、open）を、関数ごとに 1 度ずつ分類する。

    記事を読むなら、走査の結果か記事を読む口（article_path、read_user_file）を通す（ADR-0029 の I2）。新しく読み取りを
    足した関数は、ここで分類しないと落ちる。これは見直す場所の目録であり、関数内の全分岐の保護を証明するものではない。
    実際にリンクを読まないことと対象外の入力を受け付けることは、ReviewFiveTests の入口ごとの実行と対照で確かめる。
    """

    WALKED = "走査の結果のページか索引を読む（リンクは走査が拒む）"
    GATEWAY = "記事を読む口を通してから読む"
    RAW = "raw を読む（raw の側の規則は段階 2）"
    NOT_ARTICLE = "記事でないものを読む（プラグインのファイル、設定、キャッシュ、索引の台帳、記録、オントロジーなど）"
    USER_FILE = "利用者が渡したファイルを読む（wiki を受け取らない入口）"
    WORK_COPY = "評価のために写した作業用の wiki を読む（利用者の wiki ではない）"
    WRITE = "書くために開く（書き込みの守りは段階 3 の書き込みの部品）"
    URL = "ファイルではなく URL を開く"

    SITES = {
        ("wiki_codex.py", "workflow"): NOT_ARTICLE,  # 同梱の commands/*.md。wiki の記事ではない
        ("init_wiki.py", "copy_template"): NOT_ARTICLE,
        ("init_wiki.py", "detect_schema_gaps"): GATEWAY,
        ("wiki_browse_fs.py", "_check_marker"): NOT_ARTICLE,
        ("wiki_browse_fs.py", "probe_server"): NOT_ARTICLE,
        ("wiki_browse_fs.py", "read_manifest"): NOT_ARTICLE,
        ("wiki_browse_fs.py", "read_record"): NOT_ARTICLE,
        ("wiki_browse_fs.py", "serve_finish"): NOT_ARTICLE,
        ("wiki_captions.py", "check_pages.load"): RAW,
        ("wiki_captions.py", "load_pages"): WALKED,
        ("wiki_decide.py", "cmd_ask"): USER_FILE,
        ("wiki_decide.py", "cmd_screen"): USER_FILE,
        ("wiki_decide.py", "cmd_shortlist"): GATEWAY,
        ("wiki_decide.py", "load_questions"): NOT_ARTICLE,
        ("wiki_encoding.py", "convert"): USER_FILE,
        ("wiki_encoding.py", "main"): USER_FILE,
        ("wiki_evolve.py", "capture"): RAW,
        ("wiki_evolve.py", "evaluate"): GATEWAY,
        ("wiki_evolve.py", "main"): NOT_ARTICLE,
        ("wiki_evolve.py", "promote"): NOT_ARTICLE,
        ("wiki_evolve.py", "propose"): GATEWAY,
        ("wiki_evolve.py", "read_json"): GATEWAY,
        ("wiki_evolve.py", "tree"): GATEWAY,
        ("wiki_evolve.py", "copy_tree"): GATEWAY,
        ("wiki_evolve_agent.py", "execute"): WORK_COPY,
        ("wiki_evolve_api.py", "local_tool"): WORK_COPY,
        ("wiki_evolve_loop.py", "Calls.__init__"): NOT_ARTICLE,
        ("wiki_evolve_loop.py", "Calls.invoke"): NOT_ARTICLE,
        ("wiki_evolve_loop.py", "artifact_checks"): WORK_COPY,
        ("wiki_evolve_loop.py", "calibrate"): NOT_ARTICLE,
        ("wiki_evolve_loop.py", "publish_learning"): GATEWAY,
        ("wiki_evolve_loop.py", "rollout"): WORK_COPY,
        ("wiki_evolve_loop.py", "run"): GATEWAY,
        ("wiki_evolve_loop.py", "skill_text"): NOT_ARTICLE,
        ("wiki_evolve_stream.py", "append_trace"): NOT_ARTICLE,
        ("wiki_fetch.py", "build"): RAW,
        ("wiki_fetch.py", "existing_sha"): RAW,
        ("wiki_graph_extract.py", "collect_pages"): WALKED,
        ("wiki_graph_extract.py", "read_ontology"): NOT_ARTICLE,
        ("wiki_graph_lint.py", "decision_default_threshold"): NOT_ARTICLE,
        ("wiki_help.py", "collect_commands"): NOT_ARTICLE,
        ("wiki_help.py", "command_details"): NOT_ARTICLE,
        ("wiki_help.py", "read_manifest"): NOT_ARTICLE,
        ("wiki_index.py", "ChunkStore.__init__"): NOT_ARTICLE,
        ("wiki_index.py", "WikiIndex.get_page"): GATEWAY,
        ("wiki_index.py", "WriterLock.__init__"): NOT_ARTICLE,
        ("wiki_index.py", "ensure_model_files"): NOT_ARTICLE,
        ("wiki_index.py", "sha256_file"): NOT_ARTICLE,
        ("wiki_index.py", "list_index"): GATEWAY,
        ("wiki_lint.py", "collect_index_entries"): WALKED,
        ("wiki_lint.py", "collect_pages"): WALKED,
        ("wiki_mcp_common.py", "FileLock.__enter__"): NOT_ARTICLE,
        ("wiki_mcp_common.py", "code_version"): NOT_ARTICLE,
        ("wiki_mcp_common.py", "env_problems"): NOT_ARTICLE,
        ("wiki_mcp_common.py", "read_server_info"): NOT_ARTICLE,
        ("wiki_mcp_common.py", "record_failure"): NOT_ARTICLE,
        ("wiki_mcp_relay.py", "ensure_server"): NOT_ARTICLE,
        ("wiki_pages.py", "_vendor_digest"): NOT_ARTICLE,
        ("wiki_pages.py", "read_user_file"): GATEWAY,
        ("wiki_pages.py", "read_user_bytes"): GATEWAY,
        ("wiki_pages.py", "user_directory_path"): GATEWAY,
        ("wiki_pdf.py", "main"): RAW,
        ("wiki_rawcheck.py", "check"): RAW,
        ("wiki_rawcheck.py", "freeze"): RAW,
        ("wiki_rawcheck.py", "load_fetch"): RAW,
        ("wiki_rawcheck.py", "read_text"): RAW,
        ("wiki_rawcheck.py", "resumable_fetch"): RAW,
        ("wiki_rawcheck.py", "resume_fields"): RAW,
        ("wiki_rawcheck.py", "work_dir_complete"): RAW,
        ("wiki_rawcheck.py", "work_dir_matches_raw"): RAW,
        ("wiki_search.py", "collect_pages"): WALKED,
        ("wiki_search.py", "decision_default_threshold"): NOT_ARTICLE,
        ("wiki_search.py", "load_parse_cache"): NOT_ARTICLE,
        ("wiki_session.py", "_raw_frontmatter"): RAW,
        ("wiki_session.py", "cmd_decide"): RAW,
        ("wiki_session.py", "cmd_scan"): RAW,
        ("wiki_session.py", "cmd_verify"): RAW,
        ("wiki_session.py", "cmd_write"): RAW,
        ("wiki_session.py", "load_decisions"): NOT_ARTICLE,
        ("wiki_session.py", "read_range"): RAW,
        ("wiki_session.py", "write_decisions"): NOT_ARTICLE,
        ("wiki_session.py", "write_raw"): RAW,
        ("wiki_stats.py", "compute_stats"): WALKED,
        ("wiki_workspace.py", "read_json"): NOT_ARTICLE,
        ("wiki_youtube.py", "cmd_verify"): RAW,
        ("wiki_youtube.py", "parse_page_args"): GATEWAY,
        ("wiki_youtube.py", "cmd_write"): RAW,
        ("wiki_youtube.py", "existing_raws"): RAW,
        ("wiki_browse.py", "_emit"): URL,  # webbrowser.open
        ("wiki_browse_fs.py", "Os.open_excl"): WRITE,
        ("wiki_browse_fs.py", "Os.open_lock"): WRITE,
        ("wiki_browse_fs.py", "Os.open_read"): WALKED,
        ("wiki_evolve.py", "create"): WRITE,
        ("wiki_fetch.py", "fetch"): URL,
        ("wiki_fetch.py", "write_outputs"): WRITE,
        ("wiki_graph_common.py", "extract_lock.__enter__"): WRITE,
        ("wiki_graph_extract.py", "_write_lines"): WRITE,
        ("wiki_mcp_common.py", "write_server_info"): WRITE,
        ("wiki_youtube.py", "publish"): WRITE,
    }

    def sites(self):
        found = set()
        for f in sorted(SCRIPTS.glob("*.py")):
            if f.name.startswith("test_"):
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))

            def visit(node, stack):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        visit(child, stack + [child.name])
                        continue
                    if isinstance(child, ast.Call):
                        fn = child.func
                        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
                        if name in ("read_text", "read_bytes", "open", "read_user_file", "read_user_bytes", "user_file_path", "user_directory_path"):
                            found.add((f.name, ".".join(stack) or "<module>"))
                    visit(child, stack)
            visit(tree, [])
        return found

    def test_every_read_site_is_classified(self):
        found = self.sites()
        self.assertEqual(sorted(found - set(self.SITES)), [], "分類していない読み取りがある（記事なら読む口を通し、ここに足す）")
        self.assertEqual(sorted(set(self.SITES) - found), [], "もうない読み取りを分類している")

    def test_gateway_sites_reference_the_gateway(self):
        """分類に対応する参照があるかの静的な目録。分岐の保護は実行試験で確かめる。"""
        for (name, qual), kind in self.SITES.items():
            if kind != self.GATEWAY:
                continue
            with self.subTest(site=f"{name}:{qual}"):
                tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))
                node = tree
                for part in qual.split("."):
                    node = next(n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
                calls = {getattr(c.func, "attr", getattr(c.func, "id", None)) for c in ast.walk(node) if isinstance(c, ast.Call)}
                self.assertTrue(calls & {"article_path", "read_user_file", "read_user_bytes", "user_file_path", "user_directory_path", "is_link"}, calls)


class ServerFilesTests(unittest.TestCase):
    """SERVER_FILES が、サーバーが読み込む同梱のモジュール（関数の中で遅れて読み込むものも）をすべて含む。"""

    def closure(self, files):
        local = {p.stem for p in SCRIPTS.glob("*.py")}
        seen, queue = set(), [Path(name).stem for name in files]
        while queue:
            name = queue.pop()
            if name in seen or name not in local:
                continue
            seen.add(name)
            tree = ast.parse((SCRIPTS / f"{name}.py").read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    queue += [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    queue.append(node.module.split(".")[0])
        return seen

    def test_server_files_are_closed(self):
        reached = self.closure(["wiki_mcp_server.py", "wiki_mcp_relay.py", "wiki_mcp_launch.py"])
        listed = {Path(name).stem for name in wiki_mcp_common.SERVER_FILES}
        missing = sorted(reached - listed - {"wiki_mcp_relay", "wiki_mcp_launch"})
        self.assertEqual(missing, [], "SERVER_FILES に足りないモジュール")

    def test_removing_wiki_links_is_caught(self):
        reached = self.closure(["wiki_mcp_server.py"])
        self.assertIn("wiki_links", reached)
        listed = {Path(name).stem for name in wiki_mcp_common.SERVER_FILES} - {"wiki_links"}
        self.assertIn("wiki_links", reached - listed)


if __name__ == "__main__":
    unittest.main()
