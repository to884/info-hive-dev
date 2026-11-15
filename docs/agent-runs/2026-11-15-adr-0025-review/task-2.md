# レビューの目的（2 回目）

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md` を、1 回目の敵対的レビュー（`docs/agent-runs/2026-11-15-adr-0025-review/review-1.md`）の指摘を受けて作り直した。根拠の資料は `docs/research/adr-0024-verification-2026-11-15.md` と `docs/research/pdf-extraction-tools-survey-2026-11-15.md` にある。

1 回目の指摘への対応は次のとおりである。直し方が言い換えにとどまっていないか、直し方から新しい欠陥が生まれていないかを見てほしい。

1. 「何をそろえ、何をそろえないか」の表を置き、最終の本文はそろえないこと、判定の誤りで出す本文が変わることを書いた。
2. pdfminer の本文の崩れ（`(cid:<数>)`、U+FFFD、私用領域）を数え、判定を変えない「確かめるべきページ」の印に入れた。承認の条件に、その検出の確認を足した。`garbled` のページで pdfminer も化けるという断定を消した。
3. OCR の結果を、文字の層の抽出と別の鍵で保存し、今の OCR の結果を条件つきで移すことにした。取り込み直しの時間の見込みを直した。
4. 「読めないページの扱い」の節を置き、ページの種類ごとに、rag の `ocr_mode`（`auto`、`always`、`off`）で OCR されるかを分けた。`always` と `retry_job` の扱いを書き、取り込みの手順の再試行の説明も直す対象にした。
5. wiki と rag は別々に配られて版がずれうることを書き、抽出の識別を wiki のログと rag の `job_status` に残すことにした。版を合わせることは強制しないとした。
6. 軽微な指摘（比較表の最初の行の意味、Poppler を外した理由、調査の文書の状態、メモリの基準、分けて読む出し方の境界）を直した。

次の点を中心に崩してほしい。

- 1 回目の指摘が実際に直っているか。直っていないものは、そのことを書く。
- OCR の結果を分けて保存する案と、今の OCR の結果を移す条件が、rag の今のコード（`info-hive-rag/scripts/rag_pdf.py`、`rag_index.py`、`rag_config.py`）と ADR-0014 に対して成り立つか。
- 「確かめるべきページ」の印と、「読めないページの扱い」が、rag の今のコード（`rag_server.py`、`rag_jobs.py`）と取り込みの手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/commands/ingest.md`）に対して成り立つか。
- 承認の条件が、決定を確かめるのに足りるか。言い過ぎや、結果にない主張が残っていないか。
