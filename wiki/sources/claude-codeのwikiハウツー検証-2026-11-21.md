---
type: "source"
title: "Claude Desktop Code の Wiki ハウツーの検証（2026-11-21）"
authors: ["info-hive-dev"]
tags: ["試験", "コマンド"]
sources: []
entities: ["info-hive-wiki"]
raw: "raw/claude-codeのwikiハウツー検証-2026-11-21.md"
raw_sha256: "d54899a59f2fe1bce4d9c553f19da6c68ab6e0d50ba3a8df4a6b8b4f79f9730a"
created: 2026-11-21
updated: 2026-11-21
ingested: 2026-11-21
---

# Claude Desktop Code の Wiki ハウツーの検証

[[確認5の3回の共通点-2026-11-21|確認 5]] の `S2-wiki-0.39.1` から、Windows 11 の Claude Desktop 6.6395.0.0 で [[info-hive-wiki]] のハウツーを実行した。

- `/wiki:init --user` は既定のユーザー wiki を作り、承認した定型文を `%USERPROFILE%\.claude\CLAUDE.md` に新規作成した。ユーザー wiki の `SCHEMA.md` の検索例には相対パス `--wiki wiki/` が残った。
- Web ページの取り込みは `wiki:web-raw` に委ねた。翻訳警告 3 件を受理した後の検査は `ok: true`、`completed: true`。出力の末尾は切り詰められたため、作業用ディレクトリが消えたことはファイルシステムで照合した。
- `/wiki:upgrade` は `ready` を返した。同じ版の `SCHEMA.md` は前後で SHA-256 が一致した。マーケットプレイスの更新後、Wiki のアップデート確認は「前回のリリース以降、変更はありません。」だった。

## 取り込んだ内容と載せたページ

| 内容 | 掲載方法 | ページ | 理由 |
| --- | --- | --- | --- |
| ユーザー wiki、Web の取り込み、アップグレードと更新の観測 | source_only | このページ | 確認 10 の結果をアプリとプラグインの版に結びつける |
| 確認 10 の開始時点 | update | [[確認5の3回の共通点-2026-11-21]] | S2 からの続きに移動できるようにする |

[確認 10 の検証記録](../../docs/research/usage-docs-facts-2026-11-20.md#確認-10-のハウツー)

## 利用者向けの案内

導入、チュートリアル、障害対処、コマンド参照は HTML 内でつなぐ。既存の Markdown と内容が重複しても、手順に必要な情報は HTML に載せる。14 ページの試作を Chromium で開き、すべてのリンクが HTML 内で解決し、12 コマンドの書式と練習用原文 2 件が正本と一致することを確認した。[利用者向け文書の計画](../../docs/plans/usage-docs-2026-11-15.md)

入口の左側は目次、右側の先頭はプラグインの `README.md` を変換した本文にする。開発リポジトリの `tools/docs/render_readme.py` で静的 HTML を作り、利用者向けの文書リンクを `docs/` 内の HTML にそろえる。スマートフォン程度の幅では目次を本文の上に置く。

入口の「インストール」は、Windows 11 の VM で確かめた Code タブの導入を案内する。詳細は `tutorial-install.html` に置く。Claude デスクトップアプリは公式の MSIX、uv は Astral のインストーラーを使う。CLI と Codex の導入はエージェント別の HTML に載せる。

旧 `docs/index.md` の概要は `docs/html/index.html` の右側の先頭に移した。図で資料、wiki、出典つきの答えの関係を示し、図の下から Windows と Codex などの導入へ進める。左の目次と図の下の README から詳細を参照する。

利用者向け HTML と表示用の CSS・ライセンスは `info-hive-wiki/docs/html/` にまとめる。フォルダーだけをコピーして `index.html` をブラウザーで開けることを確認した。公開 URL は別途決める場合に扱う。
