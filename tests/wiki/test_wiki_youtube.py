"""YouTube の字幕の取り込み（wiki_youtube.py、wiki_captions.py、wiki_youtube_url.py）の試験。ADR-0027。

ネットにつながない。yt-dlp も読み込まない（Session を偽物に差し替える）。素材は、yt-dlp が返すメタデータの形と
json3 の形をまねて、ここで作る。実際の動画の -J の出力と json3 は使わない（字幕の URL に ip と署名が入るため）。

- URL の判定と、wiki_fetch.py が YouTube の URL を本文を読む前に拒むこと（渡された URL、--page-url、
  リダイレクトの先）。
- トラックの種類（tlang の有無、-orig のない元の字幕）、選び方、止まる動画、ID の照合。
- json3 から行へ（改行と制御文字、空の出来事、並び）、フェンスの長さ、字幕による行とフェンスの偽造、区間、
  時刻の形、字幕の URL が raw に入らないこと。
- inspect が何も書かないこと、write の排他と読み取り専用、同じ資料と別版と slug_taken、ハッシュの照合。
- 定義と印の読み書き、verify と lint の照合（ADR-0027 の (1)〜(5)）、confidence の計算、「raw にない語」。

実行（標準ライブラリと、プラグインに同梱の markdown-it-py だけで動く）:
    python -X utf8 -B -m unittest tests/wiki/test_wiki_youtube.py -v
"""
from __future__ import annotations

import http.server
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_captions as wc  # noqa: E402
import wiki_fetch  # noqa: E402
import wiki_lint  # noqa: E402
import wiki_youtube as wy  # noqa: E402
import wiki_youtube_url as wu  # noqa: E402

VID = "AbCdEfGhIj0"


def track_url(**params) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.youtube.com/api/timedtext?v={VID}&{query}&fmt=json3"


def fmts(url: str) -> list:
    return [{"ext": "srv1", "url": url.replace("json3", "srv1")}, {"ext": "json3", "url": url}]


def json3(*events) -> bytes:
    out = []
    for item in events:
        if isinstance(item, dict):
            out.append(item)
        else:
            start, text = item
            out.append({"tStartMs": start, "dDurationMs": 1000, "segs": [{"utf8": text}]})
    return json.dumps({"wireMagic": "pb3", "events": out}, ensure_ascii=False).encode("utf-8")


def info(**over) -> dict:
    base = {
        "id": VID, "title": "模擬講義 \"第 1 回\"", "channel": "講義のチャンネル", "upload_date": "20261101",
        "duration": 754, "language": "ja", "live_status": "not_live", "availability": "public",
        "subtitles": {},
        "automatic_captions": {
            "ja": fmts(track_url(kind="asr", lang="ja")),
            "ja-orig": fmts(track_url(kind="asr", lang="ja")),
            "en": fmts(track_url(kind="asr", lang="ja", tlang="en")),
        },
        "chapters": [],
    }
    base.update(over)
    return base


class FakeSession:
    """yt-dlp の代わり。取りに来た URL を記録する。"""

    def __init__(self, meta: dict, data: dict):
        self.meta = meta
        self.data = data
        self.requested = []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def info(self, url):
        self.requested.append(url)
        return self.meta

    def json3(self, track):
        self.requested.append(track.name)
        return self.data[track.name]

    def warnings(self):
        return ["No supported JavaScript runtime could be found"]


BASIC = json3((0, "こんにちは"), (1200, "今日は 15 人が来た"), (61000, "トヨタの話をする"),
              {"tStartMs": 61500, "segs": [{"utf8": "\n"}], "aAppend": 1}, (62000, "ＡＩ と 2 回 2 を言う"))


class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()  # macOS の /var -> /private/var は書き手の対象外の別名
        self.wiki = self.tmp / "wiki"
        self.raw = self.tmp / "raw"
        self.wiki.mkdir()
        self.raw.mkdir()
        (self.wiki / "SCHEMA.md").write_text("# スキーマ\n", encoding="utf-8")
        for name in ("sources", "entities", "concepts", "synthesis"):   # /wiki:init が作るディレクトリ
            (self.wiki / name).mkdir()

    def tearDown(self):
        for path in self.tmp.rglob("*"):
            try:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, *argv, session: FakeSession | None = None) -> tuple[int, dict]:
        buf = io.StringIO()
        patch = mock.patch.object(wy, "Session", session) if session else mock.patch.object(wy, "Session", wy.Session)
        with patch, redirect_stdout(buf), mock.patch.object(sys, "stderr", io.StringIO()):
            stdout = io.BytesIO()
            with mock.patch.object(sys, "stdout", io.TextIOWrapper(stdout, encoding="utf-8")):
                code = wy.main(list(argv))
                sys.stdout.flush()
                text = stdout.getvalue().decode("utf-8")
        return code, (json.loads(text) if text.strip().startswith("{") else {"_text": text})

    def write_page(self, rel: str, text: str) -> None:
        path = self.wiki / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


# ---------------------------------------------------------------- URL


class UrlTests(unittest.TestCase):
    def test_video_urls(self):
        for url in (f"https://www.youtube.com/watch?v={VID}", f"http://youtube.com/watch?v={VID}&t=30s",
                    f"https://m.youtube.com/watch?feature=share&v={VID}", f"https://www.youtube.com/shorts/{VID}",
                    f"https://www.youtube.com/live/{VID}?si=x", f"https://www.youtube.com/embed/{VID}",
                    f"https://youtu.be/{VID}?si=abc", f"HTTPS://WWW.YOUTUBE.COM/watch?v={VID}"):
            with self.subTest(url=url):
                found = wu.classify(url)
                self.assertEqual((found.kind, found.video_id), ("video", VID))
                self.assertEqual(found.canonical, f"https://www.youtube.com/watch?v={VID}")

    def test_list_is_noted(self):
        found = wu.classify(f"https://www.youtube.com/watch?v={VID}&list=PL123")
        self.assertEqual((found.kind, found.has_list), ("video", True))

    def test_not_video(self):
        for url in ("https://www.youtube.com/playlist?list=PL1", "https://www.youtube.com/@name",
                    "https://www.youtube.com/channel/UC1", "https://www.youtube.com/c/x", "https://www.youtube.com/user/x",
                    "https://www.youtube.com/results?search_query=x", "https://www.youtube.com/",
                    "https://www.youtube.com/watch?v=short", f"https://www.youtube.com/watch?v={VID}&v=BbCdEfGhIj0",
                    f"https://music.youtube.com/watch?v={VID}", "https://youtu.be/", f"https://youtu.be/{VID}/x",
                    f"https://user@www.youtube.com/watch?v={VID}", f"https://www.youtube.com/shorts/{VID}x"):
            with self.subTest(url=url):
                self.assertEqual(wu.classify(url).kind, "youtube_other")

    def test_host_as_the_network_sees_it(self):
        """判定は、通信の処理がつなぐホストで行う（実装のレビューの 1 回目の 2）。"""
        for url in (f"https://www%2eyoutube%2ecom/watch?v={VID}", f"https://ｗｗｗ.ｙｏｕｔｕｂｅ.ｃｏｍ/watch?v={VID}",
                    f"https://YOUTU.BE./{VID}", f"https://youtu%2ebe/{VID}"):
            with self.subTest(url=url):
                self.assertEqual(wu.classify(url).kind, "video")
                with self.assertRaises(wiki_fetch.YouTubeRefused):
                    wiki_fetch.refuse_youtube(url, "試験の URL ")
        wiki_fetch.refuse_youtube("https://example.com/youtube.com", "試験の URL ")

    def test_id_is_whole_string(self):
        """末尾の改行のある ID を受け入れない（レビューの 7 回目）。"""
        for url in (f"https://www.youtube.com/watch?v={VID}%0A", f"https://youtu.be/{VID}%0A"):
            with self.subTest(url=url):
                self.assertEqual(wu.classify(url).kind, "youtube_other")

    def test_other(self):
        for url in ("https://example.com/watch?v=" + VID, "ftp://youtube.com/watch?v=" + VID,
                    "https://notyoutube.com/watch?v=" + VID, "https://youtube.com.example.org/"):
            with self.subTest(url=url):
                self.assertEqual(wu.classify(url).kind, "other")


