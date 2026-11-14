# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の 4 版目である。実装はまだない。

1〜3 版目は、あなたのレビュー（`docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-1.md`〜`design-review-3.md`）で却下された。そのあと作者の判断で、4 体のエージェントに独立に設計し直させ、相互レビューと総括を受けた（`docs/agent-runs/2026-11-14-wiki-session-ingest-redesign/` の `results/`、`reviews/`、`summary.md`）。4 版目は、総括が推したエージェント A の構造に、相互レビューで当たった指摘の直しと、作者の判断を入れたものである。

この版を壊してほしい。特に、新しく入った **9 節（wiki の変更を用意する、`wiki_apply.py`）と 10 節（書く段、`apply`）** を重点に見てほしい。1〜3 回目の却下は、どれもその回に新しく足した仕組みに出た。

確かめてほしい点:

1. 9 節と 10 節: ロック、変更の 4 つの種類（`raw`、`create`、`patch`、`append`）と、その当て方の表、3 方向の当て方と「当て済み」の判定、途中で止まったときのやり直し、競合のときの流れ、秘密の検査（禁じる文字列の作り方、`plan_sha256` に縛ること）、パスの検査（リンクとジャンクション、raw のルートの中）、Git の検査。書き足し、上書き、二重の適用、検査の迂回、秘密の漏れ、ロックの外での書き込みの反例を探す。
2. 1〜8 節（抜き出しと raw の生成と確認）が、4 体のレビューで A の構造に当たった指摘（`summary.md` と `reviews/`）を本当に解消したか。
3. 13 節の手順（S1〜S10）が、モデルに Edit と Write で wiki と raw のルートを直接書かせる経路を残していないか。既存の `commands/ingest.md` の手順 1〜8 と食い違わないか。
4. 「指摘との対照」の表の「生じない」が、本当に生じないか。

## 読む版

作業ツリーのサブモジュール `info-hive-wiki/` は古いコミットにある。既存の実装と文書は、次のコミットを `git show` で読むこと。

- `info-hive-wiki`: 83dbb30。`git -C info-hive-wiki show 83dbb30:<パス>`
- 親のリポジトリ: a237e8f。`git show a237e8f:<パス>`

## レビューしなくてよいこと

- 設計書の見出しの表にある「作者の判断（2026年11月14日）」の (1)〜(6) は、作者が決めた。その是非は論じなくてよい。特に、(1) `uuid` のない知らない記録を読み飛ばすこと、(6) Claude Code のツールを通らない書き手（エディター、Codex、ほかのスクリプト）を考えないことは、前提である。判断のもとで設計が成り立たない点があれば、それは指摘してほしい。
- 「保証しないこと」の 1〜10 に書いた限界そのものは、指摘しなくてよい。限界の書き方と食い違う主張が、設計のほかの所にあれば指摘してほしい。
- 「作者が決めること」の 1〜7 のどちらが良いかは論じなくてよい。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/concurrency-check.md`（Claude Code の Edit と Write を並べて試した記録）
- `docs/agent-runs/2026-11-14-wiki-session-ingest-redesign/summary.md`、`results/A.md`、`reviews/B.md`、`reviews/C.md`、`reviews/D.md`
- `docs/agent-runs/2026-11-14-wiki-session-ingest/root-causes.md`、`design-review-3.md`
- 83dbb30 の `info-hive-wiki` の `commands/ingest.md`、`skills/info-hive/SKILL.md`、`skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`graph-workflow.md`、`skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_lint.py`、`wiki_initialized.py`、`wiki_graph_common.py`、`wiki_graph_extract.py`、`wiki_pages.py`、`wiki_text.py`、`init_wiki.py`
- a237e8f の親の `docs/adr/0004-raw-holds-translated-web-pages.md`、`0015-wiki-article-methodology-adopted-in-stages.md`、`0018-wiki-requires-python-312.md`、`0019-wiki-root-is-marked-by-schema.md`、`tests/wiki/check_commands_mcp.py`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。構造を確かめるために読んでよいが、会話の文をレビューの結果に引用しないこと。

応答は日本語で書く。
