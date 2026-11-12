# 目的

rag プラグイン（サブモジュール `info-hive-rag/`）の `read_pdf`（`info-hive-rag/scripts/rag_index.py`）は、ファイルの先頭がちょうど `%PDF-` でないと拒んでいた。検証データの 2 件（先頭が `\n%PDF-1.5`）が、PDFium では開けるのに失敗した。

変更は、`%PDF-` が先頭から 1024 バイト目までに始まれば受け付けるもの。差分は `C:/UserData/toshiki/Temp/claude/14ba59b7103758f5/f0177b65-5f2a-4ef0-affc-509384f53d47/scratchpad/change.diff`（親リポジトリとサブモジュールの両方）にある。

確かめた事実（作者側）:
- pypdfium2 5.14.0 / PDFium 156 で、作った PDF に前置きを付けると、1024 バイトまで（中身は改行、空白、NUL、任意の文字のどれでも）開け、1025 バイトでは `Data format error` になった。
- 実データの 2 件は、直した `read_pdf` と `extract_pages`（OCR なし）で全ページがテキストとして抽出できた。
- 単体試験 67 件（tests/rag/test_jobs.py、test_indexes.py、test_extraction.py）が通った。

判断してほしい点:
1. 判定の境界（`data.find(b"%PDF-", 0, 1024 + 5)`）が PDFium と一致しているか。ずれによって、受け付けたのに PDFium で開けない、あるいはその逆が起きるか。
2. ADR-0014 の抽出の版 `EXTRACT_REVISION`（`info-hive-rag/scripts/rag_config.py`）を上げないという判断は正しいか。上げると既存の抽出結果の鍵と索引の指紋が変わる。今まで受け付けていた PDF の扱いは変わらない、新たに受け付ける PDF には既存の抽出結果がない、という論理に穴はないか（台帳、ジョブの再開、doc_id = 読んだままのバイト列の SHA-256、古い版の扱いなど）。
3. 判定がほかの場所（登録 `info-hive-rag/scripts/rag_jobs.py` の `register`、MCP サーバー `rag_server.py`、wiki 側の案内）にもあって、一方だけ緩めたせいで食い違いが出ないか。
4. 試験（tests/rag/test_jobs.py に足した 2 件）が、変更を前の実装に戻したときに失敗するか。
5. バージョン 0.5.1（パッチ）、CHANGELOG、README、ADR-0013 の記述が正確か。

原本の PDF は移動・複製・書き換えしないこと。