class FetchGuardTests(Workspace):
    def fetch_args(self, url, *extra):
        return [url, "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "記事", "--json", *extra]

    def test_youtube_url_is_refused_without_network(self):
        with mock.patch.object(wiki_fetch, "fetch", side_effect=AssertionError("取得した")):
            for url in (f"https://youtu.be/{VID}", "https://www.youtube.com/@x"):
                with self.subTest(url=url):
                    out = io.StringIO()
                    with redirect_stdout(out), mock.patch.object(sys, "stderr", io.StringIO()):
                        code = wiki_fetch.main(self.fetch_args(url))
                    self.assertEqual(code, 4)
                    self.assertEqual(json.loads(out.getvalue())["error"], "youtube")
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_page_url_is_refused(self):
        html = self.tmp / "page.html"
        html.write_text("<html><body><p>x</p></body></html>", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), mock.patch.object(sys, "stderr", io.StringIO()):
            code = wiki_fetch.main(self.fetch_args("https://example.com/", "--html-file", str(html),
                                                   "--page-url", f"https://www.youtube.com/watch?v={VID}"))
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(out.getvalue())["youtube"]["video_id"], VID)

    def test_redirect_to_youtube_is_refused_before_reading(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"https://youtu.be/{VID}")
                self.end_headers()

            def log_message(self, *a):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        opened = []
        real = wiki_fetch.urllib.request.OpenerDirector.open

        def spy(self, req, *a, **k):
            url = req if isinstance(req, str) else req.full_url
            opened.append(url)
            if "youtu" in url:
                raise AssertionError("YouTube に接続した")
            return real(self, req, *a, **k)

        try:
            with mock.patch.object(wiki_fetch.urllib.request.OpenerDirector, "open", spy):
                with self.assertRaises(wiki_fetch.YouTubeRefused):
                    wiki_fetch.fetch(f"http://127.0.0.1:{server.server_port}/x", 5, 1000,
                                     refuse_youtube_redirect=True)
            # 画像の取得（refuse_youtube_redirect なし）は、この拒みに関わらない。
            self.assertTrue(all("youtu" not in u for u in opened))
        finally:
            server.shutdown()
            server.server_close()

    def test_resume_with_youtube_final_url_is_refused(self):
        """前の版で、短縮 URL から YouTube へ転送されたページを途中まで取り込んだ（実装のレビューの 1 回目の 3）。"""
        (self.raw / "記事.md").write_text("---\nurl: \"https://example.com/s\"\n---\n本文\n", encoding="utf-8")
        saved = {"url": "https://example.com/s", "final_url": f"https://www.youtube.com/watch?v={VID}",
                 "source_sha256": "0" * 64}
        out = io.StringIO()
        with mock.patch.object(wiki_fetch.wiki_rawcheck, "resumable_fetch", return_value=saved), \
                mock.patch.object(wiki_fetch, "fetch", side_effect=AssertionError("取得した")), \
                redirect_stdout(out), mock.patch.object(sys, "stderr", io.StringIO()):
            code = wiki_fetch.main(self.fetch_args("https://example.com/s"))
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(out.getvalue())["error"], "youtube")

    def test_final_url_is_checked(self):
        def fake(url, *a, **k):
            return b"<html><body><p>x</p></body></html>", f"https://www.youtube.com/watch?v={VID}", "text/html"
        out = io.StringIO()
        with mock.patch.object(wiki_fetch, "fetch", fake), redirect_stdout(out), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            code = wiki_fetch.main(self.fetch_args("https://example.com/a"))
        self.assertEqual(code, 4)
        self.assertEqual(list(self.raw.iterdir()), [])


# ---------------------------------------------------------------- トラック


class TrackTests(unittest.TestCase):
    def test_kind_from_url_not_name(self):
        meta = info(subtitles={"en": fmts(track_url(lang="en")), "live_chat": [{"ext": "json", "url": "x"}]},
                    automatic_captions={
                        # -orig のない元の字幕（名前からは訳と見分けられない）。
                        "ja": fmts(track_url(kind="asr", lang="ja")),
                        "en-orig": fmts(track_url(kind="asr", lang="ja", tlang="en")),
                        "fr": [{"ext": "vtt", "url": track_url(kind="asr", lang="fr")}],
                    })
        tracks = wy.classify_tracks(meta)
        self.assertEqual([(t.name, t.kind, t.lang) for t in tracks], [("en", "uploaded", "en"), ("ja", "asr", "ja")])

    def test_same_lang_asr_merged_prefers_orig(self):
        tracks = wy.classify_tracks(info())
        self.assertEqual([(t.name, t.kind, t.lang, t.aliases) for t in tracks],
                         [("ja-orig", "asr", "ja", ("ja", "ja-orig"))])

    def test_select(self):
        up = lambda name: wy.Track(name, "uploaded", name, "u", (name,))  # noqa: E731
        asr = lambda lang: wy.Track(f"{lang}-orig", "asr", lang, "a", (lang, f"{lang}-orig"))  # noqa: E731
        cases = [
            ([up("en"), up("ja"), asr("en")], None, None, "en"),
            ([up("en-US"), up("en-GB"), up("en"), asr("en")], None, None, "en"),
            ([up("en-US"), asr("en")], None, None, "en-US"),
            ([up("en-US"), up("en-GB"), asr("en")], None, None, None),
            ([up("de"), asr("ja")], None, None, "ja-orig"),
            ([up("ja-JP")], "ja", None, "ja-JP"),
            ([up("de")], "ja", None, None),
            ([asr("ja"), asr("en")], None, None, None),
            ([asr("ja"), asr("en")], None, "en", "en-orig"),
            ([up("en")], None, None, None),
            ([], "ja", None, None),
            ([up("en"), asr("en")], None, "en-orig", "en-orig"),
            ([up("en"), asr("en")], None, "fr", None),
            # 投稿者の字幕の名前が、自動字幕の別名と同じでも、名前で選べる（レビューの 6 回目）。
            ([up("ja"), asr("ja"), asr("en")], None, "ja", "ja"),
            ([up("ja"), asr("ja"), asr("en")], None, "ja-orig", "ja-orig"),
            ([asr("ja"), asr("en")], None, "ja", "ja-orig"),
        ]
        # -orig のない自動字幕は、名前が投稿者の字幕と同じになる。種類を前に付けた ID で選ぶ（レビューの 7 回目）。
        plain = wy.Track("ja", "asr", "ja", "a", ("ja",))
        for requested, want in (("uploaded:ja", "uploaded"), ("asr:ja", "asr"), ("ja", None)):
            with self.subTest(requested=requested):
                got, _l, _r = wy.select_track([up("ja"), plain, asr("en")], None, requested)
                self.assertEqual(got.kind if got else None, want)
        for tracks, lang, requested, want in cases:
            with self.subTest(tracks=[t.name for t in tracks], lang=lang, requested=requested):
                got, _l, reason = wy.select_track(tracks, lang, requested)
                self.assertEqual(got.name if got else None, want, reason)
                if want is None:
                    self.assertTrue(reason)

    def test_stop_conditions(self):
        wy.check_video(info(live_status="was_live", availability="unlisted"), VID)
        for over in ({"id": "zzzzzzzzzzz"}, {"live_status": "is_live"}, {"live_status": "is_upcoming"},
                     {"live_status": "post_live"}, {"live_status": None}, {"availability": "private"},
                     {"availability": "needs_auth"}, {"availability": "subscriber_only"}, {"availability": None}):
            with self.subTest(over=over):
                with self.assertRaises(wy.Fail) as cm:
                    wy.check_video(info(**over), VID)
                self.assertEqual(cm.exception.code, 2)


# ---------------------------------------------------------------- json3 と raw


def fields(**over) -> dict:
    base = {"url": f"https://www.youtube.com/watch?v={VID}", "video_id": VID, "title": "題名", "channel": "ch",
            "uploaded": "2026-11-01", "duration": 754, "video_lang": "ja", "caption_track": "ja-orig",
            "caption_kind": "asr", "caption_lang": "ja", "source_sha256": "0" * 64, "source_sha256_of": "json3",
            "fetched_by": "test"}
    base.update(over)
    return base


