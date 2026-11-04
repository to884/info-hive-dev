#!/usr/bin/env bash
# WSL の電源操作をせず、Linux の実モデルと実 MCP の試験をまとめて実行する。
set -euo pipefail
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
export RAG_TEST_RUN_ROOT=/home/ubuntu/.cache/info-hive-validation/runs
export RAG_TEST_OUTPUT=/mnt/c/Works/info-hive-dev/docs/research/rag-validation-remaining-2026-11-04/linux
export RAG_TEST_MODEL_CACHE=/mnt/c/Works/info-hive-dev/.rag-poc-data/model-cache
export RAG_TEST_FONT=/mnt/c/Windows/Fonts/meiryo.ttc
export RAG_TEST_UV_CACHE=${RAG_TEST_UV_CACHE:-/home/ubuntu/.cache/info-hive-validation/uv-cache}
export UV_CACHE_DIR="$RAG_TEST_UV_CACHE"
mkdir -p "$RAG_TEST_RUN_ROOT" "$RAG_TEST_OUTPUT"
cd /mnt/c/Works/info-hive-dev
linux_python=${RAG_TEST_PYTHON:-/home/ubuntu/.cache/info-hive-validation/venv/bin/python}
if [[ "${1:-}" != --skip-unit && "${1:-}" != --controls-only ]]; then
  "$linux_python" -m unittest discover -s tests/rag -p test_jobs.py -v > "$RAG_TEST_OUTPUT/unit.log" 2>&1
fi
if [[ "${1:-}" != --controls-only ]]; then
  "$linux_python" tests/rag/verify_pipeline.py > "$RAG_TEST_OUTPUT/pipeline.log" 2>&1
fi
export RAG_TEST_BASE_CONFIG
RAG_TEST_BASE_CONFIG=$(find "$RAG_TEST_RUN_ROOT" -maxdepth 2 -path '*/j*/config.json' -print | sort | tail -n 1)
"$linux_python" tests/rag/verify_controls.py > "$RAG_TEST_OUTPUT/controls.log" 2>&1
printf '%s\n' 'Linux の指定した試験が完了しました。'
