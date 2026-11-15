# ADR-0025 の 4 回目の敵対的レビュー

## 対象

- `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`（3 回目のレビューのあとに足した部分。`git diff 35ae0c5 -- docs/adr/` で見られる）
- `docs/research/adr-0025-measurement-2026-11-15.md` と `docs/research/adr-0025-measurement-2026-11-15/`（scripts と results）

## 目的

1. 測定の報告が、結果の JSON とスクリプトから言えることだけを書いているか。過大な主張、数え間違い、測り方の欠陥（測っているつもりのものを測っていない）を探す。
2. ADR に足した 2 つの決定が、そのまま実装して壊れないか。
   - 「本文を毎回同じにする」: pdfminer.six 20260107 の `group_textboxes` の `id()` による同点の順を、決まった順にする。この直しで本当に毎回同じになるか。ほかにプロセスごとに変わる原因（set の順、`Plane`、ハッシュ）が残っていないか。直し方（`stable_text.py` のモジュールの `id` の置きかえ）に穴がないか。
   - 「OCR の確信度とページの確認」: NDLOCR-Lite（commit e57f7c6）の PARSeq の出力から文字の確率を数え、確信度の低いページをユーザーに確かめてもらう。確率と最終の本文の対応、確認の結果の保存と古くなったときの扱い、要約との順、多数のページ（作者の資料は約 22,000 ページ）での運用、承認の条件 5 の閾値の決め方に穴がないか。
3. ADR の既存の決定（抽出の識別、OCR の保存、`page_report`、契約の試験、古い rag との組み合わせ）と、足した部分が食い違っていないか。

## 読むべきもの

- `info-hive-rag/scripts/rag_pdf.py`、`rag_ocr.py`、`rag_jobs.py`、`rag_index.py`、`rag_config.py`
- NDLOCR-Lite の `ocr.py`（`process_cascade`、`_run_ocr_on_image_array`）と `parseq.py`（`read`）: `C:/UserData/toshiki/Cache/uv/git-v0/checkouts/b64c8db5b4ea3782/e57f7c6/src/`
- pdfminer.six の `layout.py`: `C:/UserData/toshiki/Cache/uv/archive-v0/2qKOc-IXs21AJYik/Lib/site-packages/pdfminer/layout.py`

PDF の本文は試料のフォルダーの外に出さないこと。PDF とその本文はリポジトリにない（gitignore）。
