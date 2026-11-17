# 依頼: browse の索引のページで種類とグループの絞り込みを重ねない設計の敵対的レビュー

## 対象

- `docs/plans/wiki-browse-filter-type-group-2026-11-17.md`（1 版目）

## 目的

Index のページで、左の木で選んだグループ（URL の断片 `#group=`）と、右の種類のボタン（`filt.type`）が重なって 0 件になる不具合を直す。作者の決定で、あとから選んだほうだけを効かせる。タグと検索語は重ねる。

## 読むべきもの

- 今の実装: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`（「索引のページの絞り込みと並べ替え」の節。`chip()`、`rowMatches()`、`apply()`、`fromHash()`、`all` と `groupChip` の押す処理、左の木の `selectGroup()`）
- 元の設計: `docs/plans/wiki-browse-findability-2026-11-13.md` の 4.3、`docs/plans/wiki-browse-tree-2026-11-16.md` の 9 節（記事のページの木からも `index.html#group=` で来る）

## 特に見てほしいこと

- 2 節の規則が、すべての入り口（左の木の葉と枝の押す操作と Enter、記事のページからの `index.html#group=`、ブラウザの戻ると進む、断片を手で書き換える、「すべてのページ」、グループの印の ×、最初の読み込み）で、0 件の重なりを残さず、選んだ値を思わず消さないか。
- 「グループが別の値に変わったときだけ種類を戻す」という条件で、戻らない場合や、戻りすぎる場合がないか。
- `history.replaceState` で断片を消すことで、ブラウザの履歴、`hashchange`、左の木の印、グループの印がずれないか。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。表現や試験の網羅の指摘は C とする。各指摘に分類を付ける。
