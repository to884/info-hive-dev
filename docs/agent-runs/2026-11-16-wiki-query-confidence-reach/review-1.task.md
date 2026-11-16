# レビューの目的

wiki プラグイン 0.21.1 の直しをレビューしてほしい。直しの対象は `/wiki:query` の確からしさ（confidence）の決め方で、エージェントがそれを読まずに判定していた問題を直した。差分は `git -C info-hive-wiki show HEAD`（fd12baf）にある。コードは変えていない。

きっかけは、Claude Sonnet 5.5 で 11 問を 3 回ずつ流した測定である（`docs/research/wiki-query-confidence-sonnet-2026-11-16.md`。「規則の直しの案」の節を読んでほしい）。

- 決め方の正本（`query-workflow.md` の手順 5b）を開いた回は、33 回のうち 0 回だった。
- 外れた 9 回は、どれも `commands/query.md` の手順 6b の要約の言い回しを読み違えていた。
- 外の知識が回答に入る経路が 2 つあった（`AGENTS.md` と、答えを含む検索語）。

作者は、案 1〜4 を入れると決めた。

## 直したこと

1. 手順 5b の本文を `skills/info-hive/references/query-confidence.md` に移した。見出しを 1 段上げ、ほかの手順への参照を「クエリのワークフローの手順 N」にした。`query-workflow.md` の手順 5b は、このファイルへの案内だけにした。
2. コマンドの手順 6b で、`${CLAUDE_PLUGIN_ROOT}/skills/info-hive/references/query-confidence.md` を Read で開くことを求めた。要約は、読み違いを生まない次の 3 点にした。
   - ソースの要約ページに書かれていれば高で、raw まで読まなくてよい。
   - wiki 自身の事柄を `log.md` などの記録で答えたら高。
   - 上限は表の行だけで、回数、再現、raw や git で確かめていないことでは下げない。
   決め方のファイルの上限の節にも、同じことを書いた。
3. wiki の外の知識に、会話に読み込まれたプロジェクトの指示と、wiki の外のファイルを含めた。ソースの要約ページの `raw` が指す raw ソースは除く。思い付いた答えを検索語として書かないことも足した。
4. 1 行目の書き方を、字句のまま書くよう求めた。「高」のときに確かめ方を添えないことも書いた。

## 特に崩してほしい点

- 移した本文が、元の手順 5b と食い違っていないか。移すときに落ちたもの、変わったものはないか。元は `git -C info-hive-wiki show HEAD~1:skills/info-hive/references/query-workflow.md` の手順 5b にある。
- 「上限は表の行だけ」と「迷ったら低いほうにする」（`query-workflow.md` の「避けるべきパターン」）が食い違わないか。
- 外の知識の定義を広げたことで、正当な使い方まで禁じていないか。たとえば、プロジェクトの wiki の raw が `docs/` などリポジトリのファイルを指す場合や、wiki 自身の事柄を問う質問の場合。
- `${CLAUDE_PLUGIN_ROOT}` が、コマンドの本文でパスとして展開されるか。ほかのコマンドの書き方と比べてほしい。
- コマンド、決め方のファイル、`query-workflow.md`、`SKILL.md`、`docs/commands.md`、CHANGELOG、ADR-0028（承認済みで、正本を「手順 5b」と書いている）の間に、食い違いがないか。
- 0.21.1（patch）の判断。

重大度は、利用者が普通に使う場面で起きる度合いで分けてほしい。

## 対象のファイル

- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/references/query-confidence.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/docs/commands.md`
- `info-hive-wiki/CHANGELOG.md`
- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- `docs/research/wiki-query-confidence-sonnet-2026-11-16.md`
