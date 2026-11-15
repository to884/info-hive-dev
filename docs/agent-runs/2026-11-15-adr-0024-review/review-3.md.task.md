# レビューの目的（3 回目）

`docs/adr/0024-wiki-extracts-pdf-text-with-pdfium.md` は、info-hive の wiki の取り込みで、rag を使わないときの PDF の本文の取り出し方を、rag と同じ PDFium の文字の層にそろえる ADR の提案である。2 回目の敵対的レビュー（`docs/agent-runs/2026-11-15-adr-0024-review/review-2.md`）の指摘を受けて直した。1 回目は `review-1.md` にある。

2 回目の指摘への対応は次のとおりである。直し方が、言い換えにとどまっていないかを見てほしい。

- 「読めないページの扱い」の節を足し、ページの種類ごとに、rag の既定の `ocr_mode`（`auto`）で取り戻せるかを分けた。取り戻せないページ（確かめるべきページ、`blank`、文として読めない `text`）は、Read で画像を見て、画像から読んだことを要約ページに書くようにした。`always` を使うかは、設定の変更と時間を伝えたうえでユーザーが決めるとした
- rag の側の承認の条件を、「抽出の識別（`EXTRACT_REVISION` と pypdfium2 の版）を、抽出の結果の鍵、保存したページ、索引の方針の指紋のすべてに入れ、識別が違う保存済みの結果と索引を使い回さないこと」に改めた。版を固定するだけ、鍵に版を入れるだけでは足りない理由も書いた
- 軽微な指摘（`blank` の OCR の条件、Read を使う場面の食い違い、検出率の主張、`--json` の範囲）を直した

次の点を中心に崩してほしい。

- 2 回目の指摘が実際に直っているか。直し方から、新しい欠陥が生まれていないか
- 「読めないページの扱い」が、rag の今のコード（`info-hive-rag/scripts/rag_pdf.py`、`rag_server.py`、`rag_config.py`）と、wiki の取り込みの手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/commands/ingest.md`）に対して成り立つか。Read で画像から読む扱いが、wiki の要約ページの決まり（`info-hive-wiki/skills/info-hive/references/page-conventions.md`）と食い違わないか
- rag の側の承認の条件が、古い結果と索引の使い回しを防ぐのに足りるか（`rag_index.py` の移行と再利用の分岐を含む）
- 承認の条件の判断の基準が、確かめられる形になっているか。言い過ぎや、結果にない主張が残っていないか

1 回目と 2 回目の指摘のうち直っていないものは、そのことを書く。
