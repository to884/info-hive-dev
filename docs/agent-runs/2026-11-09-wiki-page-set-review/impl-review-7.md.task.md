対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、基準は wiki 0.8.0 の `c23ae5b`）で、ページの集合とリンクの規則を新しい `wiki_pages.py` にまとめた実装である。版は 0.9.0 にした。

経緯: 最初の 4 回の実装は、閲覧が使う markdown-it のブロックの規則を標準ライブラリで手で写したもので、Sol の実装レビュー（`docs/agent-runs/2026-11-09-wiki-page-set-review/impl-review-1.md`〜`impl-review-4.md`）で 4 回とも却下された。作者は 2026年11月9日に、markdown-it-py 3.0.0 と mdurl 0.1.2 を `skills/info-hive/scripts/_vendor/` に同梱し、リンクの抜き出しとセクションの分け目の判定をそれに任せる方式を選んだ。手で写した解析は消した。同梱の方式への 2 回のレビュー（impl-review-5.md、impl-review-6.md、どちらも却下）の指摘も直した（設計の最後の 2 つの表）。

読むもの:
- 設計: `docs/plans/wiki-page-set-and-links-2026-11-09.md`（2 の「リンクの抜き出し」が同梱の方式。最後に 5 回分の指摘への対応の表）
- 基準からの差分（同梱した markdown_it/ と mdurl/ の中身は除く）: `docs/agent-runs/2026-11-09-wiki-page-set-review/impl-7.wiki.diff`
- 作業ツリーの実物: `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`、`_vendor/README.md`、`_vendor/licenses/`、`wiki_search.py`、`wiki_lint.py`、`wiki_stats.py`、`wiki_graph_extract.py`、`wiki_decide.py`、`wiki_mcp_common.py`、`tests/wiki/test_page_set.py`、`.github/workflows/wiki-mcp.yml`

果たすべきこと:
- ADR-0010 の決定の 1 と 3。閲覧の markdown-it と同じトークンから wikilink を拾い、コードの中の `[[...]]` を数えない。lint、search（MCP の索引と `get_page`）、グラフ、stats、判定レイヤーのページの集合とリンクがそろう。
- 既存の利用者の wiki を壊さない。lint と stats は利用者が何も入れずに動く（同梱した解析器で）。MCP サーバーが新しい規則を使う（`SERVER_FILES`、`code_version`）。
- 同梱が正しい: 読み込み順で同梱した版が使われる、版の確認、ライセンスの表記、取得元の記録、版を上げるときに MCP サーバーが入れ替わる。

とくに崩してほしい点: 同梱した `markdown_it` より先に別の版が読み込まれる経路（MCP サーバー、uv の環境、試験）、`_splits_section` と `split_sections` と `extract_wikilinks(headings=False)` の範囲の食い違い、`_line_kinds` の `map` の扱い、`code_version` が同梱した版の変更を拾うか、性能の劣化（大きな wiki の lint と検索）、0.8.0 からの後退、変更履歴と手順書の誤り。手で写していたときの規則の写し漏れは、もう対象ではない。
