"""wiki の MCP サーバーと stdio の中継の試験（ADR-0001、ADR-0012 の段階 1）。

中継は .mcp.json と同じく `uv run --script` で起動する。試験ごとに INFO_HIVE_DATA_DIR を一時ディレクトリにし、
埋め込みはテスト用のもの（INFO_HIVE_TEST_EMBEDDER=hash）にする。サーバーの依存を初めて取得するときは
数分かかる。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 -m unittest tests/wiki/test_mcp_server.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mcp_stdio import RELAY, ROOT, StdioClient, relay_command  # noqa: E402

CORPUS = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"
TOOLS = {"query", "get_page", "list_index", "index_chunks"}


class ServerCase(unittest.TestCase):
    idle = "120"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.wiki = self.root / "wiki"
        shutil.copytree(CORPUS, self.wiki)
        self.env = {"INFO_HIVE_DATA_DIR": str(self.data), "INFO_HIVE_TEST_EMBEDDER": "hash",
                    "INFO_HIVE_MCP_IDLE_SECONDS": self.idle}
        self.clients: list[StdioClient] = []
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        for client in self.clients:
            client.close(timeout=10)
        for process in self.server_processes():
            try:
                process.kill()
                process.wait(10)
            except psutil.Error:
                pass
        self.temp.cleanup()

    def client(self) -> StdioClient:
        client = StdioClient(relay_command(), self.env)
        self.clients.append(client)
        return client

    def info(self) -> dict | None:
        try:
            return json.loads((self.data / "server.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def server_processes(self) -> list[psutil.Process]:
        """この試験のデータの置き場所を使っている、サーバーの本体のプロセス。"""
        found = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                if not any(str(p).endswith("wiki_mcp_server.py") for p in process.info["cmdline"] or []):
                    continue
                if process.environ().get("INFO_HIVE_DATA_DIR") != str(self.data):
                    continue
            except psutil.Error:
                continue
            found.append(process)
        pids = {p.pid for p in found}
        # venv の起動用の python.exe は本体を子として起動する。子（本体）だけを数える。
        return [p for p in found if not any(c.pid in pids for c in p.children())]

    def ensure(self) -> dict:
        out = subprocess.run(["uv", "run", "--quiet", "--script", str(RELAY), "--ensure"], capture_output=True,
                             env={**os.environ, "PYTHONUTF8": "1", **self.env}, timeout=1800)
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8", "replace"))
        return self.info()


class SecurityTests(ServerCase):
    """ADR-0001 の 3 条件のうち、待ち受けのアドレス、トークン、Host ヘッダー。"""

    def post(self, port, headers):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "t", "version": "0"}}}).encode()
        request = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", data=body, method="POST", headers={
            "Content-Type": "application/json", "Accept": "application/json, text/event-stream", **headers})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.headers.get("content-type"), response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.headers.get("content-type"), error.read()

    def test_guards(self):
        info = self.ensure()
        port, token = info["port"], info["token"]
        good = {"Authorization": f"Bearer {token}", "Host": f"127.0.0.1:{port}"}
        self.assertEqual(self.post(port, {"Host": f"127.0.0.1:{port}"})[0], 401)
        self.assertEqual(self.post(port, {**good, "Authorization": "Bearer wrong"})[0], 401)
        self.assertEqual(self.post(port, {**good, "Host": f"evil.example:{port}"})[0], 421)
        self.assertEqual(self.post(port, {**good, "Host": f"localhost:{port}"})[0], 421)
        status, content_type, body = self.post(port, good)
        self.assertEqual(status, 200)
        # streamable HTTP の応答は SSE ではなく JSON にする（ADR-0012）。
        self.assertTrue(content_type.startswith("application/json"), content_type)
        self.assertEqual(json.loads(body)["result"]["serverInfo"]["name"], "info-hive-wiki")

    def test_listens_on_loopback_only(self):
        info = self.ensure()
        listening = [c for c in psutil.Process(info["pid"]).net_connections("tcp") if c.status == psutil.CONN_LISTEN]
        self.assertTrue(listening)
        self.assertEqual({c.laddr.ip for c in listening}, {"127.0.0.1"})
        addresses = {a.address for addrs in psutil.net_if_addrs().values() for a in addrs
                     if a.family == socket.AF_INET and not a.address.startswith("127.")}
        for address in addresses:
            with self.assertRaises(OSError):
                socket.create_connection((address, info["port"]), timeout=1).close()

    def test_server_json_has_no_other_secrets(self):
        info = self.ensure()
        self.assertEqual(set(info), {"port", "token", "pid", "version", "protocol", "started"})
        if os.name != "nt":
            self.assertEqual((self.data / "server.json").stat().st_mode & 0o077, 0)


class RelayTests(ServerCase):
    def test_concurrent_relays_start_one_server(self):
        clients = [self.client() for _ in range(4)]
        errors = []

        def run(client):
            try:
                client.initialize()
                self.assertEqual({t["name"] for t in client.tools()}, TOOLS)
                result = client.call("query", {"wiki": str(self.wiki), "query": "熱中症", "top": 3})
                self.assertTrue(result["results"])
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=run, args=(c,)) for c in clients]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertFalse(errors, errors)
        servers = self.server_processes()
        self.assertEqual(len(servers), 1, [p.pid for p in servers])
        self.assertEqual(servers[0].pid, self.info()["pid"])

    def test_server_outlives_relay_and_is_reused(self):
        first = self.client()
        first.initialize()
        first.call("list_index", {"wiki": str(self.wiki)})
        pid = self.info()["pid"]
        self.assertEqual(first.close(), 0)
        time.sleep(1)
        self.assertTrue(psutil.pid_exists(pid), "中継が終わったらサーバーも止まった")
        second = self.client()
        second.initialize()
        second.call("get_page", {"wiki": str(self.wiki), "page": "heatstroke"})
        self.assertEqual(self.info()["pid"], pid)
        self.assertEqual(len(self.server_processes()), 1)

    def test_relay_reconnects_after_server_stops(self):
        client = self.client()
        client.initialize()
        client.call("query", {"wiki": str(self.wiki), "query": "消費税"})
        old = self.info()["pid"]
        psutil.Process(old).kill()
        psutil.Process(old).wait(10) if psutil.pid_exists(old) else None
        result = client.call("query", {"wiki": str(self.wiki), "query": "消費税"})
        self.assertTrue(result["results"])
        self.assertNotEqual(self.info()["pid"], old)

    def test_call_survives_server_stopping_mid_call(self):
        """呼び出しの途中でサーバーが止まっても、中継がつなぎ直してやり直す（mcp 1.30 は応答を返さず待ち続ける）。"""
        client = self.client()
        client.initialize()
        client.tools()
        pid = self.info()["pid"]
        chunks = [{"id": f"c{i}", "doc": "d.pdf", "text": "所得税の確定申告 " * 30 + str(i), "tokens": ["所得", "税"]}
                  for i in range(20000)]
        killer = threading.Timer(2.0, lambda: psutil.Process(pid).kill())
        killer.start()
        result = client.call("index_chunks", {"collection": "t", "tokenizer": "x", "generation": 1, "chunks": chunks},
                             timeout=600)
        killer.join()
        self.assertEqual(result["rows"], 20000)
        self.assertNotEqual(self.info()["pid"], pid)
        self.assertTrue(any("やり直す" in line for line in client.stderr), client.stderr)

    def test_version_mismatch_restarts_server(self):
        info = self.ensure()
        info["version"] = "old"
        (self.data / "server.json").write_text(json.dumps(info), encoding="utf-8")
        renewed = self.ensure()
        self.assertNotEqual(renewed["pid"], info["pid"])
        self.assertFalse(psutil.pid_exists(info["pid"]) and psutil.Process(info["pid"]).is_running()
                         and psutil.Process(info["pid"]).status() != psutil.STATUS_ZOMBIE)

    def test_tool_errors_are_reported(self):
        client = self.client()
        client.initialize()
        with self.assertRaises(RuntimeError) as caught:
            client.call("get_page", {"wiki": str(self.wiki), "page": "../../SCHEMA"})
        self.assertIn("ページが見つからない", str(caught.exception))
        with self.assertRaises(RuntimeError):
            client.call("list_index", {"wiki": str(self.wiki), "name": "../SCHEMA.md"})
        with self.assertRaises(RuntimeError):
            client.call("query", {"wiki": str(self.root / "ない"), "query": "x"})


class IdleTests(ServerCase):
    idle = "4"

    def test_idle_shutdown_with_relay_still_open(self):
        client = self.client()
        client.initialize()
        client.call("query", {"wiki": str(self.wiki), "query": "熱中症"})
        pid = self.info()["pid"]
        # 埋め込みが裏で終わり、要求がない状態が 4 秒続けば止まる。中継が開いたままの GET の流れは数えない。
        ends = time.monotonic() + 60
        while psutil.pid_exists(pid) and time.monotonic() < ends:
            time.sleep(0.5)
        self.assertFalse(psutil.pid_exists(pid), "要求がなくなってもサーバーが止まらなかった")
        self.assertIsNone(self.info())
        # 同じ中継から呼べば、サーバーを起動し直してつなぎ直す。
        result = client.call("query", {"wiki": str(self.wiki), "query": "熱中症"})
        self.assertTrue(result["results"])
        self.assertNotEqual(self.info()["pid"], pid)


if __name__ == "__main__":
    unittest.main()
