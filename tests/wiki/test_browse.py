"""閲覧（browse）の中核と静的の書き出しの試験。

設計は `docs/plans/wiki-browse-stage1-2026-11-09.md`。試験は設計の「守ること」に沿って並べる。関係表の試験は
PyYAML がなければ飛ばす。Linux でしか作れない名前（NFC と NFD、`x.md` と `x.MD`、`a\\b.md`）の試験は、
その OS でだけ流す。サーバーの試験は `tests/wiki/test_browse_server.py` にある。

実行:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py -v
"""
from __future__ import annotations

import contextlib
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

wiki_browse._load()
HAS_YAML = core.wiki_graph_extract is not None
LINUX = sys.platform.startswith("linux")


def reads_via(fn):
    """入力の中身を読む口（fs.read_input）を、fn(パス) に差し替える。fn の PermissionError は「分からない」にする。

    入力は層の口で読む（構造の直しの設計の 3）。試験は、読み取りの失敗をこの口に入れる。
    """
    def read(root, rel):
        path = Path(root) / rel
        try:
            return fn(path)
        except PermissionError as e:
            raise fs.failure(fs.Unknown, f"open_read: {type(e).__name__}", str(path)) from None
    return mock.patch.object(fs, "read_input", read)


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


# ファイルに触れた記録。集めているあいだだけ list にする。監査フックは外せないので、None のあいだは何もしない。
_ACCESS: "list | None" = None
LISTING = ("os.listdir", "os.scandir")
_AUDIT_EVENTS = ("open", *LISTING)
_HOOKED = False


def _audit(event, args):
    seen = _ACCESS
    if seen is not None and event in _AUDIT_EVENTS and args:
        seen.append((event, args[0]))


def _recorder(seen: list, kind: str, real):
    def call(path, *args, **kwargs):
        seen.append((kind, path))
        return real(path, *args, **kwargs)
    return call


@contextlib.contextmanager
def recording_access():
    """このブロックのあいだに開いた、一覧した、属性を調べたパスを、（種類, パス）の組で集める。

    開く（open）と一覧（os.listdir、os.scandir）は監査フックで捕まえるので、どの API から呼んでも漏れない。
    属性を調べるだけの呼び出しには監査の事象がないので、os.stat、os.lstat と os.path の判定を包んで捕まえる。
    """
    global _ACCESS, _HOOKED
    if not _HOOKED:
        sys.addaudithook(_audit)
        _HOOKED = True
    seen: list = []
    with contextlib.ExitStack() as stack:
        for name in ("stat", "lstat"):
            stack.enter_context(mock.patch.object(os, name, new=_recorder(seen, f"os.{name}", getattr(os, name))))
        for name in ("exists", "lexists", "isdir", "isfile", "islink"):
            stack.enter_context(mock.patch.object(os.path, name,
                                                  new=_recorder(seen, f"os.path.{name}", getattr(os.path, name))))
        _ACCESS = seen
        try:
            yield seen
        finally:
            _ACCESS = None


def touched_under(seen: list, dirs, kinds=None, exact: bool = False) -> list:
    """集めた組のうち、パスが dirs のどれか（exact でなければ、その下も）であるもの。kinds で種類を絞る。"""
    roots = [os.path.normcase(os.path.abspath(d)) for d in dirs]
    hits = []
    for kind, item in seen:
        if item is None or isinstance(item, int) or (kinds is not None and kind not in kinds):
            continue   # ファイル記述子と、絞った種類の外
        try:
            p = os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(item))))
        except (TypeError, ValueError):
            continue
        if any(p == r or (not exact and p.startswith(r + os.sep)) for r in roots):
            hits.append((kind, p))
    return hits


class TempWiki(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.wiki = self.base / "work" / "Wiki"
        self.wiki.mkdir(parents=True)
        # 入口（wiki_root）は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページではない。
        write(self.wiki, "SCHEMA.md", "# スキーマ\n")
        self.data = self.base / "data"
        self._env = mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.data)})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def build(self, out=None, raw=None) -> dict:
        with redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
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
        with redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            report = wiki_browse.build(self.wiki, str(self.base / "site2"), None)
        self.assertEqual((site1 / "a.html").read_bytes(), b"keep")
        self.assertEqual(sorted(p.name for p in site1.iterdir()), ["a.html"])
        out = Path(os.path.realpath(report["out"]))
        for f in out.rglob("*.html"):
            self.assertTrue(os.path.realpath(f).startswith(str(out) + os.sep), f)

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

def link_dir(link: Path, target: Path) -> bool:
    """ディレクトリへのシンボリックリンクを作る。作れなければ、Windows ではジャンクションにする。"""
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        if os.name != "nt":
            return False
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
        return True


class SignatureTest(TempWiki):
    def test_linked_indexes_dir_is_refused_and_reported(self):
        write(self.wiki, "a.md", page("# A"))
        split = self.base / "split-indexes"
        write(split, "contents.md", "# OLD_NAV\n\n- [[a]]\n")
        if not link_dir(self.wiki / "indexes", split):
            self.skipTest("ディレクトリのリンクを作れない")
        before = core.signature(self.wiki)
        c = build_core(self.wiki)
        self.assertNotIn("OLD_NAV", c.render_data("nav.js"))
        self.assertTrue(any(d.get("kind") == "link" and d.get("path") == "indexes" for d in c.diagnostics))
        write(split, "contents.md", "# NEW_NAV_LONGER\n\n- [[a]]\n")
        self.assertEqual(core.signature(self.wiki), before)

    def test_link_loop_terminates_and_skipped_dirs_are_ignored(self):
        write(self.wiki, "concepts/a.md", page("# A"))
        write(self.wiki, "raw/x.md", "raw 1\n")
        link_dir(self.wiki / "concepts" / "loop", self.wiki)
        before = core.signature(self.wiki)
        write(self.wiki, "raw/x.md", "raw 2 longer\n")           # 最上位の raw/ は入力でない
        self.assertEqual(core.signature(self.wiki), before)
        write(self.wiki, "concepts/a.md", page("# A longer"))
        self.assertNotEqual(core.signature(self.wiki), before)
        write(self.wiki, "graph/ontology.yaml", "node_types: {}\n")
        self.assertNotEqual(core.signature(self.wiki), before)


class UnreadableExcludedDirTest(TempWiki):
    """入力でない最上位のディレクトリ（raw など）の一覧を作れなくても、閲覧は止まらない。"""

    def denied(self):
        real = os.scandir
        blocked = {self.wiki / name for name in ("raw", "assets", ".wiki-cache")}

        def scandir(path="."):
            if Path(path) in blocked:
                raise PermissionError("denied")
            return real(path)
        return mock.patch.object(os, "scandir", scandir)

    def test_build_and_inputs_ignore_unreadable_raw(self):
        write(self.wiki, "concepts/a.md", page("# A"))
        write(self.wiki, "raw/x.md", "raw\n")
        write(self.wiki, "assets/y.md", "asset\n")
        with self.denied():
            # assets/ は図の svg の入力（ADR-0030）。一覧を作れないことは、大きさのない asset_dir の項目で表し、
            # 閲覧は止めない（図の描画の設計の 6.1）
            self.assertEqual([e[:4] for e in core.input_list(self.wiki)][-1], ("asset_dir", "assets", None, None))
            self.assertEqual([e[0] for e in core.input_list(self.wiki)], ["page", "asset_dir"])
            report = self.build(self.base / "site")
            # stop と動いているかの確かめの最初の手順も、入力でない場所に触れない
            state, _rec = fs.probe_server(self.wiki, wiki_browse.browse_dir(), wiki_browse._state_dir(self.wiki),
                                          fs.owner_of(self.wiki))
            self.assertEqual(state, "not-running")
        self.assertEqual(report["pages"], 1)

    def test_unreadable_page_dir_still_fails(self):
        write(self.wiki, "concepts/a.md", page("# A"))
        real = os.scandir

        def scandir(path="."):
            if Path(path) == self.wiki / "concepts":
                raise PermissionError("denied")
            return real(path)
        with mock.patch.object(os, "scandir", scandir):
            with self.assertRaises(core.InputsUnknown):
                core.input_list(self.wiki)


