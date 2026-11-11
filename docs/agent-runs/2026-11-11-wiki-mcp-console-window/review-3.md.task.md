# 3 回目のレビュー

2 回目の重大の指摘（`run_relay` に `CREATE_NO_WINDOW` を付けると、親のコンソールの標準ハンドルに書けない）を、前提から直した。サブモジュールの履歴は作り直したので、差分は `git -C info-hive-wiki diff f0a758f..HEAD`（コミット 9d793ea、8f1b9d0）、親リポジトリは `git diff a2e9d50..HEAD`。

## 直したこと

- `NO_WINDOW` の定数をやめ、`wiki_mcp_common` に 3 つの関数を作った。
  - `has_console()`: `GetConsoleProcessList(buf, 1) > 0`。
  - `child_creationflags()`: Windows でコンソールがあれば 0（引き継ぐ）、なければ `CREATE_NO_WINDOW`。common の 5 か所と `run_relay` が使う。
  - `server_creationflags()`: Windows では `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`。`spawn_server` だけが使う。サーバーの標準入出力は DEVNULL とログのファイル。
- `tests/wiki/test_mcp_spawn_flags.py`: AST で、起動がすべて 2 つの関数の呼び出しを `creationflags` に渡すこと（`creationflags=0` は失敗する）、`server_creationflags` は `wiki_mcp_relay.py` だけ。`DETACHED_PROCESS` と `CREATE_NO_WINDOW` の子で `has_console` が偽と真になること。窓のないコンソールを持つ python が、`CONOUT$` を標準出力にした子を `child_creationflags()` で起動して書けること。
- 軽微の指摘: `check_server_console.py` は出力をファイルに書き、窓の持ち主の pid と名前、出た時刻を記録する。0.1 秒より短い窓は見逃しうると書いた。ADR の窓 1 件は「出どころは確かめていない」と書いた。

## 確かめた事実（Windows 11、Claude Code 2.1.321）

- `child_creationflags` をいつも `CREATE_NO_WINDOW` にすると、引き継いだコンソールに書く試験は終了コード 120 で失敗した（変異の確認）。
- 実際の入口で、標準出力と標準エラーを `CONOUT$` にして `--ensure` を実行した。882f08f（定数の版）は終了コード 120、今の版は 0。
- `check_server_console.py`: `--entry uv` 2 回、`--entry detached` 3 回、どれも窓 0、サーバーは中継の後も残り、terminate で止まった。
- `test_mcp_server.py`、`test_mcp_spawn_flags.py`、`test_uv_tls.py` の 47 件が通った（skip 2）。`check_claude_spawn.py` で `claude -p` の終了後もサーバーが残った。

## 見てほしい点

- `has_console()` が誤る場合（標準ハンドルはあるがコンソールがない、`AttachConsole` されたコンソール、`FreeConsole` の後、疑似コンソール（ConPTY）の下など）と、そのときに窓が出るか、書けなくなるか。
- コンソールを引き継ぐ場合に、以前（変更前）と振る舞いが変わる点が残っていないか。
- 前回までの指摘で、まだ塞がっていないもの。
