# 依頼：ADR-0029 の実装の設計（5 版目）の敵対的レビュー

対象は `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md` の 5 版目である。応答は日本語で書く。ファイルは変えない。

## 位置づけ

ADR-0029（`docs/adr/0029-wiki-and-raw-hold-no-links.md`、11 版目）は、決定と不変条件（I1〜I7）だけを持つ。本設計書は、それを関数、欄、手順、試験に落とす。ADR の 10 版目までの本文から実装の詳細を移し、新しく「依存の完全性」と「`raw:` の解き方」の節を足した。そのあと、親のセッションの指摘（記事を名前の規則で決めること、`is_link()` と `find_links()` の使い分け、書けなかったときの振る舞い、守る木の中かの比べ方）を入れた。

## 前回のレビュー

前回のレビュー（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-9-design.md`、却下）の指摘を直した。`raw:` の解き方は、利用者が書いたままの根の綴りと解決した根の両方を受け取り、両方から候補を作り、別の実体なら曖昧にする形にした。確かめられない候補があれば `unknown` にした。書き込みの部品に、ライブラリに渡す前に道と行き先とその付随ファイルを確かめるだけの操作を置いた。ADR-0029（15 版目）は、8 回目のレビューで採用可（確信度：中）だった。直し方が原因を閉じているかも確かめ、前回までと同じ指摘の繰り返しは除く。

## このレビューで見ること

- 設計が、ADR の不変条件 I1〜I7 を満たすか。どれかを破る配置や操作の順がないか（冒頭の対応表から節をたどる）。
- 設計が、今のコード（wiki `2452f59`、rag `c59d05e`）と、書く段の設計（`docs/plans/wiki-apply-2026-11-14.md`）に対して成り立つか。書いてある行番号と振る舞いが合うか。
- 名前の規則で決める記事、走査の `Walk.links`、記事を読む口、`resolve_raw()`、依存の完全性、書き込みの部品の契約が、互いに食い違っていないか。届かない読み手や書き手、黙って「ない」になる経路が残っていないか。
- 試験の一覧で、設計の要の振る舞いが確かめられるか。

ADR-0029 の 1〜5 回目のレビューと、修正案の依頼（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`〜`review-5.md`、`proposal-1.md`）と同じ指摘の繰り返しは除く。作者の決定（ADR の 1〜9）は崩す対象ではない。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コードは主のチェックアウトで読む。wiki の指定の版は `git show 2452f59:<パス>`（`C:/Works/info-hive-dev/info-hive-wiki`）で照らす。

- 設計書: 上のパス
- ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 記録: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/`
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`
- コード: `C:/Works/info-hive-dev/info-hive-wiki/`、`C:/Works/info-hive-dev/info-hive-rag/scripts/`
