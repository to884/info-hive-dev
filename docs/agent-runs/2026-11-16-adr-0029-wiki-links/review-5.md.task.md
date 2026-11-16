# 依頼：ADR-0029（wiki と raw の記事にリンクを置かない）の 5 回目の敵対的レビュー

対象は `docs/adr/0029-wiki-and-raw-hold-no-links.md`（この worktree）の 9 版目である。応答は日本語で書く。

## 前回からの変化

4 回目のレビュー（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-4.md`、却下）のあと、次を直した。

- 記事を、変えたあとの走査の関数だけで決めた。走査は、名前が `.` で始まる項目を、どの深さでも降りず読まない形に変える。
- スクリプトが記事を読む口を、走査の結果と `wiki_pages.article_path()` の 2 つにした。MCP の `list_index()` の直接の読み取りを移す。
- `Walk.links` を、検索の `warning`、lint の `links`、閲覧の診断まで届ける。
- 書き込みの部品に渡せる根に、守る木の外のデータの場所の決まった根（ADR-0023 の `K` など）を足した。

そのあと作者が決めた（作者の決定の 8）。これは崩す対象ではない。

- リンクに当たっても、プラグインはディレクトリもファイルも置き換えない。警告を利用者に通知する。直す道具（`wiki_links.py fix`）と、部品の「リンクの名前を直す操作」は作らない。守る木の中のリンクのソースは、置き換えず、取り込まず、警告する。

作者の決定（1〜8）そのものではなく、決定を具体化した本書の提案と、事実の記述を崩してほしい。1〜4 回目と同じ指摘の繰り返しではなく、直したあとの形に残る欠陥を探してほしい。

## 確かめてほしいこと

- 作者の決定の 8 を入れたあと、本書の中に、置き換える・直すことを前提にした記述が残っていないか。決定どうし（3、7、8）が食い違っていないか。
- 「警告を利用者に通知する」が、各コマンド（lint、ingest、query、browse、MCP のツール）と書き込みの部品で、利用者に届く経路として具体的に決まっているか。黙って読まない・書かないだけになる経路がないか。
- 走査の変更（名前が `.` で始まる項目を除く、リンクを拒む）と記事を読む口が、今のコードと、ほかの ADR（0010、0017、0019、0020、0023）に対して成り立つか。
- 書き込みの部品の根の決め方に、穴が残っていないか。
- ADR が「確かめた」と書く事実が、コードと合うか。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コード、設計書、レビューの記録は、次の主のチェックアウトの絶対パスで読む（読み取りだけ）。wiki のサブモジュールは origin/main が進んでいるので、指定の版は `git show 2452f59:<パス>` で照らす。

- ADR（対象）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 1〜4 回目のレビュー: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`〜`review-4.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0010、0013、0017、0019、0020、0023）
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- wiki のコード: `C:/Works/info-hive-dev/info-hive-wiki/`（`commands/`、`skills/info-hive/scripts/`、`skills/info-hive/references/`）
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`

ファイルは変えない。
