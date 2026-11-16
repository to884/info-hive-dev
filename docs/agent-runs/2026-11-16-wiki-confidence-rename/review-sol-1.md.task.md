# レビューの目的

作者の決定で、info-hive-wiki の `/wiki:query` が回答に付ける「確からしさ（confidence）」の名前を「確信度」に変えた。決め方は変えず、名前だけを変える変更である。Claude Sonnet 5.5 がこのコマンドを実行する。

## 変更

- 子（`wiki.diff`）: `commands/query.md`、`skills/info-hive/references/query-confidence.md`、`query-workflow.md`、`graph-workflow.md`、`SKILL.md`、`docs/commands.md`、`docs/workflows.md`、`scripts/wiki_browse_core.py`（browse のエッジの表の列名）、`CHANGELOG.md` の Unreleased。決まった 1 行は `**確信度（confidence）: 中**` になる。
- 「確信度」は、グラフのエッジの `confidence`（`low` など）と、判定モデルの答えの値（0〜1）で、すでに使われていた。回答の確信度とエッジの `confidence` が同じ文に出る箇所は「回答の確信度」「エッジの `confidence`」と書き分けた。
- 親（`parent.diff`）: ADR-0028 に名前の追記（本文は承認時の言葉のまま）、wiki の 11 ページの地の文と title、`log.md` に 1 行、測定の要約のスクリプト 3 つ（新旧どちらの字句も読む）。wiki では、ページ名（スラッグ）、`[[リンク]]`、frontmatter の `sources` のページ名、当時の版の字句（バッククォートの中と「（確からしさ: 高）」）、`log.md` の過去の行は変えていない。

## 見てほしいこと

- 名前を変えたことで、回答の確信度と、エッジの `confidence` や判定モデルの確信度を、エージェント（または読み手）が取り違える文が残っていないか。特に `query-confidence.md` の上限の表と「グラフのエッジの上限」、`graph-workflow.md`、`decision-models.md`、`SKILL.md`。
- 変え漏れ（「確からしさ」が残って、新旧の名前が混ざる文）と、変えすぎ（回答の確からしさではない意味の「確からしさ」を変えた、当時の事実を書いた文を変えた）。
- 測定のスクリプトの字句の読み方と、wiki のページの置き換えの規則（何を残したか）の筋が通っているか。
- CHANGELOG の書き方と、SemVer の上げ方（決まった 1 行の字句が変わり、機械で数える側に影響する）。
