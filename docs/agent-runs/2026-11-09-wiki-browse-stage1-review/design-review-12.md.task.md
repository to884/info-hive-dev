対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`）に、閲覧（browse）の第 1 段階とサーバーのアダプタを足す設計である。2026年11月11日に全体を書き直した版で、これまでの 10 回のレビューで足した規則を「守ること」と仕組みに整理し、いくつかの決定を改めた（設計の冒頭の表）。

目的（対象が果たすべきこと）:
- ADR-0010（`docs/adr/0010-wiki-browse-separates-core-from-delivery.md`）の決定（構成、画面の契約、データの契約、安全と閲覧専用、作る順序の 2〜4、未決だった事項の決定の 2、3、7）と、ADR-0002（`docs/adr/0002-wiki-browse-uses-on-demand-local-server.md`）のうち ADR-0010 で置き換えていない行（127.0.0.1、起動ごとのトークン、Host の確認、閲覧専用、markdown-it-py、`canonical_meta()`、開いたときに変換）を満たす。
- 第 1 段階の合格の条件は、ADR-0016（`docs/adr/0016-wiki-browse-stage1-accepts-two-delivery-methods.md`、作者の決定）による。サーバーと静的 HTML の 2 方式であること自体は、崩す対象にしない。ADR-0016 のとおりに試験が定まっているかは崩す対象である。
- ADR-0001（`docs/adr/0001-local-only-server-is-not-hosted-wiki.md`）の 3 条件と、閲覧専用（Wiki のファイルを変えない、未解決リンクでファイルを作らない）を守る。
- lint と同じリンクの判定になる。
- 選択肢のレポート（`docs/research/llm-wiki-browse-options.md` の第 1 段階と合格の目安、第6.8節の安全）を満たす。

前提として扱うもの（崩す対象にしない）:
- wiki 0.9.2 のグラフの抽出の修正（to884/info-hive-wiki#34、ブランチ `fix/graph-duplicate-slugs`、先頭 `599611e`。スクリプトは `34334b3` から変わっていない。サブモジュールの作業ツリーは 0.9.0 の `64acc43` のままなので、0.9.2 のコードは `git -C info-hive-wiki show 599611e:skills/info-hive/scripts/<ファイル>` で読む）。設計の「前提」の節に挙げた 5 つの性質は、その修正の側のレビューで確かめた。この性質を満たす抽出を前提にして、browse の使い方（振り分け、診断、表示）が崩れるかを崩す対象にする。設計が挙げる 0.9.2 の関数の形（引数、返り値、キー）が、実際のコードと食い違っていれば、それは指摘の対象である。

読むもの:
- 設計: `docs/plans/wiki-browse-stage1-2026-11-09.md`
- これまでのレビュー: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/design-review-1.md` 〜 `design-review-11.md` と、指摘と対応の対照 `responses-1-10.md`、`responses-11-onward.md`（11 回目は、書き直したあとの最初のレビューである。その指摘が直ったかも確かめる）。書き直しで、前に閉じた指摘がまた開いていないかも確かめる。
- PoC: `poc/browse/gen.py`、`serve.py`、`static/`、`review_checks.py`、`names_check.py`、`test.mjs`、`kinsoku.mjs`、記録 `docs/research/wiki-browse-adr-0010-poc-2026-11-07.md`
- 今のコード（0.9.2 は上の `git show` で）: `wiki_pages.py`、`wiki_lint.py`（`collect_pages`、`collect_index_entries`、`parse_frontmatter_raw`、`missing_raw`）、`wiki_graph_extract.py`（`parse_frontmatter`、`read_ontology`、`build_nodes`、`build_edges`）、`wiki_graph_common.py`（ロック）、`wiki_mcp_common.py`（`data_dir`、`wiki_key`）、`commands/*.md`

とくに崩してほしい点:
1. この版で改めた決定（設計の冒頭の表）。とくに、(a) 変更を見つけた要求が作り直しを待つ作り（8.3）の競合、待ち、失敗時の扱い、(b) 絶対パスの検査が、利用者が本文に書いたパスを通す規則（5）の抜け道、(c) `link_candidates()` だけでリンクの状態を決める規則（3.3）と lint の `broken_links` の一致、(d) lint と同じパーサーから描く規則（3.3）で、描画と `extract_wikilinks()` が食い違う入力。
2. 「守ること」の 9 つのそれぞれについて、仕組み（1〜9 節）が守れていない入力や手順。
3. 書き込みの守り（6）と、守る場所を最初の書き込みの前に決める順序（6.1、7、8.5、8.6）の穴。
4. サーバーの起動、使い回し、停止（8.4〜8.6）の競合。
5. 「守ること」と試験（11）の対応の抜け。守ることのうち、試験で確かめられないもの。
6. ADR-0010、ADR-0002、ADR-0016 の決定との食い違い。

設計が「限界」の節に挙げたもの（挙げたとおりの範囲に限る）は、作者が受け入れた限界として扱い、同じ内容を欠陥として挙げない。限界の書き方が実際より狭い（挙げていない被害がある）ときは、指摘の対象である。
