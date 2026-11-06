"""M4（副次）: 組ごとの依存を、空の uv キャッシュから `uv run --script` で準備する時間と容量を測る。

基準は現行の info-hive-rag/scripts/rag_server.py の PEP 723 宣言。PDF・OCR・MCP など、
埋め込みとベクター DB に関わらない依存は全構成で共通にして、差が埋め込みと DB だけから出るようにする。
1 回目は空のキャッシュ（ダウンロードを含む）、2 回目は同じキャッシュでの再準備。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time

from common import OUT, WORK, directory_bytes, write_json

COMMON = ['"mcp>=1.28,<2"', '"pypdfium2>=5,<6"', '"sudachipy>=0.6,<0.8"', '"sudachidict-core"', '"pyyaml>=6,<7"',
          '"filelock>=3,<5"', '"psutil>=7,<8"', '"numpy>=2,<3"', '"pillow>=11,<14"', '"onnxruntime>=1.31,<2"']
TORCH = ['"sentence-transformers>=5,<6"', '"torch==2.8.0"']
FASTEMBED = ['"fastembed==0.8.0"']
TANTIVY = ['"tantivy==0.27.0"']
DATABASES = {"LanceDB": ['"lancedb>=0.25,<0.30"'], "sqlite-vec": ['"sqlite-vec==0.1.9"'], "Qdrant": ['"qdrant-client==1.20.0"'],
             "usearch": ['"usearch==2.26.6"'], "FAISS": ['"faiss-cpu==1.15.1"'], "Chroma": ['"chromadb==1.5.9"']}
TORCH_INDEX = """# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
"""


def configurations():
    yield "共通のみ", COMMON, False
    yield "現行 rag（torch + LanceDB）", COMMON + TORCH + DATABASES["LanceDB"], True
    yield "torch のみ", COMMON + TORCH, True
    yield "fastembed のみ", COMMON + FASTEMBED, False
    for name, packages in DATABASES.items():
        yield f"fastembed + {name}", COMMON + FASTEMBED + packages, False
    for name in ("FAISS", "usearch", "sqlite-vec"):
        yield f"fastembed + {name} + Tantivy", COMMON + FASTEMBED + DATABASES[name] + TANTIVY, False


def script(packages, torch):
    header = "# /// script\n# requires-python = \">=3.12,<3.13\"\n# dependencies = [\n#   " + ", ".join(packages) + ",\n# ]\n"
    return header + (TORCH_INDEX if torch else "") + "# ///\nprint('ready')\n"


def main():
    root = WORK / "install"
    results = []
    for name, packages, torch in configurations():
        folder = root / name.replace(" ", "_").replace("（", "_").replace("）", "").replace("+", "_")
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        path = folder / "probe.py"
        path.write_text(script(packages, torch), encoding="utf-8")
        cache = folder / "uv-cache"
        env = {**os.environ, "UV_CACHE_DIR": str(cache), "UV_LINK_MODE": "copy", "PYTHONUTF8": "1"}
        runs = []
        for attempt in ("空のキャッシュ", "同じキャッシュ"):
            started = time.perf_counter()
            completed = subprocess.run(["uv", "run", "--no-project", "--script", str(path)], capture_output=True, text=True, encoding="utf-8", env=env)
            runs.append({"run": attempt, "seconds": time.perf_counter() - started, "returncode": completed.returncode,
                         "stderr_tail": completed.stderr[-400:] if completed.returncode else ""})
        environments = cache / "environments-v2"
        record = {"configuration": name, "packages": [p.strip('"') for p in packages], "runs": runs,
                  "cache_bytes": directory_bytes(cache), "environment_bytes": directory_bytes(environments) if environments.exists() else None}
        print(name, [round(r["seconds"]) for r in runs], round(record["cache_bytes"] / 2 ** 20), "MiB", flush=True)
        results.append(record)
        shutil.rmtree(cache, ignore_errors=True)
        write_json(OUT / "install-results.json", {"python": "3.12", "uv": subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip(),
                                                   "note": "ネットワークの速さに左右される。空のキャッシュの値はダウンロードを含む。environment_bytes は uv が作った実行環境の容量",
                                                   "results": results})


if __name__ == "__main__":
    main()
