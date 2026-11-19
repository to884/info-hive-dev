#!/usr/bin/env bash
# Linux の実索引と MCP の回帰試験。全量の試験データとは別の保存先を使う。
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
linux_root=/home/ubuntu/.cache/info-hive-validation/ann-20261119-clean
out="$repo_root/docs/research/rag-full-ann-2026-11-19/linux"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
export UV_CACHE_DIR="$linux_root/uv-cache"
mkdir -p "$linux_root/runs" "$out"
if [[ ! -x "$linux_root/venv/bin/python" ]]; then
  uv venv --python 3.12 "$linux_root/venv"
fi
uv pip install --python "$linux_root/venv/bin/python" \
  --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  'torch==2.8.0+cpu' 'sentence-transformers==5.7.0' 'transformers==5.22.1' \
  'numpy==2.5.4' 'mcp==1.30.0' 'lancedb==0.29.2' 'pypdfium2>=5,<6' \
  'sudachipy>=0.6,<0.8' sudachidict-core 'pyyaml>=6,<7' 'filelock>=3,<5' \
  'psutil>=7,<8' 'pillow>=11,<14' 'onnxruntime==1.31.1' reportlab
export RAG_TEST_RUN_ROOT="$linux_root/runs"
export RAG_TEST_OUTPUT="$out"
export RAG_TEST_MODEL_CACHE=/mnt/c/Works/info-hive-dev-data/rag-poc-data/model-cache
export INFO_HIVE_POC_DATA=/mnt/c/Works/info-hive-dev-data/rag-poc-data
export HF_HUB_OFFLINE=1
export RAG_TEST_FONT=/mnt/c/Windows/Fonts/meiryo.ttc
cd "$repo_root"
"$linux_root/venv/bin/python" -B -X utf8 -m unittest discover -s tests/rag -p 'test_*.py' -v > "$out/unit.log" 2>&1
"$linux_root/venv/bin/python" -B -X utf8 tests/rag/verify_auto_indexes.py > "$out/auto-indexes.log" 2>&1
