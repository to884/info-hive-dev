# レビューの目的

`docs/plans/wiki-apply-2026-11-14.md` は、`info-hive-wiki` の wiki のページ、索引、ログへの書き込みを、モデルの Edit と Write から、wiki 単位のロックを持つ Python のプロセス（`wiki_apply.py`）に移す設計の 1 版目である。実装はまだない。

この書く段は、もとはセッションの取り込みの設計の 4 版目に入っていた。あなたの 4 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-4.md`）の重大の 7 件のうち 6 件がそこに出たので、作者の判断で別の設計書に分けた。この版は、その指摘の原因（済んだかどうかを今の中身から推す作り）を、日誌、前に進めるだけの当て方、索引とログの決まった操作に変えたものである。セッションの取り込みの設計の 5〜7 回目のレビュー（`design-review-5.md`〜`design-review-7.md`）が挙げた raw の置き場所の指摘も、この設計に回した。

この版を壊してほしい。確かめてほしい点:

1. 6 節の日誌（wiki 単位、次にロックを取った書き手が前に進める）: 途中で止まったときに、二重の適用、変更の消失、正しく当たった変更を競合と取り違えること、`stuck` にならずに他人の変更を上書きすることの反例を探す。
2. 4 節の決まった操作（`index-add`、`log-entry`、`log-sub`）: 字面の規則（節の終わり、フェンス、改行、BOM、置き換えの行、`nth`）で、違う場所に足す、行を消す、前の行を壊す反例を探す。
3. 3 節のパスの規則と同じファイルの判定、1 節の作業用のフォルダー、6 節の 1 のロック: 同じファイルを 2 つの項目で指す、ロックや管理領域を変更の対象にする、作業用のフォルダーが wiki の外か raw の中に出る反例を探す。
4. 7 節の raw の検査: 主張（書く直前に、行き先の親とその祖先の実体が raw のディレクトリの実体と一致しない）で、書く段の書き込みが raw の中身を変える反例を探す。主張の範囲を超えて「生じない」と書いた箇所がないか。
5. 5 節の `plan_sha256` が、適用の意味をすべて縛っているか。承認したあとに、承認した差分と違う結果を書ける経路がないか。
6. 10 節の手順の書き換えが、モデルに wiki のファイルを Edit と Write で直接書かせる経路を残していないか。既存の `commands/ingest.md` の手順 6〜7、`references/ingest-workflow.md`、`graph-workflow.md` と食い違わないか。セッションの取り込みの設計（`docs/plans/wiki-session-ingest-2026-11-14.md`）の S7〜S9 と `scan` の扱いと食い違わないか。
7. 「指摘との対照」の表の「生じない」が、本当に生じないか。

## 読む版

作業ツリーのサブモジュール `info-hive-wiki/` は 83dbb30 にある。既存の実装と文書はそこを読む。親のリポジトリの対象の設計書は作業ツリーのものを読む。

## レビューしなくてよいこと

- 設計書の「作者の判断（2026年11月14日）」の 4 つは、作者が決めた。その是非は論じなくてよい。特に、Claude Code のツールを通らない書き手（エディター、Codex、ほかのスクリプト）を考えないことは前提である。判断のもとで設計が成り立たない点があれば、それは指摘してほしい。
- 「保証しないこと」の 1〜8 に書いた限界そのものは、指摘しなくてよい。限界の書き方と食い違う主張が、設計のほかの所にあれば指摘してほしい。
- 「作者が決めること」の 1〜6 のどちらが良いかは論じなくてよい。

## 読むべきもの

- `docs/plans/wiki-apply-2026-11-14.md`（対象）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-v4.md` の 9 節と 10 節（前の案）、`design-review-4.md`〜`design-review-7.md`、`concurrency-check.md`
- `docs/plans/wiki-session-ingest-2026-11-14.md`（S7〜S10 と `scan`）
- `info-hive-wiki/` の `commands/ingest.md`、`commands/query.md`、`commands/learn.md`、`skills/info-hive/references/ingest-workflow.md`、`graph-workflow.md`、`scaling-playbook.md`、`skills/info-hive/assets/index.md.template`、`log.md.template`、`wiki-cache_gitignore.template`、`skills/info-hive/scripts/wiki_graph_common.py`、`wiki_browse_fs.py`、`wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_pages.py`、`wiki_initialized.py`、`wiki_mcp_common.py`、`init_wiki.py`
- `docs/adr/0008-numbered-workspace-layout.md`、`0019-wiki-root-is-marked-by-schema.md`

応答は日本語で書く。
