---
type: "entity"
title: "wiki 0.15.0"
tags:
- "グラフ"
sources:
- "追い越された版のリリース-wiki-0.15.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "release:wiki-0.15.0"
  node_type: "release"
  relationships:
  - predicate: "release_of"
    object: "product:info-hive-wiki"
    source: "追い越された版のリリース-wiki-0.15.0"
    evidence: "wiki 0.15.0（raw の段をエージェント `wiki:web-raw` に任せる変更）のタグと GitHub リリースの記録である。"
    confidence: "high"
    status: "current"
    notes: "タグの製品と版。"
  - predicate: "delivers"
    object: "change:wiki-web-raw-agent"
    source: "追い越された版のリリース-wiki-0.15.0"
    evidence: "wiki 0.15.0（raw の段をエージェント `wiki:web-raw` に任せる変更）のタグと GitHub リリースの記録である。"
    confidence: "high"
    status: "current"
    notes: "raw の変更のタグと公開という直接の報告。"
---

# wiki 0.15.0

製品: wiki。版: 0.15.0。タグ: 5adb069。marketplace では 0.16.0 が入ったため、この版の導入確認とは扱わない。採録は raw の分担の変更のみで、変更一覧の完全性は主張しない。
