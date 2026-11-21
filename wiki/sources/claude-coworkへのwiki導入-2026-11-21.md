---
type: "source"
title: "Claude Cowork への Wiki 0.39.1 の導入（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "MCP"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-coworkへのwiki導入-2026-11-21.md"
raw_sha256: "b7ff4b5db6a0681f2aea1628decfa775336f817f152d4b9da60bb4dc9949fda7"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Cowork への Wiki 0.39.1 の導入

Windows 11 の Claude Desktop 6.6395.0.0 のチャットと Cowork の統合画面で、[[info-hive-wiki]] 0.39.1 の追加を確認した。左の「プラグイン」で `to884/info-hive-marketplace` を同期し、Wiki の「追加」を選んだ。利用者がローカル MCP サーバーの警告で「続ける」を押すと「追加済み」になった。

「新規作成」→「プロジェクトまたはフォルダー」→「フォルダを追加」で練習フォルダーを選ぶと、アプリはファイルの変更について利用者に許可を求めた。最初の送信時にもクラウドでのファイル処理の許可が出た。接続後の挨拶には合言葉はなく、`/wiki:init` に続く返答で `CLAUDE.md` の合言葉が出た。

Cowork のクラウドで実行した `init_wiki.py` は、e5 取得中に Hugging Face への接続がプロキシで拒否され、HTTP 403 で止まった。Windows の同じフォルダーで `init_wiki.py` を実行すると `"status": "ready"` になり、その後の Cowork の MCP `stats` はページ数 0、Index の行数 26 を返した。[確認 8 の検証記録](../../docs/research/usage-docs-facts-2026-11-20.md#確認-8-の-cowork)

## 取り込んだ内容と載せたページ

| 内容 | 掲載方法 | ページ | 理由 |
| --- | --- | --- | --- |
| Cowork での追加とローカル MCP の確認 | update | [[info-hive-wiki]] | Code と Cowork の導入経路をたどれるようにする |
| フォルダー変更の許可画面と試験環境 | source_only | このページ | このアプリ版と検証 VM での観測 |

## 関係するページ

- [[claude-desktopへのwiki-0.39.1の導入-2026-11-21]]
