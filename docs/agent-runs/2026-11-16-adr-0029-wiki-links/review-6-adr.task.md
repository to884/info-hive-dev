# 依頼：ADR-0029（11 版目）の敵対的レビュー（決定の整合）

対象は `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md` の 11 版目である。応答は日本語で書く。ファイルは変えない。

## 前回からの変化

10 版目までは実装の詳細を ADR に書いていた。5 回のレビュー（どれも却下）と総括（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/summary.md`）を受けて、作者は ADR を決定と不変条件（I1〜I7）だけに絞り、実装の詳細を設計書（`docs/plans/wiki-links-2026-11-16.md`）に移すと決めた（作者の決定の 9）。設計書は別にレビューする。

## このレビューで見ること

ADR の水準の欠陥だけを探す。関数の名前、欄、行番号、試験の一覧は、設計書の側で見るので、ここでは対象外とする。

- 作者の決定（1〜9）と、用語、不変条件（I1〜I7）が、互いに食い違っていないか。不変条件どうしを同時に満たせない配置や操作がないか。
- 不変条件が、作者の決定の意図を、狭めすぎたり広げすぎたりしていないか。
- 不変条件のもとで、規則の目的（記事の名前が木の外の実体を指さないこと、記事を通して別の場所を書き換えないこと、拒んだことが黙って消えないこと）を破る配置が残っていないか。
- ほかの ADR（0008、0010、0013、0017、0019、0020、0023）との関係の記述が正しく、承認したときに食い違いが残らないか。
- 「保証しないこと」と「見直す条件」が、不変条件の外に出したものと合っているか。

作者の決定そのものは崩す対象ではない。1〜5 回目のレビューと同じ指摘の繰り返しは除く。

## 読むファイル

- ADR: 上のパス
- 総括とレビューの記録: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`
- 設計書（参考。ADR の記述の裏づけを確かめるときだけ）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md`
- コード（必要なときだけ）: `C:/Works/info-hive-dev/info-hive-wiki/`（指定の版は `git show 2452f59:<パス>`）、`C:/Works/info-hive-dev/info-hive-rag/scripts/`
