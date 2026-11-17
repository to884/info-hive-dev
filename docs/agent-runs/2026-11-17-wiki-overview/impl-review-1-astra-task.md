# 概要の段階1の実装の敵対的レビュー（第1回、Astra）

## 作業先と依頼

`C:/Works/info-hive-dev/.claude/worktrees/wiki-overview` を作業先にする。既定の cwd に頼らず、各コマンドにこのパスを明示する。
作者は設計第6版と ADR-0031 を承認し、段階1の実装を指示した。前のレビューでは Opus の利用上限を受けて作者が Astra を代替に指定しているため、同じ経路で実装を敵対的レビューする。

あなたが GPT-6 Astra（high）として実装を調べる。別のモデルやエージェントに再委譲しない。読み取り専用で、対象を修正せず、レビュー本文を最終回答として親へ返す。

## 正本と基準

- 承認済み設計：`docs/plans/wiki-overview-2026-11-17.md`（第6版）。ADR：`docs/adr/0031-wiki-page-overview-lives-in-a-sidecar.md`。
- プラグインは `info-hive-wiki/` の独立した Git リポジトリ。`feat/overview` を、SVG/Mermaid が入った最新の `origin/main`（`485e530`、wiki 0.27.0）に fast-forward してから実装した。プラグインの `git diff HEAD` が今回の変更である。新規ファイルは未追跡なので別途読む。
- 親は `feat/wiki-overview`、HEAD `7697aed`。親の `git diff HEAD` にテスト、CI、設計の修正と承認の記録がある。設計レビューの旧版の記録は対象ではない。
- リリースは段階2の表示と合わせる設計なので、現在は Unreleased に記録し、バージョンを上げていない。main へのマージや公開は行っていない。

## 実装の対象

プラグインの正本：

- `info-hive-wiki/skills/info-hive/scripts/wiki_overview.py`（新規、全体を読む）
- 同じディレクトリの `wiki_pages.py`（`page_text_sha256`）、`wiki_lint.py`（`overview_stale` / `overview_problems` と人向けの出力）、`wiki_mcp_common.py`（サーバーの版の入力）、`init_wiki.py`（`Page overviews` のマーカー）、`wiki_help.py`
- `info-hive-wiki/commands/overview.md`、`info-hive-wiki/skills/info-hive/references/overview-workflow.md`（新規）
- `info-hive-wiki/commands/lint.md`、`commands/upgrade.md`、`skills/info-hive/SKILL.md`、`skills/info-hive/assets/SCHEMA.md.template`、`skills/info-hive/references/lint-workflow.md`、`docs/commands.md`、`README.md`、`CHANGELOG.md`

開発用の正本：

- `tests/wiki/test_wiki_overview.py`（新規）
- `tests/wiki/test_wiki_lint.py`（既存の試験）、`test_uninitialized_wiki.py`、`test_page_set.py`、`test_mcp_server.py`、`test_help_command.py`、`test_template_script_paths.py`、`test_source_claims.py`、`test_browse.py`
- `.github/workflows/wiki-mcp.yml`

既存のプラグイン内 `eval/scripts/test_help.py` は、古いコマンド一覧の期待値に overview を1つ足した。新しい試験は親に置いている。

## 重点

1. 承認した6.5の状態表の優先順、ページ集合と識別子、NFC、曖昧な名前、ハッシュの衝突。状態表示・lint・保存・削除が同じ意味で動くか。
2. 下書き検査と組み立て後の再検査。参照と SVG フェンスの対応、図の順序、バッククォート、XML の末尾、DTD・実体、UTF-8、容量制限、本文を書き換えないこと。Markdown は実物の同梱パーサーで確かめる。
3. 書く前の経路の検査。綴り、シンボリックリンク、Windows の再解析点とジャンクション、ハードリンク、作業の記録の検査、片付けが専用の領分から出ないこと。明示された同時の差し替えと別名ジャンクションは既知の保証外として扱う。
4. 前の2件の修正。保存前の元ページの消失、読み取り失敗と非 UTF-8、同じ work_id の再試行、保存前に確定した page_changed、保存後にページを再読しないこと。置き換えに失敗したときやプロセスが止まったときの状態。
5. 常に JSON を返す CLI の終了コード、要求ファイルを消費する順番、既存の入口の初期化判定、利用者の引数をシェルに入れないコマンドの手順。
6. lint の未検査を0件と扱わないこと、MCP と CLI の一致、サーバーの版の入力、既存の検索・グラフ・統計・browse のページ集合を変えないこと。

保存後の作業フォルダー・一時ファイルの片付けが失敗した場合は、保存成功をエラーに戻さず、残りを次回 begin の片付けへ回す実装にした。この処理に反例があれば示す。

段階2の browse への差し込みは今回の実装範囲ではない。概要がまだ表示されないこと、電源断後の永続化を保証しないことは、明示された範囲として扱う。

## 確認済みの範囲

- 新しい試験は保存、破損、検査、読み取り失敗、孤立概要、symlink/hardlink/junction、別ボリューム、実際の子プロセスを置き換えの前後で止める試験を含む。
- Python 3.12 の、初期化判定、ページ集合、Python の版、概要の試験：114件、成功（3件は OS・依存などの条件でスキップ）。
- ヘルプ、ひな形、ソースの主張、lint、概要の試験：111件、成功。その後、容量制限とジャンクションの2件を追加した。
- MCP の `test_lint_matches_cli` は、古い概要と壊れた孤立概要がある場合も成功した。
- 既存の `eval/scripts` の116件は成功（4件スキップ）。UTF-8 の静的な検査59ファイルは成功。
- browse を含む213件は、旧版の期待値が1件だけ失敗した。origin/main に既にある SVG の `asset_dir` の期待値と同じに合わせ、そのクラス2件を動かして成功した。

Sonnet 5.5 によるコマンドの実行の測定は、Claude の利用上限（11月17日23:30日本時間に解除予定）が残っており、まだ行っていない。これを自動試験で確認済みと扱わない。

全テストを繰り返さず、疑わしい点に必要な小さな反例を確かめる。ネットワーク、公開、Git の状態変更、実機の電源断は不要である。
所定の「判定」「致命的・重大な欠陥」「崩れる前提」「見落としと軽微な問題」「検証した事実」「崩せなかった点」の順に日本語で報告する。
指摘には具体的な入力・操作順、正確な行番号、重大度と A/B/C/D の発生の度合いを付ける。推測と実測は区別し、修正案の作成は不要。
開始時、具体的な検証の進捗、完了時に親へ短く知らせる。
