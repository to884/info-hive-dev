---
type: "source"
title: "Claude Desktop の Code での wiki MCP 再接続（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "MCP"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-codeのwiki-mcp再接続-2026-11-21.md"
raw_sha256: "4d2f70e251c1bd0cf37256a027bfe38a3763e9e295b5932e855102a0bf95efab"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Desktop の Code での wiki MCP 再接続

Windows 11 の Claude Desktop 6.6395.0.0 の Code で [[info-hive-wiki]] 0.39.1 の接続を確認した。`/mcp` で「MCP サーバー」を開くと `wiki` の状態にチェックがあり、個別の行を開くと「接続済み・7 個のツール」と「再接続」が表示された。

個別の「再接続」を押すと「再接続中…」のあとに接続済みへ戻った。`/mcp reconnect all` は、このセッションでは全体再接続の操作が使えないというメッセージを返した。

試験は ruri を取得していない `S2-wiki-0.39.1` から始めた。モデル取得と検索の状態は [[wikiのmcp検索とruriの初回取得-2026-11-21]] にある。
