# wiki 0.12.2 の、title が値なしや配列のページで止まる件の修正の敵対的レビュー（2026-11-13）

wiki 0.12.1 の記録（`wiki/concepts/frontmatterのリストの値.md` の「残っている欠陥」）に、`title: [x, y]` と書くと検索が止まると残していた。作者の依頼で直した。調べると、`title:`（値なし。パーサーは空の配列を返す）と `title: [WIP]` でも、検索（CLI と MCP の索引）が全体で止まった。同じ原因で、lint の `--suggest-pages` とグラフの抽出も止まった。

wiki 0.12.2（to884/info-hive-wiki#51）で、新しい `wiki_pages.text_value()` に `title` を通すようにした。文字はそのまま使い、配列は空でない要素を「, 」でつなぐ。配列の扱い（つなぐか、題名なしとみなすか）は、作者が「要素をつなぐ」を選んだ。GPT-6.1 Sol（effort high、`ask-codex` の `review`）に 1 回レビューしてもらった。

- 依頼: `review-sol.md.task.md`。対象は次のとおり。
  - 差分 `reviewed.diff`（`info-hive-wiki` の 7 つのスクリプト、CHANGELOG、`plugin.json`、`docs/search.md`）。
  - `--target` で渡した 2 つの試験（`info-hive-wiki/eval/scripts/test_title_values.py` と、親の `tests/wiki/test_wiki_index.py`）。新しいファイルなので、差分には入っていない。
  - `references/graph-workflow.md` の 1 文は、レビューのあとに足したので、レビューの対象に入っていない。
- 結果: `review-sol.md`（条件付きで採用可、確信度 中）
- レビュアーは、評価のコーパスの 170 通りの検索の出力を、修正の前後の検索の関数で比べ、差がないことを確かめた。パースキャッシュから読んだ文字でない 12 通りの値でも、検索が止まらず、題名が文字になることを確かめた。PyYAML などの依存がない環境だったので、グラフと MCP の試験は流していない

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| `list_index` は、題名が空で見出しもない索引のファイルで、`title` に `null` を返す。CHANGELOG の「`list_index` の題名も文字にする」に反する | 軽微（修正の前から） | `title: ""` で見出しのないファイルも前から `null` だったので、振る舞いは変えなかった。CHANGELOG を「配列なら同じ規則でつなぐ。題名も見出しもないファイルは、今までどおり `null` を返す」に直した |
| グラフの lint の試験が `--decide` を付けず、題名を集める判定の経路を通らない。`Traceback` がないことしか見ない | 軽微 | `--decide` の有無の 2 通りで動かし、終了コードが 0 で、`--json` の出力が読めることを確かめるようにした |
| 検索の `--decide` の試験は、判定のバックエンドを止めた fail open の経路しか通らない | 軽微 | 同梱の偽のバックエンド（`eval/decisions/fake_backend.py`、127.0.0.1）で判定が成功する経路を通す `test_decide_sends_text_titles` を足した。判定モデルに渡る題名が、どの行も文字で、期待どおりであることを確かめる |
| MCP の `get_page` の `meta.title` は配列のまま返る | 崩れる前提（欠陥とはしない） | frontmatter をそのまま返すツールなので変えなかった |

上の直しは、レビューのあとに入れた。レビューにはかけ直していない。

## 確かめたこと

- 足した試験（プラグインの 12 件、親の索引の 1 件）は、修正前の実装でどれも失敗し、修正後はどれも通った。
- Windows 11 の Python 3.12 で、プラグインの `eval/scripts`（106 件）、`eval/retrieval`（45 件）、`test_link_resolution.py`（113 件）、`eval/evolution`、`eval/decisions`（43 件）、`eval/check_encoding.py` が通った。親の `tests/wiki` のグラフ（87 件）、browse（77 件）、索引（19 件）、MCP サーバー（28 件）、frontmatter、page_set、lint、走査、Python の版、テンプレートのパスの試験も通った。
- 評価ゲート（`run_eval.py --gate --baseline` と `--set ja`）の出力と、全クエリの `--json` の出力が、修正の前後でバイト単位で同じだった。

## 直していないこと

- 閲覧（`wiki_browse_core.py`）は、配列の `title` を `['x', 'y']` と表示する。別のブランチで browse を大きく変えている途中なので触らず、`text_value()` を使うよう、セッションの共有メモで伝えた。
- `type` と `updated` を配列で書くと、`--json` に配列のまま出る（止まりはしない）。