class NamesTest(unittest.TestCase):
    def test_directories_differing_only_in_case_share_one_spelling(self):
        # 大文字と小文字を区別しない書き出し先でも、一覧と書き出し先の綴りが合う（実装の 1 回目のレビューの重大 2）
        names = core.assign_names(["A/x", "a/y", "A/B/p", "a/b/q"])
        dirs = {}
        for name in names.values():
            parts = name.split("/")[:-1]
            for i in range(1, len(parts) + 1):
                prefix = "/".join(parts[:i])
                dirs.setdefault(prefix.casefold(), set()).add(prefix)
        self.assertTrue(all(len(v) == 1 for v in dirs.values()), dirs)
        self.assertEqual(len({n.casefold() for n in names.values()}), 4)
        # 書き出して、もう一度書き出すと、門を通る
        files = {name: name.encode("utf-8") for name in names.values()}
        with tempfile.TemporaryDirectory() as d:
            base = os.path.realpath(d)
            wiki = os.path.join(base, "wiki")
            os.makedirs(wiki)
            out = os.path.join(base, "site")
            owner = fs.owner_of(wiki)
            for _ in range(2):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(fs.build(wiki, out, files, False, owner, os.path.join(base, "data", "browse")),
                                     0)

    def test_no_output_directory_looks_like_a_short_name(self):
        # 8.3 の短い名前と同じ形のディレクトリの名前は、ほかの出力のディレクトリの短い名前で、同じディレクトリに
        # 届きうる（実装の 6 回目のレビューの重大 1）。どの出力のディレクトリも、その形にしない
        ids = ["data/a", "data~a~1/b", "LONGDI~1/c", "x~1.ab/d", "a~b/e", "ok/f"]
        names = core.assign_names(ids)
        for name in names.values():
            for part in name.split("/")[:-1]:
                self.assertFalse(core.looks_like_short_name(part), (name, part))
        self.assertEqual(names["ok/f"], "ok/f.html")
        for text, want in (("DATA~A~1", True), ("data~a~1", True), ("LONGDI~1.TXT", True), ("a~b", True),
                           ("data", False), ("data~a451b6e6", False), ("a~1.html", False), ("x.y.z~1", False)):
            self.assertEqual(core.looks_like_short_name(text), want, text)

    def test_reserved_names(self):
        for name in ("CON", "con", "COM0", "COM¹", "LPT²", "CONIN$", "CONOUT$", "nul.txt", "COM9 "):
            out = core.export_name(f"x/{name}")
            last = out.split("/")[-1]
            self.assertFalse(core.is_reserved_windows(last[:-len(".html")]), (name, out))
            self.assertIn("~", last, name)

    def test_generator_names_are_avoided(self):
        for pid in ("index", "data/x", "assets/x", ".browse-generation/a", "x/.browse-work/b", ".BROWSE-GENERATION/a"):
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
        # アイコンがないことを <head> で宣言する（製品の Chrome と Edge が /favicon.ico を要求して 404 になるのを防ぐ）。
        # data: は CSP の img-src が許す値でなければならない
        head = html[:html.index("</head>")]
        self.assertIn('<link rel="icon" href="data:,">', head)
        self.assertIn("img-src 'self' data:", core.CSP)
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

    @unittest.skipUnless(LINUX, "Linux でだけ同時に置ける名前")
    def test_nfc_colliding_split_indexes_get_distinct_ids(self):
        write(self.wiki, "indexes/が.md", "- [[a]]\n")
        write(self.wiki, unicodedata.normalize("NFD", "indexes/が") + ".md", "- [[a]]\n")
        write(self.wiki, "a.md", page("# A"))
        html = build_core(self.wiki).render_index()
        ids = __import__("re").findall(r'id="(_g[^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_unreadable_split_index_has_no_dangling_group_link(self):
        write(self.wiki, "index.md", "- [[indexes/people]]\n")
        target = write(self.wiki, "indexes/people.md", "- [[p]]\n")
        real = Path.read_bytes

        def flaky(self_):
            if Path(self_) == target:
                raise PermissionError("busy")
            return real(self_)
        with reads_via(flaky):
            c = build_core(self.wiki)
        items = c._nav_json()["groups"][0]["items"]
        self.assertNotEqual(items[0]["state"], "group")
        html = c.render_index()
        for anchor in __import__("re").findall(r'href="#([^"]+)"', html):
            self.assertIn(f'id="{anchor}"', html)

    def test_navigation(self):
        write(self.wiki, "index.md", "- [[pre]]\n\n# 上\n\n## 概念\n\n- [[a]] — 説明 [[b]]\n  - [[b]]\n"
                                     "- [[missing]] — 関連：[[a]]\n- [[indexes/people]]\n- 説明だけ\n")
        write(self.wiki, "indexes/people.md", page("- [[p]]", title="人物"))
        for name in ("pre", "a", "b", "p", "lone"):
            write(self.wiki, f"{name}.md", page(f"# {name}", type="concept"))
        c = build_core(self.wiki)
        nav = c._nav_json()
        self.assertEqual(nav["protocol_version"], 2)
        groups = nav["groups"]
        # N4: index.md のグループは木のいちばん上に置かない。自分の項目は「索引」のグループに、見出しのグループは上に並ぶ
        top = groups[0]
        self.assertEqual(top["title"], "Index")
        # N9: ページの項目は、最初のタグのグループ（タグがなければ「タグなし」）に移る
        self.assertEqual(top["items"], [])
        self.assertEqual([g["title"] for g in top["children"]], ["タグなし"])
        self.assertEqual(top["children"][0]["items"][0]["path"], "pre.html")
        self.assertEqual(top["children"][0]["items"][0]["id"], "pre")
        concepts = groups[1]["children"][0]
        self.assertEqual(groups[1]["title"], "上")
        self.assertEqual(concepts["title"], "概念")
        # N6: グループへの項目の名前は、行き先のグループの名前。N9-5: ページでない項目は元のグループに残る
        states = [(i["state"], i["label"]) for i in concepts["items"]]
        self.assertEqual(states, [("unresolved", "missing"), ("group", "人物")])
        self.assertEqual([(i["state"], i["label"]) for g in concepts["children"] for i in g["items"]],
                         [("resolved", "a"), ("resolved", "b")])
        people = groups[2]
        self.assertEqual(people["title"], "人物")
        self.assertTrue(people["id"].startswith("_gf"))
        self.assertEqual(people["count"], 1)
        self.assertEqual(concepts["count"], 2)
        rest = groups[-1]
        self.assertEqual(rest["title"], "Index にないページ")
        # N7: 種類の子のグループの名前は日本語にする
        self.assertEqual([g["title"] for g in rest["children"]], ["コンセプト"])
        self.assertEqual([i["path"] for g in rest["children"] for t in g["children"] for i in t["items"]],
                         ["lone.html"])
        for g in core._walk(c.nav_groups):
            if g.get("origin") == "tag":
                self.assertRegex(g["id"], r"\A_gt[0-9]+\Z")


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

    def test_bad_yaml_dates_do_not_stop_the_core(self):
        write(self.wiki, "graph/ontology.yaml", "node_types: {}\npredicates: {}\nupdated: 2026-99-99\n")
        write(self.wiki, "a.md", page("# A", type="concept"))
        c = build_core(self.wiki)   # 中核は組み立てられ、関係表だけが使えない
        self.assertEqual(c.relations_state, "error")
        self.assertIn("<h1", c.render_page("a"))
        write(self.wiki, "graph/ontology.yaml", self.ONTOLOGY)
        (self.wiki / "b.md").write_bytes(b"---\ntype: concept\ncreated: 2026-99-99\n---\n# B\n")
        c = build_core(self.wiki)   # ページの誤った日付でも、ほかのページの関係表は作れる
        self.assertEqual(c.relations_state, "ok")
        self.assertIn("<h1", c.render_page("b"))

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

# ---------------------------------------------------------------------------
# 構造の直しの設計の 4.1、9.2: 読めない入力は、その入力がない Wiki と同じに描き、読み取りの印を足す
# ---------------------------------------------------------------------------

def _view(c: core.Core) -> dict:
    """比べる値（リンクの解決、被リンク、未解決リンク、ナビゲーション、関係表、各ページの HTML）。

    読み取りの印（「不完全」と、診断の read_error）は、決まった場所に置くので、比べる前に取り除く。世代の識別子は
    読み取りの情報から作るので、そろえる（設計の 9.2）。
    """
    import re
    strip = re.compile(r'<p class="notice incomplete">[^<]*</p>\n?|<section id="_incomplete">\s*</section>\n?')

    def clean(text):
        return strip.sub("", text.replace(c.generation, "GEN"))
    return {
        "links": {pid: [(r["state"], r.get("id")) for r in c.links[pid]] for pid in sorted(c.drawn)},
        "backlinks": c.backlinks,
        "unresolved": c.unresolved(),
        "nav": json.dumps(c._nav_json()["groups"], ensure_ascii=False),
        "relations": json.dumps(c.relations, ensure_ascii=False, sort_keys=True),
        "pages": {name: clean(c.render(name)) for name in c.page_names()},
    }


class UnreadableInputTest(TempWiki):
    def make(self, root: Path):
        write(root, "SCHEMA.md", "# スキーマ\n")
        write(root, "concepts/a.md", page("# A\n\n[[b]] [[missing]] [[c#見出し]] [[x]]", type="concept"))
        write(root, "concepts/b.md", page("# B\n\n[[a]]", type="concept"))
        write(root, "concepts/c.md", page("# C\n\n## 見出し", type="concept"))
        write(root, "one/x.md", page("# x1"))
        write(root, "two/x.md", page("# x2"))
        write(root, "index.md", "- [[a]]\n- [[indexes/more]]\n")
        write(root, "indexes/more.md", "- [[b]]\n")

    def unreadable(self, target: Path):
        real = Path.read_bytes

        def fn(path):
            if path == target:
                raise PermissionError("busy")
            return real(path)
        return reads_via(fn)

    def lint_with_failure(self, root: Path, target: Path) -> list:
        real = Path.read_text

        def read_text(path, *a, **k):
            if Path(path) == target:
                raise PermissionError("busy")
            return real(path, *a, **k)
        with mock.patch.object(Path, "read_text", read_text):
            return lint_broken(root)

    def test_unreadable_page_is_drawn_as_removed(self):
        for rel in ("concepts/a.md", "two/x.md", "concepts/c.md"):
            with self.subTest(rel=rel):
                u_root = self.base / f"U-{rel.replace('/', '_')}"
                r_root = self.base / f"R-{rel.replace('/', '_')}"
                self.make(u_root)
                self.make(r_root)
                (r_root / rel).unlink()
                with self.unreadable(u_root / rel):
                    u = build_core(u_root)
                r = build_core(r_root)
                self.assertEqual(_view(u), _view(r))
                # 印は、なければならない
                self.assertEqual(u.unreadable_pages, [rel])
                self.assertIn({"kind": "read_error", "page": rel[:-3], "reason": "os"}, u.diagnostics)
                any_page = sorted(u.page_names())[0]
                self.assertIn("不完全", u.render(any_page))
                self.assertIn("不完全", u.render_index())
                self.assertEqual(json.loads(u.render_data("data/manifest.js")[len("window.WIKI_MANIFEST="):-2])
                                 ["incomplete"]["unreadable_pages"], 1)
                # 未解決リンクは、同じ失敗を入れた lint と同じ（設計の 4.3 の範囲で）
                self.assertEqual(u.unresolved(), self.lint_with_failure(u_root, u_root / rel))

    def test_unreadable_index_is_drawn_as_removed(self):
        u_root, r_root = self.base / "U", self.base / "R"
        self.make(u_root)
        self.make(r_root)
        (r_root / "indexes/more.md").unlink()
        with self.unreadable(u_root / "indexes/more.md"):
            u = build_core(u_root)
        r = build_core(r_root)
        self.assertEqual(_view(u)["nav"], _view(r)["nav"])
        self.assertIn("ナビゲーションは不完全", u.render_index())
        self.assertTrue(u._nav_json()["incomplete"])

    @unittest.skipUnless(HAS_YAML, "PyYAML がない")
    def test_unreadable_ontology_is_drawn_as_absent_with_mark(self):
        u_root, r_root = self.base / "U", self.base / "R"
        self.make(u_root)
        self.make(r_root)
        write(u_root, "graph/ontology.yaml", "node_types: {concept: {}}\npredicates: {}\n")
        with self.unreadable(u_root / "graph/ontology.yaml"):
            u = build_core(u_root)
        r = build_core(r_root)
        self.assertEqual(_view(u)["links"], _view(r)["links"])
        self.assertIn("オントロジーを読めない", u.render("concepts/a.html"))
        self.assertTrue(json.loads(u.render_data("data/manifest.js")[len("window.WIKI_MANIFEST="):-2])
                        ["incomplete"]["unreadable_ontology"])

    def test_unlistable_name_set_is_not_taken(self):
        # 名前の集合が分からないときは、全体を採らない（設計の 4.1）
        self.make(self.wiki)
        real = os.scandir

        def denied(path="."):
            if Path(path) == self.wiki / "one":
                raise PermissionError("denied")
            return real(path)
        with mock.patch.object(os, "scandir", denied):
            with self.assertRaises(core.InputsUnknown):
                core.take_snapshot(self.wiki)

    def test_ontology_only_change_changes_the_signature(self):
        # 入力の一覧は 1 つで、印もそこから作る（設計の 4。4 回目のレビューの重大 7）
        self.make(self.wiki)
        before = core.signature(self.wiki)
        write(self.wiki, "graph/ontology.yaml", "node_types: {}\n")
        mid = core.signature(self.wiki)
        self.assertNotEqual(mid, before)
        write(self.wiki, "graph/ontology.yaml", "node_types: {concept: {}}\n")
        self.assertNotEqual(core.signature(self.wiki), mid)


class PartialFailureTest(TempWiki):
    """部分の失敗（構造の直しの設計の 7.2。実装の 1 回目のレビューの重大 3）。1 つの入力の解釈の例外は、その入力を
    「描けない」か「読めない」と示し、全体を止めない。"""

    def setUp(self):
        super().setUp()
        write(self.wiki, "concepts/a.md", page("# A\n\n[[b]]", type="concept"))
        write(self.wiki, "concepts/b.md", page("# B\n\nBOOM [[a]]", type="concept"))
        write(self.wiki, "index.md", "- [[a]]\n- [[indexes/more]]\n")
        write(self.wiki, "indexes/more.md", "BOOMINDEX\n\n- [[b]]\n")

    def parser_failing_on(self, needle):
        real = wiki_pages.new_parser

        def new_parser():
            parser = real()
            original = parser.parse

            def parse(text, env=None):
                if needle in text:
                    raise ValueError("injected")
                return original(text, env)
            parser.parse = parse
            return parser
        return mock.patch.object(wiki_pages, "new_parser", new_parser)

    def test_body_parse_failure_draws_that_page_as_broken(self):
        with self.parser_failing_on("BOOM ["):
            c = build_core(self.wiki)
            self.assertIn("このページを描けない", c.render("concepts/b.html"))
            self.assertIn("concepts/b", c.render_failures)
            self.assertIn("被リンク", c.render("concepts/a.html"))
        self.assertIn("concepts/b.md", c.unreadable_pages)
        self.assertIn("不完全", c.render("concepts/a.html"))

    def test_frontmatter_failure_is_read_as_unreadable(self):
        real = wiki_lint.parse_frontmatter_raw

        def failing(text):
            if "BOOM [" in text:
                raise ValueError("injected")
            return real(text)
        with mock.patch.object(wiki_lint, "parse_frontmatter_raw", failing):
            c = build_core(self.wiki)
        self.assertNotIn("concepts/b", c.drawn)
        self.assertIn({"kind": "read_error", "page": "concepts/b", "reason": "parse"}, c.diagnostics)
        self.assertIn("concepts/b.md", c.unreadable_pages)

    def test_index_parse_failure_is_read_as_unreadable(self):
        with self.parser_failing_on("BOOMINDEX"):
            c = build_core(self.wiki)
            html = c.render_index()
        self.assertIn("ナビゲーションは不完全", html)
        for anchor in __import__("re").findall(r'href="#([^"]+)"', html):
            self.assertIn(f'id="{anchor}"', html)

    @unittest.skipUnless(HAS_YAML, "PyYAML がない")
    def test_relations_parse_failure_keeps_pages(self):
        # 関係表は、読み込みのときに作った共有のパーサー（wiki_pages._MD）も使う。その解析の例外でも、関係表だけを
        # 使えないにして、ページは描く（実装の 2 回目のレビューの重大 4）
        write(self.wiki, "graph/ontology.yaml", "node_types: {concept: {}}\npredicates: {}\n")
        original = wiki_pages._MD.parse

        def parse(text, env=None):
            if "BOOM [" in text:
                raise ValueError("injected")
            return original(text, env)
        with mock.patch.object(wiki_pages._MD, "parse", parse):
            c = build_core(self.wiki)
            self.assertIn("被リンク", c.render("concepts/a.html"))
        self.assertIn("concepts/b", c.drawn)

    def test_relations_failure_is_contained(self):
        # 関係表の組み立てのどこで思わない例外が出ても、関係表だけを使えないにする
        write(self.wiki, "graph/ontology.yaml", "node_types: {concept: {}}\npredicates: {}\n")
        with mock.patch.object(core.Core, "_relations", side_effect=ValueError("x")):
            c = build_core(self.wiki)
        self.assertEqual(c.relations_state, "error")
        self.assertIn("オントロジーを読めない", c.render("concepts/a.html"))

    def test_undecodable_page_is_marked_incomplete(self):
        (self.wiki / "concepts" / "b.md").write_bytes(b"\xff\xfe broken")
        c = build_core(self.wiki)
        self.assertIn("concepts/b.md", c.unreadable_pages)
        self.assertEqual(c.snapshot.transient, [])        # 読み直しても変わらないので、サーバーはやり直さない
        self.assertIn("不完全", c.render("concepts/a.html"))

    def test_failed_rebuild_keeps_stale_with_same_signature(self):
        state = wiki_browse.BrowseState(self.wiki)
        c, stale = state.get()
        self.assertIsNone(stale)
        state.failed = "InputsUnknown"
        self.assertEqual(state._answer(c, c.snapshot.signature, "failed"), (c, "failed"))
        state.failed = None
        self.assertEqual(state._answer(c, c.snapshot.signature, None), (c, None))


class CoreHoldsNoMachineInfoTest(TempWiki):
    """作りの確かめ（構造の直しの設計の 8）。機械の情報を書いていない Wiki を、目印の文字を含むディレクトリに
    置き、内容と、組み立てたあとの Core の値をすべてたどって、目印の文字と Path がないことを確かめる。"""

    def test_no_path_or_marker_in_core(self):
        wiki = self.base / "MACHINEMARK" / "wiki"
        write(wiki, "SCHEMA.md", "# スキーマ\n")
        write(wiki, "concepts/a.md", page("# A\n\n[[b]] [[missing]]", type="concept", raw="~/x.pdf"))
        write(wiki, "concepts/b.md", page("# B"))
        write(wiki, "index.md", "- [[a]]\n")
        c = build_core(wiki)
        c.render_all("link")
        seen = set()
        bad = []

        def walk(value, where):
            if id(value) in seen:
                return
            seen.add(id(value))
            if isinstance(value, os.PathLike):
                bad.append(f"{where}: Path")
            elif isinstance(value, str):
                if "MACHINEMARK" in value:
                    bad.append(f"{where}: 目印")
            elif isinstance(value, dict):
                for k, v in value.items():
                    walk(k, where + ".key")
                    walk(v, f"{where}[{k!r}]")
            elif isinstance(value, (list, tuple, set, frozenset)):
                for i, v in enumerate(value):
                    walk(v, f"{where}[{i}]")
            elif hasattr(value, "__dict__") and type(value).__module__ in ("wiki_browse_core",):
                for k, v in vars(value).items():
                    walk(v, f"{where}.{k}")
        walk(c, "core")
        self.assertEqual(bad[:5], [])


class BuildTest(TempWiki):
    def setUp(self):
        super().setUp()
        write(self.wiki, "concepts/a.md", page("# A\n\n[[b]]", type="concept"))
        write(self.wiki, "concepts/b.md", page("# B", type="concept"))

    def build_logged(self, out=None, raw=None):
        """書き出して、(報告, 標準エラー) を返す。"""
        err = io.StringIO()
        with redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            report = wiki_browse.build(self.wiki, None if out is None else str(out), raw)
        return report, err.getvalue()

    def work_entries(self, out) -> list:
        work = Path(str(out) + ".browse-work")
        return sorted(p.name for p in work.iterdir())

    def test_default_build_and_read_only(self):
        before = tree_state(self.wiki)
        report = self.build()
        out = Path(report["out"])
        self.assertTrue((out / "concepts/a.html").is_file())
        self.assertTrue((out / fs.MANIFEST).is_file())
        self.assertTrue((out / "assets/app.js").is_file())
        self.assertEqual(tree_state(self.wiki), before)
        # 2 度目は前の世代と入れ替わる。作業用には目印とロックだけが残る
        (self.wiki / "concepts/b.md").unlink()
        report2 = self.build()
        self.assertFalse((out / "concepts/b.html").exists())
        self.assertNotEqual(report["generation"], report2["generation"])
        self.assertEqual(self.work_entries(out), [fs.WORK_MARKER, "build.lock"])

    def test_refused_destinations(self):
        before = tree_state(self.wiki)
        refused = (fs.Stop, fs.Unknown, fs.Absent, wiki_browse.Failed)
        for out in (self.wiki / "preview", self.wiki, self.base / "work", self.data / "browse" / "x",
                    self.data, self.base):
            with self.assertRaises(refused, msg=str(out)):
                self.build(out)
        stray = self.base / "stray"
        stray.mkdir()
        (stray / "x.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(fs.Stop):     # browse が作っていないものがある（門）
            self.build(stray)
        self.assertEqual((stray / "x.txt").read_text(encoding="utf-8"), "x")
        with self.assertRaises(fs.Absent):   # 親がない（0.10.0 と同じく失敗する）
            self.build(self.base / "no-parent" / "out")
        self.assertFalse((self.base / "no-parent").exists())
        self.assertEqual(tree_state(self.wiki), before)

    def test_short_name_shaped_directories_build_twice(self):
        # 8.3 の短い名前が作られる NTFS でも、書き出した世代が次の書き出しの門を通る（実装の 6 回目のレビューの重大 1）
        write(self.wiki, "data/a.md", page("# A"))
        write(self.wiki, "data~a~1/b.md", page("# B"))
        out = self.base / "site"
        for _ in range(2):
            report = self.build(out)
            self.assertEqual(report["pages"], 4)
        files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.html") if p.parent.name.startswith("data"))
        self.assertEqual(len(files), 2, files)
        self.assertEqual(len({f.split("/")[0] for f in files}), 2, files)

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
        with self.assertRaises(fs.Stop):
            self.build(site / "nested")
        with self.assertRaises(fs.Stop):
            self.build(self.base / "exports")

    def test_out_with_user_files_is_refused_and_kept(self):
        # 書き出し先に、browse が作っていないものがある。止まり、理由を挙げ、前のままにする（設計の 6.3、10）
        out = self.base / "site"
        self.build(out)
        (out / "notes.txt").write_text("my notes", encoding="utf-8")
        before = tree_state(out)
        with self.assertRaises(fs.Stop) as cm:
            self.build(out)
        self.assertIn("notes.txt", str(cm.exception))
        self.assertEqual(tree_state(out), before)
        (out / "notes.txt").unlink()
        (out / "index.html").write_text("edited", encoding="utf-8")      # 一覧にある名前のファイルを書き換えた
        with self.assertRaises(fs.Stop):
            self.build(out)
        self.assertEqual((out / "index.html").read_text(encoding="utf-8"), "edited")

    def test_legacy_out_is_refused_and_legacy_default_is_replaced(self):
        # 0.10.0 の書き出し（一覧に名前とハッシュがない）は、--out なら止め、既定の書き出し先なら置き換える（設計の 10）
        out = self.base / "site"
        out.mkdir()
        (out / fs.MANIFEST).write_text(json.dumps({"generation": "x", "published_seq": 3}), encoding="utf-8")
        (out / "index.html").write_text("<p>0.10.0</p>", encoding="utf-8")
        with self.assertRaises(fs.Stop) as cm:
            self.build(out)
        self.assertIn("0.10.0", str(cm.exception))
        default = self.data / "browse" / wiki_browse.common.wiki_key(self.wiki)
        default.mkdir(parents=True)
        (default / fs.MANIFEST).write_text(json.dumps({"generation": "x", "published_seq": 3}), encoding="utf-8")
        (default / "index.html").write_text("<p>0.10.0</p>", encoding="utf-8")
        work = Path(str(default) + ".browse-work")
        work.mkdir()
        (work / fs.WORK_MARKER).write_text("", encoding="utf-8")
        (work / "seq").write_text("7\n", encoding="utf-8")
        (work / "build-report.json").write_text("{}", encoding="utf-8")
        report, err = self.build_logged()
        self.assertTrue((Path(report["out"]) / "concepts/a.html").is_file())
        # 0.10.0 の seq と build-report.json は消す。目印の持ち主が違うので、警告を出して引き継ぐ
        self.assertEqual(self.work_entries(default), [fs.WORK_MARKER, "build.lock"])
        self.assertIn("別の Wiki が使っていた場所を引き継いだ", err)

    def test_recovery_restores_highest_numbered_old(self):
        # 入れ替えの途中で止まった形（書き出し先がなく、作業用に old-N がある）。名前の番号がいちばん大きい old-N を、
        # 門を通るときだけ戻す。番号を決めるのに一覧は読まない（設計の 6.4 の 3）
        out = self.base / "site"
        self.build(out)
        work = Path(str(out) + ".browse-work")
        os.rename(out, work / "old-5")
        (work / "old-2").mkdir()                       # 番号の小さい、世代でないもの
        (work / "old-2" / "x.txt").write_text("x", encoding="utf-8")
        report, err = self.build_logged(out)
        self.assertIn("最後に公開した世代を戻した（old-5）", err)
        self.assertTrue((out / "index.html").is_file())
        self.assertEqual(self.work_entries(out), [fs.WORK_MARKER, "build.lock"])

    def test_recovery_skips_unrestorable_old(self):
        # いちばん大きい番号の old-N が門を通らなければ、戻さない。書き出し先は前のまま（ない）から新しい世代になる
        out = self.base / "site"
        self.build(out)
        work = Path(str(out) + ".browse-work")
        shutil.rmtree(out)
        (work / "old-9").mkdir()
        (work / "old-9" / "user.txt").write_text("x", encoding="utf-8")
        report, err = self.build_logged(out)
        self.assertNotIn("戻した", err)
        self.assertFalse((out / "user.txt").exists())
        self.assertTrue((out / "index.html").is_file())

    def test_unlistable_directory_fails_build_and_keeps_previous(self):
        out = self.base / "site"
        self.build(out)
        before = (out / "index.html").read_bytes()
        real = os.scandir

        def denied(path="."):
            if Path(path) == self.wiki:
                raise PermissionError("denied")
            return real(path)
        with mock.patch.object(os, "scandir", denied), redirect_stderr(io.StringIO()):
            code = wiki_browse.main(["build", str(self.wiki), "--out", str(out)])
        self.assertEqual(code, wiki_browse.EXIT_FAILED)
        self.assertEqual((out / "index.html").read_bytes(), before)

    def test_recovery_into_empty_output_dir(self):
        out = self.base / "site"
        self.build(out)
        work = Path(str(out) + ".browse-work")
        os.rename(out, work / "old-1")
        out.mkdir()   # 再実行するラッパーなどが、空の出力先を作り直した
        report, err = self.build_logged(out)
        self.assertIn("戻した（old-1）", err)
        self.assertTrue((out / "index.html").is_file())
        self.assertEqual(self.work_entries(out), [fs.WORK_MARKER, "build.lock"])

    def test_failed_core_leaves_no_tmp_and_keeps_error(self):
        out = self.base / "site"
        self.build(out)
        before = (out / "index.html").read_bytes()
        with mock.patch.object(core.Core, "__init__", side_effect=core.NameCollision("x")):
            with self.assertRaises(core.NameCollision):
                self.build(out)
        self.assertEqual((out / "index.html").read_bytes(), before)
        self.assertEqual(self.work_entries(out), [fs.WORK_MARKER, "build.lock"])

    def test_wiki_changing_while_reading_is_retried(self):
        # 読んでいるあいだに Wiki が変われば、その写しを採らない。3 回までやり直す（設計の 4.2）
        out = self.base / "site"
        real = core.input_list
        calls = {"n": 0}

        def changing(root):
            calls["n"] += 1
            if calls["n"] == 2:    # 1 回目の写しの、読んだあとの走査
                write(self.wiki, "concepts/c.md", page("# C"))
            return real(root)
        with mock.patch.object(core, "input_list", changing):
            report = self.build(out)
        self.assertTrue((out / "concepts/c.html").is_file())
        self.assertEqual(report["pages"], 3)

        def always(root):
            write(self.wiki, "concepts/c.md", page("# C" + "x" * calls["n"]))
            calls["n"] += 1
            return real(root)
        before = (out / "index.html").read_bytes()
        with mock.patch.object(core, "input_list", always):
            with self.assertRaises(wiki_browse.Failed):
                self.build(out)
        self.assertEqual((out / "index.html").read_bytes(), before)

    def test_machine_info_in_output_is_a_warning(self):
        # 生成器が足したかを推し量らない。出力に絶対パスがあれば警告を出し、書き出しは止めない（設計の 8、10）
        out = self.base / "site"
        original = core.Core.render_index
        wiki = str(self.wiki)

        def leaky(self_, stale=None):
            return original(self_, stale) + f"<!-- {wiki} -->"
        with mock.patch.object(core.Core, "render_index", leaky):
            report, err = self.build_logged(out)
        self.assertTrue((out / "index.html").is_file())
        self.assertTrue(any("index.html" in w and "絶対パス" in w for w in report["warnings"]), report["warnings"])
        self.assertIn("警告", err)

    def test_machine_info_forms_are_detected(self):
        root = "C:\\Users\\Alice\\Wiki"
        for leak in (root, root.replace("\\", "/"), json.dumps(root)[1:-1], "C%3A%2FUsers%2FAlice%2FWiki"):
            found = core.scan_machine_info({"a.html": f"x {leak} y".encode("utf-8")}, [root], [])
            self.assertEqual(found, [("a.html", "path")], leak)
        found = core.scan_machine_info({"a.html": b"x", "b.html": b"tok-12345678 y"}, [root], ["tok-12345678"])
        self.assertEqual(found, [("b.html", "token")])

    def test_concurrent_nested_builds_do_not_both_publish(self):
        site = self.base / "exports" / "site"
        site.parent.mkdir()
        env = {**os.environ, "INFO_HIVE_DATA_DIR": str(self.data)}
        cmd = [sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_browse.py"), "build", str(self.wiki), "--out"]
        site.mkdir()   # 親は空のディレクトリ、子はその中のまだないディレクトリ
        procs = [subprocess.Popen(cmd + [str(out)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                  text=True, encoding="utf-8") for out in (site, site / "nested", site / "nested")]
        outs = [p.communicate(timeout=180) for p in procs]
        codes = [p.returncode for p in procs]
        # 共通のロックで 1 つずつ走る。親が先なら子は親の中なので止まり、子が先なら親は空でないので止まる。
        # 初めての実行で、<data_dir> とその下を同時に作っても、止まらない（0.10.0 と同じ）
        parent_ok = codes[0] == 0
        child_ok = codes[1] == 0 or codes[2] == 0
        self.assertNotEqual(parent_ok, child_ok, (codes, outs))
        published = site if parent_ok else site / "nested"
        self.assertTrue((published / "index.html").is_file())
        self.assertTrue((published / fs.MANIFEST).is_file())
        if parent_ok:
            self.assertFalse((site / "nested").exists())

    def test_title_with_home_path_is_a_warning(self):
        home = str(Path.home())
        write(self.wiki, "sources/s.md", page("# S", type="source", title=home))
        write(self.wiki, "concepts/r.md", page("# R", type="concept", sources=["s"]))
        report = self.build(self.base / "site")
        self.assertTrue(any("concepts/r.html" in w for w in report["warnings"]), report["warnings"])

    def test_tilde_raw_is_text_in_link_mode(self):
        # ~ はホームに展開せず、文字で出す（設計の 8、10）
        write(self.wiki, "sources/s.md", page("# S", type="source", raw="~/papers/x.pdf"))
        report = self.build()   # 既定の書き出し先は link
        html = (Path(report["out"]) / "sources/s.html").read_text(encoding="utf-8")
        self.assertNotIn("file://", html)
        self.assertIn("<code>~/papers/x.pdf</code>", html)
        self.assertNotIn(str(Path.home()).replace("\\", "/"), html.replace("\\", "/"))
        self.assertEqual(report["warnings"], [])

    def test_user_written_path_is_a_warning(self):
        home = str(Path.home())
        write(self.wiki, "concepts/h.md", page(f"# H\n\nホームは `{home}` にある。\n"))
        report = self.build(self.base / "site")
        # 本文の冒頭は、索引のページの要約と検索の索引にも出る（探しやすさの設計の 4.2）。どれも入力の中身から来た警告
        self.assertEqual(sorted(w.split("（")[1].split("）")[0] for w in report["warnings"]),
                         ["concepts/h.html", "data/search.js", "index.html"], report["warnings"])

    def test_report_to_stdout_failure_keeps_exit_zero(self):
        # 公開したあとに標準出力へ書けなくても、警告を出そうとし、終了コードは 0（設計の 7、10）
        out = self.base / "site"

        class Broken(fs.Os):
            def stdout_write(self, text):
                raise OSError(5, "broken pipe")
        err = io.StringIO()
        with mock.patch.object(fs, "X", Broken()), redirect_stderr(err):
            code = wiki_browse.main(["build", str(self.wiki), "--out", str(out)])
        self.assertEqual(code, wiki_browse.EXIT_OK)
        self.assertTrue((out / "index.html").is_file())
        self.assertIn("知らせを出せなかった", err.getvalue())

    def test_unexpected_error_is_short_unless_debug(self):
        # 思わない例外でも、種類だけの短い知らせと、0 でない終了コード。スタックトレースは --debug のときだけ（設計の 7.2）
        for debug in (False, True):
            err = io.StringIO()
            with mock.patch.object(wiki_browse, "build", side_effect=RuntimeError("secret C:/x")), \
                    redirect_stderr(err):
                code = wiki_browse.main(["build", str(self.wiki)] + (["--debug"] if debug else []))
            self.assertEqual(code, wiki_browse.EXIT_FAILED)
            self.assertIn("RuntimeError", err.getvalue())
            self.assertEqual("Traceback" in err.getvalue(), debug)
            if not debug:
                self.assertNotIn("secret", err.getvalue())

    def test_markers_absent_everywhere(self):
        # Wiki、ホーム、data_dir、Wiki の外の入力の実体を、別々の目印の文字を含む場所にする（設計の 11）。
        wiki = self.base / "WIKIMARK"
        home = self.base / "HOMEMARK"
        ext = self.base / "EXTMARK"
        for d in (wiki, home, ext):
            d.mkdir()
        write(wiki, "concepts/a.md", page("# A\n\n[[b]] [[missing]]", type="concept"))
        write(wiki, "concepts/b.md", page("# B", type="source", raw="~/papers/x.pdf"))
        write(wiki, "index.md", "- [[a]]\n")
        write(ext, "outside.md", page("# 外"))
        marks = ["WIKIMARK", "HOMEMARK", "EXTMARK", "DATAMARK"]
        try:
            os.symlink(ext / "outside.md", wiki / "concepts" / "outside.md")
        except (OSError, NotImplementedError):
            marks.remove("EXTMARK")
        data = self.base / "DATAMARK"
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(data)}), \
                mock.patch.object(Path, "home", return_value=home), redirect_stderr(io.StringIO()):
            report = wiki_browse.build(wiki, str(self.base / "site"), "basename")
            out = io.StringIO()
            wiki_browse.core_loop(io.StringIO(json.dumps({"op": "manifest", "wiki": str(wiki)}) + "\n"
                                              + json.dumps({"op": "page", "wiki": str(wiki), "id": "concepts/a"}) + "\n"),
                                  out)
        texts = [p.read_text(encoding="utf-8", errors="replace")
                 for p in Path(report["out"]).rglob("*") if p.is_file()] + [out.getvalue()]
        for text in texts:
            for mark in marks:
                self.assertNotIn(mark, text)

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
        script = [sys.executable, "-X", "utf8", str(plugin / "wiki_browse.py")]
        result = subprocess.run(script + ["build", str(self.wiki), "--out", str(self.base / "site")],
                                capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_state(self.wiki), before)
        # core、serve、stop も、Wiki の中のプラグインから実際のプロセスとして動かす。
        request = json.dumps({"op": "manifest", "wiki": str(self.wiki)}) + "\n"
        result = subprocess.run(script + ["core"], input=request, capture_output=True, text=True, encoding="utf-8",
                                env=env, timeout=120)
        self.assertTrue(json.loads(result.stdout)["ok"], result.stderr)
        server = subprocess.Popen(script + ["serve", str(self.wiki), "--no-open"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, env=env, text=True, encoding="utf-8")
        try:
            url = json.loads(server.stdout.readline())["url"]
            import urllib.request
            with urllib.request.urlopen(url, timeout=30) as res:
                self.assertEqual(res.status, 200)
            stopped = subprocess.run(script + ["stop", str(self.wiki)], capture_output=True, text=True,
                                     encoding="utf-8", env=env, timeout=60)
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            server.wait(30)
        finally:
            if server.poll() is None:
                server.kill()
                server.wait(30)
            server.stdout.close()
            server.stderr.close()
        self.assertEqual(tree_state(self.wiki), before)


# ---------------------------------------------------------------------------
# 中核の子プロセスの入出力
# ---------------------------------------------------------------------------

class CoreLoopTest(TempWiki):
    def run_loop(self, *requests) -> list:
        out = io.StringIO()
        wiki_browse.core_loop(io.StringIO("".join(json.dumps(r) + "\n" for r in requests)), out)
        return [json.loads(line) for line in out.getvalue().splitlines()]

    def test_cache_key_is_the_exact_spelling(self):
        # 大文字と小文字を区別するディレクトリでは、綴りだけが違うルートは別の Wiki である。写しの使い回しは、
        # パスの等しさ（PureWindowsPath は大文字と小文字を同一視する）ではなく、綴りそのままで決める
        # （実装の 3 回目のレビューの重大 3）
        write(self.wiki, "a.md", page("# A"))
        calls = []
        real = core.take_snapshot

        def counting(root, entries=None):
            calls.append(os.fspath(root))
            return real(root, entries)
        # 大文字と小文字を区別するディレクトリは、作るのに管理者の権限が要る。入口の解決を、綴りをそのまま返す形に
        # 差し替えて、綴りだけが違う 2 つのルートを作る
        from pathlib import PureWindowsPath
        other = str(self.wiki).swapcase()
        with mock.patch.object(core, "take_snapshot", counting), \
                mock.patch.object(wiki_browse, "wiki_root", lambda arg: PureWindowsPath(arg)):
            self.run_loop({"op": "manifest", "wiki": str(self.wiki)}, {"op": "manifest", "wiki": str(self.wiki)},
                          {"op": "manifest", "wiki": other})
        self.assertEqual(len(calls), 2, calls)

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
        with reads_via(maybe):
            wiki_browse.core_loop(lines(), out)   # 同じプロセス（同じ写しの使い回し）の中で確かめる
        first, second = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(first["pages"], [])
        self.assertEqual([p["id"] for p in second["pages"]], ["a"])


# ---------------------------------------------------------------------------
# wiki のスコープの表示
# ---------------------------------------------------------------------------

class ScopeTest(TempWiki):
    """呼び出し元が --scope で指定したスコープの、画面への出し方。"""

    def test_cli_rejects_bad_scope_before_doing_anything(self):
        write(self.wiki, "a.md", page("# A"))
        for args in (["--scope", "global"], ["--scope-name", "x"], ["--scope", "project", "--scope-name", "x"]):
            with self.subTest(args=args):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                    wiki_browse.main(["build", str(self.wiki), *args])
                self.assertEqual(cm.exception.code, 2)
        self.assertFalse(self.data.exists())

    def test_label_and_title(self):
        write(self.wiki, "a.md", page("# A", title="A"))
        snap = core.take_snapshot(self.wiki)
        plain = core.Core(snap)
        cases = [("user", "ユーザースコープの wiki", "A · ユーザースコープ"),
                 ("project", "プロジェクトの wiki", "A · プロジェクト")]
        for scope, heading, title in cases:
            with self.subTest(scope=scope):
                c = core.Core(snap, scope=scope)
                for html in (c.render_page("a"), c.render_index()):
                    color = "brand" if scope == "user" else "informative"
                    self.assertIn(f'<p id="_scope" class="scope scope-{scope}"><span class="fui-Badge" '
                                  f'data-appearance="tint" data-color="{color}" data-size="large" '
                                  f'data-shape="rounded">{heading}</span></p>', html)
                    # スコープの表示は、スクリプトが足すナビゲーションより前（サイドバーの先頭）にある。
                    self.assertLess(html.index('<nav id="_nav"'), html.index('id="_scope"'))
                    self.assertLess(html.index('id="_scope"'), html.index("<noscript>"))
                self.assertIn(f"<title>{title}</title>", c.render_page("a"))
                self.assertIn(f"<title>Index · {title.split(' · ')[1]}</title>", c.render_index())
                # データのファイル（世代だけで食い違いを確かめる）は、スコープで変わらない。
                for name in core.DATA_FILES:
                    self.assertEqual(c.render_data(name), plain.render_data(name))

    def test_no_scope_draws_nothing(self):
        write(self.wiki, "a.md", page("# A", title="A"))
        for scope in (None, "unknown", "", {"kind": "user"}):
            with self.subTest(scope=scope):
                c = core.Core(core.take_snapshot(self.wiki), scope=scope)
                self.assertNotIn('id="_scope"', c.render_page("a"))
                self.assertIn("<title>A</title>", c.render_page("a"))

    def test_build_shows_given_scope(self):
        write(self.wiki, "a.md", page("# A"))
        with redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            report = wiki_browse.build(self.wiki, None, None, "project")
        index = (Path(report["out"]) / "index.html").read_text(encoding="utf-8")
        self.assertIn('<p id="_scope" class="scope scope-project"><span class="fui-Badge" data-appearance="tint" '
                      'data-color="informative" data-size="large" data-shape="rounded">プロジェクトの wiki</span></p>', index)
        self.assertEqual(report["warnings"], [])
        report = self.build()
        self.assertNotIn('id="_scope"', (Path(report["out"]) / "index.html").read_text(encoding="utf-8"))

    def test_scope_is_not_inferred_from_the_surroundings(self):
        # --scope を渡さなければ、wiki の外に作業領域の設定や .git があっても、スコープを出さない。
        # 出さないだけでなく、それらを開かず、一覧せず、あるかどうかも調べない（推し量るために読まない）。
        # wiki の祖先も一覧しない（一覧すれば、おとりに触れずに名前で見つけられる）。祖先の属性を調べるのは、
        # 書き出し先と状態の場所の確かめで、もとからしている。
        write(self.wiki, "a.md", page("# A"))
        config = write(self.base / "work", ".info-hive/workspace.json", json.dumps({"version": 1, "kind": "user"}))
        (self.base / ".git").mkdir()
        decoys = [config.parent, self.base / ".git"]
        ancestors = list(self.wiki.parents)
        # 記録の仕組みが、おとりを読むこと、あるかどうかを調べること、祖先を一覧することを捕まえると確かめておく。
        with recording_access() as seen:
            config.read_text(encoding="utf-8")
            (self.base / ".git").is_dir()
            os.listdir(self.base)
        self.assertEqual(len({Path(p).name for _k, p in touched_under(seen, decoys)}), 2)
        self.assertTrue(touched_under(seen, ancestors, kinds=LISTING, exact=True))
        with recording_access() as seen:
            report = self.build()
        self.assertTrue(touched_under(seen, [self.wiki]))   # wiki は読んでいる（記録が効いている）
        self.assertEqual(touched_under(seen, decoys), [])
        self.assertEqual(touched_under(seen, ancestors, kinds=LISTING, exact=True), [])
        self.assertNotIn('id="_scope"', (Path(report["out"]) / "index.html").read_text(encoding="utf-8"))

    def test_drawn_scope_comes_from_the_live_answer(self):
        drawn = wiki_browse._drawn_scope
        self.assertIsNone(drawn({}))                       # 前の版のサーバーは答えに scope がない
        self.assertIsNone(drawn({"scope": None}))          # スコープなしで起動した
        for bad in ("unknown", "", 3, ["user"], {"kind": "user", "name": None}):
            with self.subTest(bad=bad):
                self.assertIsNone(drawn({"scope": bad}))
        self.assertEqual(drawn({"scope": "user"}), "user")
        self.assertEqual(drawn({"scope": "project"}), "project")


# ---------------------------------------------------------------------------
# 探しやすさ（docs/plans/wiki-browse-findability-2026-11-13.md）と Fluent 2（wiki-browse-fluent2-2026-11-14.md）
# ---------------------------------------------------------------------------

NAV_MODEL_DIR = ROOT / "tests/wiki/browse_nav"


def _nav_dump(groups) -> list:
    """木を、比べられる入れ子の値にする（ID、名前、要約、件数、項目、子）。"""
    out = []
    for g in groups:
        items = [(it["state"], it.get("id"), it["label"], it.get("anchor"), it.get("group")) for it in g["items"]]
        out.append((g["id"], g["title"], g.get("summary", ""), g["count"], items, _nav_dump(g["children"])))
    return out


def _js_value(text: str, name: str):
    prefix = f"window.{name}="
    assert text.startswith(prefix) and text.endswith(";\n"), text[:40]
    return json.loads(text[len(prefix):-2])


class NavTreeTest(TempWiki):
    """2.1 の木の規則。参照の実装（書き換える前の中核の上の 2 つ目の段）と同じ木になる（9 節）。"""

    def test_tree_matches_reference_for_all_cases(self):
        sys.path.insert(0, str(NAV_MODEL_DIR))
        try:
            import nav_model
        finally:
            sys.path.remove(str(NAV_MODEL_DIR))
        for name, files, pages in nav_model.CASES:
            with self.subTest(case=name):
                wiki = Path(tempfile.mkdtemp(dir=self.base))
                nav_model.make_wiki(wiki, files, pages)
                expected = _nav_dump(nav_model.build(wiki))
                got = _nav_dump(build_core(wiki).nav_groups)
                self.assertEqual(got, expected)

    def test_data_groups_are_in_the_tree(self):
        write(self.wiki, "index.md", "# 索引\n- [[a]]\n## 分類\n- [[b]]\n- [[indexes/x]]: 分割\n")
        write(self.wiki, "indexes/x.md", "# X\n## 子\n- [[c]]\n")
        for name in ("a", "b", "c", "d"):
            write(self.wiki, f"concepts/{name}.md", page(f"# {name}", type="concept"))
        c = build_core(self.wiki)
        ids = {g["id"] for g in core._walk(c.nav_groups)}
        index = c.render_index()
        groups = [m.split('"')[0] for m in index.split('data-groups="')[1:]]
        self.assertEqual(len(groups), 4)
        for attr in groups:
            self.assertTrue(attr and set(attr.split(" ")) <= ids, attr)
        # 一覧の順は索引の順（a、b、c、索引にない d）
        order = [m.split('"')[0] for m in index.split('data-id="')[1:]]
        self.assertEqual(order, ["concepts/a", "concepts/b", "concepts/c", "concepts/d"])
        self.assertEqual([m.split('"')[0] for m in index.split('data-order="')[1:]], ["1", "2", "3", "4"])

    def test_broken_invariant_fails_the_build(self):
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "items": [], "children": []},
                              {"id": "_g1", "title": "B", "items": [], "children": []}])
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g 1", "title": "A", "items": [], "children": []}])
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "children": [],
                               "items": [{"state": "group", "group": "_g9", "label": "X"}]}])

    def test_broken_tag_stage_invariant_fails_the_build(self):
        """タグでまとめる設計の 2.4。形で決まる性質が崩れた木を拒む。"""
        page = {"state": "resolved", "id": "a", "label": "a"}

        def tag(gid, items, children=()):
            return {"id": gid, "title": "t", "items": items, "children": list(children)}

        # タグのグループでないグループが、ページの項目を持つ
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "items": [page], "children": []}])
        # タグのグループが子を持つ
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "items": [],
                               "children": [tag("_gt1", [page], [tag("_gt2", [page])])]}])
        # タグのグループが、ページでない項目を持つ
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "items": [],
                               "children": [tag("_gt1", [{"state": "unresolved", "label": "x"}])]}])
        # 同じページが、同じ親の 2 つのタグのグループに入る
        with self.assertRaises(core.NavInvariantError):
            core._check_tree([{"id": "_g1", "title": "A", "items": [],
                               "children": [tag("_gt1", [page]), tag("_gt2", [page])]}])
        core._check_tree([{"id": "_g1", "title": "A", "items": [], "children": [tag("_gt1", [page])]}])

    def test_tag_stage_rejects_a_changed_page_set(self):
        """N9 の前の木と比べる性質。ページの集合が変わると、組み立てを失敗にする。"""
        write(self.wiki, "index.md", "# Wiki\n## G\n- [[a]]\n## H\n- [[b]]\n")
        for name in ("a", "b"):
            write(self.wiki, f"concepts/{name}.md", page(f"# {name}", type="concept", tags=["t"]))
        c = build_core(self.wiki)
        top = [{"id": "_g1", "title": "G", "items": [{"state": "resolved", "id": "concepts/a", "label": "a"}],
                "children": []}]
        # N9 の前とあとで、木に載ったページの集合が違って見えると、組み立てを失敗にする
        with mock.patch.object(core, "_page_ids", side_effect=[{"concepts/a"}, {"concepts/b"}]):
            with self.assertRaises(core.NavInvariantError):
                c._nav_tag_stage(top)


