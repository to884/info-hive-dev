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
from mcp_stdio import LAUNCH, RELAY, ROOT, StdioClient, relay_command  # noqa: E402

CORPUS = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
TEMPLATE = ROOT / "info-hive-wiki/skills/info-hive/assets/ontology.yaml.template"
TOOLS = {"query", "get_page", "list_index", "lint", "stats", "graph", "index_chunks"}
sys.path.insert(0, str(SCRIPTS))
import wiki_graph_common  # noqa: E402


def run_cli(*args, script: bool = False) -> dict:
    """CLI を `--json` で実行して結果を返す。script が真なら PyYAML を使うので `uv run --script` で起動する。"""
    command = ["uv", "run", "--quiet", "--script"] if script else [sys.executable, "-X", "utf8"]
    out = subprocess.run([*command, *map(str, args)], capture_output=True, timeout=600,
                         env={**os.environ, "PYTHONUTF8": "1"})
    if out.returncode != 0:
        raise AssertionError(out.stderr.decode("utf-8", "replace"))
    return json.loads(out.stdout.decode("utf-8"))


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
        out = subprocess.run(["uv", "run", "--quiet", "--script", str(LAUNCH), "--ensure"], capture_output=True,
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

    @unittest.skipUnless(os.name == "nt", "Windows だけの試験")
    def test_server_gets_no_new_console_on_windows(self):
        """サーバーの本体に新しいコンソールが作られない（info-hive-wiki#36）。

        venv の python.exe（起動用）は本体を子として起動する。起動用がコンソールを持たないと（DETACHED_PROCESS）、
        本体に新しいコンソールが作られ、本体の子に conhost.exe が付き、画面が出る。窓のない自分のコンソール
        （CREATE_NO_WINDOW）で起動すれば、本体は起動用のコンソールを引き継ぎ、本体の子に conhost.exe は付かない。
        画面が実際に出るかは tests/wiki/check_server_console.py で確かめる。
        """
        server = psutil.Process(self.ensure()["pid"])
        consoles = [c.pid for c in server.children() if c.name().lower() == "conhost.exe"]
        self.assertEqual(consoles, [], "サーバーの本体に新しいコンソールが作られた")

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


class RepairTests(ServerCase):
    """uv の環境が作りかけで壊れていても、入口（wiki_mcp_launch.py）が入れ直して起動する。

    依存を入れている途中でホストに止められると、dist-info の METADATA が欠けた環境が残り、
    `uv run --script` が失敗し続ける（uv 0.12 の Windows で起きた）。モジュールの本体だけが欠けると、
    `uv sync` は成功するのに import に失敗する。中継の環境で、この 2 つの壊れ方を作る。
    サーバーの環境（約 1 GB）の入れ直しは時間がかかるので、ここでは試さない。
    """

    REINSTALL_LOG = "環境が作りかけで壊れているかもしれないので、入れ直す"

    def site_packages(self, script: Path) -> Path:
        env = {**os.environ, "PYTHONUTF8": "1"}
        subprocess.run(["uv", "sync", "--quiet", "--script", str(script)], check=True, capture_output=True,
                       env=env, timeout=1800)
        found = subprocess.run(["uv", "python", "find", "--script", str(script)], check=True, capture_output=True,
                               env=env, timeout=120)
        python = found.stdout.decode("utf-8").strip().splitlines()[-1]
        out = subprocess.run([python, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
                             check=True, capture_output=True, env=env, timeout=120)
        return Path(out.stdout.decode("utf-8").strip())

    def test_launcher_repairs_broken_relay_env(self):
        metadata = sorted(self.site_packages(RELAY).glob("*.dist-info/METADATA"))
        self.assertTrue(metadata)
        broken = metadata[0]
        broken.unlink()
        client = self.client()
        client.initialize(timeout=600)
        self.assertEqual({tool["name"] for tool in client.tools()}, TOOLS)
        self.assertTrue(broken.is_file(), "入口が中継の環境を入れ直していない")
        self.assertTrue(any("入れ直す" in line for line in client.stderr), client.stderr[-10:])

    def test_launcher_repairs_missing_module_body(self):
        """dist-info はそろっていて、モジュールの本体だけが欠けている。`uv sync` は成功する。"""
        broken = self.site_packages(RELAY) / "mcp" / "server" / "stdio.py"
        self.assertTrue(broken.is_file())
        broken.unlink()
        sync = subprocess.run(["uv", "sync", "--quiet", "--script", str(RELAY)], capture_output=True, timeout=600,
                              env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(sync.returncode, 0, "この壊れ方では uv sync が成功するはず")
        client = self.client()
        client.initialize(timeout=600)
        self.assertEqual({tool["name"] for tool in client.tools()}, TOOLS)
        self.assertTrue(broken.is_file(), "入口が中継の環境を入れ直していない")
        self.assertTrue(any("壊れているかもしれない" in line for line in client.stderr), client.stderr[-10:])
        self.assertTrue(any(self.REINSTALL_LOG in line for line in client.stderr), client.stderr[-10:])

    def test_launcher_repairs_missing_lazily_imported_module(self):
        """起動のときには import せず、実行中に初めて import するモジュールが欠けている（anyio のバックエンド）。"""
        broken = self.site_packages(RELAY) / "anyio" / "_backends" / "_asyncio.py"
        self.assertTrue(broken.is_file())
        broken.unlink()
        client = self.client()
        client.initialize(timeout=600)
        self.assertEqual({tool["name"] for tool in client.tools()}, TOOLS)
        self.assertTrue(broken.is_file(), "入口が中継の環境を入れ直していない")
        self.assertTrue(any(self.REINSTALL_LOG in line for line in client.stderr), client.stderr[-10:])

    def test_concurrent_repairs_reinstall_once(self):
        """壊れた環境に 3 つのセッションが同時に入っても、入れ直しは 1 回だけで、どのセッションも使える。

        後から来たセッションは、ロックを取ったあとで直っていることを確かめ、入れ直さない。入れ直すと、
        先に起動した中継が import する前のモジュールを消してしまう。
        """
        metadata = sorted(self.site_packages(RELAY).glob("*.dist-info/METADATA"))
        self.assertTrue(metadata)
        metadata[0].unlink()
        clients = [self.client() for _ in range(3)]
        results: list = []

        def run(client: StdioClient) -> None:
            try:
                client.initialize(timeout=900)
                results.append({tool["name"] for tool in client.tools()})
            except Exception as exc:  # noqa: BLE001 - 本体のスレッドで確かめる
                results.append(exc)

        threads = [threading.Thread(target=run, args=(client,)) for client in clients]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1200)
        self.assertEqual(results, [TOOLS] * 3)
        reinstalls = [line for client in clients for line in client.stderr if self.REINSTALL_LOG in line]
        self.assertEqual(len(reinstalls), 1, reinstalls)


class EnvProblemsTests(unittest.TestCase):
    """env_problems（RECORD との照合）を、uv を使わずに偽の site-packages で確かめる。

    大きさは os.scandir の一覧から読み、見つからないものと大きさの違うものだけを stat() で確かめ直す。
    その近道で、欠けたファイルや大きさの違うファイルを見逃さないことを確かめる。
    """

    def setUp(self):
        import wiki_mcp_common
        self.common = wiki_mcp_common
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.prefix = Path(self.temp.name)
        self.site = self.prefix / "Lib" / "site-packages"
        files = {"pkg/__init__.py": b"x = 1\n", "pkg/_backends/_impl.py": b"y = 2\n" * 10,
                 "pkg-1.0.dist-info/METADATA": b"Name: pkg\n", "../../Scripts/pkg.exe": b"MZ" * 8}
        rows = []
        for name, body in files.items():
            path = self.site / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            rows.append(f"{name},sha256=x,{len(body)}")
        rows += ["pkg/__pycache__/__init__.cpython-312.pyc,,", "pkg-1.0.dist-info/RECORD,,"]
        (self.site / "pkg-1.0.dist-info" / "RECORD").write_text("\n".join(rows) + "\n", encoding="utf-8")
        from unittest import mock
        patcher = mock.patch("sysconfig.get_paths", return_value={"purelib": str(self.site),
                                                                  "platlib": str(self.site)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_complete_env_has_no_problems(self):
        self.assertEqual(self.common.env_problems(), [])

    def test_missing_lazily_imported_module(self):
        (self.site / "pkg" / "_backends" / "_impl.py").unlink()
        self.assertEqual(self.common.env_problems(), ["pkg/_backends/_impl.py がない"])

    def test_missing_metadata(self):
        (self.site / "pkg-1.0.dist-info" / "METADATA").unlink()
        self.assertEqual(self.common.env_problems(), ["pkg-1.0.dist-info/METADATA がない"])

    def test_size_differs(self):
        (self.site / "pkg" / "__init__.py").write_bytes(b"")
        self.assertEqual(self.common.env_problems(), ["pkg/__init__.py の大きさ（0）が RECORD（6）と違う"])

    def test_file_outside_site_packages(self):
        """Scripts/ の実行ファイルは site-packages の外にあるので、一覧になく、1 つずつ確かめる。"""
        (self.prefix / "Scripts" / "pkg.exe").unlink()
        self.assertEqual(self.common.env_problems(), ["../../Scripts/pkg.exe がない"])

    def test_dangling_symlink(self):
        """リンク先のないシンボリックリンクは、リンク自体の大きさが RECORD と同じでも欠けとみなす。"""
        target = self.site / "pkg" / "__init__.py"
        target.unlink()
        try:
            os.symlink("abcdef", target)  # リンク自体の大きさは 6 で、RECORD の大きさと同じ
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"シンボリックリンクを作れない: {exc}")
        self.assertEqual(self.common.env_problems(), ["pkg/__init__.py がない"])

    def test_dotdot_through_symlink(self):
        """.. を含む行は、文字列の上で正規化せず、実際の場所を確かめる。

        Windows は .. をパスの文字の上で解決する（リンクをたどらない）ので、この食い違いは POSIX だけで起きる。
        """
        if os.name == "nt":
            self.skipTest("Windows は .. をパスの文字の上で解決する")
        outside = self.prefix / "outside" / "sub"
        outside.mkdir(parents=True)
        try:
            os.symlink(outside, self.site / "jump", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"シンボリックリンクを作れない: {exc}")
        record = self.site / "pkg-1.0.dist-info" / "RECORD"
        record.write_text(record.read_text(encoding="utf-8") + "jump/../pkg/__init__.py,,6\n", encoding="utf-8")
        # 実際の jump/../pkg/__init__.py は outside/pkg/__init__.py で、存在しない。
        self.assertEqual(self.common.env_problems(), ["jump/../pkg/__init__.py がない"])

    def test_truncated_record(self):
        record = self.site / "pkg-1.0.dist-info" / "RECORD"
        record.write_text(record.read_text(encoding="utf-8").replace("pkg-1.0.dist-info/RECORD,,\n", ""),
                          encoding="utf-8")
        self.assertEqual(self.common.env_problems(), ["pkg-1.0.dist-info/RECORD が途中で切れている"])


class ScriptToolTests(ServerCase):
    """lint、stats、graph（ADR-0012 の段階 3）。CLI の `--json` と同じ結果を返すことを確かめる。"""

    def setUp(self):
        super().setUp()
        self.client_ = self.client()
        self.client_.initialize()

    def call(self, name, **arguments):
        return self.client_.call(name, {"wiki": str(self.wiki), **arguments})

    def build_graph(self) -> list[str]:
        """オントロジーを置いて extract を実行し、ノード ID の一覧を返す。"""
        (self.wiki / "graph").mkdir(exist_ok=True)
        shutil.copyfile(TEMPLATE, self.wiki / "graph" / "ontology.yaml")
        out = subprocess.run(["uv", "run", "--quiet", "--script", str(SCRIPTS / "wiki_graph_extract.py"),
                              str(self.wiki)], capture_output=True, timeout=600, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8", "replace"))
        lines = (self.wiki / "graph" / "nodes.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line)["id"] for line in lines if line.strip()]

    def test_lint_matches_cli(self):
        result = self.call("lint", suggest_pages=True)
        graph = result.pop("graph")
        self.assertEqual(result, run_cli(SCRIPTS / "wiki_lint.py", self.wiki.resolve(), "--json", "--suggest-pages"))
        # オントロジーがない wiki では、CLI の 3 つの入口と同じ文面で disabled を返す。
        missing = wiki_graph_common.GraphLayerDisabled(self.wiki.resolve() / "graph" / "ontology.yaml")
        self.assertEqual(graph, {"state": "disabled", "message": wiki_graph_common.disabled_message(missing)})
        self.assertEqual(self.call("lint", graph=False)["graph"], {"state": "skipped"})
        # 上限を渡すと CLI の引数と同じく効く。
        strict = self.call("lint", soft_char_cap=100, hard_char_cap=200, required_fm=["type", "title", "author"])
        cli = run_cli(SCRIPTS / "wiki_lint.py", self.wiki.resolve(), "--json", "--soft-char-cap", "100", "--hard-char-cap",
                      "200", "--required-fm", "type,title,author")
        strict.pop("graph")
        self.assertEqual(strict, cli)
        self.assertTrue(cli["oversized_hard"] and cli["missing_frontmatter"])
        # タグの体系を渡すと、CLI の --allowed-tags と同じく体系にないタグを挙げる。省くと検査しない。
        self.assertIsNone(self.call("lint", graph=False)["summary"]["unknown_tags"])
        tagged = self.call("lint", graph=False, allowed_tags=["存在しないタグ"])
        cli = run_cli(SCRIPTS / "wiki_lint.py", self.wiki.resolve(), "--json", "--allowed-tags", "存在しないタグ")
        tagged.pop("graph")
        self.assertEqual(tagged, cli)
        self.assertTrue(cli["unknown_tags"])
        with self.assertRaises(RuntimeError):
            self.call("lint", soft_cap=0)

    def test_lint_includes_graph_lint(self):
        self.build_graph()
        result = self.call("lint")
        self.assertEqual(result["graph"]["state"], "checked")
        self.assertEqual(result["graph"]["findings"],
                         run_cli(SCRIPTS / "wiki_graph_lint.py", self.wiki.resolve(), "--json", script=True))
        (self.wiki / "graph" / "ontology.yaml").write_text("node_types: [\n", encoding="utf-8")
        broken = self.call("lint")["graph"]
        self.assertEqual(broken["state"], "error")
        self.assertIn("オントロジーを読めない", broken["message"])

    def test_stats_matches_cli_and_reports_index(self):
        result = self.call("stats")
        index, server = result.pop("index"), result.pop("server")
        cli = run_cli(SCRIPTS / "wiki_stats.py", self.wiki.resolve(), "--json")
        self.assertEqual(result, cli)
        self.assertEqual(cli["pages"], sum(cli["pages_by_type"].values()))
        self.assertEqual(set(index), {"sections", "embedded", "pending", "state", "dir", "embedder", "fingerprint",
                                      "model"})
        self.assertGreater(index["sections"], 0)
        self.assertEqual(index["pending"], index["sections"] - index["embedded"])
        self.assertEqual(index["model"]["name"], "cl-nagoya/ruri-v3-130m")
        self.assertEqual(server["version"], self.info()["version"])
        self.assertEqual(server["pid"], self.info()["pid"])
        # stats は埋め込みを始めない。query のあとは ready になる。
        self.call("query", query="熱中症")
        ends = time.monotonic() + 120
        while self.call("stats")["index"]["state"] != "ready" and time.monotonic() < ends:
            time.sleep(0.5)
        self.assertEqual(self.call("stats")["index"]["state"], "ready")

    def test_graph_matches_cli(self):
        with self.assertRaises(RuntimeError) as caught:
            self.call("graph", command="facts", about="x")
        self.assertIn("グラフ層を導入する前の wiki", str(caught.exception))
        ids = self.build_graph()
        node = next(i for i in ids if i.startswith("concept:"))
        db = self.wiki / "graph" / "graph.sqlite"
        before = db.stat().st_mtime_ns
        cases = [
            ({"command": "facts", "about": node}, ["facts", "--about", node]),
            ({"command": "neighbors", "node": node}, ["neighbors", "--node", node]),
            ({"command": "edges", "subject": node}, ["edges", "--subject", node]),
            ({"command": "path", "from_node": node, "to_node": ids[-1], "max_depth": 3},
             ["path", "--from", node, "--to", ids[-1], "--max-depth", "3"]),
        ]
        for arguments, argv in cases:
            with self.subTest(command=arguments["command"]):
                self.assertEqual(self.call("graph", **arguments),
                                 run_cli(SCRIPTS / "wiki_graph_query.py", self.wiki.resolve(), "--json", *argv))
        # NFD で渡しても同じノードに当たる。
        import unicodedata
        nfd = self.call("graph", command="facts", about=unicodedata.normalize("NFD", node))
        self.assertEqual(nfd["node"]["id"], node)
        self.assertEqual(db.stat().st_mtime_ns, before, "問い合わせが graph.sqlite を書き換えた")
        for arguments, message in [({"command": "facts", "about": "concept:ない"}, "ノードが見つからない"),
                                   ({"command": "facts"}, "about が要る"),
                                   ({"command": "path", "from_node": node}, "from と to が要る")]:
            with self.subTest(error=message), self.assertRaises(RuntimeError) as caught:
                self.call("graph", **arguments)
            self.assertIn(message, str(caught.exception))
        db.unlink()
        with self.assertRaises(RuntimeError) as caught:
            self.call("graph", command="facts", about=node)
        self.assertIn("graph.sqlite が見つからない", str(caught.exception))


class WorkspaceConfigTests(ServerCase):
    """ツールは wiki を引数で受け取る。サーバーの cwd（データの置き場所）と wiki の上に、サーバーを起動する前から
    壊れた作業領域の設定があっても、それを読まずに答える（ADR-0008）。"""

    def test_tools_ignore_workspace_config(self):
        config = self.root / ".info-hive" / "workspace.json"
        config.parent.mkdir()
        config.write_text("{", encoding="utf-8")
        self.data.mkdir(parents=True, exist_ok=True)
        # 同じ場所で wiki を省いた CLI は、設定を読んで止まる。
        out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_lint.py"), "--json"], cwd=self.data,
                             capture_output=True, timeout=120, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(out.returncode, 1)
        self.assertIn("作業領域の設定を読めない", out.stderr.decode("utf-8", "replace"))
        # 設定を置いてからサーバーを起動する。起動と import の時点で読んでも見つかる。
        client = self.client()
        client.initialize()
        self.assertEqual({tool["name"] for tool in client.tools()}, TOOLS)
        arguments = {"wiki": str(self.wiki)}
        result = client.call("lint", {**arguments, "graph": False})
        result.pop("graph")
        self.assertEqual(result, run_cli(SCRIPTS / "wiki_lint.py", self.wiki.resolve(), "--json"))
        self.assertGreater(client.call("stats", arguments)["pages"], 0)
        self.assertTrue(client.call("query", {**arguments, "query": "熱中症"})["results"])


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
