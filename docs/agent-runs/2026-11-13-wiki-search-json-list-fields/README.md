# wiki 0.12.1 の検索の結果の tags と sources の修正の敵対的レビュー（2026-11-13）

browse の画面の改修（`docs/plans/wiki-browse-ui-2026-11-13.md`）で、埋め込みの検索の結果を `wiki_search.py --json` の結果と同じ型にそろえる契約（`tests/wiki/browse/search_result_contract.json`）を作ったとき、`wiki_search.py` 自身が契約から外れていることが分かった。frontmatter に `tags: 検索` のように値を 1 つだけ書くと、`json_result()` が `tags` を配列でなく文字のまま返していた（`sources` も同じ）。

wiki 0.12.1（to884/info-hive-wiki#50）で、`json_result()` の `tags` と `sources` を、lint が `sources` を読むのと同じ `wiki_pages.ref_values()` で作るようにした。MCP の `query` も同じ関数で結果を作るので、同じく直る。GPT-6.1 Sol（effort high、`ask-codex` の `review`）に 1 回レビューしてもらった。

- 依頼: `review-sol.md.task.md`。対象は差分 `reviewed.diff`（`info-hive-wiki` の `wiki_search.py`、試験、`docs/search.md`、CHANGELOG、`plugin.json`）
- 結果: `review-sol.md`（採用可、確信度 高）
- レビュアーは、`ref_values()` に文字、空、数、真偽値、辞書、入れ子の配列を渡し、どれも文字の配列を返すことを確かめた。修正前の式に戻すと、足した試験が失敗することも確かめた。評価のコーパスの 170 通りの `--json` の出力が、修正の前後で同じことも確かめ直した。`WikiIndex.search()` は、索引を代わりの実装に差し替えて呼んだ

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| CHANGELOG の「規約どおりに配列で書いたページの結果は変わらない」は広すぎる。`tags: [" x "]` は `[" x "]` から `["x"]` に変わる。ページの規約は、引用符の中の前後の空白を禁じていない | 軽微 | 「配列で書いていて、要素が空でなく、引用符の中に前後の空白もないページの結果は変わらない」に直した |
| 足した試験は、`--decide`、`WikiIndex.search()`、MCP の `query` を呼ばない。共通の関数を使わなくなっても気づけない | 軽微 | `JsonListFieldsContractTest.test_decide`（判定のバックエンドを止めて、どの行も残す）と、`tests/wiki/test_wiki_index.py` の `test_search_list_fields_are_string_arrays`（語彙とハイブリッドの検索）を足した。どちらも修正前の実装で失敗することを確かめた |
| パースキャッシュの `tags` が文字でない値（`5` など）のとき、`--tag` で絞り込むと `normalize_tags()` が `TypeError` を出す | 崩れる前提（修正の前から） | パーサーは文字しか返さず、キャッシュを手で書き換えたときだけ起きる。別の欠陥として残した |

上の 2 つの直しは、レビューのあとに入れた。レビューにはかけ直していない。

## 確かめたこと

- Windows 11 の Python 3.12 で、`eval/retrieval`（依存つき）、`eval/scripts`、`test_link_resolution.py`、`eval/decisions/test_decisions.py`、`eval/check_encoding.py` と、`tests/wiki` の frontmatter、page_set、lint、テンプレートのパス、索引、MCP サーバーの試験が通った。
- 評価ゲート（`run_eval.py --gate --baseline` と `--set ja --gate --baseline`）の出力が、修正の前後で同じだった。

## 見つけたが直していないこと

- frontmatter に `title: [x, y]` と書くと、`wiki_search.collect_pages()` の `body + " " + meta.get("title", "")` が `TypeError` を出し、検索が止まる（CLI と MCP の索引の両方）。
- `type` と `updated` を配列で書くと、`--json` に配列のまま出て、契約（文字か `null`）から外れる。
- MCP の `get_page` の `meta` は frontmatter をそのまま返すので、`tags` は文字のままである。ツールの説明は、キーの別名をそろえることしか約束していない。
- 値が 1 つの文字を配列にする規則が、`wiki_pages.ref_values()` のほかに、`wiki_text.normalize_tags()`（NFKC をかけ、`""` を `[""]` にする）と `wiki_graph_extract._tag_list()` にもある。
