---
type: "source"
title: "経験: wiki_evolve.py capture が Windows で raw を CRLF で書き、返す SHA-256 とファイルが食い違った（2026-11-15）"
tags: ["windows"]
raw: "raw/experiences/evolve-capture-writes-crlf-2026-11-15.json"
ingested: 2026-11-15
created: 2026-11-15
updated: 2026-11-15
---

# 経験: wiki_evolve.py capture が Windows で raw を CRLF で書き、返す SHA-256 とファイルが食い違った（2026-11-15）

`/wiki:learn` で記録した経験である。raw は `raw/experiences/evolve-capture-writes-crlf-2026-11-15.json`（ファイルの SHA-256 は `aaf4243629d164885de3801b7eca7bbe82e4f9291982db6063dccdce903f901f`。capture が返した値は `31df675f987b0ce8…` で、これも食い違う）。結果は failure。

## 観測したこと

- インストール済みの wiki 0.11.0 の `wiki_evolve.py capture` で、5 つの経験を記録した。保存されたファイルは、5 つとも CRLF だった。
- 例えば `extraction-metrics-string-presence-2026-11-15.json` では、capture が返した sha256 は `87919184f7a664d5…`、ファイルのバイト列の SHA-256 は `def2d0757e195430…` だった。
- capture は `path.open('x', encoding='utf-8')` で書き、`newline` を指定していない。info-hive-wiki 0.18.1 の `wiki_evolve.py` も、149 行と 183 行で同じ書き方をしている（コードを読んだだけで、実行はしていない）。

## 原因についての仮説

Windows の Python は、文字のモードで書く `\n` を `\r\n` に変える。capture は変える前の文字列の SHA-256 を返す（仮説。[[pythonの書き戻しの改行]] と同じ性質）。

## 適用範囲と反例

Windows で capture を使い、返された sha256 でファイルを確かめるとき。Linux と macOS では食い違わないはずである（確かめていない）。返した sha256 をほかの処理が使っているかは確かめていない。この記録の作業ではスキルを変えないので、直していない。

## 関係するページ

- [[pythonの書き戻しの改行]]
