# rag の PDF のヘッダーの判定の修正の敵対的レビュー（2026-11-12）

rag 0.5.0 の `read_pdf`（`info-hive-rag/scripts/rag_index.py`）は、ファイルの先頭がちょうど `%PDF-` でないと拒んでいた。全量の OCR（[rag-full-ocr-v050-2026-11-09](../../research/rag-full-ocr-v050-2026-11-09.md)）で、先頭に改行 1 バイトがあるだけの 2 文書（`L4/Comprehensive-Formal-Verification-of-an-OS-Microkernel.pdf`、`L4/From-L3-to-seL4-What-Have-We-Learnt-in-20-Years-of-L4-Microkernels.pdf`）が失敗した。`%PDF-` が先頭から 1024 バイト目までに始まれば受け付けるように直し、GPT-6.1 Sol（effort high）に 1 回レビューしてもらった。

- 依頼: `review-sol.md.task.md`。対象は作業ツリーの `rag_index.py`、`rag_jobs.py`、`rag_config.py`、`tests/rag/test_jobs.py` と、差分 `reviewed.diff`
- 結果: `review-sol.md`（採用可、確信度 中）
- Codex の読み取り専用のサンドボックスからは、作業フォルダーの外に置いた `reviewed.diff` を読めなかった。レビュアーは作業ツリーのファイルを直接読んだ。pypdfium2 などが入っていないので、PDFium を使う試験は再実行していない

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| wiki の `skills/info-hive/references/ingest-workflow.md` が「先頭が `%PDF-`」のままで、rag の受け付ける条件と食い違う | 軽微 | この変更では直さない。wiki プラグインの版を上げる別の変更にする |
| 境界の試験が `read_pdf` までで、1024 バイトの前置きを PDFium が開けるかを見ていない | 軽微 | 受け付けた 3 例を PDFium で開け、1025 バイトの前置きを PDFium も開けないことを確かめるようにした |
| CHANGELOG の例のコードスパンに、文字の `\n` ではなく本物の改行が入っている | 軽微 | Bash のヒアドキュメントで `\\` が縮んでいた。「改行のあとに `%PDF-1.5` が続く」と書き直した |
| 前の版でこの理由で失敗したジョブは、更新しても自動では再開しない | 崩れる前提 | CHANGELOG に、`retry_job` で再試行するか、取り込み直すよう書いた |
| ヘッダーの判定を通っても、PDFium で開けるとは限らない（ヘッダーだけで本体がないなど） | 崩れる前提 | 判定はヘッダーの開始位置の上限を PDFium にそろえるだけで、開けないものは抽出で失敗する。前の判定も同じだったので、変えない |

## 判断

- 境界: `data.find(b"%PDF-", 0, 1024 + 5)` で、`%PDF-` の開始位置が 0〜1024 なら受け付ける。PDFium は `%PDF` を位置 0〜1024 で探す（`core/fpdfapi/parser/fpdf_parser_utility.cpp`）。pypdfium2 5.14.0、PDFium 156 で、作った PDF に改行、CRLF、空白、NUL、任意の文字の前置きを付けて、1024 バイトまでなら開け、1025 バイトでは `Data format error` になった（`probe_header_offset.py`）。
- `EXTRACT_REVISION` は上げない。SHA-256 と抽出は、前と同じく読んだままのバイト列に対して行う。今まで受け付けていた PDF（`%PDF-` が位置 0）は判定の結果が変わらないので、抽出の結果も同じである。新たに受け付ける PDF は前の版では抽出まで進まないので、既存の抽出の結果を持たない。レビュアーもこの論理を崩せなかった。
- 版は 0.5.1（パッチ）。今まで受け付けていた入力の扱いを変えない、受け付ける範囲を広げるだけの修正である。

## 確かめたこと

- 実データの 2 件を、直した `read_pdf` と `extract_pages`（`ocr_mode` は `off`）に通した（`probe_real_pdfs.py`）。原本は読むだけで、書き換えていない。
  - `Comprehensive-Formal-Verification-of-an-OS-Microkernel.pdf`: 1,861,193 バイト、70 ページ、すべてテキストのページ、266,495 文字
  - `From-L3-to-seL4-What-Have-We-Learnt-in-20-Years-of-L4-Microkernels.pdf`: 277,217 バイト、18 ページ、すべてテキストのページ、83,426 文字
- 2 件とも pypdfium2 でそのまま開け、前置きの改行を取り除いたバイト列でも、先頭の 3 ページのテキストは同じだった（`probe_leading_newline.py`）。
- Windows の `.rag-venv` で、`tests/rag/test_jobs.py`、`test_indexes.py`、`test_extraction.py` の 67 件が通った。

## 確かめていないこと

- Linux（CI の `RAG unit tests`）での試験。PR で流す。
- 実データの 2 件を、MCP の `register_pdf` から索引化までの経路で取り込むこと。
