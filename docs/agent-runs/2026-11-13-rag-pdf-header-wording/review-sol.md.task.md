# 依頼: rag 0.5.2（PDF のヘッダーの境界の書き方）の敵対的レビュー

## 背景

rag 0.5.1（to884/info-hive-rag#7）の `has_pdf_header`（`info-hive-rag/scripts/rag_index.py`）は、`data.find(b"%PDF-", 0, PDF_HEADER_OFFSET_LIMIT + 5)`（上限は 1024）で、`%PDF-` の開始位置（0 始まり）が 0〜1024 なら受け付ける。PDFium も `%PDF` を位置 0〜1024 で探す。

rag の README、CHANGELOG の 0.5.1 の項、`rag_index.py` のコメントは「`%PDF-` が先頭から 1024 バイト目までに始まれば」と書いていた。1 始まりで読むと、受け付ける範囲が実装より 1 バイト狭い。wiki 0.11.1 は「`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付ける」と書いているので、rag 側もそれにそろえ、版を 0.5.2（パッチ）にした。親リポジトリの `docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md` の同じ書き方も直した。

差分は `docs/agent-runs/2026-11-13-rag-pdf-header-wording/reviewed.diff`（前半がサブモジュール `info-hive-rag`、後半が親の ADR）にある。変更後のファイルは `info-hive-rag/README.md`、`info-hive-rag/CHANGELOG.md`、`info-hive-rag/scripts/rag_index.py`、`info-hive-rag/.claude-plugin/plugin.json`、`docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md` で読める。

## 意図して残したもの

- `rag_index.py` の `read_pdf` のエラーメッセージ「先頭の 1024 バイトに %PDF- がない」は変えていない。実行時の文字列で、親の `tests/rag/test_jobs.py` が正規表現で固定しているため、文書だけの修正の範囲から外した。フォローアップにする予定。
- `docs/agent-runs/` の過去の記録は履歴なので直していない。
- CHANGELOG の 0.5.2 の日付は「未定」にしている。日付は main に入り、マーケットプレイスから配られ始めた日を書く決まりで、0.5.1 も同じ手順（マージ後に日付を入れる）だった。

## 見てほしいこと

1. 直した文が、実装の境界（開始位置 0〜1024 を受け付け、1025 以上は拒む）と、どの読み方でも食い違わないか。特に「前にあるバイトが 1024 バイト以下」「開始位置（0 始まり）が 0〜1024」「`%PDF-` がないか、前に 1024 バイトを超えるバイトがある」の各表現。`%PDF-` が複数あるときの読み方も含める。
2. 「1024 バイト目まで」の書き方が、rag と親の ADR に残っていないか（`docs/agent-runs/` を除く）。
3. 0.5.2 の CHANGELOG の項が、事実（文書とコメントだけ、受け付ける PDF は変わらない）と合っているか。0.5.1 の項を書き換えたことの扱いが妥当か。
4. 版を 0.5.2 にしたことが、AGENTS.md の決まり（plugin.json と CHANGELOG をまとめて更新、マーケットプレイスには版を書かない）に合っているか。
