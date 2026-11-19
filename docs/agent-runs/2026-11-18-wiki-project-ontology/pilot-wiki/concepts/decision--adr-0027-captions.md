---
type: "concept"
title: "ADR-0027 の字幕を固定した yt-dlp で取る判断"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの設計-2026-11-15"
- "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "decision:adr-0027-captions"
  node_type: "decision"
  relationships:
  - predicate: "selects"
    object: "product:yt-dlp-2026-8-19"
    source: "youtubeの字幕の取り込みの設計-2026-11-15"
    evidence: "`wiki_youtube.py` を `uv run --script` で動かし、PEP 723 で yt-dlp の版を 1 つに固定して、字幕だけを取る。"
    confidence: "high"
    status: "current"
    notes: "版を固定した字幕だけの取得。版の値は E13 で特定する。"
---

# ADR-0027 の字幕を固定した yt-dlp で取る判断

ADR 全体ではなく、字幕の取得方法の判断を対象にする。承認日: 2026-11-16。
