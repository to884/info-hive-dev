---
type: "entity"
title: "wiki の YouTube 字幕の取得"
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
    evidence: "wiki に次の 3 つのスクリプトを足した（to884/info-hive-wiki#74）。\n  - `wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。"
    confidence: "high"
    status: "current"
    notes: "wiki に足した字幕取得スクリプトの責務。"
---

# wiki の YouTube 字幕の取得

この試料では字幕を取得する責務だけを指す。query や lint の変更の全体とは区別する。
