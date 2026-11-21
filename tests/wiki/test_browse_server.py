"""閲覧（browse）のサーバーの試験。

設計は `docs/plans/wiki-browse-stage1-2026-11-09.md` の 8（守ること 3、7、8、9）。要求の拒否、作り直し、
「古い」状態、操作の口は、試験のプロセスの中で動かすサーバーで確かめる。起動の競合、使い回し、停止、
操作がないときの終了は、実際のプロセス（`wiki_browse.py serve`）で確かめる。

実行:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse_server.py -v
"""
from __future__ import annotations

import hashlib
import html
import http.client
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import wiki_browse  # noqa: E402
import wiki_browse_core as core  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402

wiki_browse._load()


def enter_state(wiki: Path) -> Path:
    """起動と同じに、状態のディレクトリに入る（なければ作り、目印を置く）。状態のディレクトリを返す。"""
    state_dir = wiki_browse._state_dir(wiki)
    fs._enter_state(wiki, wiki_browse.browse_dir(), state_dir, fs.owner_of(wiki), create=True)
    return Path(state_dir)


def state_lock(wiki: Path) -> "fs.Lock":
    return fs.Lock(str(enter_state(wiki) / "server.lock"))


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def request(port: int, method: str, path: str, host: "str | None" = None, *, headers: dict | None = None) -> tuple:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    try:
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        conn.putheader("Host", host if host is not None else f"127.0.0.1:{port}")
        for name, value in (headers or {}).items():
            conn.putheader(name, value)
        conn.endheaders()
        res = conn.getresponse()
        return res.status, res.read().decode("utf-8", errors="replace"), dict(res.getheaders())
    finally:
        conn.close()



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


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.wiki = self.base / "wiki"
        # 入口（wiki_root）は SCHEMA.md のないディレクトリを断る（ADR-0019）。SCHEMA.md はページではない。
        write(self.wiki, "SCHEMA.md", "# スキーマ\n")
        write(self.wiki, "concepts/a.md", '---\ntype: "concept"\n---\n# A\n\n本文 1。 [[b]] [[missing]]\n')
        write(self.wiki, "concepts/b.md", "# B\n")
        self.data = self.base / "data"
        self.env = {**os.environ, "INFO_HIVE_DATA_DIR": str(self.data)}
        self._env = mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(self.data)})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()


class InProcess(Base):
    """試験のプロセスの中でサーバーを動かす。"""

    def setUp(self):
        super().setUp()
        self.state_dir = enter_state(self.wiki)
        self.owner = fs.owner_of(self.wiki)
        self.app = wiki_browse.App(self.wiki, idle=600, assets=core.load_assets())
        self.httpd = wiki_browse._Server(("127.0.0.1", 0), wiki_browse.Handler)
        self.httpd.app = self.app
        self.app.httpd = self.httpd
        self.app.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()
        self.port = self.app.port
        self.prefix = f"/{self.app.view_token}/w/{self.app.key}/"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def get(self, name: str, method: str = "GET") -> tuple:
        return request(self.port, method, self.prefix + name)