class SummaryTest(TempWiki):
    """4.2 の要約の順: frontmatter、索引の行、本文の冒頭、なし。"""

    def test_summary_order(self):
        write(self.wiki, "index.md", "- [[own]]: 索引の行\n- [[line]]：　全角の区切りの要約\n- [[dash]] — ダッシュの要約\n"
                                     "- [[lead]]\n- [[none]]\n")
        write(self.wiki, "concepts/own.md", page("# Own\n\n本文の冒頭。", type="concept", summary="自分の要約"))
        write(self.wiki, "concepts/line.md", page("# Line\n\n本文の冒頭。", type="concept"))
        write(self.wiki, "concepts/dash.md", page("# Dash", type="concept"))
        write(self.wiki, "concepts/lead.md", page("# Lead\n\n- リストは飛ばす\n\n> 引用も飛ばす\n\n最初の段落。次の文。",
                                                  type="concept"))
        write(self.wiki, "concepts/none.md", page("# None\n\n- リストだけ", type="concept"))
        c = build_core(self.wiki)
        got = {pid.split("/")[1]: c.page_summary(pid) for pid in c.drawn}
        self.assertEqual(got["own"], ("自分の要約", "frontmatter"))
        self.assertEqual(got["line"], ("全角の区切りの要約", "index"))
        self.assertEqual(got["dash"], ("ダッシュの要約", "index"))
        self.assertEqual(got["lead"], ("最初の段落。", "lead"))
        self.assertEqual(got["none"], ("", "none"))

    def test_long_lead_is_cut(self):
        write(self.wiki, "a.md", page("# A\n\n" + "あ" * 300))
        c = build_core(self.wiki)
        self.assertEqual(c.page_summary("a"), ("あ" * core.LEAD_LIMIT, "lead"))


