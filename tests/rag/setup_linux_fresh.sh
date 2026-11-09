#!/usr/bin/env bash
# Linux（WSL）の検証環境を作り直し、run_linux.sh を流す。
# 既定の置き場所は tmpfs（/dev/shm）。WSL の仮想ディスクが遅い HDD にあっても、
# Python、依存、モデル、uv のキャッシュ、試験のデータを RAM から読める。
# tmpfs は WSL を止めると消えるので、そのあとはこのスクリプトから流し直す。
#   bash tests/rag/setup_linux_fresh.sh             作り直して、すべての試験を流す
#   bash tests/rag/setup_linux_fresh.sh --setup-only 作り直すだけ
# 環境変数
#   RAG_LINUX_ROOT          置き場所（既定 /dev/shm/info-hive-validation）
#   RAG_TEST_MODEL_SOURCE   既存の Hugging Face のキャッシュ。あれば ruri-v3-30m を写す
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.local/bin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
linux_root=${RAG_LINUX_ROOT:-/dev/shm/info-hive-validation}
export UV_CACHE_DIR=${RAG_TEST_UV_CACHE:-$linux_root/uv-cache}
export UV_PYTHON_INSTALL_DIR=${UV_PYTHON_INSTALL_DIR:-$linux_root/python}
export UV_PYTHON_PREFERENCE=only-managed
# ~/.local/bin に python3.12 の入口を作らない。
export UV_PYTHON_BIN_DIR=${UV_PYTHON_BIN_DIR:-$linux_root/bin}
export TMPDIR=${RAG_TEST_TMPDIR:-$linux_root/tmp}
venv="$linux_root/venv"
models=${RAG_TEST_MODEL_CACHE:-$linux_root/models}
# PoC データ（既定は開発用リポジトリの本体の隣の info-hive-dev-data/rag-poc-data）にあるモデルを既定の写し元にする。
# 置き場所は poc/poc_data.py と同じ決め方で、INFO_HIVE_POC_DATA で変えられる（WSL のパスで書く）。
# worktree の .git は Windows のパスを指し、WSL の git では読めないので、パスから本体を求める。
common_root=${repo_root%%/.claude/worktrees/*}
poc_data=${INFO_HIVE_POC_DATA:-$(dirname "$common_root")/info-hive-dev-data/rag-poc-data}
model_source=${RAG_TEST_MODEL_SOURCE:-$poc_data/model-cache}
model=models--cl-nagoya--ruri-v3-30m

if [[ -e "$venv" ]]; then
  # 前回の venv は消して作り直す。uv のキャッシュとモデルは使い回す。
  rm -rf -- "$venv"
fi
mkdir -p "$linux_root" "$UV_CACHE_DIR" "$TMPDIR" "$models"
uv python install 3.12
uv venv --python 3.12 "$venv"
# rag_server.py の依存（PEP 723）に、試験だけで使う reportlab を足す。版は 0.5.0 の Windows の検証と合わせる。
uv pip install --python "$venv/bin/python" \
  --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  'torch==2.8.0+cpu' 'sentence-transformers==5.7.0' 'transformers==5.22.1' \
  'numpy==2.5.4' 'mcp==1.30.0' 'lancedb==0.29.2' 'pypdfium2>=5,<6' \
  'sudachipy>=0.6,<0.8' sudachidict-core 'pyyaml>=6,<7' 'filelock>=3,<5' \
  'psutil>=7,<8' 'pillow>=11,<14' 'onnxruntime==1.31.1' reportlab
if [[ ! -d "$models/$model" && -d "$model_source/$model" ]]; then
  cp -r -- "$model_source/$model" "$models/"
fi
# OCR（rag_ocr.py）と配布の起動（rag_server.py、verify_controls が使う）の uv の環境を先に作る。
# 試験の中で初めて作ると、その時間が待ち時間の上限に食い込む。
uv sync --script "$repo_root/info-hive-rag/scripts/rag_ocr.py"
uv sync --script "$repo_root/info-hive-rag/scripts/rag_server.py"
"$venv/bin/python" -X faulthandler -c 'import torch, transformers, sentence_transformers; print(torch.__version__, transformers.__version__, sentence_transformers.__version__, flush=True)'
if [[ "${1:-}" == --setup-only ]]; then
  exit 0
fi
export RAG_LINUX_ROOT="$linux_root" RAG_TEST_UV_CACHE="$UV_CACHE_DIR" RAG_TEST_MODEL_CACHE="$models"
exec bash "$repo_root/tests/rag/run_linux.sh" "$@"
