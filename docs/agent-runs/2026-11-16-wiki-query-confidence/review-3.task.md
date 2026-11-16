# 3 回目のレビュー

2 回目のレビュー（`review-2.md`、却下）の指摘を受けて直した。差分は `git -C info-hive-wiki show HEAD`（6c24bdb）にある。ADR-0028 の「理由」に、2 回目に崩れた前提と直し方を足した。

直した構造は次のとおりである。

1. 前提の出発点を「その事柄の正本に書かれていたか」で決め直した。wiki 自身の事柄（取り込みの時系列、規約、構成）では、wiki の記録（`log.md`、`SCHEMA.md`、インデックス、frontmatter）を正本とした。
2. 出発点の表は上から順に見て、最初に当たった行を取る形にした。最後の行は「どれにも当たらない wiki のファイル → 中」である。
3. 確かめに読むソースの要約ページを、1 つの前提につき 2 ページまでにした。見つからないか読めなければ「中」のままにする。
4. 検索の縮退の条件を「`mode` が `hybrid` でないか、`index.state` が `embedding`」とした。理由は、付けた引数と `warning`、標準エラーで決め、上から順に見る表にした。表は、ページ単位、`--no-embed`、モデルを使えない、埋め込みの途中、不明の順である。直し方も理由ごとに分けた。
5. 結論ごとの確からしさを示す条件を「結論によって違うとき、それぞれに書く」に直した。
6. 決まった手順と判断の境目に、評価の言葉で書かれた条件を判断の側に入れた。

前回と同じ対象を、同じ観点で読み直してほしい。直しが元の指摘を解消したか、直しの仕組みから新しい欠陥が出ていないかを、特に確かめてほしい。

重大度は、利用者が普通に使う場面で起きる度合いで分けてほしい。作るのに特別な条件が要る反例は「軽微」とし、その条件を書いてほしい。

対象のファイルは前回と同じである。

- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/docs/commands.md`
- `info-hive-wiki/CHANGELOG.md`
