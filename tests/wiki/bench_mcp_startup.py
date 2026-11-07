"""wiki の MCP の起動の速さを、2 つの版のスクリプトで交互に測って比べる。

.mcp.json と同じく入口（wiki_mcp_launch.py）を `uv run --script` で起動し、次を測る。
- initialize            入口の起動、中継の環境の確かめ（uv sync、RECORD との照合、import）、中継の応答まで
- tools_list_cold       サーバーが止まっている状態からの tools/list（サーバーの環境の確かめと起動を含む）
- initialize_warm、tools_list_warm  サーバーが動いている状態で、新しいセッションを開いたとき

比べる版は、git のコミットを指定すると info-hive-wiki のそのコミットのスクリプトを一時ディレクトリに取り出す。
`work` は今の作業ツリーのスクリプトである。版ごとに INFO_HIVE_DATA_DIR を分け（版の違うサーバーを止め合わない
ように）、埋め込みはテスト用（INFO_HIVE_TEST_EMBEDDER=hash）にする。版を交互に（ABAB…）測り、測る前後の
CPU の使用率を記録する。最初の 1 回は、uv の環境を作る時間を含むので捨てる。

    uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/bench_mcp_startup.py 36a4089 work --rounds 7

結果は docs/research/wiki-mcp-startup-2026-11-07/startup.json に書く（--out で変えられる）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WIKI = ROOT / "info-hive-wiki"
SCRIPTS = "skills/info-hive/scripts"
sys.path.insert(0, str(HERE))
from mcp_stdio import StdioClient  # noqa: E402

OUT = ROOT / "docs/research/wiki-mcp-startup-2026-11-07/startup.json"


def scripts_for(version: str, temp: Path) -> Path:
    if version == "work":
        return WIKI / SCRIPTS
    archive = subprocess.run(["git", "-C", str(WIKI), "archive", "--format=tar", version, SCRIPTS],
                             capture_output=True, check=True).stdout
    dest = temp / f"wiki-{version}"
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")
    return dest / SCRIPTS


def server_pids(data: Path) -> list[psutil.Process]:
    info = data / "server.json"
    try:
        pid = json.loads(info.read_text(encoding="utf-8"))["pid"]
        return [psutil.Process(pid)]
    except (OSError, ValueError, KeyError, psutil.Error):
        return []


def stop_server(data: Path) -> None:
    for process in server_pids(data):
        try:
            process.terminate()
            process.wait(30)
        except psutil.Error:
            pass
    (data / "server.json").unlink(missing_ok=True)


def timed(fn) -> float:
    started = time.perf_counter()
    fn()
    return (time.perf_counter() - started) * 1000


def one_round(scripts: Path, data: Path) -> dict:
    command = ["uv", "run", "--quiet", "--script", str(scripts / "wiki_mcp_launch.py")]
    env = {"INFO_HIVE_DATA_DIR": str(data), "INFO_HIVE_TEST_EMBEDDER": "hash", "INFO_HIVE_MCP_IDLE_SECONDS": "600"}
    stop_server(data)
    sample = {}
    client = StdioClient(command, env)
    try:
        sample["initialize"] = timed(lambda: client.initialize(timeout=1800))
        sample["tools_list_cold"] = timed(lambda: client.tools())
    finally:
        client.close(timeout=10)
    client = StdioClient(command, env)
    try:
        sample["initialize_warm"] = timed(lambda: client.initialize(timeout=1800))
        sample["tools_list_warm"] = timed(lambda: client.tools())
    finally:
        client.close(timeout=10)
    return sample


def summary(values: list[float]) -> dict:
    ordered = sorted(values)
    p95 = ordered[min(len(ordered) - 1, max(0, round(0.95 * len(ordered)) - 1))]
    return {"n": len(ordered), "median_ms": round(statistics.median(ordered), 1), "p95_ms": round(p95, 1),
            "min_ms": round(ordered[0], 1), "max_ms": round(ordered[-1], 1)}


def busy_processes() -> list[str]:
    """CPU を取り合いそうな、ほかの作業のプロセス（rag の OCR と検証）。"""
    found = []
    for process in psutil.process_iter(["cmdline"]):
        line = " ".join(process.info["cmdline"] or [])
        if any(word in line for word in ("rag_ocr.py", "verify_pipeline.py", "rag_worker.py")):
            found.append(line[-120:])
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("versions", nargs=2, help="比べる 2 つの版（info-hive-wiki のコミットか work）")
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    temp = Path(tempfile.mkdtemp(prefix="wiki-startup-"))
    report = {"purpose": "wiki の MCP の起動の速さ（入口から initialize と tools/list まで）",
              "env": {"python": sys.version.split()[0], "platform": platform.platform(), "cpu_count": os.cpu_count(),
                      "uv": subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip()},
              "versions": {}, "rounds": []}
    try:
        variants = {}
        for version in args.versions:
            scripts = scripts_for(version, temp)
            data = temp / f"data-{version}"
            one_round(scripts, data)  # 環境を作る分を捨てる
            variants[version] = (scripts, data)
            report["versions"][version] = {"samples": []}
        for index in range(args.rounds):
            order = args.versions if index % 2 == 0 else list(reversed(args.versions))
            for version in order:
                scripts, data = variants[version]
                cpu_before = psutil.cpu_percent(interval=1.0)
                sample = one_round(scripts, data)
                sample["cpu_percent_before"] = cpu_before
                report["versions"][version]["samples"].append(sample)
                print(version, {k: round(v, 1) for k, v in sample.items()}, flush=True)
            report["rounds"].append({"round": index, "busy": busy_processes()})
        for version, entry in report["versions"].items():
            entry["summary"] = {key: summary([s[key] for s in entry["samples"]])
                                for key in ("initialize", "tools_list_cold", "initialize_warm", "tools_list_warm")}
        for _, data in variants.values():
            stop_server(data)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({v: e["summary"] for v, e in report["versions"].items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
