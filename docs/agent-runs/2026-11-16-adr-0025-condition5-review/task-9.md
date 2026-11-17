# 別の認識器の印の比べ方の直しのレビュー（9 回目、確かめる資料を数える前）

## 目的

8 回目（`review-8.md`、却下）の 2 つの指摘（負号の足し忘れを見逃す、差分の区切り方で落としただけの違いや入れ替えに印が付く）を直した。直し方は `docs/research/adr-0025-condition5-v3-2026-11-17.md` の「8 回目のレビューで直したこと」と、ADR の「行の印」の 4 にある。

- `info-hive-rag/scripts/rag_ocr_flags.py` の `rapid_added`、`_counted`、`_marked`、`LOOKALIKE`、`AMBIGUOUS`（文字の数で比べる）。`OCR_FLAG_REVISION = "flags-v3"`。
- 試験: `tests/contract/test_rag_review.py` の `test_rapid_added_counts_characters`、`test_rapid_flags_added_symbols_only`。
- 試しのスクリプトは製品の `rapid_added` を呼ぶ（`docs/research/adr-0025-condition5-2026-11-16/scripts/probe_rapid_analyze.py`）。
- 前の版で OCR した結果は、読みから印を付け直す（`scripts/reflag_ocr.py`）。

次の性質を壊す欠陥だけを、重大として挙げてほしい。

1. **`rapid_added` が ADR の決まり（足した英数字か記号に印。落としただけ、見た目の同じ文字、取り違えやすい英数字どうしの入れ替えは印にしない）と食い違わない。**
2. **印を付け直す手順が、OCR し直したときと同じ印を与える。**

公開の PDF の中身はこの依頼に含めない。
