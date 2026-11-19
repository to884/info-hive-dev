---
type: "entity"
title: "Web raw の段を専用エージェントに任せる変更"
tags:
- "グラフ"
sources:
- "追い越された版のリリース-wiki-0.15.0"
- "rawの段を任せるエージェントの確かめ-2026-11-14"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "change:wiki-web-raw-agent"
  node_type: "change"
  relationships:
  - predicate: "changes"
    object: "component:wiki-web-raw"
    source: "rawの段を任せるエージェントの確かめ-2026-11-14"
    evidence: "wiki プラグイン 0.15.0 で足すエージェント `wiki:web-raw`（`model: sonnet`）に、`/wiki:ingest` の raw を作る段を任せ、要約ページから後をメインのモデル（Opus 5.5）で行ったときの記録である。"
    confidence: "high"
    status: "current"
    notes: "raw の作成の分担だけの変更。"
  - predicate: "implements"
    object: "decision:web-raw-split-20261114"
    source: "rawの段を任せるエージェントの確かめ-2026-11-14"
    evidence: "メインは `model` の引数を渡さずに `wiki:web-raw` を呼び、エージェントは Sonnet 5.5 で取得から `check --finish` までを行い、wiki のページには書かなかった。要約ページ、`index.md`、`log.md` はメインが書いた。"
    confidence: "high"
    status: "current"
    notes: "raw と後段を分けた実行が観測された。比較の判断の日付とは別。"
---

# Web raw の段を専用エージェントに任せる変更

実施済み。範囲は raw の分担。11-14 の分担の設計を実装した。
