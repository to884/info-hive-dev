# ADR-0025 の行の印の実装と、条件 5 の 2 回目の測り方のレビュー（5 回目、確かめる資料を測る前）

## 目的

4 回目（`review-4.md`、設計）の指摘を直し、行の印を rag に実装した。条件 5 の 2 回目の測り方を、確かめる資料を測る前に決めた。

- **実装（rag）:** `info-hive-rag/scripts/rag_ocr_flags.py`（新規）、`rag_ocr.py`（ぼかした読み）、`rag_ocr_confidence.py`（`blur_text`）、`rag_ocr_client.py`、`rag_pdf.py`（別の解像度の読み、`page_flagged`）、`rag_review.py`（`is_flagged`、`page_detail`）、`rag_config.py`（OCR の保存先の鍵、閾値の既定 0.3）、`rag_jobs.py`、`rag_server.py`。差分は info-hive-rag の `git diff 6c7185b 24ddbb3`。
- **実装（wiki）:** `info-hive-wiki/skills/info-hive/references/ingest-workflow.md` の確認の手順。
- **試験:** `tests/contract/test_rag_review.py` の `FlagTests` ほか。手元で 120 件が通った。
- **測り方:** `docs/research/adr-0025-condition5-v2-2026-11-16.md` と、`docs/research/adr-0025-condition5-2026-11-16/scripts/score_v2.py`、`compare_flags.py`、`public_truth.py`、`eye_truth_packets.py`、`probe_analyze.py`（`eye_truth`、`apply_eye_truth`）。
- **4 回目の指摘の直し:** 試しの読みに画像と PDF の SHA-256 を記録して照らす（`probe_render.py`、`probe_reads.py`、`probe_analyze.load_reads`）。読む順を入力の順によらない全順序にした（`score.reading_order`、`rag_ocr_flags.reading_order`）。98 文字以上の行は ADR の決まり（左右に分けて読む）を正とし、選ぶ資料に該当がなかったことを測り方に書く。

確かめたこと: 製品のコードの印は、選ぶ資料の 75 ページ、3,211 行のすべてで、試した印と一致した（`compare_flags.py`）。製品の印で選ぶ資料を数えた値は `results/v2-tuning.json` にある。確かめる資料は、まだ数えていない。

次の性質を壊す欠陥だけを、重大として挙げてほしい。

1. **製品の印が、ADR の「行の印」と、測った印と同じになる:** 実装が ADR と食い違わない。OCR の保存、印が不明のときの扱い、閾値を変えたときの扱い、作り直しと確認の仕組み（段階 3）が、印でも成り立つ。
2. **測り方が、確かめる資料での偶然の合格や、後からの選択を許さない:** v2 の文書とスクリプトが食い違わない。目で作る正解、(b) から外す行、単位ごとの限界と「情報のある単位が 10 以上」の決まり、確かめる資料の増やし方（防衛白書を 50 ページに）が、合格を甘くしない。
3. **確かめる資料が漏れていない:** 選ぶ資料の結果を見て決めたことが、確かめる資料の結果に寄せて決めたものになっていない。

公開の PDF の中身はこの依頼に含めない。
