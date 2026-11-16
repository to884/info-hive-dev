## 判定

**採用可。確信度：高。** N9 の規則そのものについて、分類 A の反例は崩せなかった。ただし、2.5 の例には既存の N3・N4 と食い違う木があり、検索データのフィールド名にも誤記がある。いずれも分類 C。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **単独の見出しが、その名前と親子関係を保って残るという前提。** `index.md` のファイルグループが項目を持たず、子を一つだけ持つ場合、N3 がその子を畳む。その後、N4 が項目と子グループを分けて最上位に置く。2.5 の複数の例は、この処理を反映していない。
- **2.5 のすべての例が、記載された入力だけで再現できるという前提。** 最後の三例はページのタグだけを示し、結果にある `G` を作る索引を示していない。記載されたファイルだけなら N7 の「索引にないページ」に入り、提示された木にはならない。

## 見落としと軽微な問題

1. **［分類 C・軽微］2.5 の四例が、規則を最後まで当てた結果と一致しない。**

   - 「基本」の最上位は `コンセプト（4）` ではなく **`索引（4）`**。
   - 「タグを持つページがない」は `ソース（1）` ではなく **`索引（1）`**。
   - 「同じグループに同じページが 2 回」は `G（1）` ではなく **`索引（1）`**。
   - 「項目と見出しの子」は名前だけでなく、階層と件数も異なる。規則どおりの結果は次になる。

   ```text
   索引（1）: ?nope（unresolved）
     x（1）: a
   節（1）
     y（1）: b
   ```

   `章（2）` は残らず、`節` は最上位になる。したがって `b` の `fx-path` も、表が示唆する `章 › 節 › y` にはならない。

   **根拠：** [対象設計の2.5](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/docs/plans/wiki-browse-tag-groups-2026-11-16.md:86)、[既存設計のN3・N4](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/docs/plans/wiki-browse-findability-2026-11-13.md:112)、[実装の畳み込み処理](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:965)。既存 `Core` に同じ索引を与え、N9 より前の状態でも食い違うことを確認した。N9 自体の欠陥ではない。

2. **［分類 C・軽微］検索データの `path` と `group_path` を取り違えている。**

   4 節は、タグの階層が付く先を「`data/search.js` の `path`」としている。しかし `path` は `concepts/a.html` のようなリンク先であり、階層は **`group_path`** に格納される。135 行目の試験変更対象にも同じ取り違えがある。

   **根拠：** [対象設計の階層の説明](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/docs/plans/wiki-browse-tag-groups-2026-11-16.md:116)、[検索データの実装](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1478)。既存設計・実装とも、フィールドの区別は一致している。

## 検証した事実

- **ID：一致。** 既存の生成形式は `_g<数字>` と `_gf<数字>`。追加する `_gt<数字>` は衝突せず、`GROUP_ID_RE` と JavaScript の `GROUP_ID` にも適合する。空白区切りの `data-groups` と `#group=` の読み取りにも矛盾しない。
- **画面の再帰処理：一致。** `containsCurrent()` は子孫を探索し、`treeGroup()` は各グループで判定するため、複数箇所に載るページについてもタググループと祖先を開ける。`indexTree()` も深さに依存せず子を描く。[app.js](/C:/Works/info-hive-dev/.claude/worktrees/browse-tag-groups/info-hive-wiki/skills/info-hive/scripts/browse_assets/app.js:348)
- **タグの読み方：一致。** `page_tags()` は `ref_values()` の結果を NFC にする。文字列、配列、空要素の説明は実装と一致する。
- **参照実装・試験：確認済み。** 現在は N9 未実装。上記の実行確認は、既存 `Core` と、レビュー用にメモリー上で規則を適用した結果であり、実装済み N9 の試験結果ではない。
- **折り返し：コード上は一致。** 既存 CSS はグループ名の折り返しと深い段の字下げ停止を扱う。追加したタググループの実ブラウザー表示は未確認。

## 崩せなかった点

- 既存の五つの性質と、追加する三つの性質の同時成立。
- N9 が N6 の後に来ることで、指せないグループや新しい 0 件のタググループが生まれるという反例。対象には解決済み項目が必須であり、既存グループの ID も消さない。
- 同じページの重複掲載・複数アンカーによる件数の破綻。N8 はページ ID の集合で数える。
- 要約の選択順の破綻。同じページの出現順は維持され、移動後のタググループも既存の子グループより前に置かれる。
- `protocol_version: 2` の継続による読み取りの破綻。既存 `app.js` はグループの出自を判定せず、既存と同じ形の入れ子を処理する。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
