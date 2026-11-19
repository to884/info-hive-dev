#!/usr/bin/env bash
# 既存の隔離環境を使い、今回の回帰試験だけを別の場所に記録する。
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
validation_root=/home/ubuntu/.cache/info-hive-validation/ann-20261119-clean
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
export RAG_TEST_RUN_ROOT="$validation_root/cache-retirement-20261120"
mkdir -p "$RAG_TEST_RUN_ROOT"
cd "$repo_root"
"$validation_root/venv/bin/python" -B -X utf8 -m unittest discover -s tests/rag -p 'test_*.py' -v > docs/research/rag-cache-retirement-2026-11-20/unit-linux.log 2>&1
