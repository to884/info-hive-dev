"""閲覧（browse）のサーバーの試験。

設計は `docs/plans/wiki-browse-stage1-2026-11-09.md` の 8（守ること 3、7、8、9）。要求の拒否、作り直し、
「古い」状態、操作の口は、試験のプロセスの中で動かすサーバーで確かめる。起動の競合、使い回し、停止、
操作がないときの終了は、実際のプロセス（`wiki_browse.py serve`）で確かめる。

実行:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse_server.py -v
"""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import wiki_browse  # noqa: E402
import wiki_browse_core as core  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def request(port: int, method: str, path: str, host: "str | None" = None) -> tuple:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    try:
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        conn.putheader("Host", host if host is not None else f"127.0.0.1:{port}")
        conn.endheaders()
        res = conn.getresponse()
        return res.status, res.read().decode("utf-8", errors="replace"), dict(res.getheaders())
    finally:
        conn.close()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.wiki = self.base / "wiki"
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
        with redirect_stderr(io.StringIO()):
            guard, state_dir = wiki_browse._prepare_state(self.wiki)
        self.app = wiki_browse.App(self.wiki, guard, state_dir, idle=600)
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

    def test_overlap_shuts_down_from_any_entry(self):
        self.get("concepts/a.html")
        write(self.wiki, "concepts/c.md", "# C\n")
        with mock.patch.object(self.app.state.guard, "overlapping", return_value=True):
            code, body, _h = request(self.port, "GET", f"/{self.app.control_token}/control/locate/a")
        self.assertEqual(code, 503)
        self.assertTrue(self.app.state.shutdown_requested)
        self.assertTrue(self.app._stopping.is_set())

    def test_headers(self):
        _code, _body, headers = self.get("concepts/a.html")
        self.assertEqual(headers["Content-Security-Policy"], core.CSP)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        code, body, headers = self.get("assets/app.js")
        self.assertEqual(code, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))

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

    def test_finish_keeps_record_pointed_by_a_page(self):
        record = self.app.state_dir / "server.json"
        record.write_text("{}", encoding="utf-8")
        try:
            os.symlink(record, self.wiki / "concepts" / "record.md")
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない")
        with redirect_stderr(io.StringIO()):
            code = wiki_browse._finish(self.wiki, self.app, self.app.guard, self.app.state_dir)
        self.assertEqual(code, wiki_browse.EXIT_FAILED)
        self.assertTrue(record.exists())

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
        with mock.patch.object(core, "Core", side_effect=counting):
            write(self.wiki, "concepts/a.md", "# A\n\n本文 5。\n")
            threads = [threading.Thread(target=self.get, args=("concepts/a.html",)) for _ in range(5)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
        self.assertEqual(count["n"], 1)

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
        with mock.patch.object(Path, "read_bytes", flaky):
            body = self.get("concepts/a.html")[1]
            self.assertIn("オントロジーを読めない", body)
            busy["on"] = False
            time.sleep(0.4)
            body = self.get("concepts/a.html")[1]
            self.assertNotIn("オントロジーを読めない", body)
            self.assertIn('"label":"a"', self.get("nav.js")[1])

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
        with mock.patch.object(Path, "read_bytes", flaky):
            self.assertEqual(self.get("concepts/b.html")[0], 404)
            busy["on"] = False
            time.sleep(0.4)
            self.assertEqual(self.get("concepts/b.html")[0], 200)

    def test_server_does_not_record(self):
        self.get("concepts/a.html")
        self.assertFalse(self.app.state.current.recorder.enabled)


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
        with redirect_stderr(io.StringIO()):
            guard, state_dir = wiki_browse._prepare_state(self.wiki)
        lock = fs.Lock(guard, state_dir / "server.lock")
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
        with redirect_stderr(io.StringIO()):
            guard, state_dir = wiki_browse._prepare_state(self.wiki)
        probe = fs.Lock(guard, state_dir / "server.lock")
        deadline = time.monotonic() + 30
        while probe.try_acquire():
            probe.release()
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
