# 行の印の 4 つ目（別の認識器）の実装と、条件 5 の 3 回目の測り方のレビュー（8 回目、確かめる資料を数える前）

## 目的

条件 5 の 2 回目は、公開の (b) が 0.737 で不合格だった。作者の決定で、印に 4 つ目の決まり（横書きの行を RapidOCR の日本語の認識モデルで読み、英数字か記号が足されるか置き換わる）を足し、新しい確かめる資料で 3 回目を測る。

- **ADR:** `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md` の「行の印」の 4。
- **実装（rag）:** `info-hive-rag/scripts/rag_ocr_flags.py`（`skeleton`、`rapid_added`、`static_flags`、`OCR_FLAG_REVISION = "flags-v2"`）、`rag_ocr_confidence.py`（`rapid_reader`、`RAPID_REVISION`）、`rag_ocr.py`（依存に `rapidocr==3.10.0`、行ごとの `rapid_text`）、`rag_pdf.py`、`rag_review.py`、`rag_server.py`。差分は info-hive-rag の `git diff 24ddbb3 9468711`。
- **試験:** `tests/contract/test_rag_review.py` の `test_rapid_flags_added_symbols_only`。手元で 117 件が通った。
- **測り方:** `docs/research/adr-0025-condition5-v3-2026-11-17.md`。2 回目（`adr-0025-condition5-v2-2026-11-16.md`）の合否と数え方を引き継ぐ。新しい確かめる資料は `scripts/make_synthetic_v3.py`、`public_truth.py`（`seeded_pages_v3`、`DROPPED_V3`、割り当てのない文字の除外）で作る。
- **開発用の資料での選び方:** `scripts/probe_rapid.py`、`probe_rapid_analyze.py`。

確かめる資料は、まだ数えていない（正解を目で作っている途中）。

次の性質を壊す欠陥だけを、重大として挙げてほしい。

1. **製品の印が ADR の決まりと、開発用の資料で試した印と同じになる。**
2. **3 回目の確かめる資料が、開発用の資料と漏れなく分かれ、測る前の決めごとが、数えたあとの選択で動かない。**
3. **段階 3 の仕組み（確認待ち、台帳、作り直し、検索の印）が、flags-v2 でも成り立つ。**

合否の限界が近似であること（2 回目の 7 回目のレビュー）は、文書に書いた前提として扱う。公開の PDF の中身はこの依頼に含めない。
