# 依頼: browse の左のペインを Fluent 2 の Tree にする設計の敵対的レビュー

## 対象

- `docs/plans/wiki-browse-tree-2026-11-16.md`（この設計。1 版目）

## 目的

`/wiki:browse` の左のペインの木（記事のページのサイドバーと、索引のページの左の木）を、Fluent 2 の Nav の部品の入れ子から、Fluent 2 の Tree の部品に置き換える。木のデータと中核は変えず、`app.js` と `style.css` だけを直す。作者は、Nav の規則（入れ子は 1 段まで、深い階層は Tree）に合わせるために Tree を選んだ。

設計が、Fluent 2 の Tree の部品と規則に忠実で、既存の約束（CSP、画面の契約、スクリプトなしの表示、コントラスト、キーボードだけで操作できること）を破らずに目的を満たすかを崩してほしい。

## 読むべきもの

- Tree と Nav の部品の章: `.claude/skills/fluent2-html-replica/references/14-components-navigation.md`（Nav と Tree の節）
- Tree の CSS: `info-hive-wiki/skills/info-hive/scripts/browse_assets/fluent2.css` の「Tree（TreeItem、TreeItemLayout）」の節（11570 行付近から）
- Tree の動きの参考: `.claude/skills/fluent2-html-replica/assets/fluent2.js` の `enhanceTree`（1330 行付近）
- 今の左のペイン: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`（「左の木」から、絞り込みの `hashchange` まで）、`browse_assets/style.css`（木の規則）
- 元の設計: `docs/plans/wiki-browse-fluent2-2026-11-14.md`（1 節、4 節、4.2、4.3）、`docs/plans/wiki-browse-findability-2026-11-13.md`（1 節、3.1、3.2、3.3、4.3）
- 一緒に出す設計: `docs/plans/wiki-browse-tag-groups-2026-11-16.md`

## 特に見てほしいこと

- `fluent2.css` の Tree の規則が、設計のマークアップ（葉を `a.fui-TreeItem`、`span.fui-TreeItemLayout` にすること、枝の中の `__actions` のリンク、`aria-level` の 11 段以上と `tree-deep`）で、設計の書いたとおりに効くか。セレクターがタグの名前や子の結合子に頼っていて効かない所はないか。
- ARIA の木として正しいか（`treeitem` のリンク、`aria-label` で件数を名前に含めること、`treeitem` の中の「一覧」のリンク、`aria-disabled` の葉、`aria-current` と treeitem の組み合わせ）。支援技術で読めない、または操作できない場合はないか。
- キーボードの操作（2.4）が、今できること（Tab で木のすべての項目に移れる、「一覧」に移れる、索引のページで絞れる）を失わせないか。ローヴィングの tabindex と「一覧」の tabindex の扱いに穴はないか。
- 索引のページの枝をリンクにしない判断と、押す場所で動きを分けること（名前は絞り込み、シェブロンは開閉）が、Fluent の Tree の使い方と矛盾しないか。
- 今の項目の見た目（2.3）が、コントラストと強制カラーの約束を満たすか。地を変える Tree のホバーと押下で、文字の色が 4.5:1 を割る組がないか。
- 狭い幅の「メニュー」、検索の結果を木の場所に出すこと、`scrollIntoView` との組み合わせで崩れる所はないか。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。参照の実装や試作だけの欠陥で設計の文が正しいものは B、表現や試験の網羅の指摘は C とする。各指摘に分類を付ける。
