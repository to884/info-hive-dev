# レビューの目的

`docs/plans/wiki-raw-size-in-stats-2026-11-11.md` は、`info-hive-wiki` の `/wiki:stats`（`wiki_stats.py` と MCP の `stats`）に、Raw の大きさの集計と閾値の警告を足す設計の案である。実装はまだない。この設計のまま実装すると壊れる点、既存の実装や設計書（ADR）と食い違う点、決め残しを探してほしい。

## 設計が果たすべきこと

- Raw の大きさ（ファイルの数とバイト数）を `/wiki:stats` で見られるようにする。
- 閾値を超えたら警告し、何が場所を取っているかを手を打てる単位で示す。
- info-hive はプラグインなので、開発用の PC に固有の値を仕様にしない。
- CLI の `wiki_stats.py --json` と MCP の `stats` は、同じ wiki に対して同じ結果を返す（`tests/wiki/test_mcp_server.py` の `test_stats_matches_cli_and_reports_index`）。
- 遅いドライブや大きな書庫を、利用者が意図せずに走査しない。
- 閲覧と集計で、wiki と Raw のファイルを変えない。

## 確かめてほしい点

1. Raw の場所の解決（設計の「1. Raw の場所」）。`info-hive-wiki/skills/info-hive/scripts/wiki_workspace.py`、`wiki_lint.py` の `missing_raw()`、`wiki_pages.py`、`commands/ingest.md` の `<RAW_ROOT>` の扱い、ADR-0008 と食い違わないか。ルートの検査（wiki そのもの、祖先、重なり）に抜けがないか。Windows と Linux の両方で考える。
2. 走査（「2. 測り方」）。`os.scandir()`、シンボリックリンク、ジャンクション、OneDrive などの再解析ポイント、項目の上限、`truncated` の判定に、誤りや決め残しがないか。Python は 3.10 以上で動く必要がある。
3. 出力の契約（「5. 出力」）。今ある `compute_stats()` のキー、MCP の `stats`、`tests/wiki/test_mcp_server.py`、`tests/wiki/check_commands_mcp.py` と食い違わないか。CLI と MCP で結果が変わる経路がないか。
4. 閾値と `advice`（「4. 閾値と警告」）。`scale_advice()` の今の形、lint の上限の引数と整合するか。
5. 「範囲に入れないこと」と「圧縮しない理由」に、事実の誤りがないか。
6. 「試験」の節で、上の点を確かめきれるか。

## 読むべきもの

- `docs/plans/wiki-raw-size-in-stats-2026-11-11.md`（対象）
- `info-hive-wiki/skills/info-hive/scripts/wiki_stats.py`、`wiki_workspace.py`、`wiki_lint.py`、`wiki_pages.py`、`wiki_mcp_server.py`、`wiki_mcp_common.py`、`wiki_fetch.py`
- `info-hive-wiki/commands/stats.md`、`commands/ingest.md`、`skills/info-hive/references/scaling-playbook.md`
- `docs/adr/0004-raw-holds-translated-web-pages.md`、`0008-numbered-workspace-layout.md`、`0012-wiki-owns-local-mcp-index-server.md`、`0013-rag-records-pdfs-by-absolute-path-and-hash.md`
- `tests/wiki/test_mcp_server.py`、`tests/workspace/`

応答は日本語で書く。
