# レビューの目的

`docs/plans/wiki-session-ingest-2026-11-14.md` は、`info-hive-wiki` の `/wiki:ingest` に、Claude Code のセッションの記録（JSONL）を原本にする取り込みを足す設計の案である。実装はまだない。この設計のまま実装すると壊れる点、既存の実装や設計書（ADR）と食い違う点、決め残しを探してほしい。

## 読む版についての注意（重要）

作業ツリーは古い。サブモジュール `info-hive-wiki/` は 0.10.1 の古いコミットにあり、`wiki_rawcheck.py`、`commands/ingest.md` の W1〜W9、`wiki_fetch.py` の `--wiki` がない。親のリポジトリの `docs/adr/` にも、ADR-0018 と ADR-0019 がないことがある。

設計は origin/main を基準にしている。次の展開した写しを読むこと（どちらも origin/main を `git archive` で展開したもの）。

- `info-hive-wiki` の origin/main（318a357）: `C:\UserData\toshiki\Temp\claude\870eed15d1242065\ee976e3c-1e88-4b33-b7e0-3c4b933e8b94\scratchpad\wiki-main\`
- 親のリポジトリの origin/main（68c5673）の `docs/` と `tests/`: `C:\UserData\toshiki\Temp\claude\870eed15d1242065\ee976e3c-1e88-4b33-b7e0-3c4b933e8b94\scratchpad\dev-main\`

写しが読めなければ、`git -C info-hive-wiki show origin/main:<パス>` と `git show origin/main:<パス>` で読む。

## 設計が果たすべきこと

- 1 回の取り込みで、セッションの会話を raw の原本と、記事の形のソースの要約ページとして wiki に入れる。
- raw は記録から決まった手順で作る。同じ記録からは同じ raw ができる。
- モデルの思考（`thinking`）を raw に入れない。秘密の情報と個人の情報を、raw を固定する前に伏せられる。
- info-hive はプラグインなので、開発用の PC に固有の置き場所や値を仕様にしない。Claude Code の記録の形式は公開された仕様ではないことを前提にする。
- 既存の取り込み（`commands/ingest.md` の手順 1〜8 と W1〜W9、`wiki_fetch.py`、`wiki_rawcheck.py`）と、承認済みの ADR に食い違わない。

## 確かめてほしい点

1. 記録の読み方と抜き出し（設計の「3. 読み方」と「4. 残すものと除くもの」）。許可リストの規則で、会話でないもの（特に思考、ツールの結果、ハーネスやアプリが差し込んだ文）が raw に入る経路がないか。人の発言を取りこぼす経路がないか。ターンの区切りが誤る経路がないか。書きかけの最後の行とハッシュの扱いに誤りがないか。
2. 伏せ字（「5. 伏せ字」）と確認の検査（「7. 伏せ字の確認」）。`check` の性質（frontmatter の一致、`［伏せ字］` を除いた本文が写しの部分列であること、ターンの見出しの扱い）で、書き足しや言い換えを通してしまう反例がないか。逆に、正当な伏せ字を誤りにする反例がないか。
3. raw の形（「6. raw の形」）。frontmatter の値、見出しを 2 段下げる処理、ターンの番号を根拠の位置に使うことが、`wiki_text.py`、`wiki_pages.py`、`page-conventions.md`、lint、閲覧、グラフの抽出と食い違わないか。
4. 記録の場所（「2. 記録の場所」）と ID の検査。パスの外を読む経路、`CLAUDE_CONFIG_DIR` の扱いの誤りがないか。
5. 既存の取り込みとの整合（「1. 入口」「8. 取り込み」「9. 取り込み直し」「10. スクリプト」）。`wiki_fetch.py` の作業用の写し（`.wiki-cache/ingest/<スラッグ>/`、`fetch.json`）、終了コード、`unchanged` の扱い、ADR-0004、ADR-0015、ADR-0018、ADR-0019 と食い違わないか。
6. 「試験」の節で、上の点を確かめきれるか。

## レビューしなくてよいこと

- 「作者が決めること」の 1（入口を `/wiki:ingest` の引数にするか、専用の `/wiki:session` にするか）は作者が決める。どちらが良いかは論じなくてよい。どちらを選んでも成り立たない点があれば、それは指摘してほしい。

## 読むべきもの

- `docs/plans/wiki-session-ingest-2026-11-14.md`（対象。作業ツリーにある）
- 写しの `wiki-main\commands\ingest.md`、`wiki-main\commands\learn.md`
- 写しの `wiki-main\skills\info-hive\scripts\wiki_fetch.py`、`wiki_rawcheck.py`、`wiki_text.py`、`wiki_pages.py`、`wiki_lint.py`、`wiki_initialized.py`
- 写しの `wiki-main\skills\info-hive\references\ingest-workflow.md`、`page-conventions.md`、`SKILL.md`
- 写しの `dev-main\docs\adr\0004-raw-holds-translated-web-pages.md`、`0015-wiki-article-methodology-adopted-in-stages.md`、`0018-wiki-requires-python-312.md`、`0019-wiki-root-is-marked-by-schema.md`
- 写しの `dev-main\tests\wiki\test_wiki_fetch.py`、`check_commands_mcp.py`、`test_source_claims.py`

Claude Code のセッションの記録の実物は、`C:\Users\toshiki\.claude\projects\C--Works-info-hive-dev\*.jsonl` にある。形を確かめるために読んでよいが、中身（会話の文）をレビューの結果に引用しないこと。個人の情報が含まれる。

応答は日本語で書く。
