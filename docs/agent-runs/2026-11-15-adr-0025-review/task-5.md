# ADR-0025 の 5 回目の敵対的レビュー

4 回目のレビュー（`review-4.md`）の指摘を、コミット 6e4c587 で直した。差分は `git diff 9e2a70c..HEAD -- docs/adr/ docs/research/adr-0025-measurement-2026-11-15.md docs/research/adr-0025-measurement-2026-11-15/` で見られる（9e2a70c は ADR-0025 の最初のコミット。3 回目までの直しも含む。4 回目のあとの差分だけなら `git diff d5b5639..HEAD`）。

## 確かめてほしいこと

1. 4 回目の重大な指摘 3 つ（空の行の確信度、wiki ごとの確認の結果と共有の抽出の結果、確認の保存と索引の作り直しの整合）が、構造として解消されたか。直し方が、新しい食い違いを作っていないか。
   - 台帳、当てた本文と索引、公開する `generation` の切りかえ、反映待ちの状態、`ocr_page_detail` と `decide_ocr_pages` の楽観的な排他。
   - rag の今の実装（`info-hive-rag/scripts/rag_index.py`、`rag_config.py`、`rag_jobs.py`）に照らして、実装できる契約になっているか。
2. 軽微な指摘（並行の置きかえ、ページの対応の主張、試料の SHA-256、PARSeq の記録、承認の条件 5 の資料の分け方）の直しに、穴が残っていないか。
3. ADR の全体で、足した部分と既存の決定（抽出の識別、OCR の保存、`page_report`、契約の試験、古い rag との組み合わせ、wiki だけの経路）が食い違っていないか。

対象: `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`、`docs/research/adr-0025-measurement-2026-11-15.md`、`docs/research/adr-0025-measurement-2026-11-15/`。PDF とその本文はリポジトリにない。