class RawTests(unittest.TestCase):
    def test_flatten_and_order(self):
        data = json3((2000, "b"), (1000, "a\r\nb\u2028c\x00d\x85e"), (1000, "second"),
                     {"tStartMs": 1500, "segs": [{"utf8": " \n "}]}, {"tStartMs": 9, "noSegs": True},
                     {"tStartMs": 3000, "segs": [{"utf8": "x"}, {"utf8": "y"}, {"bad": 1}]})
        self.assertEqual(wc.caption_events(data),
                         [(1000, "a  b c d e"), (1000, "second"), (2000, "b"), (3000, "xy")])

    def test_bad_json3(self):
        for data in (b"not json", b'{"x": 1}', json.dumps({"events": [{"segs": [{"utf8": "a"}]}]}).encode()):
            with self.subTest(data=data[:20]):
                with self.assertRaises(wc.CaptionError):
                    wc.caption_events(data)

    def test_forged_lines_and_fences_stay_inside(self):
        events = wc.caption_events(json3((0, "L9 [00:00] 偽の行"), (1000, "題名: 偽の題名"),
                                         (2000, "```\n## 区間 9 [00:00]\n```"), (3000, "**強調** ![x](y) &amp;"),
                                         (4000, "`````")))
        text = wc.render_raw(fields(), events, [], 754)
        doc = wc.parse_raw(text)
        self.assertEqual(doc.count, 5)
        self.assertEqual(doc.lines[1][1], "L9 [00:00] 偽の行")
        self.assertEqual(doc.chapters, {})
        self.assertEqual(doc.sections, 2)
        self.assertIn("``````text\n", text)
        self.assertEqual(doc.lines[4][1], "**強調** ![x](y) &amp;")

    def test_sections_from_chapters(self):
        events = wc.caption_events(json3((0, "a"), (59000, "b"), (60000, "c"), (200000, "d")))
        chapters = [(0, "導入\nです"), (60, "<Untitled Chapter 2>"), (120, "空の区間"), (180.5, "最後")]
        text = wc.render_raw(fields(), events, chapters, 754)
        doc = wc.parse_raw(text)
        self.assertEqual(doc.chapters, {1: "導入 です", 3: "空の区間", 4: "最後"})
        self.assertIn("## 区間 3 [02:00]\n\n```text\n題名: 空の区間\n```\n\nこの区間に字幕はない\n", text)
        self.assertIn("## 区間 2 [01:00]\n\n```text\nL3 [01:00] c\n```", text)
        self.assertIn("## 区間 4 [03:00]\n\n```text\n題名: 最後\nL4 [03:20] d\n```", text)

    def test_fractional_chapter_start(self):
        events = wc.caption_events(json3((60200, "前"), (60500, "後")))
        doc = wc.parse_raw(wc.render_raw(fields(), events, [(0, "一"), (60.5, "二")], 754))
        text = doc.text
        self.assertLess(text.index("L1 [01:00] 前"), text.index("## 区間 2 [01:00]"))
        self.assertGreater(text.index("L2 [01:00] 後"), text.index("## 区間 2 [01:00]"))

    def test_parse_raw_accepts_only_the_written_form(self):
        events = wc.caption_events(json3((0, "a")))
        text = wc.render_raw(fields(), events, [], 10)
        wc.parse_raw(text)
        for extra in ("\n## 足した見出し\n\n本文\n", "\n- 箇条書き\n", "\n" + wc.NO_CAPTION + "\n"):
            with self.subTest(extra=extra):
                with self.assertRaises(wc.CaptionError):
                    wc.parse_raw(text.replace(f"# YouTube の字幕 {VID}\n", f"# YouTube の字幕 {VID}\n" + extra, 1))
        # 区間の中の組み合わせも、生成器が書く形だけにする（レビューの 2 回目）。
        for tail in ("\n" + wc.NO_CAPTION + "\n", "\n```text\n題名: FAKE\n```\n", "\n```text\nL2 [00:00] b\n```\n"):
            with self.subTest(tail=tail):
                with self.assertRaises(wc.CaptionError):
                    wc.parse_raw(text + tail)

    def test_ten_minute_sections_and_long_time(self):
        events = wc.caption_events(json3((0, "a"), (1300000, "b"), (3700000, "c")))
        text = wc.render_raw(fields(duration=3720), events, [], 3720)
        self.assertIn("## 区間 3 [0:20:00]", text)
        self.assertIn("L2 [0:21:40] b", text)
        self.assertIn("L3 [1:01:40] c", text)
        self.assertIn("## 区間 2 [0:10:00]\n\nこの区間に字幕はない\n", text)
        self.assertEqual(wc.parse_raw(text).sections, 7)

    def test_frontmatter_escaping(self):
        events = wc.caption_events(json3((0, "a")))
        text = wc.render_raw(fields(title='a "b" \\ c', channel="x: y # z"), events, [], 10)
        doc = wc.parse_raw(text)
        self.assertEqual((doc.meta["title"], doc.meta["channel"]), ('a "b" \\ c', "x: y # z"))
        self.assertTrue(text.split("\n---\n", 1)[1].startswith(f"\n# YouTube の字幕 {VID}\n"))


# ---------------------------------------------------------------- inspect と write


class InspectWriteTests(Workspace):
    URL = f"https://youtu.be/{VID}?list=PL1"

    def session(self, data=BASIC, meta=None):
        return FakeSession(meta or info(), {"ja-orig": data})

    def inspect(self, *extra, session=None):
        return self.run_main("inspect", "--url", self.URL, "--wiki", str(self.wiki), "--raw-root", str(self.raw),
                             "--json", *extra, session=session or self.session())

    def write(self, slug, sha, *extra, session=None):
        return self.run_main("write", "--url", self.URL, "--wiki", str(self.wiki), "--raw-root", str(self.raw),
                             "--slug", slug, "--expect-sha256", sha, "--json", *extra,
                             session=session or self.session())

    def test_inspect_writes_nothing_and_hides_urls(self):
        before = sorted(p.as_posix() for p in self.tmp.rglob("*"))
        session = self.session()
        code, out = self.inspect("--slug", "動画", session=session)
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(p.as_posix() for p in self.tmp.rglob("*")), before)
        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["track"]["name"], "ja-orig")
        self.assertEqual(out["lines"], 4)
        self.assertEqual(out["slug_state"], "free")
        self.assertIn("list=", out["notes"][0])
        self.assertEqual(session.requested[0], f"https://www.youtube.com/watch?v={VID}")
        self.assertNotIn("timedtext", json.dumps(out))

    def test_track_undecided(self):
        meta = info(automatic_captions={"ja": fmts(track_url(kind="asr", lang="ja")),
                                        "en": fmts(track_url(kind="asr", lang="en"))})
        code, out = self.inspect(session=FakeSession(meta, {}))
        self.assertEqual((code, out["status"], out["source_sha256"]), (3, "track_undecided", None))
        self.assertTrue(out["reason"])

    def test_stops(self):
        code, out = self.inspect(session=FakeSession(info(id="zzzzzzzzzzz"), {}))
        self.assertEqual(code, 2)
        code, _out = self.run_main("inspect", "--url", "https://www.youtube.com/@x", "--wiki", str(self.wiki),
                                   "--raw-root", str(self.raw), "--json", session=self.session())
        self.assertEqual(code, 1)
        code, out = self.inspect(session=self.session(data=json3({"tStartMs": 0, "segs": [{"utf8": "\n"}]})))
        self.assertEqual(code, 2)
        # 字幕のない動画は、空のトラックの一覧から選ばせず、止まる（実装のレビューの 1 回目）。
        code, out = self.inspect(session=FakeSession(info(subtitles={}, automatic_captions={}), {}))
        self.assertEqual((code, out["status"]), (2, "error"))
        self.assertIn("字幕がない", out["message"])

    def test_write_flow(self):
        code, out = self.inspect("--slug", "動画")
        sha = out["source_sha256"]
        code, out = self.write("動画", "f" * 64)
        self.assertEqual((code, out["status"]), (3, "changed"))
        self.assertEqual(list(self.raw.iterdir()), [])
        code, out = self.write("動画", sha)
        self.assertEqual((code, out["status"]), (0, "created"), out)
        # 字幕を取った時刻を返す。要約ページの fetched_at に写す（0.23.2）。
        from datetime import datetime
        self.assertIsNotNone(datetime.fromisoformat(out["fetched_at"]).utcoffset())
        path = self.raw / "動画.md"
        self.assertTrue(out["read_only"])
        self.assertFalse(os.stat(path).st_mode & 0o222)
        self.assertEqual(out["raw_ref"], "raw/動画.md")
        text = path.read_text(encoding="utf-8")
        for bad in ("timedtext", "signature", "ip=", "expire"):
            self.assertNotIn(bad, text)
        doc = wc.parse_raw(text)
        self.assertEqual((doc.video_id, doc.caption_kind, doc.meta["source_sha256"]), (VID, "asr", sha))
        # 同じ資料は、スラッグによらず same。書き込みできる状態になっていれば、読み取り専用に戻す（#74 のレビュー）。
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        code, out = self.write("別の名前", sha)
        self.assertEqual((code, out["status"], out["raw_ref"]), (0, "same", "raw/動画.md"))
        self.assertTrue(out["read_only"])
        self.assertFalse(os.stat(path).st_mode & 0o222)
        self.assertFalse((self.raw / "別の名前.md").exists())
        # 字幕が変わったら different。--new-version で別版を書く。
        changed = json3((0, "こんにちは"), (1200, "今日は 50 人が来た"))
        sha2 = self.inspect(session=self.session(data=changed))[1]["source_sha256"]
        code, out = self.write("動画-20261116", sha2, session=self.session(data=changed))
        self.assertEqual((code, out["status"]), (3, "different"))
        code, out = self.write("動画", sha2, "--new-version", session=self.session(data=changed))
        self.assertEqual((code, out["status"], out["slug_state"]), (3, "different", "different"))
        code, out = self.write("動画-20261116", sha2, "--new-version", session=self.session(data=changed))
        self.assertEqual((code, out["status"]), (0, "created"))
        code, out = self.inspect("--slug", "動画", session=self.session(data=changed))
        self.assertEqual(sorted(x["state"] for x in out["existing"]), ["different", "same"])

    def test_upper_case_extension_is_found(self):
        """拡張子が .MD の raw も、同じ資料として見つける（レビューの 6 回目）。"""
        sha = self.inspect()[1]["source_sha256"]
        self.assertEqual(self.write("動画", sha)[1]["status"], "created")
        path = self.raw / "動画.md"
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        os.rename(path, self.raw / "tmp.MD")
        os.rename(self.raw / "tmp.MD", self.raw / "動画.MD")
        code, out = self.write("別の名前", sha)
        self.assertEqual((code, out["status"]), (0, "same"))

    def test_slug_taken(self):
        (self.raw / "記事.md").write_text("---\ntitle: \"記事\"\n---\n本文\n", encoding="utf-8")
        (self.raw / "壊れ.md").write_bytes(b"\xff\xfe")
        self.write_page("sources/要約だけ.md", "---\ntype: \"source\"\n---\n")
        code, out = self.inspect("--slug", "記事")
        self.assertEqual(out["slug_state"], "slug_taken")
        self.assertIn("壊れ.md", out["unreadable"])
        sha = out["source_sha256"]
        for slug in ("記事", "要約だけ"):
            with self.subTest(slug=slug):
                code, out = self.write(slug, sha)
                self.assertEqual((code, out["status"]), (3, "slug_taken"))
        self.assertEqual((self.raw / "記事.md").read_text(encoding="utf-8"), "---\ntitle: \"記事\"\n---\n本文\n")

    def test_uploaded_track(self):
        meta = info(subtitles={"ja": fmts(track_url(lang="ja"))})
        session = FakeSession(meta, {"ja": json3((0, "投稿者の字幕"))})
        code, out = self.inspect(session=session)
        self.assertEqual((out["track"]["name"], out["track"]["kind"]), ("ja", "uploaded"))

    def test_define(self):
        out = io.BytesIO()
        wrapper = io.TextIOWrapper(out, encoding="utf-8")
        with mock.patch.object(sys, "stdout", wrapper):
            code = wy.main(["define", "--id", "L2-1", "--caption", "15", "--corrected", "`50 ", "--basis", "model:常識"])
            wrapper.flush()
            value = out.getvalue().decode("utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(value, "- L2-1: 字幕 `15` を `` `50  `` に訂正（根拠 model:常識）\n")
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(wy.main(["define", "--id", "L2", "--caption", "x"]), 1)
            self.assertEqual(wy.main(["define", "--id", "L2-1", "--caption", "x", "--corrected", "y"]), 1)


# ---------------------------------------------------------------- 定義と印


class DefinitionTests(unittest.TestCase):
    def test_roundtrip(self):
        for caption, nth, corrected, basis in (("15", None, "50", "caption:L3"), ("`a``b", 2, " x ", "model:理由 （注）"),
                                               ("a b", None, None, None), ("|縦棒|", 3, "x", "wiki_source:記事 2"),
                                               ("x", None, "y", "metadata:chapter:2")):
            with self.subTest(caption=caption):
                line = wc.format_definition("L5-1", caption, nth, corrected, basis)
                d = wc.parse_definition(line)
                self.assertIsInstance(d, wc.Definition, line)
                self.assertEqual((d.caption, d.nth, d.corrected, d.basis), (caption, nth, corrected, basis))

    def test_bad(self):
        for line in ("- L5-1: 字幕 `15` を `15` に訂正（根拠 model:x）", "- L5-1: 字幕 `15` を `50` に訂正（根拠 web:x）",
                     "- L5-1: 字幕 `15` を `50` に訂正", "- L5: 字幕 `15` は留保", "- L5-1: 字幕 15 は留保",
                     "- L5-1: 字幕 `15` は留保。", "- L0-1: 字幕 `15` は留保", "- L5-1: 字幕 `15` を `50` に訂正（根拠 model:）"):
            with self.subTest(line=line):
                self.assertIsInstance(wc.parse_definition(line), str)

    def test_tail(self):
        cases = [
            ("今日は 50", "50", None), ("今日は150", "50", "途中"), ("今日は１50", "50", "途中"),
            ("値は x*y", "x*y", None), ("ABC", "BC", "途中"), ("ﾄヨタ", "ヨタ", "途中"),
            ("ーヨタ", "ヨタ", "途中"), ("東京都", "京都", None), ("x [[50]]", "50", "末尾"), ("café", "fé", "途中"),
            ("", "50", "末尾"),
            # 結合文字で語の途中の切れ目を隠さない（レビューの 6 回目）。
            ("ト\u3099ヨタ", "ヨタ", "途中"), ("A\u0301BC", "BC", "途中"),
            # 半角の濁点（レビューの 7 回目）。NFKC にそろえて照らす。
            ("ﾄﾞヨタ", "ヨタ", "途中"), ("ｶﾞﾗｽ", "ﾗｽ", "途中"), ("ﾄﾞ", "ﾞ", "結合"),
            # 目に見えない文字（レビューの 8 回目）。種類で拒む。
            ("ト\u2060ヨタ", "ヨタ", "誤り"), ("ト\u200dヨタ", "ヨタ", "誤り"),
            ("1\u00ad5", "5", "誤り"), ("ト\ufe0fヨタ", "ヨタ", "誤り"), ("ト\ue000ヨタ", "ヨタ", "誤り"),
            # 目に見えない文字を語の先頭に入れても、取り除いた前の文字で分かる（レビューの 9 回目）。
            ("ト\u2060ヨタ", "\u2060ヨタ", "誤り"),
            # 段落の中の改行は、閲覧と同じく空白（レビューの 9 回目）。
            ("説明は\n50", "50", None),
            # 補助面のカタカナ（レビューの 10 回目）。文字の名前の文字体系で決める。
            ("\U0001b155ヨタ", "ヨタ", "途中"), ("\U0001b000ヨタ", "ヨタ", "途中"),
            ("αβγ", "βγ", "途中"), ("Жук", "ук", "途中"), ("①5", "5", "途中"), ("ｶﾀカナ", "カナ", "途中"),
            ("東京都", "京都", None), ("ひらがな", "がな", None),
        ]
        for prefix, word, want in cases:
            with self.subTest(prefix=prefix, word=word):
                got = wc.tail_problem(prefix, word)
                if want is None:
                    self.assertIsNone(got)
                elif want == "途中":
                    self.assertIn("途中", got)
                elif want == "結合":
                    self.assertIn("結合", got)
                elif want == "誤り":
                    self.assertIsNotNone(got)
                else:
                    self.assertIn("末尾", got)


