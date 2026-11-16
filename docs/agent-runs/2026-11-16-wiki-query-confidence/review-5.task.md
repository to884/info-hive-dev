# 5 回目のレビュー（wiki に内容がないときの扱い）

前回の監査の指摘 6 で、wiki に関係する内容がないときの扱いが決まっていなかった。2 つの規則が食い違っていたためである。

- `commands/query.md` の手順 7：確からしさを付けない。
- 手順 5b の表：wiki の外の知識で補った → 低。

作者は「wiki の外の知識を添えない」と決めた。差分は `git -C info-hive-wiki show HEAD`（2359ba0）にある。親の ADR-0028 の決定の表にも 1 行足した（`docs/adr/0028-wiki-query-answer-confidence-by-rules.md`、まだコミットしていない）。

直した場所は次のとおりである。

- `commands/query.md` の手順 7
- `query-workflow.md` の手順 5 と手順 5b の冒頭。5b の表の「wiki の外の知識 → 低」は、wiki に答えの一部があり、残りの前提を補ったときだけに限った。
- `SKILL.md` の概要
- `docs/commands.md`、`docs/workflows.md`
- CHANGELOG

## 特に崩してほしい点

- 「関係する内容がまったくない」と「答えの一部がある」の境目があいまいで、外の知識を添えてよいかが判定によって割れないか。
- 手順 4 の「答えは自分の知識ではなく wiki から取る」、手順 5b、手順 7、手順 8 との間に食い違いが残っていないか。
- コマンド、スキル、利用者向けの文書、CHANGELOG、ADR の書き方がそろっているか。

重大度は、利用者が普通に使う場面で起きる度合いで分けてほしい。

## 対象のファイル

- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/docs/commands.md`
- `info-hive-wiki/docs/workflows.md`
- `info-hive-wiki/CHANGELOG.md`
- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
