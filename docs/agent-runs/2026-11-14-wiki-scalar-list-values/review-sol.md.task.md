# レビューの目的

info-hive-wiki（Claude Code プラグイン `wiki`。日本語の Markdown の wiki を作り、検索、lint、統計、グラフを提供する）の修正を壊してほしい。

## 修正が果たすべきこと

frontmatter のパーサー（`wiki_pages.py` などが使う、PyYAML を使わない自前のパーサー）は、値を書かれた形のまま返す。1 つの値を入れる欄でも、`type: [concept]` は配列、値なしの `type:` は空の配列になる。修正前は次のようになっていた。

- 検索の `--json` と MCP の `query` の結果で、`type` と `updated` が配列のまま出た。人が読む出力の type の欄にも `['concept']` や `[]` と出た。
- `--type concept` が `type: [concept]` のページを外し、`--since` が `updated: [2026-03-01]` のページを外した。
- 統計が `type: [concept]` のページを種類なしと数えた。
- lint とグラフが `type: [source]` のページを source として読まなかった。
- グラフの抽出が、配列の `type` と `kind` を sqlite に渡して止まった。

修正は `wiki_pages.scalar_value()`、`type_value()`、`kind_value()` を足し、`type`、`kind`、`updated`、`created` を読む箇所をそろえる。

- 文字と None は、そのまま返す（`""` も変えない。文字の結果を変えない）。
- 配列は、空でない要素を「, 」でつなぐ（0.12.2 で `title` に入れた `text_value()` と同じ規則）。`type` と `kind` の要素は、日本語の別名を英語に直す。空なら None。
- lint の指摘（`non_iso_dates` の `value` など）は、書かれた形のまま出す。
- 閲覧（`/wiki:browse`、`wiki_browse_core.py`）は、意図して直していない。

## 見てほしいこと

- `type`、`kind`、`updated`、`created` を、まだ生の値で読んでいて、同じ取り違えや例外が残る箇所。MCP のサーバー、索引（`wiki_index.py`）、`wiki_decide.py`、グラフの extract と lint、統計、lint を含む。
- 文字の値の結果が、修正の前後で変わってしまう場合。
- 日本語の別名の扱い（文字の `type` は読み込みの `canonical_meta()` で直してあるという前提）が崩れる場合。
- 配列の要素が文字でない（数、日付、真偽値、入れ子）場合の扱い。
- 規則の文書（`CHANGELOG.md` の `[Unreleased]`、`docs/search.md`、`skills/info-hive/references/graph-workflow.md`）と実装の食い違い。
- 試験（`eval/scripts/test_scalar_values.py`）が確かめていると主張して、実際には確かめていないこと。

対象は `origin/main..HEAD` の差分である。リポジトリのほかのファイルも自由に読んでよい。
