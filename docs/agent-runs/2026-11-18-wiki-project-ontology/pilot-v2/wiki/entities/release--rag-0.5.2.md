---
type: "entity"
title: "rag 0.5.2"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "release:rag-0.5.2"
  node_type: "release"
  relationships:
  - predicate: "release_of"
    object: "product:info-hive-rag"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "v0.5.2 は 2026-11-13 01:04（日本時間。GitHub の記録では 2026-11-12T16:04Z）にリリースされた。"
    confidence: "high"
    status: "current"
    notes: "公開した製品と版。"
  - predicate: "delivers"
    object: "change:rag-header-wording-v052"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "文書の修正を rag 0.5.2 で行ったと明記され、公開は E23 に記録。"
---

# rag 0.5.2

製品: rag。版: 0.5.2。公開日: 2026-11-13 JST。採録は PDF ヘッダーの文書の変更のみ。
