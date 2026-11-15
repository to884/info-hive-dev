#!/usr/bin/env bash
# 1 つのブラウザで browse.test.mjs と findability.test.mjs を、静的とサーバーの両方の方式で流す。
# 使い方（開発リポジトリのルートで）: bash docs/agent-runs/2026-11-15-wiki-browse-cross-browser/run.sh <ブラウザ>
# ブラウザは firefox、webkit、msedge、chrome のどれか。結果はこのディレクトリに書く。
set -u
name="$1"
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here/../../../tests/wiki/browse"
for t in browse findability; do
  start=$(date +%s)
  BROWSERS="$name" OUT="$here/$t-$name.json" node "$t.test.mjs" > "$here/$t-$name.log" 2>&1
  code=$?
  echo "$t $name exit=$code sec=$(( $(date +%s) - start ))" >> "$here/summary-$name.txt"
done
