---
type: "entity"
title: "wiki の Web raw 作成"
tags:
- "グラフ"
sources:
- "追い越された版のリリース-wiki-0.15.0"
- "rawの段を任せるエージェントの確かめ-2026-11-14"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "component:wiki-web-raw"
  node_type: "component"
  relationships:
  - predicate: "part_of"
    object: "product:info-hive-wiki"
    source: "rawの段を任せるエージェントの確かめ-2026-11-14"
    evidence: "wiki プラグイン 0.15.0 で足すエージェント `wiki:web-raw`（`model: sonnet`）に、`/wiki:ingest` の raw を作る段を任せ、要約ページから後をメインのモデル（Opus 5.5）で行ったときの記録である。"
    confidence: "high"
    status: "current"
    notes: "wiki の raw を作る段の所属。"
---

# wiki の Web raw 作成

専用エージェントの有無を超えた工程の責務。取得後の整理、訳、画像の補足。
