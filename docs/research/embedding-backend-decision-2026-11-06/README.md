# 統一の決定のための追加測定（2026-11-06）

[統一の測定](../embedding-backend-unification-2026-11-05.html)が推した組（案 A）と wiki の MCP サーバー（案 B）について、決定に足りなかった点を E1〜E11 で測った結果である。読むのは [レポート](../embedding-backend-decision-2026-11-06.html) でよい。レポートの数値は、すべてこのフォルダーの JSON から生成している。

## ファイル

| ファイル | 測定 | 作ったスクリプト |
| --- | --- | --- |
| `onnx-distribution.json` | E9: 公開版の ONNX の取得、sha256、ライセンス、出力の一致 | `onnx_distribution.py` |
| `wiki-gate.json` | E8: wiki の評価ゲート（e5、R-130、R-130 + Sudachi）と `max_distance` の較正 | `wiki_gate.py`、`wiki_search_variant.py` |
| `fusion-sweep.json` | E1: 保存済みの順位での融合の掃引 | `fusion_sweep.py` |
| `wiki-reembed.json` | E7: 長さの区間ごとの埋め込みの時間と、wiki 規模の再埋め込みの推定 | `wiki_reembed.py` |
| `wiki-reembed-check.json` | E7: 無作為の 1,000 行での推定の確かめ | `reembed_check.py` |
| `fusion-deep.json` | E2: 全量で候補数 400、800 と、スコアの正規化による融合 | `fusion_deep.py` |
| `db-knobs-full.json` | E3: 全量での usearch と FAISS IVF_SQ8 のつまみ | `db_knobs_full.py` |
| `generation-filter.json` | E4: 世代の絞り込みと削除の費用 | `generation_filter.py` |
| `write-safety.json` | E5: Windows での usearch と Tantivy の書き込み（a〜d、d2） | `write_safety.py` |
| `tantivy-commit-retry.json` | E5 の補足: Tantivy の commit の失敗と rollback からの回復 | `tantivy_commit_retry.py` |
| `server-memory.json` | E6: 常駐するサーバーのメモリ | `server_memory.py` |
| `mcp-relay.json` | E10: 127.0.0.1 の MCP サーバーと stdio の中継の試作（ログあり、SSE） | `mcp_relay_probe.py`、`mcp_probe/` |
| `mcp-relay-quiet.json`、`mcp-relay-quiet-json.json` | E10 の測り直し: ログなし、ログなしで JSON の応答 | 同上（`PROBE_LOG_LEVEL`、`PROBE_JSON_RESPONSE`、`PROBE_OUT`） |
| `claude-job-check.json` | E10 の補足: Claude Code（CLI）が stdio の MCP サーバーをジョブに入れるか | `claude_job_check.py`、`mcp_probe/job_check_server.py` |
| `decision-scores.json` | E11: 最終の採点と、推奨が覆る条件の判定 | `decision_summary.py` |

スクリプトはすべて `poc/rag/decision/` にある。HTML は `build_decision_report.py` が作る。各 JSON の `env` に、ライブラリの版、スレッド数、各リポジトリの commit、データの場所を記録している。

## 再現の手順

統一の測定の作業データ（`unification-20261105/`）と、全量・natural のデータが要る。置き場所は環境変数 `INFO_HIVE_POC_DATA` で渡す。この測定では `C:\Works\info-hive-dev\.rag-poc-data` を使った。

```bat
set INFO_HIVE_POC_DATA=C:\Works\info-hive-dev\.rag-poc-data
set PY=%INFO_HIVE_POC_DATA%\unification-20261105\venv\Scripts\python.exe
cd poc\rag\decision
%PY% -X utf8 onnx_distribution.py
%PY% -X utf8 wiki_gate.py
%PY% -X utf8 fusion_sweep.py
%PY% -X utf8 wiki_reembed.py
%PY% -X utf8 reembed_check.py
%PY% -X utf8 fusion_deep.py
%PY% -X utf8 db_knobs_full.py
%PY% -X utf8 generation_filter.py
%PY% -X utf8 write_safety.py
%PY% -X utf8 write_safety.py --add-d2
%PY% -X utf8 tantivy_commit_retry.py
%PY% -X utf8 server_memory.py
%PY% -X utf8 wiki_gate.py --add r130-tantivy
set MPY=%INFO_HIVE_POC_DATA%\decision-20261106\mcp-venv\Scripts\python.exe
%MPY% -X utf8 mcp_relay_probe.py
set PROBE_LOG_LEVEL=WARNING& set PROBE_OUT=mcp-relay-quiet.json& %MPY% -X utf8 mcp_relay_probe.py
set PROBE_JSON_RESPONSE=1& set PROBE_OUT=mcp-relay-quiet-json.json& %MPY% -X utf8 mcp_relay_probe.py
%PY% -X utf8 claude_job_check.py
%PY% -X utf8 decision_summary.py
%PY% -X utf8 build_decision_report.py
```

- 時間を測る測定は直列に動かした。CPU は 4 スレッドに制限している（`common.limit_threads`）。
- E10 は mcp 1.30.0、uvicorn、filelock、psutil、pywin32 を入れた別の venv（`decision-20261106\mcp-venv`）で動かす。
- 作業データは `$INFO_HIVE_POC_DATA/decision-20261106/` に書く。E3 は usearch の索引を 3 つ作り直すので、1 時間ほどかかる。

## 計画との違い

- レポートの CSS は、`poc/rag/unification/build_report.py` の `<style>` を実行時に取り出して使った。計画では CSS を定数に出す小さなリファクタリングをする予定だったが、旧レポートを作り直す必要がなくなるので、旧スクリプトには手を入れなかった。
- E5 に (d2)（同じプロセスの読み手）と `tantivy_commit_retry.py` を足した。(d) で Tantivy の commit が失敗したので、案 B の形（索引をサーバーのプロセスだけが開く）でも起きるか、回復できるかを確かめるためである。
- E10 に「中継が終わってもサーバーが残るか」の判定を足した。最初の実行でサーバーが中継とともに止まったためで、起動の方式（子プロセス、`CREATE_BREAKAWAY_FROM_JOB`、WMI）を比べた。
- 2026-11-06 の判断を受けて 3 つを足した。E8 に案 2（語彙のエンジンを Tantivy にし、トークンは wiki の bigram のまま）の構成 `r130-tantivy`、E10 にログなしと JSON の応答での測り直し、Claude Code（CLI）がサーバーをジョブに入れるかの確認である。`claude_job_check.py` は `claude -p` を 1 回実行するので、モデルの呼び出しが 1 回分かかる。
- E11 の E6 の判定は、計画の停止の規則（usearch が上限を超え、かつ FAISS が収まるときだけ索引を替える）に合わせて直した。最初の版は usearch が上限を超えただけで覆ったと判定していた。

## 測り直したもの

- E2 と E4 は、最初の実行で 1 つ目の設定だけを冷えた状態（メモリ写像の読み込み前）で測っていた。全体を 1 巡して温めてから測るように直し、測り直した。
- E5 は、最初の版の読み書きのロックが読み手を優先していたため、検索が途切れずに続くと書き手がロックを取れず、6 時間止まった。書き手を優先する形に直して測り直した。
- E10 は、venv の `python.exe` が本体を子プロセスとして起動するため、サーバーの pid の確かめ方と重複の数え方を直した。
- E3 の既存の索引の再現は、dense の p95 が 32.2 ms で、統一の測定の 41.1 ms から ±10% を外れた。統一の測定は GPU の埋め込みと並べて測っていたので、今回のほうが速く出たと考える。動作点の規則は変えていない。
