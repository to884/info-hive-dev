# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の 5 版目に、5 回目と 6 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-5.md`、`design-review-6.md`。あなたのレビュー）の直しを入れたものである。実装はまだない。

6 回目の重大 2 件は、どちらも「wiki の書く先が raw と重ならないことを、パスの検査で示す」作りに出た。作者の側は、パスで重なりを証明するのをやめた。代わりに、`write` が書いた raw を読み取り専用にし（9 節の手順 8）、S10 の `verify` が raw のバイト列と読み取り専用の属性を照らす形に変えた。Windows では、読み取り専用のファイルへの Claude Code の Write と Edit が、ジャンクションを経由しても `EPERM` で失敗することを確かめた。POSIX では防げない見込みで、`verify` で見つけるだけにした（「保証しないこと」の 12）。

この版を壊してほしい。特に次を見てほしい。

1. 読み取り専用と `verify` の組み合わせで、「保証しないこと」の 12 に書いた範囲の外で、raw が気づかれずに変わる反例がないか（Windows と POSIX。Claude Code の Write と Edit、`wiki_graph_extract.py`、lint、閲覧、MCP の索引を含む）。逆に、正しい運用で `verify` が誤って止まる場合が、設計の書き方と食い違わないか。
2. 6 回目の軽微 2 件（`show` の続きの案内、自己検査の数え方）が解消したか。
3. 1〜6 回目のレビューで崩せなかった点が、直しで崩れていないか。

## 読む版

既存の実装と文書は、次のコミットを `git show` で読むこと。

- `info-hive-wiki`: 83dbb30。`git -C info-hive-wiki show 83dbb30:<パス>`
- 親のリポジトリ: a237e8f。`git show a237e8f:<パス>`

## レビューしなくてよいこと

- 設計書の見出しの表にある「作者の判断（2026年11月14日）」の (1)〜(7) の是非。特に、(1) `uuid` のない知らない記録を読み飛ばすこと、(6) Claude Code のツールを通らない書き手を考えないこと、(7) wiki の書く段を別の設計書に分け、wiki の書き込みの排他をこの設計で扱わないことは、前提である。判断のもとで設計が成り立たない点があれば、それは指摘してほしい。
- `docs/plans/wiki-apply-2026-11-14.md`（書く段の方針）。
- 「保証しないこと」の 1〜12 に書いた限界そのもの。限界の書き方と食い違う主張が、設計のほかの所にあれば指摘してほしい。
- 「作者が決めること」の 1〜7 のどちらが良いか。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-6.md`、`design-review-5.md`
- 83dbb30 の `info-hive-wiki` の `commands/ingest.md`、`skills/info-hive/SKILL.md`、`skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_lint.py`、`wiki_initialized.py`、`wiki_pages.py`、`wiki_text.py`、`wiki_graph_extract.py`
- a237e8f の親の `docs/adr/0004-raw-holds-translated-web-pages.md`、`0019-wiki-root-is-marked-by-schema.md`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。構造を確かめるために読んでよいが、会話の文をレビューの結果に引用しないこと。

応答は日本語で書く。
