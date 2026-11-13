# レビューの目的

`info-hive-wiki`（Claude Code プラグイン `wiki`）の 0.12.2 の差分である。frontmatter の `title` が文字でないページが 1 つあると、検索などが止まっていたのを直した。

## 直したい欠陥

frontmatter のパーサー（`skills/info-hive/scripts/wiki_text.py` の `parse_frontmatter_text`）は、書かれた形のまま、文字か文字の配列を返す。`title:`（値なし）は空の配列、`title: [WIP]` は `["WIP"]`、`title: [x, y]` は `["x", "y"]` になる。読む側の多くは `title` を文字と決めつけていた。

- `wiki_search.collect_pages()` の `body + " " + meta.get("title", "")` が `TypeError` になり、CLI の検索のすべての機能と、MCP の索引（`wiki_index.WikiIndex`、ツール `query`）が止まった。
- lint の `--suggest-pages` の `nfkc(p["meta"].get("title", ""))` が止まった。
- グラフの抽出が、配列の `title` を sqlite に渡して止まった。

## 決めた規則（作者が選んだ）

新しい `wiki_pages.text_value()` で、`title` を文字にそろえる。

- 文字はそのまま返す。前後の空白も変えない（文字の `title` の結果を 1 バイトも変えないため）。
- 文字でなければ、`ref_values()` でそろえ、要素を「, 」でつなぐ。
- 値がないか空なら `""` を返し、呼ぶ側がスラッグや見出しを使う。
- 検索の語（トークン）には、今までどおり title だけを足す（ないときは何も足さない）。スラッグに置き換えるのは表示の側だけである。

閲覧（`wiki_browse_core.py`）は、別の作業のブランチで大きく変わっている途中なので、触っていない（配列の title を `['x', 'y']` と表示する）。範囲の外として承知している。

## 完了の条件

- `title` が値なし、空の配列、配列、ブロックの配列、文字でない値（パースキャッシュから）のページがあっても、検索（CLI の section、page、`--decide`、`--cache`、`--backlinks`、`--top-linked`、MCP の `query`）、lint の `--suggest-pages`、グラフの抽出とグラフの lint、判定レイヤー、MCP の `list_index` が止まらない。結果の `title` はいつも文字である。
- 文字の `title` だけのページの結果は変わらない。評価ゲート（`run_eval.py --gate --baseline` と `--set ja`）の出力と、評価のコーパスの全クエリの `--json` の出力（170 通り）は、修正の前後でバイト単位で同じだった。

## 読むとよいファイル

- `skills/info-hive/scripts/wiki_pages.py` の `ref_values()` と `text_value()`
- 差分のある `wiki_search.py`、`wiki_lint.py`、`wiki_graph_extract.py`、`wiki_graph_lint.py`、`wiki_decide.py`、`wiki_index.py`
- 新しい試験 `eval/scripts/test_title_values.py`
- 親リポジトリの試験 `C:\Works\info-hive-dev\.claude\worktrees\full-ocr-continue-94ee76\tests\wiki\test_wiki_index.py` の `test_non_string_titles_do_not_stop_the_index`
- `CHANGELOG.md` の 0.12.2 の節、`docs/search.md` の結果の欄の表

## とくに崩してほしい点

- まだ `title` を文字と決めつけて止まる経路、または `title` が文字でないまま出る経路が残っていないか。browse を除く。`grep` で `get("title")` を探すだけでなく、`meta["title"]` や、title を受け取る関数の引数もたどってほしい。
- 文字の `title` の結果が、どこかで変わっていないか（トークン、表示、`--json`、グラフのノード、lint の候補の除外）。
- `text_value()` の規則が、`ref_values()` と食い違う入力、または期待と違う入力。
- 試験が欠陥を捕まえられない書き方になっていないか（修正前の実装で失敗することは確かめた）。
- CHANGELOG と `docs/search.md` が、実装と食い違っていないか。版 0.12.2（パッチ）が妥当か。
