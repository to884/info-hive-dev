# 依頼: browse の木をタグでまとめる実装の敵対的レビュー

## 対象

- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/impl-review-1.plugin.diff`（プラグインの差分。`info-hive-wiki/` からの相対パス）
- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/impl-review-1.tests.diff`（開発リポジトリの試験と設計の差分）
- 実装後のファイルそのもの: `info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`、`tests/wiki/browse_nav/nav_model.py`、`tests/wiki/test_browse.py`、`tests/wiki/browse/findability.test.mjs`

## 目的

設計 `docs/plans/wiki-browse-tag-groups-2026-11-16.md`（2 版目）の規則 N9 を、中核の木の組み立てに実装した。設計は 1 回目の設計のレビュー（`design-review-1.md`）で採用可だった。実装が設計の約束（2.2 の規則、2.3 の ID、2.4 の性質、4 節の波及、1 節の守ること）を破る反例を探してほしい。

## 特に見てほしいこと

- 中核の `_nav_tag_stage` と参照の実装の `tag_stage` が、同じ規則を独立に書いているか。どちらかが同じ誤りを共有して、比べる試験が通ってしまう形になっていないか。
- `_check_tree` に足した形の検査が、正しい入力で誤って落ちる場合がないか（例: 1 つ目の段の ID が `_gt` で始まりうるか、`index.md` の「索引」のグループが `{**index_g}` で項目の list を共有することの影響）。
- `page_order`、`page_path`（`fx-path`、`group_path`）、`page_groups`（`data-groups`）、`index_summary`、`index_unresolved`、件数への波及が設計の 4 節のとおりか。
- 読めないページ、描けないページ、`drawn` にないページの項目で、`page_tags()` が例外を出す、または中身の違う値を返す場合がないか。
- 静的版とサーバーで同じ木になるか。
- 足した試験（Python と `findability.test.mjs`）が、実装の誤りで落ちる形になっているか。条件が常に真になる確かめがないか。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。試験や参照の実装だけの欠陥で中核が正しいものは B、表現や網羅の指摘は C とする。各指摘に分類を付ける。
