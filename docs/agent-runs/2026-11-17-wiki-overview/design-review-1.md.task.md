# 敵対的レビューの依頼: ページの概要を作り、サイドカーに置く設計（1 版目）

## 対象が果たすべき目的

Claude Code プラグイン `wiki`（`info-hive-wiki/`、スキル名 `info-hive`）に、ページごとの「概要」（LLM が作る、図を中心にした初心者向けの説明）を作って wiki に置く仕組みを足す。対象の 2 つの文書は、その設計と決定の記録である。

- `docs/plans/wiki-overview-2026-11-17.md`: 設計（段 1。概要を作って wiki に置く側）
- `docs/adr/0031-wiki-page-overview-lives-in-a-sidecar.md`: 決定の記録

設計は、次を満たさなければならない。

1. wiki に書くのは `wiki_overview.py` だけで、モデルは wiki の外の作業用のフォルダーに下書きを置く。
2. 概要が新しいか古いかを、今の中身から推さずに、スクリプトが書いたハッシュで決める。
3. サイドカーと概要の図を置いても、既存の読み手（lint、検索、グラフ、統計、今の browse、MCP サーバー）の結果が変わらない。
4. 書き込みが途中で止まっても、参照先のない図を参照する概要が wiki に残らない。
5. 利用者の引数（日本語を含むページ名）を、シェルに安全に渡す。
6. あとで書く browse の表示（段 2）と、別のブランチで進んでいる図の表示（ADR-0030）に、無理なくつながる。
7. 開発用の PC にだけあるもの（スキルの名前、絶対パス）を仕様にしない。

## 読むとよい場所

- プラグインの今の実装: `info-hive-wiki/skills/info-hive/scripts/`（wiki 0.25.2）。特に `wiki_pages.py`（走査、`link_candidates`、`build_page_index`）、`wiki_lint.py`（`lint()`、`missing_assets`、`parse_frontmatter_raw`）、`wiki_text.py`（`parse_frontmatter_text`、`format_frontmatter`、`IMAGE_RE`）、`wiki_session.py` と `wiki_youtube.py`（スクリプトが raw を書く前例）、`wiki_fetch.py`（`write_outputs`、`replace_with_retry`）、`wiki_mcp_common.py`（`data_dir`、`wiki_key`、`SERVER_FILES`）、`wiki_browse_core.py`（`_page_id`、`read_text_like_lint`、`body_html`）、`init_wiki.py`（`SCHEMA_SECTION_MARKERS`）。
- コマンド: `info-hive-wiki/commands/*.md`。引数の渡し方の決まりは `wiki/concepts/コマンドの引数の渡し方.md`。
- 関連する決定: `docs/adr/0005-*.md`、`0017-*.md`、`0020-*.md`、`0023-*.md`、`0029-*.md`。書く段の設計は `docs/plans/wiki-apply-2026-11-14.md`、リンクの設計は `docs/plans/wiki-links-2026-11-16.md`（どちらも未実装）。
- 図の表示の設計と ADR-0030 は、この作業ツリーにはない。別の作業ツリーの `C:\Works\info-hive-dev\.claude\worktrees\browse-figures\docs\plans\wiki-browse-figures-2026-11-17.md` と `…\docs\adr\0030-wiki-browse-shows-figures-as-images.md` にある（読めれば読む。読めなければ、設計書の 1 節と 12 節の記述を前提にしてよい）。
- 試作: `poc/wiki-overview/`（`overview/` の下が、概要の実物。`build.py` が browse の書き出しに差し込む）。

## 特に崩してほしい点

- 5 節の置き場所と名前（サイドカーのパス、図の名前の `<P>` と `<C>`、ページの識別子と NFC、大文字と小文字、ページの改名）。
- 5.5 節の状態の表（上から順に見て最初に当たる行で決まるか。もれと重なり）。
- 6 節のサブコマンドの流れ（`prepare`、`check`、`write`、`status`、`remove`）。作業用のフォルダー、`plan.json`、ページの写し、終了コード、JSON の形の矛盾や欠落。
- 6.4 節の書き込みの順と守り（途中で止まったときの状態、Windows の置き換え、リンクとジャンクション、`assets` の綴り、同時の書き手）。
- 7 節の下書きの規則（`image_form` の「markdown-it の結果と行の形の突き合わせ」で、すり抜けや、正しい下書きを拒む場合があるか。行き先の書き換えが壊れる場合）。
- 8.1 節の引数の渡し方（Git Bash と PowerShell の両方で、挙げた文字の制限で足りるか）。
- 9 節の lint（`figure_unused` と `figure_missing` の判定が、ADR-0005 の図や利用者のファイルを取り違えないか。MCP の `lint` と CLI の一致）。
- 11 節の「失敗の形」と「保証しないこと」に書かれていない、実装すれば必ず踏む欠陥。
- 12 節と 13 節の、図の表示（ADR-0030）への依存の置き方。

重大の指摘には、発生の度合いを A（仕様の矛盾か欠落で、実装すれば必ず踏む）、B（日常の使い方で起きうる）、C（まれな時機や名前）、D（作為的な配置が要る）で添えてほしい。
