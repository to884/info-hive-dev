info-hive-wiki（Claude Code のプラグイン wiki）の、frontmatter の文字列のパーサー `wiki_text.parse_frontmatter_text()` が読む YAML の書き方を広げる設計をレビューしてほしい。応答は日本語で書く。設計の段階のレビューである。

設計書: `docs/plans/wiki-frontmatter-parser-2026-11-11.md`（このレビューの対象）。前提になる 0.9.5 の設計は `docs/plans/wiki-graph-frontmatter-values-2026-11-11.md` にある。

設計の要点:
1. 今は読まない 5 つの書き方（字下げが 2 つでないブロックの配列、複数行にまたがる `[...]`、引用符つきのキーとコロンの前の空白、二重引用符の中の `\"` と `\\` のほかのエスケープ、`|` と `>` のブロックのスカラー）を、すべて読む。
2. 値は、YAML が読む値と同じ文字列かその配列にする（型には直さない。比べる相手は PyYAML の `BaseLoader`）。YAML として誤りの書き方と、設計 2.7 の読まない書き方は、今までの読み方を変えない。
3. PyYAML には依存しない（lint と検索は標準ライブラリだけで動く）。
4. 行の読み方を 1 つの関数にまとめ、`parse_frontmatter_text()`、`top_level_keys()`、`unquoted_string_keys()` が使う。グラフの `_unread_fields()` の判定は変えない。
5. 検索のパースキャッシュの形式の番号を上げる。
6. 版は 0.9.6（パッチ）。

設計を確かめるための試作が、作業ツリーの `info-hive-wiki/skills/info-hive/scripts/wiki_text.py` に入っている（コミットしていない）。レビューの対象は設計だが、試作を実行して反例を探してよい。変更前（0.9.5）の実装は `git -C info-hive-wiki show 426d6bf:skills/info-hive/scripts/wiki_text.py` で読める。

読むとよいファイル:
- `info-hive-wiki/skills/info-hive/scripts/wiki_text.py`（試作。`_fm_entries`、`_fm_block_scalar`、`_fm_multiline_flow`、`_fm_unescape`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（`parse_frontmatter_raw`、`collect_pages`、`missing_raw`）、`wiki_search.py`（`collect_pages`、パースキャッシュ）、`wiki_stats.py`、`wiki_fetch.py`、`wiki_help.py`、`wiki_pages.py`（`ref_values`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`（`read_frontmatter`、`_read_graph`、`_unread_fields`）
- `info-hive-wiki/skills/info-hive/references/page-conventions.md`
- `tests/wiki/test_graph_frontmatter_values.py`、`tests/wiki/test_frontmatter_raw.py`、`info-hive-wiki/eval/scripts/test_frontmatter.py`

特に確かめてほしいこと:
- 2.1 の決まり（YAML として正しい 5 つの書き方は `BaseLoader` と同じ値）が崩れる入力。設計が「違ってよい」「読まない」と書いていない食い違いを探してほしい。
- 今のパーサーで読めているページ（規約どおりのページと、規約にないが今読めているページ）の値が、設計 3 の表にない形で変わる入力。特に 2.2（配列の形を次の行で決める）、2.3（閉じない `[` を、後ろの行の `]` まで読む）、2.4（キーの正規表現を広げる）。
- 2.5 のエスケープを YAML の意味で読む判断の弱点。今は書かれた文字で読めている値（`"C:\books\new.pdf"`、`"$\theta$"`）が黙って変わることを受け入れてよいか。採らなかった 3 つの案との比較が妥当か。サロゲートの扱い（対は 1 文字にまとめ、対にならないものは書かれた文字のまま）の反例。
- 2.6 のブロックのスカラーで、末尾の改行を YAML のとおりに付ける判断と、frontmatter の最後の行に改行があるものとして読む判断の弱点。改行を含む値が流れる先（lint、検索の出力、索引、グラフ、MCP）で止まる、または壊れる箇所。
- 制御文字（NUL を含む）やブロックのスカラーの値が、下流（`missing_raw` のパスの検査、JSON と GraphML の書き出し、SQLite、Tantivy）で例外になる箇所。
- 2.8 の `_unread_fields()` を変えない判断で、診断が誤って残る、または出るべきなのに出なくなる入力。
- 2.9 のほかに、古い値を持ち続けるキャッシュや索引があるか。
- 5 の試験で確かめられない性質。パッチの版（0.9.6）でよいか。

PyYAML 6.0.3 は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 ...` で使える。関数を実行して確かめてよい（読み取り専用）。
