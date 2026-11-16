# 依頼: browse の木をタグでまとめる設計の敵対的レビュー

## 対象

- `docs/plans/wiki-browse-tag-groups-2026-11-16.md`（この設計。1 版目）

## 目的

`/wiki:browse` のナビゲーションの木で、索引の見出しのグループの直下にあるページを、ページの最初のタグの値ごとのグループ（タグのないページは「タグなし」）にまとめる。規則は、既存の木の規則 N1〜N8 のあとに 3 つ目の段 N9 として足し、N8（件数）は N9 のあとに数える。作者は、いつも段を挟むこと、タグのグループは索引に現れた順、「タグなし」は最後、と決めた。

設計が、既存の契約を破らずに、この目的を満たすかを崩してほしい。

## 読むべきもの

- 元の設計: `docs/plans/wiki-browse-findability-2026-11-13.md`（2 節の N1〜N8、2.2 のグループの ID、2.3 の `nav.js`、4.1 の索引のページの骨組み、4.3 の絞り込み）
- 実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`（`_nav`、`_nav_stage_two`、`_page_listing`、`_check_tree`、`page_tags`、`GROUP_ID_RE`、search.js の書き出し）
- 画面: `info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js`（木の描画、`#group=` の読み方、今のページの探し方）
- frontmatter の読み方: `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py` の `ref_values`
- 参照の実装と試験: `tests/wiki/browse_nav/nav_model.py`、`tests/wiki/test_browse.py` の `NavTreeTest`
- Fluent 2 の設計: `docs/plans/wiki-browse-fluent2-2026-11-14.md`（4.3 の折り返し、木の字下げ）

## 特に見てほしいこと

- N9 のあと、探しやすさの設計 2.1 の末尾の 5 つの性質と、この設計 2.4 の 3 つの性質が、正しい使い方のすべての入力で同時に成り立つか。反例があれば具体的な索引とページで示す。
- ID の作り方（`_gt` と通し番号）が、既存の ID と作りの上で重ならないか。`GROUP_ID_RE`、`data-groups`、`#group=` の読み方と矛盾しないか。
- 2.5 の当てはめの例が、2.2 の規則を最後まで当てた結果と一致するか（手で書いた表なので、誤りがありうる）。
- N4、N6、N7 との相互作用（N9 が N6 の外し方より後に来ることで、指せないグループや 0 件のグループが生まれないか）。
- 索引の順、`fx-path`、`data-groups`、4.4、要約、件数への波及の書き漏れ。
- `nav.js` の `protocol_version` を 2 のままにする判断が正しいか。
- 画面（`app.js`）を変えずに済むという前提が崩れないか（今のページの探し方、グループを開く規則、索引のページの左の木）。

## 止める条件

失敗も競合も入れない正しい使い方で、設計の約束を破る反例を分類 A とする。参照の実装や試作だけの欠陥で設計の文が正しいものは B、表現や試験の網羅の指摘は C とする。各指摘に分類を付ける。
