---
type: "entity"
title: "先頭に改行のある PDF が拒否される"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "issue:rag-pdf-prefix-rejected"
  node_type: "issue"
  relationships:
  - predicate: "affects"
    object: "component:rag-pdf-reader"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "rag 0.5.0 の `read_pdf` は、ファイルの先頭がちょうど `%PDF-` でないと「PDF の形式ではありません」として拒んでいた。"
    confidence: "high"
    status: "current"
    notes: "rag 0.5.0。先頭が厳密に %PDF- でない場合。"
---

# 先頭に改行のある PDF が拒否される

条件: rag 0.5.0 のヘッダー判定。原因の仮説とは別に、観測した拒否を記録する。
