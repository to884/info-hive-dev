# 実装と設計（2 版目）の敵対的レビューの依頼（1 回目）

info-hive-dev のブランチ `fix/wiki-uninitialized-root` と、サブモジュール `info-hive-wiki` のブランチ `fix/uninitialized-root` の変更をレビューしてほしい。設計の 1 版目は、あなたの 1 回目のレビュー（`docs/agent-runs/2026-11-13-wiki-uninitialized-root/design-review-1.md`）で却下だった。指摘を崩れた前提ごとに分けて 2 版目に直し、実装した。2 版目の設計の確かめも、このレビューに含める。

## 対象が果たすべき目的

`/wiki:init` をしていないディレクトリ（`SCHEMA.md` のない `wiki/`、GitHub の wiki の写し、空のディレクトリ、ないパス）を、wiki プラグイン `info-hive-wiki` のどの入口も wiki として扱わないこと。

1. 「初期化された wiki」の判定を 1 か所（`info-hive-wiki/skills/info-hive/scripts/wiki_initialized.py`）に決める。
2. wiki を読む入口と wiki のために書く入口（CLI、MCP のツール、閲覧、Web ページの取得、経験の記録、アップグレード）が、すべてその判定を通る。長く動くプロセスは要求ごとに通る。未初期化なら何も書かずに止まり、`/wiki:init` を案内する。
3. コマンドの文章（`info-hive-wiki/commands/*.md`）とスキルの指示（`SKILL.md`、`references/`）が同じ扱いを書く。
4. 版（0.13.0）と CHANGELOG が、利用者に見える変更を正しく書く。

## 読むもの

- 設計（2 版目）: `docs/plans/wiki-uninitialized-root-2026-11-13.md`。末尾に「1 回目のレビューの指摘と直し方」がある
- ADR: `docs/adr/0019-wiki-root-is-marked-by-schema.md`
- 子の変更: `info-hive-wiki` で `git diff 5326bf9..HEAD`（3 つのコミット。新しいファイル `skills/info-hive/scripts/wiki_initialized.py` もある）
- 親の変更: `git diff main..HEAD`（新しいファイル `tests/wiki/test_uninitialized_wiki.py` もある）
- 1 回目のレビュー: `docs/agent-runs/2026-11-13-wiki-uninitialized-root/design-review-1.md`

## 特に崩してほしいこと

- 1 回目のレビューの指摘（閲覧のサーバーの要求、評価のランナー、バイトコード、`--stop`、解決の前の判定）が、2 版目の決め方と実装で本当に閉じたか。例外にしたもの（評価のランナー、バイトコード）の理由が成り立つか。
- 判定を通らずに wiki を読むか書く経路が、まだ残っていないか（コードを読んで確かめる）。入口を機械的に数える試験（`EntranceInventoryTests`）の数え方に、漏れる形がないか。
- 判定の前に何かを書く経路（ディレクトリ、キャッシュ、データの場所の状態や索引）がないか。
- 文章とスクリプトの食い違い（コマンドの手順、案内の文、終了コード）。
- 既存の試験の素材に `SCHEMA.md` を足した直しが、試験の意味を変えていないか。
- 互換でない変更の書き方と、版の判断。

出力は日本語で書く。
