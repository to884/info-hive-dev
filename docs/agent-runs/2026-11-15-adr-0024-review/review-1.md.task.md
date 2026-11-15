# レビューの目的

`docs/adr/0024-wiki-extracts-pdf-text-with-pdfium.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）の取り込みで、rag を使わないときの PDF の本文の取り出し方を、rag と同じ PDFium の文字の層にそろえる ADR の提案である。根拠は `docs/research/markitdown-benchmark-2026-11-15.md` のベンチマークで、比べた対象は Office で書き出した 4 つの PDF だけである。

作者がこの ADR を、承認の条件の検証に進めてよいかを判断できるようにしたい。次の点を中心に崩してほしい。

- ベンチマークの結果から、決定と理由に書いたことが言えるか。言い過ぎや、結果にない主張がないか
- rag の今の作り（`info-hive-rag/scripts/rag_pdf.py` の `inspect_page` と `extract_pages`、`rag_index.py` の `_write_markdown`、`rag_config.py` の `EXTRACT_REVISION`）と、決定の「同じ取り出し方、同じ形、同じ判定」が本当に両立するか。バイト列が同じになると言える範囲
- OCR が要るページの扱い、標準出力で分けて読む出し方、写しを作らないこと、uv がないときに止まること、Read を本文の出典にしないことに、取り込みの手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/commands/ingest.md`）と食い違う点や、運用で崩れる点がないか
- 契約の試験と `EXTRACT_REVISION` で、wiki と rag がそろい続けると言えるか。pypdfium2 の版の扱いに抜けがないか
- 承認の条件が、決定を確かめるのに足りるか。検討した選択肢の退け方に誤りがないか
- 依存の向き（rag は wiki に依存し、プラグインは互いの内部のスクリプトを呼ばない。`AGENTS.md`）と、ADR-0012、ADR-0014、ADR-0018 との食い違い
