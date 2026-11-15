## 判定

**条件付きで採用可。確信度：高。** 「環境を用意できなかった理由を `launch.log` に残す」という目的に未達の経路がある。また、CI の行列の書式変更を黙って見逃す反例を確認した。

## 致命的・重大な欠陥

- **重大：TLS・依存解決以外の失敗では、元の原因が `launch.log` に残らない。**

  **反例：** uv が終了コード 2 と次の出力を返し続ける状態を、子プロセスだけ差し替えて再現した。

  ```text
  error: Failed to download Python
    cause: connection refused by proxy 127.0.0.1:9
  ```

  `prepare_script` は uv を3回呼び、入れ直しにも進む。`server.log` 相当の出力先には元の原因が残るが、`launch.log` 相当の記録は次の1件だけだった。

  ```text
  wiki_mcp_server.py の環境を用意できなかった: RuntimeError: wiki_mcp_server.py の環境を入れ直せなかった（uv sync --reinstall の終了コード 2）
  ```

  プロキシ接続拒否という原因は消失する。中継の `--ensure` と通常の serve は同じ `server_python` を通るため、どちらにも該当する。

  **根拠：** [wiki_mcp_common.py](/C:/Works/info-hive-dev/.claude/worktrees/wiki-py315/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:454) の `_run_uv` は出力を返すが、通常の失敗では `_uv_sync` が終了コードだけを上位へ渡す。647行目の例外にも元の出力がなく、632行目はその例外だけを記録する。[CHANGELOG.md](/C:/Works/info-hive-dev/.claude/worktrees/wiki-py315/info-hive-wiki/CHANGELOG.md:15) の「理由は、どれも `launch.log` に書く」と**食い違う**。

## 崩れる前提

- **「3.15 しかなければ uv が3.14を取得できる」**  
  `UV_PYTHON_DOWNLOADS=never`、オフライン、取得先への通信制限では成立しない。さらに `.mcp.json` は入口自体を `uv run --script` で起動するため、入口用の Python を選べない失敗は `prepare_script` の実行前に起こる。今回のログ処理や TLS の再試行には届かない。取得を禁止できることは [uv の公式仕様](https://docs.astral.sh/uv/concepts/python-versions/#disabling-automatic-python-downloads)とも一致する。実機再現は未実施。

- **「宣言を同じ範囲にすれば、その範囲の MCP 依存も CI で検証される」**  
  プラグインの行列は3.12と3.14だが、そこでインストールする直接依存は PyYAML、FastEmbed、sqlite-vec。MCP の完全な依存を指定する親の `.github/workflows/wiki-mcp.yml` は3.12固定である。行列と宣言の一致だけでは、上限付近で MCP 全体が起動する保証にはならない。

- **「診断文のどこかに解決失敗の句があれば、依存解決エラーである」**  
  パスにも同じ句を含められる。以下の軽微な問題の反例では、この前提が崩れる。

## 見落としと軽微な問題

- **軽微：CI の行列を部分的に読み落としても試験が通る。**  
  Windows 側だけを次の有効な YAML に変更し、Linux 側を現状のまま残した。

  ```yaml
  python:
    - '3.12'
    - '3.14'
    - '3.15'
  ```

  ファイルを変更せず、読み取り結果の差し替えで検証したところ、`tested_python_range()` は依然 `('3.12', '3.14')` を返し、宣言の試験も通った。[test_python_version.py](/C:/Works/info-hive-dev/.claude/worktrees/wiki-py315/tests/wiki/test_python_version.py:158) は1行形式だけを拾い、別の行列が1件でも残っていれば読み落としを検知しない。ADR-0025 の「新しい版を足すと試験が落ちる」は、この変更では成立しない。

- **軽微：パス中の句で、修復対象を `UvResolveError` と誤判定する。**  
  次の入力に対して `is_resolve_error()` が `True` を返すことを確認した。

  ```text
  error: Failed to read metadata from installed package at C:/cache/no solution found when resolving/pkg.dist-info/METADATA
  ```

  これはメタデータ読み取り失敗なのに、入れ直しを止める分類になる。根拠は `wiki_mcp_common.py` の387〜389行目の全文部分一致。**分類の誤りは再現済みだが、そのパスを使った実際の uv の修復成功までは未検証**。

- **軽微：追加した回帰試験が CI から呼ばれていない。**  
  `.github/workflows/wiki-mcp.yml` とプラグインのワークフローに `test_uv_tls.py` の実行はなく、同ファイルを含む一括実行もない。追加した依存解決失敗・記録回数の試験は、現状の CI では自動実行されない。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 対象コミットと読み取ったファイルが一致する | **一致**。親 HEAD は `fca89e8`、プラグイン HEAD は `1cdd88e`。対象ファイルに差分なし |
| PEP 723 を持つ8スクリプトの宣言が統一されている | **一致**。すべて `>=3.12,<3.15` |
| 現在の CI 行列から同じ範囲が算出される | **一致**。3.12〜3.14 |
| `python` で直接動く経路にも上限が付いた | **付いていない**。`wiki_text.py` の実行時検査は下限だけ |
| 版のガードと宣言の既存試験 | **3件成功** |
| 通常の uv 失敗の原因も `launch.log` に残る | **食い違い**。終了コードだけになる反例を再現 |
| uv 0.13.8 の実出力、別バージョンの文言、既存キャッシュからの更新 | **確かめられず**。実行環境に uv が見つからず、子プロセスを差し替えて検証した |

ファイルは変更していない。

## 崩せなかった点

- 提示された `No solution found when resolving dependencies` の出力では、通常経路・`force=True` とも `UvResolveError` になり、入れ直しに進まなかった。
- 上記の失敗は、`launch.log` 相当の記録が1件だけだった。入口の変更による二重記録は確認できなかった。
- 解決失敗の句を含まない通常のメタデータ障害は、入れ直し経路に進み、成功を返せた。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
