"""PoC の共通コアを呼ぶ CLI と stdio MCP。"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time

from job_core import Store


def worker(path, delay, lease, stop=None):
    store = Store(path)
    while stop is None or not stop.is_set():
        if not store.work_once(delay=delay, lease=lease):
            time.sleep(0.03)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["server", "worker", "submit", "status", "cancel", "retry", "active", "run_sync"])
    parser.add_argument("--db", required=True)
    parser.add_argument("--wiki", default="wiki")
    parser.add_argument("--source", default="")
    parser.add_argument("--job", default="")
    parser.add_argument("--policy", default="protocol-v1")
    parser.add_argument("--mode", choices=["thread", "child", "none"], default="child")
    parser.add_argument("--delay", type=float, default=0.02)
    parser.add_argument("--lease", type=float, default=0.5)
    parser.add_argument("--pid-file", default="")
    args = parser.parse_args()
    store = Store(args.db)
    if args.action == "worker":
        worker(args.db, args.delay, args.lease)
        return
    if args.action != "server":
        if args.action in {"submit", "run_sync"}:
            result = getattr(store, args.action)(args.wiki, args.source, args.policy)
        elif args.action == "active":
            result = store.active(args.wiki, args.source)
        else:
            result = getattr(store, args.action)(args.job)
        print(json.dumps(result, ensure_ascii=False))
        return
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("info-hive-rag-poc")
    server.tool()(store.submit)
    server.tool()(store.status)
    server.tool()(store.cancel)
    server.tool()(store.retry)
    server.tool()(store.active)
    server.tool()(store.run_sync)
    stop = threading.Event()
    process = None
    thread = None
    if args.mode == "child":
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen([sys.executable, __file__, "worker", "--db", args.db, "--delay", str(args.delay), "--lease", str(args.lease)],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    elif args.mode == "thread":
        thread = threading.Thread(target=worker, args=(args.db, args.delay, args.lease, stop), daemon=True)
        thread.start()
    if args.pid_file:
        from pathlib import Path
        Path(args.pid_file).write_text(json.dumps({"server": os.getpid(), "worker": process.pid if process else None}), encoding="utf-8")
    try:
        server.run(transport="stdio")
    finally:
        stop.set()
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        if thread:
            thread.join(timeout=1)


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
