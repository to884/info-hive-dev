# info-hive-wiki#36 の修正の敵対的レビュー（2026-11-11）

Windows で wiki の MCP サーバーに接続すると、ターミナルの画面が 1 つ出る不具合の修正を、GPT-6.1 Sol（effort high）に 3 回レビューしてもらった。2 回目と 3 回目は、1 回目のセッションを続けて（`--resume`）頼んだ。

- 依頼: `review-1.md.task.md`、`review-2.md.task.md`、`review-3.md.task.md`。対象の差分は `submodule.diff`（info-hive-wiki）と `parent.diff`（このリポジトリ）
- 結果: `review-1.md`（条件付きで採用可、確信度 高）、`review-2.md`（却下、確信度 高）、`review-3.md`（採用可、確信度 中）

## 原因

中継はサーバーを `DETACHED_PROCESS` で起動していた。コンソールを持たない venv の `python.exe`（起動用）が本体の `python.exe` を子として起動するときに、本体に新しいコンソールが作られ、既定のターミナル（Windows Terminal）の窓が出ていた。窓の題はサーバーの venv の `Scripts\python.exe` のパスで、本体の子に `conhost.exe` が付いていた。

## 指摘と対応

| 回 | 指摘 | 重大度 | 対応 |
| --- | --- | --- | --- |
| 1 | ホストが入口をコンソールなしで起動すると、`uv` の呼び出しと `run_relay` でも窓が出る | 重大 | 入口と中継の子プロセスの起動に、窓を抑える指定を付けた（2 回目に直し方を改めた）。入口を `DETACHED_PROCESS` で起動すると、直す前は窓が 4 つ出た |
| 1 | 確認スクリプトが窓の題に頼り、起動の後しか見ない | 軽微 | 題を見ず、起動のあいだも 0.1 秒ごとに数える。`--entry detached` を足した |
| 1 | 単体試験がコンソールの分離を見ていない | 軽微 | `spawn_server` の旗を差し替えた `Popen` で確かめる試験を足した。Ctrl+C を起こす試験は足していない |
| 1 | ADR が、測っていないデスクトップアプリの終了まで含めて書いている | 軽微 | 測った範囲（`claude -p` のセッションの終了まで）に改めた |
| 1 | 更新しても、窓の出ている古いサーバーが入れ替わらない | 軽微 | 直す先の `wiki_mcp_common.py` はサーバーの版に入るので、版が変わる。開いたままのセッションの古い中継が古いサーバーを起動し直すことは、CHANGELOG に書いた |
| 2 | `run_relay` にいつも `CREATE_NO_WINDOW` を付けると、中継が別のコンソールに入り、親から受け取ったコンソールの標準出力と標準エラーに書けない（終了コード 120） | 重大 | 前提（子はいつも別のコンソールでよい）を改めた。子は、親がコンソールを持てば引き継ぎ（旗 0）、持たなければ `CREATE_NO_WINDOW`（`child_creationflags`）。サーバーだけはいつも別の窓のないコンソール（`server_creationflags`）。実際の入口で `--ensure` の出力をコンソールにすると、途中の版は 120、直した版は 0 |
| 2 | AST の試験が `creationflags` の有無しか見ず、`creationflags=0` でも通る | 軽微 | 2 つの関数の呼び出しを渡していることを見る。`server_creationflags` は `spawn_server` だけ |
| 2 | 確認スクリプトのパイプが詰まりうる。窓の持ち主と時刻を記録しない | 軽微 | 出力をファイルに書き、窓の持ち主の pid と名前、出た時刻を記録する |
| 2 | 途中の版で出た窓 1 件を、無関係のプロセスのものとした判断は推測 | 軽微 | ADR に「出どころは確かめていない」と書いた |
| 3 | 確認スクリプトを途中で止めると、試験のサーバーが残る | 軽微 | `finally` でサーバーを止める |

## 確かめたこと

- Windows 11（既定のターミナルは Windows Terminal）、Claude Code 2.1.321。
- `tests/wiki/check_server_console.py`: 直した版で、`--entry uv` 2 回、`--entry detached` 4 回、どれも窓は 0。入口と中継が終わった後もサーバーが応答し、terminate で止まった。
- `tests/wiki/check_claude_spawn.py`: `claude -p` の終了後もサーバーが残った。
- `test_mcp_server.py`、`test_mcp_spawn_flags.py`、`test_uv_tls.py` の 47 件が通った（skip 2）。新しい試験は、直す前のコードと、`child_creationflags` をいつも `CREATE_NO_WINDOW` にした変異で失敗した。
- WSL（Ubuntu 24.04）で `test_mcp_server.py` と `test_mcp_spawn_flags.py` の 36 件が通った（Windows だけの試験など skip 4）。POSIX の `spawn_server` の起動（新しいセッション）も、ここで通る。

## 確かめていないこと

- マーケットプレイスから入れた 0.10.1 での、デスクトップアプリの実際のセッション。
- デスクトップアプリそのものを終えたあとに、サーバーが残るか。
