# 依頼: wiki 0.21.2 の確からしさの規則の直しを壊す

info-hive の wiki プラグインの `/wiki:query` は、回答に規則で決める確からしさ（高、中、低）を付ける（ADR-0028）。規則の正本は `info-hive-wiki/skills/info-hive/references/query-confidence.md`、エージェントが従う手順は `info-hive-wiki/commands/query.md` である。読み手は Claude Sonnet 5.5 のエージェントで、規則の文だけを見て判定する。

0.21.1 の規則を試験用の wiki で測ったところ、外れは規則に書かれていないことから生じた（`docs/research/wiki-query-confidence-rules-2026-11-16.md`）。作者は直しの向きを 4 つ決めた（同レポートの「規則の直しの案」の案 1-A、2-B、3、4）。0.21.2 の直しは、その 4 つと、それを閉じるために足した 3 つの決め事（ADR-0028 の「0.21.2 の追記」で「新しく決めたこと」と書いたもの）である。

## 対象

- 差分: `docs/agent-runs/2026-11-16-wiki-query-confidence-0-21-2/plugin.diff`（プラグインの `origin/main..HEAD`）
- 直したあとのファイル: `info-hive-wiki/skills/info-hive/references/query-confidence.md`、`info-hive-wiki/commands/query.md`、`info-hive-wiki/skills/info-hive/references/query-workflow.md`
- ADR の追記: `docs/adr/0028-wiki-query-answer-confidence-by-rules.md` の「0.21.2 の追記」
- 試験用の wiki: `docs/research/wiki-query-confidence-rules-2026-11-16/fixture/wiki/`、問いと期待: `docs/research/wiki-query-confidence-rules-2026-11-16/questions.json`

## 直したあとに成り立つべきこと

1. 作者の決めた 4 つの向きを、文が忠実に表している。決めていないことを決めたことにしていない（決めたなら ADR で「新しく決めたこと」と明示している）。
2. 試験用の wiki で、規則の文から次の判定だけが導ける。ほかの読みが成り立つなら、その読みと根拠の文を示す。
   - R08（`tsuyukusa-cli` に携わっているのは誰か）: 高。エッジ `works_on` は `confidence: medium` だが、ソースの要約ページ「開発者インタビュー-2025」の本文が関係を直接述べている。
   - R07（差分同期を最初に言い出したのは誰か）: 中。本文は「佐伯さんだったと思う」という記憶。エッジ `originated` は `confidence: low`。
   - R11、R12: インデックスから答えのページを選べず、`Grep` で見つけた回は中（検索の縮退の理由 0）。MCP の縮退した検索で見つけた回も中（理由 3、4）。
   - R13: インデックスの行から答えのページを選べるので、`Grep` を先に呼んだ回も含めて高。
   - R14、R15: 結論ごとに確からしさを結論の文の終わりに書き、決まった 1 行は 1 つの値。
3. 測った 15 問のほかの問い（R01〜R06、R09、R10）の判定を変えていない。
4. 規則どうし、`commands/query.md`、`query-workflow.md`、`graph-workflow.md` の間に食い違いがない（グラフを呼ぶ条件、ノードの ID、`グラフの行だけをもとに答えてはならない` との関係など）。
5. 規則の外で、判定を下げる経路や上げる経路を新しく開いていない（たとえば、`Grep` を使っただけで縮退に数えられる、インデックスの行の読み方しだいで縮退を外せる、など）。

特に、「インデックスから見つけた」の定義（インデックスの行が質問の事柄を挙げていた）、エッジだけの前提の出発点を「中」にしたこと、推測を答えにすることを「判断を加えた導き方」に入れたこと、理由 0 と理由 3・4 が重なるときの扱いを崩してほしい。
