---
type: "entity"
title: "PR #74 の字幕取得スクリプトの追加"
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
    evidence: "wiki に次の 3 つのスクリプトを足した（to884/info-hive-wiki#74）。\n  - `wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。"
    confidence: "high"
    status: "current"
    notes: "字幕取得の追加。PR の変更全体の索引ではない。"
  - predicate: "implements"
    object: "decision:adr-0027-captions"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "`wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。"
    confidence: "high"
    status: "current"
    notes: "字幕の取得のスクリプトで yt-dlp を固定した実装。ADR の全要件の充足やレビュー合格は意味しない。"
---

# PR #74 の字幕取得スクリプトの追加

実施済み。PR #74 全体ではなく、wiki_youtube.py を足し字幕取得を固定した依存で行う部分のみ。別の query/lint の変更はこの change の範囲外。
