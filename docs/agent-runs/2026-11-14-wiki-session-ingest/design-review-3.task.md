# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の案の 3 版目である。実装はまだない。

1 版目と 2 版目は、あなたのレビュー（`design-review-1.md`、`design-review-2.md`）で却下された。作者の側は、崩れた前提を `root-causes.md`（1 回目は A〜H、2 回目は I〜P）に書き出して、構造を変えた。3 版目を書いたあと、レビューの前に別のモデルの見直しも入れた（設計書の最後の「3 版目をレビューの前に見直して直した点」）。どれも `docs/agent-runs/2026-11-14-wiki-session-ingest/` にある。

次の 2 つを確かめてほしい。

1. 2 回目の指摘（致命 1、重大 2〜7、崩れる前提、軽微 1〜5）が、3 版目の構造で本当に解消したか。解消していないもの、別の形で残ったものを挙げる。
2. 3 版目で新しく入った構造に、新しい欠陥、反例、決め残しがないか。特に次のもの。
   - 入口: `.jsonl` を `inspect` にかけ、`session` でなければ止まる。
   - raw の文法と、自前の読み手と書き手による書き直しの一致（「6. raw の形」と「7. 伏せ字の確認」の字面の検査）。
   - 確認で許す編集を、ひと続きの並びの `［伏せ字］` への置き換えと、ターンの丸ごとの削除だけにしたことと、その照らし方（断片を左から最も早い位置で探す）。
   - 確認の前の写しを作業用のフォルダーに置き、raw を `check --finish` だけが書くこと。「9. 取り込み直し」の 6 行の表。
   - `--before <uuid>` で範囲を決めること。
   - セッションの ID の 4 段の決め方。
   - フェンスの外に置く文字列の制限（題名を見出しにしない、モデルの名前の検査）。

## 読む版についての注意（重要）

作業ツリーのサブモジュール `info-hive-wiki/` は古いコミットにある。設計は origin/main を基準にしている。既存の実装と文書は、次のコミットを `git show` で読むこと。

- `info-hive-wiki`: 7495ca5（0.14.1）。`git -C info-hive-wiki show 7495ca5:<パス>`
- 親のリポジトリ: a0f01c9。`git show a0f01c9:<パス>`

2 回目のレビューは 318a357 と 68c5673 を読んだ。その後に入った変更（`/wiki:help` の個別のヘルプ、`type` と `updated` の値の扱い）は、設計の「基準にした版」の欄に書いた。

## 設計が果たすべきこと

- 1 回の取り込みで、セッションの会話を raw の原本と、記事の形のソースの要約ページとして wiki に入れる。
- raw は記録から決まった手順で作る。記録の同じ範囲を、同じ版の抽出器に同じ引数で渡せば、どの PC でも同じ raw ができる。
- モデルの思考（`thinking`）を raw に入れない。秘密の情報と個人の情報を、人が確かめる。raw のルートには、確認を終えたものだけを書く。
- info-hive はプラグインなので、開発用の PC に固有の置き場所や値を仕様にしない。Claude Code の記録の形式は公開された仕様ではないことを前提にし、形式が変わっても、入口で認識できなくても、ユーザーの明示の指示なしには何も通さない。
- 既存の取り込み（`commands/ingest.md` の手順 1〜8 と W1〜W9、`wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_lint.py` の `missing_raw()`）と、承認済みの ADR に食い違わない。

## レビューしなくてよいこと

- 「作者が決めること」の 1（入口を `/wiki:ingest` の引数にするか、専用の `/wiki:session` にするか）と 7（先頭の `<system-reminder>` を既定で除くか）は作者が決める。どちらが良いかは論じなくてよい。どちらを選んでも成り立たない点があれば、それは指摘してほしい。
- 設計は、`［伏せ字］` で隠したことで文の意味が変わらないことを保証しない、と明記している（「7. 伏せ字の確認」）。この限界そのものは指摘しなくてよい。限界の書き方と食い違う主張が設計のほかの所にあれば、指摘してほしい。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象。作業ツリーにある）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-1.md`、`design-review-2.md`、`root-causes.md`（作業ツリーにある）
- 7495ca5 の `info-hive-wiki` の `commands/ingest.md`、`commands/learn.md`、`skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_text.py`、`wiki_pages.py`、`wiki_lint.py`、`wiki_initialized.py`、`init_wiki.py`、`skills/info-hive/assets/wiki-cache_gitignore.template`、`skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`skills/info-hive/SKILL.md`
- a0f01c9 の親の `docs/adr/0004-raw-holds-translated-web-pages.md`、`0015-wiki-article-methodology-adopted-in-stages.md`、`0018-wiki-requires-python-312.md`、`0019-wiki-root-is-marked-by-schema.md`、`tests/wiki/test_wiki_fetch.py`、`check_commands_mcp.py`、`test_source_claims.py`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。形を確かめるために読んでよいが、中身（会話の文）をレビューの結果に引用しないこと。個人の情報が含まれる。

応答は日本語で書く。
