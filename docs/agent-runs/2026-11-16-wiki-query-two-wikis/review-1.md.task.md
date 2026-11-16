# レビューの目的

`docs/plans/wiki-query-two-wikis-2026-11-16.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）の `/wiki:query` で、利用者が求めたときだけ、ユーザースコープの wiki とプロジェクトの wiki の 2 つを引く設計である。コードは変えず、コマンドとスキルの手順の文書だけを変える。背景は `docs/research/wiki-cross-scope-copy-options-2026-11-15.md` の案 E。

設計が守ろうとしていること:

- 2 つの wiki を引くのは、問い合わせごとに利用者が求めたときだけ。
- 2 つの根は、登録（指示と作業領域の設定）で決め、場所から推し量らない。決まらなければ、もう 1 つは引かずに理由を書く。
- 検索の順位を wiki をまたいで混ぜない。リンク、raw、sources、グラフは、書かれた wiki の中でだけ解決する。
- 出典に wiki の区別を付ける。食い違いは両方を示す。
- 2 つの wiki のページを使った回答は、シンセシスとして保存しない（写す機能に化けないため）。
- 「黙って混ぜない」の意味を `SKILL.md` の 1 か所に書き、ほかは指す。

設計が保証しないと認めていること（第 5 節）: 登録の読み違い、会話に入ったユーザースコープの中身があとでプロジェクトのファイルやコミットに書かれること、出典にしなかったページの中身が回答の文に入ること、同じ話題の判断の誤り、費用。

次を崩すことを狙ってほしい。

- 第 2 節の前提が、今の実装（`info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py`、`wiki_index.py`、`wiki_search.py`、`wiki_workspace.py`、`wiki_help.py`）と文書（`info-hive-wiki/commands/query.md`、`info-hive-wiki/skills/info-hive/references/query-workflow.md`、`SKILL.md`、`agent-memory-integration.md`、`mcp-server.md`）と照らして誤っていないか。
- 第 3.2 節の根の決め方で、別の wiki を選ぶ、同じ wiki を 2 回引く、引けないのに黙って 1 つで答える反例。`docs/plans/wiki-browse-scope-2026-11-12.md` のスコープの規則との矛盾。
- 第 3.6 節の保存の制限をすり抜けて、もう 1 つの wiki の中身が wiki に書かれる経路（手順 8 以外の書き込みも含む）。
- 第 3.7 節の書き込みの記述の誤り。
- 「コードを変えない」が成り立たない箇所（今のツールの制約で、手順だけでは守れない規則）。
- 作者が決める事項（第 6 節）の抜け。保証しないことに入れるべきなのに入っていない欠陥。

設計の段階なので、細かな文言より、設計を覆す欠陥を優先する。
