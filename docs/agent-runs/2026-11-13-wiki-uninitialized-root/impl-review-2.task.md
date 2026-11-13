# 実装と設計（3 版目）の敵対的レビューの依頼（2 回目）

info-hive-dev のブランチ `fix/wiki-uninitialized-root` と、サブモジュール `info-hive-wiki` のブランチ `fix/uninitialized-root` の変更をレビューしてほしい。実装の 1 回目のレビュー（`docs/agent-runs/2026-11-13-wiki-uninitialized-root/impl-review-1.md`）は却下だった。指摘を崩れた前提ごとに分けて、設計を 3 版目にし、実装と試験を直した。

## 対象が果たすべき目的

`/wiki:init` をしていないディレクトリ（`SCHEMA.md` のない `wiki/`、GitHub の wiki の写し、空のディレクトリ、ないパス）を、wiki プラグイン `info-hive-wiki` のどの入口も wiki として扱わないこと。

1. 「初期化された wiki」の判定を 1 か所（`info-hive-wiki/skills/info-hive/scripts/wiki_initialized.py`）に決める。
2. wiki を読む入口と wiki のために書く入口が、すべてその判定を、パスを解決する前に通る。長く動くプロセスは要求ごとに通る。未初期化なら何も書かずに止まり、`/wiki:init` を案内する。
3. コマンドの文章とスキルの指示が同じ扱いを書く。
4. 版（0.13.0）と CHANGELOG が、利用者に見える変更を正しく書く。

## 読むもの

- 設計（3 版目）: `docs/plans/wiki-uninitialized-root-2026-11-13.md`。末尾の「レビューの指摘と直し方」に、2 回分の指摘と直し方がある
- ADR: `docs/adr/0019-wiki-root-is-marked-by-schema.md`
- 子の変更: `info-hive-wiki` で `git diff 5326bf9..HEAD`（`5326bf9` は origin/main の 0.12.1）
- 親の変更: `git diff d100dfd..HEAD`（`d100dfd` は分岐点。ローカルの `main` は古いので使わない）
- 前のレビュー: 同じディレクトリの `design-review-1.md` と `impl-review-1.md`

## 確かめたこと

- Windows 11（Python 3.12）と WSL の Ubuntu 24.04（Python 3.12）で、`tests/wiki/test_uninitialized_wiki.py`、`test_browse.py`、`test_browse_server.py` が通る。`<wiki>/ない/..` の試験は、Windows ではパスがあるものになるので飛ばし、Linux で動いて通った。
- 子の CI の手順（`eval/` の試験、評価ゲート、リンクの試験）と、親の `tests/workspace`、`tests/wiki`（MCP、索引、グラフ、閲覧）は、Windows で通った。

## 特に崩してほしいこと

- 実装の 1 回目の指摘（判定の前の解決、アクセス権の失敗、入口の一覧の数え方、基準のディレクトリがないアップグレード）が、3 版目の決め方と実装で本当に閉じたか。
- 判定を通らずに wiki を読むか書く経路、判定の前に何かを書く経路が、まだ残っていないか（コードを読んで確かめる）。
- 閲覧のサーバーが「調べられない」を未初期化と決めない扱いが、未初期化のディレクトリを wiki として扱う穴にならないか。
- 文章とスクリプトの食い違い（コマンドの手順、案内の文、終了コード、CHANGELOG）。

重大な欠陥がなく、軽微な問題だけなら、そう書いてほしい。出力は日本語で書く。
