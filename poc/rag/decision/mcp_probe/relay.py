"""E10 の試作: stdio の中継の入口。ホストは stdio で起動し、中継は HTTP のサーバーに要求を渡す。配布対象ではない。

起動時に state/server.lock を取り、server.json の指すサーバーが生きていれば使い、いなければ起動する。
ロックで、同時に起動された中継がサーバーを 1 つだけ起動するようにする。
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from filelock import FileLock
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.fastmcp import Context, FastMCP

STATE = Path(os.environ["PROBE_STATE"])
HERE = Path(__file__).resolve().parent


def alive(info):
    if not info or not psutil.pid_exists(info["pid"]):
        return False
    try:
        with socket.create_connection(("127.0.0.1", info["port"]), timeout=0.5):
            return True
    except OSError:
        return False


def read_info():
    try:
        return json.loads((STATE / "server.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


SPAWN = {"method": None}
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


def spawn(args):
    """サーバーを、中継が属するジョブオブジェクトの外で起動する。

    Windows の MCP の SDK（stdio_client）は中継を KILL_ON_JOB_CLOSE のジョブに入れる。
    中継の子として起動すると、起動したセッションが終わったときにサーバーも止まり、他のセッションが共有できない。
    PROBE_SPAWN: child（ジョブの中。比較のため）、breakaway（CREATE_BREAKAWAY_FROM_JOB）、wmi（WMI に起動させる）。既定は wmi。
    breakaway はエラーにならないが、実測ではサーバーがジョブに残り、中継の終了とともに止まった。
    """
    mode = os.environ.get("PROBE_SPAWN", "wmi")
    if os.name != "nt":
        return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True), "posix"
    base = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    io = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if mode == "child":
        return subprocess.Popen(args, creationflags=base, **io), "child"
    if mode == "breakaway":
        return subprocess.Popen(args, creationflags=base | CREATE_BREAKAWAY_FROM_JOB, **io), "breakaway"
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    wmi = win32com.client.GetObject(r"winmgmts:root\cimv2")
    startup = wmi.Get("Win32_ProcessStartup").SpawnInstance_()
    startup.ShowWindow = 0
    process = wmi.Get("Win32_Process")
    params = process.Methods_("Create").InParameters.SpawnInstance_()
    params.CommandLine = subprocess.list2cmdline(args)
    params.CurrentDirectory = str(HERE)
    params.ProcessStartupInformation = startup
    out = process.ExecMethod_("Create", params)
    if out.ReturnValue != 0:
        raise RuntimeError(f"WMI でサーバーを起動できなかった（{out.ReturnValue}）")
    return None, "wmi"


def ensure_server():
    with FileLock(str(STATE / "server.lock"), timeout=60):
        info = read_info()
        if alive(info):
            return info, False
        (STATE / "server.json").unlink(missing_ok=True)
        args = [sys.executable, "-X", "utf8", str(HERE / "server.py"), "--state", str(STATE),
                "--index", os.environ["PROBE_INDEX"], "--queries", os.environ["PROBE_QUERIES"],
                "--idle", os.environ.get("PROBE_IDLE", "600")]
        proc, SPAWN["method"] = spawn(args)
        # Windows の venv の python.exe は本体を子プロセスとして起動するので、proc.pid と server.json の pid は一致しない。
        # 起動の前にロックの中で server.json を消しているので、新しく現れた server.json は今起動したサーバーのものである。
        ends = time.time() + 60
        while time.time() < ends:
            info = read_info()
            if info and alive(info):
                return info, True
            if proc is not None and proc.poll() not in (None, 0):
                raise RuntimeError(f"wiki のサーバーが終了コード {proc.returncode} で止まった")
            time.sleep(0.05)
        raise RuntimeError("wiki のサーバーが 60 秒以内に起動しなかった")


@asynccontextmanager
async def lifespan(_app):
    info, started = ensure_server()
    url = f"http://127.0.0.1:{info['port']}/mcp"
    async with streamablehttp_client(url, headers={"Authorization": f"Bearer {info['token']}"}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield {"session": session, "started_server": started, "server_pid": info["pid"]}


relay = FastMCP("info-hive-wiki-relay", lifespan=lifespan)


@relay.tool()
async def query(i: int, k: int = 10, ctx: Context = None) -> list[int]:
    result = await ctx.request_context.lifespan_context["session"].call_tool("query", {"i": i, "k": k})
    return (result.structuredContent or {}).get("result", [])


@relay.tool()
async def index_chunks(chunks: list[dict], ctx: Context = None) -> dict:
    result = await ctx.request_context.lifespan_context["session"].call_tool("index_chunks", {"chunks": chunks})
    return result.structuredContent or {}


@relay.tool()
async def relay_info(ctx: Context = None) -> dict:
    context = ctx.request_context.lifespan_context
    return {"started_server": context["started_server"], "server_pid": context["server_pid"], "relay_pid": os.getpid(),
            "spawn_method": SPAWN["method"]}


if __name__ == "__main__":
    relay.run("stdio")
