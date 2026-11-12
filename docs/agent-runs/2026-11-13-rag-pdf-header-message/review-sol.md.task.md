# 依頼: rag 0.5.3（PDF のヘッダーがないときのエラーメッセージ）の敵対的レビュー

## 背景

`info-hive-rag/scripts/rag_index.py` の `has_pdf_header` は、`data.find(b"%PDF-", 0, PDF_HEADER_OFFSET_LIMIT + 5)`（上限は 1024）で、`%PDF-` の開始位置（0 始まり）が 0〜1024 なら受け付ける。rag 0.5.2 で、文書の書き方を「`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付ける」にそろえた。親の ADR-0013 は、拒む条件を「`%PDF-` がないか、最初の `%PDF-` の前に 1024 バイトを超えるバイトがある」と書く。

`read_pdf` が拒むときのエラーメッセージ「PDF の形式ではありません（先頭の 1024 バイトに %PDF- がない）。」だけが前の書き方で残っていた。`%PDF-` が先頭の 1024 バイトに収まっていなければならないように読める（実際は開始位置 1020〜1024 の `%PDF-` もはみ出して受け付ける）。今回、これを「PDF の形式ではありません（%PDF- がないか、最初の %PDF- の前に 1024 バイトを超えるバイトがある）。」に直し、親の `tests/rag/test_jobs.py` の正規表現を合わせた。版は 0.5.3（パッチ）にした。親の wiki の `concepts/pdfのヘッダーの条件.md` と `wiki/log.md` も更新した。

差分は `docs/agent-runs/2026-11-13-rag-pdf-header-message/reviewed.diff`（前半がサブモジュール `info-hive-rag`、後半が親の試験と wiki）にある。変更後のファイルは `info-hive-rag/scripts/rag_index.py`、`info-hive-rag/CHANGELOG.md`、`info-hive-rag/.claude-plugin/plugin.json`、`tests/rag/test_jobs.py`、`wiki/concepts/pdfのヘッダーの条件.md` で読める。

CHANGELOG の 0.5.3 の日付は「未定」で、main に入る日に入れる（0.5.2 と同じ）。

## 見てほしいこと

1. 新しいメッセージが、`has_pdf_header` が False を返すすべての入力（空のファイル、`%PDF-` がない、`%PDF` だけ、最初の `%PDF-` が 1025 以降、`%PDF-` が複数あるなど）を正しく言い表しているか。逆に、受け付ける入力について誤った印象を与えないか。
2. メッセージの文字列に依存する箇所（ジョブの再試行の判定、wiki の取り込み手順、MCP の応答、ほかの試験）が、変えたことで壊れないか。`git grep` で rag と親（`docs/agent-runs/` と `docs/research/` の過去の記録を除く）を確かめてほしい。
3. 試験の正規表現が、メッセージの肝心な部分を固定できているか。
4. 版を 0.5.3 にしたこと、CHANGELOG の項が事実と合っているか（受け付ける PDF は変わらない）。