class RequestTest(InProcess):
    def test_listens_only_on_loopback(self):
        self.assertEqual(self.httpd.server_address[0], "127.0.0.1")

    def test_rejections(self):
        self.assertEqual(self.get("concepts/a.html")[0], 200)
        self.assertEqual(request(self.port, "GET", self.prefix + "concepts/a.html", host="localhost")[0], 421)
        self.assertEqual(request(self.port, "GET", self.prefix + "concepts/a.html", host="127.0.0.1")[0], 421)
        wrong = f"/{'x' * len(self.app.view_token)}/w/{self.app.key}/index.html"
        self.assertEqual(request(self.port, "GET", wrong)[0], 404)
        self.assertEqual(request(self.port, "GET", f"/%E3%81%82/w/{self.app.key}/index.html")[0], 404)
        self.assertEqual(self.get("concepts/a.html", "POST")[0], 405)
        self.assertEqual(self.get("concepts/a.html", "PUT")[0], 405)
        for bad in ("%2e%2e/x.html", "../x.html", "concepts/%5c..%5ca.html", "a%00.html", "%ff.html",
                    "concepts//a.html", "./index.html"):
            self.assertEqual(self.get(bad)[0], 404, bad)
        code, body, _h = self.get("concepts/nope.html")
        self.assertEqual(code, 404)
        self.assertIn('href="../index.html"', body)
        self.assertNotIn(str(self.wiki), body)
        # 見つからないページも、アイコンがないことを宣言し、製品の Chrome と Edge に /favicon.ico を要求させない
        self.assertIn(core.ICON_LINK, body)

    def test_other_methods_and_bad_request_line(self):
        for method in ("PATCH", "OPTIONS", "DELETE"):
            self.assertEqual(self.get("concepts/a.html", method)[0], 405, method)
        import socket
        with socket.create_connection(("127.0.0.1", self.port), timeout=10) as s:
            s.sendall(f"GET {self.prefix}index.html HTTP/9.9 x\r\nHost: 127.0.0.1:{self.port}\r\n\r\n".encode())
            data = s.recv(65536).decode("utf-8", errors="replace")
        self.assertTrue(data.startswith("HTTP/1.1 400") or data.startswith("HTTP/1.0 400"), data[:60])
        self.assertIn("Content-Security-Policy", data)
        self.assertNotIn(self.app.view_token, data)

    def test_render_error_is_500_and_keeps_serving(self):
        self.assertEqual(self.get("concepts/a.html")[0], 200)
        with mock.patch.object(core.Core, "render", side_effect=RuntimeError("x")), redirect_stderr(io.StringIO()):
            code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 500)
        self.assertNotIn("RuntimeError", body)
        self.assertEqual(self.get("concepts/a.html")[0], 200)

    def test_unparsable_raw_is_served(self):
        write(self.wiki, "concepts/a.md", '---\ntype: "source"\nraw: "http://["\n---\n# A\n')
        self.assertEqual(self.get("concepts/a.html")[0], 200)

    def test_page_pointing_at_the_record_is_not_drawn(self):
        # Wiki のページが browse の作ったファイル（記録）を指すシンボリックリンクなら、読まず、描かない
        # （info-hive-dev の ADR-0029。ADR-0017 の「入力の実体は、置き場所によらず読む」のうち、リンクを通って
        # 届くものを置き換えた）。サーバーは動き続ける（構造の直しの設計の 5、10）
        record = self.state_dir / "server.json"
        record.write_text(json.dumps({"note": "RECORD-CONTENT"}), encoding="utf-8")
        try:
            os.symlink(record, self.wiki / "concepts" / "record.md")
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない")
        code, body, _h = self.get("concepts/record.html")
        self.assertEqual(code, 404)
        self.assertNotIn("RECORD-CONTENT", body)
        self.assertFalse(self.app._stopping.is_set())
        self.assertEqual(request(self.port, "GET", f"/{self.app.control_token}/control/locate/a")[0], 200)

    def test_headers(self):
        _code, _body, headers = self.get("concepts/a.html")
        self.assertEqual(headers["Content-Security-Policy"], core.CSP)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        code, body, headers = self.get("assets/app.js")
        self.assertEqual(code, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))
        # Fluent 2 の同梱の CSS と、配色を決める theme.js（Fluent 2 の設計の 2、6）
        for name, kind in (("assets/fluent2.css", "text/css"), ("assets/theme.js", "text/javascript"),
                           ("assets/style.css", "text/css")):
            code, body, headers = self.get(name)
            self.assertEqual(code, 200, name)
            self.assertTrue(headers["Content-Type"].startswith(kind), name)
            self.assertEqual(body.encode("utf-8"), (SCRIPTS / "browse_assets" / name.split("/")[1]).read_bytes(), name)

    def test_search_data_is_embedded(self):
        # data/search.js を返し、静的の書き出しと同じ中身になる。capabilities.search は embedded（探しやすさの設計の 6）
        code, body, headers = self.get("data/search.js")
        self.assertEqual(code, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))
        self.assertTrue(body.startswith("window.WIKI_SEARCH="))
        snap = core.take_snapshot(self.wiki)
        self.assertEqual(body, core.Core(snap).render_data("data/search.js"))
        manifest = self.get("data/manifest.js")[1]
        self.assertIn('"search":"embedded"', manifest)

    def test_control(self):
        code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/status")
        self.assertEqual(json.loads(body)["instance"], self.app.instance)
        # 閲覧のトークンでは、操作の口に届かない
        self.assertEqual(request(self.port, "POST", f"/{self.app.view_token}/control/stop")[0], 404)
        self.assertFalse(self.app._stopping.is_set())
        for target, state in (("b", "resolved"), ("missing", "unresolved")):
            code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/{target}")
            self.assertEqual(json.loads(body)["state"], state, target)

    def test_responses_have_no_paths_or_tokens(self):
        names = ["index.html", "nav.js", "data/manifest.js", "data/diagnostics.js", "concepts/a.html",
                 "concepts/nope.html", "assets/app.js"]
        bodies = [self.get(n)[1] for n in names]
        bodies.append(request(self.port, "GET", self.prefix + "concepts/a.html", host="x")[1])
        bodies.append(request(self.port, "GET", f"/{self.app.control_token}/control/locate/a")[1])
        for body in bodies:
            for needle in (str(self.wiki), self.wiki.as_posix(), str(self.data), self.app.control_token):
                self.assertNotIn(needle, body)

    def test_broken_record_is_not_reused(self):
        for rec in ({"port": 1, "view_token": "a", "control_token": "b", "instance": None},
                    {"port": "1", "view_token": "a", "control_token": "b", "instance": "c"},
                    {"port": 1, "view_token": "", "control_token": "b", "instance": "c"}, None, []):
            self.assertIsNone(wiki_browse._valid_record(rec), rec)
            self.assertIsNone(wiki_browse._answering(rec), rec)

    def test_stop_waits_for_record_of_starting_server(self):
        # サーバーがロックを持ち、まだ記録を書いていない状態を作る。
        record = self.state_dir / "server.json"
        if record.exists():
            record.unlink()
        lock = state_lock(self.wiki)
        self.assertTrue(lock.try_acquire())

        def later():
            time.sleep(0.7)
            record.write_text(json.dumps(dict(self.app.record(), owner=self.owner)), encoding="utf-8")
            self.app._stopping.wait(20)
            lock.release()
        helper = threading.Thread(target=later)
        helper.start()
        out = io.StringIO()
        from contextlib import redirect_stdout
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = wiki_browse.stop(self.wiki)
        helper.join(30)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out.getvalue())["stopped"])
        self.assertTrue(self.app._stopping.is_set())

    def test_finish_removes_record_pointed_by_a_page(self):
        # 記録は browse のものである。ページが指していても、終了で消す。ページのリンクは先のないリンクになる
        # （構造の直しの設計の 10。言い換えのあとは欠陥でない）
        root, state_dir = wiki_browse.browse_dir(), str(self.state_dir)
        outcome, server = fs.serve_start(self.wiki, root, state_dir, self.owner, lambda: {"instance": "x"})
        self.assertEqual(outcome, "started")
        record = self.state_dir / "server.json"
        try:
            os.symlink(record, self.wiki / "concepts" / "record.md")
        except (OSError, NotImplementedError):
            server.lock.release()
            self.skipTest("シンボリックリンクを作れない")
        fs.serve_finish(server)
        self.assertFalse(record.exists())
        self.assertTrue(os.path.islink(self.wiki / "concepts" / "record.md"))

    def test_record_and_marker_carry_the_wiki_root(self):
        # 記録と目印に Wiki のルートの識別子を書き、記録を読む側はいつも照らす（構造の直しの設計の 7.1）
        root, state_dir = wiki_browse.browse_dir(), str(self.state_dir)
        outcome, server = fs.serve_start(self.wiki, root, state_dir, self.owner, lambda: {"instance": "x"})
        try:
            rec = json.loads((self.state_dir / "server.json").read_text(encoding="utf-8"))
            self.assertEqual(rec["owner"], self.owner)
            self.assertEqual((self.state_dir / fs.SERVER_MARKER).read_text(encoding="utf-8"), self.owner)
            with self.assertRaises(fs.Stop):
                fs.probe_server(self.wiki, root, state_dir, "other-wiki")
            with self.assertRaises(fs.Stop):
                fs.serve_start(self.wiki, root, state_dir, "other-wiki", lambda: {"instance": "y"})
            self.assertEqual(fs.probe_server(self.wiki, root, state_dir, self.owner)[0], "running")
        finally:
            fs.serve_finish(server)
        self.assertEqual(fs.probe_server(self.wiki, root, state_dir, self.owner), ("not-running", None))

    def test_locate_accepts_wikilink_spellings(self):
        import urllib.parse
        for target in ("concepts/b", "concepts\\b", "/concepts/b", "b", "concepts/b.md", "b#x"):
            quoted = urllib.parse.quote(target, safe="")
            code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/{quoted}")
            self.assertEqual(code, 200, target)
            res = json.loads(body)
            self.assertEqual(res["state"], "resolved", target)
            self.assertEqual(res["path"], "concepts/b.html", target)
        # 閲覧のトークンでは届かず、行き先がファイルのパスとして使われることもない
        self.assertEqual(request(self.port, "GET", f"/{self.app.view_token}/control/locate/b")[0], 404)
        code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/..%2F..%2Fsecret")
        self.assertEqual(json.loads(body)["state"], "unresolved")
        self.assertEqual(request(self.port, "POST", f"/{self.app.control_token}/control/locate/b")[0], 405)
        self.assertEqual(request(self.port, "GET", f"/{self.app.control_token}/control/locate/%ff")[0], 404)

    def test_generated_at_belongs_to_the_core(self):
        self.get("index.html")
        c = self.app.state.current
        self.assertTrue(c.generated_at)
        c.generated_at = "TIME-A"
        self.assertIn('"generated_at":"TIME-A"', self.get("data/manifest.js")[1])
        self.assertFalse(hasattr(self.app.state, "generated_at"))

    def test_log_has_no_tokens(self):
        self.app.verbose = True
        err = io.StringIO()
        with redirect_stderr(err):
            self.get("concepts/a.html")
            request(self.port, "GET", f"/{self.app.control_token}/control/status")
        log = err.getvalue()
        self.assertIn("GET", log)
        self.assertNotIn(self.app.view_token, log)
        self.assertNotIn(self.app.control_token, log)


class RecordReads(fs.Os):
    """記録（server.json）を開く口を見張る。fails() が真のあいだは PermissionError にする（fails がなければ手を入れない）。

    記録を開けなかったら（入れた失敗でも、OS の失敗でも）、unreadable を立てる。試験の補助のスレッドは、時間ではなく
    この合図で次に進む。stop が読めない記録を見たあとでだけ、サーバーの次の段（記録を消す、ロックを離す）に進む。
    """

    def __init__(self, fails=None):
        self.fails = fails
        self.denied = 0
        self.unreadable = threading.Event()

    def open_read(self, path):
        record = os.path.basename(os.fspath(path)) == "server.json"
        if record and self.fails is not None and self.fails():
            self.denied += 1
            self.unreadable.set()
            raise PermissionError(13, "injected")
        try:
            return super().open_read(path)
        except PermissionError:
            if record:
                self.unreadable.set()
            raise

    def wait_unreadable(self, done: threading.Event) -> None:
        wait_either(self.unreadable, done)


