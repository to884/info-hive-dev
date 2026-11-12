# レビューの依頼: browse の画面に wiki のスコープを出す（2 版目の設計と実装）

## 目的

info-hive の wiki プラグイン（`info-hive-wiki`、Claude Code プラグイン `wiki`）の閲覧機能 `/wiki:browse` に、開いた wiki が「ユーザースコープの wiki」か「どのプロジェクトの wiki」かを出す。作者の依頼は「ユーザースコープなのかプロジェクトスコープなのかわかるようにして」である。

1 版目（スクリプトが wiki の周りのファイルからスコープを推し量る）は、1 回目のレビュー（`docs/agent-runs/2026-11-12-wiki-browse-scope/review-1.md`）で却下された。2 版目は、指摘を原因の構造で分け、スコープを wiki を選んだ側（`/wiki:browse` のコマンド）が `--scope` で渡し、スクリプトは何も推し量らない設計に変えた。起動の出力は、画面を描くサーバーが記録したスコープだけを書く。経緯と決めたことは設計の文書にある。

この変更が守るべきこと:

1. 表示されるスコープと、起動の出力のスコープが、利用者を誤らせない（違うスコープを確信をもって出さない。画面に出ていないスコープを出力に書かない）。
2. 閲覧は読むだけで、wiki のファイルも wiki の外のファイルも書き換えない。閲覧が読んだ入力の実体を変えない（第 1 段階の設計の 6）。
3. 静的の書き出し（`build`）は、生成器が入れた絶対パスを出力に含めない（第 1 段階の設計の 5、`find_leaks`）。
4. 中核（`wiki_browse_core.Core`）は wiki の写しだけから描き、wiki の外を読まない（ADR-0010）。
5. 既存の閲覧の振る舞い（ナビゲーション、データの契約の版と世代の確かめ、サーバーの使い回しと停止、`--scope` を付けないときの画面）を壊さない。

## 読むもの

- 設計（2 版目）: `docs/plans/wiki-browse-scope-2026-11-12.md`
- 1 回目のレビュー: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-1.md`
- 実装の差分（main からの全体）: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-2-info-hive-wiki.diff`（サブモジュール `info-hive-wiki` の作業ツリーの差分）
- 試験の差分: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-2-tests.diff`
- 変更後のソース: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`browse_assets/style.css`、`browse_assets/app.js`、`info-hive-wiki/commands/browse.md`
- 前提の文書: `docs/plans/wiki-browse-stage1-2026-11-09.md`、`docs/adr/0008-numbered-workspace-layout.md`、`docs/adr/0010-*`、`info-hive-wiki/skills/info-hive/SKILL.md` の「wiki を保存する範囲」の節、`info-hive-wiki/commands/init.md`

## 特に崩してほしい点

- 2 版目の構造（スコープを呼び出し元が渡す）で、1 回目の指摘の原因が本当に取り除かれたか。同じ形の欠陥が、別の場所に移っただけになっていないか。
- コマンドの手順 0 の表（どこで見つけたか → スコープ）が、誤ったスコープを確信をもって出す場合。特に、ユーザーがパスを明示したとき、プロジェクトの指示とグローバルな指示が同じ wiki を指すとき、作業領域の設定と指示が食い違うとき。
- 起動の出力と画面の食い違い（新しく起動、使い回し、前の版のサーバー、スコープなしのサーバー、記録が壊れているとき、起動と停止が競合するとき）。
- `--scope-name` の確かめの抜け（記録の書き込み、HTML、題名、絶対パスの検査）。
- 試験が、主張していることを本当に確かめているか。

実行環境は Windows 11、Python 3.12 以上（`uv run --script`）である。試験は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py tests/wiki/test_browse_server.py` で、すべて通っている（106 件、5 件は Linux だけの試験で飛ばす）。
