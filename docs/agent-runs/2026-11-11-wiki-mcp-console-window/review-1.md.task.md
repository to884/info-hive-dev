# レビューの目的

info-hive-wiki のイシュー #36「Windows で wiki の MCP サーバーに接続すると、ターミナル（コンソール）の画面が 1 つ起動する」の修正を、壊すつもりで見てほしい。

## 変更

- `info-hive-wiki/skills/info-hive/scripts/wiki_mcp_relay.py` の `spawn_server`: Windows の creationflags を `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` から `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` に置き換えた。サブモジュールの差分は `git -C info-hive-wiki diff f0a758f..HEAD` で見られる。
- 親リポジトリ: `tests/wiki/test_mcp_server.py` に `test_server_gets_no_new_console_on_windows` を足した。`tests/wiki/check_server_console.py`（新規、手で回す確認）、`tests/wiki/README.md`、`docs/adr/0012-wiki-owns-local-mcp-index-server.md`、`docs/research/wiki-mcp-server-2026-11-06.md`、`docs/research/wiki-mcp-server-2026-11-06/claude-spawn.json`。差分は `git diff a2e9d50..HEAD`。
- 版を 0.10.1 に上げ、CHANGELOG に書いた。

## 守るべき要件

1. Windows で、サーバーの起動で画面（既定のターミナルの窓。Windows Terminal への委譲を含む）が出ない。
2. 中継、入口、ホスト（Claude Code のデスクトップアプリと CLI）が終わってもサーバーは残り、次のセッションの中継が使う（ADR-0012）。
3. 版の違うサーバーを `stop_server`（psutil の terminate）で止められる。要求がないときにサーバーが自分で止まる。
4. 中継側の Ctrl+C などのコンソールのイベントが、サーバーに届いて止めることがない。
5. POSIX の振る舞いは変えない。

## 確かめた事実（この PC: Windows 11、既定のターミナルは Windows Terminal、Claude Code 2.1.321）

- 直す前: 窓の題が `...\environments-v2\wiki-mcp-server-<hash>\Scripts\python.exe` の Windows Terminal の窓が出た。server.json の pid（本体の base の python.exe）の子に conhost.exe が付いていた。
- 直した後: 新しい窓は出ず、本体の子に conhost.exe は付かない。`--ensure` の入口と中継が終わった後もサーバーは応答し、terminate で止まった。`check_claude_spawn.py` でも `claude -p` の終了後にサーバーが残った。`test_mcp_server.py` の 28 件が通った。新しい試験は直す前のコードで失敗した。

## 見てほしい点

- 要件 2〜4 を崩す筋（コンソールの寿命、CTRL_CLOSE_EVENT、ログオフ、ジョブ、親コンソールの閉じ方、venv のランチャーの振る舞いなど）。
- `wiki_mcp_common.py` の `uv` の呼び出しと `wiki_mcp_launch.py` の `run_relay` を変えなかった判断（それらはコンソールを持つプロセスから呼ばれる、という前提）が崩れる場合。例えば、ホストが中継をコンソールなしで起動する場合。
- 試験が要件を本当に確かめているか（conhost.exe の子の有無を代わりの指標にしている点など）。
- 文書（ADR、CHANGELOG）の記述が事実と食い違っていないか。
