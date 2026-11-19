---
type: "entity"
title: "先頭に 1 バイトの改行がある PDF 2 件の拒否"
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
    object: "release:rag-0.5.0"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "rag 0.5.0 の `read_pdf` は、ファイルの先頭がちょうど `%PDF-` でないと「PDF の形式ではありません」として拒んでいた。\n- 全量の OCR（`docs/research/rag-full-ocr-v050-2026-11-09.md`）で、先頭に改行が 1 バイトあるだけの 2 文書（`L4/` の下の seL4 の論文）が、この理由で失敗した。"
    confidence: "high"
    status: "current"
    notes: "先頭 1 バイトの改行がある観測 2 件。read_pdf のヘッダー判定。版を固定して記録し、現在の rag への障害とは読まない。"
---

# 先頭に 1 バイトの改行がある PDF 2 件の拒否

対象版: rag 0.5.0。観測: seL4 の PDF 2 件の先頭に改行が 1 バイトあり、ヘッダー判定で拒否。任意長の前置きや、すべての不正 PDF を受け付ける要求ではない。
