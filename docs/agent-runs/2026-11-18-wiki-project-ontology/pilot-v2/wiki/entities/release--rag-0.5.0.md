---
type: "entity"
title: "rag 0.5.0"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "release:rag-0.5.0"
  node_type: "release"
  relationships:
  - predicate: "release_of"
    object: "product:info-hive-rag"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "rag 0.5.0 の `read_pdf` は、ファイルの先頭がちょうど `%PDF-` でないと「PDF の形式ではありません」として拒んでいた。"
    confidence: "high"
    status: "current"
    notes: "問題が観測された版。"
---

# rag 0.5.0

製品: rag。版: 0.5.0。観測された問題が残る固定の版であり、現在の最新版を意味しない。
