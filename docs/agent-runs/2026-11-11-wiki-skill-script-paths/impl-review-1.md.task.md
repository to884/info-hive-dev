対象は Claude Code プラグイン wiki（info-hive-wiki）の 0.9.3（パッチ版）の変更である。差分は be117ad..HEAD。

背景:
- 0.9.1 で、`init_wiki.py` が書き出すひな形（`assets/SCHEMA.md.template`、`assets/graph_README.md.template`）のスクリプトを `"<skill-root>/scripts/..."` にそろえた。
- 今回は、スキルの `skills/info-hive/SKILL.md` と `skills/info-hive/references/*.md` のコマンドの例を同じ書き方にそろえた。今までは `scripts/...`、`skills/info-hive/scripts/...`、`${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/...`、`<プラグインのパス>/skills/info-hive/scripts/...`、名前だけ（`wiki_mcp_launch.py`）が混ざっていた。

決めた規則:
- 実行するコマンドのスクリプトは `"<skill-root>/scripts/<名前>.py"`（`"` で囲む）。
- `<skill-root>` の定義は SKILL.md の「## スクリプトのパス」に 1 か所。コマンドのある各リファレンスには、そこを指す 1 行を足した。`references/graph-workflow.md` の古い説明（`${CLAUDE_PLUGIN_ROOT}` で呼ぶ）は書き換えた。
- 文の中でスキルの中のファイルを指す `scripts/wiki_pages.py` や `references/...` は、スキルのディレクトリから見たパスとして残す（SKILL.md に明記）。
- JSON の `argv` の例は `<skill-root>/scripts/...` にし、シェルを通さないので絶対パスに置き換えると書いた。
- `eval/decisions/run_eval.py` はスキルではなくリポジトリにあるので、リポジトリのルートで実行すると書いた。
- `commands/*.md` は `${CLAUDE_PLUGIN_ROOT}` のまま（そこでは展開される）。
- 範囲外: リポジトリの README.md と docs/*.md、`--wiki`/`wiki/` の引数の書き方、パスに `$` を含む場合。

レビューしてほしいこと:
- SKILL.md とリファレンスの中に、直し漏れ（実行するのに解決しないスクリプトの書き方）がないか。コードブロックの中も文の中も。
- 規則の説明（SKILL.md の「スクリプトのパス」）が正確か。エージェントが `<skill-root>` を正しく決められるか。誤解を招く書き方はないか。
- 一括の書き換えで、文の意味が壊れた箇所（引用符の入れ子、表、インラインコードの中の `"`、行末の `\` など）がないか。
- 開発リポジトリの試験 `C:/Works/info-hive-dev/.claude/worktrees/wiki-template-script-paths-733553/tests/wiki/test_template_script_paths.py` の `SkillDocsScriptPathTests` が、目的の性質を確かめているか。素通りする穴（検出の正規表現が拾わないコマンドの形など）はないか。
- CHANGELOG の 0.9.3 の記述が変更と合っているか。パッチ版でよいか。
