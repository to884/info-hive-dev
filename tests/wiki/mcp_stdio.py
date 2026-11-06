"""テストと測定のための、最小の stdio の MCP クライアント。

Python の MCP の SDK の stdio_client は、Windows で起動したサーバーを KILL_ON_JOB_CLOSE のジョブに入れる。
そのため、中継が終わったあとにサーバーが残るかを確かめられない。ここでは subprocess で中継を起動し、
改行で区切った JSON-RPC を直接やり取りする。ジョブには入れない（Claude Code と同じ）。
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
RELAY = SCRIPTS / "wiki_mcp_relay.py"
SERVER = SCRIPTS / "wiki_mcp_server.py"


def relay_command() -> list[str]:
    """中継の起動のしかた。.mcp.json と同じく uv run --script で起動する。"""
    return ["uv", "run", "--quiet", "--script", str(RELAY)]


class StdioClient:
    def __init__(self, command: list[str], env: dict | None = None):
        self.process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONUTF8": "1", **(env or {})})
        self._messages: queue.Queue = queue.Queue()
        self.stderr: list[str] = []
        self._next = 0
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            try:
                self._messages.put(json.loads(line.decode("utf-8")))
            except ValueError:
                self.stderr.append("非 JSON の出力: " + line.decode("utf-8", "replace"))

    def _read_err(self):
        for line in self.process.stderr:
            self.stderr.append(line.decode("utf-8", "replace").rstrip())

    def send(self, message: dict) -> None:
        self.process.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def request(self, method: str, params: dict | None = None, timeout: float = 600) -> dict:
        self._next += 1
        ident = self._next
        self.send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params or {}})
        ends = time.monotonic() + timeout
        while True:
            remaining = ends - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"{method} の応答がない。stderr: {self.stderr[-10:]}")
            try:
                message = self._messages.get(timeout=remaining)
            except queue.Empty:
                continue
            if message.get("id") == ident:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def initialize(self, timeout: float = 1800) -> dict:
        result = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                             "clientInfo": {"name": "info-hive-test", "version": "0"}}, timeout)
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    def tools(self, timeout: float = 1800) -> list[dict]:
        return self.request("tools/list", timeout=timeout)["tools"]

    def call(self, name: str, arguments: dict, timeout: float = 1800) -> dict:
        result = self.request("tools/call", {"name": name, "arguments": arguments}, timeout)
        if result.get("isError"):
            text = " ".join(c.get("text", "") for c in result.get("content", []))
            raise RuntimeError(f"{name} がエラーを返した: {text}")
        if result.get("structuredContent") is not None:
            structured = result["structuredContent"]
            return structured.get("result", structured) if set(structured) == {"result"} else structured
        return json.loads(result["content"][0]["text"])

    def close(self, timeout: float = 30) -> int:
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            return self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            return self.process.wait()


def server_processes() -> list:
    """wiki_mcp_server.py を動かしているプロセス。venv の起動用の python.exe の子は、親だけを数える。"""
    import psutil
    found = []
    for process in psutil.process_iter(["pid", "ppid", "cmdline"]):
        try:
            cmdline = process.info["cmdline"] or []
        except psutil.Error:
            continue
        if any(part.endswith("wiki_mcp_server.py") for part in cmdline):
            found.append(process)
    pids = {p.pid for p in found}
    return [p for p in found if p.info["ppid"] not in pids]


if __name__ == "__main__":
    # 手で試すとき: python tests/wiki/mcp_stdio.py <wiki のルート> <検索語>
    client = StdioClient(relay_command())
    client.initialize()
    print([tool["name"] for tool in client.tools()])
    print(json.dumps(client.call("query", {"wiki": sys.argv[1], "query": sys.argv[2], "top": 3}), ensure_ascii=False,
                     indent=1))
    client.close()
