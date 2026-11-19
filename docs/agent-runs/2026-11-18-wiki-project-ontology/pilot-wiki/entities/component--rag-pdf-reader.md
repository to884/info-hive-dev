---
type: "entity"
title: "rag の PDF 読み取り"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "component:rag-pdf-reader"
  node_type: "component"
  relationships:
  - predicate: "part_of"
    object: "product:info-hive-rag"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "rag 0.5.0 の `read_pdf` は、ファイルの先頭がちょうど `%PDF-` でないと「PDF の形式ではありません」として拒んでいた。"
    confidence: "high"
    status: "current"
    notes: "rag 0.5.0〜0.5.1 の観測。製品内の責務を指す。"
---

# rag の PDF 読み取り

対象: `read_pdf` と PDF の受け付け判定。
