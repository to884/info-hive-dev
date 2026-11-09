対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、今は wiki 0.8.0、`c23ae5b`）で、ページの集合とリンクの規則を 1 つのモジュール `wiki_pages.py` にまとめる設計である。

目的（対象が果たすべきこと）:
- ADR-0010（`docs/adr/0010-wiki-browse-separates-core-from-delivery.md`）の決定の 1 と 3、および「承認のあとの作業」の 1 と 2 を満たす。閲覧の「ページ」とリンクの解決は lint の集合を正とし、除外の規則とリンクの抜き出し方を 1 か所に置く。コードスパンとコードブロックの中の `[[...]]` は数えない。検索（search と MCP の索引）も同じ集合にそろえる。lint に大文字と小文字だけが違うページの検査を足す。
- のちに browse の中核（PoC は `poc/browse/gen.py`）が同じ規則を使えること。
- 既存の利用者の wiki を壊さないこと。lint は報告だけで編集しない。lint と stats は標準ライブラリだけで動く。

読むもの:
- 設計: `docs/plans/wiki-page-set-and-links-2026-11-09.md`
- 今のコード: `info-hive-wiki/skills/info-hive/scripts/` の `wiki_lint.py`、`wiki_search.py`、`wiki_graph_extract.py`、`wiki_graph_lint.py`、`wiki_stats.py`、`wiki_text.py`（`lines_outside_fences`、`CODE_SPAN_RE`）、`wiki_index.py`、`wiki_decide.py`、`wiki_mcp_server.py`、`setup_wiki.py`、`test_link_resolution.py`
- 試験: `tests/wiki/`
- PoC の記録: `docs/research/wiki-browse-adr-0010-poc-2026-11-07.md` の未決 1

とくに崩してほしい点:
1. `extract_wikilinks` の「フェンスの外の行から、インラインのコードを除いて拾う」が、CommonMark（markdown-it）の解釈と食い違う反例。複数行にまたがるコードスパン、HTML ブロック、エスケープ、表の中の `\|`、フェンスの開きの規則など。
2. `.` で始まる要素をどこでも除くことの副作用。
3. 使う側の見落とし（ページの集合やリンクを自前で拾うスクリプト、キャッシュ、MCP のツール、試験）。
4. `case_only_duplicates` の定義の穴（NFC と casefold の順、ディレクトリとファイルが同じ名前になる場合など）。
5. 版（0.9.0）と、利用者に見える変化の書き漏らし。
