# 依頼: browse の左のペインを Fluent 2 の Tree にする設計（2 版目）の敵対的レビュー

## 対象

- `docs/plans/wiki-browse-tree-2026-11-16.md`（2 版目）

## 目的

1 版目への 1 回目のレビュー（`docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-design-review-1.md`）の指摘を直し、作者の決定で、見た目を Fluent 2 のサイト（fluent2.microsoft.design）の左のペインに合わせた（6 節）。サイトのアクセントの色は、Fluent の既定の brand のトークンに置き換えた。件数は Tree の aside に CounterBadge で置き、記事のページの「一覧」は Tree のクイックアクションにした。

2 版目が、1 回目の指摘を根本から直したか、新しく足した 6 節と 2.2〜2.4 の変更が新しい欠陥を生んでいないかを崩してほしい。

## 読むべきもの

- 1 回目のレビューと、その依頼: `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-design-review-1.md`、`tree-design-review-1-task.md`
- Tree、Nav の章: `.claude/skills/fluent2-html-replica/references/14-components-navigation.md`
- Badge と CounterBadge の章: `.claude/skills/fluent2-html-replica/references/12-components-choice.md`（Badge の節）
- 同梱の CSS: `info-hive-wiki/skills/info-hive/scripts/browse_assets/fluent2.css`（Tree の節は 11570 行付近、Badge と CounterBadge は 7500〜7730 行付近、トークンの light と dark の宣言）
- Tree の動きの参考: `.claude/skills/fluent2-html-replica/assets/fluent2.js` の `enhanceTree`
- 今の左のペイン: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`、`browse_assets/style.css`
- 元の設計: `docs/plans/wiki-browse-fluent2-2026-11-14.md`、`docs/plans/wiki-browse-findability-2026-11-13.md`、`docs/plans/wiki-browse-tag-groups-2026-11-16.md`

## 特に見てほしいこと

- 6.2 の状態の色の組と比が、同梱の `fluent2.css` の light と dark のトークンの値で正しいか。Tree の CSS の既定のホバーと押下（`colorSubtleBackgroundHover`、`colorNeutralForeground2Hover` ほか）を上書きするとき、上書きが漏れる状態（`:active`、フォーカス、選んだ項目へのホバー、シェブロン、バッジ、「一覧」）で 4.5:1 を割る組がないか。
- 6.3 の CounterBadge の属性（`data-appearance`、`data-color`、`data-size`、`data-shape`）が、同梱の CSS で設計のとおりに効くか。`aria-hidden` のバッジと `aria-label` の項目の組み合わせで、読み上げに件数が伝わるか。
- 2.4 の `focusin` によるローヴィングの同期で、「一覧」と枝の行き来、閉じた枝の中のフォーカス、検索の結果が木を隠したとき（`tree.hidden`）に、`tabindex="0"` が 0 個か 2 個になる場合がないか。
- 6.1 でペインの地をページと同じにすると、狭い幅の「メニュー」や、ペインの見出しの部分（スコープの札、配色の選択）、検索の結果の表示で崩れる所がないか。
- 2.3 の深さの上限（9 段）の数え方が、タグでまとめる設計の木の規則（N1〜N9）と合っているか。
- 1 回目の指摘（A の下線、B の Enter、C の 2 件）が、場当たりでなく、作りで直っているか。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。参照の実装や試作だけの欠陥で設計の文が正しいものは B、表現や試験の網羅の指摘は C とする。各指摘に分類を付ける。
