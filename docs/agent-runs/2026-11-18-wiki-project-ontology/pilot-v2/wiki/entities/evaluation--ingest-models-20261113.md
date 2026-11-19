---
type: "entity"
title: "2026-11-13 の Web raw のモデル比較"
tags:
- "グラフ"
sources:
- "ingestのモデルの比較-2026-11-13"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "evaluation:ingest-models-20261113"
  node_type: "evaluation"
  relationships:
  - predicate: "evaluates"
    object: "release:claude-sonnet-5.5"
    source: "ingestのモデルの比較-2026-11-13"
    evidence: "Haiku 5.5、Sonnet 5.5、Opus 5.5 で同じ 4 つの Web ページを `/wiki:ingest` に取り込み、raw の違いを比べた調査である。"
    confidence: "high"
    status: "current"
    notes: "比較した特定版のモデル。一般の Sonnet 全版には広げない。"
---

# 2026-11-13 の Web raw のモデル比較

対象: Sonnet 5.5 ほか 3 モデル × 4 Web ページ、各組 1 回。取り込み全体を各モデルで実行し、評価したのは raw。後段の記事の品質と費用比は評価していない。