class SearchDataTest(TempWiki):
    """5.1 の data/search.js。"""

    def search(self, c=None):
        c = c or build_core(self.wiki)
        return _js_value(c.render_data("data/search.js"), "WIKI_SEARCH")

    def test_rows_are_drawn_pages(self):
        write(self.wiki, "concepts/a.md", page("# A", type="concept", tags=["検索"], updated="2026-04-18"))
        write(self.wiki, "concepts/dup.md", page("# Dup"))
        write(self.wiki, "entities/dup.md", page("# Dup"))
        (self.wiki / "concepts" / "bad.md").write_bytes(b"\xff\xfe\x00bad")
        c = build_core(self.wiki)
        data = self.search(c)
        self.assertEqual(data["protocol_version"], 2)
        self.assertEqual(data["generation"], c.generation)
        at = {f: k for k, f in enumerate(data["fields"])}
        ids = [r[at["id"]] for r in data["rows"]]
        self.assertEqual(ids, sorted(c.drawn))
        self.assertNotIn("concepts/bad", ids)
        self.assertTrue(data["incomplete"])
        row = data["rows"][ids.index("concepts/a")]
        self.assertEqual(row[at["tags"]], ["検索"])
        self.assertEqual(row[at["updated"]], "2026-04-18")
        self.assertEqual(row[at["type"]], "concept")
        self.assertEqual(json.loads(c.render_data("data/manifest.js")[len("window.WIKI_MANIFEST="):-2])
                         ["capabilities"]["search"], "embedded")

    def test_script_end_is_escaped(self):
        write(self.wiki, "a.md", page("# A", title="</script><b>x"))
        text = build_core(self.wiki).render_data("data/search.js")
        self.assertNotIn("</script>", text)
        self.assertEqual(self.search()["rows"][0][2], "</script><b>x")

    def test_headings_include_h1_and_are_nfc(self):
        nfd = unicodedata.normalize("NFD", "カイド")
        write(self.wiki, "a.md", page(f"# 題名と違う見出し\n\n## {nfd}\n", title=nfd, tags=[nfd]))
        data = self.search()
        at = {f: k for k, f in enumerate(data["fields"])}
        row = data["rows"][0]
        self.assertEqual([h[1] for h in row[at["headings"]]], ["題名と違う見出し", "カイド"])
        self.assertEqual(row[at["title"]], "カイド")
        self.assertEqual(row[at["tags"]], ["カイド"])


