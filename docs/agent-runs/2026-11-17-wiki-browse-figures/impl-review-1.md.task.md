# 図の描画の実装（PR 1: svg）の 1 回目のレビュー

対象は、`/wiki:browse` に `wiki/assets/` の svg の表示を足す実装である。設計は `docs/plans/wiki-browse-figures-2026-11-17.md` の 6 節（svg）、8 節のうち svg の入れ物、9 節、10 節。決定は `docs/adr/0030-wiki-browse-shows-figures-as-images.md`（提案）。Mermaid（7 節）はこの PR に含まない。

差分は 2 つのリポジトリにある。

- プラグイン（サブモジュール `info-hive-wiki`）: `git -C info-hive-wiki diff HEAD`。`skills/info-hive/scripts/` の `wiki_pages.py`（`walk_assets`）、`wiki_browse_fs.py`（`walk_inputs`、`read_file_capped`、`read_input_capped`、`TooLarge`）、`wiki_browse_core.py`（`CSP_SVG`、`ASSET_MAX_BYTES`、`is_utf8_svg`、`svg_size`、`_read_asset`、`take_snapshot`、`figure_target`、`Core._build_assets`、`figure_state`、`asset_bytes`、`_figure_html`、`_prepass` の画像の診断、`_transform_inline` の画像の分岐、`knows`、`render_all`、`CORE_VERSION`）、`wiki_browse.py`（`_send` の `csp` と `cache`、`_view` の svg）、`wiki_lint.py`（`missing_assets` の文字参照）、`browse_assets/style.css`、文書 3 つ。
- 開発リポジトリ: `tests/wiki/test_browse.py`（`FigureTargetTest`、`FigureSvgTest`、`UnlistableAssetsTest`、`UnreadableExcludedDirTest` の期待の変更）、`tests/wiki/test_browse_server.py`（`SvgServeTest`）、新しい `tests/wiki/browse/figures.test.mjs`、`.github/workflows/wiki-browse.yml`。

実装は設計から 3 点を変えた。設計書に反映してある。

1. `assets/` の一覧を作れなくても閲覧を止めない。大きさのない `asset_dir` の項目で表す（既存の試験 `UnreadableExcludedDirTest` が守る契約に合わせた）。ルートの一覧を作れないときは今と同じく全体を採らない（入出力の層の掃引の試験 `QuickSweepTest` で分かった）。
2. `<img>` に `width` と `height` の属性を付け、`loading="lazy"` を付けない。入れ物は `inline-block`。WebKit と Firefox で画像の幅が 0 になったため。
3. lint の `missing_assets` が、参照先の文字参照を解く。

守るべき目的は、設計書の冒頭と 6 節にある。とくに次を崩せるか見てほしい。

- 入力の走査と写しの契約: `walk_inputs` の一覧と印、2 回の走査、`InputsUnknown`、`unreadable` と `transient`、世代、`_machine_needles`（`asset_dir` の項目や大きさのない `asset` が、ほかの処理を壊さないか）、`fs.build` と書き出しの門。
- 出力の名前 `assets/wiki/<16 桁>.svg` と、ページの出力、生成器のファイル、`RESERVED_TOP`、`unify_dir_case`、`_clashes` の関係。大文字と小文字だけが違う svg、NFC と NFD で同じ綴りの svg。
- `figure_target` と lint の `missing_assets` のずれ（文字参照、エスケープ、`%` の符号化、`..`、Windows の大文字と小文字）。
- サーバーの `_view`: svg の名前の扱い、CSP とヘッダー、HEAD、`stale` のときの応答、作り直しのあとの古い名前。
- `svg_size` と `is_utf8_svg` の正規表現と、信頼しない svg（巨大、壊れた、宣言の位置、コメントの中の `<svg`）。
- 既存の試験の期待を変えた箇所（`UnreadableExcludedDirTest`）が、守っていた性質を弱めていないか。
- 試験が、主張していることを本当に確かめているか（とくに `figures.test.mjs` の色の確かめ、`test_links_are_not_read` が Windows で飛ばされること）。
