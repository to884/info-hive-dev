# レビューの依頼: browse の画面に wiki のスコープを出す（3 版目の設計と実装）

## 目的

info-hive の wiki プラグイン（`info-hive-wiki`、Claude Code プラグイン `wiki`）の閲覧機能 `/wiki:browse` に、開いた wiki が「ユーザースコープの wiki」か「どのプロジェクトの wiki」かを出す。作者の依頼は「ユーザースコープなのかプロジェクトスコープなのかわかるようにして」である。

1 版目と 2 版目は、それぞれ 1 回目と 2 回目のレビューで却下された（`review-1.md`、`review-2.md`）。3 版目は、2 回目の指摘 2（指示のファイルの場所で決めていた）と指摘 3（使い回したときに記録のファイルからスコープを読んでいた）を原因の構造で直し、指摘 1 は理由を書いて採らなかった。経緯、採らなかった理由、決めたことは設計の文書にある。

この変更が守るべきこと:

1. 表示されるスコープと、起動の出力のスコープが、利用者を誤らせない（違うスコープを確信をもって出さない。画面に出ていないスコープを出力に書かない）。
2. 閲覧のスクリプトは読むだけで、wiki のファイルも wiki の外のファイルも書き換えない。閲覧のスクリプトが読んだ入力の実体を変えない（第 1 段階の設計の 6）。
3. 静的の書き出し（`build`）は、生成器が入れた絶対パスを出力に含めない（第 1 段階の設計の 5、`find_leaks`）。
4. 中核（`wiki_browse_core.Core`）は wiki の写しだけから描き、wiki の外を読まない（ADR-0010）。
5. 既存の閲覧の振る舞い（ナビゲーション、データの契約の版と世代の確かめ、サーバーの使い回しと停止、`--scope` を付けないときの画面）を壊さない。

## 読むもの

- 設計（3 版目）: `docs/plans/wiki-browse-scope-2026-11-12.md`
- これまでのレビュー: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-1.md`、`review-2.md`
- 実装の差分（main からの全体）: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-3-info-hive-wiki.diff`（サブモジュール `info-hive-wiki` の作業ツリーの差分）
- 試験の差分: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-3-tests.diff`
- 変更後のソース: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`browse_assets/style.css`、`browse_assets/app.js`、`info-hive-wiki/commands/browse.md`
- 前提の文書: `docs/plans/wiki-browse-stage1-2026-11-09.md`、`docs/adr/0008-numbered-workspace-layout.md`、`info-hive-wiki/skills/info-hive/SKILL.md` の「wiki を保存する範囲」の節、`info-hive-wiki/commands/init.md`

## 特に崩してほしい点

- 3 版目で、2 回目の指摘 2 と 3 の原因が本当に取り除かれたか。同じ形の欠陥が別の場所に移っただけになっていないか。
- 2 回目の指摘 1 を採らなかった判断の当否。この変更が新しく起こすか、広げるものかどうか。
- 手順 0 の規則（登録の内容で決め、食い違えば決めない）が、誤ったスコープを確信をもって出す、指示の書き方の具体例。
- 使い回したときに操作の口で聞くスコープと、画面の食い違い。前の版のサーバー、スコープなしのサーバー、起動と停止の競合を含む。
- 試験が、主張していることを本当に確かめているか。

実行環境は Windows 11、Python 3.12 以上（`uv run --script`）である。試験は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py tests/wiki/test_browse_server.py` で、すべて通っている（107 件、5 件は Linux だけの試験で飛ばす）。