class IndexPageTest(TempWiki):
    """4.1 の索引のページ。スクリプトなしで、全ページの題名、種類、更新日、要約、タグ、階層を読める。"""

    def test_rows_and_parts(self):
        write(self.wiki, "index.md", "# 索引\n## コンセプト\n- [[a]]: 要約 A\n- [[missing]]\n")
        write(self.wiki, "concepts/a.md", page("# A", title="A", type="concept", tags=["t1", "t2"], updated="2026-04-18"))
        write(self.wiki, "b.md", page("# B", type="__proto__"))
        index = build_core(self.wiki).render_index()
        self.assertIn('<h1 class="fui-Title2">Index</h1>', index)
        self.assertIn('<a class="ix-title" href="concepts/a.html">A</a>', index)
        self.assertIn('class="badge fui-Badge t-concept"', index)
        self.assertIn('class="badge fui-Badge t-other"', index)
        self.assertIn(">__proto__</span>", index)
        self.assertIn('<time class="fui-Caption1" datetime="2026-04-18">2026-04-18</time>', index)
        self.assertIn('<p class="ix-summary">要約 A</p>', index)
        self.assertIn('<span class="fui-Tag__primaryText">t2</span>', index)
        # N9: 階層のいちばん下は、最初のタグのグループ（タグがなければ「タグなし」）
        self.assertIn('<div class="fx-path fui-Caption1">コンセプト › t1</div>', index)
        self.assertIn('<div class="fx-path fui-Caption1">Index にないページ › __proto__ › タグなし</div>', index)
        self.assertIn('id="_index_unresolved"', index)
        self.assertIn('<span class="wl wl-unresolved" title="ページがない">missing</span>', index)
        self.assertIn('id="_filters"', index)
        self.assertIn('id="_count"', index)


