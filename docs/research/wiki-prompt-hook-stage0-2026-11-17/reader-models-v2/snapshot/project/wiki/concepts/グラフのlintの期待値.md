---
type: "concept"
title: "グラフの lint の期待値の取り直し"
tags: ["グラフ", "試験", "リリース"]
sources: ["グラフの抽出の修正-0.9.2"]
created: 2026-11-11
updated: 2026-11-11
---

# グラフの lint の期待値の取り直し

`info-hive-wiki` の `eval/decisions/fixtures/graph_lint_golden.json` は、`wiki_graph_lint.py` に `--decide` を付けないときの出力を、バイト単位で記録した期待値である。試験 `eval/decisions/test_decisions.py` の `GraphLintTests.test_output_without_decide_is_byte_identical` が、テキストと `--json` の出力をこれと比べる。判定レイヤーを足しても、`--decide` を付けなければ出力が変わらないことを守るためのものである。

## 取り直す条件

グラフの lint の出力を意図して変えたときは、期待値を取り直す。ファイルの `note` に、いつ、なぜ取り直したかを書き足す。

- P4 で表示を日本語にしたとき
- wiki 0.9.2 で検出結果（`ambiguous_object_refs`、`ambiguous_sources`、`unresolved_sources`、`order_dependent_edge_ids`）を足したとき。`--json` の出力にキーが増え、テキストの出力は変わらなかった（[[グラフの抽出の修正-0.9.2]]）

取り直すときは、試験と同じ呼び方（`test_decisions.run()`）で出力を取り、元のファイルの書式（JSON の字下げは 1、末尾の改行はない）を保つ。元の内容を同じ書式で書き戻すと同じバイト列になることを先に確かめると、書式の違いだけの差分を出さずに済む。

## info-hive-wiki の CI を手元で流す

0.9.2 では、開発リポジトリ（`info-hive-dev`）の試験しか流さずに PR を出したので、`info-hive-wiki` の CI の 4 つのジョブがすべてこの試験で落ちた。

`info-hive-wiki` のスクリプトを変えたら、開発リポジトリの `tests/` に加えて、`info-hive-wiki/.github/workflows/wiki-tests.yml` の手順（`eval/` の下の試験、検索の評価ゲート、`test_link_resolution.py` など 11 の手順）も手元で流す。依存は CI と同じ版にそろえる（`uv run --python 3.12 --with PyYAML==6.0.3 --with fastembed==0.8.0 --with sqlite-vec==0.1.9`）。
