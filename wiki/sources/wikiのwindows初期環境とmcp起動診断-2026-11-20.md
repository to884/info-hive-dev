---
type: "source"
title: "wiki の Windows 初期環境と MCP 起動診断（2026-11-20）"
authors: ["info-hive-dev"]
tags: ["試験", "コマンド"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/wikiのwindows初期環境とmcp起動診断-2026-11-20.md"
raw_sha256: "5f1111992d9937bbf4935b417e14f83dd0a24b3a79322f29e6b8999323c19b9e"
created: 2026-11-20
updated: 2026-11-20
ingested: 2026-11-20
---

# wiki の Windows 初期環境と MCP 起動診断（2026-11-20）

利用者向け文書の段階 2 で、新規の Windows 11 Enterprise 評価版 VM（26H2、build 26300.9457）に Claude Desktop の MSIX `5.11492.5.0` を入れた。

- Windows 標準の PowerShell をログオン済みユーザーのセッションで実行すると、Git と uv は見つからず、`python` は Microsoft Store の実行エイリアスだった。`python --version` は終了コード 9009。PowerShell Direct から直接 `Get-Command python.exe` を実行したときは結果がなかった。
- [[info-hive-wiki]] `v0.39.1` を専用ディレクトリに展開した。`wiki_mcp_launch.py --ensure` は、Visual C++ ランタイムの DLL 3 本がない状態で 34.41 秒後に終了コード 1 を返した。例外と `launch.log` の両方に、`winget install --id Microsoft.VCRedist.2015+.x64 -e --source winget` が出た。
- 旧 VM の `0.39.0` では、同ランタイムを入れたあと `--ensure` が終了コード 0 になった。旧 VM の `/wiki:help` は Store の実行エイリアスで失敗し、Python 3.12.10 の導入後に [[wikiのコマンド一覧-v0.38.1|12 本のコマンド]] を表示した。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| 1 | Python の実行エイリアスの観測は対話セッションと PowerShell Direct で異なった。 | Windows の対話セッション | `source_only` | このページ。検証時の条件として記録する。 |
| 2 | v0.39.1 の直接起動は、DLL 不足を終了コード 1 と導入案内で知らせた。 | wiki v0.39.1 の起動診断 | `source_only` | このページ。Code タブでの表示は別途確認する。 |
| 3 | v0.39.0 の直接起動と `/wiki:help` は、前提を導入したあとに通った。 | 旧版との比較 | `source_only` | このページ。別 VM と別版の観測として記録する。 |

## 関係するページ

- [[info-hive-wiki]]
- [[wikiのコマンド一覧-v0.38.1]]