def parts_of(markup: str, section_id: str) -> list:
    """id が section_id の要素の中の要素を (タグ, 属性, 祖先のタグの並び) で返す。void 要素は祖先に積まない。"""
    from html.parser import HTMLParser
    void = {"br", "img", "hr", "meta", "link", "input", "wbr"}

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.found, self.depth, self.done = [], [], None, False

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if self.depth is not None and not self.done:
                self.found.append((tag, a, [t for t, _ in self.stack[self.depth:]]))
            if tag in void:
                return
            self.stack.append((tag, a))
            if self.depth is None and a.get("id") == section_id:
                self.depth = len(self.stack)

        def handle_endtag(self, tag):
            if tag in void:
                return
            while self.stack:
                t, _a = self.stack.pop()
                if self.depth is not None and len(self.stack) < self.depth:
                    self.done = True   # 節を出たら、それより後ろは集めない
                if t == tag:
                    break
    p = P()
    p.feed(markup)
    return p.found


def classes(attrs: dict) -> set:
    return set((attrs.get("class") or "").split())


class ArticlePartsTest(TempWiki):
    """Fluent 2 の設計の 5（段 F2）。中核が描く記事のページの部品の class。本文（Markdown の出力）には class を足さない。"""

    def setUp(self):
        super().setUp()
        write(self.wiki, "sources/paper.md", page("# P", type="source", title="論文"))
        write(self.wiki, "a.md", page("# A\n\n## 節\n\n[[b]] と [[ない]] と [[b#ない見出し]]。\n\n| l | c | r |\n| :--- | :---: | ---: |\n"
                                      "| 1 | 2 | 3 |\n\n> 引用\n\n---\n\n`code`\n",
                                      type="concept", tags=["t1"], summary="要約", updated="2026-04-18",
                                      sources=["sources/paper"], raw="raw/a.md"))
        write(self.wiki, "b.md", page("# B\n\n[[a]] を見る。", type="concept"))

    def assert_table(self, found, row_scope):
        rows = [x for x in found if x[0] == "tr"]
        self.assertTrue(rows)
        for tag, attrs, _anc in found:
            if tag == "tr":
                self.assertIn("fui-TableRow", classes(attrs))
            elif tag == "th":
                self.assertIn("fui-TableHeaderCell", classes(attrs))
                self.assertEqual(attrs.get("scope"), row_scope)
            elif tag == "td":
                self.assertIn("fui-TableCell", classes(attrs))
            elif tag == "tbody":
                self.assertIn("fui-TableBody", classes(attrs))
            elif tag == "thead":
                self.assertIn("fui-TableHeader", classes(attrs))

    def test_meta_is_small_fluent_table(self):
        markup = build_core(self.wiki).render_page("a")
        self.assertIn('<table id="_meta" class="meta fui-Table" data-size="small"', markup)
        found = parts_of(markup, "_meta")
        self.assert_table(found, "row")
        labels = [x for x in found if x[0] == "th"]
        self.assertEqual([x[2] for x in labels][0][-1], "tr")
        self.assertEqual(len(labels), 6)   # 種類、タグ、要約、更新、出典、原本
        self.assertIn('href="sources/paper.html">論文</a>', markup)

    def test_backlinks_are_fluent_list(self):
        markup = build_core(self.wiki).render_page("b")
        found = parts_of(markup, "_backlinks")
        self.assertEqual(found[0][0], "h2")
        self.assertEqual(classes(found[0][1]), {"fui-Subtitle2"})
        lists = [x for x in found if x[0] == "ul"]
        self.assertEqual(len(lists), 1)
        self.assertEqual(classes(lists[0][1]), {"fui-List"})
        items = [x for x in found if x[0] == "li"]
        self.assertTrue(items)
        self.assertTrue(all(classes(a) == {"fui-ListItem"} for _t, a, _anc in items))
        links = [x for x in found if x[0] == "a"]
        self.assertEqual([a.get("href") for _t, a, _anc in links], ["a.html"])

    def test_diagnostics_heading_and_list(self):
        c = build_core(self.wiki)
        for markup in (c.render_page("a"), c.render_index()):
            found = parts_of(markup, "_diagnostics")
            self.assertTrue(found, "診断の節がない")
            self.assertEqual((found[0][0], classes(found[0][1])), ("h2", {"fui-Subtitle2"}))
            self.assertEqual([classes(a) for t, a, _anc in found if t == "ul"], [{"diag-list"}])
            self.assertTrue(any(t == "li" for t, _a, _anc in found))

    def test_core_sections_have_no_bare_h2_and_body_has_no_fluent_class(self):
        markup = build_core(self.wiki).render_page("a")
        body = markup[markup.index('<div id="_body">'):markup.index("</article>")]
        outside = markup.replace(body, "")
        self.assertNotIn("<h2>", outside)
        self.assertNotIn("fui-", body)
        self.assertIn('<h2 id="節">', body)
        self.assertIn('class="ta-center"', body)
        self.assertIn('class="ta-right"', body)

    @unittest.skipUnless(HAS_YAML, "PyYAML が要る")
    def test_relations_table_states(self):
        write(self.wiki, "graph/ontology.yaml", RelationsTest.ONTOLOGY)
        write(self.wiki, "c.md", "---\ntype: concept\ngraph:\n  relationships:\n"
                                 "    - {predicate: uses, object: 'concept:b', source: sources/paper, evidence: 本文の 2 節}\n"
                                 "---\n# C\n")
        c = build_core(self.wiki)
        markup = c.render_page("c")
        found = parts_of(markup, "_relations")
        self.assertEqual((found[0][0], classes(found[0][1])), ("h2", {"fui-Subtitle2"}))
        scroll = [x for x in found if x[0] == "div"]
        self.assertEqual(len(scroll), 1)
        self.assertEqual(classes(scroll[0][1]), {"table-scroll"})
        self.assertEqual((scroll[0][1].get("role"), scroll[0][1].get("tabindex")), ("region", "0"))
        tables = [x for x in found if x[0] == "table"]
        self.assertEqual(len(tables), 1)
        self.assertEqual(classes(tables[0][1]), {"relations", "fui-Table"})
        self.assertEqual(tables[0][1].get("data-size"), "small")
        self.assertIn("div", tables[0][2])   # 表は横に送る入れ物の中にある
        self.assert_table(found, "col")
        self.assertEqual(len([x for x in found if x[0] == "th"]), 9)
        self.assertIn('<td class="fui-TableCell"><a href="b.html">b</a></td>', markup)
        self.assertIn('<td class="fui-TableCell"><a href="sources/paper.html">論文</a></td>', markup)
        # 関係のないページと、オントロジーを読めないときも、見出しは Subtitle2
        self.assertIn('<section id="_relations"><h2 class="fui-Subtitle2">関係</h2>', c.render_page("a"))
        write(self.wiki, "graph/ontology.yaml", "- not a mapping\n")
        self.assertIn('<section id="_relations"><h2 class="fui-Subtitle2">関係</h2><p class="state-error">',
                      build_core(self.wiki).render_page("a"))


