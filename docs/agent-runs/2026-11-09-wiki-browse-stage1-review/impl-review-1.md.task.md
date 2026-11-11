対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、ブランチ `feature/browse-stage1`、0.9.3 の `c50854a` の上）に足した、閲覧（browse）の第 1 段階の実装のうち、中核、書き込みの守り、静的の書き出し、中核の子プロセスの入出力である。サーバー（`serve` と `stop`）はまだ作っていない。今回は崩す対象にしない（`wiki_browse.py` の `_add_server_commands` は空である）。

目的（対象が果たすべきこと）:
- 設計 `docs/plans/wiki-browse-stage1-2026-11-09.md`（Sol の設計のレビューで「条件付きで採用可」になり、指摘を入れたもの）の 1〜7 と 9 と 11 のうち、サーバーを除く部分を満たす。設計の「守ること」の 1〜6、8、9 を、静的の書き出しと中核で守る。
- ADR-0010（`docs/adr/0010-wiki-browse-separates-core-from-delivery.md`）と ADR-0016（`docs/adr/0016-wiki-browse-stage1-accepts-two-delivery-methods.md`）の決定に従う。
- 既存のスクリプト（lint、グラフの抽出、検索）の振る舞いを変えない。

読むもの:
- 新しいファイル: `info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_browse.py`、`browse_assets/app.js`、`browse_assets/style.css`
- 既存のファイルの変更（振る舞いを変えない切り出し）: `git -C info-hive-wiki diff c50854a 35f73fc` で見られる。`wiki_pages.py` の `new_parser()` と `WIKILINK_FULL_RE`、`wiki_lint.py` の `index_files()`、`wiki_graph_extract.py` の `parse_ontology()`
- 試験: `tests/wiki/test_browse.py`、`tests/wiki/test_browse_fs.py`、`tests/wiki/browse/browse.test.mjs`（Playwright。手元の Windows の Chromium で、静的版だけを流して通った）
- 使っている既存の関数: `wiki_pages.py`（`link_candidates`、`build_page_index`、`classify_source_ref`、`ref_values`、`extract_wikilinks`）、`wiki_lint.py`（`collect_pages`、`parse_frontmatter_raw`、`lint` の `broken_links`、`missing_raw`）、`wiki_graph_extract.py`（`parse_frontmatter`、`normalize_refs`、`build_nodes`、`build_edges`）、`wiki_graph_common.py`（`_try_lock`）、`wiki_mcp_common.py`（`data_dir`、`wiki_key`）
- これまでの設計のレビュー: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/design-review-11.md` 〜 `design-review-14.md`

手元で試験を流すとき:
- `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -B -m unittest tests/wiki/test_browse.py tests/wiki/test_browse_fs.py -v`（Windows で 47 件が通り、Linux だけの 2 件を飛ばす）

とくに崩してほしい点:
1. 設計と実装の食い違い（設計に書いたのに実装にない、実装が設計と違う規則で動く）。
2. 守ること 1（閲覧専用）: `wiki_browse_fs.Guard` を通らない書き込み、実体の判定の穴（Windows のジャンクション、大文字と小文字、`st_ino` が 0 のファイルシステム、まだないパス）、`cleanup` と入れ替えの手順で、最後に公開した世代が失われる経路、ほかの書き出しのファイルを消す経路。
3. 守ること 2（lint と同じ判定）: 描画が wikilink として描くものと `extract_wikilinks()` の食い違い、`unresolved` と lint の `broken_links` の食い違い、`id_collision` と `ambiguous` の扱い。
4. 守ること 4（絶対パス）: 生成器が出力に絶対パスを入れる経路（診断、関係表、ナビゲーション、`core` の応答）と、`find_leaks` が見逃す形、利用者の内容として誤って通す形。
5. 描画の安全: HTML のエスケープの漏れ、インラインの `style` やスクリプト、`<a>` の入れ子、`href` に入る危ないスキーム。
6. 試験が、主張していることを本当に確かめているか（通るのに守れていない試験）。
