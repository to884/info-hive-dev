# レビューの依頼: browse の画面に wiki のスコープを出す（設計と実装）

## 目的

info-hive の wiki プラグイン（`info-hive-wiki`、Claude Code プラグイン `wiki`）の閲覧機能 `/wiki:browse` に、開いた wiki が「ユーザースコープの wiki」か「どのプロジェクトの wiki」かを出す。作者の依頼は「ユーザースコープなのかプロジェクトスコープなのかわかるようにして」である。作者は、ユーザースコープの wiki（`~/info-hive/W0_Wiki`、作業領域の設定なし）と、プロジェクトの wiki（`C:/Works/info-hive-dev/wiki`、作業領域の設定なし、プロジェクトのルートに `.git`）の 2 つを使っている。

この変更が守るべきこと:

1. 表示されるスコープが、利用者を誤らせない（違うスコープを確信をもって出さない）。
2. 閲覧は読むだけで、wiki のファイルも wiki の外のファイルも書き換えない（`docs/adr/0017-*` と第 1 段階の設計の 6）。
3. 静的の書き出し（`build`）は、生成器が入れた絶対パスを出力に含めない（第 1 段階の設計の 5、`find_leaks`）。
4. 中核（`wiki_browse_core.Core`）は wiki の写しだけから描き、wiki の外を読まない（ADR-0010）。
5. 既存の閲覧の振る舞い（ナビゲーション、データの契約の版、サーバーの使い回しと停止）を壊さない。

## 読むもの

- 設計: `docs/plans/wiki-browse-scope-2026-11-12.md`
- 実装の差分: `docs/agent-runs/2026-11-12-wiki-browse-scope/info-hive-wiki.diff`（サブモジュール `info-hive-wiki` の作業ツリーの差分）
- 試験の差分: `docs/agent-runs/2026-11-12-wiki-browse-scope/tests.diff`
- 変更後のソース: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`browse_assets/style.css`、`browse_assets/app.js`、`wiki_workspace.py`（変えていない。`find_workspace` と `user_workspace_root` を使う）
- 前提の文書: `docs/adr/0008-numbered-workspace-layout.md`（作業領域と `kind`）、`docs/adr/0010-*`、`docs/plans/wiki-browse-stage1-2026-11-09.md`、`info-hive-wiki/commands/browse.md`、`info-hive-wiki/commands/init.md`、`info-hive-wiki/skills/info-hive/SKILL.md` のスコープの節

## 特に崩してほしい点

- スコープの決め方（設定 → ユーザースコープの作業領域の場所 → 親の `.git` → 不明）の順と各規則が、誤ったスコープを出す具体的な配置。特に、作者の実際の 2 つの wiki、`/wiki:init` と `/wiki:init --user` の既定の配置、`--wiki-dir` を使った配置、サブモジュールの中の wiki、シンボリックリンクやジャンクション、Windows のドライブ違いや大文字小文字。
- 決め方が、閲覧が守るべき 2〜5 のどれかを破るか（読み取りの副作用、パスの漏れ、例外で閲覧が止まるなど）。
- サーバーを使い回したときの出力と画面の食い違い、記録（`server.json`）の互換性。
- 試験が、主張していることを本当に確かめているか。

実行環境は Windows 11、Python 3.12 以上（`uv run --script`）である。試験は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py tests/wiki/test_browse_server.py` で、すべて通っている（107 件、5 件は Linux だけの試験で飛ばす）。
