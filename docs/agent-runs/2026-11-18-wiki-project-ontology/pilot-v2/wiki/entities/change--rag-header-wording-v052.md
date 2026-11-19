---
type: "entity"
title: "rag 0.5.2 の PDF ヘッダーの書き方の統一"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "change:rag-header-wording-v052"
  node_type: "change"
  relationships:
  - predicate: "changes"
    object: "artifact:rag-readme"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "E06 に列挙された文書・コメントの直接の変更。"
  - predicate: "changes"
    object: "artifact:rag-changelog"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "E06 に列挙された文書・コメントの直接の変更。"
  - predicate: "changes"
    object: "artifact:rag-index-comments"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "E06 に列挙された文書・コメントの直接の変更。"
  - predicate: "changes"
    object: "artifact:rag-v051-release-notes"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "E06 に列挙された文書・コメントの直接の変更。"
  - predicate: "changes"
    object: "artifact:dev-adr-0013"
    source: "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3"
    evidence: "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。"
    confidence: "high"
    status: "current"
    notes: "E06 に列挙された文書・コメントの直接の変更。"
---

# rag 0.5.2 の PDF ヘッダーの書き方の統一

実施済み。コードの受け付け条件を変えず、README、CHANGELOG、コメント、リリース本文、親の ADR の記述をそろえた。v0.5.3 のエラーメッセージの変更とは別。
