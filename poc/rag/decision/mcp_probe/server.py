"""E10 の試作: wiki の MCP サーバー（127.0.0.1 の streamable HTTP）。配布対象ではない。

ADR-0001 の条件に合わせ、127.0.0.1 だけで待ち受け、起動ごとのトークンと Host ヘッダーを確かめる。
起動したら、ポートとトークンと pid を state/server.json に一時ファイル経由で書く。
idle 秒のあいだ要求がなければ止まる。検索は natural（8,275 行）の usearch の索引で行う（MCP の上乗せだけを測るため）。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import socket
import time
from pathlib import Path

import numpy as np
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--idle", type=float, default=600)
    args = parser.parse_args()
    state = Path(args.state)
    port, token = free_port(), secrets.token_urlsafe(32)
    from usearch.index import Index
    index = Index.restore(args.index, view=True)
    index.expansion_search = 256
    qvecs = np.load(args.queries)
    last = [time.monotonic()]
    mcp = FastMCP("info-hive-wiki-probe", host="127.0.0.1", port=port,
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
                                                               allowed_hosts=[f"127.0.0.1:{port}"], allowed_origins=[]))

    @mcp.tool()
    def query(i: int, k: int = 10) -> list[int]:
        """natural の i 番目のクエリのベクトルで、上位 k 件の id を返す。"""
        return [int(key) for key in index.search(qvecs[i % len(qvecs)], k, threads=1).keys]

    @mcp.tool()
    def index_chunks(chunks: list[dict]) -> dict:
        """rag から渡されるチャンクを受け取る（試作では数えるだけ）。"""
        return {"accepted": len(chunks), "characters": sum(len(c.get("text", "")) for c in chunks)}

    class Guard(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            last[0] = time.monotonic()
            if request.headers.get("authorization") != f"Bearer {token}":
                return PlainTextResponse("unauthorized", status_code=401)
            return await call_next(request)

    app = mcp.streamable_http_app()
    app.add_middleware(Guard)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on"))

    async def run():
        serving = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.02)
        tmp = state / "server.json.tmp"
        tmp.write_text(json.dumps({"port": port, "token": token, "pid": os.getpid()}), encoding="utf-8")
        os.replace(tmp, state / "server.json")
        while not serving.done():
            await asyncio.sleep(0.5)
            if time.monotonic() - last[0] > args.idle:
                server.should_exit = True
                break
        await serving

    asyncio.run(run())


if __name__ == "__main__":
    main()
