#!/usr/bin/env bash
# 破損が見つかった旧環境を保持し、独立した環境へ同じ版を再導入する。
set -euo pipefail
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
validation_root=/home/ubuntu/.cache/info-hive-validation
validation_env=${RAG_VALIDATION_ENV:-venv-serial-20261104}
validation_python="$validation_root/$validation_env/bin/python"
export UV_CACHE_DIR="$validation_root/uv-cache-clean-20261104"
export UV_CONCURRENT_INSTALLS=1 UV_CONCURRENT_DOWNLOADS=4
if [[ -e "$validation_root/$validation_env" ]]; then
  printf '%s\n' '保存済み環境の上書きを避けるため、別の RAG_VALIDATION_ENV を指定してください。' >&2
  exit 1
fi
uv venv --python /usr/bin/python3.12 "$validation_root/$validation_env"
uv pip install --python "$validation_python" --no-cache --link-mode copy \
  --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  'torch==2.8.0+cpu' 'sentence-transformers==5.7.0' 'transformers==5.22.1' \
  'numpy==2.5.4' 'mcp==1.30.0' 'lancedb==0.29.2' 'pypdfium2>=5,<6' \
  'sudachipy>=0.6,<0.8' sudachidict-core 'pyyaml>=6,<7' 'filelock>=3,<5' \
  'psutil>=7,<8' 'pillow>=11,<14' 'onnxruntime==1.31.1' reportlab py-spy
sync
"$validation_python" -X faulthandler -c 'import torch; import transformers; import sentence_transformers; print(torch.__version__, transformers.__version__, sentence_transformers.__version__, flush=True)'
export RAG_TEST_PYTHON="$validation_python"
export RAG_TEST_UV_CACHE="$UV_CACHE_DIR"
bash /mnt/c/Works/info-hive-dev/tests/rag/run_linux.sh