def wait_either(event: threading.Event, done: threading.Event) -> None:
    """event が立つか、done（stop が終わった）が立つまで待つ。時間では抜けない（順を時間で作らない）。

    stop が合図を立てずに終われば、補助のスレッドも先に進み、試験の確かめ（合図が立ったか）が落ちる。
    """
    while not event.wait(0.05):
        if done.is_set():
            return


def win_hold_for_delete(path, pending: bool):
    """Windows で、名前を付け替えるか消す途中のハンドル（DELETE の権利、共有はすべて）を開いて返す。

    os.replace（MoveFileExW）と os.unlink（DeleteFileW）は、途中でこの形のハンドルを持つ。pending なら、削除の印を
    付け（FileDispositionInfo）、名前を削除待ちにする。閉じるまで、名前はどの共有でも開けない。閉じると名前が消える。
    """
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k32.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.SetFileInformationByHandle.restype = wintypes.BOOL
    handle = k32.CreateFileW(str(path), 0x00010000, 0x7, None, 3, 0x80, None)    # DELETE、OPEN_EXISTING
    if handle in (None, wintypes.HANDLE(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    if pending:
        delete = ctypes.c_ubyte(1)          # FILE_DISPOSITION_INFO（DeleteFile = TRUE）
        if not k32.SetFileInformationByHandle(handle, 4, ctypes.byref(delete), 1):
            error = ctypes.get_last_error()
            k32.CloseHandle(handle)
            raise ctypes.WinError(error)
    return handle


def win_close(handle) -> None:
    import ctypes
    ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(handle))


class UnreadableRecordTest(InProcess):
    """サーバーがロックを持ち、記録を読めない（分からない）あいだ、stop と serve は待つ（構造の直しの設計の 7.1）。

    0.19.0 までの stop は、記録を読めない失敗で、すぐに「確かめられないので、何も変えずに止める」で終わった。
    Windows では、サーバーが記録を置き換えるか消している途中に、stop の読み取りがそうなる（CI の
    test_stop_while_starting_waits_for_record が、ときどき落ちた）。ここでは、その途中の状態を作って確かめる。
    """

    def setUp(self):
        super().setUp()
        self.record = self.state_dir / "server.json"
        self.lock = state_lock(self.wiki)
        self.assertTrue(self.lock.try_acquire())
        self.write_record()
        self.stop_done = threading.Event()        # stop が戻った（成功でも例外でも）
        self.held = []                            # 開いたままの Windows のハンドル（一時ディレクトリを消す前に閉じる）

    def close_held(self):
        while self.held:
            win_close(self.held.pop())

    def tearDown(self):
        self.stop_done.set()
        self.close_held()
        self.lock.release()
        fs.MUTANTS.clear()
        super().tearDown()

    def write_record(self):
        self.record.write_text(json.dumps(dict(self.app.record(), owner=self.owner)), encoding="utf-8")

    def stop(self, reads=None):
        from contextlib import redirect_stdout
        out = io.StringIO()
        try:
            with mock.patch.object(fs, "X", reads or fs.Os()), redirect_stdout(out), redirect_stderr(io.StringIO()):
                code = wiki_browse.stop(self.wiki)
        finally:
            self.stop_done.set()
        return code, json.loads(out.getvalue())

    def release_after_stop(self, then=None) -> threading.Thread:
        """stop の要求が届いたら、then() を呼んでからロックを離す（終わるサーバーの順）。stop が要求を送らずに
        終われば、そこでロックを離す（時間では進まない）。"""
        def later():
            wait_either(self.app._stopping, self.stop_done)
            if then is not None:
                then()
            self.lock.release()
        helper = threading.Thread(target=later)
        helper.start()
        return helper

    def assert_reports_like_ci(self, error):
        # 対照の失敗は、CI で出た知らせと同じ形になる
        err = io.StringIO()
        with redirect_stderr(err):
            wiki_browse._exit_for(error, False)
        self.assertIn("確かめられないので、何も変えずに止める: open_read: PermissionError", err.getvalue())

    def test_stop_waits_while_the_starting_server_record_is_unreadable(self):
        reads = RecordReads(lambda: reads.denied < 3)
        helper = self.release_after_stop()
        code, out = self.stop(reads)
        helper.join(30)
        self.assertEqual((code, out["stopped"]), (0, True))
        self.assertEqual(reads.denied, 3)
        self.assertTrue(self.app._stopping.is_set())

    def test_control_stop_fails_on_the_unreadable_record(self):
        fs.MUTANTS.add("unreadable_record_fails")
        reads = RecordReads(lambda: reads.denied < 3)
        with self.assertRaises(fs.Unknown) as caught:
            self.stop(reads)
        self.assertFalse(self.app._stopping.is_set())
        self.assert_reports_like_ci(caught.exception)

    def test_stop_waits_while_the_finishing_server_removes_the_record(self):
        # 止める要求のあと、終わるサーバーが記録を消す途中（読めない）でも、ロックがあるあいだは待つ。終わるサーバーは、
        # stop がロックのあるあいだに読めない記録を見てから、記録を消してロックを離す（順を合図で決める）
        reads = RecordReads(lambda: self.app._stopping.is_set() and self.lock.fd is not None)

        def finishing():
            reads.wait_unreadable(self.stop_done)
            self.record.unlink()
        helper = self.release_after_stop(finishing)
        try:
            code, out = self.stop(reads)
        finally:
            helper.join(30)
        self.assertEqual((code, out["stopped"]), (0, True))
        self.assertGreater(reads.denied, 0)

    def test_control_stop_fails_while_the_finishing_server_removes_the_record(self):
        fs.MUTANTS.add("unreadable_record_fails")
        reads = RecordReads(lambda: self.app._stopping.is_set())
        helper = self.release_after_stop(lambda: reads.wait_unreadable(self.stop_done))
        try:
            with self.assertRaises(fs.Unknown):
                self.stop(reads)
        finally:
            helper.join(30)
        self.assertGreater(reads.denied, 0)

    def test_stop_reports_the_unreadable_record_when_time_runs_out(self):
        reads = RecordReads(lambda: True)
        with mock.patch.object(wiki_browse, "RECORD_WAIT", 0.6):
            with self.assertRaises(wiki_browse.Failed) as caught:
                self.stop(reads)
        self.assertIn("サーバーの記録を読めないので、止められない: open_read: PermissionError", str(caught.exception))
        self.assertFalse(self.app._stopping.is_set())

    def test_serve_waits_and_reports_the_unreadable_record(self):
        reads = RecordReads(lambda: True)
        with mock.patch.object(fs, "X", reads), mock.patch.object(wiki_browse, "RECORD_WAIT", 0.6), \
                redirect_stderr(io.StringIO()):
            self.assertEqual(fs.serve_start(self.wiki, wiki_browse.browse_dir(), str(self.state_dir), self.owner,
                                            lambda: {"instance": "x"})[0], "unreadable")
            with self.assertRaises(wiki_browse.Failed) as caught:
                wiki_browse.serve(self.wiki, None, False, 600)
        self.assertIn("動いているサーバーの記録を読めないので、使い回せない: open_read: PermissionError",
                      str(caught.exception))

    @unittest.skipUnless(os.name == "nt", "共有の指定と削除待ちは Windows だけ")
    def test_record_held_for_rename_or_delete_is_read(self):
        # os.replace と os.unlink の途中のハンドル（DELETE の権利）があっても、記録を読める（設計の 3.1）
        handle = win_hold_for_delete(self.record, pending=False)
        try:
            self.assertEqual(fs.read_record(str(self.state_dir))["instance"], self.app.instance)
            fs.MUTANTS.add("read_without_share_delete")      # 対照: os.open は共有違反で開けない
            with self.assertRaises(fs.Unknown):
                fs.read_record(str(self.state_dir))
        finally:
            win_close(handle)

    @unittest.skipUnless(os.name == "nt", "共有の指定は Windows だけ")
    def test_reading_the_record_does_not_block_its_removal(self):
        # 読んで開いているあいだも、サーバーは記録を消せる（読む側が FILE_SHARE_DELETE で開く。設計の 3.1）
        fd = fs.X.open_read(str(self.record))
        try:
            os.unlink(self.record)
        finally:
            os.close(fd)
        self.assertFalse(self.record.exists())
        self.write_record()
        fs.MUTANTS.add("read_without_share_delete")          # 対照: os.open で開くと、消す側が共有違反になる
        fd = fs.X.open_read(str(self.record))
        try:
            with self.assertRaises(PermissionError):
                os.unlink(self.record)
        finally:
            os.close(fd)

    @unittest.skipUnless(os.name == "nt", "削除待ちは Windows だけ")
    def test_stop_waits_while_the_record_is_delete_pending(self):
        # 実際の OS の状態で、CI の失敗を作る。記録は削除待ちで、どの共有でも開けない。サーバーは、stop が削除待ちの
        # 記録を見てから、記録を消し終え、新しい記録を書き、止める要求を受けてからロックを離す（順を合図で決める）
        self.held.append(win_hold_for_delete(self.record, pending=True))
        self.assertEqual(fs.probe_server(self.wiki, wiki_browse.browse_dir(), str(self.state_dir), self.owner)[0],
                         "unreadable")
        reads = RecordReads()          # 手を入れずに見張る（失敗は OS の削除待ちだけ）

        def server():
            reads.wait_unreadable(self.stop_done)
            self.close_held()
            self.write_record()
            wait_either(self.app._stopping, self.stop_done)
            self.lock.release()
        helper = threading.Thread(target=server)
        helper.start()
        try:
            code, out = self.stop(reads)
        finally:
            helper.join(30)
        self.assertTrue(reads.unreadable.is_set())
        self.assertEqual((code, out["stopped"]), (0, True))

    @unittest.skipUnless(os.name == "nt", "削除待ちは Windows だけ")
    def test_control_stop_fails_while_the_record_is_delete_pending(self):
        handle = win_hold_for_delete(self.record, pending=True)
        try:
            fs.MUTANTS.add("unreadable_record_fails")
            with self.assertRaises(fs.Unknown) as caught:
                self.stop()
        finally:
            win_close(handle)
        self.assert_reports_like_ci(caught.exception)


class RebuildTest(InProcess):
    def setUp(self):
        super().setUp()
        self._retry = mock.patch.object(wiki_browse, "RETRY_INTERVAL", 0.3)
        self._retry.start()

    def tearDown(self):
        self._retry.stop()
        super().tearDown()

    def test_edit_is_shown_on_next_request(self):
        self.assertIn("本文 1", self.get("concepts/a.html")[1])
        write(self.wiki, "concepts/a.md", '---\ntype: "concept"\n---\n# A\n\n本文 2 が新しい。\n')
        self.assertIn("本文 2", self.get("concepts/a.html")[1])
        write(self.wiki, "graph/ontology.yaml", "node_types: {concept: {}}\npredicates: {}\n")
        self.assertIn("_relations", self.get("concepts/a.html")[1])
        write(self.wiki, "index.md", "# 索引\n\n- [[a]]\n")
        self.assertIn('"label":"a"', self.get("nav.js")[1])

    def test_failed_build_is_stale_and_recovers_after_revert(self):
        page = self.wiki / "concepts/a.md"
        self.get("concepts/a.html")
        original = page.read_bytes()
        st = os.stat(page)
        with mock.patch.object(core, "Core", side_effect=RuntimeError("x")):
            write(self.wiki, "concepts/a.md", "# 壊れた\n")
            code, body, _h = self.get("concepts/a.html")
            self.assertEqual(code, 200)
            self.assertIn("最新の内容を表示できていない", body)
            self.assertIn("本文 1", body)               # 前の中核で答える
            self.assertNotIn("RuntimeError", body)
        # 変更を取り消して、印を前と同じに戻す
        page.write_bytes(original)
        os.utime(page, ns=(st.st_atime_ns, st.st_mtime_ns))
        time.sleep(0.4)
        body = self.get("concepts/a.html")[1]
        self.assertNotIn("最新の内容を表示できていない", body)

    def test_schema_removed_while_serving_is_503(self):
        """要求のたびに初期化を確かめる（ADR-0019）。起動のあとで SCHEMA.md が消えたら、前の中核でも答えない。"""
        self.assertIn("本文 1", self.get("concepts/a.html")[1])
        schema = self.wiki / "SCHEMA.md"
        original = schema.read_bytes()
        schema.unlink()
        code, body, headers = self.get("concepts/a.html")
        self.assertEqual(code, 503)
        self.assertIn("初期化された wiki ではない", body)
        self.assertIn("/wiki:init", body)
        self.assertNotIn("本文 1", body)
        self.assertIn("Retry-After", headers)
        code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/b")
        self.assertEqual(json.loads(body)["state"], "unavailable")
        schema.write_bytes(original)
        time.sleep(0.4)
        code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertIn("本文 1", body)

    def test_uncertain_check_builds_nothing(self):
        """判定が「調べられない」（アクセス権、循環するリンクなど）を返したときは、新しい中核を組み立てない。
        前の中核がなければ 503、あれば前の内容を古いと示して出し、wiki の変更を取り込まない。"""
        uncertain = wiki_browse.initialized.Finding("marker_unreadable", "調べられない")
        self.assertFalse(uncertain.certain)
        with mock.patch.object(wiki_browse.initialized, "check", return_value=uncertain):
            code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 503)
        self.assertNotIn("本文 1", body)
        self.assertIsNone(self.app.state.current)
        self.assertIn("本文 1", self.get("concepts/a.html")[1])
        write(self.wiki, "concepts/a.md", '---\ntype: "concept"\n---\n# A\n\n本文 2 が新しい。\n')
        with mock.patch.object(wiki_browse.initialized, "check", return_value=uncertain):
            code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertIn("本文 1", body)
        self.assertNotIn("本文 2", body)
        self.assertIn("最新の内容を表示できていない", body)
        self.assertIn("本文 2", self.get("concepts/a.html")[1])

    def test_first_build_failure_is_503_but_control_works(self):
        with mock.patch.object(core, "Core", side_effect=RuntimeError("x")):
            code, _body, headers = self.get("index.html")
            self.assertEqual(code, 503)
            self.assertIn("Retry-After", headers)
            code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/status")
            self.assertEqual(json.loads(body)["instance"], self.app.instance)
            code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/b")
            self.assertEqual(json.loads(body)["state"], "unavailable")

    def test_failed_reason_persists_during_retry_interval(self):
        self.get("concepts/a.html")
        with mock.patch.object(core, "Core", side_effect=RuntimeError("x")), \
                mock.patch.object(wiki_browse, "RETRY_INTERVAL", 30):
            write(self.wiki, "concepts/a.md", "# 壊れた 1\n")
            first = self.get("concepts/a.html")[1]
            second = self.get("concepts/a.html")[1]
        for body in (first, second):
            self.assertIn("組み立てに失敗した", body)

    def test_wait_timeout_over_http(self):
        real = core.Core
        gate = threading.Event()

        def slow(*a, **k):
            gate.wait(10)
            return real(*a, **k)
        with mock.patch.object(wiki_browse, "BUILD_WAIT", 0.3), mock.patch.object(core, "Core", side_effect=slow):
            first = threading.Thread(target=self.get, args=("index.html",))
            first.start()
            time.sleep(0.2)
            code, _body, headers = self.get("index.html")   # 最初の組み立てを待ちきれない
            self.assertEqual(code, 503)
            self.assertIn("Retry-After", headers)
            gate.set()
            first.join()
            gate.clear()
            write(self.wiki, "concepts/a.md", "# A\n\n本文 4。\n")
            second = threading.Thread(target=self.get, args=("concepts/a.html",))
            second.start()
            time.sleep(0.2)
            code, body, _h = self.get("concepts/a.html")   # 前の中核で、古いと示して答える
            self.assertEqual(code, 200)
            self.assertIn("最新の内容を表示できていない", body)
            gate.set()
            second.join()

    def test_concurrent_requests_build_once(self):
        self.get("index.html")
        real = core.Core
        count = {"n": 0}

        def counting(*a, **k):
            count["n"] += 1
            time.sleep(0.3)
            return real(*a, **k)
        results = []

        def fetch():
            code, body, _h = self.get("concepts/a.html")
            gen = body.split('data-generation="', 1)[1].split('"', 1)[0] if 'data-generation="' in body else None
            results.append((code, "本文 5" in body, gen))
        with mock.patch.object(core, "Core", side_effect=counting):
            write(self.wiki, "concepts/a.md", "# A\n\n本文 5。\n")
            threads = [threading.Thread(target=fetch) for _ in range(5)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
        self.assertEqual(count["n"], 1)
        # どの応答も、成功し、新しい 1 つの世代の内容だけでできている
        self.assertEqual([r[0] for r in results], [200] * 5)
        self.assertTrue(all(r[1] for r in results))
        self.assertEqual(len({r[2] for r in results}), 1)
        nav = self.get("nav.js")[1]
        self.assertIn(f'"generation":"{results[0][2]}"', nav)

    def test_unreadable_ontology_and_index_recover(self):
        write(self.wiki, "graph/ontology.yaml", "node_types: {concept: {}}\npredicates: {}\n")
        write(self.wiki, "index.md", "# 索引\n\n- [[a]]\n")
        targets = {self.wiki / "graph/ontology.yaml", self.wiki / "index.md"}
        real = Path.read_bytes
        busy = {"on": True}

        def flaky(self_):
            if busy["on"] and Path(self_) in targets:
                raise PermissionError("busy")
            return real(self_)
        with reads_via(flaky):
            body = self.get("concepts/a.html")[1]
            self.assertIn("オントロジーを読めない", body)
            busy["on"] = False
            time.sleep(0.4)
            body = self.get("concepts/a.html")[1]
            self.assertNotIn("オントロジーを読めない", body)
            self.assertIn('"label":"a"', self.get("nav.js")[1])

    def test_unlistable_directory_keeps_previous_core(self):
        self.assertEqual(self.get("concepts/a.html")[0], 200)
        real = os.scandir

        def denied(path="."):
            if Path(path) == self.wiki:
                raise PermissionError("denied")
            return real(path)
        with mock.patch.object(os, "scandir", denied):
            code, body, _h = self.get("concepts/a.html")
            self.assertEqual(code, 200)                         # 0 ページに切り替えない
            self.assertIn("最新の内容を表示できていない", body)
            manifest = self.get("data/manifest.js")[1]
            self.assertNotIn('"pages":0', manifest)
        time.sleep(0.4)
        self.assertNotIn("最新の内容を表示できていない", self.get("concepts/a.html")[1])

    def test_manifest_has_generated_at(self):
        manifest = self.get("data/manifest.js")[1]
        self.assertNotIn('"generated_at":""', manifest)

    def test_signature_failure_is_stale_not_500(self):
        self.assertEqual(self.get("concepts/a.html")[0], 200)
        with mock.patch.object(core, "signature", side_effect=PermissionError("x")):
            code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertIn("最新の内容を表示できていない", body)
        time.sleep(0.4)
        code, body, _h = self.get("concepts/a.html")
        self.assertEqual(code, 200)
        self.assertNotIn("最新の内容を表示できていない", body)

    def test_wait_timeout_is_stale(self):
        self.get("concepts/a.html")
        real = core.Core
        gate = threading.Event()

        def slow(*a, **k):
            gate.wait(5)
            return real(*a, **k)
        with mock.patch.object(wiki_browse, "BUILD_WAIT", 0.3), mock.patch.object(core, "Core", side_effect=slow):
            write(self.wiki, "concepts/a.md", "# A\n\n本文 3。\n")
            first = threading.Thread(target=self.get, args=("concepts/a.html",))
            first.start()
            time.sleep(0.2)
            # BUILD_WAIT は既定の引数に入っているので、待つ時間を直接短くする
            c, stale = self.app.state.get(wait=0.3)
            self.assertIsNotNone(c)
            self.assertEqual(stale, "building")
            gate.set()
            first.join()
        self.assertIn("本文 3", self.get("concepts/a.html")[1])

    def test_unreadable_page_recovers_without_change(self):
        target = self.wiki / "concepts" / "b.md"
        real = Path.read_bytes
        busy = {"on": True}

        def flaky(self_):
            if busy["on"] and Path(self_) == target:
                raise PermissionError("busy")
            return real(self_)
        with reads_via(flaky):
            self.assertEqual(self.get("concepts/b.html")[0], 404)
            busy["on"] = False
            time.sleep(0.4)
            self.assertEqual(self.get("concepts/b.html")[0], 200)

    def test_core_holds_no_recorder(self):
        # 利用者が書いたかの推定（Recorder）をなくした（構造の直しの設計の 8）
        self.get("concepts/a.html")
        self.assertFalse(hasattr(self.app.state.current, "recorder"))


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>x()</script></svg>\n'


class SvgServeTest(InProcess):
    """図の svg を配る（図の描画の設計の 6.5）。"""

    def setUp(self):
        super().setUp()
        self._retry = mock.patch.object(wiki_browse, "RETRY_INTERVAL", 0.3)
        self._retry.start()
        (self.wiki / "assets").mkdir()
        (self.wiki / "assets" / "a-01.svg").write_bytes(SVG)
        write(self.wiki, "concepts/f.md", "# F\n\n![図](../assets/a-01.svg)\n")

    def tearDown(self):
        self._retry.stop()
        super().tearDown()

    def svg_name(self) -> str:
        return core.Core(core.take_snapshot(self.wiki)).asset_out["assets/a-01.svg"]

    def test_svg_is_served_with_sandbox_csp(self):
        body = self.get("concepts/f.html")[1]
        name = self.svg_name()
        self.assertIn(f'src="../{name}"', body)
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.putrequest("GET", self.prefix + name, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", f"127.0.0.1:{self.port}")
            conn.endheaders()
            res = conn.getresponse()
            data, headers = res.read(), dict(res.getheaders())
        finally:
            conn.close()
        self.assertEqual(res.status, 200)
        self.assertEqual(data, SVG)
        self.assertEqual(headers["Content-Type"], "image/svg+xml")
        self.assertEqual(headers["Content-Security-Policy"], core.CSP_SVG)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cache-Control"], "no-store")
        code, _b, headers = self.get(name, "HEAD")
        self.assertEqual((code, headers["Content-Length"]), (200, str(len(SVG))))
        # ページの応答の CSP は今までと同じ
        self.assertEqual(self.get("concepts/f.html")[2]["Content-Security-Policy"], core.CSP)

    def test_unknown_svg_name_is_404(self):
        self.assertEqual(self.get("assets/wiki/0000000000000000.svg")[0], 404)
        self.assertEqual(self.get("assets/wiki/../app.js")[0], 404)

    def test_svg_change_is_served_on_next_request(self):
        name = self.svg_name()
        self.assertEqual(self.get(name)[0], 200)
        bigger = SVG.replace(b"x()", b"y(); z()")
        (self.wiki / "assets" / "a-01.svg").write_bytes(bigger)
        self.assertEqual(self.get(name)[1].encode("utf-8"), bigger)


class FrameServeTest(InProcess):
    """Mermaid の図の枠の同梱物を、トークンなしの /_frame/<版>/ から配る（図の描画の設計の 7.2、7.3）。"""

    def setUp(self):
        super().setUp()
        self.app.frame_assets = core.load_frame_assets()
        self.base = f"/{core.FRAME_PREFIX}/{core.FRAME_VERSION}/"

    def raw(self, method: str, path: str) -> tuple:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", f"127.0.0.1:{self.port}")
            conn.endheaders()
            res = conn.getresponse()
            return res.status, res.read(), dict(res.getheaders())
        finally:
            conn.close()

    def test_frame_files_are_served_without_token(self):
        for name in core.FRAME_ASSETS:
            code, body, headers = self.raw("GET", self.base + name)
            self.assertEqual(code, 200, name)
            self.assertEqual(body, (SCRIPTS / "browse_assets" / name).read_bytes(), name)
            self.assertEqual(headers["Cache-Control"], "private, max-age=86400", name)
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff", name)
            if name.endswith(".html"):
                self.assertTrue(headers["Content-Type"].startswith("text/html"))
                self.assertEqual(headers["Content-Security-Policy"], core.frame_csp(self.port))
            else:
                self.assertTrue(headers["Content-Type"].startswith("text/javascript"))
                self.assertEqual(headers["Content-Security-Policy"], core.CSP)
        code, _b, headers = self.raw("HEAD", self.base + "mermaid-frame.html")
        self.assertEqual((code, headers["Content-Length"]), (200, str(len(self.app.frame_assets["mermaid-frame.html"]))))

    def test_other_paths_are_404_and_never_redirect(self):
        for path in (f"/{core.FRAME_PREFIX}/mermaid-0.0.0-0/mermaid.tiny.js", self.base + "app.js",
                     self.base + "style.css", self.base + "../mermaid.tiny.js", self.base + "%2e%2e/x",
                     f"/{core.FRAME_PREFIX}/{core.FRAME_VERSION}", f"/{core.FRAME_PREFIX}/{core.FRAME_VERSION}/",
                     self.base + "mermaid-frame.html/x", f"/{core.FRAME_PREFIX}/{core.FRAME_VERSION}/data/search.js"):
            code, _b, headers = self.raw("GET", path)
            self.assertEqual(code, 404, path)
            self.assertNotIn("Location", headers, path)
        self.assertEqual(self.raw("POST", self.base + "mermaid-frame.html")[0], 405)
        code, _b, _h = request(self.port, "GET", self.base + "mermaid-frame.html", host="localhost")
        self.assertEqual(code, 421)

    def test_page_csp_allows_only_same_origin_frames(self):
        _code, _body, headers = self.get("concepts/a.html")
        self.assertEqual(headers["Content-Security-Policy"], core.CSP)
        self.assertIn("frame-src 'self'", headers["Content-Security-Policy"])

    def test_server_figures_require_a_top_level_local_navigation(self):
        for mode, dest, site, allowed in (
            ("navigate", "document", "none", True),
            ("navigate", "document", "same-origin", True),
            ("navigate", "document", "same-site", False),
            ("navigate", "document", "cross-site", False),
            ("navigate", "iframe", "same-origin", False),
            ("cors", "document", "same-origin", False),
            (None, None, None, False),
        ):
            with self.subTest(mode=mode, dest=dest, site=site):
                navigation = {"Sec-Fetch-Mode": mode, "Sec-Fetch-Dest": dest, "Sec-Fetch-Site": site}
                code, body, headers = request(self.port, "GET", self.prefix + "concepts/a.html",
                                              headers={name: value for name, value in navigation.items() if value})
                self.assertEqual(code, 200)
                self.assertEqual("assets/figures.js" in body, allowed)
                self.assertEqual(headers["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertEqual(self.get("index.html")[2]["Cross-Origin-Opener-Policy"], "same-origin")


class ServeScopeTest(Base):
    """serve の出力の scope と、そのサーバーが描くスコープ（BrowseState.scope）の一致。

    実際の serve() を試験のプロセスの中で動かし、最初の組み立てに失敗しているあいだの、新しく起動したときと
    使い回したときの出力を確かめる。出力は wiki_browse の print を差し替えて集める（裏のスレッドの出力も取れる）。
    """

    def setUp(self):
        super().setUp()
        self.lines: list = []
        self.thread = None
        self._print = mock.patch.object(wiki_browse, "print", create=True, new=self._capture)
        self._print.start()

    def tearDown(self):
        if self.thread is not None and self.thread.is_alive():
            wiki_browse.stop(self.wiki)
            self.thread.join(30)
        self._print.stop()
        super().tearDown()

    def _capture(self, *args, file=None, **_kwargs):
        if file is None:   # 標準エラーへの文（say）は集めない
            self.lines.append(" ".join(map(str, args)))

    def start(self, scope) -> dict:
        """新しいサーバーを裏のスレッドで起動し、起動の出力を返す。"""
        self.thread = threading.Thread(target=wiki_browse.serve, args=(self.wiki, None, False, 60),
                                       kwargs={"scope": scope}, daemon=True)
        self.thread.start()
        return self.emitted(1)

    def reuse(self, scope) -> dict:
        self.assertEqual(wiki_browse.serve(self.wiki, None, False, 60, scope=scope), wiki_browse.EXIT_OK)
        return self.emitted(2)

    def emitted(self, n: int) -> dict:
        deadline = time.monotonic() + 30
        while len(self.lines) < n and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertGreaterEqual(len(self.lines), n, "起動の出力がない")
        return json.loads(self.lines[n - 1])

    def view(self, out: dict) -> tuple:
        port = out["port"]
        return request(port, "GET", out["url"].split(str(port), 1)[1])

    def test_output_is_the_scope_drawn_once_built_even_while_the_first_build_fails(self):
        with mock.patch.object(core, "Core", side_effect=RuntimeError("x")):
            new = self.start("project")
            code, body, _ = self.view(new)
            self.assertEqual(code, 503)                    # wiki のページも、スコープの表示も描かない
            self.assertNotIn('id="_scope"', body)
            reused = self.reuse("user")
        self.assertEqual((new["reused"], new["scope"]), (False, "project"))
        # 使い回したときも、今回の指定（user）ではなく、動いているサーバーが描くスコープを書く。
        self.assertEqual((reused["reused"], reused["scope"]), (True, "project"))
        with mock.patch.object(wiki_browse, "RETRY_INTERVAL", 0.0):   # 失敗のあとの待ちを飛ばす
            code, body, _ = self.view(new)
        self.assertEqual(code, 200)                        # 組み立てられたら、出力のスコープを描く
        self.assertIn('<p id="_scope" class="scope scope-project">', body)

    def test_server_keeps_one_normalized_scope(self):
        # コマンドラインを通さずに正しくない値を渡しても、出力、操作の口、ページは同じもの（出さない）になる。
        new = self.start("global")
        self.assertIsNone(new["scope"])
        code, body, _ = self.view(new)
        self.assertEqual(code, 200)
        self.assertNotIn('id="_scope"', body)
        self.assertIsNone(self.reuse("project")["scope"])


class MarkersTest(unittest.TestCase):
    """Wiki、ホーム、data_dir、Wiki の外の入力を別々の目印の場所にして、サーバーの応答と記録に出ないことを確かめる。"""

    def test_markers_absent_from_server(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            wiki, home, ext, data = (base / n for n in ("WIKIMARK", "HOMEMARK", "EXTMARK", "DATAMARK"))
            for x in (wiki, home, ext):
                x.mkdir()
            write(wiki, "concepts/a.md", '---\ntype: "source"\nraw: "~/papers/x.pdf"\n---\n# A\n\n[[b]] [[missing]]\n')
            write(wiki, "concepts/b.md", "# B\n")
            write(wiki, "index.md", "- [[a]]\n")
            write(ext, "outside.md", "# 外\n")
            marks = ["WIKIMARK", "HOMEMARK", "EXTMARK", "DATAMARK"]
            try:
                os.symlink(ext / "outside.md", wiki / "concepts" / "outside.md")
            except (OSError, NotImplementedError):
                marks.remove("EXTMARK")
            log = io.StringIO()
            with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": str(data)}), \
                    mock.patch.object(Path, "home", return_value=home), redirect_stderr(log):
                app = wiki_browse.App(wiki, idle=600, verbose=True, assets=core.load_assets())
                httpd = wiki_browse._Server(("127.0.0.1", 0), wiki_browse.Handler)
                httpd.app = app
                app.httpd = httpd
                app.port = httpd.server_address[1]
                th = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
                th.start()
                try:
                    prefix = f"/{app.view_token}/w/{app.key}/"
                    paths = [prefix + n for n in ("index.html", "nav.js", "data/manifest.js", "data/diagnostics.js",
                                                  "concepts/a.html", "concepts/outside.html", "concepts/nope.html",
                                                  "%2e%2e/x")]
                    paths += [f"/{app.control_token}/control/status", f"/{app.control_token}/control/locate/a", "/x"]
                    bodies = [request(app.port, "GET", p)[1] for p in paths]
                    bodies.append(request(app.port, "GET", prefix + "index.html", host="x")[1])
                finally:
                    httpd.shutdown()
                    httpd.server_close()
            for text in bodies + [log.getvalue()]:
                for mark in marks:
                    self.assertNotIn(mark, text)


class ProcessTest(Base):
    """実際のプロセスで確かめる。"""

    def serve(self, *args) -> subprocess.Popen:
        proc = subprocess.Popen([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_browse.py"), "serve",
                                 str(self.wiki), "--no-open", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=self.env, text=True, encoding="utf-8")
        self.procs.append(proc)
        return proc

    def setUp(self):
        super().setUp()
        self.procs = []

    def first_line(self, proc) -> dict:
        line = proc.stdout.readline()
        self.assertTrue(line, proc.stderr.read() if proc.poll() is not None else "出力がない")
        return json.loads(line)

    def stop(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_browse.py"), "stop", str(self.wiki)],
                              capture_output=True, text=True, encoding="utf-8", env=self.env, timeout=60)

    def state_dir(self) -> Path:
        import wiki_mcp_common as common
        return self.data / "browse" / f"{common.wiki_key(self.wiki)}.server"

    def tearDown(self):
        self.stop()
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
            proc.wait(30)
            proc.stdout.close()
            proc.stderr.close()
        super().tearDown()

    def test_concurrent_serves_share_one_server_and_stop(self):
        a, b = self.serve(), self.serve()
        try:
            ra, rb = self.first_line(a), self.first_line(b)
            self.assertEqual(ra["port"], rb["port"])
            self.assertEqual(sorted([ra["reused"], rb["reused"]]), [False, True])
            running = a if not ra["reused"] else b
            other = b if running is a else a
            self.assertEqual(other.wait(30), 0)
            res = self.stop()
            self.assertEqual(json.loads(res.stdout)["stopped"], True, res.stderr)
            self.assertEqual(running.wait(30), 0)
            self.assertFalse((self.state_dir() / "server.json").exists())
        finally:
            for p in (a, b):
                if p.poll() is None:
                    p.kill()

    def screen(self, r: dict) -> str:
        port = r["port"]
        code, body, _ = request(port, "GET", r["url"].split(str(port), 1)[1])
        self.assertEqual(code, 200)
        return body

    def test_raw_category_uses_first_tag_other_than_raw_and_reloads(self):
        raw = self.base / "raw"
        write(raw, "own.md", '---\ntags: ["最初", "raw", "次"]\n---\n# 原本\n\n原本の本文。\n')
        inherited = write(raw, "nested/inherited.md", "# ソースのタグを使う原本\n")
        write(raw, "single.md", '---\ntags: ["一つだけ"]\n---\n# タグが一つの原本\n')
        write(raw, "prefixed.md", '---\ntags: ["raw", "具体的", "補助"]\n---\n# 分類用のタグがある原本\n')
        write(raw, "raw-only.md", '---\ntags: ["RAW", "ｒａｗ"]\n---\n# 分類用のタグがない原本\n')
        marker = write(raw, "source-tag-only.md", '---\ntags: ["raw"]\n---\n# ソースから分類する原本\n')
        write(raw, "assets/caption.md", "# アセット\n")
        write(self.wiki, "sources/summary.md",
              '---\ntype: "source"\n'
              f'raw: ["{inherited.as_posix()}", "{marker.as_posix()}"]\ntags: ["分類", "継承"]\n---\n# 要約\n')
        r = self.first_line(self.serve("--raw-root", str(raw)))
        port = r["port"]
        base = r["url"].split(str(port), 1)[1].removesuffix("index.html")

        def groups():
            status, body, _ = request(port, "GET", base + "nav.js")
            self.assertEqual(status, 200)
            return json.loads(body.split("=", 1)[1].strip().removesuffix(";"))["groups"]

        def raw_group():
            return next(g for g in groups() if g["title"] == "raw")

        self.assertEqual({g["title"]: [it["id"] for it in g["items"]] for g in raw_group()["children"]},
                         {"最初": ["raw/own"], "分類": ["raw/nested/inherited", "raw/source-tag-only"], "一つだけ": ["raw/single"],
                          "具体的": ["raw/prefixed"], "タグなし": ["raw/raw-only"]})
        rest = next(g for g in groups() if g["title"] == "Index にないページ")
        source = next(g for g in rest["children"] if g["title"] == "ソース")
        self.assertEqual([g["title"] for g in source["children"]], ["分類"])
        self.assertIn('data-type="raw"', self.screen(r))
        status, summary, _ = request(port, "GET", base + "sources/summary.html")
        self.assertEqual(status, 200)
        self.assertIn(f'href="../raw/nested/inherited.html"><code>{html.escape(inherited.as_posix())}', summary)
        status, body, _ = request(port, "GET", base + "raw/own.html")
        self.assertEqual(status, 200)
        self.assertIn("原本の本文。", body)

        write(raw, "own.md", '---\ntags: ["raw", "更新したグループ"]\n---\n# 更新\n')
        self.assertIn("更新したグループ", [g["title"] for g in raw_group()["children"]])
        other = self.serve("--raw-root", str(self.base / "other"))
        self.assertNotEqual(other.wait(30), 0)
        self.assertIn("raw の設定が異なる", other.stderr.read())

    def test_source_opens_raw_markdown_in_viewer(self):
        raw_root = self.base / "raw"
        raw = write(raw_root, "nested/日本語 raw.md", "# 原本\n\n日本語で保存した記事の本文。\n")
        outside = write(self.base, "other/nested/日本語 raw.md", "# 範囲外の本文\n")
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        home = "USERPROFILE" if os.name == "nt" else "HOME"
        self.env[home] = str(self.base)
        available = [raw.as_posix(), raw.as_uri(), "~/raw/nested/日本語 raw.md", "../raw/nested/日本語 raw.md"]
        excluded = [outside.as_posix(), f"{raw_root.as_posix()}/alt/../nested/日本語 raw.md",
                    "../raw/alt/../nested/日本語 raw.md"]
        if os.name == "nt":
            available.append(str(raw)[0].swapcase() + str(raw)[1:])
            other_drive = "D:" if raw.drive.upper() == "C:" else "C:"
            excluded.append(other_drive + raw.as_posix()[2:])
        all_refs = json.dumps(available + excluded, ensure_ascii=False)
        matching_hashes = json.dumps([digest] * (len(available) + len(excluded)))
        summary = write(self.wiki, "sources/summary.md",
                        "---\ntype: \"source\"\n"
                        f"raw: {all_refs}\nraw_sha256: {matching_hashes}\n---\n# 要約\n")
        opened = self.first_line(self.serve("--raw-root", str(raw_root), "--page", "summary"))
        route = "../raw/nested/%E6%97%A5%E6%9C%AC%E8%AA%9E%20raw.html"
        page = self.screen(opened)
        self.assertIn(f'<a href="{route}"><code>{html.escape(raw.as_posix())}</code></a>', page)
        self.assertIn(f'<td class="fui-TableCell"><a href="{route}">', page)
        self.assertEqual(page.count(f'<a href="{route}"><code>'), len(available))
        for ref in excluded:
            self.assertIn(f'<br><code>{html.escape(ref)}</code>', page)
        target = urlsplit(urljoin(opened["url"], route)).path
        status, body, _ = request(opened["port"], "GET", target)
        self.assertEqual(status, 200)
        self.assertIn("日本語で保存した記事の本文。", body)
        self.assertNotIn("範囲外の本文", body)

        original = summary.read_text(encoding="utf-8")
        for hashes in (matching_hashes.replace(digest, "0" * 64), json.dumps([digest]), '"不正な SHA-256"'):
            with self.subTest(hashes=hashes):
                summary.write_text(original.replace(matching_hashes, hashes), encoding="utf-8")
                changed = self.screen(opened)
                self.assertNotIn(f'<a href="{route}"><code>', changed)
                self.assertIn(f'<code>{html.escape(raw.as_posix())}</code>', changed)

    def test_session_source_resolves_raw_relative_to_wiki_parent(self):
        raw_root = self.wiki / "raw"
        write(raw_root, "session.md", "# 会話の本文\n")
        write(self.wiki, "sources/session.md",
              '---\ntype: "source"\nsession_id: "test"\nraw: ["wiki/raw/session.md", "raw/session.md"]\n---\n# 要約\n')
        opened = self.first_line(self.serve("--raw-root", str(raw_root), "--page", "session"))
        page = self.screen(opened)
        self.assertIn('<a href="../raw/session.html"><code>wiki/raw/session.md</code></a>', page)
        self.assertIn('<br><code>raw/session.md</code>', page)

    def test_serve_reports_the_scope_the_server_draws(self):
        a = self.serve("--scope", "project")
        ra = self.first_line(a)
        self.assertEqual((ra["reused"], ra["scope"]), (False, "project"))
        self.assertNotIn("scope_name", ra)
        self.assertIn('<p id="_scope" class="scope scope-project">', self.screen(ra))
        self.assertIn("<title>Index · プロジェクト</title>", self.screen(ra))
        # 使い回したときは、今回の指定ではなく、ページを描くサーバーが操作の口で答えたスコープを書く。
        # 記録のファイルは画面を描かないので、記録にスコープを書き足しても使わない。
        record = self.state_dir() / "server.json"
        rec = json.loads(record.read_text(encoding="utf-8"))
        self.assertNotIn("scope", rec)
        record.write_text(json.dumps({**rec, "scope": "user"}), encoding="utf-8")
        b = self.serve("--scope", "user")
        rb = self.first_line(b)
        self.assertEqual((rb["reused"], rb["scope"]), (True, "project"))
        self.assertEqual(b.wait(30), 0)
        code, body, _ = request(ra["port"], "GET", f"/{rec['control_token']}/control/status")
        self.assertEqual(json.loads(body)["scope"], "project")

    def test_serve_without_scope_reports_none_even_when_reused_with_one(self):
        a = self.serve()
        ra = self.first_line(a)
        self.assertIsNone(ra["scope"])
        self.assertNotIn('id="_scope"', self.screen(ra))
        b = self.serve("--scope", "user")
        rb = self.first_line(b)
        self.assertTrue(rb["reused"])
        self.assertIsNone(rb["scope"])
        self.assertEqual(b.wait(30), 0)

    def test_bad_scope_is_a_usage_error(self):
        proc = self.serve("--scope", "global")
        self.assertEqual(proc.wait(30), 2)
        self.assertFalse((self.state_dir() / "server.json").exists())

    def test_tokens_change_on_restart_and_page_states(self):
        p1 = self.serve("--page", "b")
        r1 = self.first_line(p1)
        self.assertEqual(r1["page"], "resolved")
        self.assertTrue(r1["url"].endswith("/concepts/b.html"))
        self.stop()
        p1.wait(30)
        p2 = self.serve("--page", "missing")
        r2 = self.first_line(p2)
        self.assertEqual(r2["page"], "unresolved")
        self.assertTrue(r2["url"].endswith("/index.html"))
        self.assertNotEqual(r1["url"].split("/")[3], r2["url"].split("/")[3])
        self.stop()
        p2.wait(30)

    def test_idle_timeout(self):
        p = self.serve("--idle-timeout", "1.5")
        self.first_line(p)
        self.assertEqual(p.wait(30), 0)
        self.assertFalse((self.state_dir() / "server.json").exists())

    def test_serve_waits_while_stop_holds_the_lock(self):
        lock = state_lock(self.wiki)
        self.assertTrue(lock.try_acquire())
        p = self.serve()
        time.sleep(1.0)
        lock.release()
        r = self.first_line(p)
        self.assertFalse(r["reused"])

    def test_stop_does_not_stop_a_different_instance(self):
        p = self.serve()
        r = self.first_line(p)
        rec_path = self.state_dir() / "server.json"
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec["instance"] = "0" * 24
        rec_path.write_text(json.dumps(rec), encoding="utf-8")
        res = self.stop()
        self.assertNotEqual(res.returncode, 0)
        self.assertIsNone(p.poll())   # 止めていない
        self.assertEqual(request(r["port"], "GET", "/x")[0], 404)
        p.kill()
        p.wait(30)

    def test_two_concurrent_stops(self):
        p = self.serve()
        self.first_line(p)
        cmd = [sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_browse.py"), "stop", str(self.wiki)]
        stops = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env, text=True,
                                  encoding="utf-8") for _ in range(2)]
        outs = [s.communicate(timeout=60) for s in stops]
        self.assertEqual([s.returncode for s in stops], [0, 0], outs)
        self.assertEqual(p.wait(30), 0)
        self.assertFalse((self.state_dir() / "server.json").exists())

    def test_stop_while_starting_waits_for_record(self):
        p = self.serve("--page", "a")
        # サーバーがロックを取った（起動の途中に入った）ことを確かめてから止める。
        lock_path = os.path.join(wiki_browse._state_dir(self.wiki), "server.lock")
        deadline = time.monotonic() + 30
        # 何も作らずに確かめる（stop と同じ口）
        while not (os.path.exists(lock_path) and fs.lock_held(lock_path)):
            self.assertLess(time.monotonic(), deadline, "サーバーがロックを取らない")
            time.sleep(0.05)
        res = self.stop()
        self.assertEqual(res.returncode, 0, res.stderr)
        p.wait(30)

    @unittest.skipUnless(os.name == "posix", "POSIX の権限")
    def test_permissions(self):
        p = self.serve()
        self.first_line(p)
        self.assertEqual(self.state_dir().stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.state_dir() / "server.json").stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(os.name == "nt", "ジャンクションは Windows だけ")
    def test_state_dir_junction_into_wiki_is_refused(self):
        import _winapi
        (self.data / "browse").mkdir(parents=True)
        _winapi.CreateJunction(str(self.wiki), str(self.state_dir()))
        before = sorted(p.name for p in self.wiki.rglob("*"))
        p = self.serve()
        self.assertNotEqual(p.wait(30), 0)
        self.assertEqual(sorted(p.name for p in self.wiki.rglob("*")), before)

    @unittest.skipUnless(os.name == "nt", "Windows の警告")
    def test_warning_when_data_dir_is_set(self):
        p = self.serve()
        self.first_line(p)
        self.stop()
        p.wait(30)
        self.assertIn("INFO_HIVE_DATA_DIR", p.stderr.read())


if __name__ == "__main__":
    unittest.main()
