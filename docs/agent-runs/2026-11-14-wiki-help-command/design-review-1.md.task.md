# 依頼: `/wiki:help [command]` の設計の敵対的レビュー

## 目的

Claude Code プラグイン `wiki`（`info-hive-wiki/`）のコマンド `/wiki:help` に、コマンド名を 1 つ受け取って、そのコマンドの詳しいヘルプを出す形を足す。設計は `docs/plans/wiki-help-command-2026-11-14.md` にある。実装の前に、この設計を壊してほしい。

作者が決めたこと（前提として扱い、覆す指摘はしなくてよいが、この前提が招く欠陥は挙げてよい）:

- 詳細は `info-hive-wiki/docs/commands.md` の該当する節をそのまま出す。ヘルプ専用の文章は書かない。
- 変更は 0.14.0 に含めてリリースする（main の `plugin.json` は 0.14.0 だが、タグとリリースはまだない）。

## 読むファイル

- `docs/plans/wiki-help-command-2026-11-14.md`（設計）
- `info-hive-wiki/commands/help.md`（今のコマンドの定義）
- `info-hive-wiki/skills/info-hive/scripts/wiki_help.py`（今のスクリプト）
- `info-hive-wiki/docs/commands.md`（詳細の出どころ）
- `info-hive-wiki/eval/scripts/test_help.py`（今の試験）
- `info-hive-wiki/commands/*.md`（ほかのコマンドの frontmatter）
- `tests/wiki/test_uninitialized_wiki.py` の `NO_WIKI` と `WIKI_PATTERN`（入口の分類の試験）
- 必要なら `info-hive-wiki/skills/info-hive/scripts/wiki_text.py`（`_fm_unquote`、`localize_argparse`）

## 特に見てほしい点

1. `commands/help.md` から `--command='<引数>'` で渡す方法は、Claude Code の `$ARGUMENTS` の置き換え、Bash（Git Bash）と PowerShell の両方で、意図どおりの 1 つの値になるか。エージェントが引数を言い換えたり、別の形で呼んだりする余地はないか。
2. 名前の正規化と照合で、取りこぼす入力や、誤って別のコマンドに当たる入力はないか。
3. 節の取り出し（見出しの正規表現、フェンスの扱い、次の `## ` までの範囲）が、今の `docs/commands.md` と、ありうる書き方で崩れないか。
4. リンクの書き換え（`file:///` の URI、`#frag`、インラインコードとフェンスの除外、リンクの文字の中のインラインコード）の欠陥。チャットでの表示で、`file:///` の宛先が使えないときの扱いは十分か。
5. 出力（Markdown と JSON）の形と、引数なしの一覧の後方互換。
6. 試験の計画の抜け（今の試験が通らなくなるもの、確かめていない振る舞い）。
7. 0.14.0 に含めることで起きる問題（文書、CHANGELOG、利用者への配布）。

## 出力

日本語で、指定の見出しの順に書く。ファイル名と行番号、または再現の手順を根拠に添える。
