#!/usr/bin/env bash
# WSL の電源操作をせず、Linux の実モデルと実 MCP の試験をまとめて実行する。
# 環境は setup_linux_fresh.sh で作る。置き場所は RAG_LINUX_ROOT で変えられる。
#   bash tests/rag/run_linux.sh                 単体試験、verify_pipeline、verify_controls
#   bash tests/rag/run_linux.sh --skip-unit     単体試験を省く
#   bash tests/rag/run_linux.sh --controls-only verify_controls だけ
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.local/bin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
# 既定は tmpfs。WSL の仮想ディスクが遅い HDD にあると、torch の読み込みだけで数分かかる。
linux_root=${RAG_LINUX_ROOT:-/dev/shm/info-hive-validation}
export RAG_TEST_RUN_ROOT=${RAG_TEST_RUN_ROOT:-$linux_root/runs}
export RAG_TEST_OUTPUT=${RAG_TEST_OUTPUT:-$repo_root/docs/research/rag-0.5.0-linux-verification-2026-11-08/linux}
export RAG_TEST_MODEL_CACHE=${RAG_TEST_MODEL_CACHE:-$linux_root/models}
export RAG_TEST_FONT=${RAG_TEST_FONT:-/mnt/c/Windows/Fonts/meiryo.ttc}
# ほかのセッションと uv のキャッシュを共有すると verify_controls が止まるので、専用にする。
export RAG_TEST_UV_CACHE=${RAG_TEST_UV_CACHE:-$linux_root/uv-cache}
export UV_CACHE_DIR="$RAG_TEST_UV_CACHE"
# OCR と verify_controls の uv run も、同じ場所の Python を使う。
export UV_PYTHON_INSTALL_DIR=${UV_PYTHON_INSTALL_DIR:-$linux_root/python}
export UV_PYTHON_PREFERENCE=only-managed
export TMPDIR=${RAG_TEST_TMPDIR:-$linux_root/tmp}
linux_python=${RAG_TEST_PYTHON:-$linux_root/venv/bin/python}
if [[ ! -x "$linux_python" ]]; then
  printf '%s\n' "検証用の Python がありません: $linux_python" 'tests/rag/setup_linux_fresh.sh で環境を作ってください。' >&2
  exit 1
fi
mkdir -p "$RAG_TEST_RUN_ROOT" "$RAG_TEST_OUTPUT" "$TMPDIR"
cd "$repo_root"
# pdfium は最初のページを読むときに、システムのフォントのフォルダーを全部開いて調べる
# （試験の PDF は CID フォントを埋め込まない）。フォントが遅いディスクにあると十数秒かかるので、
# 先にページキャッシュへ読み込む。
fonts_started=$SECONDS
for folder in /usr/share/fonts /usr/share/X11/fonts /usr/local/share/fonts; do
  [[ -d "$folder" ]] && find -L "$folder" -type f -exec cat {} + > /dev/null 2>&1 || true
done
printf '%s\n' "フォントの先読み: $((SECONDS - fonts_started)) 秒"
{
  printf 'date=%s\n' "$(date --iso-8601=seconds)"
  printf 'repo=%s\n' "$repo_root"
  printf 'rag_version=%s\n' "$(grep -o '"version": *"[^"]*"' info-hive-rag/.claude-plugin/plugin.json | cut -d'"' -f4)"
  # worktree の .git は Windows のパスを指すことがある。読めなければ Windows の git に聞く。
  printf 'rag_commit=%s\n' "$(git -C info-hive-rag rev-parse HEAD 2>/dev/null || git.exe -C "$(wslpath -w info-hive-rag)" rev-parse HEAD)"
  printf 'linux_root=%s\n' "$linux_root"
  printf 'kernel=%s\n' "$(uname -r)"
  "$linux_python" -c 'import sys; from importlib.metadata import version; print("python=" + sys.version.split()[0]); [print(f"{name}={version(name)}") for name in ("torch", "transformers", "sentence-transformers", "pypdfium2", "lancedb", "mcp", "onnxruntime")]'
  uv --version
} > "$RAG_TEST_OUTPUT/environment.txt" 2>&1 || true
run() {
  local name=$1; shift
  local started=$SECONDS status=0
  "$@" > "$RAG_TEST_OUTPUT/$name.log" 2>&1 || status=$?
  printf '%s exit=%s seconds=%s\n' "$name" "$status" "$((SECONDS - started))" | tee -a "$RAG_TEST_OUTPUT/summary.txt"
  (( status == 0 )) || failed=1
}
failed=0
: > "$RAG_TEST_OUTPUT/summary.txt"
if [[ "${1:-}" != --skip-unit && "${1:-}" != --controls-only ]]; then
  run unit "$linux_python" -m unittest discover -s tests/rag -p 'test_*.py' -v
fi
if [[ "${1:-}" != --controls-only ]]; then
  run pipeline "$linux_python" tests/rag/verify_pipeline.py
fi
export RAG_TEST_BASE_CONFIG
RAG_TEST_BASE_CONFIG=$(find "$RAG_TEST_RUN_ROOT" -maxdepth 2 -path '*/j*/config.json' -print | sort | tail -n 1)
run controls "$linux_python" tests/rag/verify_controls.py
if (( failed )); then
  printf '%s\n' "失敗した試験があります。$RAG_TEST_OUTPUT のログを確かめてください。" >&2
  exit 1
fi
printf '%s\n' 'Linux の指定した試験がすべて通りました。'
