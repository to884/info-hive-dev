# 依頼: 2 回目の実装のレビューの指摘を直したので、続けて壊してほしい

前回のレビュー（`docs/agent-runs/2026-11-14-wiki-help-command/impl-review-2.md`）の指摘を、設計 `docs/plans/wiki-help-command-2026-11-14.md` の「レビューの指摘と直し方」の 3 つ目の表のとおりに直した。

- `verify_rewrite()` は、宛先を復号せずに比べる。期待する宛先は、前の宛先を `link_url()` で書き換え、パーサーの `normalizeLink()` で正規化したもの。
- `link_url()` は、宛先を `urlsplit` で部分に分け、パスだけをファイルにし、クエリとフラグメントは書かれたまま付ける。画像は `raw.githubusercontent.com` を指す。
- `token_shape()` は、画像の子をたどらない。
- 試験に、わざと壊した書き換えを照らし合わせに渡す試験と、実物の宛先を本体の関数を使わずに求めて照らす試験を足した。
- プラグインのブランチを origin/main（PR #54 のマージ）の上に載せ直し、CHANGELOG の `[Unreleased]` の #54 の Fixed を 0.14.0 に移した（作者の決定）。

差分: `git -C info-hive-wiki diff origin/main..HEAD`、`git diff origin/main..HEAD`。

直しが指摘を閉じたか、直しが新しい欠陥を生んでいないかを確かめ、前回と同じ見出しの順で書いてほしい。
