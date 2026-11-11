対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、今は wiki 0.9.0、`64acc43`）に、閲覧（browse）の第 1 段階とサーバーのアダプタを足す設計である。

目的（対象が果たすべきこと）:
- ADR-0010（`docs/adr/0010-wiki-browse-separates-core-from-delivery.md`）の決定（構成、画面の契約、データの契約、安全と閲覧専用、合格の条件、作る順序の 2〜4、未決だった事項の決定の 2、3、7）と、ADR-0002（`docs/adr/0002-wiki-browse-uses-on-demand-local-server.md`）のうち ADR-0010 で置き換えていない行（127.0.0.1、起動ごとのトークン、Host の確認、閲覧専用、markdown-it-py、`canonical_meta()`、開いたときに変換）を満たす。
- 第 1 段階の合格の条件は、ADR-0016（`docs/adr/0016-wiki-browse-stage1-accepts-two-delivery-methods.md`、2026年11月9日に作者が決めた）による。ADR-0010 の合格の条件のうち、交換できることの確認と閲覧専用の確認の 2 行を、第 1 段階についてサーバーと静的 HTML の 2 方式に改めた。この ADR は作者の決定なので、2 方式であること自体は崩す対象にしない。ADR-0016 の書いたとおりに試験が定まっているかは崩す対象である。
- 関係表は、別の作業で行うグラフの抽出の修正を前提にする。設計の 3 の「グラフの抽出に求める契約」が、関係表を正しく作るのに足りるか（足りない入力があるか）を崩す対象にする。修正の実装は、まだない。
- ADR-0001（`docs/adr/0001-local-only-server-is-not-hosted-wiki.md`）の 3 条件と、閲覧専用（Wiki のファイルを変えない、未解決リンクでファイルを作らない）を守る。
- wiki 0.9.0 の `wiki_pages.py`（ページの集合とリンクの規則）と同梱した markdown-it-py 3.0.0 を使い、lint と同じリンクの判定になる。
- 選択肢のレポート（`docs/research/llm-wiki-browse-options.md` の第 1 段階と合格の目安、第6.8節の安全）を満たす。

読むもの:
- これまでのレビュー: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/design-review-1.md`、`design-review-2.md`、`design-review-3.md`（設計の最後に対応の表がある。前の指摘が直ったかも確かめる）
- `docs/adr/0016-wiki-browse-stage1-accepts-two-delivery-methods.md`
- 設計: `docs/plans/wiki-browse-stage1-2026-11-09.md`
- PoC: `poc/browse/gen.py`、`serve.py`、`static/`、`review_checks.py`、`names_check.py`、`test.mjs`、記録 `docs/research/wiki-browse-adr-0010-poc-2026-11-07.md`
- 今のコード: `info-hive-wiki/skills/info-hive/scripts/` の `wiki_pages.py`、`wiki_lint.py`（`collect_pages`、`collect_index_entries`）、`wiki_graph_extract.py`（`collect_pages`、`build_nodes`、`build_edges`）、`wiki_mcp_common.py`（`data_dir`、`wiki_key`）、`wiki_index.py`（`stat_signature`）、`wiki_workspace.py`、`commands/*.md`

とくに崩してほしい点:
1. ADR-0010 と ADR-0002 の決定との食い違い、満たしていない決定。
2. サーバーの安全（トークン、Host、DNS rebinding、パスの閉じ方、`..` と符号化、Windows のパス、シンボリックリンク、起動の競合、終了しない場合）。
3. 閲覧専用と絶対パスの漏れ（生成の記録、`data/*.js`、エラーの応答、`raw:`）。
4. 開いたときに描く作りと、要求ごとの作り直しの競合や古さ。
5. 関係表を frontmatter から作る判断と、PyYAML が要ることの影響。
6. ナビゲーションを `index.md` と `indexes/` から作る規則の穴。
7. `export_name` と出力の入れ替え（Windows のファイルの掴み、途中で止まったとき）。
8. 試験の網羅（ADR-0010 の「交換できることの確認」「閲覧専用の確認」を満たすか）。
