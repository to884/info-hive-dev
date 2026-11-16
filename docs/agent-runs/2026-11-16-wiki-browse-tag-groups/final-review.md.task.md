# 依頼: browse のタグの段と左のペインの Tree の、リリース前の最終の敵対的レビュー

## 対象

- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/final-review.plugin.diff`（`info-hive-wiki` の差分の全体。`info-hive-wiki/` からの相対パス）
- `docs/agent-runs/2026-11-16-wiki-browse-tag-groups/final-review.tests.diff`（開発リポジトリの試験と設計の差分。新しいファイルは含まない）
- 実装後のファイルそのもの: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`、`browse_assets/style.css`、`info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`tests/wiki/browse/findability.test.mjs`、`tests/wiki/browse_nav/nav_model.py`
- 設計: `docs/plans/wiki-browse-tag-groups-2026-11-16.md`、`docs/plans/wiki-browse-tree-2026-11-16.md`（特に 2.3、6 節、7 節、8 節、9 節）

## 目的

この 2 つの設計を同じ版で出す。前回の実装のレビュー（`docs/agent-runs/2026-11-16-wiki-browse-tag-groups/tree-impl-review-1.md`）のあと、作者が画面を見て次を決め、実装した。直したあとの版は、まだレビューを受けていない。

1. 件数のバッジを名前のすぐ隣に置いた（6.3）。字下げを Fluent 2 のサイトの形（1 段目と 2 段目の名前がそろい、3 段目から 1 段 18px）にした（2.3）。バッジを tint にし、地を `colorNeutralBackground6` にした。
2. 配色の切り替えを、選択から「テーマ」のトグル（Fluent 2 のサイトの形。オンでダーク、OS と同じ見た目に戻すと auto を保存）にした（7 節）。
3. 画面に出る「索引」を「Index」にした（8 節）。
4. 記事のページの左の木も、Index のページと同じくグループの名前と件数だけにし、記事の題名と「一覧」のクイックアクションをなくした（9 節）。

実装と試験が、設計の約束と、これまでの約束（CSP と画面の契約、スクリプトなし、コントラスト 4.5:1、キーボードだけの操作、ローヴィングの `tabindex="0"` が 1 つ、静的版とサーバーで同じ画面）を破る反例を探してほしい。

## 特に見てほしいこと

- トグル: `theme.js` の保存と読み出し、`prefers-color-scheme` の変化、保存できないとき、`file://` と http の両方で、7 節の規則（OS と同じ見た目なら auto を保存）が崩れる場合がないか。入力を枠の上に重ねる作りで、押せない、フォーカスの輪が見えない、読み上げの名前が見えるラベルを含まない、強制カラーで見えない、という場合がないか。
- 9 節: 記事のページで、今のページを持つグループが葉でなく枝になる場合（見出しのグループがタグのグループを持たずにページを持つことはないか。N9 のあとはタグのグループだけがページを持つ）、今のページがどのグループにもない場合（索引の外のページ、読めない索引）、2 つのグループに載る場合に、印、開く枝、Tab の入口が崩れないか。
- 記事のページで枝の名前と Enter が `location.href` で移るとき、静的版（`file://`）とサーバーで、`groupHref` の行き先が正しいか（`href()` と `root` の扱い）。
- 「Index」への改名の漏れ（画面に「索引」が残る所）と、検索の索引の文言を誤って替えた所がないか。
- 試験が、実装の誤りで落ちる形になっているか（条件が常に真になる確かめ、材料で起きない操作）。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。試験だけの欠陥で実装が正しいものは B、表現や網羅の指摘は C とする。各指摘に分類を付ける。