class FluentAssetsTest(TempWiki):
    """Fluent 2 の設計の 2、3、6。同梱の資産、配色、ライセンスの表示。"""

    ASSET_DIR = SCRIPTS / "browse_assets"

    def test_fluent_css_matches_record(self):
        data = (self.ASSET_DIR / "fluent2.css").read_bytes()
        readme = (self.ASSET_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn(hashlib.sha256(data).hexdigest(), readme)
        self.assertIn(f"{len(data):,} バイト", readme)
        self.assertTrue(data.startswith(b"/*!"))
        self.assertIn(b"Copyright (c) Microsoft Corporation", data[:20000])

    def test_build_writes_assets_and_notices(self):
        write(self.wiki, "a.md", page("# A"))
        out = Path(self.build()["out"])
        for name in ("app.js", "style.css", "fluent2.css", "theme.js"):
            self.assertEqual((out / "assets" / name).read_bytes(), (self.ASSET_DIR / name).read_bytes(), name)
        self.assertFalse((out / "assets" / "licenses").exists())
        self.assertFalse(any(p.name.endswith((".LICENSE", ".txt")) for p in out.rglob("*")))
        css = (out / "assets" / "style.css").read_text(encoding="utf-8")
        style_lines = [line.lstrip(" *").strip() for line in css.splitlines()]
        license_text = (self.ASSET_DIR / "licenses" / "fluent2-html-replica.LICENSE").read_text(encoding="utf-8")
        for line in (x.strip() for x in license_text.splitlines()):
            if line:
                self.assertIn(line, style_lines)

    def test_html_has_theme_and_asset_order(self):
        write(self.wiki, "a.md", page("# A"))
        c = build_core(self.wiki)
        for html in (c.render_page("a"), c.render_index()):
            self.assertIn('<html lang="ja" data-theme="auto"', html)
            head = html[:html.index("</head>")]
            self.assertLess(head.index("assets/fluent2.css"), head.index("assets/style.css"))
            self.assertLess(head.index("assets/style.css"), head.index('<script src="assets/theme.js"')
                            if 'src="assets/theme.js"' in head else head.index('theme.js"></script>'))
            self.assertIn('<body class="fui-FluentProvider', html)
            self.assertNotIn("style=", html)

    def test_style_css_uses_tokens(self):
        import re
        css = (self.ASSET_DIR / "style.css").read_text(encoding="utf-8")
        body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", body), [])
        self.assertEqual(re.findall(r"\b\d+(?:\.\d+)?px\b", body), [])
        self.assertEqual(re.findall(r"\b\d+(?:\.\d+)?rem\b", body.split("@media")[0]), [])


# ---------------------------------------------------------------------------
# 図の svg（ADR-0030、図の描画の設計の 6）
# ---------------------------------------------------------------------------

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>\n'


class FigureTargetTest(unittest.TestCase):
    """本文の画像の参照を、図の svg に解く（図の描画の設計の 6.4）。"""

    def test_table(self):
        cases = [
            ("concepts/p.md", "../assets/x.svg", "assets/x.svg"),
            ("concepts/p.md", "../assets/x.SVG", "assets/x.SVG"),
            ("concepts/p.md", "../assets/a%20b.svg", "assets/a b.svg"),
            ("concepts/p.md", "../assets/a&b.svg", "assets/a&b.svg"),
            ("concepts/p.md", "../assets/%E5%9B%B3.svg", "assets/図.svg"),
            ("concepts/p.md", "../assets/x.svg#frag", "assets/x.svg"),
            ("concepts/p.md", "../assets/x.svg?q=1", "assets/x.svg"),
            ("top.md", "assets/x.svg", "assets/x.svg"),
            ("a/b/p.md", "../../assets/x.svg", "assets/x.svg"),
            ("concepts/p.md", "assets/x.svg", None),            # concepts/assets/ を指す（lint が指摘する）
            ("concepts/p.md", "../assets/sub/x.svg", None),     # 下位のディレクトリ
            ("concepts/p.md", "../../assets/x.svg", None),      # wiki の外
            ("concepts/p.md", "../assets/x.png", None),
            ("concepts/p.md", "../assets/.x.svg", None),
            ("concepts/p.md", "../assets/a%5Cb.svg", None),     # \ を含む
            ("concepts/p.md", "../assets/a%00.svg", None),
            ("concepts/p.md", "../assets/%FF.svg", None),       # UTF-8 でない
            ("concepts/p.md", "https://example.com/x.svg", None),
            ("concepts/p.md", "data:image/svg+xml,x", None),
            ("concepts/p.md", "/assets/x.svg", None),
            ("concepts/p.md", "#x", None),
            ("concepts/p.md", "", None),
        ]
        for page_rel, src, want in cases:
            with self.subTest(src=src):
                self.assertEqual(core.figure_target(page_rel, src), want)

    def test_nfc(self):
        nfd = unicodedata.normalize("NFD", "が")
        src = "../assets/" + urllib_quote(nfd) + ".svg"
        self.assertEqual(core.figure_target("concepts/p.md", src), "assets/が.svg")

    def test_svg_size(self):
        cases = [
            (b'<svg width="200" height="100">', (200, 100)),
            (b'<svg width="200px" height="99.6px">', (200, 100)),
            (b'<svg viewBox="0 0 640 480">', (640, 480)),
            (b'<svg width="50%" height="100" viewBox="0,0,30,20">', (30, 20)),
            (b'<?xml version="1.0"?>\n<svg\n xmlns="http://www.w3.org/2000/svg" width=\'12\' height=\'34\'>', (12, 34)),
            (b'<svg width="10em" height="2em">', None),
            (b'<svg>', None),
            (b'<svg width="0" height="10">', None),
            (b'<svg viewBox="0 0 x 1">', None),
            (b'<svg width="99999" height="1">', None),
            (b"\xff<svg width='1' height='1'>", None),
            # 実装の 1 回目のレビューの反例: コメントの中の <svg と、data-width を拾わない
            (b'<!-- <svg width="1" height="1"> --><svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"/>',
             (800, 600)),
            (b'<svg width="800" height="600" data-width="1" data-height="1"/>', (800, 600)),
            (b'<svg:svg xmlns:svg="http://www.w3.org/2000/svg" width="5" height="6"/>', (5, 6)),
            (b'<html><svg width="5" height="6"/></html>', None),             # 根が svg でない
            (b'<!DOCTYPE svg [<!ENTITY a "x">]><svg width="1" height="1"/>', None),   # DTD は読まない
            (b'<svg width="1" height="1"', None),                           # 開始タグが閉じていない
        ]
        for data, want in cases:
            with self.subTest(data=data):
                self.assertEqual(core.svg_size(data), want)

    def test_utf8_only(self):
        self.assertTrue(core.is_utf8_svg(SVG.encode("utf-8")))
        self.assertTrue(core.is_utf8_svg(b"\xef\xbb\xbf" + SVG.encode("utf-8")))
        self.assertTrue(core.is_utf8_svg(b'<?xml version="1.0" encoding="UTF-8"?>' + SVG.encode("utf-8")))
        self.assertFalse(core.is_utf8_svg(SVG.encode("utf-16")))
        self.assertFalse(core.is_utf8_svg(b"<svg>\xff</svg>"))
        self.assertFalse(core.is_utf8_svg(b'<?xml version="1.0" encoding="Shift_JIS"?><svg/>'))
        # 実装の 1 回目のレビューの重大: BOM のない UTF-16 の ASCII の XML は、UTF-8 としても読めるが落とす
        decl = '<?xml version="1.0" encoding="UTF-16"?>' + SVG
        for enc in ("utf-16-le", "utf-16-be", "utf-32-le"):
            with self.subTest(enc=enc):
                self.assertFalse(core.is_utf8_svg(decl.encode(enc)))
                self.assertFalse(core.is_utf8_svg(SVG.encode(enc)))
        self.assertFalse(core.is_utf8_svg(b"<svg>\x01</svg>"))       # XML で許されない制御文字
        # 処理命令は XML の宣言ではない（実装の 2 回目のレビューの軽微）
        self.assertTrue(core.is_utf8_svg(b'<?xml-stylesheet type="text/css" href="s.css?encoding=\'Shift_JIS\'"?>' + SVG.encode()))
        self.assertTrue(core.is_utf8_svg(b'<?xml\nversion="1.0"\nencoding="utf-8"?>' + SVG.encode()))
        self.assertTrue(core.is_utf8_svg("<svg>\t改行\r\n😀</svg>".encode("utf-8")))


def urllib_quote(text: str) -> str:
    import urllib.parse
    return urllib.parse.quote(text)


class FigureSvgTest(TempWiki):
    """図の svg の入力、写し、描画、書き出し（図の描画の設計の 6）。"""

    def setUp(self):
        super().setUp()
        write(self.wiki, "concepts/p.md", page("# P\n\n図は次のとおり。\n\n![流れの図](../assets/p-01.svg)\n"))

    def svg(self, name: str, data: bytes) -> Path:
        path = self.wiki / "assets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_inputs_are_direct_svg_files(self):
        self.svg("p-01.svg", SVG.encode("utf-8"))
        self.svg("x.png", b"png")
        self.svg(".hidden.svg", SVG.encode("utf-8"))
        self.svg("sub/y.svg", SVG.encode("utf-8"))
        kinds = [(k, rel) for k, rel, _s, _m in core.input_list(self.wiki)]
        self.assertEqual([e for e in kinds if e[0] == "asset"], [("asset", "assets/p-01.svg")])

    def test_wiki_without_svg_keeps_its_signature_entries(self):
        before = core.input_list(self.wiki)
        self.assertFalse([e for e in before if e[0].startswith("asset")])
        (self.wiki / "assets").mkdir()
        self.assertEqual(core.input_list(self.wiki), before)

    def test_page_draws_img_with_relative_src(self):
        self.svg("p-01.svg", SVG.encode("utf-8"))
        write(self.wiki, "top.md", page("# T\n\n![上の図 <b>](assets/p-01.svg)\n"))
        c = build_core(self.wiki)
        out = c.asset_out["assets/p-01.svg"]
        self.assertRegex(out, r"^assets/wiki/[0-9a-f]{16}\.svg$")
        body = c.render(c.out_name["concepts/p"])
        self.assertIn(f'<img class="fui-Image" src="../{out}" alt="流れの図" width="10" height="10">', body)
        self.assertIn('data-fig="svg" data-theme="light"', body)
        top = c.render(c.out_name["top"])
        self.assertIn(f'src="{out}" alt="上の図 &lt;b&gt;"', top)
        self.assertNotIn("style=", body)
        self.assertEqual(c.asset_bytes(out), SVG.encode("utf-8"))
        self.assertTrue(c.knows(out))
        self.assertFalse([d for d in c.diagnostics if d.get("page") == "concepts/p"])

    def test_missing_svg_keeps_alt_text_and_diagnoses(self):
        c = build_core(self.wiki)
        body = c.render(c.out_name["concepts/p"])
        self.assertIn("流れの図", body)
        self.assertNotIn("<img", body)
        self.assertIn({"kind": "missing_asset", "page": "concepts/p", "target": "assets/p-01.svg"}, c.diagnostics)

    def test_other_images_stay_alt_text(self):
        write(self.wiki, "concepts/q.md", page("# Q\n\n![外](https://example.com/x.svg) ![png](../assets/x.png)\n"))
        self.svg("x.png", b"png")
        c = build_core(self.wiki)
        body = c.render(c.out_name["concepts/q"])
        self.assertNotIn("<img", body)
        self.assertFalse([d for d in c.diagnostics if d.get("page") == "concepts/q"])

    def test_heading_image_keeps_heading_id(self):
        self.svg("p-01.svg", SVG.encode("utf-8"))
        write(self.wiki, "concepts/h.md", page("# H\n\n## 見出し ![図](../assets/p-01.svg)\n"))
        c = build_core(self.wiki)
        self.assertIn('id="見出し-図"', c.render(c.out_name["concepts/h"]))

    def test_non_utf8_svg_is_not_output(self):
        secret = f'<?xml version="1.0" encoding="UTF-16"?><svg xmlns="http://www.w3.org/2000/svg"><desc>{self.wiki}</desc></svg>'
        for name, data in (("p-01.svg", SVG.encode("utf-16")),
                           ("p-01.svg", secret.encode("utf-16-le")),
                           ("p-01.svg", b'<?xml version="1.0" encoding="Shift_JIS"?>' + SVG.encode("ascii"))):
            with self.subTest(data=data[:20]):
                self.svg(name, data)
                snap = core.take_snapshot(self.wiki)
                self.assertIn(("asset", "assets/p-01.svg"), snap.unreadable)
                c = core.Core(snap)
                self.assertEqual(c.asset_out, {})
                self.assertIn({"kind": "asset_unreadable", "page": "concepts/p", "target": "assets/p-01.svg"},
                              c.diagnostics)

    def test_too_large_svg_is_not_read(self):
        self.svg("p-01.svg", b"<svg>" + b" " * 64 + b"</svg>")
        with mock.patch.object(core, "ASSET_MAX_BYTES", 32):
            snap = core.take_snapshot(self.wiki)
        f = snap.by_kind("asset")[0]
        self.assertEqual((f.error, f.data), ("too_large", None))

    def test_read_cap_is_enforced_by_the_reader(self):
        # 走査で見た大きさではなく、読む口が上限を強制する（走査のあとで大きくなった場合）
        path = self.svg("p-01.svg", b"x" * 100)
        with self.assertRaises(fs.TooLarge):
            fs.read_input_capped(self.wiki, "assets/p-01.svg", 99)
        self.assertEqual(fs.read_input_capped(self.wiki, "assets/p-01.svg", 100), path.read_bytes())

    def test_svg_change_changes_signature_and_generation(self):
        self.svg("p-01.svg", SVG.encode("utf-8"))
        sig, gen = core.signature(self.wiki), core.take_snapshot(self.wiki).generation
        self.svg("p-01.svg", SVG.replace("10", "200").encode("utf-8"))   # 印は大きさと時刻で見るので、大きさを変える
        self.assertNotEqual(core.signature(self.wiki), sig)
        self.assertNotEqual(core.take_snapshot(self.wiki).generation, gen)

    def outside_svg(self) -> Path:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "p-01.svg").write_bytes(SVG.encode("utf-8"))
        return outside

    def test_file_link_is_not_read(self):
        outside = self.outside_svg()
        (self.wiki / "assets").mkdir()
        try:
            os.symlink(outside / "p-01.svg", self.wiki / "assets" / "p-01.svg")
        except (OSError, NotImplementedError):
            self.skipTest("ファイルのシンボリックリンクを作れない")
        self.assertFalse([e for e in core.input_list(self.wiki) if e[0] == "asset"])

    def test_linked_assets_dir_is_not_read(self):
        # ディレクトリのシンボリックリンク（作れなければ、Windows ではジャンクション）。どちらもたどらない
        outside = self.outside_svg()
        if not link_dir(self.wiki / "assets", outside):
            self.skipTest("ディレクトリのリンクを作れない")
        self.assertFalse([e for e in core.input_list(self.wiki) if e[0].startswith("asset")])
        c = build_core(self.wiki)
        self.assertIn({"kind": "missing_asset", "page": "concepts/p", "target": "assets/p-01.svg"}, c.diagnostics)

    @unittest.skipUnless(os.name == "nt", "ジャンクションは Windows だけ")
    def test_junction_assets_dir_is_not_read(self):
        import _winapi
        outside = self.outside_svg()
        _winapi.CreateJunction(str(outside), str(self.wiki / "assets"))
        self.assertFalse([e for e in core.input_list(self.wiki) if e[0].startswith("asset")])

    def test_output_names_do_not_clash(self):
        self.svg("p-01.svg", SVG.encode("utf-8"))
        self.svg("P-01.SVG", SVG.encode("utf-8")) if not (self.wiki / "assets" / "P-01.SVG").exists() else None
        write(self.wiki, "assets.md", page("# 予約の名前と同じページ"))
        write(self.wiki, "Assets/wiki.md", page("# 大文字の Assets"))
        c = build_core(self.wiki)
        pages = {n.casefold() for n in c.out_name.values()} | {n.casefold() for n in core._fixed_files()}
        dirs = {"/".join(n.casefold().split("/")[:i]) for n in pages for i in range(1, n.count("/") + 1)}
        for name in c.asset_by_out:
            self.assertNotIn(name.casefold(), pages)
            self.assertNotIn(name.casefold(), dirs)
            self.assertTrue(core.is_safe_relative(name))

    def test_build_writes_svg_bytes(self):
        data = b"\xef\xbb\xbf" + SVG.replace("\n", "\r\n").encode("utf-8")
        self.svg("p-01.svg", data)
        out = self.base / "site"
        self.build(out)
        c = build_core(self.wiki)
        self.assertEqual((out / c.asset_out["assets/p-01.svg"]).read_bytes(), data)

    def test_machine_info_in_svg_is_reported(self):
        self.svg("p-01.svg", f'<svg xmlns="http://www.w3.org/2000/svg"><desc>{self.wiki}</desc></svg>'.encode("utf-8"))
        report = self.build(self.base / "site")
        self.assertTrue(any("絶対パス" in w and "assets/wiki/" in w for w in report["warnings"]), report["warnings"])

    def test_lint_and_browse_resolve_the_same_path(self):
        # 同じ参照先を、lint（本文の文字から image_ref_path）と閲覧（markdown-it の src から figure_target）が
        # 同じパスに解く（実装の 1 回目のレビューの軽微。文字参照の # と &quest;）
        import posixpath
        parser = wiki_pages.new_parser()
        raws = ["../assets/a.svg", "../assets/a&amp;b.svg", "../assets/a&#38;b.svg", "../assets/a&#x26;b.svg",
                "../assets/a.svg&quest;v=1", "../assets/a.svg&#35;frag", "../assets/a\\&amp;b.svg",
                "../assets/a\\#b.svg", "../assets/a%20b.svg", "../assets/%E5%9B%B3.svg", "../assets/a%zz.svg",
                "../assets/a(1).svg", "<../assets/a b.svg>", "../assets/a.svg?q#f", "../assets/x%2Fy.svg",
                # 空白の文字参照。markdown-it は URL の正規化で前後の空白を落とす（実装の 2 回目のレビューの軽微）
                "../assets/a.svg&#32;", "&#32;../assets/a.svg", "../assets/a.svg&#9;", "../assets/a.svg&NewLine;"]
        for raw in raws:
            with self.subTest(raw=raw):
                tokens = parser.parse(f"![x]({raw})\n")
                image = next(c for t in tokens if t.type == "inline" for c in t.children if c.type == "image")
                browse = core.figure_target("concepts/p.md", image.attrs["src"])
                target = raw[1:-1] if raw.startswith("<") else raw
                rel = wiki_lint.image_ref_path(target)
                lint = posixpath.normpath(posixpath.join("concepts", rel)) if rel else None
                if browse is not None:
                    self.assertEqual(unicodedata.normalize("NFC", lint), browse)
                else:
                    self.assertFalse(lint and lint.startswith("assets/") and lint.count("/") == 1
                                     and lint.lower().endswith(".svg") and "\\" not in lint, lint)

    def test_lint_resolves_character_references_like_markdown(self):
        # lint と閲覧は、参照先の文字参照を同じに解く（図の描画の設計の 6.4）
        self.svg("a&b.svg", SVG.encode("utf-8"))
        md = write(self.wiki, "concepts/r.md", page("# R\n\n![図](../assets/a&amp;b.svg) ![x](../assets/a\\&amp;b.svg)\n"))
        found = wiki_lint.missing_assets(md.read_text(encoding="utf-8"), md, self.wiki)
        self.assertEqual([f["target"] for f in found], ["../assets/a\\&amp;b.svg"])
        c = build_core(self.wiki)
        self.assertIn('<img class="fui-Image"', c.render(c.out_name["concepts/r"]))


