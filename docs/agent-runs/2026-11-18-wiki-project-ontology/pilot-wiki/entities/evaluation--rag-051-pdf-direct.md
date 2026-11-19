---
type: "entity"
title: "rag 0.5.1 の実 PDF の直接抽出の確認"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "evaluation:rag-051-pdf-direct"
  node_type: "evaluation"
  relationships:
  - predicate: "evaluates"
    object: "change:rag-pdf-prefix-1024"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "実データの 2 件を、直した `read_pdf` と `extract_pages`（`ocr_mode` は `off`）に通した。70 ページと 18 ページで、すべてテキストのページだった。"
    confidence: "high"
    status: "current"
    notes: "実 PDF 2 件、OCR off、直接経路のみ。E05 に全経路未確認の留保がある。"
---

# rag 0.5.1 の実 PDF の直接抽出の確認

方法: 実 PDF 2 件を read_pdf と extract_pages に通す。OCR は off。結果: 70 ページと 18 ページで文字の抽出を観測。限界: MCP register_pdf→索引化は未実施。
