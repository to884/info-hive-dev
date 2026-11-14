# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の案の 2 版目である。実装はまだない。

1 版目は、あなたのレビュー（`docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-1.md`）で却下された。作者の側は、指摘を 1 つずつ塞がず、崩れた前提を `docs/agent-runs/2026-11-14-wiki-session-ingest/root-causes.md`（記号 A〜H）に書き出して、構造を変えた。対応の対照は、設計書の最後の「1 回目のレビューの指摘と対応」にある。

次の 2 つを確かめてほしい。

1. 1 回目の指摘（致命 1、重大 2〜8、崩れる前提、軽微）が、2 版目の構造で本当に解消したか。解消していないもの、別の形で残ったものを挙げる。
2. 2 版目で新しく入った構造（本文をターンごとに 1 つのフェンスで囲む形、構造と中身を分けた `check`、記録ごとの属性だけで決める話者、除いた位置の印のターン、`reviewed_at` と `review_state`、`raw_ref`、`inspect` と `--title`、ID の探し方でリンクをたどらないこと）に、新しい欠陥、反例、決め残しがないか。

## 読む版についての注意（重要）

作業ツリーのサブモジュール `info-hive-wiki/` は 0.10.1 の古いコミットにある。設計は origin/main を基準にしている。既存の実装と文書は、`git -C info-hive-wiki show origin/main:<パス>` と、親のリポジトリの `git show origin/main:<パス>` で読むこと（1 回目と同じ。展開した写しは読めなかったので使わない）。

- `info-hive-wiki` の origin/main は 318a357、親の origin/main は 68c5673 である。

## 設計が果たすべきこと

- 1 回の取り込みで、セッションの会話を raw の原本と、記事の形のソースの要約ページとして wiki に入れる。
- raw は記録から決まった手順で作る。同じ記録を、同じ版の抽出器に同じ引数で渡せば、同じ raw ができる。
- モデルの思考（`thinking`）を raw に入れない。秘密の情報と個人の情報を、raw を固定する前に、人が本文、会話から来た frontmatter の値、ファイル名のどこからでも伏せられる。
- info-hive はプラグインなので、開発用の PC に固有の置き場所や値を仕様にしない。Claude Code の記録の形式は公開された仕様ではないことを前提にし、形式が変わったら何も通さない側に倒れる。
- 既存の取り込み（`commands/ingest.md` の手順 1〜8 と W1〜W9、`wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_lint.py` の `missing_raw()`）と、承認済みの ADR に食い違わない。

## 特に確かめてほしい点

- フェンスで囲む形: 本文がフェンスの外に出る経路が本当にないか（CommonMark と、同梱の markdown-it-py の `wiki_pages.new_parser()` の両方で）。改行の正規化、空の本文、本文がバッククォートだけの行、`\r` だけの改行、Unicode の改行（U+2028 など）、行頭の空白、フェンスの情報の文字列を含めて考える。
- `check`: 構造と中身を分けた照らし方で、書き足し、言い換え、ターンをまたぐ移動、話者のすり替えを通す反例がないか。逆に、正当な伏せ字（例えば、本文に `［伏せ字］` という文字列がもともとある場合）を誤りにする反例がないか。frontmatter の値の照らし方（引用符、エスケープ、`format_fm_value` の書き方）で崩れないか。
- `review_state`: 3 つの状態の判定と、`--force`、`check --finish` の途中で止まった場合の組み合わせに、穴がないか。
- 話者: 記録ごとの属性だけで決める規則で、会話でないものが入る経路と、人の発言を取りこぼす経路を、実物の記録の構造（中身は引用しない）で確かめる。

## レビューしなくてよいこと

- 「作者が決めること」の 1（入口を `/wiki:ingest` の引数にするか、専用の `/wiki:session` にするか）は作者が決める。どちらが良いかは論じなくてよい。どちらを選んでも成り立たない点があれば、それは指摘してほしい。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象。作業ツリーにある）
- `docs/agent-runs/2026-11-14-wiki-session-ingest/design-review-1.md`、`root-causes.md`（作業ツリーにある）
- origin/main の `info-hive-wiki` の `commands/ingest.md`、`commands/learn.md`、`skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_text.py`、`wiki_pages.py`、`wiki_lint.py`、`wiki_initialized.py`、`skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`skills/info-hive/SKILL.md`
- origin/main の親の `docs/adr/0004-raw-holds-translated-web-pages.md`、`0015-wiki-article-methodology-adopted-in-stages.md`、`0018-wiki-requires-python-312.md`、`0019-wiki-root-is-marked-by-schema.md`、`tests/wiki/test_wiki_fetch.py`、`check_commands_mcp.py`、`test_source_claims.py`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。形を確かめるために読んでよいが、中身（会話の文）をレビューの結果に引用しないこと。個人の情報が含まれる。

応答は日本語で書く。
