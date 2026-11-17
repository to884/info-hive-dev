---
type: "source"
title: "経験: PowerShell の Select-Object -First が、ファイルを書く前のスクリプトを止めた（2026-11-15）"
tags: ["windows"]
raw: "raw/experiences/powershell-select-first-stops-writer-2026-11-15.json"
ingested: 2026-11-15
created: 2026-11-15
updated: 2026-11-15
---

# 経験: PowerShell の Select-Object -First が、ファイルを書く前のスクリプトを止めた（2026-11-15）

`/wiki:learn` で記録した経験である。raw は `raw/experiences/powershell-select-first-stops-writer-2026-11-15.json`（ファイルの SHA-256 は `98166a9dffbcfda5d58b38156f594710ec2da64ca32e840288ffb00a6ef32f26`）。結果は failure。

## 観測したこと

- `uv run --script scripts/run_bench.py --metrics-only 2>&1 | Select-Object -First 1` で実行すると、1 行目は出たが、`results.json` の `versions.pdftotext` は書き直す前の文字列のままだった。
- 同じコマンドを `Select-Object -Last 1` で実行し直すと、`versions.pdftotext` が書き直された。
- スクリプトは、すべての行を出したあとに `results.json` を書く。

## 原因についての仮説

`Select-Object -First` は、必要な数の行を受け取るとパイプラインの上流を止めるので、ファイルを書く前にスクリプトが止まったと考えられる（仮説）。

## 適用範囲と反例

PowerShell 7.6.9（Claude Code の PowerShell ツール）、uv 0.12.2、Python 3.12.13 で観測した。`-Last` では止まらなかった。Bash の `head` でも同じことが起きうるかは確かめていない。

## 関係するページ

- [[powershellのパイプの打ち切り]]
