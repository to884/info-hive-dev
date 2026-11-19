---
type: "concept"
title: "raw の段を Sonnet のエージェントに分担する設計"
tags:
- "グラフ"
sources:
- "rawの段を任せるエージェントの確かめ-2026-11-14"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "decision:web-raw-split-20261114"
  node_type: "decision"
  relationships:
  - predicate: "selects"
    object: "release:claude-sonnet-5.5"
    source: "rawの段を任せるエージェントの確かめ-2026-11-14"
    evidence: "メインは `model` の引数を渡さずに `wiki:web-raw` を呼び、エージェントは Sonnet 5.5 で取得から `check --finish` までを行い、wiki のページには書かなかった。要約ページ、`index.md`、`log.md` はメインが書いた。"
    confidence: "high"
    status: "current"
    notes: "raw だけの分担。11-13 の全工程への選択と混ぜない。"
---

# raw の段を Sonnet のエージェントに分担する設計

記録日: 2026-11-14。正確な決定日時は未確定。選択: raw を専用の Sonnet、後段をメインのモデルに分担する。前日の全体の継続とは別の範囲。正式な撤回・差し替えを示す一次記録がないため supersedes は補わない。
