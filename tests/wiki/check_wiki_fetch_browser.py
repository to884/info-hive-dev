# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = ["playwright==1.65.2"]
# ///
"""Chromium で遅延する本文と、多段リダイレクトの拒否を実際に確かめる。

uv run --script tests/wiki/check_wiki_fetch_browser.py
既定は Chromium を明示して検査する。WIKI_TEST_BROWSER=system なら Windows の既定ブラウザを検査する。
Chromium の初回は導入のためネットにつなぐ。取得先は試験用のローカルサーバーだけである。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_fetch
import wiki_fetch_browser

BODY = "遅れて描画された本文だけを原本として保存する。" * 45
BROWSER = os.environ.get("WIKI_TEST_BROWSER", "chromium")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.server.hits[self.path] += 1
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if self.path == "/cookie-start":
            self.send_response(302)
            self.send_header("Location", origin + "/cookie-app")
            self.send_header("Set-Cookie", "public_session=render; Path=/; HttpOnly")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/cookie-api":
            present = "public_session=render" in self.headers.get("Cookie", "")
            data = json.dumps({"html": '<p>' + BODY + '</p>' if present else ''}).encode("utf-8")
            self.send_response(200 if present else 403)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        redirects = {"/redirect-a": origin + "/redirect-b",
                     "/redirect-b": f"http://localhost:{self.server.server_port}/secret",
                     "/redirect-good": origin + "/posts/final",
                     "/script-a": origin + "/script-b",
                     "/script-b": f"http://localhost:{self.server.server_port}/secret"}
        if self.path in redirects:
            self.send_response(302)
            self.send_header("Location", redirects[self.path])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/cookie-app":
            body = '<article id="article">読み込み中</article><script>fetch("/cookie-api").then(r=>r.json()).then(d=>document.querySelector("#article").innerHTML=d.html)</script>'
        elif self.path == "/delayed":
            article = '<p>' + BODY + '</p><p><a href="reference">参照</a></p><img src="figure.png" alt="図"/>'
            body = '<article id="article">読み込み中</article><script>setTimeout(() => {document.querySelector("#article").innerHTML = ' + json.dumps(article) + ';}, 4000)</script>'
        elif self.path == "/subresource":
            body = '<article><p>' + BODY + '</p></article><script src="/script-a"></script>'
        elif self.path == "/jump":
            body = '<article><p>' + BODY + '</p></article><script>setTimeout(() => location.href = "http://localhost:' + str(self.server.server_port) + '/secret", 300)</script>'
        else:
            body = '<article><p>' + BODY + '</p><a href="reference">参照</a></article>'
        html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>遅延の試験</title></head><body>' + body + '</body></html>').encode("utf-8")
        self.send_response(403 if self.path == "/forbidden" else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)


class RealBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.hits = collections.Counter()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(5)

    def capture(self, path, *, block=False):
        return wiki_fetch_browser.capture_page(self.origin + path, 12, 200000, block, BROWSER, "isolated")

    def test_delayed_japanese_is_ingested_and_resumed_through_real_child_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wiki, raw = root / "wiki", root / "raw"
            wiki.mkdir()
            raw.mkdir()
            (wiki / "SCHEMA.md").write_text("# 規約\n", encoding="utf-8")
            args = argparse.Namespace(url=self.origin + "/delayed", wiki=wiki, raw_root=raw, slug="delayed",
                                      no_images=True, timeout=12, max_bytes=200000, max_images=0,
                                      force=False, browser_fallback=True, browser=BROWSER, browser_session="isolated")
            code, result = wiki_fetch.build(args)
            self.assertEqual(code, 0)
            self.assertEqual(result["fetch_method"], "playwright")
            text = (raw / "delayed.md").read_text(encoding="utf-8")
            self.assertIn(BODY, text)
            self.assertNotIn("読み込み中", text)
            self.assertIn(self.origin + "/reference", text)
            requests_before = self.server.hits.copy()
            _, resumed = wiki_fetch.build(args)
            self.assertTrue(resumed["fetch_skipped"])
            self.assertEqual(self.server.hits, requests_before)

    def test_browser_http_error_is_not_content(self):
        with self.assertRaisesRegex(wiki_fetch.FetchError, "HTTP 403"):
            self.capture("/forbidden")

    def test_original_redirect_sets_cookie_needed_by_public_javascript_api(self):
        captured = self.capture("/cookie-start")
        self.assertEqual(captured["final_url"], self.origin + "/cookie-app")
        self.assertIn(BODY, captured["html"])

    def test_valid_redirect_has_the_real_final_url(self):
        captured = self.capture("/redirect-good")
        self.assertEqual(captured["final_url"], self.origin + "/posts/final")
        self.assertEqual(captured["browser"], wiki_fetch_browser.browser_launch_options(self.origin, BROWSER)["channel"])

    def test_multihop_private_redirect_is_blocked_before_secret_request(self):
        before = self.server.hits["/secret"]
        with mock.patch.object(wiki_fetch, "is_private_host", side_effect=lambda host: host == "localhost"):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "内部のアドレス"):
                self.capture("/redirect-a", block=True)
        self.assertEqual(self.server.hits["/secret"], before)

    def test_subresource_redirect_is_not_delegated_to_chromium(self):
        before = self.server.hits["/script-b"]
        self.capture("/subresource")
        self.assertEqual(self.server.hits["/script-b"], before)

    def test_javascript_navigation_to_private_url_is_blocked(self):
        before = self.server.hits["/secret"]
        with mock.patch.object(wiki_fetch, "is_private_host", side_effect=lambda host: host == "localhost"):
            with self.assertRaisesRegex(wiki_fetch.FetchError, "内部のアドレス"):
                self.capture("/jump", block=True)
        self.assertEqual(self.server.hits["/secret"], before)


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
