"""Claude Code が stdio の MCP サーバーをどう起動するかを調べるための、最小の MCP サーバー。配布対象ではない。

標準ライブラリだけで動く（venv の起動用の python.exe を挟まないように、本体の python.exe で直接起動する）。
起動したら次を JSON に書き、その後は stdio で MCP の initialize と tools/list にだけ答える。

- 自分がジョブオブジェクトに入っているか、そのジョブの制限の旗（KILL_ON_JOB_CLOSE、BREAKAWAY_OK など）、ジョブ内のプロセス数
- DETACHED_PROCESS で起動した孫プロセスと、CREATE_BREAKAWAY_FROM_JOB も付けた孫プロセスの pid

使い方: python job_check_server.py <出力の JSON>
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
from ctypes import wintypes

KILL_ON_JOB_CLOSE = 0x2000
BREAKAWAY_OK = 0x0800
SILENT_BREAKAWAY_OK = 0x1000
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


def job_info():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    in_job = wintypes.BOOL()
    kernel32.IsProcessInJob(kernel32.GetCurrentProcess(), None, ctypes.byref(in_job))
    info = {"in_job": bool(in_job.value)}
    if not in_job.value:
        return info
    extended = ctypes.create_string_buffer(144)  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION（x64）
    if kernel32.QueryInformationJobObject(None, 9, extended, len(extended), None):
        flags = int.from_bytes(extended.raw[16:20], "little")
        info.update(limit_flags=hex(flags), kill_on_job_close=bool(flags & KILL_ON_JOB_CLOSE),
                    breakaway_ok=bool(flags & BREAKAWAY_OK), silent_breakaway_ok=bool(flags & SILENT_BREAKAWAY_OK))
    else:
        info["limit_error"] = ctypes.get_last_error()
    ids = ctypes.create_string_buffer(8 + 8 * 4096)
    if kernel32.QueryInformationJobObject(None, 3, ids, len(ids), None):
        assigned = int.from_bytes(ids.raw[0:4], "little")
        listed = int.from_bytes(ids.raw[4:8], "little")
        info.update(processes_in_job=assigned,
                    pids_in_job=[int.from_bytes(ids.raw[8 + 8 * i:16 + 8 * i], "little") for i in range(min(listed, 50))])
    return info


def spawn(flags):
    try:
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], creationflags=flags,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"pid": proc.pid}
    except OSError as error:
        return {"error": f"{type(error).__name__}: {error}"}


def main():
    out = sys.argv[1]
    base = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    report = {"pid": os.getpid(), "ppid": os.getppid(), "job": job_info(),
              "grandchild_detached": spawn(base), "grandchild_breakaway": spawn(base | CREATE_BREAKAWAY_FROM_JOB)}
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False)
    os.replace(out + ".tmp", out)
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    for line in stdin:
        try:
            message = json.loads(line.decode("utf-8"))
        except ValueError:
            continue
        if "id" not in message:
            continue
        method = message.get("method")
        if method == "initialize":
            result = {"protocolVersion": message.get("params", {}).get("protocolVersion", "2025-06-18"),
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "job-check", "version": "0"}}
        elif method == "tools/list":
            result = {"tools": []}
        else:
            result = {}
        stdout.write((json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}) + "\n").encode("utf-8"))
        stdout.flush()


if __name__ == "__main__":
    main()
