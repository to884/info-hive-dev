# 2 回目のレビュー

前回の指摘を受けて、次のように直した。直し方が指摘を本当に塞いでいるか、新しい欠陥を入れていないかを、壊すつもりで見てほしい。

## 直したこと

- 重大の指摘（入口がコンソールなしで起動されると窓が出る）: `wiki_mcp_common.NO_WINDOW`（Windows では `CREATE_NO_WINDOW`、POSIX では 0）を作り、`wiki_mcp_common.py` の 5 か所の `subprocess.run`、`wiki_mcp_launch.run_relay`、`wiki_mcp_relay.spawn_server` に付けた。`spawn_server` は `Popen` の呼び出しを 1 つにし、`creationflags=(NO_WINDOW | CREATE_NEW_PROCESS_GROUP) if windows else 0`、`start_new_session=not windows` にした。
- 新しい試験 `tests/wiki/test_mcp_spawn_flags.py`: AST で、MCP の 4 つのスクリプトの `subprocess.*` の起動がすべて `creationflags` を持つこと、`DETACHED_PROCESS` を使わないこと。`spawn_server` の旗を差し替えた `Popen` で確かめる。
- 軽微 1: `tests/wiki/check_server_console.py` は窓の題を見ず、起動のあいだも 0.1 秒ごとに数える。`--entry detached` で、入口を base の python から `DETACHED_PROCESS` で起動する。
- 軽微 3: ADR-0012 に測った範囲（`claude -p` のセッションの終了まで、デスクトップアプリの終了は測っていない）を書いた。
- 軽微 4: `wiki_mcp_common.py` は `SERVER_FILES` に入るので、サーバーの版が変わる（旧 573213623c90e161、新 e87338645e6416c0）。CHANGELOG に、古いサーバーは更新後の最初の接続で入れ替わると書いた。
- 軽微 2（単体試験がコンソールの分離を見ていない）: 旗の差し替えの試験で、`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` であることを見るようにした。Ctrl+C や窓を閉じるイベントを起こす試験は足していない。

サブモジュールの差分は `git -C info-hive-wiki diff f0a758f..HEAD`、親リポジトリの差分は `git diff a2e9d50..HEAD`。

## 確かめた事実（Windows 11、Windows Terminal に委譲、Claude Code 2.1.321）

- 直す前、`--entry detached`: 窓が 4 つ出た。直した後、`--entry detached`: 3 回のうち 1 回で窓が 1 つ出た。同じ時刻に別のセッションの rag の OCR のワーカー（`uv run ... rag_ocr.py --worker`）が起動していた。残り 2 回は 0。プロセスの記録では、入口、uv、中継、サーバーの子はすべて自分の conhost.exe を持っていた。
- `--entry uv`: 窓は 0。入口と中継が終わった後もサーバーが応答し、terminate で止まった。
- `test_mcp_server.py`、`test_mcp_spawn_flags.py`、`test_uv_tls.py` の 43 件が通った（skip 1）。`check_claude_spawn.py` で、`claude -p` の終了後もサーバーが残った。

## 特に見てほしい点

- `run_relay` に `CREATE_NO_WINDOW` を付けたことで、中継が入口と別のコンソールになる。ホストが入口を止めたときに中継が残り続ける、標準入出力の受け渡しが崩れる、などの筋はないか。
- 3 回のうち 1 回の窓を、無関係のプロセスのものと見た判断は妥当か。
- AST の試験が見逃す起動の形（`os.system`、`os.startfile`、別名での import、別のスクリプトからの起動など）で、MCP の経路に実際にあるもの。
