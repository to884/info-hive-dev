---
type: "entity"
title: "wiki の YouTube 字幕の取り込み"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "component:wiki-youtube-ingest"
  node_type: "component"
  relationships:
  - predicate: "part_of"
    object: "product:info-hive-wiki"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "作者が ADR-0027（[[youtubeの字幕の取り込みの設計-2026-11-15]]）を承認し、実装を求めた（2026-11-16）。この記録は、その実装と、それを出した wiki 0.23.0 のものである。"
    confidence: "high"
    status: "current"
    notes: "wiki 0.23.0 の機能。"
  - predicate: "depends_on"
    object: "product:yt-dlp-2026-8-19"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "`wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。"
    confidence: "high"
    status: "current"
    notes: "wiki 0.23.0 の PEP 723 の固定。将来の版の依存は別に確認する。"
---

# wiki の YouTube 字幕の取り込み

字幕を取る構成要素。
