# レビューの目的（3 回目）

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md` を、2 回目の敵対的レビュー（`docs/agent-runs/2026-11-15-adr-0025-review/review-2.md`）の指摘を受けて直した。1 回目は `review-1.md` にある。根拠の資料は `docs/research/adr-0024-verification-2026-11-15.md` にある。

2 回目の指摘への対応は次のとおりである。直し方が言い換えにとどまっていないか、直し方から新しい欠陥が生まれていないかを見てほしい。

1. rag の `job_status` の結果に `page_report`（判定ごとのページ、確かめるべきページ、OCR したページ、OCR の結果が空のページ、抽出の識別）を足し、取り込みの手順がそれを読むことにした。`extracted_markdown` だけを読んではいけないと書いた。
2. rag の `status` の結果に、今の設定（`ocr_mode`、`ocr_dpi`）を足すことにした。
3. OCR の結果の鍵に、描画の識別（pypdfium2 の版と描画の dpi）を入れた。今の結果を移すときは、描画の識別を「不明」として記録し、移す 1 回だけ使い回す割り切りを明記した。
4. `always` の説明に、索引の方針の指紋に OCR の設定が入るので、その PC のすべての wiki の索引に影響することを足した。
5. 確かめるべきページの条件から私用領域の文字を外し（公開の 33 ページ中 8 ページに印）、承認の条件に印の割合の上限（3 割）と契約の試験（OCR の保存と `page_report` を含む）を足した。
6. 検証の報告の古い記述を直した。

次の点を中心に崩してほしい。

- 1 回目と 2 回目の指摘が実際に直っているか。直っていないものは、そのことを書く。
- `page_report`、`status` の設定、OCR の保存の分け方と移し方が、rag の今のコード（`info-hive-rag/scripts/rag_pdf.py`、`rag_index.py`、`rag_config.py`、`rag_jobs.py`、`rag_server.py`、`rag_worker.py`）と ADR-0014 に対して成り立つか。
- 承認の条件と契約の試験で、決めた動作を確かめられるか。言い過ぎや、結果にない主張が残っていないか。
