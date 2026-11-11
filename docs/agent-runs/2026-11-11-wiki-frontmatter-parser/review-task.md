設計のレビュー（`docs/agent-runs/2026-11-11-wiki-frontmatter-parser/design-review-1.md`、却下）の続きである。指摘を受けて設計を改め、実装した。実装をレビューしてほしい。応答は日本語で書く。

対象:
- `info-hive-wiki` のコミット 26d8c8e（`git -C info-hive-wiki show 26d8c8e`。親は 0.9.5 の 426d6bf）。中心は `skills/info-hive/scripts/wiki_text.py` の `_fm_entries()`、`_fm_multiline_flow()`、`_fm_flow_line()`、`_fm_block_scalar()`、`_fm_unescape()`、`_fm_unquote()` と、`wiki_graph_extract.py` の `_xml_text()`、`wiki_search.py` の `PARSE_CACHE_SCHEMA` である。
- 改めた設計: `docs/plans/wiki-frontmatter-parser-2026-11-11.md`。指摘と対応の対応表は `docs/agent-runs/2026-11-11-wiki-frontmatter-parser/README.md` にある。
- 開発リポジトリの試験（コミットしていない作業ツリー）: `tests/wiki/test_frontmatter_parser.py`（新規）、`tests/wiki/frontmatter_parser_golden.json`（0.9.5 のパーサーの出力）、`tests/wiki/test_graph_frontmatter_values.py` と `tests/wiki/test_frontmatter_raw.py`（期待値を変えた）。

設計が約束していること（2.1 の 3 つの決まり）:
1. YAML として正しい書き方のうち、設計 2.2 から 2.6 のものは、`yaml.load(fm_text + "\n", Loader=yaml.BaseLoader)` と同じ文字列かその配列になる。設計 2.1 の表の箇所と、2.7 の読まない書き方は除く。
2. 0.9.5 がキーの行として読んでいた行は、今も同じキーの行として読む（0.9.5 が読んでいた欄を、欄ごと失わない）。
3. 0.9.5 と値が変わるのは、設計 3 の表の書き方だけである。

前回の指摘への対応:
- 致命 1: 複数行の `[...]` は、閉じる前に字下げのないキーの行（`_FM_KEY_RE` に当たる行）が来たら、読むのをやめて今までどおり読む。エスケープは、値の中に戻せないものが 1 つでもあれば、値の全体を 0.9.5 までと同じに読む。
- 重大 2: 複数行の `[...]` のコメントは、`,`・`[`・`]`・`{`・`}` と閉じた引用符の直後の `#` も認める。
- 重大 3: GraphML に書く文字列で、XML に書けない文字を U+FFFD に置き換える。
- 重大 4: Unicode の空白を除くことと、LF だけで行を分けることは、0.9.5 までの読み方として残し、設計 2.1 の表に書いた。

特に確かめてほしいこと:
- 3 つの決まりを破る入力。特に 2（0.9.5 が読んだ欄を失う入力）と 3（設計 3 の表にない値の変化）。0.9.5 の実装は `git -C info-hive-wiki show 426d6bf:skills/info-hive/scripts/wiki_text.py` で読める。
- 前回の反例が、どれも再現しなくなっているか。対応が別の後退を作っていないか（キーの行で止めることで読めなくなる正しい YAML が、設計 2.3 と 2.7 に書いたもののほかにあるか）。
- `_fm_block_scalar()` と `_fm_unescape()` が、`BaseLoader` と違う値を返す正しい YAML（設計が違ってよいと書いていないもの）。
- `top_level_keys()` と `unquoted_string_keys()` が、値の辞書と違う行を見る入力。グラフの `_unread_fields()` が、読めるようになった書き方で診断を誤って残す、または 0.9.5 で出ていた診断が、読めていないのに出なくなる入力。
- `_xml_text()` の置き換えで、GraphML がまだ読めない XML になる入力。ID を置き換えることで起きる問題。
- 試験が確かめていない性質。試験の期待値が、実装の出力を写しただけで、設計の値と違う箇所。
- CHANGELOG（`info-hive-wiki/CHANGELOG.md` の 0.9.6）の記述が、実装と違う箇所。

PyYAML 6.0.3 は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 ...` で使える。関数を実行して確かめてよい（読み取り専用）。試験は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_frontmatter_parser.py -v` で動く。
