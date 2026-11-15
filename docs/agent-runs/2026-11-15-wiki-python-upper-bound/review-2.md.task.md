# 依頼: 1 回目の指摘を直したあとの再レビュー

1 回目の指摘を、次のように直した。プラグインのコミット 050def7（`git -C info-hive-wiki log -1`）と、親の最新のコミットである。

- 重大（TLS と依存の解決のほかの失敗では、元の原因が launch.log に残らない）: 原因は、uv の失敗を上に伝えるときに、出力を捨てて終了コードだけを渡していたこと。`_uv_sync_result` が終了コードと最後の uv の出力を返し、`_prepare_script` の入れ直しの失敗の例外に、`uv_error_summary`（`error:`、`cause:`、`hint:` の行）を添える。`prepare_script` がそれを launch.log に書く。
- 前提（3.15 しかなく、uv が Python を取れない環境）: ADR-0025 の影響と、README のトラブルシューティングに、範囲の Python を入れる手順を書いた。CHANGELOG にも書いた。
- 前提（プラグインの CI の行列では、MCP サーバーの依存を範囲の版で試していない）: `tests/wiki/check_script_python_range.py` を足し、宣言の範囲のすべての minor の版で、uv で動くすべてのスクリプトに `uv sync --script` をかける。`wiki-mcp.yml` で流す。手元の Windows で 3.12、3.13、3.14 の 24 通りが通った。
- 軽微（行列の読み落とし）: `matrix:` の下の `python:` を、1 行の並びと続く行の並びの両方で読み、読めないものが 1 つでもあれば落とす。
- 軽微（パスに含まれた句で誤判定）: 依存の解決の失敗は、行の頭の `error: no solution found when resolving` でだけ見分ける。
- 軽微（試験が CI で流れていない）: `test_uv_tls.py` を `wiki-mcp.yml` で流す。

同じ観点で、もう一度崩してほしい。
