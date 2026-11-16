# 2 回目のレビュー

1 回目（`review-1.md`、条件付きで採用可）の指摘を受けて直した。差分は `git -C info-hive-wiki show HEAD`（17362bf）にある。親の ADR-0028 にも追記した（まだコミットしていない）。

## 直したこと

- **重大の指摘：** 外の知識の例外を、frontmatter の `raw` の欄ではなく役割で決めた。新しい例外は「ソースの要約ページが raw ソースとして参照しているファイル」である。`raw` の原本のほか、取り込みの手順がそのソースのために作って本文から参照しているファイル（文字コードを変換した写し、rag の抽出済みの Markdown、Web ページの画像など）も含む。直した場所は、決め方のファイル、コマンドの手順 7、`docs/commands.md`、CHANGELOG である。
- **軽微の指摘：** `docs/commands.md` に、この例外を書いた。
- **軽微の指摘：** CHANGELOG の原因の書き方を、「読み違いで説明できた」「この版で測り直して確かめる」に弱めた。
- **軽微の指摘：** ADR-0028 の置き場所の行に、日付つきの追記を足した。承認済みなので、元の文は消していない。

## 確かめてほしいこと

- 直しが重大の反例を解消したか。Shift_JIS の写しと、rag の抽出済みの Markdown の 2 つで確かめてほしい。
- 直しの仕組みから、新しい抜け道が出ていないか。たとえば、「本文から参照しているファイル」と言えば、何でも raw の層として扱えてしまわないか。
- 前回の観点で、新しい食い違いが出ていないか。

重大度は、利用者が普通に使う場面で起きる度合いで分けてほしい。

## 対象のファイル

- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/references/query-confidence.md`
- `info-hive-wiki/docs/commands.md`
- `info-hive-wiki/CHANGELOG.md`
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`
- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
