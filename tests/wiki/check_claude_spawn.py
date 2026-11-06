"""Claude Code が wiki の中継（stdio の MCP サーバー）をどう起動するか、サーバーがセッションの後に残るかを確かめる。

ADR-0012 の「デスクトップアプリが stdio の MCP サーバーをどう起動するかは確かめていない」への答えを記録する。
デスクトップアプリは、アプリ本体（Claude.exe）の子として CLI（claude.exe）を動かし、MCP サーバーはその CLI の子として
起動される。このスクリプトをデスクトップアプリのセッションの中から実行すると、同じ親子関係とジョブの中で
`claude -p` が中継を起動する。

確かめること:
1. このプロセス（デスクトップアプリの子孫）がジョブに入っているか、ジョブの制限の旗（KILL_ON_JOB_CLOSE など）
2. `claude -p` が中継を起動し、中継がサーバーを起動するか
3. `claude -p` が終わった後もサーバーが残るか（DETACHED_PROCESS の孫がセッションの終了で止まらないか）
4. サーバーがジョブに入っているか（外から IsProcessInJob で見る）

試作の job_check_server.py は GetCurrentProcess() の疑似ハンドル（-1）を ctypes の既定の int で渡していたので、
64 ビットのハンドルが切り詰められ、ジョブの中でも「入っていない」と返していた。ここでは型を指定する。

`claude -p` を 1 回実行するので、モデルの呼び出しが 1 回分かかる。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_claude_spawn.py
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

OUT = ROOT / "docs/research/wiki-mcp-server-2026-11-06/claude-spawn.json"
CORPUS = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"
KILL_ON_JOB_CLOSE, BREAKAWAY_OK, SILENT_BREAKAWAY_OK = 0x2000, 0x0800, 0x1000


def kernel32():
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = wintypes.HANDLE
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    k.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                            ctypes.c_void_p]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k, wintypes


def own_job() -> dict:
    k, wintypes = kernel32()
    flag = wintypes.BOOL()
    k.IsProcessInJob(k.GetCurrentProcess(), None, ctypes.byref(flag))
    info = {"in_job": bool(flag.value)}
    if flag.value:
        extended = ctypes.create_string_buffer(144)  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION（x64）
        if k.QueryInformationJobObject(None, 9, extended, len(extended), None):
            flags = int.from_bytes(extended.raw[16:20], "little")
            info.update(limit_flags=hex(flags), kill_on_job_close=bool(flags & KILL_ON_JOB_CLOSE),
                        breakaway_ok=bool(flags & BREAKAWAY_OK), silent_breakaway_ok=bool(flags & SILENT_BREAKAWAY_OK))
        ids = ctypes.create_string_buffer(8 + 8 * 4096)
        if k.QueryInformationJobObject(None, 3, ids, len(ids), None):
            info["processes_in_job"] = int.from_bytes(ids.raw[0:4], "little")
    return info


def child_job() -> dict:
    """子プロセスから見たジョブ。

    uv の venv の python.exe（起動用のプログラム）は、本体の python を自分だけのジョブ（KILL_ON_JOB_CLOSE と
    SILENT_BREAKAWAY_OK）に入れる。そのため own_job() はそのジョブを返す。SILENT_BREAKAWAY_OK のジョブの子は
    黙ってジョブから抜けるので、子から測ると、その外側（ホストが作ったジョブ）が見える。中継やサーバーも同じ
    しくみで、ホストのジョブに入る。
    """
    code = (f"import sys, json; sys.path.insert(0, {str(HERE)!r}); import check_claude_spawn as c; "
            "print(json.dumps(c.own_job()))")
    out = subprocess.run([getattr(sys, "_base_executable", sys.executable), "-c", code], capture_output=True,
                         timeout=60)
    try:
        return json.loads(out.stdout.decode("utf-8"))
    except ValueError:
        return {"error": out.stderr.decode("utf-8", "replace")[-300:]}


def in_job(pid: int) -> bool | None:
    k, wintypes = kernel32()
    handle = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    flag = wintypes.BOOL()
    k.IsProcessInJob(handle, None, ctypes.byref(flag))
    k.CloseHandle(handle)
    return bool(flag.value)


def ancestry(pid: int) -> list[dict]:
    import psutil
    chain = []
    try:
        process = psutil.Process(pid)
        while process is not None and len(chain) < 10:
            chain.append({"pid": process.pid, "name": process.name(),
                          "in_job": in_job(process.pid) if os.name == "nt" else None})
            process = process.parent()
    except psutil.Error:
        pass
    return chain


def host_claude() -> str | None:
    """このプロセスの祖先にある claude.exe（デスクトップアプリが動かしている CLI）。なければ None。"""
    import psutil
    try:
        process = psutil.Process(os.getpid()).parent()
        while process is not None:
            if process.name().lower() in ("claude.exe", "claude") and "claude-code" in process.exe().replace("\\", "/"):
                return process.exe()
            process = process.parent()
    except psutil.Error:
        pass
    return None


def main() -> None:
    import psutil
    from mcp_stdio import RELAY
    # デスクトップアプリのセッションから動かすときは、アプリが使っている CLI と同じものを使う。
    claude = host_claude() or shutil.which("claude")
    if not claude:
        raise SystemExit("claude（Claude Code の CLI）が PATH にない")
    report = {"purpose": "Claude Code が wiki の中継とサーバーをどう起動し、セッションの後にサーバーが残るか",
              "claude": claude,
              "platform": platform.platform(), "claude_version": subprocess.run(
                  [claude, "--version"], capture_output=True, text=True, encoding="utf-8").stdout.strip(),
              "measuring_process": {"ancestry": ancestry(os.getpid()),
                                    "job": own_job() if os.name == "nt" else None,
                                    "child_job": child_job() if os.name == "nt" else None}}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        data = Path(tmp) / "data"
        wiki = Path(tmp) / "wiki"
        shutil.copytree(CORPUS, wiki)
        config = Path(tmp) / "mcp.json"
        config.write_text(json.dumps({"mcpServers": {"wiki": {
            "type": "stdio", "command": "uv", "args": ["run", "--quiet", "--script", str(RELAY)],
            "env": {"INFO_HIVE_DATA_DIR": str(data), "INFO_HIVE_TEST_EMBEDDER": "hash",
                    "INFO_HIVE_MCP_IDLE_SECONDS": "600"}}}}), encoding="utf-8")
        prompt = (f"mcp__wiki__list_index ツールを wiki={wiki.as_posix()} で 1 回だけ呼び、"
                  "結果の indexes の件数を数字だけで答えてください。ほかのツールは使わないでください。")
        started = time.perf_counter()
        run = subprocess.run([claude, "-p", prompt, "--mcp-config", str(config), "--strict-mcp-config",
                              "--allowedTools", "mcp__wiki__list_index", "--output-format", "json"],
                             capture_output=True, timeout=900, cwd=tmp,
                             env={**os.environ, "PYTHONUTF8": "1"})
        report["claude_p"] = {"exit_code": run.returncode, "seconds": round(time.perf_counter() - started, 1),
                              "stderr_tail": run.stderr.decode("utf-8", "replace")[-400:]}
        try:
            report["claude_p"]["result"] = json.loads(run.stdout.decode("utf-8"))["result"][:200]
        except (ValueError, KeyError):
            report["claude_p"]["stdout_tail"] = run.stdout.decode("utf-8", "replace")[-500:]
            report["claude_p"]["stderr_tail"] = run.stderr.decode("utf-8", "replace")[-500:]
        try:
            info = json.loads((data / "server.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            info = None
        report["server_started"] = info is not None
        if info:
            pid = info["pid"]
            time.sleep(3)
            report["server_alive_after_claude_exit"] = psutil.pid_exists(pid)
            if psutil.pid_exists(pid):
                report["server"] = {"in_job": in_job(pid) if os.name == "nt" else None,
                                    "ancestry": ancestry(pid)}
                psutil.Process(pid).terminate()
                psutil.Process(pid).wait(30)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
