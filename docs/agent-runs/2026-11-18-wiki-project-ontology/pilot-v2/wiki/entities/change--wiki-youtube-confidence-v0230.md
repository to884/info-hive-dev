---
type: "entity"
title: "動画ソースの確信度の上限の表への追加"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "change:wiki-youtube-confidence-v0230"
  node_type: "change"
  relationships:
  - predicate: "changes"
    object: "artifact:wiki-query-confidence"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "取り込みの手順に V1〜V10 を足した。確信度の上限の表（`query-confidence.md`）には、動画のソースの行を足した。"
    confidence: "high"
    status: "current"
    notes: "文書の変更先を直接示す。"
---

# 動画ソースの確信度の上限の表への追加

実施済み。PR #74 のうち query-confidence.md に動画のソースの行を足した変更。採録範囲を分離し、字幕の取得だけからこの変更を推論させない。
