# ADR-0025 の段階 3 の実装のレビュー（1 回目）

## 目的

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md` の「OCR の確信度とページの確認」の実装を壊してほしい。段階 2（rag 0.6.0 の本文の切りかえ、OCR の保存、`page_report`）の上に作った。まず、**状態の遷移**に絞って見てほしい（確信度の数え方の細部はあとでよい）。

## 作ったもの

- **確信度:** `info-hive-rag/scripts/rag_ocr_confidence.py`（OCR の環境で動く）が、PARSeq のロジットに softmax をかけ、文字と終わりの記号の確率を `ProbStr`（str の子クラス）に持たせる。NDLOCR-Lite の `process_cascade` は、読み直しと、長い行を分けて読んだ文字列の `+` を通しても、確率を残す。行の確信度は最小値で、空の行は 0。`rag_ocr.py` は `lines` と `confidence_revision` を返す。`rag_pdf.OcrStore.save` が保存し、ページの記録に `confidence_min` と `ocr_sha256` を入れる。閾値は設定（`ocr_confidence_threshold`、既定 0.8、未校正）で、指紋に入れない。
- **台帳:** `info-hive-rag/scripts/rag_review.py` の `Ledger`。wiki の作業領域の `reviews.sqlite`（catalog とは別のファイル）。`decide` は、版の照合と版上げを 1 つの `BEGIN IMMEDIATE` で行う。
- **確認を当てた索引:** `rag_index.Engine.ingest_pdf` は、台帳の最新の版 V を読み、`Config.generation(doc_id, V)` の行を作り、すべて書いてから `documents.generation` と `review_version` を切りかえ、前の版の行と catalog の途中経過を消す。`existing` の分岐は、`review_version` が V と違えば通らない。却下したページは索引に入れない。検索できる本文がなくなっても、最初の取り込みでなければ 0 行の版を公開する。V>0 なら `reviewed/<doc>/<V>/document.md` を返す。
- **作り直し:** `Engine.rebuild_reviewed` が `ingest_pdf(expected_doc_id=..., allow_reset=False)` を、公開した版が台帳の版に追いつくまで繰り返す。方針が変わった索引では何もしない（`deferred`）。ジョブは `rag_jobs.Jobs.register_rebuild`（`kind='review'`、wiki と PDF ごとに 1 つ）で、処理中なら `rerun=1` を付け、`finish` は `rerun` があれば待ちに戻す。
- **ツール:** `rag_server.ocr_page_detail` と `decide_ocr_pages`。`job_status` の `page_report` に、確信度の低いページ、確信度が不明のページ、確認の状態ごとのページ（`review:pending` など、`review:awaiting_publish`）と版を、返すときに足す（`Jobs._with_review`）。`status` と検索の結果に、確認の状態の印。
- **試験:** `tests/contract/test_rag_review.py`（11 件、試験 8）。

## 見てほしいこと（状態の遷移）

1. 台帳の版、作っている版、公開した版の 3 つが、どの順の操作（確認、作り直しの途中で止まる、再試行、取り込み直し、方針の変更、OCR のやり直し、2 つの wiki）でも食い違わないか。
2. 作り直しのジョブの取りこぼし: 確認を受け付ける時点と、ジョブが台帳を読む、公開する、終わりを書く時点の、すべての前後関係。`register_rebuild` と `finish` の `rerun`。2 つの DB（`reviews.sqlite` と `jobs-v2.sqlite`）にまたがる順序。
3. 公開の切りかえ: 行を書き終える前に検索に新しい版が混ざる経路、前の版の行や途中経過が残って埋め込みを飛ばす経路、0 行の版、`_reset_index` が起きる経路。
4. `Jobs` の `register`、`claim`、`unfinished`、`retry`、`cancel`、`recover`、`list` が、作り直しのジョブ（`kind='review'`、`source` が空）で壊れないか。
5. 古い台帳（rag 0.5.3 の `catalog.sqlite` と `jobs-v2.sqlite`）から始めたとき。
6. 確認の状態の決め方（`rag_review.page_state`、`review_lists`、古くなった結果）が ADR と合うか。

## 読むファイル

- `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`（「OCR の確信度とページの確認」と「rag」）
- `info-hive-rag/scripts/rag_review.py`、`rag_index.py`、`rag_jobs.py`、`rag_worker.py`、`rag_server.py`、`rag_pdf.py`、`rag_config.py`、`rag_ocr.py`、`rag_ocr_confidence.py`
- `tests/contract/test_rag_review.py`、`tests/rag/verify_ocr_confidence.py`

## 確かめた事実（参考）

- Windows 11、Python 3.12 で、`tests/contract/test_rag_review.py`（11）、`test_rag_contract.py`（12）、`tests/rag/test_jobs.py`（33）、`test_indexes.py`（4）、`test_extraction.py`（27）が通った。
- `tests/rag/verify_ocr_confidence.py` を手元の OCR の環境で動かし、本物の `process_cascade` で読み直しと分けた読みの不変条件を、本物の 3 つの認識器で包んだ読みと元の `read` の文字列が同じことを確かめた。
