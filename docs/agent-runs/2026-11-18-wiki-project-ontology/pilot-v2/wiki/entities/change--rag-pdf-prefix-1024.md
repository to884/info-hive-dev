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
    notes: "read_pdf のヘッダー判定。"
  - predicate: "fixes"
    object: "issue:rag-pdf-prefix-rejected"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "全量の OCR（`docs/research/rag-full-ocr-v050-2026-11-09.md`）で、先頭に改行が 1 バイトあるだけの 2 文書（`L4/` の下の seL4 の論文）が、この理由で失敗した。\n- `%PDF-` の前にあるバイトが 1024 バイト以下なら受け付けるように直した。上限は PDFium にそろえた"
    confidence: "high"
    status: "current"
    notes: "対象は先頭 1 バイトの改行がある 2 件。任意の前置きの拒否全般を直したという意味ではない。"
---

# PDF の前置きを 1024 バイトまで受け付ける変更

実施済み: rag PR #7。ヘッダー判定の受け付け範囲を変更。1 バイトの改行で拒否された観測 2 件を解消した。1024 バイトを超える前置きは引き続き対象外。MCP→索引化は未確認。
