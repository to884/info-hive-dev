"""Windows で wiki の MCP サーバーを起動したときに、画面（コンソールの窓）が出ないかを確かめる（info-hive-wiki#36）。

入口の `wiki_mcp_launch.py --ensure` で、ホストと同じ経路（入口 → 中継 → サーバー）でサーバーを起動する。
起動のあいだ 0.1 秒ごとに見えるトップレベルの窓を数え、起動の前になかった窓が 1 つでも出たら失敗にする。
窓の題は見ない（Windows Terminal の設定によっては、題がプログラムのパスにならない）。同じ時間に別のアプリが
窓を開くと誤って失敗になるので、出た窓の題、持ち主のプロセス、出た時刻を見て判断する。0.1 秒より短いあいだだけ
出て消える窓は、見逃すことがある。

- 既定（`--entry uv`）: .mcp.json と同じく `uv run --script` で入口を起動する。
- `--entry detached`: 入口を、コンソールを持たないプロセス（DETACHED_PROCESS）として、base の python で直接起動する。
  ホストがコンソールなしで MCP サーバーを起動する場合に当たる。uv の環境の用意（uv sync など）、中継の起動、
  サーバーの起動が出す窓を見る。

あわせて、入口と中継が終わった後もサーバーが残って応答するか、`stop_server` と同じ terminate で止まるかを見る。

データの置き場所（INFO_HIVE_DATA_DIR）は一時ディレクトリにする。既定の置き場所で動いている、版の違うサーバーを
止めないためである。uv の環境は既定のものを使うので、初回はサーバーの依存の用意に時間がかかる。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_server_console.py [--entry uv|detached] [--plugin <info-hive-wiki>]

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


def visible_windows() -> dict[int, tuple[str, int]]:
    """見えるトップレベルの窓の、題と持ち主のプロセスの pid。"""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found: dict[int, tuple[str, int]] = {}

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            found[int(hwnd or 0)] = (buffer.value, pid.value)
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


def start_entry(entry: str, launch: Path, env: dict, out, err) -> subprocess.Popen:
    # 出力はファイルに書く。パイプにすると、読まないあいだに詰まって入口が止まることがある。
    if entry == "uv":
        return subprocess.Popen(["uv", "run", "--quiet", "--script", str(launch), "--ensure"],
                                stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=env)
    # 入口は標準ライブラリだけで動く。venv の python.exe は本体を子として起動し、それ自体が窓を出すので、
    # base の python で直接起動する。
    python = getattr(sys, "_base_executable", sys.executable)
    return subprocess.Popen([python, "-X", "utf8", str(launch), "--ensure"], stdin=subprocess.DEVNULL,
                            stdout=out, stderr=err, env=env,
                            creationflags=subprocess.DETACHED_PROCESS)


def main() -> int:
    if os.name != "nt":
        print("Windows だけで確かめる", file=sys.stderr)
        return 2
    import psutil

    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", type=Path, default=ROOT / "info-hive-wiki")
    parser.add_argument("--entry", choices=("uv", "detached"), default="uv")
    parser.add_argument("--settle", type=float, default=3.0, help="起動の後も窓を数え続ける秒数")
    args = parser.parse_args()
    launch = args.plugin.resolve() / "skills/info-hive/scripts/wiki_mcp_launch.py"

    with tempfile.TemporaryDirectory(prefix="wiki-console-") as data:
        env = {**os.environ, "PYTHONUTF8": "1", "INFO_HIVE_DATA_DIR": data}
        before = visible_windows()
        seen: dict[int, dict] = {}

        def look():
            for hwnd, (title, owner) in visible_windows().items():
                if hwnd not in before and hwnd not in seen:
                    try:
                        name = psutil.Process(owner).name()
                    except psutil.Error:
                        name = "?"
                    seen[hwnd] = {"title": title, "owner_pid": owner, "owner": name,
                                  "at_seconds": round(time.perf_counter() - started, 2)}

        out_path, err_path = Path(data) / "ensure.out", Path(data) / "ensure.err"
        with open(out_path, "wb") as out, open(err_path, "wb") as err:
            started = time.perf_counter()
            process = start_entry(args.entry, launch, env, out, err)
            while process.poll() is None and time.perf_counter() - started < 3600:
                look()
                time.sleep(0.1)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=60)
        stderr = err_path.read_bytes()
        seconds = round(time.perf_counter() - started, 1)
        ends = time.monotonic() + args.settle
        while time.monotonic() < ends:
            look()
            time.sleep(0.1)
        result: dict = {"plugin": str(args.plugin), "entry": args.entry, "ensure_returncode": process.returncode,
                        "ensure_seconds": seconds, "new_windows": list(seen.values())}
        info_path = Path(data) / "server.json"
        if process.returncode != 0 or not info_path.exists():
            result["stderr"] = stderr.decode("utf-8", "replace")[-2000:]
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
    ok = not result["new_windows"] and result["alive_after_relay_exit"] and result["stopped"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
