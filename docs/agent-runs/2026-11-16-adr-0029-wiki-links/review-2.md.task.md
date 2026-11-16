# 依頼：ADR-0029（wiki と raw の木にリンクを置かない）の 2 回目の敵対的レビュー

対象は `docs/adr/0029-wiki-and-raw-hold-no-links.md`（この worktree）の 3 版目である。応答は日本語で書く。

## 前回からの変化

1 回目のレビュー（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`、却下）のあと、次を直した。直し方が原因を閉じているかも確かめてほしい。

- 一時ファイルを書き手ごとに直す節をやめ、プラグインのスクリプトが守る木に書くすべてを ADR-0023 の `wiki_fsguard.Writer` に通す形にした。ADR-0023 の範囲を広げることになる。入口には、一時ファイルを既にない一意の名前で作ることと、置き換えは名前で行うことを足した。
- 今ある配置の直し方を、手順ではなく、直したあとに成り立つ状態と確かめ方で決めた。読み取り専用とハードリンクの振る舞いは、Windows 11 と Python 3.14.6 で確かめた。
- 相対パスの `raw:` は、raw の根が渡されないとき、先頭の `..` を除いた最初の要素を raw の根とみなし、その下の道を調べる。
- `SERVER_FILES` の試験を、構文木の `import` をたどる形にした。

そのあと作者が 2 つを決めた。

- 作者の決定の 4: wiki の外の原本（rag が参照する PDF など）は規則の対象外で、リンクをたどってよい。lint も調べない。
- 作者の決定の 5: 規則はすべてのコマンドに当てる。当て方は「どのコマンドも守る木にリンクを作らず、置くときはふつうのファイルを置く」（読み方 A）。コマンドごとに守る木を調べて止まる形（読み方 B）は採らない。ADR は、コマンドごとの当て方の表と、POSIX の `publish_exclusive()` の一時的なハードリンクの例外を足した。

作者の決定（1〜5）そのものは崩す対象ではない。決定を具体化した本書の提案と、事実の記述を崩してほしい。

## 確かめてほしいこと

- コマンドごとの当て方の表が、実際のコマンドとスクリプトの書き込みと合うか。守る木にリンクを作るものが、`publish_exclusive()` のほかにないか（`os.link`、`os.symlink`、`mklink`、ハードリンクを作るコピー、`subprocess` から呼ぶ道具を含む）。
- ADR-0023 の入口に任せる形が、ADR-0023 と書く段の設計（`docs/plans/wiki-apply-2026-11-14.md`）と矛盾しないか。範囲を広げることで破れるものがないか。
- 移行の「成り立つ状態」と確かめ方に、満たせない組み合わせや、確かめをすり抜ける形がないか。
- 相対パスの `raw:` の raw の根の見なし方が、実際の `raw:` の書き方（取り込みの手順、セッションの `raw_ref`、`missing_raw()` の候補）と合うか。
- 外の原本を対象外にしたことで、守る木の規則に穴が開かないか（絶対パスの `raw:` が守る木の中を指す場合を含む）。
- ADR が「確かめた」と書く事実が、コードと合うか。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コード、設計書、レビューの記録は、次の主のチェックアウトの絶対パスで読む（読み取りだけ）。

- ADR（対象）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 1 回目のレビュー: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0013、0017、0019、0020、0023）
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- wiki のコード（v0.19.5、`2452f59`）: `C:/Works/info-hive-dev/info-hive-wiki/`（`commands/`、`skills/info-hive/scripts/`、`skills/info-hive/references/`）
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`

ファイルは変えない。
