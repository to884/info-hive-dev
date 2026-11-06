"""初めて使う人の最初のセッションで、wiki の MCP サーバーの依存の取得がホストの待ち時間に収まるかを確かめる。

uv のキャッシュ（UV_CACHE_DIR）とデータの置き場所（INFO_HIVE_DATA_DIR）を空の一時ディレクトリにして、
`claude -p --plugin-dir <info-hive-wiki>` を 2 回実行する。埋め込みはテスト用のものにせず、本物のモデルを取得させる。

1. 最初のセッション（cold）: 中継の依存、サーバーの依存（約 1 GB）を取得するところから始まる。
   ホストが MCP のサーバーを「connected」と見て、ツールを一覧に出すか。出なければ CLI に戻って答えるか。
2. 2 回目のセッション（warm）: 1 回目のあとに残った取得の続きと、サーバーの起動を待ってから実行する。
   ツールを使って答えるか。

ダウンロードが約 1.5 GB ある。結果は docs/research/wiki-mcp-server-2026-11-06/first-run-mcp.json に書く。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_first_run_mcp.py
"""
from __future__ import annotations

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
sys.path.insert(0, str(HERE))
import check_commands_mcp as base  # noqa: E402

OUT = base.ROOT / "docs/research/wiki-mcp-server-2026-11-06/first-run-mcp.json"
RELAY = base.PLUGIN / "skills/info-hive/scripts/wiki_mcp_relay.py"


def wait_server(env: dict, timeout: float) -> dict:
    """中継の --ensure で、サーバーの依存の取得とサーバーの起動が終わるまで待つ。"""
    started = time.perf_counter()
    out = subprocess.run(["uv", "run", "--quiet", "--script", str(RELAY), "--ensure"], capture_output=True,
                         timeout=timeout, env={**os.environ, "PYTHONUTF8": "1", **env})
    return {"returncode": out.returncode, "seconds": round(time.perf_counter() - started, 1),
            "stdout_tail": out.stdout.decode("utf-8", "replace")[-400:],
            "stderr_tail": out.stderr.decode("utf-8", "replace")[-400:]}


def main() -> None:
    claude = base.find_claude()
    report = {"purpose": "初めて使う人の最初のセッションで、MCP のサーバーの依存の取得がホストの待ち時間に収まるか",
              "platform": platform.platform(),
              "claude_version": subprocess.run([claude, "--version"], capture_output=True, text=True,
                                               encoding="utf-8").stdout.strip(),
              "plugin_commit": subprocess.run(["git", "-C", str(base.PLUGIN), "describe", "--always", "--dirty"],
                                              capture_output=True, text=True).stdout.strip(),
              "mcp_timeout_env": os.environ.get("MCP_TIMEOUT"), "runs": []}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        temp = Path(temp)
        project = temp / "project"
        shutil.copytree(base.CORPUS, project / "wiki")
        wiki = (project / "wiki").resolve()
        data = temp / "data"
        env = {"INFO_HIVE_DATA_DIR": str(data), "UV_CACHE_DIR": str(temp / "uv-cache"),
               "INFO_HIVE_MCP_IDLE_SECONDS": "120"}
        stats = base.COMMANDS[0][1].format(wiki=wiki.as_posix())
        query = base.COMMANDS[1][1].format(wiki=wiki.as_posix())

        cold = base.run_command(claude, base.PLUGIN, project, stats, env, wiki)
        report["runs"].append({"session": "cold", "command": "stats", **cold,
                               "server_json_after": (data / "server.json").is_file()})
        print(f"cold stats: mcp_servers={cold['mcp_servers']} tools={cold['tools']} "
              f"seconds={cold['seconds']}", flush=True)

        report["wait_server"] = wait_server(env, timeout=2400)
        print(f"サーバーの用意: {report['wait_server']['seconds']} 秒", flush=True)

        warm = base.run_command(claude, base.PLUGIN, project, query, env, wiki)
        report["runs"].append({"session": "warm", "command": "query", **warm})
        print(f"warm query: mcp_servers={warm['mcp_servers']} tools={warm['tools']} "
              f"seconds={warm['seconds']}", flush=True)
        log = data / "logs" / "server.log"
        report["server_log_tail"] = log.read_text("utf-8", "replace")[-1500:] if log.is_file() else None
        # 一時ディレクトリを消す前に、サーバーを止める（Windows では開いているファイルを消せない）。
        info_path = data / "server.json"
        if info_path.is_file():
            try:
                import psutil
                psutil.Process(int(json.loads(info_path.read_text("utf-8"))["pid"])).terminate()
                time.sleep(2)
            except Exception:  # noqa: BLE001
                pass

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
