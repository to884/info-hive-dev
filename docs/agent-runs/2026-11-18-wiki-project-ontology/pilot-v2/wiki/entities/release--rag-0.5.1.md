---
type: "entity"
title: "rag 0.5.1"
tags:
- "グラフ"
sources:
- "pdfのヘッダーの判定の修正-rag-0.5.1"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "release:rag-0.5.1"
  node_type: "release"
  relationships:
  - predicate: "release_of"
    object: "product:info-hive-rag"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "to884/info-hive-rag#7 を 2026-11-12 にマージし（b3f45e3）、CHANGELOG に日付を入れた #8（0dea049）のあと、v0.5.1 をリリースした。"
    confidence: "high"
    status: "current"
    notes: "rag v0.5.1 の公開。"
  - predicate: "delivers"
    object: "change:rag-pdf-prefix-1024"
    source: "pdfのヘッダーの判定の修正-rag-0.5.1"
    evidence: "版は 0.5.1（パッチ）。今まで受け付けていた入力の扱いを変えず、受け付ける範囲を広げるだけである。"
    confidence: "high"
    status: "current"
    notes: "受け付け範囲を変えた版が 0.5.1 と明記され、公開は E03 に記録。"
---

# rag 0.5.1

製品: rag。版: 0.5.1。公開日: 2026-11-12。出荷した変更の記録は本試料では PDF の判定の修正だけを採録した。
