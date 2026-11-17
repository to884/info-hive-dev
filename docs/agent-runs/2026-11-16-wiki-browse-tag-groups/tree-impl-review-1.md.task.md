# 依頼: browse の左のペインを Fluent 2 の Tree にした実装の敵対的レビュー

## 対象

- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-impl-review-1.plugin.diff`（`info-hive-wiki/skills/info-hive/scripts/browse_assets/` の差分。`app.js` と `style.css`）
- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-impl-review-1.tests.diff`（`tests/wiki/browse/findability.test.mjs` の差分。同じブランチのタグでまとめる変更の試験も含む）
- 実装後のファイルそのもの: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`、`browse_assets/style.css`、`tests/wiki/browse/findability.test.mjs`

## 目的

設計 `docs/plans/wiki-browse-tree-2026-11-16.md`（3 版目。2 回の設計のレビューで条件付きで採用可）を実装した。実装が設計の約束（2.2 の項目の作り、2.3 の開閉と字下げ、2.4 のキーボードとローヴィング、6 節の見た目と色、6.3 のバッジ、6.4 のクイックアクション、1 節の守ること）を破る反例を探してほしい。

## 読むべきもの

- 設計と、2 回の設計のレビュー: `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-design-review-1.md`、`tree-design-review-2.md`
- 同梱の CSS: `info-hive-wiki/skills/info-hive/scripts/browse_assets/fluent2.css`（Tree の節は 11570 行付近、Badge と CounterBadge は 7500〜7730 行付近、NavDrawer と NavItem）
- Tree の動きの参考: `.claude/skills/fluent2-html-replica/assets/fluent2.js` の `enhanceTree`
- 元の設計: `docs/plans/wiki-browse-findability-2026-11-13.md`（3 節、4.3）、`docs/plans/wiki-browse-fluent2-2026-11-14.md`（1 節、4.2、4.3）

## 特に見てほしいこと

- `style.css` の上書き（ホバー、押下、今の項目、未解決の葉、aside をいつも出す規則、「一覧」の色）が、`fluent2.css` の規則に詳細度と順で確実に勝つか。勝たずに Fluent の既定の色が残り、4.5:1 を割る状態がないか（フォーカスだけの状態、今の項目にポインターを置いた状態、`:active` の間にポインターが外れた状態を含む）。
- `app.js` のローヴィング: `tabindex="0"` の項目がちょうど 1 つであり続けるか。枝を閉じたとき、検索の結果で木が隠れたとき、索引のページで `hashchange` が来たとき、`rovingToCurrent` を呼ぶ時機、「一覧」の `tabindex`。
- キーボードの操作: Enter が葉の移動を止めないか。修飾キーの扱い。先頭の文字での移動と、`/` の検索欄のキーとの競合。変換中のキー。
- 索引のページの枝の押す操作（名前は絞り込み、シェブロンは開閉）と、`location.hash` の書き換えが、絞り込みの既存の規則（4.3、`#group=` の読み方、「すべてのページ」）と食い違わないか。
- 試験（`treeChecks` ほか）が、実装の誤りで落ちる形になっているか。条件が常に真になる確かめや、試験の材料で起きない操作を確かめた気になっている所がないか。
- 画面の契約（`[style]` が 0 件、`app.js` が変えるのは class、`hidden`、`open`、`aria-*`、`tabindex` だけ）を破っていないか。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。試験だけの欠陥で実装が正しいものは B、表現や網羅の指摘は C とする。各指摘に分類を付ける。
