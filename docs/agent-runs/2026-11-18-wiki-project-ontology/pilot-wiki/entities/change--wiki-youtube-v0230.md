---
type: "entity"
title: "wiki 0.23.0 の YouTube 字幕取り込みの実装"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "change:wiki-youtube-v0230"
  node_type: "change"
  relationships:
  - predicate: "changes"
    object: "component:wiki-youtube-ingest"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "作者が ADR-0027（[[youtubeの字幕の取り込みの設計-2026-11-15]]）を承認し、実装を求めた（2026-11-16）。この記録は、その実装と、それを出した wiki 0.23.0 のものである。"
    confidence: "high"
    status: "current"
    notes: "wiki 0.23.0 の実装。"
  - predicate: "implements"
    object: "decision:adr-0027-captions"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "作者が ADR-0027（[[youtubeの字幕の取り込みの設計-2026-11-15]]）を承認し、実装を求めた（2026-11-16）。この記録は、その実装と、それを出した wiki 0.23.0 のものである。"
    confidence: "high"
    status: "current"
    notes: "字幕の取得方法を実装した。残る限界やレビュー結果は別に読む。"
---

# wiki 0.23.0 の YouTube 字幕取り込みの実装

実施済み。ADR のすべての性質を証明したという意味ではない。
