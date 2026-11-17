# wiki の Codex 対応の検証

日付: 2026-11-17。実装の決定は [ADR-0031](../../adr/0031-wiki-codex-plugin.md)。配布物の版は 0.28.0。公開、マージ、通常のユーザー設定への導入は行っていない。

## 実機の結果

Windows と Codex CLI 0.166.0 で `tests/wiki/check_codex_plugin.py` を実行した。[機械が読む結果](smoke.json)も保存した。

- 一時的な `CODEX_HOME` と、日本語と空白を含むカタログ、プラグイン、利用者のプロジェクトのパスを使った。
- カタログの登録とインストールに成功した。スキル `wiki:info-hive` と 7 個の MCP ツールを認識した。
- Codex の `mcpServer/tool/call` を通じて `stats` と `query` を呼び、1 ページを数え、日本語のページを検索できた。
- 検索は埋め込みモデルの準備中に行い、`mode: lexical` で結果を得た。この試験は意味検索の精度を測るものではない。
- wiki の全ファイルを呼び出しの前後でバイト単位で比べ、変更がないことを確かめた。
- MCP のデータディレクトリも一時的な場所にし、既存の wiki のサーバーと分けた。モデルの推論のターンと Claude CLI は呼んでいない。

最初の調査では、互換形式の MCP 定義にある `${CLAUDE_PLUGIN_ROOT}`、`${PLUGIN_ROOT}`、`${CODEX_PLUGIN_ROOT}` は展開されず、その文字列を含むパスを uv が開こうとして失敗した。Codex の定義を `cwd: "."` と相対パスの引数に変えると接続できた。Claude Code の `.mcp.json` は変えていない。

## 回帰の試験

次の 6 ファイルについて、Python 3.12 の uv の環境で 109 件を実行し、失敗はなかった。1 件は Windows では動かさない POSIX の試験としてスキップした。

```powershell
uv run --python 3.12 --with pyyaml==6.0.3 --with cryptography python -X utf8 -B -m unittest tests/wiki/test_mcp_spawn_flags.py tests/wiki/test_python_version.py tests/wiki/test_uv_tls.py tests/wiki/test_codex_plugin.py tests/wiki/test_template_script_paths.py tests/wiki/test_help_command.py -q
```

このほか、`eval/scripts/test_init_base_dir.py` の 4 件と、`eval/check_encoding.py` の 59 ファイルの検査も通った。Codex の入口は UTF-8 モードを切り、標準入出力を cp932 に指定して起動しても、UTF-8 で操作手順を表示できることを試験した。Codex の配布契約と手順の試験は、親リポジトリの既存の Wiki MCP の CI にも追加した。配布カタログの試験は、marketplace のチェックアウトがある場合だけ行う。

## 確かめていない範囲

Codex のモデルにすべての操作を実行させる試験、macOS / Linux の Codex CLI、公開済みの GitHub カタログからの 0.28.0 の導入は行っていない。11 種類の操作は、既存の手順を表示する入口、全操作の個別のヘルプ、パスの検査を自動試験した。

利用者の指示に従い、`ask-claude` は使っていない。
