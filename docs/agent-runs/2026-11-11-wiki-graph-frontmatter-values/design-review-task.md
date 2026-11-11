info-hive-wiki（Claude Code のプラグイン wiki。今は 0.9.3）の、グラフの抽出が frontmatter を lint と違う値に読む不具合を直す設計をレビューしてほしい。応答は日本語で書く。実装はまだない。設計の段階のレビューである。

設計書: `docs/plans/wiki-graph-frontmatter-values-2026-11-11.md`（このレビューの対象）。

設計の要点:
1. `wiki_graph_extract.parse_frontmatter()` は、最上位の欄を lint と同じ `wiki_text.parse_frontmatter_text()` と `canonical_meta()` で読み、`graph` の欄だけを PyYAML から取る。
2. `graph:` の中の、ページやノードを指す欄（`node_id`、`aliases`、`relationships[]` の `object`・`source`・`contradicts`・`supersedes`）で、PyYAML が真偽値、数、日付に読んだ値は、`yaml.BaseLoader` で読んだ「書かれた文字」に置き換える。`None` は値なしのまま。
3. lint の形に `graph` のキーがあるのに PyYAML から `graph` のマッピングを取れなかったページを、診断 `unreadable_graph` に挙げる。
4. オントロジーは PyYAML で読むままにする。
5. lint のパーサーが読まない YAML の書き方（字下げのない `- ` の配列など）は、グラフでも読まなくなる。これは受け入れ、パーサーを広げるのは別の課題にする。

読むとよいファイル（サブモジュール `info-hive-wiki` の中。現行の実装）:
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`（`parse_frontmatter`、`normalize_refs`、`build_nodes`、`build_edges`、`relationship_variant_key`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py`
- `info-hive-wiki/skills/info-hive/scripts/wiki_text.py`（`parse_frontmatter_text`、`canonical_meta`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（`parse_frontmatter_raw`、`collect_pages`、`missing_raw`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（`ref_values`、`classify_source_ref`）
- `info-hive-wiki/skills/info-hive/references/graph-workflow.md`、`references/page-conventions.md`

特に確かめてほしいこと:
- 2.1 の読み方で、lint とグラフの最上位の欄の値がまだ食い違う入力があるか。
- 2.2 の「BaseLoader で読んだ同じ位置の値に置き換える」が、誤った値に置き換える、止まる、または安全でない入力があるか（アンカー、マージキー、タグ、複雑なキー、同じキーの重複）。`None` を値なしのまま残す判断の反例。
- 2.3 の診断の条件に、挙げるべきなのに挙がらない、または誤って挙がる入力があるか。
- 3 の「規約どおりのページではノードもエッジも ID も変わらない」が崩れる入力があるか。
- 3 の後退（字下げのない配列を読まなくなる）を受け入れる判断と、2.4（オントロジーを変えない）の判断の弱点。
- 4 の試験で確かめられない性質。
- パッチの版（0.9.5）でよいか。

PyYAML 6.0.3 は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 ...` で使える。現行の関数を実行して確かめてよい（読み取り専用）。
