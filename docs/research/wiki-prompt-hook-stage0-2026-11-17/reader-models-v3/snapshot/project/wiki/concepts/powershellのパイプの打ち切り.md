---
type: "concept"
kind: "experience-pattern"
title: "PowerShell の Select-Object -First は、上流のスクリプトを止める"
tags: ["windows"]
sources: ["powershell-select-first-stops-writer-2026-11-15"]
created: 2026-11-15
updated: 2026-11-15
status: "hypothesis"
---

# PowerShell の Select-Object -First は、上流のスクリプトを止める

PowerShell で、最後にファイルを書くスクリプトの出力を `Select-Object -First N` でしぼると、N 行を受け取ったところで上流が止まり、ファイルが書かれないことがある。出力を短く見たいときは、`Select-Object -Last N` にするか、出力をファイルに書いてから読む。実行のあとで、書くはずのファイルが変わったかを確かめる。

## 根拠

- 観測（[[powershell-select-first-stops-writer-2026-11-15]]）: `uv run --script run_bench.py --metrics-only 2>&1 | Select-Object -First 1` のあと、`results.json` は書き直されていなかった。`Select-Object -Last 1` で実行し直すと書き直された。エラーは出ず、1 行目は正しく出たので、止まったことに気づきにくい。

## 原因と手順

- 仮説: `Select-Object -First` は、必要な数の行を受け取るとパイプラインの上流を止める。上流のスクリプトは、最後の書き込みの前に止まる。
- 手順の案: ファイルを書くスクリプトには `-First` を付けない。付けるなら、書き込みを出力より先にするか、実行のあとでファイルの更新を確かめる。

## 適用範囲と反例

PowerShell 7.6.9（Claude Code の PowerShell ツール）で、uv と Python の子プロセスを動かしたときに観測した。`-Last` では止まらなかった。Bash の `head` で同じことが起きるかは確かめていない。Windows PowerShell 5.1 では確かめていない。
