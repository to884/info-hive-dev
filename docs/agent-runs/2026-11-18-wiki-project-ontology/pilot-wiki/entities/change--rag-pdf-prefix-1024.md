---
type: "entity"
title: "PDF の前置きを 1024 バイトまで受け付ける変更"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "change:rag-pdf-prefix-1024"
  node_type: "change"
  relationships:
  - predicate: "changes"
    object: "component:rag-pdf-reader"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付けるように直した。上限は PDFium にそろえた"
    confidence: "high"
    status: "current"
    notes: "rag PR #7 の read_pdf の受け付け判定。"
  - predicate: "fixes"
    object: "issue:rag-pdf-prefix-rejected"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付けるように直した。上限は PDFium にそろえた"
    confidence: "high"
    status: "current"
    notes: "前置き 1024 バイト以下の拒否条件を解消。MCP から索引化までの成功は未確認。"
---

# PDF の前置きを 1024 バイトまで受け付ける変更

実施済み: rag PR #7。ヘッダーの受け付け範囲の変更であり、PDF 本体を開ける保証ではない。
