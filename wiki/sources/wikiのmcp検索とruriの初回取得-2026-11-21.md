---
type: "source"
title: "wiki の MCP 検索と ruri の初回取得（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "MCP"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/wikiのmcp検索とruriの初回取得-2026-11-21.md"
raw_sha256: "2287a857d2c77b354232ced8b7ac58b0283b47967e689271c47fd1998f0b3a0c"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# wiki の MCP 検索と ruri の初回取得

[[確認5の3回の共通点-2026-11-21|確認 5]] の質問では、Claude は索引とページを読んだ。ruri は 3 回とも未取得だった。確認 6 では、Windows 11 の Claude Desktop の Code で [[info-hive-wiki]] 0.39.1 の MCP の `query` を直接呼んだ。

- 初回は語彙検索で味噌の要約を返し、`mode: lexical` と `index.state: embedding` を報告した。
- モデルは自動で取得された。この VM では、最初の呼び出しから 16.31 秒後に `verified.json` が書かれ、モデルのディレクトリは 535,699,472 バイトだった。
- 同じ検索を再実行すると `mode: hybrid` になり、語彙検索と埋め込みの検索が使われた。索引は `ready` で 14 セクションを埋め込み済みだった。

利用者向けの手順で、ruri の取得をチュートリアルの前提にする必要はない。MCP の意味検索を使うとき、自動取得されることを案内できる。

接続状況を確かめる画面と再接続の操作は [[claude-codeのwiki-mcp再接続-2026-11-21]] にある。