class MermaidAssetsTest(TempWiki):
    """Mermaid の同梱物と、ページの読み込み（ADR-0030、図の描画の設計の 7.2、7.3）。"""
    ASSET_DIR = SCRIPTS / "browse_assets"

    def test_tiny_matches_record(self):
        data = (self.ASSET_DIR / "mermaid.tiny.js").read_bytes()
        readme = (self.ASSET_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn(hashlib.sha256(data).hexdigest(), readme)
        self.assertIn(f"{len(data):,} バイト", readme)
        self.assertIn(f"`{core.FRAME_VERSION}`", readme)
        attrs = (ROOT / "info-hive-wiki" / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("skills/info-hive/scripts/browse_assets/mermaid.tiny.js -text", attrs)

    def test_frame_version_matches_figures_js(self):
        js = (self.ASSET_DIR / "figures.js").read_text(encoding="utf-8")
        self.assertIn(f'var FRAME_VERSION = "{core.FRAME_VERSION}";', js)

    def test_frame_document_has_no_inline_code_or_meta_csp(self):
        import re
        doc = (self.ASSET_DIR / "mermaid-frame.html").read_text(encoding="utf-8")
        self.assertNotIn("Content-Security-Policy", doc)     # <meta> を置くと WebKit が 'self' で止める
        self.assertNotIn("style", doc)
        self.assertEqual(re.findall(r"<script[^>]*>", doc),
                         ['<script src="mermaid.tiny.js">', '<script src="mermaid-frame.js">'])
        self.assertEqual(re.findall(r"<script[^>]*>([^<]*)</script>", doc), ["", ""])
        self.assertEqual(sorted(core.load_frame_assets()), sorted(core.FRAME_ASSETS))

    def test_license_notice_is_in_frame_script(self):
        js = (self.ASSET_DIR / "mermaid-frame.js").read_text(encoding="utf-8")
        self.assertIn("MIT ライセンス、Copyright (c) 2014 - 2022 Knut Sveidqvist", js)
        self.assertTrue((self.ASSET_DIR / "licenses" / "mermaid.LICENSE").is_file())
        self.assertTrue((self.ASSET_DIR / "licenses" / "mermaid.THIRD-PARTY-NOTICES.txt").is_file())

    def test_frame_csp(self):
        csp = core.frame_csp(41234)
        self.assertIn(f"script-src http://127.0.0.1:41234/_frame/{core.FRAME_VERSION}/;", csp)
        self.assertNotIn("'self'", csp)
        self.assertIn("default-src 'none'", csp)
        self.assertIn("style-src 'unsafe-inline'", csp)
        self.assertTrue(csp.endswith("sandbox allow-scripts"))
        self.assertIn("frame-src 'self'", core.CSP)
        self.assertNotIn("unsafe", core.CSP)

    def test_build_has_figures_js_but_not_the_frame(self):
        write(self.wiki, "a.md", page("# A\n\n```mermaid\nflowchart LR\n  a --> b\n```\n"))
        out = Path(self.build()["out"])
        self.assertEqual((out / "assets" / "figures.js").read_bytes(), (self.ASSET_DIR / "figures.js").read_bytes())
        for name in core.FRAME_ASSETS:
            self.assertFalse(list(out.rglob(name)), name)
        html_text = (out / "a.html").read_text(encoding="utf-8")
        self.assertIn('<script src="assets/figures.js"></script>', html_text)
        self.assertLess(html_text.index("assets/app.js"), html_text.index("assets/figures.js"))
        self.assertIn('<code class="language-mermaid">', html_text)     # 静的版ではコードのまま
        self.assertIn("frame-src &#x27;self&#x27;", html_text.replace("'", "&#x27;"))

    def test_assets_are_not_scanned_for_machine_info(self):
        # 同梱物は入力の中身を含まないので、公開の前の検査で調べない（図の描画の設計の 7.2）
        write(self.wiki, "a.md", page("# A"))
        seen = []
        real = core.scan_machine_info

        def spy(files, needles, tokens):
            seen.extend(files)
            return real(files, needles, tokens)
        with mock.patch.object(core, "scan_machine_info", spy):
            self.build()
        self.assertIn("a.html", seen)
        self.assertFalse([n for n in seen if n in core.ASSETS])


class UnlistableAssetsTest(TempWiki):
    """assets/ の一覧を作れなくても閲覧は止めず、図を「読めない」と示す（図の描画の設計の 6.1）。"""

    def test_unlistable_assets_marks_figures_unreadable(self):
        write(self.wiki, "concepts/p.md", page("# P\n\n![図](../assets/p-01.svg)\n"))
        (self.wiki / "assets").mkdir()
        (self.wiki / "assets" / "p-01.svg").write_bytes(SVG.encode("utf-8"))
        real = os.scandir
        blocked = self.wiki / "assets"

        def scandir(path="."):
            if Path(path) == blocked:
                raise PermissionError("denied")
            return real(path)
        with mock.patch.object(os, "scandir", scandir):
            snap = core.take_snapshot(self.wiki)
        c = core.Core(snap)
        self.assertIn({"kind": "assets_unlistable", "target": "assets"}, c.diagnostics)
        self.assertIn({"kind": "asset_unreadable", "page": "concepts/p", "target": "assets/p-01.svg"}, c.diagnostics)
        self.assertNotEqual(snap.signature, core.signature(self.wiki))   # 一覧を作れるようになれば作り直す


if __name__ == "__main__":
    unittest.main()
