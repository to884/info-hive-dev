---
type: "concept"
kind: "experience-pattern"
title: "Office の COM で文書を開いて書き出すとき"
tags: ["windows"]
sources: ["office-com-word-export-2026-11-15"]
created: 2026-11-15
updated: 2026-11-15
status: "hypothesis"
---

# Office の COM で文書を開いて書き出すとき

スクリプトから Word の COM で文書を開き、PDF に書き出すときは、`Documents.Open` にパスだけを渡し、`DisplayAlerts` を 0 にし、pwsh 7 で動かす。止まったときに備えて、時間の上限を付けて別のジョブで動かし、残った `/Automation -Embedding` の WINWORD.EXE を確かめる。

## 根拠

- 観測（[[office-com-word-export-2026-11-15]]）: 読み取り専用の引数を渡した `Documents.Open` は、300 秒で終わらなかった。パスだけを渡し、pwsh 7 の `Start-Job` で動かすと書き出せた。Windows PowerShell 5.1 では、パスだけを渡しても `Documents.Open` が null を返した。PowerPoint と Excel は、同じスクリプトで書き出せた。
- 成功した例は 1 回の作業だけで、同じ条件でくり返してはいない。

## 原因と手順

- 仮説: 読み取り専用の引数で、画面に出ない確認を待ったまま止まった。Windows PowerShell 5.1 で null が返った原因は分かっていない。直前の試しの Word が残っていた影響の可能性もある。
- 手順の案: `$w.DisplayAlerts = 0`、`$w.Documents.Open($path)`、戻り値が null なら止まる、`ExportAsFixedFormat($pdf, 17)`、`Close(0)`、`Quit()`。全体を `Start-Job` と `Wait-Job -Timeout` で包む。
- 使った例: info-hive-dev の `docs/research/markitdown-benchmark-2026-11-15/scripts/export_office.ps1`（[[抽出の方式の比較-markitdown-2026-11-15]]）。

## 適用範囲と反例

Office 16.0、Windows PowerShell 5.1.26100.9711、PowerShell 7.6.9、Windows 11 で観測した。`pwsh -File` でスクリプト全体を最後まで通せるかは確かめていない。ほかの PC と Office の版では確かめていない。PowerPoint と Excel には、この問題は出なかった。
