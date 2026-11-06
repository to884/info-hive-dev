"""E10: wiki の MCP サーバー（案 B）の形を試作で確かめる。mcp を入れた別の環境（DWORK/mcp-venv）で動かす。

- 上乗せ: 同じ検索を、関数の直接呼び出し、HTTP のサーバーへの直接の MCP、stdio の中継経由の MCP で 200 回ずつ測る。
- 起動: 中継の起動から initialize の完了まで（サーバーも起動する冷えた状態と、サーバーが動いている状態）。
- index_chunks: 1,000 チャンク（約 1 MB）を 1 回の呼び出しで渡す時間。
- 防御: トークンなし、Host ヘッダーの偽装の応答コード。
- 重複起動: サーバーを止めてから、4 つの中継を同時に起動し、サーバーがいくつ起動したかを数える。
- 停止: 要求がなくなってから idle 秒で止まるか。
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import psutil

from decision_common import DWORK, HERE, save
from common import WORK, p95

STATE = DWORK / "mcp-state"
INDEX = DWORK / "memory/natural.usearch"
QUERIES = WORK / "vectors/natural/R-130.queries.npy"
IDLE = 20
CALLS = 200


def relay_params():
    from mcp.client.stdio import StdioServerParameters
    env = {**os.environ, "PROBE_STATE": str(STATE), "PROBE_INDEX": str(INDEX), "PROBE_QUERIES": str(QUERIES), "PROBE_IDLE": str(IDLE)}
    return StdioServerParameters(command=sys.executable, args=["-X", "utf8", str(HERE / "mcp_probe/relay.py")], env=env)


def server_processes():
    """動いているサーバーの数を数えるための pid の一覧。

    Windows の venv の python.exe は本体を子プロセスとして起動するので、1 つのサーバーが 2 つのプロセスに見える。
    親もサーバーのコマンドラインを持つプロセスは数えない。
    """
    found = {}
    for proc in psutil.process_iter(["pid", "ppid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except psutil.Error:
            continue
        if "server.py" in cmd and str(STATE) in cmd:
            found[proc.info["pid"]] = proc.info["ppid"]
    return [pid for pid, ppid in found.items() if ppid not in found]


def all_server_processes():
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except psutil.Error:
            continue
        if "server.py" in cmd and str(STATE) in cmd:
            found.append(proc.info["pid"])
    return found


def kill_servers():
    for pid in all_server_processes():
        try:
            psutil.Process(pid).kill()
        except psutil.Error:
            pass
    time.sleep(1)


async def time_calls(session, name, make_args, count):
    for i in range(5):
        await session.call_tool(name, make_args(i))
    times = []
    for i in range(count):
        started = time.perf_counter()
        await session.call_tool(name, make_args(i))
        times.append((time.perf_counter() - started) * 1000)
    return times


async def via_relay():
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    started = time.perf_counter()
    async with stdio_client(relay_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            cold = time.perf_counter() - started
            info = json.loads((await session.call_tool("relay_info", {})).content[0].text)
            times = await time_calls(session, "query", lambda i: {"i": i, "k": 10}, CALLS)
            chunks = [{"chunk_id": i, "text": "消費税の軽減税率の対象になる飲食料品の範囲。" * 22} for i in range(1000)]
            payload = len(json.dumps(chunks, ensure_ascii=False).encode("utf-8"))
            t = time.perf_counter()
            accepted = (await session.call_tool("index_chunks", {"chunks": chunks})).structuredContent
            index_ms = (time.perf_counter() - t) * 1000
            relay_rss = psutil.Process(info["relay_pid"]).memory_info().rss
            server_rss = psutil.Process(info["server_pid"]).memory_info().rss
    return {"initialize_seconds": cold, "started_server": info["started_server"], "spawn_method": info.get("spawn_method"),
            "server_pid": info["server_pid"], "query_p95_ms": p95(times),
            "query_median_ms": float(np.median(times)), "index_chunks": {"chunks": 1000, "payload_bytes": payload, "ms": index_ms, "result": accepted},
            "relay_rss_bytes": relay_rss, "server_rss_bytes": server_rss}


async def direct_http():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    info = json.loads((STATE / "server.json").read_text(encoding="utf-8"))
    url = f"http://127.0.0.1:{info['port']}/mcp"
    async with streamablehttp_client(url, headers={"Authorization": f"Bearer {info['token']}"}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            times = await time_calls(session, "query", lambda i: {"i": i, "k": 10}, CALLS)
    import httpx
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}}}
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    no_token = httpx.post(url, json=body, headers=headers).status_code
    bad_host = httpx.post(url, json=body, headers={**headers, "Authorization": f"Bearer {info['token']}", "Host": "evil.example"}).status_code
    wrong_token = httpx.post(url, json=body, headers={**headers, "Authorization": "Bearer nope"}).status_code
    return {"query_p95_ms": p95(times), "query_median_ms": float(np.median(times)),
            "security": {"no_token": no_token, "wrong_token": wrong_token, "spoofed_host": bad_host}}


async def concurrent_relays(count=4):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async def one():
        started = time.perf_counter()
        async with stdio_client(relay_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                info = json.loads((await session.call_tool("relay_info", {})).content[0].text)
                await session.call_tool("query", {"i": 1, "k": 10})
                servers = server_processes()
                await asyncio.sleep(3)
                return {"seconds": time.perf_counter() - started, "started_server": info["started_server"],
                        "server_pid": info["server_pid"], "servers_seen": servers}
    return await asyncio.gather(*(one() for _ in range(count)))


def main():
    # PROBE_LOG_LEVEL=WARNING で、測定のプロセス・中継・サーバーの INFO のログ（httpx の HTTP Request など）を止める
    import logging
    level = os.environ.get("PROBE_LOG_LEVEL", "INFO")
    for name in ("", "httpx", "mcp"):
        logging.getLogger(name).setLevel(level)
    if STATE.exists():
        kill_servers()
        shutil.rmtree(STATE, ignore_errors=True)
    STATE.mkdir(parents=True)
    # 関数の直接呼び出し（上乗せの基準）
    from usearch.index import Index
    index = Index.restore(str(INDEX), view=True)
    index.expansion_search = 256
    qvecs = np.load(QUERIES)
    for i in range(5):
        index.search(qvecs[i], 10, threads=1)
    direct = []
    for i in range(CALLS):
        t = time.perf_counter()
        [int(k) for k in index.search(qvecs[i % len(qvecs)], 10, threads=1).keys]
        direct.append((time.perf_counter() - t) * 1000)
    report = {"function_p95_ms": p95(direct)}
    report["relay_cold"] = asyncio.run(via_relay())
    print("relay cold", report["relay_cold"], flush=True)
    report["relay_warm"] = asyncio.run(via_relay())
    # 1 回目の中継が終わった後もサーバーが生きていれば、2 回目はサーバーを起動しない（セッションをまたいで共有できる）
    report["server_survived_relay_exit"] = (not report["relay_warm"]["started_server"]
                                            and report["relay_warm"]["server_pid"] == report["relay_cold"]["server_pid"])
    print("relay warm", report["relay_warm"], "survived", report["server_survived_relay_exit"], flush=True)
    report["direct_http"] = asyncio.run(direct_http())
    print("direct http", report["direct_http"], flush=True)
    kill_servers()
    (STATE / "server.json").unlink(missing_ok=True)
    report["concurrent"] = asyncio.run(concurrent_relays())
    pids = {r["server_pid"] for r in report["concurrent"]}
    report["concurrent_summary"] = {"relays": len(report["concurrent"]), "distinct_server_pids": len(pids),
                                    "servers_started": sum(r["started_server"] for r in report["concurrent"]),
                                    "max_servers_seen": max(len(r["servers_seen"]) for r in report["concurrent"])}
    print("concurrent", report["concurrent_summary"], flush=True)
    time.sleep(IDLE + 8)
    report["idle_shutdown"] = {"idle_seconds": IDLE, "servers_after_idle": len(server_processes())}
    kill_servers()
    overhead_relay = report["relay_warm"]["query_p95_ms"] - report["function_p95_ms"]
    overhead_http = report["direct_http"]["query_p95_ms"] - report["function_p95_ms"]
    report["overhead_p95_ms"] = {"relay": overhead_relay, "http": overhead_http}
    security_ok = report["direct_http"]["security"]["no_token"] == 401 and report["direct_http"]["security"]["wrong_token"] == 401 \
        and report["direct_http"]["security"]["spoofed_host"] in (400, 403, 421)
    passed = report["server_survived_relay_exit"] and overhead_relay <= 10 and report["concurrent_summary"]["distinct_server_pids"] == 1 \
        and report["concurrent_summary"]["max_servers_seen"] == 1 and security_ok and report["idle_shutdown"]["servers_after_idle"] == 0
    save(os.environ.get("PROBE_OUT", "mcp-relay.json"), {"purpose": "wiki の MCP サーバー（127.0.0.1 の streamable HTTP）と stdio の中継の試作",
                            "log_level": level, "json_response": os.environ.get("PROBE_JSON_RESPONSE") == "1",
                            "auth": os.environ.get("PROBE_AUTH", "starlette"), **report,
                            "security_ok": security_ok, "passed": passed,
                            "criterion": "中継が終わってもサーバーが残る、中継の上乗せの p95 ≤ 10 ms、同時に 4 つ起動してもサーバーは 1 つ、トークンと Host の確認が効く、idle で止まる"})


if __name__ == "__main__":
    main()
