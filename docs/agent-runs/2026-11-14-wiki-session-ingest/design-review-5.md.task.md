# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の 5 版目である。実装はまだない。

4 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-4.md`）は 4 版目を却下したが、重大の指摘の大半は、新しく足した wiki の書く段（`wiki_apply.py`）に出た。作者の判断で、書く段を別の設計書（`docs/plans/wiki-apply-2026-11-14.md`。今は方針だけ）に分けた。5 版目は、4 版目から書く段を外し、wiki への書き込みを既存の手順（モデルの Write と Edit）に戻して、書く前の確認（`scan` と、中身をユーザーに見せる手順）を足したものである。4 版目は `design-v4.md` に残してある。

この版を壊してほしい。特に、4 版目から変えた所を重点に見てほしい。

1. 9 節（`write`。raw を重ねて書かない形で置く）: 排他作成、行き先の検査、同じ取り込みの判定、途中で止まったときの扱いに、上書き、不完全な raw、リンクを経由した書き込みの反例がないか。
2. 10 節（`scan` と中身を見せる手順）: 伏せた文字列の作り方、短い文字列の扱い、`--allow`、出力に文字列を出さないこと、助言の検査という位置づけが、目的（秘密の情報と個人の情報が、人の確認を経ずに Git で管理される場所に入らない）と食い違わないか。`scan` がディスクやコマンドの引数に秘密を出す経路がないか。
3. 13 節（S1〜S10）: 既存の `commands/ingest.md` の手順 1〜8 と食い違わないか。raw の確認の前の会話の文がディスクに出る経路、モデルが raw のルートを直接書く経路が残っていないか。
4. 「前提にすること」と「保証しないこと」: wiki の書き込みを既存の取り込みと同じ水準にとどめる、という割り切りの書き方が、ほかの節の主張と食い違わないか。
5. 「指摘との対照」の表の「生じない」が、本当に生じないか。4 回目の指摘のうち、この版の範囲に残したもの（重大 5 と軽微）が解消したか。

## 読む版

作業ツリーのサブモジュール `info-hive-wiki/` は古いコミットにある。既存の実装と文書は、次のコミットを `git show` で読むこと。

- `info-hive-wiki`: 83dbb30。`git -C info-hive-wiki show 83dbb30:<パス>`
- 親のリポジトリ: a237e8f。`git show a237e8f:<パス>`

## レビューしなくてよいこと

- 設計書の見出しの表にある「作者の判断（2026年11月14日）」の (1)〜(7) の是非は論じなくてよい。特に、(1) `uuid` のない知らない記録を読み飛ばすこと、(6) Claude Code のツールを通らない書き手を考えないこと、(7) wiki の書く段を別の設計書に分け、wiki の書き込みの排他をこの設計で扱わないことは、前提である。判断のもとで設計が成り立たない点があれば、それは指摘してほしい。
- `docs/plans/wiki-apply-2026-11-14.md`（書く段の方針）は、レビューの対象ではない。
- 「保証しないこと」の 1〜11 に書いた限界そのものは、指摘しなくてよい。限界の書き方と食い違う主張が、設計のほかの所にあれば指摘してほしい。
- 「作者が決めること」の 1〜7 のどちらが良いかは論じなくてよい。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-4.md`、`design-v4.md`、`concurrency-check.md`
- `docs/agent-runs/2026-11-14-wiki-session-ingest-redesign/summary.md`
- 83dbb30 の `info-hive-wiki` の `commands/ingest.md`、`skills/info-hive/SKILL.md`、`skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_lint.py`、`wiki_initialized.py`、`wiki_pages.py`、`wiki_text.py`
- a237e8f の親の `docs/adr/0004-raw-holds-translated-web-pages.md`、`0015-wiki-article-methodology-adopted-in-stages.md`、`0018-wiki-requires-python-312.md`、`0019-wiki-root-is-marked-by-schema.md`、`tests/wiki/check_commands_mcp.py`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。構造を確かめるために読んでよいが、会話の文をレビューの結果に引用しないこと。

応答は日本語で書く。
