"""統一の決定のための追加測定の共通部品。配布対象ではない。

../unification の部品（common、backends、db_bench、runtime_parity、summarize）をそのまま使う。
測定データの場所は INFO_HIVE_POC_DATA で渡す（common.POC_DATA）。
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNIFICATION = HERE.parent / "unification"
sys.path.insert(0, str(UNIFICATION))

from common import POC_DATA, ROOT, THREADS, WORK, read_json, write_json  # noqa: E402

OUT_D = ROOT / "docs/research/embedding-backend-decision-2026-11-06"
DWORK = POC_DATA / "decision-20261106"
WIKI_SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
WIKI_EVAL = ROOT / "info-hive-wiki/eval/retrieval"
R130_ONNX = WORK / "onnx/R-130/onnx-fp32"
PACKAGES = ["numpy", "usearch", "faiss-cpu", "tantivy", "fastembed", "onnxruntime", "sqlite-vec", "sudachipy", "psutil", "mcp"]


def _version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
    except OSError:
        return None


def gpu_busy():
    """GPU で別の仕事が動いていないことを記録する。nvidia-smi がなければ None。"""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, encoding="utf-8", timeout=10).stdout.strip()
        utilization, memory = (int(v) for v in out.split(","))
        return {"utilization_percent": utilization, "memory_used_mib": memory}
    except Exception:
        return None


def env():
    return {"python": platform.python_version(), "platform": platform.platform(), "cpu_threads_limit": THREADS,
            "logical_cpus": os.cpu_count(), "packages": {p: _version(p) for p in PACKAGES},
            "dev_commit": _git("rev-parse", "--short", "HEAD"),
            "wiki_commit": _git("-C", "info-hive-wiki", "rev-parse", "--short", "HEAD"),
            "rag_commit": _git("-C", "info-hive-rag", "rev-parse", "--short", "HEAD"),
            "poc_data": str(POC_DATA), "gpu": gpu_busy()}


def save(name, value):
    write_json(OUT_D / name, {"env": env(), **value})
    print("保存した", OUT_D / name, flush=True)


def load(name):
    return read_json(OUT_D / name)
