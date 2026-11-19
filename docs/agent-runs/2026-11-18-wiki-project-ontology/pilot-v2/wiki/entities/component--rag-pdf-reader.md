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
    notes: "rag の read_pdf という所属関係。現在の動作の保証ではない。"
---

# rag の PDF 読み取り

read_pdf という責務の構成要素。問題の有効な版は affects の release を読む。
