# 依頼：ADR-0029（wiki と raw の記事にリンクを置かない）の 4 回目の敵対的レビュー

対象は `docs/adr/0029-wiki-and-raw-hold-no-links.md`（この worktree）の 7 版目である。応答は日本語で書く。

## 前回からの変化

3 回目のレビュー（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-3.md`、却下）のあと、次を直した。

- 書き込みの部品に渡す根を、wiki の根か raw の根だけにした（`.wiki-cache` を根にしない）。
- 外の原本を、場所ではなく `rag_job_id:` の印で見分ける形にした。

そのあと作者が次を決めた（作者の決定の 6 と 7）。これは崩す対象ではない。

- 規則の対象を「記事」に絞る。記事は、wiki のページ、最上位の `index.md`、`indexes/` の下の索引、`log.md`、`SCHEMA.md`、`raw:` が指す raw（外の原本を除く）と、そこまでの途中のディレクトリ。`.git/`、`.wiki-cache/`、`graph/`、`assets/` などは対象外。
- ページの走査（`wiki_pages.walk_markdown()`）を、リンクを拒む形に変える（ジャンクションに降りない、ファイルのシンボリックリンクとハードリンクのページを読まない）。拒んだ項目は `Walk.links` で返す。
- lint が見つけたリンクと、取り込みで見つけた守る木の中のリンクのソースを、利用者の承認を得て直す道具（`wiki_links.py fix`）で直す。
- 書き込みの部品の道の検査は、ADR-0023 の `Writer` と同じく、すべてのリパースポイントを拒む。

決定そのものではなく、決定を具体化した本書の提案と、事実の記述を崩してほしい。1〜3 回目と同じ指摘の繰り返しではなく、直したあとの形に残る欠陥を探してほしい。

## 確かめてほしいこと

- 「記事」の定義と「記事までの道」が、実際の走査（`walk_pages()`、`walk_index_files()`）、lint、取り込みの `raw:` の書き方と合うか。記事に入るべきなのに漏れるもの、記事でないのに入るものがないか。
- 走査を変える提案（「ページの走査」の表）が、今のコード（`wiki_pages.py`、`wiki_index.py`、`wiki_search.py`、`wiki_lint.py`、閲覧の中核）と、ほかの ADR（0010、0017、0019）に対して成り立つか。ハードリンクの判定に既存の `os.stat()` を使えるという主張は正しいか。
- 直す道具（「直す道具」と「今ある wiki と raw の直し方」）の状態の 1〜5 と確かめ方に、満たせない組み合わせ、すり抜ける形、利用者のデータを壊す形がないか。
- 書き込みの部品と ADR-0023 の `Writer` の関係、根を守る木の根だけにする形に、穴が残っていないか。
- ADR が「確かめた」と書く事実が、コードと合うか。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コード、設計書、レビューの記録は、次の主のチェックアウトの絶対パスで読む（読み取りだけ）。wiki のサブモジュールは origin/main が進んでいるので、指定の版は `git show 2452f59:<パス>` で照らす。

- ADR（対象）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 1〜3 回目のレビュー: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`〜`review-3.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0010、0013、0017、0019、0020、0023）
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- wiki のコード: `C:/Works/info-hive-dev/info-hive-wiki/`（`commands/`、`skills/info-hive/scripts/`、`skills/info-hive/references/`）
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`

ファイルは変えない。
