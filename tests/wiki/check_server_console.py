"""Windows で wiki の MCP サーバーを起動したときに、画面（コンソールの窓）が出ないかを確かめる（info-hive-wiki#36）。

入口の `wiki_mcp_launch.py --ensure` で、ホストと同じ経路（入口 → 中継 → サーバー）でサーバーを起動する。
起動の前後で見えるトップレベルの窓を比べ、題にサーバーの環境の名前（wiki-mcp-server）が入る窓が出ていないかを見る。
既定のターミナルが Windows Terminal なら、出た窓の題は venv の `Scripts\\python.exe` のパスになる。

あわせて、入口と中継が終わった後もサーバーが残って応答するか、`stop_server` と同じ terminate で止まるかを見る。

データの置き場所（INFO_HIVE_DATA_DIR）は一時ディレクトリにする。既定の置き場所で動いている、版の違うサーバーを
止めないためである。uv の環境は既定のものを使うので、初回はサーバーの依存の用意に時間がかかる。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_server_console.py [--plugin <info-hive-wiki>]

結果は標準出力に JSON で書く。窓が出たか、サーバーが残らなかったときは、終了コード 1 を返す。
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = "wiki-mcp-server"


def visible_windows() -> dict[int, str]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found: dict[int, str] = {}

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            found[int(hwnd or 0)] = buffer.value
        return True

    user32.EnumWindows(enum_proc(callback), 0)
    return found


def responds(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def tree(pid: int) -> list[dict]:
    import psutil
    root = psutil.Process(pid)
    return [{"pid": p.pid, "ppid": p.ppid(), "name": p.name(), "exe": p.exe()}
            for p in [root, *root.children(recursive=True)]]


def main() -> int:
    if os.name != "nt":
        print("Windows だけで確かめる", file=sys.stderr)
        return 2
    import psutil

    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", type=Path, default=ROOT / "info-hive-wiki")
    parser.add_argument("--settle", type=float, default=3.0, help="起動の後、窓を数えるまでに待つ秒数")
    args = parser.parse_args()
    launch = args.plugin.resolve() / "skills/info-hive/scripts/wiki_mcp_launch.py"

    with tempfile.TemporaryDirectory(prefix="wiki-console-") as data:
        env = {**os.environ, "PYTHONUTF8": "1", "INFO_HIVE_DATA_DIR": data}
        before = visible_windows()
        started = time.perf_counter()
        out = subprocess.run(["uv", "run", "--quiet", "--script", str(launch), "--ensure"], stdin=subprocess.DEVNULL,
                             capture_output=True, env=env, timeout=3600)
        seconds = round(time.perf_counter() - started, 1)
        time.sleep(args.settle)
        new = [title for hwnd, title in visible_windows().items() if hwnd not in before]
        result: dict = {"plugin": str(args.plugin), "ensure_returncode": out.returncode, "ensure_seconds": seconds,
                        "new_windows": new, "server_windows": [t for t in new if MARKER in t]}
        info_path = Path(data) / "server.json"
        if out.returncode != 0 or not info_path.exists():
            result["stderr"] = out.stderr.decode("utf-8", "replace")[-2000:]
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        info = json.loads(info_path.read_text(encoding="utf-8"))
        pid, port = int(info["pid"]), int(info["port"])
        # --ensure の入口と中継は、ここではもう終わっている。サーバーが残って応答するかを見る。
        result["alive_after_relay_exit"] = psutil.pid_exists(pid) and responds(port)
        result["server_tree"] = tree(pid) if psutil.pid_exists(pid) else []
        # 中継の stop_server と同じく terminate で止める。
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=30)
        except psutil.Error:
            pass
        result["stopped"] = not psutil.pid_exists(pid)
        time.sleep(1)  # サーバーが止まり、一時ディレクトリのファイルを手放すのを待つ
    print(json.dumps(result, ensure_ascii=False, indent=2))
    ok = not result["server_windows"] and result["alive_after_relay_exit"] and result["stopped"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
