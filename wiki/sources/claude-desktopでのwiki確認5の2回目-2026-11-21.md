---
type: "source"
title: "Claude Desktop での wiki 確認 5 の 2 回目（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "コマンド"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-desktopでのwiki確認5の2回目-2026-11-21.md"
raw_sha256: "d4d106b72b54aad5e3f429c403984f1cde4ab0a52bd96cb10a6d7cce182f9dee"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Desktop での wiki 確認 5 の 2 回目

Windows 11 VM の Claude Desktop 6.6395.0.0 の Code タブで、[[info-hive-wiki]] 0.39.1 の確認 5 を 2 回目まで通した。e5 と ruri は開始時に未取得。[[段階2のvmconnect再認証-2026-11-21]] のあと、空の練習用フォルダーで始めた。

- 初期化の出力は `"status": "ready"`。味噌の質問に `[[味噌]]`、`[[麹]]` と確信度が付いた。
- 醤油の追加で取り込みログが 1 件から 2 件になった。browse の応答はループバックとプロジェクトスコープ。Code のブラウザペインで 2 件の要約と、麹に至る 2 件の被リンクを確認した。
- MCP の構造点検は 3 ページを検査し、孤立、リンク切れ、読み込みエラーはいずれも 0。空の `tags` が必須項目の欠落と報告された。[[claude-desktopでのwiki確認5の1回目-2026-11-21|1 回目]] では、構造点検は CLI を使った。

醤油の適用後に補足ログを書いたとき、エージェントが差分全体をコマンドライン引数に渡して失敗した。再実行でハッシュだけを渡し、補足ログを追加できた。

その後の照合結果は [[確認5の3回の共通点-2026-11-21]] にある。
