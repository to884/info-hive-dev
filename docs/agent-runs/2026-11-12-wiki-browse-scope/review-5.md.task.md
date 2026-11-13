# レビューの依頼: browse の画面に wiki のスコープを出す（5 版目の設計と実装）

## 目的

info-hive の wiki プラグイン（`info-hive-wiki`、Claude Code プラグイン `wiki`）の閲覧機能 `/wiki:browse` に、開いた wiki が「ユーザースコープの wiki」か「プロジェクトの wiki」かを出す。作者の依頼は「ユーザースコープなのかプロジェクトスコープなのかわかるようにして」である。

1〜4 版目は、それぞれ 1〜4 回目のレビューで却下された（`review-1.md`〜`review-4.md`）。4 回目の指摘は、`--scope project` で起動して最初の組み立てに失敗し、画面が 503 でスコープを出さないあいだも、起動の出力と操作の口（`control/status`）が `scope: "project"` を答える、というものだった。5 版目は、出力の `scope` の意味を「そのサーバーが wiki のページに描くスコープ」と定め直し、守ることの 1 を「出力と違うスコープのページを描かない」にした。最初の組み立てに失敗したあいだの振る舞い（503 でスコープの表示がなく、操作の口は起動したときのスコープを答え、組み立てられたらそのスコープを描く）を試験で固定した。経緯、採らなかった理由、決めたことは設計の文書にある。

この変更が守るべきこと:

1. 出力と違うスコープのページを描かない（起動の出力の `scope` は、URL の先のサーバーが wiki のページに描くスコープである。違うスコープを確信をもって出さない）。
2. 閲覧のスクリプトは読むだけで、wiki のファイルも wiki の外のファイルも書き換えない。閲覧のスクリプトが読んだ入力の実体を変えない（第 1 段階の設計の 6）。
3. 静的の書き出し（`build`）は、生成器が入れた絶対パスを出力に含めない（第 1 段階の設計の 5、`find_leaks`）。
4. 中核（`wiki_browse_core.Core`）は wiki の写しだけから描き、wiki の外を読まない（ADR-0010）。
5. 既存の閲覧の振る舞い（ナビゲーション、データの契約の版と世代の確かめ、サーバーの使い回しと停止、`--scope` を付けないときの画面）を壊さない。

## 読むもの

- 設計（5 版目）: `docs/plans/wiki-browse-scope-2026-11-12.md`
- これまでのレビュー: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-1.md`、`review-2.md`、`review-3.md`、`review-4.md`
- 実装の差分（main からの全体）: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-5-info-hive-wiki.diff`（サブモジュール `info-hive-wiki` の作業ツリーの差分）
- 試験の差分: `docs/agent-runs/2026-11-12-wiki-browse-scope/review-5-tests.diff`
- 変更後のソース: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`browse_assets/style.css`、`browse_assets/app.js`、`info-hive-wiki/commands/browse.md`
- 前提の文書: `docs/plans/wiki-browse-stage1-2026-11-09.md`、`docs/adr/0008-numbered-workspace-layout.md`、`info-hive-wiki/skills/info-hive/SKILL.md` の「wiki を保存する範囲」の節、`info-hive-wiki/commands/init.md`

## 特に崩してほしい点

- 4 版目までの要件の言い方（「画面に出ていないスコープを出力に書かない」）を 5 版目で変えたことが、要件のすり替え（守るべきことを弱めただけ）になっていないか。作者の依頼（ユーザースコープかプロジェクトかを見分ける）と、利用者が出力や画面から受け取る意味に照らして、言い直した要件で利用者が誤る場合がないか。
- 5 版目の要件 1（出力と違うスコープのページを描かない）を破る経路。最初の組み立ての失敗、組み立て直し、使い回し、停止との競合、前の版のサーバー、記録の書き換えを含む。
- 1〜4 回目で崩せなかった点（共有のユーザースコープの wiki、指示と設定の食い違い、設定を読む経路を増やさないこと、使い回したときにサーバー自身の答えを書くこと、名前をやめたこと）が、5 版目の変更で崩れていないか。
- 手順 0 の規則（登録の内容で決め、設定は設定で見つけたときだけ使い、食い違えば決めない）が、誤ったスコープを確信をもって出す、指示の書き方の具体例。
- 試験が、主張していることを本当に確かめているか。特に、最初の組み立ての失敗のあいだの振る舞いを固定した試験。

実行環境は Windows 11、Python 3.12 以上（`uv run --script`）である。試験は `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_browse.py tests/wiki/test_browse_server.py` で、すべて通っている（105 件、5 件は Linux だけの試験で飛ばす）。
