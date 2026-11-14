# 依頼: `/wiki:help [command]` の実装（と 2 版目の設計）の敵対的レビュー

## 目的

Claude Code プラグイン `wiki`（`info-hive-wiki/`）のコマンド `/wiki:help` に、コマンド名を 1 つ受け取って、そのコマンドの詳しいヘルプを出す形を足した。設計は `docs/plans/wiki-help-command-2026-11-14.md`（2 版目）にある。1 版目の設計のレビュー（`docs/agent-runs/2026-11-14-wiki-help-command/design-review-1.md`）は却下で、2 版目は指摘を「崩れた前提」ごとに直した（設計の「レビューの指摘と直し方」）。実装と 2 版目の設計を壊してほしい。

作者が決めたこと（前提として扱う。覆す指摘はしなくてよいが、この前提が招く欠陥は挙げてよい）:

- 詳細は `info-hive-wiki/docs/commands.md` の該当する節をそのまま出す。ヘルプ専用の文章は書かない。
- 変更は 0.14.0 に含めてリリースする（main の `plugin.json` は 0.14.0 だが、タグとリリースはまだない）。

## 読むもの

- 設計: `docs/plans/wiki-help-command-2026-11-14.md`
- 1 版目のレビュー: `docs/agent-runs/2026-11-14-wiki-help-command/design-review-1.md`
- 差分: プラグインはサブモジュール `info-hive-wiki/` の作業ツリー（`git -C info-hive-wiki diff`）。親は `git diff` と未追跡のファイル（`tests/wiki/test_help_command.py`、`docs/plans/wiki-help-command-2026-11-14.md`）。
- 変えたファイル: `info-hive-wiki/commands/help.md`、`info-hive-wiki/skills/info-hive/scripts/wiki_help.py`、`info-hive-wiki/docs/commands.md`、`info-hive-wiki/README.md`、`info-hive-wiki/CONTRIBUTING.md`、`info-hive-wiki/CHANGELOG.md`、`tests/wiki/test_help_command.py`、`tests/wiki/README.md`、`tests/wiki/test_uninitialized_wiki.py`、`.github/workflows/wiki-mcp.yml`

## 特に見てほしい点

1. 1 版目の致命（引数のシェルへの注入）と重大（対話のセッションでの `/wiki:help /wiki:query` の展開）が、構造として閉じたか。`commands/help.md` の 4 段の手順に、エージェントが利用者の文字列をシェルに入れる余地が残っていないか。Git Bash のパスの書き換えに当たる値が残っていないか。
2. 「扱う Markdown の範囲」を決めて試験で守らせる方針（設計の 6）が、範囲の外の書き方を取りこぼさずに検出できるか。範囲の中なのに誤って書き換える、または検出する書き方はないか。
3. `file:` の URI（フラグメントを捨てる）の欠陥。Windows の UNC パス、ジャンクション、8.3 の短い名前、日本語や空白を含むパス。
4. 試験（`tests/wiki/test_help_command.py`）が、主張していることを本当に確かめているか。見落とした振る舞い。
5. 文書（`docs/commands.md`、README、CONTRIBUTING、CHANGELOG）の記述と実装の食い違い。
6. 引数なしの一覧と、`--json` の一覧の後方互換。

## 出力

日本語で、指定の見出しの順に書く。ファイル名と行番号、または再現の手順を根拠に添える。
