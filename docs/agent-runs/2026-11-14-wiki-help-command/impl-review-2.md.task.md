# 依頼: `/wiki:help [command]` の 3 版目の実装の敵対的レビュー

## 目的

Claude Code プラグイン `wiki`（`info-hive-wiki/`）の `/wiki:help` に、コマンド名を 1 つ受け取って詳しいヘルプを出す形を足した。設計は `docs/plans/wiki-help-command-2026-11-14.md`（3 版目）にある。2 版目の実装のレビュー（`docs/agent-runs/2026-11-14-wiki-help-command/impl-review-1.md`、条件付きで採用可）の指摘を、設計の「レビューの指摘と直し方」の 2 つ目の表のとおりに直した。3 版目の実装を壊してほしい。

3 版目の主な変更:

- リンクの行き先を、`file:` の URI から、GitHub の導入した版のタグ（`https://github.com/<owner>/<repo>/blob/v<version>/...`）の URL に替えた（作者がデスクトップアプリで `file:` を開けないことを確かめ、選んだ）。
- 範囲の外の書き方を自前の正規表現で探すこと（`unsupported_markdown()`）をやめ、書き換えの前後を同梱の markdown-it（`wiki_pages.new_parser()`）で読み、リンクの宛先のほかが同じかを照らし合わせる（`verify_rewrite()`）。食い違えば、書き換えずに節をそのまま出して警告する。
- 節の見出しと範囲を、行の正規表現ではなくパーサーで読む（`find_doc_section()`）。

作者が決めたこと（前提として扱う。覆す指摘はしなくてよいが、この前提が招く欠陥は挙げてよい）:

- 詳細は `info-hive-wiki/docs/commands.md` の該当する節をそのまま出す。
- リンクは GitHub の導入した版のタグの URL にする。タグのない開発中の版で 404 になること、ネットが要ることは受け入れる。
- 変更は 0.14.0 に含めてリリースする。

## 読むもの

- 設計: `docs/plans/wiki-help-command-2026-11-14.md`
- 前のレビュー: `docs/agent-runs/2026-11-14-wiki-help-command/design-review-1.md`、`impl-review-1.md`
- プラグインの差分: `git -C info-hive-wiki diff origin/main..HEAD`（サブモジュールのブランチ `feature/help-command`）
- 親の差分: `git diff origin/main..HEAD`
- 主なファイル: `info-hive-wiki/skills/info-hive/scripts/wiki_help.py`、`info-hive-wiki/commands/help.md`、`info-hive-wiki/docs/commands.md`、`tests/wiki/test_help_command.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（`new_parser()`）

## 特に見てほしい点

1. 照らし合わせ（`verify_rewrite()`）が、書き換えの誤り（コードの例の改変、リンクの消失、宛先の誤り）を本当に見つけるか。前の木を「文書の全体を読んで、節の本文の行にある最上位のブロックのトークン」とする取り方の穴。照らし合わせが見逃す書き換えの誤りの反例。
2. 照らし合わせが、正しい書き換えを誤って食い違いとし、節をそのまま出してしまう書き方（今の文書と、ありうる書き方）。
3. `link_url()` の URL の組み立て（百分率符号化、フラグメント、`..`、ルートの外、画像の `?raw=true`、Windows のパス、ジャンクション）。`docs_base_url()` の `repository` と `version` の読み方。
4. パーサーで読む `find_doc_section()` の欠陥（見出しの文字の取り方、h1 で終わること、Setext の見出し、節の行の範囲）。
5. 試験が主張を本当に確かめているか（試験が本体と同じ読み方に頼って、本体の見落としを見落としていないか）。
6. 1 版目の致命と重大（シェルへの注入、対話のセッションでの展開）が閉じたままか。
7. 文書（`docs/commands.md`、README、CONTRIBUTING、CHANGELOG、設計）と実装の食い違い。

## 出力

日本語で、指定の見出しの順に書く。ファイル名と行番号、または再現の手順を根拠に添える。
