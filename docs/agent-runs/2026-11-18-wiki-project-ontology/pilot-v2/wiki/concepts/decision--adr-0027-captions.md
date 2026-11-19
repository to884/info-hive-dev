---
type: "concept"
title: "ADR-0027 の字幕を固定した yt-dlp で取る判断"
tags:
- "グラフ"
sources:
- "youtubeの字幕の取り込みの設計-2026-11-15"
created: 2026-11-18
updated: 2026-11-18
graph:
  node_id: "decision:adr-0027-captions"
  node_type: "decision"
  relationships:
  - predicate: "selects"
    object: "product:yt-dlp"
    source: "youtubeの字幕の取り込みの設計-2026-11-15"
    evidence: "`wiki_youtube.py` を `uv run --script` で動かし、PEP 723 で yt-dlp の版を 1 つに固定して、字幕だけを取る。"
    confidence: "high"
    status: "current"
    notes: "製品の選択と版を固定する方式。実装で使った数値の版は release 間の depends_on へ記録する。"
---

# ADR-0027 の字幕を固定した yt-dlp で取る判断

具体的な選択: yt-dlp の版を 1 つに固定して字幕だけを取る。特定の数値の版を永続的に選ぶ判断とはしない。
