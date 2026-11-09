# wiki の MCP サーバーの試験と測定

`info-hive-wiki` の MCP サーバー（ADR-0012）と検索の基盤（ADR-0011）の試験と測定を置く。プラグインの本体には置かない。

| ファイル | 中身 |
| --- | --- |
| `test_wiki_index.py` | 検索の基盤（`wiki_index.py`）の試験。差分の更新、途中で止まったときのそろえ直し、Tantivy の commit のやり直し、fingerprint が変わったときの作り直し、書き手のロック、`index_chunks` の世代 |
| `test_mcp_server.py` | サーバーと中継の試験。トークンと Host ヘッダー、127.0.0.1 だけで待ち受けること、中継を 4 つ同時に起動してもサーバーが 1 つ、中継の終了後もサーバーが残ること、サーバーが止まった後や呼び出しの途中で止まったときの接続し直し、版の違うサーバーの入れ替え、要求がないときの停止。ツール `lint`、`stats`、`graph` が CLI の `--json` と同じ結果を返すこと |
| `test_wiki_lint.py` | lint の索引、出典、原本、タグの検査（0.7.0 の `index_type_mismatch`、`unresolved_sources`、`missing_raw`、`unknown_tags`）。標準ライブラリだけで動く |
| `test_uv_tls.py` | TLS を検査する社内ネットワークで uv が証明書を検証できないとき（info-hive-wiki#30）。`UV_SYSTEM_CERTS=true` での 1 回だけのやり直し、利用者の設定の尊重、入れ直しに進まないこと。自己署名の証明書の HTTPS の索引を手元に立て、入口が理由と対処を `logs/launch.log` に書いてすぐ止まることも確かめる（`--with cryptography` で動かす） |
| `run_mcp_gate.py`、`mcp_eval_search.py` | wiki の評価ゲート（`eval/retrieval/run_eval.py`）を新しい基盤で通す |
| `bench_mcp_latency.py` | 検索の速さ（今の CLI、中継経由の MCP、直接呼び出し） |
| `bench_mcp_startup.py` | 起動の速さ（入口から `initialize` と `tools/list` まで）。2 つの版のスクリプトを交互に起動して比べる。結果は `docs/research/wiki-mcp-startup-2026-11-07/` に置く |
| `measure_dense_threshold.py` | 意味の検索の距離の上限（`max_distance`）。評価セットの距離の分布と、上限を変えたときの成績。結果は `docs/research/wiki-dense-threshold-2026-11-07/` に置く |
| `check_claude_spawn.py` | Claude Code が中継とサーバーをどう起動し、セッションの後にサーバーが残るか（`claude -p` を 1 回実行する） |
| `check_commands_mcp.py` | コマンド（`/wiki:stats`、`/wiki:query`、`/wiki:lint`）がまず MCP のツールを使い、`.mcp.json` のないプラグインでは CLI に戻るか（`claude -p --plugin-dir` をコマンドの数だけ実行する。引数にコマンド名を渡すと、それだけを実行する） |
| `check_first_run_mcp.py` | 初めて使う人の最初のセッション。uv のキャッシュとデータの置き場所を空にして `claude -p` を実行し、サーバーの依存（約 1 GB）とモデル（約 530 MB）の取得のあいだにどう振る舞うかと、用意ができたあとの 2 回目のセッションを確かめる |
| `mcp_stdio.py` | 試験用の最小の stdio の MCP クライアント |

結果は、ことわりがなければ `docs/research/wiki-mcp-server-2026-11-06/` に置く。

## 動かし方

依存はサーバーのスクリプトの宣言と同じ版にそろえる。Windows では一時ディレクトリが遅いドライブにあると試験が遅くなるので、`TMP` を速いドライブに向けるとよい。

```bat
python -X utf8 -m unittest tests/wiki/test_wiki_lint.py -v
set DEPS=--with mcp==1.30.0 --with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0 --with fastembed==0.8.0 --with onnxruntime==1.31.1 --with pyyaml==6.0.3 --with psutil==7.2.2
uv run --python 3.12 %DEPS% python -X utf8 -m unittest tests/wiki/test_wiki_index.py -v
uv run --python 3.12 %DEPS% python -X utf8 -m unittest tests/wiki/test_mcp_server.py -v
uv run --python 3.12 --with cryptography python -X utf8 -m unittest tests/wiki/test_uv_tls.py -v
set INFO_HIVE_POC_DATA=C:\Works\info-hive-dev\.rag-poc-data
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/run_mcp_gate.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/bench_mcp_latency.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/measure_dense_threshold.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/check_claude_spawn.py
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/bench_mcp_startup.py 36a4089 work --rounds 7
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_commands_mcp.py
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_first_run_mcp.py
```

- `check_commands_mcp.py` と `check_first_run_mcp.py` は、`claude -p --plugin-dir` で手元の `info-hive-wiki` を読み込む。マーケットプレイスから `wiki@info-hive` を入れていても、`--plugin-dir` の側が優先され、その MCP のサーバーが使われる（Claude Code 2.1.316 で確かめた）。
- macOS と Linux では、`.github/workflows/wiki-mcp.yml`（手で起動するか、`info-hive-wiki` の参照か `tests/wiki/` を変えた PR で動く）が、lint、索引、サーバーの試験と、本物のモデルでの評価ゲートを動かす。

- 試験はテスト用の埋め込み（`INFO_HIVE_TEST_EMBEDDER=hash`）を使い、モデルを読み込まない。中継は `.mcp.json` と同じく `uv run --script` で起動するので、サーバーの依存を初めて取得するときは数分かかる。
- 評価ゲートと速さの測定は、本物のモデル（約 530 MB）を `$INFO_HIVE_POC_DATA/wiki-mcp-20261106/data/models/` に取得して使う。
