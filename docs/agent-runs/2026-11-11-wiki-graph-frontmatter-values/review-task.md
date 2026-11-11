info-hive-wiki（Claude Code のプラグイン wiki）の、グラフの抽出が frontmatter を lint と違う値に読む不具合の修正（0.9.3 → 0.9.5）の実装をレビューしてほしい。応答は日本語で書く。

変更: サブモジュール `info-hive-wiki` のコミット a38c537（親は c50854a = main）。`git -C info-hive-wiki diff c50854a a38c537` で差分を読める。試験は開発リポジトリの `tests/wiki/test_graph_frontmatter_values.py`（未コミット）。設計は `docs/plans/wiki-graph-frontmatter-values-2026-11-11.md`（設計のレビュー `docs/agent-runs/2026-11-11-wiki-graph-frontmatter-values/design-review-1.md` を受けて改めた版）。

修正の意図:
1. `wiki_graph_extract.read_frontmatter()` は、最上位の欄を lint と同じ `wiki_text.parse_frontmatter_text()` と `canonical_meta()` で読み、`graph` の欄だけを PyYAML から取る。PyYAML には構文だけを読ませ、値に組み立てるのは `graph` のノードだけにする（`graph` の外の `created: 2026-13-01` などで止まらない）。
2. `graph:` の中の、ページやノードを指す欄（`node_id`、`aliases`、`relationships[]` の `object`・`source`・`contradicts`・`supersedes`）で、PyYAML が真偽値、数、日付に読んだ値は、同じノードを `BaseConstructor` で組み立てた「書かれた文字」に置き換える。`None` は値なしのまま。
3. `graph:` を読めなかったページを診断 `unreadable_graph`（`yaml_error`、`not_mapping`）に、lint のパーサーが読めない書き方の `type`・`kind`・`sources`・`raw` を診断 `unread_field` に挙げる。グラフの lint は `unreadable_graph` と `unread_fields` に挙げる。
4. オントロジーの `node_types[*].maps_from` の `type` と `kind` も、書かれた文字にそろえる。`read_ontology()` は `ValueError` も読めないものとして扱う。
5. `raw:` の配列は値ごとに `summarizes_raw` を作り、`tags:` の文字列は 1 つのタグにする。
6. 設計 3 の 2 つの条件を満たすページでは、書き出すノードとエッジが ID を含めて変わらない。

特に確かめてほしいこと:
- lint（`wiki_lint.collect_pages()` の meta）とグラフ（`wiki_graph_extract.collect_pages()` の meta から `graph` を除いたもの）が、`normalize_refs()` の差を除いて、まだ食い違う入力。
- `_read_graph()`、`_graph_refs_as_written()`、`_unread_fields()`、`_maps_from_as_written()` が、止まる、誤った値に置き換える、誤って診断する、挙げるべきなのに挙げない入力（アンカー、マージキー、タグ、同じキーの重複、再帰するアンカー、複数の文書、空の frontmatter）。`flatten_mapping()` と `construct_document()`、`BaseConstructor().construct_document()` を同じノードに使うことの副作用。
- 0.9.3 から変わらないはずの出力が変わる入力（設計 3 の条件を満たすページ）。
- ほかの呼び出し元への影響: `wiki_graph_lint.py`、`wiki_mcp_server.py`（ツール `lint` の `graph`）、`skills/info-hive/scripts/test_link_resolution.py`、開発リポジトリの `tests/graph/test_graph.py`、`tests/wiki/test_graph_duplicate_slugs.py`、`tests/wiki/test_page_set.py`。ページの辞書に `fm_problems` がない呼び出し（試験が手で作るページ）。
- `CHANGELOG.md` の 0.9.5 と `references/graph-workflow.md` の記述が、実装と食い違うところ。
- 試験が確かめていない性質。

通っている試験（Windows、Python 3.12、PyYAML 6.0.3）: `tests/wiki/test_graph_frontmatter_values.py`（41 件）、`tests/wiki/test_graph_duplicate_slugs.py`、`tests/wiki/test_page_set.py`、`tests/wiki/test_wiki_lint.py`、`tests/graph/test_graph.py`（28 件）、`info-hive-wiki/skills/info-hive/scripts/test_link_resolution.py`（113 件）、`info-hive-wiki/eval/scripts/`（81 件）、`info-hive-wiki/eval/decisions/`（43 件。`graph_lint_golden.json` は検出結果のキーが増えたので取り直した）。

実行するとき: `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_frontmatter_values.py -v`。関数を直接呼んで確かめてよい（読み取り専用）。
