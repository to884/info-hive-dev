# レビューの目的

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md` は、info-hive の wiki と rag で、PDF の文字の層の本文を pdfminer（`LAParams(detect_vertical=True)`）で取り出し、ページの判定と OCR の画像は今の rag の PDFium（`rag_pdf.inspect_page`）で作る ADR の提案である。取り下げた ADR-0024（PDFium の文字の層にそろえる案）の代わりである。根拠は `docs/research/adr-0024-verification-2026-11-15.md` の検証と比較（Sol に画像つきで 3 回判定させた結果、`adr-0024-verification-2026-11-15/summary*.md`）と、`docs/research/pdf-extraction-tools-survey-2026-11-15.md` の調査である。

ADR-0024 のレビュー（`docs/agent-runs/2026-11-15-adr-0024-review/review-1.md` から `review-3.md`）で崩れた点（本文が同じになる範囲、判定の限界、抽出の識別と古い結果の使い回し、rag の OCR の設定とジョブ、分けて読む出し方、承認の条件の確かめ方）を、この ADR が引き継いで守れているかも見てほしい。

次の点を中心に崩してほしい。

- 比較の結果から、決定と理由に書いたことが言えるか。言い過ぎや、結果にない主張がないか
- pdfminer の本文と PDFium の判定を組み合わせる作りが、rag の今のコード（`info-hive-rag/scripts/rag_pdf.py`、`rag_index.py`、`rag_config.py`、`rag_jobs.py`）に対して成り立つか。ページの対応、OCR に回すページ、抽出の識別、取り込み直しの扱いに抜けがないか
- wiki の出し方（判定ごとの出し方、`vertical` のページの本文を出すこと、確かめるべきページ、分けて読む出し方）が、取り込みの手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/commands/ingest.md`）と食い違わないか
- wiki と rag をそろえ続ける方法（同じ中身の関数を両方に持つこと、契約の試験）で、そろい続けると言えるか
- 承認の条件が、決定を確かめるのに足りるか。検討した選択肢の退け方に誤りがないか