class VerifyTests(Workspace):
    def setUp(self):
        super().setUp()
        events = wc.caption_events(json3((0, "こんにちは"), (1200, "今日は 15 人が来た 15"), (61000, "トヨタの話をする"),
                                         (62000, "AI の話")))
        self.raw_text = wc.render_raw(fields(title="トヨダの講義", caption_kind="asr"), events,
                                      [(0, "はじめに"), (60, "トヨダの歴史")], 754)
        (self.raw / "動画.md").write_text(self.raw_text, encoding="utf-8", newline="")
        (self.raw / "記事.md").write_text("---\ntitle: \"記事\"\n---\nトヨダ自動織機\n", encoding="utf-8")
        self.write_page("sources/記事.md", self.page("記事", "本文", raw="raw/記事.md", kind=None, confidence=None))

    @staticmethod
    def page(title, body, raw="raw/動画.md", kind="asr", confidence="medium", type_="source", defs=""):
        fm = [f"type: \"{type_}\"", f"title: \"{title}\"", "tags: [\"x\"]", "created: 2026-11-16", "updated: 2026-11-16"]
        if raw:
            fm.append(f"raw: \"{raw}\"")
        if kind:
            fm.append(f"caption_kind: \"{kind}\"")
        if confidence:
            fm.append(f"confidence: \"{confidence}\"")
        text = "---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n"
        if defs:
            text += f"\n## 字幕の訂正と留保\n\n{defs}\n"
        return text

    def check(self, overlay=None):
        return wc.check_wiki(self.wiki, overlay or {}, only_raw="raw/動画.md", unknown_for=set(overlay or {}))

    def codes(self, overlay):
        return sorted(f.code for f in self.check(overlay).findings)

    def test_valid(self):
        summary = self.page("動画", "講義では 50〔訂正 L2-1〕 人が来た。トヨダ〔訂正 L3-1〕の話で、AI〔留保 L4-1〕も出た。"
                            "トヨダは 50 人。", confidence="low",
                            defs="- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:文脈）\n"
                                 "- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 metadata:title）\n"
                                 "- L4-1: 字幕 `AI` は留保")
        related = self.page("トヨダ", "トヨダ〔訂正 [[動画]] L3-1〕は会社。", raw=None, kind=None, confidence=None,
                            type_="entity")
        overlay = {"sources/動画.md": summary, "entities/トヨダ.md": related}
        result = self.check(overlay)
        self.assertEqual([f.as_dict() for f in result.findings], [])
        raw = result.raws[0]
        # 重みは model 3 + metadata 1 + 留保 3 = 7、行は 4 なので 175（3 以上）で low。
        self.assertEqual((raw.confidence, raw.weight, raw.parent), ("low", 7, "sources/動画.md"))
        self.assertEqual(result.unknown_words, {})

    def test_codes(self):
        base = "今日は 50〔訂正 L2-1〕 人。"
        defs = "- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 caption:L1）"
        cases = {
            # (1) 字幕の語の位置
            "bad_definition:pos": (base, "- L2-1: 字幕 `15` を `50` に訂正（根拠 model:x）", None),
            "bad_definition:line": ("x 50〔訂正 L9-1〕", "- L9-1: 字幕 `15` を `50` に訂正（根拠 model:x）", None),
            "bad_definition:word": ("x 50〔訂正 L2-1〕", "- L2-1: 字幕 `16` を `50` に訂正（根拠 model:x）", None),
            "bad_definition:nth": ("x 50〔訂正 L2-1〕", "- L2-1: 字幕 `15`（3 つ目） を `50` に訂正（根拠 model:x）", None),
            # (2) 根拠の場所
            "bad_definition:caption": (base, defs, None),
            "bad_definition:same_line": ("x 来た〔訂正 L2-1〕", "- L2-1: 字幕 `人が来た` を `来た` に訂正（根拠 caption:L2）", None),
            "bad_definition:title": ("x 講義〔訂正 L1-1〕", "- L1-1: 字幕 `こんにちは` を `講義` に訂正（根拠 metadata:channel）", None),
            "bad_definition:chapter": ("x トヨダ〔訂正 L3-1〕", "- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 metadata:chapter:1）", None),
            "bad_definition:wiki_source": ("x トヨダ〔訂正 L3-1〕", "- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 wiki_source:ない）", None),
            # (4) 印と定義
            "undefined_mark": ("x 50〔訂正 L2-2〕", defs.replace("caption:L1", "model:x"), None),
            "mark_kind_mismatch": ("x 50〔留保 L2-1〕", defs.replace("caption:L1", "model:x"), None),
            "mark_tail": ("x 150〔訂正 L2-1〕", defs.replace("caption:L1", "model:x"), None),
            "link_in_summary_mark": ("x 50〔訂正 [[動画]] L2-1〕 50〔訂正 L2-1〕", defs.replace("caption:L1", "model:x"), None),
            "mark_in_quote": ("x 50〔訂正 L2-1〕\n\n> 50〔訂正 L2-1〕", defs.replace("caption:L1", "model:x"), None),
            "bad_mark": ("x 50〔訂正 L2〕 50〔訂正 L2-1〕", defs.replace("caption:L1", "model:x"), None),
            "unused_definition": ("x", defs.replace("caption:L1", "model:x"), None),
            # (5) confidence
            "confidence_mismatch": ("x 50〔訂正 L2-1〕", defs.replace("caption:L1", "model:x"), "medium"),
            "missing_confidence": ("x", "", ""),
        }
        for name, (body, d, conf) in cases.items():
            code = name.split(":")[0]
            with self.subTest(case=name):
                overlay = {"sources/動画.md": self.page("動画", body, confidence=("low" if conf is None else conf) or None,
                                                         defs=d)}
                self.assertIn(code, self.codes(overlay), name)

    def test_parser_decides_marks(self):
        """印は、表示と同じパーサーが本文の文字としたところから読む（実装のレビューの 1 回目の 1）。"""
        defs = "- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:x）"
        cases = {
            # バックスラッシュ 2 つのあとのバッククォートはコードの始まり。印は本文にあるので、定義がなければ誤り。
            "\\\\`x` 50〔訂正 L1-1〕 `z`": "undefined_mark",
            # 文字参照で書いた印も印である。
            "x 50&#x3014;訂正 L1-1〕": "undefined_mark",
            # 文字参照の 1 は、表示では 15 になる。
            "x &#49;50〔訂正 L2-1〕": "mark_tail",
            # 書式とリンクの直後の印は、末尾が語にならない。
            "x **50**〔訂正 L2-1〕": "mark_tail",
            "x [50](https://example.com/)〔訂正 L2-1〕": "mark_tail",
            "x `50`〔訂正 L2-1〕": "mark_tail",
        }
        for body, code in cases.items():
            with self.subTest(body=body):
                overlay = {"sources/動画.md": self.page("動画", body, confidence="low", defs=defs)}
                self.assertIn(code, self.codes(overlay))
        # 表示では書式の前の文字も語の前の文字である。書式の入った印は、形の誤りとして挙がる（レビューの 2 回目）。
        five = "- L2-1: 字幕 `15`（1 つ目） を `5` に訂正（根拠 model:x）"
        for body, code in {"x **1**5〔訂正 L2-1〕": "mark_tail", "x [1](https://example.com/)5〔訂正 L2-1〕": "mark_tail",
                           "x `1`5〔訂正 L2-1〕": "mark_tail", "x 50〔**訂正** L2-1〕": "bad_mark",
                           "x 50〔訂**正** L2-1〕": "bad_mark", "x 50〔訂正 `L2-1`〕": "bad_mark",
                           # wikilink は表示名で照らす（レビューの 3 回目）。
                           "x [[1]]5〔訂正 L2-1〕": "mark_tail", "x [[c|1]]5〔訂正 L2-1〕": "mark_tail",
                           "x 50〔[[訂正]] L2-1〕": "bad_mark", "x 50〔訂[[正]] L2-1〕": "bad_mark",
                           # 表示に見える壊れた印は、隠れた正しい形の印と相殺しない（レビューの 4 回目）。
                           "15〔[[留保]] L2-2〕 [[50〔訂正 L2-1〕|本文]]": "bad_mark",
                           "x 1![](missing.png)5〔訂正 L2-1〕": "mark_tail",
                           # 始まりだけをコードにした印は、例でなく形の誤り（レビューの 5 回目）。
                           "x 50`〔訂正` L2-1〕": "bad_mark", "x 15`〔留保` L2-1〕": "bad_mark",
                           "x 50`〔訂正 L999-9`〕": "bad_mark"}.items():
            with self.subTest(body=body):
                overlay = {"sources/動画.md": self.page("動画", body, confidence="low", defs=five)}
                self.assertIn(code, self.codes(overlay))
        # 全体がコードスパンの中の印は、例として数えない。
        example = self.page("動画", "書き方の例は `〔訂正 L1-1〕` である", confidence="medium")
        self.assertEqual(self.codes({"sources/動画.md": example}), [])
        # エスケープを外すと語になるなら、通る。
        ok = self.page("動画", "値は x\\*y〔訂正 L2-1〕", confidence="low",
                       defs="- L2-1: 字幕 `15`（1 つ目） を `x*y` に訂正（根拠 model:x）")
        self.assertEqual(self.codes({"sources/動画.md": ok}), [])

    def test_mark_in_code_is_ignored(self):
        body = "`50〔訂正 L2-1〕` と\n\n```\n50〔訂正 L9-9〕\n```"
        self.assertEqual(self.codes({"sources/動画.md": self.page("動画", body)}), [])

    def test_conflict_and_same_position(self):
        d1 = "- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 metadata:title）"
        child_defs = "- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 metadata:chapter:2）\n- L3-2: 字幕 `トヨタ` は留保"
        overlay = {
            "sources/動画.md": self.page("動画", "トヨダ〔訂正 L3-1〕", confidence="low", defs=d1),
            "sources/動画-2.md": self.page("動画 2", "トヨダ〔訂正 L3-1〕と トヨタ〔留保 L3-2〕", confidence=None,
                                           defs=child_defs),
        }
        codes = self.codes(overlay)
        self.assertIn("conflicting_definition", codes)
        self.assertIn("same_position", codes)

    def test_related_pages(self):
        summary = self.page("動画", "トヨダ〔訂正 L3-1〕", confidence="low",
                            defs="- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 wiki_source:記事）")
        cases = {
            "mark_without_summary": "トヨダ〔訂正 L3-1〕",
            "bad_mark_summary": "トヨダ〔訂正 [[記事]] L3-1〕",
            "undefined_mark": "トヨダ〔訂正 [[動画]] L3-9〕",
            "mark_tail": "トヨタ〔訂正 [[動画]] L3-1〕",
        }
        self.assertEqual(self.codes({"sources/動画.md": summary}), [])
        for code, body in cases.items():
            with self.subTest(code=code):
                overlay = {"sources/動画.md": summary,
                           "concepts/c.md": self.page("c", body, raw=None, kind=None, confidence=None, type_="concept")}
                self.assertIn(code, self.codes(overlay))
        defs_elsewhere = self.page("c", "x", raw=None, kind=None, confidence=None, type_="concept",
                                   defs="- L3-1: 字幕 `トヨタ` は留保")
        self.assertIn("definition_outside_summary", self.codes({"sources/動画.md": summary, "concepts/c.md": defs_elsewhere}))

    def test_confidence_rules(self):
        def calc(kind, defs, count):
            parsed = [wc.parse_definition(d) for d in defs]
            return wc.compute_confidence(kind, parsed, count)[0]
        light = "- L1-1: 字幕 `a` を `b` に訂正（根拠 caption:L2）"
        heavy = "- L1-2: 字幕 `a` を `b` に訂正（根拠 model:x）"
        hedge = "- L1-3: 字幕 `a` は留保"
        self.assertEqual(calc("uploaded", [], 100), "high")
        self.assertEqual(calc("asr", [], 100), "medium")
        self.assertEqual(calc("uploaded", [light, light.replace("L1-1", "L2-1")], 100), "high")
        self.assertEqual(calc("uploaded", [heavy], 1000), "medium")
        self.assertEqual(calc("uploaded", [hedge], 1000), "medium")
        self.assertEqual(calc("uploaded", [light, light.replace("L1-1", "L2-1"), light.replace("L1-1", "L3-1")], 100), "low")
        self.assertEqual(calc("asr", [heavy], 100), "low")
        self.assertEqual(calc("asr", [light, light.replace("L1-1", "L2-1")], 100), "medium")
        self.assertIsNone(calc("auto", [], 100))

    def test_no_parent_and_child_confidence(self):
        overlay = {"sources/動画-2.md": self.page("動画 2", "x", confidence="medium")}
        codes = self.codes(overlay)
        self.assertIn("no_parent_summary", codes)
        overlay["sources/動画.md"] = self.page("動画", "x", confidence="medium")
        self.assertIn("confidence_on_child", self.codes(overlay))

    def test_several_video_raws_and_unreadable_pages(self):
        """照らせない形を黙って除かない（レビューの 2 回目の 3 と 4）。"""
        other = self.raw_text.replace(VID, "BbCdEfGhIj0")
        (self.raw / "別.md").write_text(other, encoding="utf-8", newline="")
        page = self.page("動画", "x", confidence="medium").replace('raw: "raw/動画.md"', 'raw: ["raw/動画.md", "raw/別.md"]')
        codes = self.codes({"sources/動画.md": page})
        self.assertIn("several_video_raws", codes)
        self.assertIn("no_summary", codes)
        # 分割したページを読めなければ、指摘にする。
        self.write_page("sources/動画.md", self.page("動画", "x", confidence="medium"))
        self.write_page("sources/動画-2.md", self.page("動画 2", "x", confidence=None))
        real = Path.read_text

        def deny(path, *a, **k):
            if Path(path).name == "動画-2.md":
                raise PermissionError("拒否")
            return real(path, *a, **k)

        with mock.patch.object(Path, "read_text", deny):
            result = wc.check_wiki(self.wiki, {}, only_raw="raw/動画.md")
        self.assertIn("unreadable_page", [f.code for f in result.findings])
        # 一覧を作れないディレクトリも、黙って除かない（レビューの 3 回目）。
        import wiki_pages
        real_walk = wiki_pages.walk_pages

        def walk(root, visited=None):
            got = real_walk(root, visited=visited)
            return got._replace(files=[f for f in got.files if "動画-2" not in f.rel], unlistable=["sources/split"])

        with mock.patch.object(wiki_pages, "walk_pages", walk):
            result = wc.check_wiki(self.wiki, {}, only_raw="raw/動画.md")
        self.assertIn("unreadable_page", [f.code for f in result.findings])

    def test_several_raws_child_is_kept_for_one_raw(self):
        """2 つの raw を持つ分割ページの指摘は、1 つの raw に絞った verify でも残る（レビューの 3 回目）。"""
        other = self.raw_text.replace(VID, "BbCdEfGhIj0")
        (self.raw / "別.md").write_text(other, encoding="utf-8", newline="")
        child = self.page("動画 2", "x 50〔訂正 L2-1〕", confidence=None,
                          defs="- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:x）")
        child = child.replace('raw: "raw/動画.md"', 'raw: ["raw/動画.md", "raw/別.md"]')
        overlay = {"sources/動画.md": self.page("動画", "x", confidence="medium"), "sources/動画-2.md": child}
        self.assertIn("several_video_raws", self.codes(overlay))

    def test_hidden_mark_is_not_a_mark(self):
        """wikilink の行き先に隠れた印は、読み手に見えないので印として数えない（レビューの 4 回目）。"""
        body = "x [[50〔訂正 L2-1〕|本文]]"
        defs = "- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:x）"
        self.assertIn("unused_definition", self.codes({"sources/動画.md": self.page("動画", body, confidence="low",
                                                                                    defs=defs)}))

    def test_overlay_where_walk_does_not_go_is_refused(self):
        """ページの一覧が降りないディレクトリ（シンボリックリンク、ジャンクションの循環など）の中は、用意したページの
        場所にできない（レビューの 9 回目と 10 回目）。判定は、一覧そのものが降りたディレクトリで行う。"""
        import wiki_pages
        (self.wiki / "sources" / "linked").mkdir()
        (self.wiki / "sources" / "linked" / "deeper").mkdir()
        real_walk = wiki_pages.walk_pages

        def walk(root, visited=None):
            got = real_walk(root, visited=visited)
            if visited is not None:
                visited[:] = [v for v in visited if not v.startswith("sources/linked")]
            return got

        with mock.patch.object(wiki_pages, "walk_pages", walk):
            for rel in ("sources/linked/動画.md", "sources/linked/deeper/動画.md", "sources/linked/new/動画.md"):
                with self.subTest(rel=rel):
                    with self.assertRaises(ValueError):
                        wc.check_wiki(self.wiki, {rel: self.page("動画", "x")})
        # 新しいページは、一覧が降りる既存のディレクトリの直下にだけ置ける。新しいディレクトリは先に作る
        # （ファイルとディレクトリがぶつかる組を作れないようにする。レビューの 12 回目）。
        with self.assertRaises(ValueError):
            wc.check_wiki(self.wiki, {"sources/new/動画.md": self.page("動画", "x")})
        (self.wiki / "sources" / "new").mkdir()
        wc.check_wiki(self.wiki, {"sources/new/動画.md": self.page("動画", "x")})

    def test_overlay_set_must_be_writable_together(self):
        """用意したページは組として書けなければならない（レビューの 11 回目）。"""
        page = self.page("動画", "x")
        self.write_page("sources/既存.md", page)
        for overlay in ({"sources/x.md": page, "sources/x.md/child.md": page},
                        {"sources/新.md": page, "sources/新.MD": page},
                        {"sources/a.md": page, "Sources/A.md": page},
                        # 既存のページを、大文字と小文字だけが違う 2 つの指定で渡す（レビューの 12 回目）。
                        {"sources/既存.md": page, "SOURCES/既存.MD": page}):
            with self.subTest(overlay=list(overlay)):
                with self.assertRaises(ValueError):
                    wc.check_wiki(self.wiki, overlay)

    def test_binary_raw_of_other_sources_is_not_a_caption_raw(self):
        """PDF などの、動画でないソースの原本は、照合の対象にしない（to884/info-hive-wiki#74 のレビュー）。"""
        (self.raw / "資料.pdf").write_bytes(b"%PDF-1.7" + bytes(range(128, 256)))
        self.write_page("sources/資料.md", self.page("資料", "x", raw="raw/資料.pdf", kind=None, confidence=None))
        self.assertEqual([f.as_dict() for f in wc.check_wiki(self.wiki, {}).findings
                          if f.path in ("sources/資料.md", "raw/資料.pdf")], [])

    def test_new_page_appears_on_every_alias(self):
        """新しいページは、一覧がそのディレクトリに降りるすべての道筋で読まれる（レビューの 13 回目）。
        ジャンクションは試験で作れないので、実体の鍵だけを差し替えて、別名のディレクトリをまねる。"""
        (self.wiki / "sources" / "real").mkdir()
        (self.wiki / "sources" / "alias").mkdir()
        real_identity = wc._identity

        def identity(path):
            return real_identity(Path(str(path).replace("alias", "real")))

        with mock.patch.object(wc, "_identity", identity):
            pages, _u, _r = wc.load_pages(self.wiki, {"sources/real/a.md": self.page("a", "x")})
            self.assertEqual(sorted(p.rel for p in pages if p.slug == "a"), ["sources/alias/a.md", "sources/real/a.md"])
            with self.assertRaises(ValueError):
                wc.load_pages(self.wiki, {"sources/real/b.md": self.page("b", "x"),
                                          "sources/alias/B.md": self.page("b", "y")})

    def test_names_equal_after_nfc_are_not_merged(self):
        """NFC にそろえると同じ名前になる 2 つのファイルは、黙って 1 つにまとめず指摘にする（レビューの 14 回目）。"""
        decomposed = "e\u0301"
        composed = "\u00e9"
        try:
            self.write_page(f"sources/{decomposed}.md", self.page("a", "x"))
            self.write_page(f"sources/{composed}.md", self.page("b", "y"))
        except OSError:
            self.skipTest("このファイルシステムは、この名前を作れない")
        if not (self.wiki / "sources" / f"{decomposed}.md").samefile(self.wiki / "sources" / f"{composed}.md"):
            result = wc.check_wiki(self.wiki, {})
            self.assertIn("ambiguous_page_path", [f.code for f in result.findings])
        # 名前を正規化するファイルシステムでも確かめられるよう、一覧と読み込みを差し替えて同じ状態を作る。
        import wiki_pages
        files = [wiki_pages.MdFile(f"sources/{decomposed}.md", 1, 1), wiki_pages.MdFile(f"sources/{composed}.md", 1, 1)]
        texts = {decomposed: self.page("a", "x"), composed: self.page("b", "y")}
        real_read = Path.read_text

        def read(path, *a, **k):
            stem = Path(path).stem
            return texts[stem] if stem in texts else real_read(path, *a, **k)

        with mock.patch.object(wiki_pages, "walk_pages",
                               lambda root, visited=None: wiki_pages.Walk(files, [], [])), \
                mock.patch.object(Path, "read_text", read):
            pages, unreadable, _r = wc.load_pages(self.wiki, {})
        self.assertEqual(len(pages), 1)
        self.assertEqual([f.code for f in unreadable], ["ambiguous_page_path"])

    def test_slug_with_other_case_is_the_same_raw(self):
        """大文字と小文字だけが違うスラッグの指定でも、同じ動画の別版を different と判定する（レビューの 14 回目）。"""
        if os.path.normcase("A") != os.path.normcase("a"):
            self.skipTest("大文字と小文字を区別するファイルシステム")
        (self.raw / "Video.md").write_text(self.raw_text, encoding="utf-8", newline="")
        rel = wy.relations(self.wiki, self.raw, VID, "f" * 64, "video")
        self.assertEqual(rel["slug_state"], "different")

    def test_identity_is_the_file_not_the_spelling(self):
        """実体の鍵は、ファイルシステムの識別子で決める（レビューの 15 回目）。別のファイルは、名前の大文字と小文字が
        そろっても別の鍵になる。大文字と小文字を区別するディレクトリは試験で作れないので、識別子を差し替えてまねる。"""
        self.write_page("sources/Detail.md", self.page("d", "x"))
        a = wc._identity(self.wiki / "sources" / "Detail.md")
        self.assertTrue(a.startswith("id:"))
        if os.path.normcase("A") == os.path.normcase("a"):
            self.assertEqual(wc._identity(self.wiki / "SOURCES" / "detail.md"), a)
        real_stat = os.stat

        class Fake:
            def __init__(self, st, ino):
                self.st_dev, self.st_ino = st.st_dev, ino

        def fake_stat(path, *args, **kwargs):
            st = real_stat(path, *args, **kwargs)
            return Fake(st, 111 if Path(path).name == "Detail.md" else 222) if Path(path).suffix == ".md" else st

        with mock.patch.object(wc.os, "stat", fake_stat):
            self.assertNotEqual(wc._identity(self.wiki / "sources" / "Detail.md"),
                                wc._identity(self.wiki / "sources" / "detail.md"))

    def test_new_page_is_not_mistaken_for_other_case(self):
        """大文字と小文字を区別するディレクトリで、新しく作る detail.md を既存の Detail.md と取り違えない（レビューの
        16 回目）。区別するディレクトリは試験で作れないので、ファイルがあるかの答えを差し替えてまねる。"""
        self.write_page("sources/Detail.md", self.page("d", "既存の本文"))
        real_lexists = os.path.lexists
        with mock.patch.object(wc.os.path, "lexists", lambda q: False if Path(q).name == "detail.md" else real_lexists(q)):
            pages, _u, renamed = wc.load_pages(self.wiki, {"sources/detail.md": self.page("d2", "新しい本文")})
        texts = {p.rel: p.text for p in pages}
        self.assertIn("既存の本文", texts["sources/Detail.md"])
        self.assertIn("新しい本文", texts["sources/detail.md"])
        self.assertEqual(renamed, {"sources/detail.md": "sources/detail.md"})

    def test_new_name_is_not_normalized_before_asking(self):
        """新しく作る分解した形の名前を、合成済みの既存のページと取り違えない（レビューの 17 回目）。名前を区別する
        ファイルシステムは試験で作れないので、ファイルがあるかの答えを差し替えてまねる。"""
        composed = "\u00e9"
        decomposed = "e\u0301"
        self.write_page(f"sources/{composed}.md", self.page("c", "既存の本文"))
        real_lexists = os.path.lexists
        with mock.patch.object(wc.os.path, "lexists",
                               lambda q: False if Path(q).stem == decomposed else real_lexists(q)):
            pages, unreadable, _r = wc.load_pages(self.wiki, {f"sources/{decomposed}.md": self.page("n", "新しい本文")})
        self.assertIn("既存の本文", next(p.text for p in pages if p.slug == composed))
        self.assertEqual([f.code for f in unreadable], ["ambiguous_page_path"])

    def test_upper_case_page_extension_is_accepted(self):
        page_file = self.tmp / "draft.md"
        page_file.write_text(self.page("動画", "x"), encoding="utf-8", newline="")
        self.assertEqual(list(wy.parse_page_args([f"sources/A.MD={page_file}"])), ["sources/A.MD"])

    def test_same_page_twice_is_refused(self):
        page_file = self.tmp / "draft.md"
        page_file.write_text(self.page("動画", "x"), encoding="utf-8", newline="")
        code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "動画",
                                  "--page", f"sources/動画.md={page_file}", "--page", f"sources/動画.md={page_file}",
                                  "--json")
        self.assertEqual((code, out["status"]), (1, "error"))

    def test_unknown_words_use_the_same_char_classes(self):
        """「raw にない語」も、語の境目と同じ文字の種類で切る（レビューの 11 回目）。"""
        doc = wc.parse_raw(self.raw_text)
        word = "\U0001b000\U0001b155"
        self.assertEqual(wc.unknown_words([word + " と ニッサン と café"], doc, []), [word, "ニッサン", "café"])

    def test_invisible_corrected_word_is_refused(self):
        line = wc.format_definition("L2-1", "15", 1, "\u2060ヨタ", "model:x")
        self.assertIsInstance(wc.parse_definition(line), str)

    def test_findings_are_not_narrowed_to_one_raw(self):
        """verify は wiki 全体の指摘を返す。関係するページの壊れた印も残る（レビューの 4 回目）。"""
        summary = self.page("動画", "x 50〔訂正 L2-1〕", confidence="low",
                            defs="- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:x）")
        self.write_page("concepts/c.md", self.page("c", "999〔**訂正** [[動画]] L2-1〕", raw=None, kind=None,
                                                   confidence=None, type_="concept"))
        self.assertIn("bad_mark", self.codes({"sources/動画.md": summary}))

    @unittest.skipUnless(os.path.normcase("A") == os.path.normcase("a"), "大文字と小文字を区別しないファイルシステムだけ")
    def test_raw_spelled_with_other_case_is_the_same_raw(self):
        """`raw` の大文字と小文字の違いで、同じ raw を別に数えない（レビューの 4 回目）。"""
        parent = self.page("動画", "x", confidence="high").replace('caption_kind: "asr"', 'caption_kind: "asr"')
        child = self.page("動画 2", "x 50〔訂正 L2-1〕", confidence=None,
                          defs="- L2-1: 字幕 `15`（1 つ目） を `50` に訂正（根拠 model:x）").replace(
            'raw: "raw/動画.md"', 'raw: "RAW/動画.MD"')
        result = wc.check_wiki(self.wiki, {"sources/動画.md": parent, "sources/動画-2.md": child},
                               only_raw="raw/動画.md")
        self.assertEqual(len(result.raws), 1)
        self.assertEqual(result.raws[0].summaries, ["sources/動画-2.md", "sources/動画.md"])
        self.assertIn("confidence_mismatch", [f.code for f in result.findings])

    def test_raw_without_sections_is_refused(self):
        head = self.raw_text.split("\n## 区間 1", 1)[0] + "\n"
        with self.assertRaises(wc.CaptionError):
            wc.parse_raw(head)

    def test_caption_kind_copied(self):
        self.assertIn("caption_kind_mismatch", self.codes({"sources/動画.md": self.page("動画", "x", kind="uploaded")}))

    def test_unknown_words(self):
        overlay = {"sources/動画.md": self.page("動画", "トヨダの話で 50 人、ニッサンも。> 引用 ホンダ\n\n> スズキ\n\n"
                                                 "[リンク](https://example.com/マツダ) と `スバル`")}
        words = self.check(overlay).unknown_words["sources/動画.md"]
        self.assertIn("ニッサン", words)
        self.assertIn("50", words)
        self.assertIn("ホンダ", words)          # 行の途中の > は引用ではない
        for absent in ("トヨダ", "スズキ", "マツダ", "スバル"):
            self.assertNotIn(absent, words)
        # 用意したページの綴りをディスクの綴りに直しても、目印を探す（レビューの 8 回目）。
        if os.path.normcase("A") == os.path.normcase("a"):
            result = wc.check_wiki(self.wiki, {"SOURCES/動画.md": self.page("動画", "999 人")}, only_raw="raw/動画.md",
                                   unknown_for={"SOURCES/動画.md"})
            self.assertIn("999", result.unknown_words["sources/動画.md"])
        # `## 取り込んだ内容と載せたページ` の表の「掲載方法」の列で、中身がちょうど手順の値のセルだけを目印から外す。表の主張、
        # 関係するページの下の本文、本文の同じ語は残す（0.23.2 のレビューの 1 回目と 2 回目）。
        claims = self.page("動画", "命令は update である").replace(
            "命令は update である", "命令は update である\n\n## 取り込んだ内容と載せたページ\n\n| 取り込んだ内容 | 掲載方法 | 掲載ページと理由 |\n| --- | --- | --- |\n"
            "| 参加者は 999 人 | create | x |\n| 命令は delete | update | y |\n| z | source_only | create の理由 |\n\n"
            "## 関係するページ\n\n### 概要\n\nサンプル")
        words = self.check({"sources/動画.md": claims}).unknown_words["sources/動画.md"]
        for present in ("999", "サンプル", "update", "delete", "create"):
            self.assertIn(present, words)
        self.assertNotIn("source", words)
        # 掲載方法の値がその列にしかないページで、新旧の表記を確かめる。
        for heading, column in (
            ("取り込んだ内容と載せたページ", "掲載方法"),
            ("取り込んだ内容と載せたページ", "行き先"),
            ("主張と行き先", "行き先"),
        ):
            with self.subTest(heading=heading, column=column):
                only_dest = self.page(
                    "動画",
                    f"本文は x\n\n## {heading}\n\n| 内容 | {column} |\n| --- | --- |\n"
                    "| a | create |\n| b | update |\n| c | source_only |",
                )
                words = self.check({"sources/動画.md": only_dest}).unknown_words.get("sources/動画.md", [])
                for absent in ("create", "update", "source", "only"):
                    self.assertNotIn(absent, words)
        plain = self.page("動画", "| 主張 | 行き先 |\n| --- | --- |\n| a | create |")
        self.assertIn("create", self.check({"sources/動画.md": plain}).unknown_words["sources/動画.md"])
        # 印のない関係するページも、sources の要約ページの raw と照らす（レビューの 10 回目）。
        entity = self.page("e", "999 社", raw=None, kind=None, confidence=None, type_="entity").replace(
            'tags: ["x"]', 'tags: ["x"]' + chr(10) + 'sources: ["動画"]')
        result = wc.check_wiki(self.wiki, {"sources/動画.md": self.page("動画", "x"), "entities/e.md": entity},
                               only_raw="raw/動画.md", unknown_for={"entities/e.md"})
        self.assertIn("999", result.unknown_words["entities/e.md"])
        # 画像の代替の文字は、閲覧では本文として表示されるので、目印の対象にする（レビューの 5 回目）。
        overlay = {"sources/動画.md": self.page("動画", "![999](https://example.com/image.png)")}
        self.assertIn("999", self.check(overlay).unknown_words["sources/動画.md"])

    def test_verify_refuses_primary_hardlink_before_parsing_raw(self):
        os.link(self.raw / "動画.md", self.tmp / "raw-copy.md")
        with mock.patch.object(wc, "parse_raw", side_effect=AssertionError("リンクの本文を読んだ")):
            code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw),
                                      "--slug", "動画", "--json")
        self.assertNotEqual(code, 0)
        self.assertIn("link", json.dumps(out, ensure_ascii=False))

    def test_write_rejects_parent_in_root_before_fetch(self):
        from types import SimpleNamespace
        args = SimpleNamespace(wiki=str(self.wiki), raw_root=str(self.wiki / "../raw"))
        with mock.patch.object(wy, "take", side_effect=AssertionError("取得に進んだ")):
            with self.assertRaises(wy.Fail):
                wy.cmd_write(args)

    def test_rejected_evidence_is_not_called_missing(self):
        os.link(self.raw / "記事.md", self.tmp / "article-copy.md")
        self.write_page("sources/動画.md", self.page("動画", "トヨダ〔訂正 L3-1〕の話", confidence="medium",
            defs="- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 wiki_source:記事）"))
        result = wc.check_wiki(self.wiki, raw_roots=[self.raw])
        messages = [f.message for f in result.findings if f.code == "bad_definition"]
        self.assertTrue(any("リンクなので読まない" in m for m in messages), messages)
        self.assertFalse(any("見つからない" in m for m in messages), messages)

    def test_partial_evidence_keeps_refusal_after_filtering(self):
        os.link(self.raw / "記事.md", self.tmp / "article-copy.md")
        (self.raw / "other.md").write_text("訂正した語のない別の原本", encoding="utf-8")
        refs = ["raw/記事.md", "raw/other.md"]
        source = self.page("記事", "本文", raw=None, kind=None, confidence=None)
        source = source.replace("created: 2026-11-16", "raw: " + json.dumps(refs, ensure_ascii=False) + "\ncreated: 2026-11-16")
        self.write_page("sources/記事.md", source)
        self.write_page("sources/動画.md", self.page("動画", "トヨダ〔訂正 L3-1〕の話", confidence="medium",
            defs="- L3-1: 字幕 `トヨタ` を `トヨダ` に訂正（根拠 wiki_source:記事）"))
        for text, has_witness in (("別の原本", False), (self.raw_text, False), ("トヨダ", True)):
            (self.raw / "other.md").write_text(text, encoding="utf-8")
            result = wc.check_wiki(self.wiki, raw_roots=[self.raw])
            messages = [f.message for f in result.findings if f.code == "bad_definition"]
            if has_witness:
                self.assertEqual(messages, [])
            else:
                self.assertTrue(any("リンクなので読まない" in m for m in messages), messages)
                self.assertFalse(any("見つからない" in m or "raw にない" in m for m in messages), messages)

    def test_verify_passes_raw_root_for_auxiliary_raw(self):
        from tests.wiki.test_wiki_links import junction
        external = self.tmp / "external"
        external.mkdir()
        (external / "other.md").write_text(self.raw_text, encoding="utf-8")
        jump = self.raw / "jump"
        if not junction(jump, external):
            self.skipTest("ディレクトリのリンクを作れない")
        def cleanup_jump():
            if os.path.lexists(jump):
                os.rmdir(jump) if os.name == "nt" else jump.unlink()
        self.addCleanup(cleanup_jump)
        self.write_page("sources/動画.md", self.page("動画", "本文"))
        self.write_page("sources/別.md", self.page("別", "本文", raw="raw/jump/other.md"))
        original = Path.read_text
        def checked_read(path, *args, **kwargs):
            if "jump" in path.parts:
                raise AssertionError("途中のリンクを通って読んだ")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "read_text", checked_read):
            code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw),
                                      "--slug", "動画", "--json")
        self.assertEqual(code, 1)
        self.assertTrue(any(f["code"] == "unreadable_raw" and f["path"] == "sources/別.md" for f in out["findings"]))

    def test_verify_warns_about_unrelated_ambiguity_without_blocking(self):
        self.write_page("sources/動画.md", self.page("動画", "本文"))
        self.write_page("sources/別.md", self.page("別", "本文", raw="other.md", kind=None, confidence=None))
        (self.wiki / "other.md").write_text("A", encoding="utf-8")
        (self.wiki.parent / "other.md").write_text("B", encoding="utf-8")
        code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw),
                                  "--slug", "動画", "--json")
        self.assertEqual((code, out["findings"]), (0, []))
        self.assertTrue(any(w["state"] == "ambiguous" for w in out["raw_warnings"]))

    def test_verify_cli_and_lint(self):
        summary = self.page("動画", "講義では 50〔訂正 L2-1〕 人", confidence="medium",
                            defs="- L2-1: 字幕 `15`（2 つ目） を `50` に訂正（根拠 model:x）")
        page_file = self.tmp / "draft.md"
        page_file.write_text(summary, encoding="utf-8", newline="")
        code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "動画",
                                  "--page", f"sources/動画.md={page_file}", "--json")
        self.assertEqual(code, 1)
        self.assertEqual([f["code"] for f in out["findings"]], ["confidence_mismatch"])
        self.assertEqual(out["result"]["confidence"], "low")
        page_file.write_text(summary.replace('confidence: "medium"', 'confidence: "low"'), encoding="utf-8", newline="")
        code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "動画",
                                  "--page", f"sources/動画.md={page_file}", "--json")
        self.assertEqual((code, out["findings"]), (0, []))
        code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug", "動画",
                                  "--json")
        self.assertEqual(out["findings"][-1]["code"], "no_summary")
        # ページとして読まれない場所の用意したページは、照らさずに止まる（レビューの 6 回目）。
        for rel in (".wiki-cache/動画.md", "raw/動画.md", "assets/動画.md", "indexes/動画.md", "sources/.x/動画.md",
                    "sources/../動画.md", "index.md", "GRAPH/動画.md", "Assets/動画.md", "INDEX.md",
                    # Windows が読み替える形（レビューの 8 回目）。
                    "graph./動画.md", "graph /動画.md", "WIKI-C~1/動画.md", "sources/CON.md", "sources/a:b.md",
                    "sources /動画.md", "sources/COM¹/動画.md", "sources/CONIN$/動画.md", "LPT³.md"):
            with self.subTest(rel=rel):
                code, out = self.run_main("verify", "--wiki", str(self.wiki), "--raw-root", str(self.raw), "--slug",
                                          "動画", "--page", f"{rel}={page_file}", "--json")
                self.assertEqual(code, 1)
                self.assertEqual(out.get("status"), "error", out)
        # lint は、ディスクに書いたページを同じ規則で照らす。
        self.write_page("sources/動画.md", summary)
        pages = wiki_lint.collect_pages(self.wiki)
        findings = wiki_lint.lint(pages, 100, 200, [], False, 5, wiki_root=self.wiki)
        self.assertEqual([f["code"] for f in findings["caption_corrections"]], ["confidence_mismatch"])
        self.assertEqual(findings["summary"]["caption_corrections"], 1)
        self.assertIsNone(wiki_lint.lint(pages, 100, 200, [], False, 5)["summary"]["caption_corrections"])
        out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_lint.py"), str(self.wiki)],
                             capture_output=True, timeout=120)
        self.assertIn("YouTube の字幕", out.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
