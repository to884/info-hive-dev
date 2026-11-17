"""Playwright への切り替えと raw の保存を、ブラウザを起動せずに検査する。

本物の Chromium と遅延するページは check_wiki_fetch_browser.py で確かめる。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_fetch
import wiki_fetch_browser

URL = "https://example.com/start"
FINAL = "https://example.com/posts/article"
SHORT = b"<html><main>Loading</main></html>"
DOM = ('<html lang="ja"><head><title>遅れた本文</title></head><body><article><h1>遅れた本文</h1>'
       '<p>' + 'JavaScript で表示した日本語の本文である。' * 40
       + '</p><p><a href="../reference">参照</a></p><img src="figure.png" alt="図"/>'
       '</article></body></html>').encode("utf-8")


class FallbackTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wiki = self.root / "wiki"
        self.raw = self.root / "raw"
        self.wiki.mkdir()
        self.raw.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# 規約\n", encoding="utf-8")
        self.args = argparse.Namespace(url=URL, wiki=self.wiki, raw_root=self.raw, slug="article",
                                       json=True, no_images=True, timeout=5, max_bytes=200000,
                                       max_images=50, force=False, browser_fallback=True, browser_session="isolated")
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(wiki_fetch, "is_private_host", return_value=False).start()
        self.http = mock.patch.object(wiki_fetch, "fetch", return_value=(SHORT, URL, "text/html")).start()
        self.browser = mock.patch.object(wiki_fetch, "fetch_browser", return_value=(DOM, FINAL, "text/html; charset=utf-8")).start()

    def test_short_http_is_replaced_before_writing_and_uses_dom_hash_and_final_url(self):
        code, result = wiki_fetch.build(self.args)
        self.assertEqual(code, 0)
        self.browser.assert_called_once_with(URL, 5, 200000, True, browser="system",
                                            browser_session="isolated", capture_images=mock.ANY, max_images=0)
        self.assertEqual(result["source_sha256"], hashlib.sha256(DOM).hexdigest())
        self.assertEqual(result["source_sha256_of"], "dom")
        self.assertEqual(result["fetch_method"], "playwright")
        self.assertEqual(result["browser_fallback_reason"], "short_body")
        text = (self.raw / "article.md").read_text(encoding="utf-8")
        self.assertNotIn("Loading", text)
        self.assertIn("https://example.com/reference", text)
        self.assertEqual(result["images"][0]["url"], "https://example.com/posts/figure.png")
        saved = self.wiki / ".wiki-cache/ingest/article"
        self.assertEqual((saved / "fetched.md").read_bytes(), (self.raw / "article.md").read_bytes())

    def test_normal_body_does_not_start_browser(self):
        self.http.return_value = DOM, URL, "text/html"
        code, result = wiki_fetch.build(self.args)
        self.assertEqual(code, 0)
        self.browser.assert_not_called()
        self.assertEqual(result["fetch_method"], "http")

    def test_boilerplate_removed_by_rules_does_not_count_as_body(self):
        html = '<html><main>' + '<p>Press enter or click to view image in full size</p>' * 20 + '</main></html>'
        self.http.return_value = html.encode("utf-8"), URL, "text/html"
        _, result = wiki_fetch.build(self.args)
        self.browser.assert_called_once()
        self.assertEqual(result["fetch_method"], "playwright")

    def test_keep_noise_is_respected_when_deciding_whether_to_start_browser(self):
        html = '<html><main>' + '<p>Press enter or click to view image in full size</p>' * 20 + '</main></html>'
        self.args.keep_noise = True
        self.http.return_value = html.encode("utf-8"), URL, "text/html"
        _, result = wiki_fetch.build(self.args)
        self.browser.assert_not_called()
        self.assertEqual(result["fetch_method"], "http")

    def test_without_flag_keeps_standard_library_path(self):
        self.args.browser_fallback = False
        _, result = wiki_fetch.build(self.args)
        self.browser.assert_not_called()
        self.assertEqual(result["source_sha256_of"], "html")

    def test_http_403_tries_browser(self):
        self.http.side_effect = wiki_fetch.FetchError("HTTP 403", http_status=403)
        _, result = wiki_fetch.build(self.args)
        self.assertEqual(result["browser_fallback_reason"], "http_403")
        self.browser.assert_called_once()

    def test_browser_starts_from_original_url_after_http_redirect(self):
        self.http.return_value = SHORT, FINAL, "text/html"
        wiki_fetch.build(self.args)
        self.browser.assert_called_once_with(URL, 5, 200000, True, browser="system",
                                            browser_session="isolated", capture_images=mock.ANY, max_images=0)

    def test_browser_override_is_forwarded_for_short_body_and_http_403(self):
        self.args.browser = "msedge"
        wiki_fetch.build(self.args)
        self.browser.assert_called_once_with(URL, 5, 200000, True, browser="msedge",
                                            browser_session="isolated", capture_images=mock.ANY, max_images=0)
        self.args.force = True
        self.browser.reset_mock()
        self.http.side_effect = wiki_fetch.FetchError("HTTP 403", http_status=403)
        wiki_fetch.build(self.args)
        self.browser.assert_called_once_with(URL, 5, 200000, True, browser="msedge",
                                            browser_session="isolated", capture_images=mock.ANY, max_images=0)

    def test_other_errors_do_not_start_browser(self):
        for status in (404, 429, 500, None):
            with self.subTest(status=status):
                self.http.side_effect = wiki_fetch.FetchError("取得の失敗", http_status=status)
                with self.assertRaises(wiki_fetch.FetchError):
                    wiki_fetch.build(self.args)
        self.browser.assert_not_called()
        self.assertFalse((self.raw / "article.md").exists())

    def test_http_401_uses_browser_session(self):
        self.http.side_effect = wiki_fetch.FetchError("HTTP 401", http_status=401)
        _, result = wiki_fetch.build(self.args)
        self.assertEqual(result["browser_fallback_reason"], "http_401")

    def test_browser_only_does_not_fetch_login_wall_over_http(self):
        self.args.browser_only = True
        _, result = wiki_fetch.build(self.args)
        self.http.assert_not_called()
        self.assertEqual(result["browser_fallback_reason"], "explicit")

    def test_browser_only_does_not_resume_anonymous_work_copy(self):
        wiki_fetch.build(self.args)
        self.args.browser_only = True
        self.browser.reset_mock()
        _, result = wiki_fetch.build(self.args)
        self.browser.assert_called_once()
        self.assertNotIn("fetch_skipped", result)

    def test_existing_session_images_use_captured_pixels_without_anonymous_request(self):
        from tests.wiki.test_wiki_fetch import png
        self.args.browser_session = "existing"
        self.args.no_images = False
        self.args.browser_only = True
        image_url = "https://example.com/posts/figure.png"
        def captured(*args, capture_images, **kwargs):
            capture_images[image_url] = png(120, 80)
            return DOM, FINAL, "text/html"
        self.browser.side_effect = captured
        _, result = wiki_fetch.build(self.args)
        self.http.assert_not_called()
        self.assertTrue((self.raw / result["images"][0]["path"]).is_file())
        self.assertEqual(result["browser_session"], "existing")

    def test_uncaptured_session_image_is_not_retrieved_without_authentication(self):
        self.args.browser_session = "existing"
        self.args.no_images = False
        self.args.browser_only = True
        _, result = wiki_fetch.build(self.args)
        self.http.assert_not_called()
        self.assertEqual(result["images"][0]["status"], "failed")

    def test_non_html_does_not_start_browser(self):
        self.http.return_value = b"%PDF-1.7", URL, "application/pdf"
        with self.assertRaises(wiki_fetch.FetchError):
            wiki_fetch.build(self.args)
        self.browser.assert_not_called()

    def test_browser_failure_keeps_previous_raw_and_work_copy_even_when_forced(self):
        wiki_fetch.build(self.args)
        saved = self.wiki / ".wiki-cache/ingest/article"
        before_raw = (self.raw / "article.md").read_bytes()
        before_copy = (saved / "fetched.md").read_bytes()
        before_json = (saved / "fetch.json").read_bytes()
        self.args.force = True
        self.browser.side_effect = wiki_fetch.FetchError("Chromium を起動できない")
        with self.assertRaises(wiki_fetch.FetchError):
            wiki_fetch.build(self.args)
        self.assertEqual((self.raw / "article.md").read_bytes(), before_raw)
        self.assertEqual((saved / "fetched.md").read_bytes(), before_copy)
        self.assertEqual((saved / "fetch.json").read_bytes(), before_json)

    def test_failed_first_capture_leaves_no_raw_or_copy(self):
        self.browser.side_effect = wiki_fetch.FetchError("本文を取れない")
        with self.assertRaises(wiki_fetch.FetchError):
            wiki_fetch.build(self.args)
        self.assertEqual(list(self.raw.iterdir()), [])
        self.assertFalse((self.wiki / ".wiki-cache").exists())

    def test_resume_keeps_method_without_fetching(self):
        wiki_fetch.build(self.args)
        self.http.reset_mock()
        self.browser.reset_mock()
        code, result = wiki_fetch.build(self.args)
        self.assertEqual(code, 0)
        self.assertTrue(result["fetch_skipped"])
        self.assertEqual(result["fetch_method"], "playwright")
        self.assertEqual(result["browser_fallback_reason"], "short_body")
        self.http.assert_not_called()
        self.browser.assert_not_called()

    def test_existing_unfinished_dom_is_not_overwritten(self):
        target = self.raw / "article.md"
        target.write_text("以前の raw", encoding="utf-8")
        code, result = wiki_fetch.build(self.args)
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "existing_differs")
        self.assertEqual(target.read_text(encoding="utf-8"), "以前の raw")
        self.assertFalse((self.wiki / ".wiki-cache").exists())

    def test_saved_html_does_not_start_browser(self):
        html_file = self.root / "saved.html"
        html_file.write_bytes(SHORT)
        self.args.html_file = html_file
        self.args.page_url = FINAL
        _, result = wiki_fetch.build(self.args)
        self.assertEqual(result["fetch_method"], "html_file")
        self.http.assert_not_called()
        self.browser.assert_not_called()

    def test_short_dom_does_not_start_another_browser(self):
        self.browser.return_value = SHORT, URL, "text/html; charset=utf-8"
        _, result = wiki_fetch.build(self.args)
        self.browser.assert_called_once()
        self.assertLess(result["chars"], 500)
        self.assertEqual(result["source_sha256_of"], "dom")

    def test_youtube_is_rejected_before_any_fetch(self):
        self.args.url = "https://www.youtube.com/watch?v=abcdefghijk"
        with self.assertRaises(wiki_fetch.YouTubeRefused):
            wiki_fetch.build(self.args)
        self.http.assert_not_called()
        self.browser.assert_not_called()


class BrowserProtocolTest(unittest.TestCase):
    def test_existing_session_image_bytes_stay_in_memory(self):
        from tests.wiki.test_wiki_fetch import png
        payload = png(120, 80)
        result = {"html": "<main>本文</main>", "final_url": URL, "request_url": URL, "matched_url": URL,
                  "images": [{"url": "https://example.com/figure", "base64": base64.b64encode(payload).decode()}]}
        capture_images = {}
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=json.dumps(result), stderr="", returncode=0)):
            wiki_fetch.fetch_browser(URL, 5, 200000, False, capture_images=capture_images)
        self.assertEqual(capture_images["https://example.com/figure"], payload)

    def test_existing_session_wrong_url_is_rejected(self):
        result = {"html": "<main>別のページ</main>", "final_url": FINAL, "images": []}
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=json.dumps(result), stderr="", returncode=0)):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "URL が一致しない"):
                wiki_fetch.fetch_browser(URL, 5, 200000, False)
    def test_explicit_browser_reaches_child_as_separate_argument(self):
        output = json.dumps({"html": "<main>本文</main>", "final_url": URL, "request_url": URL, "matched_url": URL})
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=output, stderr="", returncode=0)) as run:
            wiki_fetch.fetch_browser(URL, 5, 200000, False, browser="chrome")
        command = run.call_args.args[0]
        self.assertEqual(command[-2:], ["--browser", "chrome"])

    def test_missing_uv_gives_manual_html_instructions(self):
        with mock.patch.object(wiki_fetch.shutil, "which", return_value=None):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "--html-file"):
                wiki_fetch.fetch_browser(URL, 5, 200000, True)

    def test_child_errors_and_invalid_protocol_do_not_return_content(self):
        for output, code in (("not json", 0), ('[]', 0), ('{"error":"HTTP 403"}', 2),
                             ('{"html":1,"final_url":"https://example.com"}', 0),
                             ('{"html":"abc","final_url":"file:///private"}', 0)):
            with self.subTest(output=output), mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                    mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                        stdout=output, stderr="", returncode=code)):
                with self.assertRaises(wiki_fetch.FetchError):
                    wiki_fetch.fetch_browser(URL, 5, 200000, False)

    def test_response_limit_is_on_utf8_bytes(self):
        output = json.dumps({"html": "日本語", "final_url": URL})
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=output, stderr="", returncode=0)):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "バイト"):
                wiki_fetch.fetch_browser(URL, 5, 8, False)

    def test_node_url_normalization_is_not_rejected_by_a_different_python_rule(self):
        requested, final = "https://EXAMPLE.com:443", "https://example.com/"
        output = json.dumps({"html": "<main>本文</main>", "final_url": final,
                             "request_url": requested, "matched_url": final, "images": []})
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=output, stderr="", returncode=0)):
            _, actual, _ = wiki_fetch.fetch_browser(requested, 5, 200000, False)
        self.assertEqual(actual, final)

    def test_protocol_debugging_environment_is_not_passed_to_browser_child(self):
        env = {"DEBUG": "pw:protocol", "DEBUG_FILE": "fixture.log", "PW_PROFILE_DIR": "fixture-profiles",
               "PWTEST_EXTENSION_USER_DATA_DIR": "fixture-profile", "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "fixture-token"}
        with mock.patch.dict(wiki_fetch.os.environ, env):
            actual = wiki_fetch.browser_environment()
        self.assertFalse(set(actual) & {"DEBUG", "DEBUG_FILE", "PW_PROFILE_DIR", "PWTEST_EXTENSION_USER_DATA_DIR"})
        self.assertEqual(actual["PLAYWRIGHT_MCP_EXTENSION_TOKEN"], "fixture-token")

    def test_youtube_redirect_from_child_keeps_the_youtube_exit_path(self):
        output = json.dumps({"error": "動画は別の経路で取る", "kind": "youtube",
                             "url": "https://youtu.be/abcdefghijk"})
        with mock.patch.object(wiki_fetch.shutil, "which", return_value="uv"), \
                mock.patch.object(wiki_fetch.subprocess, "run", return_value=argparse.Namespace(
                    stdout=output, stderr="", returncode=2)):
            with self.assertRaises(wiki_fetch.YouTubeRefused):
                wiki_fetch.fetch_browser(URL, 5, 200000, False)

    def test_private_and_youtube_destinations_are_rejected(self):
        with mock.patch.object(wiki_fetch, "is_private_host", return_value=True):
            with self.assertRaises(wiki_fetch.FetchError):
                wiki_fetch_browser.allowed_url("http://127.0.0.1/secret", True)
        with self.assertRaises(wiki_fetch.YouTubeRefused):
            wiki_fetch_browser.allowed_url("https://youtu.be/abcdefghijk", False, navigation=True)


class SystemBrowserTest(unittest.TestCase):
    def test_images_are_selected_from_article_and_duplicates_do_not_spend_budget(self):
        html = ('<html><body><nav><img src="/avatar.png" width="64" height="64"></nav>'
                '<article><h1>題名</h1><p>' + '本文。' * 200
                + '</p><img src="/figure.png" width="120" height="80">'
                '<img src="/figure.png" width="120" height="80"></article></body></html>')
        self.assertEqual(wiki_fetch_browser.select_image_urls(html, URL, 1), ['https://example.com/figure.png'])
        self.assertEqual(wiki_fetch_browser.select_image_urls(html, URL, 2), ['https://example.com/figure.png'])
    def test_actual_default_executable_is_used_even_outside_standard_channel_directory(self):
        for executable, channel in ((r"C:\Custom Browser\chrome.exe", "chrome"),
                                    (r"C:\Program Files (x86)\Microsoft\Edge Beta\Application\msedge.exe", "msedge")):
            with self.subTest(executable=executable), mock.patch.object(sys, "platform", "win32"), \
                    mock.patch.object(wiki_fetch_browser, "windows_default_executable", return_value=executable) as query, \
                    mock.patch.object(Path, "is_file", return_value=True):
                options = wiki_fetch_browser.browser_launch_options(URL)
            query.assert_called_once_with("https")
            self.assertEqual(options["executable_path"], executable)
            self.assertEqual(options["channel"], channel)

    def test_original_url_protocol_selects_default_browser(self):
        with mock.patch.object(sys, "platform", "win32"), \
                mock.patch.object(wiki_fetch_browser, "windows_default_executable", return_value=r"C:\Browser\chrome.exe") as query, \
                mock.patch.object(Path, "is_file", return_value=True):
            wiki_fetch_browser.browser_launch_options("http://example.com/page")
        query.assert_called_once_with("http")

    def test_explicit_browser_does_not_query_os_default(self):
        with mock.patch.object(wiki_fetch_browser, "windows_default_executable") as query:
            for channel in ("chrome", "msedge", "chromium"):
                self.assertEqual(wiki_fetch_browser.browser_launch_options(URL, channel),
                                 {"channel": channel, "headless": True})
        query.assert_not_called()

    def test_unsupported_default_does_not_switch_to_another_browser(self):
        with mock.patch.object(sys, "platform", "win32"), \
                mock.patch.object(wiki_fetch_browser, "windows_default_executable", return_value=r"C:\Firefox\firefox.exe"):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "対応していない"):
                wiki_fetch_browser.browser_launch_options(URL)

    def test_missing_or_relative_default_executable_is_rejected(self):
        for executable in ("chrome.exe", r"C:\Missing\msedge.exe"):
            with self.subTest(executable=executable), mock.patch.object(sys, "platform", "win32"), \
                    mock.patch.object(wiki_fetch_browser, "windows_default_executable", return_value=executable), \
                    mock.patch.object(Path, "is_file", return_value=False):
                with self.assertRaisesRegex(wiki_fetch.FetchError, "実行ファイルが見つからない"):
                    wiki_fetch_browser.browser_launch_options(URL)

    def test_other_operating_systems_report_detection_limit(self):
        with mock.patch.object(sys, "platform", "linux"):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "Windows に対応"):
                wiki_fetch_browser.browser_launch_options(URL)

    def test_windows_api_accepts_s_false_for_sizing_and_reads_unicode_path(self):
        import ctypes
        path = r"C:\利用者\ブラウザ\chrome.exe"

        def query(flags, field, scheme, verb, output, length):
            self.assertEqual((flags, field, scheme, verb), (0x1000, 2, "https", None))
            if output is None:
                length._obj.value = len(path) + 1
                return 1  # S_FALSE は必要な文字数を返す正常な応答。
            output.value = path
            return 0

        dll = mock.Mock()
        dll.AssocQueryStringW = mock.Mock(side_effect=query)
        with mock.patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            self.assertEqual(wiki_fetch_browser.windows_default_executable("https"), path)

    def test_windows_api_failure_returns_reason_instead_of_empty_path(self):
        import ctypes
        dll = mock.Mock()
        dll.AssocQueryStringW.return_value = -2147467259
        with mock.patch.object(ctypes, "WinDLL", return_value=dll, create=True):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "既定ブラウザを調べられない"):
                wiki_fetch_browser.windows_default_executable("https")


if __name__ == "__main__":
    unittest.main()
