# レビューの目的

Claude Code プラグイン `wiki`（info-hive-wiki）の `/wiki:query` に、回答の確からしさ（confidence）を付ける変更をレビューしてほしい。変更は、エージェント（LLM）が従う手順の文書だけで、コードは変えていない。

作者の要求は次の 2 つである。

1. `/wiki:query` の結果（回答）に confidence を付ける。
2. confidence が低いときは、上げる方法をユーザーに提案する。

設計の判断は ADR-0028 にある。検索の行に付ける案（B）は採らず、回答に付ける案（A）を採った。

## 読むファイル

- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`（設計の判断）
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`（決め方の正本。手順 5b、手順 6、特殊なクエリの種類、避けるべきパターン）
- `info-hive-wiki/commands/query.md`（コマンド。手順 6b、7、8）
- `info-hive-wiki/skills/info-hive/SKILL.md` の「クエリのワークフロー（概要）」
- `info-hive-wiki/docs/commands.md` の `/wiki:query` の節
- `info-hive-wiki/CHANGELOG.md` の 0.20.0
- 差分は `git -C info-hive-wiki show HEAD` で見られる

規則が参照している既存の仕組みが、実際にそう動くかも確かめてほしい。たとえば、グラフのエッジの `confidence` と `status` の値（`references/graph-workflow.md`）、経験のパターンの `status`（`SCHEMA.md` の テンプレート `skills/info-hive/assets/SCHEMA.md.template`、`/wiki:learn`、`/wiki:evolve`）、MCP の `query` の `warning` と `index.state`（`scripts/wiki_mcp_server.py`、`scripts/wiki_index.py`）、`--decide` の `failed_open`、`/wiki:graph lint`、`/wiki:lint` が古い主張や矛盾を検出するか（`references/lint-workflow.md`）。

## 特に崩してほしい点

- 規則が、同じ wiki と同じ質問で、エージェントごとに違う判定を生む余地（主張の切り分け、「直接書かれている」の解釈、「結論を支える主張」の範囲など）。
- 判定が高すぎる方向に誤る反例（自分の回答を根拠にする、同じ資料の言い換えを根拠にする、シンセシスのページの扱い、抜粋だけ読む、など）。
- 上限の表の抜けや、出発点と上限の食い違い。
- 「上げる方法」が、存在しないコマンドや機能、またはその機能がしないことを勧めていないか。承認なしに wiki を書き換える道が残っていないか。
- コマンドの文書と正本（query-workflow.md）、利用者向け文書、CHANGELOG、ADR の間の食い違い。
- 並行して設計中の「2 つの wiki を引く問い合わせ」（`docs/plans/wiki-query-two-wikis-2026-11-16.md` が親のリポジトリの main の作業ツリーにある。この worktree にはないかもしれない）と組み合わさったときに、規則が崩れるか。読めなければ飛ばしてよい。
- SemVer（0.20.0、minor）の判断が妥当か。
