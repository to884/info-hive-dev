---
type: "source"
title: "経験: Word の COM で PDF に書き出すとき、Documents.Open が止まるか null を返した（2026-11-15）"
tags: ["windows"]
raw: "raw/experiences/office-com-word-export-2026-11-15.json"
ingested: 2026-11-15
created: 2026-11-15
updated: 2026-11-15
---

# 経験: Word の COM で PDF に書き出すとき、Documents.Open が止まるか null を返した（2026-11-15）

`/wiki:learn` で記録した経験である。raw は `raw/experiences/office-com-word-export-2026-11-15.json`（ファイルの SHA-256 は `c8825524ce099170f210b1ec9d428d144ae523161672efffc64ae7aad7dccf5a`）。結果は failure。スクリプトは `docs/research/markitdown-benchmark-2026-11-15/scripts/export_office.ps1` にある。

## 観測したこと

- Windows PowerShell 5.1（`powershell -File`）で、`Documents.Open(パス, $false, $true)`（読み取り専用）で開くと、300 秒で終わらず、PDF もできなかった。`/Automation -Embedding` の WINWORD.EXE が残っていた。
- pwsh 7 の `Start-Job` の中で、`DisplayAlerts = 0` にし、パスだけを渡すと、開いて書き出せた。
- 引数をパスだけにしたスクリプトを、Windows PowerShell 5.1 で動かすと、`Documents.Open` が null を返した。同じ実行で、PowerPoint と Excel の書き出しは成功した。
- Word の 2 つの PDF は、pwsh 7 の `Start-Job` で書き出した。

## 原因についての仮説

読み取り専用の引数で、画面に出ない確認を待ったまま止まったと考えられる。null を返した原因は分かっていない。直前の試しで開いた Word が終わらずに残っていた影響の可能性もある（どちらも確かめていない）。

## 適用範囲と反例

スクリプトから Office の COM で文書を開いて書き出すとき。Office 16.0、Windows PowerShell 5.1.26100.9711、PowerShell 7.6.9、Windows 11 で観測した。`pwsh -File` で最後まで通るかは確かめていない。PowerPoint と Excel では問題がなかった。

## 関係するページ

- [[officeのcomでの書き出し]]
