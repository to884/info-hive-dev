---
type: "entity"
title: "wiki 0.23.0"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "release:wiki-0.23.0"
  node_type: "release"
  relationships:
  - predicate: "release_of"
    object: "product:info-hive-wiki"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "作者が ADR-0027（[[youtubeの字幕の取り込みの設計-2026-11-15]]）を承認し、実装を求めた（2026-11-16）。この記録は、その実装と、それを出した wiki 0.23.0 のものである。"
    confidence: "high"
    status: "current"
    notes: "wiki 0.23.0 の出荷。"
  - predicate: "delivers"
    object: "change:wiki-youtube-v0230"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "`v0.23.0` は注釈付きのタグで、#74 のマージコミット（`1252fda`）を指す。"
    confidence: "high"
    status: "current"
    notes: "#74 の字幕取得の追加 E20 を含むマージコミットをタグが指す。"
  - predicate: "delivers"
    object: "change:wiki-youtube-confidence-v0230"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "`v0.23.0` は注釈付きのタグで、#74 のマージコミット（`1252fda`）を指す。"
    confidence: "high"
    status: "current"
    notes: "#74 の表の追加 E22 を含むマージコミットをタグが指す。"
  - predicate: "depends_on"
    object: "release:yt-dlp-2026.8.19"
    source: "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
    evidence: "`wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。"
    confidence: "high"
    status: "current"
    notes: "wiki 0.23.0 の字幕取得で固定した版。現在の製品全体への無版の依存とはしない。"
---

# wiki 0.23.0

製品: wiki。版: 0.23.0。タグ: 1252fda。PR #74 の変更のうち本試料は字幕取得と回答の確信度の表の 2 件だけを採録し、全件の変更一覧とはしない。
