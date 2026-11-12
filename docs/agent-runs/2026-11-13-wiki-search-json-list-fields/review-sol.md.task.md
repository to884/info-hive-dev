# レビューの目的

`info-hive-wiki`（Claude Code プラグイン `wiki`）の検索スクリプト `skills/info-hive/scripts/wiki_search.py` の `json_result()` を直した差分である。

## 直したい欠陥

`--json` の結果（と、同じ関数で結果を作る MCP のツール `query`、`skills/info-hive/scripts/wiki_index.py` の `WikiIndex.search`）の `tags` と `sources` は、契約では「文字の配列」である。修正前は `meta.get("tags", []) or []` だったので、frontmatter に `tags: 検索` や `sources: paper` のように値を 1 つだけ書くと、文字のまま返していた。

## 完了の条件

- `wiki_search.py --json` の `tags` と `sources` が、どの経路（section と page の粒度、`--decide`、パースキャッシュ `--cache` から読んだ meta、MCP の `query`）でも、いつも文字の配列になる。
- 規則を二重に持たない。既存の `wiki_pages.ref_values()`（lint が `sources` を読むのに使う）を使った。
- 規約どおりに配列で書いたページの結果は変えない。評価ゲート（`python eval/retrieval/run_eval.py --gate --baseline` と `--set ja`）の出力は、修正の前後で同じだった。評価のコーパスの全クエリの `--json` の出力もバイト単位で同じだった。

## 読むとよいファイル

- `skills/info-hive/scripts/wiki_search.py`（`json_result()`、`collect_pages()`、`load_parse_cache()`、`passes_filters()`）
- `skills/info-hive/scripts/wiki_pages.py` の `ref_values()`
- `skills/info-hive/scripts/wiki_text.py` の `parse_frontmatter_text()`、`canonical_meta()`、`normalize_tags()`
- `skills/info-hive/scripts/wiki_index.py` の `WikiIndex.search()`
- `eval/retrieval/test_search_contracts.py` の `JsonListFieldsContractTest`（新しい試験）
- `CHANGELOG.md` の 0.12.1 の節、`docs/search.md` の結果の欄の表

## とくに崩してほしい点

- `ref_values()` が文字の配列を返さない入力、または期待と違う値を返す入力（パーサーが返しうる値と、パースキャッシュの JSON に入りうる値）。
- 試験が欠陥を捕まえられない書き方になっていないか（修正前の実装で失敗することは確かめた）。
- 今回の変更で、ほかの利用者（`--tag` の絞り込み、browse、rag、MCP のほかのツール）の挙動が変わるところ。
- CHANGELOG と `docs/search.md` の記述が、実装と食い違っていないか。版 0.12.1（パッチ）が妥当か。

範囲の外として承知していること（指摘は不要）: `title: [x]` で `collect_pages()` が `TypeError` で落ちること、`type` と `updated` を配列で書くと配列のまま出ること、MCP の `get_page` の `meta` が frontmatter をそのまま返すこと。これらは別の作業として報告する。
