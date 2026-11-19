---
type: "concept"
title: "比較後も取り込みを Sonnet 5.5 で続ける判断"
tags:
- "グラフ"
sources:
- "ingestのモデルの比較-2026-11-13"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "decision:ingest-sonnet-20261113"
  node_type: "decision"
  relationships:
  - predicate: "selects"
    object: "release:claude-sonnet-5.5"
    source: "ingestのモデルの比較-2026-11-13"
    evidence: "結論として、Sonnet 5.5 を使い続けることにした"
    confidence: "high"
    status: "current"
    notes: "11-13 時点で継続したモデルの特定版。"
  - predicate: "motivated_by"
    object: "evaluation:ingest-models-20261113"
    source: "ingestのモデルの比較-2026-11-13"
    evidence: "Haiku 5.5、Sonnet 5.5、Opus 5.5 で同じ 4 つの Web ページを `/wiki:ingest` に取り込み、raw の違いを比べた調査である。原本は `docs/research/wiki-ingest-model-comparison-2026-11-13.md`、実行の記録とスクリプトは `docs/agent-runs/2026-11-13-wiki-ingest-model-comparison/` にある。結論として、Sonnet 5.5 を使い続けることにした"
    confidence: "high"
    status: "current"
    notes: "比較の紹介と結論が同じ段落に明記されている。測定は raw に限られる。"
---

# 比較後も取り込みを Sonnet 5.5 で続ける判断

記録日: 2026-11-13。当時の運用は取り込み全体を Sonnet にしていた。根拠の測定範囲は raw。11-14 の raw の分担とは別の判断であり、現在の全ホストの設定ではない。
