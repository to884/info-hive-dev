"""E10 の補足: Claude Code（CLI）が stdio の MCP サーバーをジョブオブジェクトに入れるか、セッションが終わると孫プロセスも止めるかを確かめる。

mcp_probe/job_check_server.py を、本体の python.exe で直接起動する MCP サーバーとして登録し、
`claude -p` を 1 回だけ実行する。終わった後に、サーバーが起動した孫プロセスが生きているかを見る。
比べるため、同じことをこのスクリプトから直接（Claude Code を挟まずに）子プロセスとして起動しても確かめる。

Claude Code のデスクトップアプリは測っていない。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time

import psutil

from decision_common import DWORK, HERE, save

WORKDIR = DWORK / "claude-job-check"
SERVER = HERE / "mcp_probe/job_check_server.py"
BASE_PYTHON = getattr(sys, "_base_executable", sys.executable)


def alive(info):
    return bool(info.get("pid")) and psutil.pid_exists(info["pid"])


def direct_child():
    """Claude Code を挟まずに起動したとき。親が終わった後に孫が残るかの基準。"""
    out = WORKDIR / "direct.json"
    proc = subprocess.Popen([BASE_PYTHON, "-X", "utf8", str(SERVER), str(out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
    for _ in range(100):
        if out.exists():
            break
        time.sleep(0.1)
    proc.stdin.close()
    proc.wait(timeout=10)
    time.sleep(2)
    report = json.loads(out.read_text(encoding="utf-8"))
    report["after_parent_exit"] = {k: alive(report[k]) for k in ("grandchild_detached", "grandchild_breakaway")}
    return report


def via_claude():
    out = WORKDIR / "claude.json"
    config = WORKDIR / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"job-check": {"type": "stdio", "command": BASE_PYTHON,
                                                               "args": ["-X", "utf8", str(SERVER), str(out)]}}}), encoding="utf-8")
    claude = shutil.which("claude")
    started = time.perf_counter()
    completed = subprocess.run([claude, "-p", "「了解」とだけ答えてください。", "--mcp-config", str(config), "--strict-mcp-config",
                                "--max-turns", "1"], stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", timeout=300)
    seconds = time.perf_counter() - started
    time.sleep(3)
    if not out.exists():
        return {"error": "MCP サーバーが起動しなかった", "returncode": completed.returncode, "stderr": completed.stderr[-1500:]}
    report = json.loads(out.read_text(encoding="utf-8"))
    report["claude_returncode"] = completed.returncode
    report["claude_seconds"] = seconds
    report["server_alive_after_claude_exit"] = psutil.pid_exists(report["pid"])
    report["after_claude_exit"] = {k: alive(report[k]) for k in ("grandchild_detached", "grandchild_breakaway")}
    try:
        parent = psutil.Process(report["ppid"]) if psutil.pid_exists(report["ppid"]) else None
        report["parent_name"] = parent.name() if parent else "（終了済み）"
    except psutil.Error:
        report["parent_name"] = None
    return report


def main():
    shutil.rmtree(WORKDIR, ignore_errors=True)
    WORKDIR.mkdir(parents=True)
    sys.path.insert(0, str(HERE / "mcp_probe"))
    from job_check_server import job_info
    report = {"claude_version": subprocess.run([shutil.which("claude"), "--version"], stdin=subprocess.DEVNULL, capture_output=True,
                                               text=True, encoding="utf-8", timeout=60).stdout.strip(),
              "measuring_process_job": job_info(), "direct": direct_child(), "claude": via_claude()}
    print(json.dumps({k: v for k, v in report.items()}, ensure_ascii=False)[:3000], flush=True)
    c = report["claude"]
    report["summary"] = {
        "claude_puts_server_in_new_job": bool(c.get("job", {}).get("in_job")) and
        c.get("job", {}).get("pids_in_job") != report["measuring_process_job"].get("pids_in_job"),
        "detached_grandchild_survives_claude": c.get("after_claude_exit", {}).get("grandchild_detached"),
        "breakaway_grandchild_survives_claude": c.get("after_claude_exit", {}).get("grandchild_breakaway"),
    }
    save("claude-job-check.json", {"purpose": "Claude Code（CLI）が stdio の MCP サーバーをジョブに入れるか、セッションの終了で孫も止まるか",
                                   **report, "note": "デスクトップアプリは測っていない。測定用のプロセス自身もホストのジョブに入っている"})


if __name__ == "__main__":
    main()
