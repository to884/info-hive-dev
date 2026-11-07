"""未決 4（RAG への経路）の材料。wiki の MCP サーバー（ADR-0012）に、閲覧の画面から直接つなげるかを確かめる。

wiki 0.6.0（36a4089）の中継を、別の data_dir（out/mcp-data）で起動し、作者の環境のサーバーと分ける。
1. 中継に stdio で initialize、tools/list、tools/call（list_index）を送る（アダプタが MCP のクライアントになる経路）
2. server.json のポートとトークンで、Origin と Authorization を変えた HTTP の要求を送る
3. ブラウザのページ（file:// と http://127.0.0.1）から fetch する（画面が直接クライアントになる経路）
配布対象ではない。使い方: python -X utf8 mcp_origin_probe.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "out" / "wiki-src" / "skills" / "info-hive" / "scripts"
DATA = HERE / "out" / "mcp-data"
WIKI = HERE / "out" / "fixture-wiki"
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "browse-poc", "version": "0"}}}


def rpc(proc, message, expect_id=None, timeout=600):
    proc.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
    proc.stdin.flush()
    if expect_id is None:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("中継が終了した")
        data = json.loads(line.decode("utf-8"))
        if data.get("id") == expect_id:
            return data
    raise TimeoutError("応答がない")


def http(port, token, origin=None, method="POST", auth=True):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "Host": f"127.0.0.1:{port}"}
    if auth:
        headers["Authorization"] = f"Bearer {token}"
    if origin is not None:
        headers["Origin"] = origin
    if method == "OPTIONS":
        headers["Access-Control-Request-Method"] = "POST"
        headers["Access-Control-Request-Headers"] = "authorization,content-type"
    body = json.dumps(INIT).encode("utf-8") if method == "POST" else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return {"status": res.status, "acao": res.headers.get("Access-Control-Allow-Origin")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "acao": e.headers.get("Access-Control-Allow-Origin"),
                "body": e.read(200).decode("utf-8", "replace")}


def browser_fetch(port, token):
    (HERE / "out" / "blank.html").write_text("<!doctype html><meta charset=utf-8><title>CSP なし</title>", encoding="utf-8")
    """Playwright の Chromium で、file:// と http://127.0.0.1 のページから fetch する。トークンを知っていても通るか。"""
    script = HERE / "out" / "fetch_probe.mjs"
    script.write_text("""
import { chromium } from "playwright";
import { pathToFileURL } from "node:url";
const [port, token, staticDir] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage();
const out = {};
const call = () => p.evaluate(async ([port, token]) => {
  try {
    const r = await fetch(`http://127.0.0.1:${port}/mcp`, { method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                 "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }) });
    return "status " + r.status;
  } catch (e) { return "error " + e; }
}, [port, token]);
// 生成物のページは CSP（default-src 'none'）で fetch を自分で禁じるので、CSP のないページからも呼ぶ。
await p.goto(pathToFileURL(staticDir).href + "/index.html");
out.file_with_csp = await call();
await p.goto(pathToFileURL(staticDir).href + "/../blank.html");
out.file_without_csp = await call();
p.on("request", (r) => { if (r.url().includes("/mcp")) out.origin_sent = r.headers()["origin"] ?? null; });
await call();
await p.goto(`http://127.0.0.1:${port}/`).catch(() => {});
await b.close();
console.log(JSON.stringify(out));
""", encoding="utf-8")
    res = subprocess.run(["node", str(script), str(port), token, str(HERE / "out" / "static")],
                         capture_output=True, cwd=HERE, timeout=120)
    return json.loads(res.stdout.decode("utf-8").strip().splitlines()[-1])


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, INFO_HIVE_DATA_DIR=str(DATA), INFO_HIVE_MCP_IDLE_SECONDS="60", PYTHONUTF8="1")
    started = time.perf_counter()
    proc = subprocess.Popen(["uv", "run", "--quiet", "--script", str(SCRIPTS / "wiki_mcp_launch.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=open(HERE / "out" / "mcp-relay.stderr.log", "wb"), env=env)
    result = {}
    try:
        rpc(proc, INIT, 1)
        result["initialize_s"] = round(time.perf_counter() - started, 2)
        rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, 2)
        result["tools_list_s"] = round(time.perf_counter() - started, 2)
        result["tools"] = [t["name"] for t in tools["result"]["tools"]]
        called = rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                            "params": {"name": "list_index", "arguments": {"wiki": str(WIKI)}}}, 3)
        result["relay_list_index_ok"] = not called["result"].get("isError", False)
        info = json.loads((DATA / "server.json").read_text(encoding="utf-8"))
        port, token = info["port"], info["token"]
        result["http"] = {
            "bearer_no_origin": http(port, token),
            "bearer_origin_null": http(port, token, origin="null"),
            "bearer_origin_loopback_other_port": http(port, token, origin="http://127.0.0.1:1"),
            "no_bearer": http(port, token, auth=False),
            "preflight_origin_null": http(port, token, origin="null", method="OPTIONS"),
        }
        result["browser"] = browser_fetch(port, token)
    finally:
        proc.terminate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    out = HERE / "out" / "results" / "mcp-origin.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
