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
    notes: "直接経路だけの確認。全経路の成功は未確認。"
---

# rag 0.5.1 の実 PDF の直接抽出の確認

対象: PR #7 の修正後の read_pdf と extract_pages。方法: 実 PDF 2 件、OCR off。観測結果: 70 ページと 18 ページのテキスト。限界: register_pdf→索引化は未実施。変更・出典の本文を回答時に必ず読む。
