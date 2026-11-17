"""概要の表示と更新、同じ写しからの結び付け、保存の境界（ADR-0033）。"""
from __future__ import annotations

import errno
import itertools
import json
import os
from pathlib import Path
from unittest import mock

from tests.wiki.test_wiki_overview import OverviewCase, SVG
from tests.wiki.test_browse_server import InProcess
import wiki_overview as overview
import wiki_pages
import wiki_browse_core as core
import wiki_browse_fs as fs
import wiki_browse as browse
browse._load()


class BrowseOverviewTests(OverviewCase):
    pid = "concepts/概要の元"

    def save(self, body="### 概要専用の語\n\n![図](#fig-flow)\n", figures=None):
        ready = self.prepare(refresh=True)
        self.draft(ready, body, figures)
        self.assertEqual(overview.check(self.wiki, ready["work_id"]), {"status": "ok"})
        return overview.write(self.wiki, ready["work_id"])

    def build(self):
        return core.Core(core.take_snapshot(self.wiki))

    def test_insert_after_h1_and_keep_page_search_headings_and_links(self):
        self.source.write_bytes("導入。\n\n# 元のページ\n\n### 概要\n\n本文。".encode("utf-8"))
        before = self.build()
        search = before.search_json()
        heads = before.headings[self.pid]
        links = before.link_targets(self.pid)
        self.save()
        built = self.build()
        html = built.render(built.out_name[self.pid])
        self.assertIn('</h1>\n<details class="wiki-overview', html)
        self.assertIn('data-overview-state="fresh" open', html)
        self.assertIn('id="概要"', html)
        self.assertNotIn('id="概要専用の語"', html)
        self.assertEqual(built.headings[self.pid], heads)
        self.assertEqual(built.link_targets(self.pid), links)
        self.assertEqual({k: v for k, v in built.search_json().items() if k != "generation"},
                         {k: v for k, v in search.items() if k != "generation"})
        self.assertEqual(len(built.drawn), 1)
        self.assertEqual(built.body_html(self.pid), built.body_html(self.pid))

    def test_missing_nested_and_multiple_h1(self):
        for source in ("本文。", "> # 引用\n\n本文。", "# 最初\n\n# 次"):
            with self.subTest(source=source):
                self.source.write_bytes(source.encode("utf-8"))
                self.save()
                html = self.build().body_html(self.pid)
                self.assertEqual(html.count('<details class="wiki-overview'), 1)
                if source.startswith("#"):
                    self.assertLess(html.index("</h1>"), html.index("<details"))
                    self.assertLess(html.index("<details"), html.index('id="次"'))
                else:
                    self.assertTrue(html.startswith("<details"))

    def test_stale_is_closed_with_visible_notice_and_none_has_no_container(self):
        self.assertNotIn("wiki-overview", self.build().body_html(self.pid))
        self.save()
        self.source.write_bytes(b"changed")
        html = self.build().body_html(self.pid)
        self.assertIn('data-overview-state="stale"><summary', html)
        self.assertIn('wiki-overview-status">元のページが更新されている', html)
        self.assertIn("この概要は古い", html)
        self.assertIn("概要専用の語", html)

    def test_svg_is_shared_as_bytes_with_content_url_and_csp(self):
        self.save()
        built = self.build()
        name = core.overview_svg_name(overview.embedded_figures(self.sidecar.read_bytes())["flow"])
        self.assertTrue(built.knows(name))
        self.assertEqual(built.asset_bytes(name), built.render_all("text")[name])
        self.assertIn('width="720" height="120"', built.body_html(self.pid))
        self.assertIn(name, " ".join(built.overview_assets))
        self.assertNotIn("<svg xmlns", built.body_html(self.pid))
        self.assertIn("sandbox", core.CSP_SVG)
        old = name
        self.save(figures={"flow.svg": SVG.replace(b"flow", b"changed")})
        updated = self.build()
        self.assertNotIn(old, updated.overview_assets)
        self.assertNotEqual(list(updated.overview_assets), list(built.overview_assets))

    def test_invalid_saved_body_never_displays_as_fresh(self):
        body = "### 概要専用の語\n\n説明。"
        self.save(body, {})
        original = self.sidecar.read_bytes()
        for bad in ("# 不正なh1", "### 概要\n\n[[別ページ]]", "x" * (overview.MAX_BODY + 1)):
            with self.subTest(bad=bad[:20]):
                self.sidecar.write_bytes(original.replace(body.encode("utf-8"), bad.encode("utf-8")))
                built = self.build()
                self.assertEqual(built.overviews[self.pid][1].state, "broken")
                self.assertIn("概要を読めない", built.body_html(self.pid))
                self.assertNotIn(bad[:20], built.body_html(self.pid))
                self.assertEqual(built.overview_assets, {})

    def test_saved_boundary_preserves_all_payload_whitespace(self):
        for figures, bom, crlf in itertools.product((False, True), repeat=3):
            with self.subTest(figures=figures, bom=bom, crlf=crlf):
                newline = "\r\n" if crlf else "\n"
                prefix = ("\n\t\n    code\n\n\u0085\u2028\n\n" +
                          ("![図](#fig-flow)\n\n" if figures else "") + "### 概要\n\n").replace("\n", newline)
                first = b"\xef\xbb\xbf" if bom else b""
                end = (newline * 3).encode("utf-8")
                encoded = prefix.encode("utf-8")
                raw = first + encoded + b"a" * (overview.MAX_BODY - len(first) - len(encoded) - len(end)) + end
                ready = self.prepare(refresh=True)
                self.draft(ready, raw, None if figures else {})
                self.assertEqual(overview.check(self.wiki, ready["work_id"]), {"status": "ok"})
                overview.write(self.wiki, ready["work_id"])
                view = overview.view(self.key, overview.Sidecar("ok", self.sidecar.read_bytes()),
                                     overview.PageState("ok", self.build().page_files[self.source.relative_to(self.wiki).as_posix()].sha))
                # ページの raw SHA は、この素材では BOM/改行なしなので正規化 SHA と同じ。
                self.assertEqual(view.state, "fresh")
                expected = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
                self.assertEqual(view.body, expected)

    def test_broken_orphan_and_unknown_entry_do_not_hide_page(self):
        self.save()
        self.put("assets/overview/user.txt", "keep")
        built = self.build()
        self.assertEqual(built.overviews[self.pid][1].state, "fresh")
        self.assertTrue(any(d["kind"] == "overview_unknown_entry" for d in built.diagnostics))
        self.sidecar.write_bytes(b"broken")
        built = self.build()
        self.assertIn("元のページ", built.body_html(self.pid))
        self.assertIn("概要を読めない", built.body_html(self.pid))
        self.source.unlink()
        built = self.build()
        self.assertEqual(built.drawn, {})

    def test_page_unreadable_uses_all_input_names(self):
        self.save()
        original = fs.read_input
        def read(root, rel):
            if rel == "concepts/概要の元.md":
                raise fs.Unknown("試験の読み取り拒否")
            return original(root, rel)
        with mock.patch.object(fs, "read_input", side_effect=read):
            built = self.build()
        self.assertTrue(any(d["kind"] == "overview_page_unreadable" for d in built.diagnostics))
        self.assertFalse(any(d["kind"] == "overview_orphan" for d in built.diagnostics))

    def test_page_key_collision_does_not_choose_a_page(self):
        self.save()
        self.put("concepts/別のページ.md", "# 別のページ")
        collision = "f" * 16
        self.sidecar.rename(self.sidecar.with_name(collision + ".overview.md"))
        with mock.patch.object(overview, "page_key", return_value=collision):
            built = self.build()
        self.assertEqual({v.state for _, v in built.overviews.values()}, {"page_unknown"})
        self.assertEqual(built.overview_assets, {})

    def test_svg_name_collision_rejects_all_affected_overviews(self):
        self.save("### 図\n\n![a](#fig-a)\n\n![b](#fig-b)",
                  {"a.svg": SVG, "b.svg": SVG.replace(b"flow", b"different")})
        with mock.patch.object(core, "overview_svg_name", return_value="assets/overview/collision.svg"):
            built = self.build()
        self.assertEqual(built.overview_assets, {})
        self.assertIn("概要を読めない", built.body_html(self.pid))
        self.assertTrue(any(d.get("reason") == "figure_name_collision" for d in built.diagnostics))

    def test_unknown_namespace_from_eio_is_transient(self):
        self.save()
        original = os.scandir
        def scan(path):
            if Path(path) == self.sidecar.parent:
                raise OSError(errno.EIO, "試験の一覧拒否")
            return original(path)
        with mock.patch.object(os, "scandir", side_effect=scan):
            built = self.build()
        self.assertTrue(built.overview_scan_unknown)
        self.assertIn(("overview_dir", "assets/overview"), built.snapshot.transient)
        self.assertIn("概要の一覧を確認できない", built.body_html(self.pid))
        self.assertTrue(built.manifest()["incomplete"]["overview_scan_unknown"])

    def test_non_utf8_sidecar_is_unreadable_but_not_transient(self):
        self.save()
        self.sidecar.write_bytes(b"\xff")
        built = self.build()
        self.assertEqual(built.overviews[self.pid][1].state, "broken")
        self.assertEqual(built.manifest()["incomplete"]["unreadable_overviews"], 1)
        self.assertEqual(built.snapshot.transient, [])

    def test_page_normalization_is_applied_once_even_with_two_boms(self):
        self.source.write_bytes(b"\xef\xbb\xbf\xef\xbb\xbf" + "# 元のページ\r\n本文。\r\n".encode("utf-8"))
        self.save()
        self.assertEqual(self.build().overviews[self.pid][1].state, "fresh")

    def test_known_sidecar_stat_failure_does_not_hide_other_overviews(self):
        self.save()
        self.put("concepts/別.md", "# 別")
        ready = self.prepare(page="別")
        self.draft(ready, "### 別の概要", {})
        overview.write(self.wiki, ready["work_id"])
        original = os.lstat
        def lstat(path, *args, **kwargs):
            if Path(path) == self.sidecar:
                raise PermissionError("試験の属性拒否")
            return original(path, *args, **kwargs)
        with mock.patch.object(os, "lstat", side_effect=lstat):
            built = self.build()
        self.assertFalse(built.overview_scan_unknown)
        self.assertEqual(built.overviews[self.pid][1].state, "broken")
        self.assertEqual(built.overviews["concepts/別"][1].state, "fresh")

    def test_unreadable_nfc_collision_is_still_counted_for_binding(self):
        self.put("concepts/café.md", "# café")
        ready = self.prepare(page="café")
        self.draft(ready)
        overview.write(self.wiki, ready["work_id"])
        snapshot = core.take_snapshot(self.wiki)
        snapshot.inputs.append(core.InputFile("page", "concepts/cafe\u0301.md", "concepts/café.md", error="os"))
        built = core.Core(snapshot)
        self.assertEqual(built.overviews["concepts/café"][1].state, "page_unknown")
        self.assertEqual(built.overview_assets, {})

    def test_metadata_is_escaped_and_has_no_generated_ids(self):
        self.save()
        data = self.sidecar.read_bytes().replace(b"generated: ", b'generator: "<script>boom</script>"\ngenerated: ', 1)
        self.sidecar.write_bytes(data)
        html = self.build().body_html(self.pid)
        self.assertIn("&lt;script&gt;boom&lt;/script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn('id=""', html)

    def test_link_installed_after_walk_is_not_read_or_committed(self):
        self.save()
        previous = self.sidecar.read_bytes()
        ready = self.prepare(refresh=True)
        self.draft(ready)
        other = self.put("other.txt", "リンク先の中身")
        original_index, original_read = overview._index, Path.read_bytes
        def index(root):
            found = original_index(root)
            self.source.unlink()
            os.link(other, self.source)
            return found
        def read(path):
            if path == self.source:
                raise AssertionError("リンクの記事を読んだ")
            return original_read(path)
        with mock.patch.object(overview, "_index", side_effect=index), mock.patch.object(Path, "read_bytes", read), \
             mock.patch.object(wiki_pages, "_notice"):
            self.assert_error(overview.write, "page_unreadable", self.wiki, ready["work_id"])
        self.assertEqual(self.sidecar.read_bytes(), previous)
        self.assertTrue(Path(ready["draft_dir"]).exists())

    def test_refused_article_is_not_orphan_or_deletable(self):
        self.save()
        previous = self.sidecar.read_bytes()
        target = self.source.with_suffix(".txt")
        self.source.rename(target)
        os.link(target, self.source)
        self.assertEqual(overview.inspect_wiki(self.wiki)["overviews"][0]["state"], "page_unreadable")
        self.assert_error(overview.remove, "not_orphan", self.wiki, self.key)
        built = self.build()
        self.assertTrue(any(d["kind"] == "overview_page_unreadable" for d in built.diagnostics))
        self.assertFalse(any(d["kind"] == "overview_orphan" for d in built.diagnostics))
        self.assertEqual(self.sidecar.read_bytes(), previous)

    def test_refused_directory_does_not_hide_orphan_from_deletion_guard(self):
        from tests.wiki.test_wiki_links import junction
        self.save()
        previous = self.sidecar.read_bytes()
        path = self.source.parent
        target = path.with_name("moved-concepts")
        path.rename(target)
        if not junction(path, target):
            target.rename(path)
            self.skipTest("ディレクトリのリンクを作れない")
        try:
            self.assertEqual(overview.inspect_wiki(self.wiki)["overviews"][0]["state"], "page_unreadable")
            self.assert_error(overview.remove, "not_orphan", self.wiki, self.key)
            self.assertTrue(any(d["kind"] == "overview_page_unreadable" for d in self.build().diagnostics))
            self.assertEqual(self.sidecar.read_bytes(), previous)
        finally:
            os.rmdir(path) if os.name == "nt" else path.unlink()
            target.rename(path)

    def test_unsafe_sidecar_is_stable_and_link_count_recovery_changes_signature(self):
        self.save()
        linked = self.sidecar.with_name("copy.txt")
        os.link(self.sidecar, linked)
        snapshot = core.take_snapshot(self.wiki)
        self.assertEqual(snapshot.transient, [])
        built = core.Core(snapshot)
        self.assertEqual(built.overviews[self.pid][1].state, "broken")
        self.assertEqual(overview.inspect_wiki(self.wiki)["overviews"][0]["state"], "broken")
        self.assertEqual(built.manifest()["incomplete"]["unreadable_overviews"], 1)
        linked.unlink()
        recovered = self.build()
        self.assertNotEqual(snapshot.signature, recovered.snapshot.signature)
        self.assertEqual(recovered.overviews[self.pid][1].state, "fresh")

    def test_absent_overview_remove_remains_absent_with_unrelated_link(self):
        self.source.unlink()
        target = self.put("notes.txt", "別のファイル")
        os.link(target, self.wiki / "elsewhere.md")
        self.assertEqual(overview.remove(self.wiki, self.key)["status"], "absent")

    def test_oversized_draft_reports_size_once(self):
        ready = self.prepare()
        self.draft(ready, "x" * (overview.MAX_BODY + 1), {})
        result = overview.check(self.wiki, ready["work_id"])
        self.assertEqual(sum(p["code"] == "too_large" for p in result["problems"]), 1)

    def test_sidecar_lstat_and_open_failures_leave_article_visible(self):
        self.save()
        previous = self.sidecar.read_bytes()
        original_lstat, original_open = os.lstat, Path.open
        def lstat(path, *args, **kwargs):
            if Path(path) == self.sidecar:
                raise OSError(errno.EIO, "概要の属性だけ失敗")
            return original_lstat(path, *args, **kwargs)
        with mock.patch.object(os, "lstat", side_effect=lstat):
            built = self.build()
        self.assertTrue(built.overview_scan_unknown)
        self.assertIn("元のページ", built.body_html(self.pid))
        def open_(path, *args, **kwargs):
            if path == self.sidecar:
                raise PermissionError("概要の open だけ失敗")
            return original_open(path, *args, **kwargs)
        with mock.patch.object(Path, "open", open_):
            built = self.build()
        self.assertIn(("overview", self.sidecar.relative_to(self.wiki).as_posix()), built.snapshot.transient)
        self.assertIn("元のページ", built.body_html(self.pid))
        self.assertEqual(self.sidecar.read_bytes(), previous)

    def test_undrawn_article_does_not_export_overview_svg(self):
        self.save()
        with mock.patch.object(core.wiki_lint, "parse_frontmatter_raw", side_effect=ValueError("記事を解釈できない")):
            built = self.build()
        self.assertEqual(built.drawn, {})
        self.assertEqual(built.overview_assets, {})

    def test_overview_only_changes_update_signature_and_generation(self):
        empty = self.build()
        self.save()
        first = self.build()
        self.save("### 別の説明", {})
        second = self.build()
        self.sidecar.unlink()
        removed = self.build()
        self.assertNotEqual(empty.snapshot.signature, first.snapshot.signature)
        self.assertNotEqual(first.generation, second.generation)
        self.assertNotEqual(second.snapshot.signature, removed.snapshot.signature)
        self.assertEqual(removed.snapshot.signature, empty.snapshot.signature)

    def test_core_does_not_reread_source_or_sidecar(self):
        self.save()
        snapshot = core.take_snapshot(self.wiki)
        with mock.patch.object(overview, "read_sidecar", side_effect=AssertionError("再読み取り")), \
             mock.patch.object(fs, "read_input", side_effect=AssertionError("再読み取り")):
            built = core.Core(snapshot)
            self.assertIn("概要専用の語", built.body_html(self.pid))

    def test_render_failure_is_local_to_overview(self):
        self.save()
        built = self.build()
        original = built.parser.renderer.render
        def render(tokens, *args):
            if any(t.content == "概要専用の語" for t in tokens):
                raise RuntimeError("概要だけの描画失敗")
            return original(tokens, *args)
        with mock.patch.object(built.parser.renderer, "render", side_effect=render):
            html = built.body_html(self.pid)
        self.assertIn("元のページ", html)
        self.assertIn("概要を表示できない", html)
        self.assertTrue(any(d["kind"] == "overview_render_error" for d in built.diagnostics))
        self.assertNotIn(self.pid, built._body_cache)
        self.assertIn("概要専用の語", built.body_html(self.pid))
        self.assertFalse(any(d["kind"] == "overview_render_error" for d in built.diagnostics))

    def test_common_markdown_rules_do_not_create_inline_style_or_external_images(self):
        self.save('### 表\n\n| a |\n| :-: |\n| b |\n\n<script>alert(1)</script>\n\n[外](https://example.com)', {})
        html = self.build().body_html(self.pid)
        self.assertNotIn("style=", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn('class="ta-center"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_known_read_failure_recovers_but_unobserved_permission_loss_is_cached(self):
        self.save()
        state = browse.BrowseState(self.wiki)
        with mock.patch.object(fs, "read_overview", return_value=overview.Sidecar("unreadable")):
            failed, _ = state.get()
        self.assertIn(("overview", f"assets/overview/{self.key}.overview.md"), failed.snapshot.transient)
        state.attempts.clear()
        recovered, _ = state.get()
        self.assertEqual(recovered.snapshot.transient, [])
        self.assertEqual(recovered.overviews[self.pid][1].state, "fresh")
        with mock.patch.object(fs, "read_overview", return_value=overview.Sidecar("unreadable")) as read:
            cached, _ = state.get()
        self.assertIs(cached, recovered)
        read.assert_not_called()

    def test_snapshot_retries_if_sidecar_list_changes_during_read(self):
        self.save()
        entries = core.input_list(self.wiki)
        with mock.patch.object(core, "input_list", side_effect=[entries, tuple(e for e in entries if e[0] != "overview")]):
            with self.assertRaises(core.InputsChanged):
                core.take_snapshot(self.wiki)


class OverviewHttpTests(InProcess):
    def save(self, body="### HTTPの概要\n\n![図](#fig-flow)", svg=SVG):
        ready = overview.begin(self.wiki)
        Path(ready["request_path"]).write_bytes(json.dumps({"format": 2, "action": "create", "page": "a", "refresh": True}).encode("utf-8"))
        work = overview.prepare(self.wiki)
        (Path(work["draft_dir"]) / "overview.md").write_bytes(body.encode("utf-8"))
        (Path(work["draft_dir"]) / "flow.svg").write_bytes(svg)
        self.assertEqual(overview.check(self.wiki, work["work_id"]), {"status": "ok"})
        return overview.write(self.wiki, work["work_id"])

    def test_svg_http_matches_static_and_has_restrictive_csp(self):
        self.save()
        code, body, headers = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertIn("HTTPの概要", body)
        self.assertIn("style-src 'self'", headers["Content-Security-Policy"])
        built = self.app.state.current
        name = next(iter(built.overview_assets))
        code, data, headers = self.get(name)
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Security-Policy"], core.CSP_SVG)
        static = core.Core(core.take_snapshot(self.wiki)).render_all("text")
        self.assertEqual(data.encode("utf-8"), static[name])
        self.assertEqual(self.get(name, "HEAD")[1], "")
        self.assertEqual(self.get("assets/overview/../../server.json")[0], 404)

    def test_overview_only_update_and_delete_rebuild_http_without_changing_page(self):
        saved = self.save()
        original = (self.wiki / "concepts/a.md").read_bytes()
        self.assertEqual(self.get("concepts/a.html")[0], 200)
        first = self.app.state.current
        old_name = next(iter(first.overview_assets))
        self.save("### 更新後の概要\n\n![図](#fig-flow)", SVG.replace(b"flow", b"new"))
        code, body, _ = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertIn("更新後の概要", body)
        second = self.app.state.current
        self.assertNotEqual(first.generation, second.generation)
        self.assertEqual(self.get(old_name)[0], 404)
        self.assertEqual(self.get(next(iter(second.overview_assets)))[0], 200)
        (self.wiki / saved["sidecar"]).unlink()
        self.assertNotIn('<details class="wiki-overview', self.get("concepts/a.html")[1])
        self.assertEqual((self.wiki / "concepts/a.md").read_bytes(), original)
