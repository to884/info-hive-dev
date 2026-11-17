# 図の描画の実装（PR 1: svg）の 2 回目のレビュー

1 回目のレビュー（`docs/agent-runs/2026-11-17-wiki-browse-figures/impl-review-1.md`）の指摘への対応を、`docs/agent-runs/2026-11-17-wiki-browse-figures/impl-responses.md` に書いた。直したプラグインの差分は `docs/agent-runs/2026-11-17-wiki-browse-figures/impl-review-2.plugin.diff`（`info-hive-wiki` の HEAD との差）、開発リポジトリの差分は埋め込んだものである。

1 回目と同じ目的と観点で、次を崩せるか見てほしい。

- `is_utf8_svg` の新しい判定（XML 1.0 の文字の範囲、宣言の読み方）が、XML の符号化の自動判定と食い違う入力。UTF-8 と判定したのに、ブラウザや XML パーサーが別の符号化で読む svg。
- `_svg_root_attrs` の expat の使い方（例外の扱い、DTD、外部実体、巨大な入力、名前空間）。
- `image_ref_path` と `figure_target` が、まだ食い違う参照先。
- 直したことで壊れたもの。
