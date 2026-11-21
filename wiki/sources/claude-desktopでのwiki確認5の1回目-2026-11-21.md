---
type: "source"
title: "Claude Desktop での wiki 確認 5 の 1 回目（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "コマンド"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-desktopでのwiki確認5の1回目-2026-11-21.md"
raw_sha256: "e22a2e556345ceff66442f4a89ebae900e7c57b1813af1e71d3e152967a018b0"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Desktop での wiki 確認 5 の 1 回目

新規 Windows 11 VM の Claude Desktop 6.6395.0.0 の Code タブで、[[info-hive-wiki]] 0.39.1 の初期化から閲覧、点検までを 1 回通した。e5 と ruri のキャッシュが空のチェックポイントから開始した。導入時の画面と版は [[claude-desktopへのwiki-0.39.1の導入-2026-11-21]] にある。

- `/wiki:init` は選択式の質問を順に出し、グラフ層だけ自由入力で後回しにした。標準の `CLAUDE.md` を承認したあと、ツール出力に `status: ready` があり、e5 の取得を確認した。
- 味噌の取り込み後は、索引と 1 件のログ、味噌と麹のページができた。回答は索引とページに基づき、`[[味噌]]`、`[[麹]]` と確信度を示した。MCP の `query` と `wiki:wiki-reader` の呼び出しはなかった。
- 醤油を追加したあと、Code のブラウザペインで Index の 2 件の要約と、麹のページへの 2 件の被リンクを確認した。CLI 版の構造 lint は 3 ページを調べ、孤立、リンク切れ、読み込みエラーを報告しなかった。

確認表では同じ初期状態から 3 回を通す。このページは 1 回目の記録で、チュートリアルで使う共通の目印は残り 2 回を終えて判定する。

2 回目を始める際の接続切断と操作の記録は [[段階2のvmconnect再認証-2026-11-21]] にある。

[[claude-desktopでのwiki確認5の2回目-2026-11-21|2 回目]] では、構造点検に MCP が使われた。
