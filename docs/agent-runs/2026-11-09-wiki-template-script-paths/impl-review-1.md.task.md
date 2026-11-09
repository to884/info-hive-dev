対象は Claude Code プラグイン wiki（info-hive-wiki）の 0.9.1（パッチ版）の変更である。

目的:
- `skills/info-hive/scripts/init_wiki.py` は `assets/` のひな形を、wiki を使う側のプロジェクトに `wiki/SCHEMA.md` と `wiki/graph/README.md` として書き出す。
- 0.9.0 のひな形は、コマンドの例でスクリプトを `scripts/wiki_graph_extract.py`（スキルのディレクトリから見たパス）と `skills/info-hive/scripts/wiki_search.py`（プラグインのルートから見たパス）で書いていて、利用者のプロジェクトのどこから実行しても解決しなかった。
- 直し方として、`<skill-root>/scripts/...` と書き、同じファイルの中で `<skill-root>` の意味（インストールした info-hive スキルのディレクトリ。Claude Code では `${CLAUDE_PLUGIN_ROOT}/skills/info-hive`）を説明することにした。
  - `${CLAUDE_PLUGIN_ROOT}` をそのまま書かない理由: プラグインのコマンドの本文でだけ展開され、書き出したファイルの中では展開されず、エージェントの Bash でも空だった（このセッションで確かめた）。Codex などのホストには変数がない。
  - 初期化のときに実際の絶対パスを書き込まない理由: プラグインのキャッシュのパスは版ごとに変わり、wiki は git で共有されうるので、マシン固有のパスを残したくない。
  - `<skill-root>` は SKILL.md と references/evolution-workflow.md ですでに使っている書き方である。
- 既存の wiki の `SCHEMA.md` と `graph/README.md` は書き換えない。`--upgrade` の検出は見出し（`## Retrieval` など）と特定の行で行うので、本文の変更は案内されない。これは意図どおりで CHANGELOG に書いた。
- `references/*.md` と `SKILL.md` にも `scripts/...` の書き方があるが、スキルを読み込んだ状態で読まれ、スキルのディレクトリからの相対であることが graph-workflow.md に書いてあるので、このパッチでは扱わない（範囲外）。

レビューしてほしいこと:
- 書き出したファイルを読む利用者とエージェントが、正しくスクリプトを見つけて実行できるか。説明の文は正確か、誤解を招かないか。
- ひな形の中に、直し漏れ（スクリプトのパスや、解決しない別の書き方）がないか。
- `wiki/` の扱い（プロジェクトのルートから実行する前提）に破綻がないか。
- 試験 `tests/wiki/test_template_script_paths.py`（開発リポジトリ側。絶対パスで渡す）が、目的の性質を実際に確かめているか。素通りする穴はないか。
- CHANGELOG の記述と版（0.9.1、パッチ版）が妥当か。
- `init_wiki.py --upgrade` の検出（SCHEMA_SECTION_MARKERS）を壊していないか。
