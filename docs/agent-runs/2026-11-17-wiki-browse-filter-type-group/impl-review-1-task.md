# 依頼: browse の索引のページで種類とグループの絞り込みを重ねない実装の敵対的レビュー

## 対象

- `docs/agent-runs/2026-11-17-wiki-browse-filter-type-group/impl-review-1.plugin.diff`（`info-hive-wiki/` からの相対パス）
- `docs/agent-runs/2026-11-17-wiki-browse-filter-type-group/impl-review-1.tests.diff`
- 実装後のファイル: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`、`tests/wiki/browse/findability.test.mjs`

## 目的

設計 `docs/plans/wiki-browse-filter-type-group-2026-11-17.md`（2 版目、設計のレビューで採用可）を実装した。実装と試験が、設計の 2 節の規則と 3 節の試験、これまでの約束（画面の契約、`[style]` が 0 件、キーボードだけの操作、スクリプトなしで一覧が読める）を破る反例を探してほしい。

## 特に見てほしいこと

- `pressType()`、`chip()` の押す処理、`fromHash()` の条件が、2 節の表のすべての行のとおりに働くか。
- 試験が、実装の誤りで落ちる形になっているか（条件が常に真になる確かめ、材料で起きない操作）。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。試験だけの欠陥は B、表現や網羅の指摘は C とする。各指摘に分類を付ける。
