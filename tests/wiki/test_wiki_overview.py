"""概要の保存、検査、状態、経路、停止時の契約（ADR-0031）の試験。

一時的な wiki を使う。ネットワークや LLM は使わない。実機の電源断は試さない。
    python -X utf8 -B -m unittest tests/wiki/test_wiki_overview.py -v
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_overview as overview
import wiki_pages
import wiki_lint
import wiki_fetch

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="120"><text x="10" y="30">flow</text></svg>'
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


class OverviewCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.wiki = self.base / "wiki"
        self.wiki.mkdir()
        self.put("SCHEMA.md", "# スキーマ\n")
        self.source = self.put("concepts/概要の元.md", "---\ntitle: \"概要の元\"\n---\n\n# 元のページ\n\n本文。\n")
        self.key = overview.page_key("concepts/概要の元")
        self.sidecar = self.wiki / "assets/overview" / f"{self.key}.overview.md"

    def put(self, rel, value):
        path = self.wiki / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))
        return path

    def request(self, action="create", **values):
        ready = overview.begin(self.wiki)
        request = {"format": 2, "action": action, "page": "概要の元", **values}
        Path(ready["request_path"]).write_bytes(json.dumps(request, ensure_ascii=False).encode("utf-8"))
        return Path(ready["request_path"])

    def prepare(self, **values):
        self.request(**values)
        return overview.prepare(self.wiki)

    def draft(self, ready, body="### 概要\n\n![流れ](#fig-flow)\n", figures=None):
        folder = Path(ready["draft_dir"])
        (folder / "overview.md").write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
        for name, value in (figures if figures is not None else {"flow.svg": SVG}).items():
            (folder / name).write_bytes(value)
        return folder

    def saved(self):
        ready = self.prepare()
        self.draft(ready)
        self.assertEqual(overview.check(self.wiki, ready["work_id"]), {"status": "ok"})
        result = overview.write(self.wiki, ready["work_id"])
        self.assertEqual(result["status"], "written")
        return result

    def lint(self):
        return wiki_lint.lint(wiki_lint.collect_pages(self.wiki), 100, 200, [], False, 5, wiki_root=self.wiki)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-X", "utf8", "-B", str(SCRIPTS / "wiki_overview.py"), *map(str, args)],
                              cwd=ROOT, capture_output=True, encoding="utf-8", env=ENV, timeout=30)

    def assert_error(self, function, code, *args):
        with self.assertRaises(overview.OverviewError) as caught:
            function(*args)
        self.assertEqual(caught.exception.payload.get("code", caught.exception.payload["status"]), code)
        return caught.exception


class WorkflowTests(OverviewCase):
    def test_roundtrip_preserves_body_and_embeds_svg(self):
        ready = self.prepare(generator="GPT-6 Astra")
        body = "### 日本語の概要\r\n\r\n文中に ![流れ](#fig-flow) を置く。\r\n"
        self.draft(ready, body)
        result = overview.write(self.wiki, ready["work_id"])
        self.assertEqual(result["figures"], ["flow"])
        self.assertFalse(result["page_changed"])
        data = self.sidecar.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        meta, _, rendered_body, malformed = wiki_lint.parse_frontmatter_raw(data.decode("utf-8"))
        self.assertFalse(malformed)
        self.assertIn(body.replace("\r\n", "\n"), rendered_body)
        self.assertEqual(meta["format"], "2")
        self.assertEqual(meta["generator"], "GPT-6 Astra")
        self.assertEqual(meta["page"], "concepts/概要の元")
        self.assertEqual(set(overview.embedded_figures(data)), {"flow"})
        self.assertFalse(Path(ready["draft_dir"]).parent.exists())
        self.assertEqual(overview.status(self.wiki)["overviews"][0]["state"], "fresh")

    def test_fresh_exists_refresh_and_invalid_generator(self):
        self.saved()
        self.assertEqual(self.prepare()["status"], "exists")
        ready = self.prepare(refresh=True, generator="引用符\"つき")
        self.draft(ready, "本文だけ。", {})
        overview.write(self.wiki, ready["work_id"])
        meta = wiki_lint.parse_frontmatter_raw(self.sidecar.read_text(encoding="utf-8"))[0]
        self.assertNotIn("generator", meta)
        self.assertEqual(meta["figures"], [])

    def test_shell_like_name_is_a_json_value(self):
        name = "日本語”（$変数）"
        self.put(f"concepts/{name}.md", "本文。")
        request = self.request(page=name)
        done = self.cli("prepare", self.wiki)
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        self.assertEqual(json.loads(done.stdout)["page"], f"concepts/{name}")
        self.assertFalse(request.exists())

    def test_requests_are_consumed_on_invalid_json_and_wrong_action(self):
        request = self.request()
        request.write_bytes(b"{")
        self.assert_error(overview.prepare, "invalid_request", self.wiki)
        self.assertFalse(request.exists())
        request = self.request(action="remove")
        self.assert_error(overview.prepare, "wrong_action", self.wiki)
        self.assertFalse(request.exists())
        self.assert_error(overview.prepare, "no_request", self.wiki)

    def test_ambiguous_slug_can_be_selected_by_exact_id(self):
        self.put("概要の元.md", "別のページ。")
        self.request()
        error = self.assert_error(overview.prepare, "ambiguous", self.wiki)
        self.assertEqual(set(error.payload["candidates"]), {"概要の元", "concepts/概要の元"})
        request = overview.begin(self.wiki)["request_path"]
        Path(request).write_bytes(json.dumps({"format": 2, "action": "create", "id": "概要の元"}).encode("utf-8"))
        self.assertEqual(overview.prepare(self.wiki)["page"], "概要の元")

    def test_nfc_collision_is_ambiguous(self):
        self.put("concepts/が.md", "NFC")
        self.put("concepts/か\u3099.md", "NFD")
        self.request(page="が")
        self.assert_error(overview.prepare, "ambiguous", self.wiki)

    def test_hash_collision_stops_creation(self):
        self.put("concepts/別のページ.md", "本文。")
        self.request()
        with mock.patch.object(overview, "page_key", return_value="a" * 16):
            self.assert_error(overview.prepare, "id_collision", self.wiki)

    def test_hash_normalizes_bom_and_all_newlines(self):
        expected = hashlib.sha256("本文\n次の行\n".encode("utf-8")).hexdigest()
        for text in ("本文\n次の行\n", "\ufeff本文\r\n次の行\r\n", "本文\r次の行\r"):
            with self.subTest(text=repr(text)):
                self.assertEqual(wiki_pages.page_text_sha256(text.encode("utf-8")), expected)

    def test_page_change_before_save_marks_stale(self):
        ready = self.prepare()
        self.draft(ready)
        self.source.write_bytes("変更した本文。".encode("utf-8"))
        result = overview.write(self.wiki, ready["work_id"])
        self.assertTrue(result["page_changed"])
        self.assertEqual(overview.status(self.wiki)["overviews"][0]["state"], "stale")

    def test_non_utf8_before_save_keeps_old_overview_and_draft(self):
        self.saved()
        original = self.sidecar.read_bytes()
        ready = self.prepare(refresh=True)
        self.draft(ready)
        self.source.write_bytes(b"\xff")
        error = self.assert_error(overview.write, "page_unreadable", self.wiki, ready["work_id"])
        self.assertEqual(error.exit_code, 1)
        self.assertEqual(self.sidecar.read_bytes(), original)
        self.assertTrue(Path(ready["draft_dir"]).exists())
        self.source.write_bytes("回復した本文。".encode("utf-8"))
        self.assertEqual(overview.write(self.wiki, ready["work_id"])["status"], "written")

    def test_os_error_and_first_save_leave_no_sidecar(self):
        ready = self.prepare()
        self.draft(ready)
        original = Path.read_bytes

        def denied(path):
            if path == self.source:
                raise PermissionError("試験の読み取り拒否")
            return original(path)

        with mock.patch.object(Path, "read_bytes", denied):
            self.assert_error(overview.write, "page_unreadable", self.wiki, ready["work_id"])
        self.assertFalse(self.sidecar.exists())
        self.assertTrue(Path(ready["draft_dir"]).exists())

    def test_page_removed_before_or_after_walk_keeps_draft(self):
        for after_walk in (False, True):
            with self.subTest(after_walk=after_walk):
                self.source.write_bytes(b"page")
                ready = self.prepare()
                self.draft(ready)
                original = overview._checked

                def checked(*args):
                    result = original(*args)
                    self.source.unlink()
                    return result

                if not after_walk:
                    self.source.unlink()
                with mock.patch.object(overview, "_checked", checked if after_walk else original):
                    error = self.assert_error(overview.write, "page_gone", self.wiki, ready["work_id"])
                self.assertEqual(error.exit_code, 3)
                self.assertFalse(self.sidecar.exists())
                self.assertTrue(Path(ready["draft_dir"]).exists())

    def test_no_page_reread_after_replace(self):
        for change in (b"changed", b"\xff", None):
            with self.subTest(change=change):
                self.source.write_bytes(b"page")
                ready = self.prepare(refresh=True)
                self.draft(ready)
                original_read = Path.read_bytes
                original_replace = wiki_fetch.replace_with_retry
                reads = []

                def read(path):
                    if path == self.source:
                        reads.append(path)
                    return original_read(path)

                def replace(src, dst):
                    if change is None:
                        self.source.unlink()
                    else:
                        self.source.write_bytes(change)
                    original_replace(src, dst)

                with mock.patch.object(Path, "read_bytes", read), mock.patch.object(wiki_fetch, "replace_with_retry", replace):
                    result = overview.write(self.wiki, ready["work_id"])
                self.assertEqual(result["status"], "written")
                self.assertFalse(result["page_changed"])
                self.assertEqual(len(reads), 1)

    def test_cross_device_keeps_old_overview_and_draft(self):
        self.saved()
        old = self.sidecar.read_bytes()
        ready = self.prepare(refresh=True)
        self.draft(ready)
        with mock.patch.object(wiki_fetch, "replace_with_retry", side_effect=OSError(errno.EXDEV, "different volume")):
            self.assert_error(overview.write, "cross_device", self.wiki, ready["work_id"])
        self.assertEqual(self.sidecar.read_bytes(), old)
        self.assertTrue(Path(ready["draft_dir"]).exists())
        self.assertEqual(list(self.wiki.joinpath(*overview.CACHE, "tmp").iterdir()), [])

    def test_cleanup_error_does_not_change_committed_success(self):
        ready = self.prepare()
        self.draft(ready)
        with mock.patch.object(overview, "_remove_tree", side_effect=PermissionError("試験")):
            self.assertEqual(overview.write(self.wiki, ready["work_id"])["status"], "written")
        self.assertEqual(overview.status(self.wiki)["overviews"][0]["state"], "fresh")

    def test_remove_returns_removed_and_absent(self):
        self.saved()
        self.request(action="remove")
        self.assertEqual(overview.remove(self.wiki)["status"], "removed")
        self.request(action="remove")
        self.assertEqual(overview.remove(self.wiki)["status"], "absent")

    def test_broken_orphan_can_be_removed_without_reading_contents(self):
        self.saved()
        self.source.unlink()
        self.sidecar.write_bytes(b"broken")
        finding = self.lint()["overview_problems"][0]
        self.assertEqual(finding["code"], "broken")
        self.assertTrue(finding["page_absent"])
        self.assertEqual(finding["orphan_id"], self.key)
        with mock.patch.object(overview, "_read", side_effect=AssertionError("孤立した概要の本文は読まない")):
            self.assertEqual(overview.remove(self.wiki, self.key)["status"], "removed")

    def test_orphan_remove_never_removes_existing_page_overview(self):
        self.saved()
        self.assert_error(overview.remove, "not_orphan", self.wiki, self.key)
        self.assertTrue(self.sidecar.exists())


class ValidationTests(OverviewCase):
    def test_invalid_drafts_return_machine_codes(self):
        cases = [
            (b"\xff", {}, "not_utf8"), (" \n", {}, "empty"), ("あ" * overview.MAX_BODY, {}, "too_large"),
            ("---\nkey: value\n---\n本文。", {}, "frontmatter"),
            ("## 上位の見出し\n", {}, "heading_level"), ("本文に [[ページ]]。", {}, "wikilink"),
            ("```svg-figure fake\n<svg/>\n```\n", {}, "figure_fence"),
            ("![外](https://example.invalid/a.svg)", {}, "image_ref"),
            ("![図](#fig-flow)", {}, "figure_missing"), ("本文だけ。", {"flow.svg": SVG}, "figure_unused"),
            ("![図](#fig-flow)", {"flow.svg": SVG.replace(b"</svg>", b"")}, "figure_xml"),
            ("![図](#fig-flow)", {"flow.svg": b'<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg"/>'}, "figure_xml"),
            ("![図](#fig-flow)", {"flow.svg": b'<svg xmlns="http://www.w3.org/2000/svg"/>'}, "figure_no_size"),
            ("![図](#fig-flow)", {"flow.svg": b"\x00" + SVG}, "figure_encoding"),
            ("本文だけ。", {"unknown.txt": b"x"}, "extra_file"),
            ("![図](#fig-flow)\n\n```mermaid\nflowchart TD\n A --> B\n", {"flow.svg": SVG}, "assembly"),
        ]
        for body, figures, code in cases:
            with self.subTest(code=code):
                ready = self.prepare()
                self.draft(ready, body, figures)
                result = overview.check(self.wiki, ready["work_id"])
                self.assertEqual(result["status"], "rejected")
                self.assertIn(code, {p["code"] for p in result["problems"]})
                self.assertFalse(self.sidecar.exists())

    def test_code_image_literals_and_mermaid_are_not_svg_references(self):
        ready = self.prepare()
        self.draft(ready, 'コード `![図](#fig-missing)`。\n\n```mermaid\nflowchart TD\n A --> B\n```\n', {})
        self.assertEqual(overview.check(self.wiki, ready["work_id"]), {"status": "ok"})

    def test_svg_backticks_cannot_close_generated_fence(self):
        ready = self.prepare()
        svg = SVG.replace(b"flow", b"````````")
        self.draft(ready, figures={"flow.svg": svg})
        overview.write(self.wiki, ready["work_id"])
        data = self.sidecar.read_bytes()
        self.assertIn(b"`````````svg-figure flow", data)
        self.assertIn(b"````````", overview.embedded_figures(data)["flow"])

    def test_size_and_figure_count_limits(self):
        ready = self.prepare()
        figures = {f"f{i}.svg": SVG for i in range(13)}
        self.draft(ready, "\n".join(f"![図](#fig-f{i})" for i in range(13)), figures)
        self.assertIn("too_many_figures", {p["code"] for p in overview.check(self.wiki, ready["work_id"])["problems"]})
        ready = self.prepare()
        self.draft(ready, figures={"flow.svg": SVG + b" " * overview.MAX_SVG})
        self.assertIn("figure_encoding", {p["code"] for p in overview.check(self.wiki, ready["work_id"])["problems"]})

    def test_combined_sidecar_size_limit(self):
        ready = self.prepare()
        # 各図は 2 MiB 未満でも、5枚でサイドカー全体の 8 MiB を超える。
        svg = SVG.replace(b"flow", b"x" * (1800 * 1024))
        self.draft(ready, "\n".join(f"![図](#fig-f{i})" for i in range(5)), {f"f{i}.svg": svg for i in range(5)})
        self.assertIn("assembly", {p["code"] for p in overview.check(self.wiki, ready["work_id"])["problems"]})

    def test_classification_priority_and_all_page_states(self):
        plan = {"page": "concepts/概要の元", "page_sha256": "a" * 64}
        data = overview._assemble(plan, "本文。", {})
        sidecar = overview.Sidecar("ok", data)
        cases = [(overview.PageState("unknown"), "page_unknown"), (overview.PageState("absent"), "orphan"),
                 (overview.PageState("unreadable"), "page_unreadable"), (overview.PageState("ok", "b" * 64), "stale"),
                 (overview.PageState("ok", "a" * 64), "fresh")]
        for page, expected in cases:
            self.assertEqual(overview.classify(self.key, sidecar, page).state, expected)
        self.assertEqual(overview.classify(self.key, overview.Sidecar("absent"), cases[0][0]).state, "none")
        self.assertEqual(overview.classify(self.key, overview.Sidecar("ok", b"bad"), overview.PageState("absent")).state, "broken")
        for original, replacement, reason in [(b"format: 2", b"format: 3", "format"),
                                               (b'page: "concepts/', b'page: "changed/', "page_field"),
                                               (b"a" * 64, b"bad-hash", "fields")]:
            broken = data.replace(original, replacement) + b"```svg-figure bad\nnot xml\n```\n"
            self.assertEqual(overview.classify(self.key, overview.Sidecar("ok", broken), cases[-1][0]).detail, reason)


class FilesystemTests(OverviewCase):
    def link(self, destination, target, *, directory=False):
        try:
            os.symlink(target, destination, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない")

    def test_cache_and_assets_links_are_rejected(self):
        target = self.base / "outside"
        target.mkdir()
        self.link(self.wiki / ".wiki-cache", target, directory=True)
        self.assert_error(overview.begin, "unsafe_path", self.wiki)
        self.assertEqual(list(target.iterdir()), [])

    def test_wrong_case_directory_is_not_used(self):
        (self.wiki / "Assets").mkdir()
        self.assert_error(overview.begin, "spelling", self.wiki)
        self.assertFalse((self.wiki / ".wiki-cache").exists())

    @unittest.skipUnless(os.name == "nt", "Windows のジャンクションの試験")
    def test_junction_is_not_followed(self):
        target = self.base / "outside-junction"
        target.mkdir()
        link = self.wiki / ".wiki-cache"
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                              capture_output=True, encoding="utf-8", errors="replace", timeout=10)
        if done.returncode != 0:
            self.skipTest("ジャンクションを作れない")
        self.assert_error(overview.begin, "unsafe_path", self.wiki)
        self.assertEqual(list(target.iterdir()), [])

    def test_hardlink_destination_is_not_replaced_or_removed(self):
        self.saved()
        outside = self.base / "outside.md"
        try:
            os.link(self.sidecar, outside)
        except OSError:
            self.skipTest("ハードリンクを作れない")
        original = outside.read_bytes()
        ready = self.prepare(refresh=True)
        self.draft(ready)
        self.assert_error(overview.write, "unsafe_path", self.wiki, ready["work_id"])
        self.assertEqual(outside.read_bytes(), original)
        self.request(action="remove")
        self.assert_error(overview.remove, "unsafe_path", self.wiki)

    def test_draft_link_is_rejected_without_following(self):
        ready = self.prepare()
        self.draft(ready, "本文。", {})
        outside = self.base / "outside.svg"
        outside.write_bytes(SVG)
        self.link(Path(ready["draft_dir"]) / "flow.svg", outside)
        result = overview.check(self.wiki, ready["work_id"])
        self.assertIn("extra_file", {p["code"] for p in result["problems"]})
        self.assertEqual(outside.read_bytes(), SVG)

    def test_incomplete_page_walk_stops_delete_and_reports_unknown(self):
        self.saved()
        original = os.scandir

        def scan(path):
            if Path(path) == self.wiki / "concepts":
                raise PermissionError("試験の一覧拒否")
            return original(path)

        with mock.patch.object(os, "scandir", scan):
            self.assert_error(overview.remove, "walk_incomplete", self.wiki, self.key)
            result = overview.inspect_wiki(self.wiki)
        self.assertFalse(result["complete"])
        self.assertEqual(result["overviews"][0]["state"], "page_unknown")
        self.assertTrue(self.sidecar.exists())

    def test_unlistable_sidecars_are_not_reported_as_zero_problems(self):
        self.saved()
        original = os.scandir

        def scan(path):
            if Path(path) == self.sidecar.parent:
                raise PermissionError("試験の一覧拒否")
            return original(path)

        with mock.patch.object(os, "scandir", scan):
            result = self.lint()
        self.assertIsNone(result["overview_problems"])
        self.assertIsNone(result["summary"]["overview_problems"])
        self.assertIn("概要の検査は完了していない", wiki_lint.render_text(result))

    def test_eio_in_overview_scan_does_not_stop_other_lint_findings(self):
        self.saved()
        original = os.scandir

        def scan(path):
            if Path(path) == self.sidecar.parent:
                raise OSError(errno.EIO, "試験の I/O エラー")
            return original(path)

        with mock.patch.object(os, "scandir", scan):
            inspection = overview.inspect_wiki(self.wiki)
            report = self.lint()
        self.assertFalse(inspection["complete"])
        self.assertIsNone(inspection["overview_problems"])
        self.assertEqual(report["summary"]["total_pages"], 1)
        self.assertTrue(report["orphans"])
        self.assertIsNone(report["overview_problems"])

    def test_eio_during_overview_iteration_is_also_incomplete(self):
        self.saved()
        original = os.scandir
        closed = []

        class Iterator:
            def __next__(self):
                raise OSError(errno.EIO, "試験の途中の I/O エラー")

            def close(self):
                closed.append(True)

        def scan(path):
            return Iterator() if Path(path) == self.sidecar.parent else original(path)

        with mock.patch.object(os, "scandir", scan):
            self.assertIsNone(overview.inspect_wiki(self.wiki)["overview_problems"])
        self.assertEqual(closed, [True])

    def test_begin_cleans_only_old_owned_work(self):
        ready = self.prepare()
        work = Path(ready["draft_dir"]).parent
        old = time.time() - 8 * 86400
        os.utime(work, (old, old))
        outside = self.wiki.joinpath(*overview.CACHE, "work", "user-folder")
        outside.mkdir()
        overview.begin(self.wiki)
        self.assertFalse(work.exists())
        self.assertTrue(outside.exists())

    def test_real_child_exit_during_write_fsync_and_around_replace(self):
        code = '''
import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import wiki_overview, wiki_fetch
when=sys.argv[4]
def stop(src,dst):
    if when=='after': os.replace(src,dst)
    os._exit(92 if when=='after' else 91)
wiki_fetch.replace_with_retry=stop
if when=='after_fsync':
    original_fsync=os.fsync
    def stop_fsync(fd):
        original_fsync(fd)
        os._exit(94)
    os.fsync=stop_fsync
elif when=='during_write':
    original_open=Path.open
    class PartialWrite:
        def __init__(self,stream): self.stream=stream
        def __enter__(self): return self
        def __exit__(self,*args): self.stream.close()
        def write(self,data):
            self.stream.write(data[:len(data)//2])
            self.stream.flush()
            os._exit(93)
    def partial_open(path,*args,**kwargs):
        stream=original_open(path,*args,**kwargs)
        return PartialWrite(stream) if path.suffix=='.tmp' and args==('xb',) else stream
    Path.open=partial_open
wiki_overview.write(Path(sys.argv[2]),sys.argv[3])
'''
        for when in ("during_write", "after_fsync", "before", "after"):
            for existing in (False, True):
                with self.subTest(when=when, existing=existing):
                    if self.sidecar.exists():
                        self.sidecar.unlink()
                    if existing:
                        self.sidecar.parent.mkdir(parents=True, exist_ok=True)
                        self.sidecar.write_bytes(b"old-complete-state")
                    ready = self.prepare(refresh=True)
                    self.draft(ready)
                    done = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code, str(SCRIPTS),
                                           str(self.wiki), ready["work_id"], when], capture_output=True,
                                          encoding="utf-8", env=ENV, timeout=30)
                    self.assertEqual(done.returncode, {"before": 91, "after": 92, "during_write": 93, "after_fsync": 94}[when], done.stderr)
                    if when != "after":
                        self.assertEqual(self.sidecar.read_bytes() if existing else self.sidecar.exists(),
                                         b"old-complete-state" if existing else False)
                    else:
                        self.assertEqual(overview.status(self.wiki)["overviews"][0]["state"], "fresh")


class IntegrationTests(OverviewCase):
    def cp932_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / "wiki_overview.py"), *map(str, args)],
                              capture_output=True, env={**os.environ, "PYTHONUTF8": "0", "PYTHONIOENCODING": "cp932"},
                              timeout=30)

    def test_cp932_host_receives_utf8_json_after_committed_write(self):
        self.put("concepts/絵文字😀.md", "日本語の本文。")
        ready = self.prepare(page="絵文字😀")
        self.draft(ready, "### 概要\n\n日本語の概要。", {})
        done = self.cp932_cli("write", self.wiki, f"--work={ready['work_id']}")
        self.assertEqual(done.returncode, 0, done.stderr.decode("utf-8", "replace"))
        result = json.loads(done.stdout.decode("utf-8"))
        self.assertEqual(result["status"], "written")
        self.assertEqual(result["page"], "concepts/絵文字😀")
        self.assertTrue((self.wiki / result["sidecar"]).is_file())
        self.assertFalse(Path(ready["draft_dir"]).parent.exists())

    def test_cp932_host_receives_utf8_json_on_early_error(self):
        done = self.cp932_cli("status", self.base)
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout.decode("utf-8"))
        self.assertEqual(result["code"], "not_initialized")
        self.assertIn("初期化された wiki ではない", result["message"])
        self.assertEqual(done.stderr, b"")

    def test_lint_reports_stale_orphan_and_rename_candidates(self):
        self.saved()
        original = self.source.read_bytes()
        self.source.write_bytes(original + b"changed")
        report = self.lint()
        self.assertEqual(len(report["overview_stale"]), 1)
        self.assertIn("概要", wiki_lint.render_text(report))
        self.source.unlink()
        self.put("concepts/改名先.md", original)
        report = self.lint()
        finding = report["overview_problems"][0]
        self.assertEqual(finding["code"], "orphan")
        self.assertEqual(finding["candidates"], ["concepts/改名先"])

    def test_derived_files_do_not_change_page_set_or_missing_assets(self):
        before = [f.rel for f in wiki_pages.walk_pages(self.wiki).files]
        self.saved()
        self.assertEqual([f.rel for f in wiki_pages.walk_pages(self.wiki).files], before)
        self.assertEqual(self.lint()["summary"]["total_pages"], 1)
        self.assertEqual(wiki_lint.missing_assets("![図](#fig-flow)", self.source, self.wiki), [])

    def test_cli_errors_are_one_json_and_have_exit_codes(self):
        for args, code, status in [(('status', self.base), 1, 'error'),
                                    (('check', self.wiki, '--work=../outside'), 1, 'error'),
                                    (('remove', self.wiki, '--orphan=../../outside'), 1, 'error')]:
            done = self.cli(*args)
            self.assertEqual(done.returncode, code, done.stdout + done.stderr)
            self.assertEqual(json.loads(done.stdout)["status"], status)
            self.assertNotIn("Traceback", done.stderr)
        ready = self.prepare()
        self.draft(ready, "## 禁じた見出し", {})
        done = self.cli("check", self.wiki, f"--work={ready['work_id']}")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(json.loads(done.stdout)["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
