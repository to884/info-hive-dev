# レビューの目的

`docs/plans/wiki-apply-2026-11-14.md` は、`info-hive-wiki` の wiki のページ、索引、ログへの書き込みを、モデルの Edit と Write から、利用者の PC に 1 つのロックを持つ Python のプロセス（`wiki_apply.py`）に移す設計の 4 版目である。実装はまだない。

1〜3 版目（`design-v1.md`〜`design-v3.md`）は、あなたの 1〜3 回目のレビュー（`design-review-1.md`〜`design-review-3.md`。どれも `docs/agent-runs/2026-11-14-wiki-apply/` にある）で却下された。2〜4 版目は、指摘を 1 件ずつ塞がず、前提に分けて構造を変えた（設計書の「1 回目のレビューで崩れた前提」の Q〜U、「2 回目」の V〜Z、「3 回目」の AA〜AE）。4 版目の主な変更は次のとおりである。

- AA: 行き先のパスの途中に、初期化された wiki のルートがあれば拒む。
- AB: `D/applied.json` を日誌を閉じる前に書き、日誌は印があるか `D` がないときだけ消す。
- AC: 日誌に wiki と raw のルートを書き、前に進めるときは日誌ごとに `Writer` を作り直す。
- AD: 文面の検査は、書く先の語に触れる段落をすべて挙げて分類を求める。
- AE: 節の最後の行を空でない行にし、並びに `hidden` を入れる。

3 版目で入れた構造は次のとおりである。

- V: ロック、日誌、作業用のフォルダーを、wiki の中から利用者の PC の 1 か所（`data_dir()/apply`）に移した。
- W: `plan.json` と `D` の中身を 1 回だけ読み、そのバイト列を使う。
- X: 構造の確かめを、トークンの並びの比較にした。
- Y: 移す範囲に漏れを足し、文面とスクリプトの書き込みの呼び出しの機械の検査で閉じる。
- Z: 前に進める手順の順番を決め、`D/applied.json` でやり直しを止める。

2 版目で入れた構造は次のとおりである。

- Q: 書き込みの入口を `wiki_fsguard.Writer` の 1 つにし、日誌と一時ファイルを含むすべての書き込みを同じ検査に通す。
- R: wiki の中のパスは正規のもの（途中のリンクと再解析点を拒み、祖先と同じ実体の要素を拒み、途中の要素は `.md` で終われない）だけを受ける。
- S: `apply` は計画の外の入力を取らない。計画に `plan_id` を入れ、日誌を `plan_id` で引く。
- T: 一時ファイルの名前を置く前に日誌に書く。置けないものは `stuck` にし、`stuck` があればどの計画も書かない。
- U: 見出しと節は同梱のパーサーで決め、当てたあとに読み直して、ブロックの並びが変わらないことを確かめる。

この版を壊してほしい。確かめてほしい点:

1. 1 回目と 2 回目の指摘の反例が、本当に成り立たなくなったか。Q〜AE の構造の変え方そのものから、新しい反例が出ないか（1 回目までの却下は、どれもその回に新しく足した仕組みに出た）。
2. 6 節の日誌と前に進める手順: 二重の適用、変更の消失、正しく当たった変更の取り違え、他人の変更の上書き、完了できない状態、wiki 全体が止まり続ける状態の反例。
3. 4 節の構造の確かめ: 足した行より前と後ろのブロックの並びを比べる規則で、違う場所に足す、前の行を壊す、確かめをすり抜ける反例。パーサーのトークンで節の「最後の行」を決める規則が、既存の `index.md` と `log.md` の形で破綻しないか。
4. 1 節と 3 節: 管理領域、正規のパス、同じファイルの判定、`Writer` の 4 つの検査に、書き込みの対象を取り違える、wiki の外か raw の中に書く反例。
5. 5 節の `plan_sha256` と `plan_id`: 承認した差分と違う結果を書ける経路。
6. 10 節の書き込みの指示と書き手の一覧が、`info-hive-wiki` の 83dbb30 の `commands/`、`SKILL.md`、`references/`、`scripts/` の実際の指示と書き手を漏らしていないか。11 節の 2 つの機械の検査が、漏れを本当に閉じるか。
7. 「指摘との対照」の表の「生じない」が、本当に生じないか。

## 読む版

作業ツリーのサブモジュール `info-hive-wiki/` は 83dbb30 にある。既存の実装と文書はそこを読む。対象の設計書は作業ツリーのものを読む。

## レビューしなくてよいこと

- 設計書の「作者の判断（2026年11月14日）」の 4 つは、作者が決めた。その是非は論じなくてよい。特に、Claude Code のツールを通らない書き手（エディター、Codex、ほかのスクリプト）を考えないことは前提である。判断のもとで設計が成り立たない点があれば、それは指摘してほしい。
- 「保証しないこと」の 1〜9 に書いた限界そのものは、指摘しなくてよい。限界の書き方と食い違う主張が、設計のほかの所にあれば指摘してほしい。
- 「作者が決めること」の 1〜7 のどちらが良いかは論じなくてよい。

## 読むべきもの

- `docs/plans/wiki-apply-2026-11-14.md`（対象）
- `docs/agent-runs/2026-11-14-wiki-apply/design-v1.md`、`design-v2.md`、`design-v3.md`、`design-review-1.md`〜`design-review-3.md`
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-4.md`〜`design-review-7.md`、`concurrency-check.md`
- `docs/plans/wiki-session-ingest-2026-11-14.md`（S7〜S10 と `scan`）
- `info-hive-wiki/` の `commands/`、`skills/info-hive/SKILL.md`、`skills/info-hive/references/`、`skills/info-hive/assets/index.md.template`、`log.md.template`、`wiki-cache_gitignore.template`、`skills/info-hive/scripts/wiki_graph_common.py`、`wiki_browse_fs.py`、`wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_pages.py`、`wiki_text.py`、`wiki_initialized.py`、`wiki_mcp_common.py`、`init_wiki.py`
- 親のリポジトリの `wiki/index.md` と `wiki/log.md`（既存の索引とログの実例）
- `docs/adr/0008-numbered-workspace-layout.md`、`0019-wiki-root-is-marked-by-schema.md`

応答は日本語で書く。
