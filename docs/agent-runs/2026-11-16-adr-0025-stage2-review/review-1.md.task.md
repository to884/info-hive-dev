# ADR-0025 の段階 2 の実装のレビュー

## 目的

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`（ADR-0025、提案）の実装の段階 2 を壊してほしい。段階 1（wiki と rag で同じ中身の `rag_pdf_layer.py`、`wiki_pdf.py`、契約の試験 1、2、6、7）はマージ済みである。段階 2 の範囲は次のとおりである（ADR の「rag」の節）。

- rag の判定が `text` のページの本文を、PDFium から pdfminer（`rag_pdf_layer.analyze_pages`）に変える。`EXTRACT_REVISION` を `extract-v2` に上げ、索引の方針の指紋と抽出の結果の鍵に、文字の層の識別を入れる。
- OCR の結果を、ページの抽出の結果とは別の置き場所（`<data_dir>/extracted/<SHA-256>/ocr/<ocr_key>/`）に保存する。鍵は描画の識別（pypdfium2 の版と dpi）と OCR の版である。文字の層の取り出し方を変えても OCR を使い回す。
- rag 0.5 までの OCR の結果（`extract-v1` の `page-*.json` で `ocr` が真のもの）を、同じ PDF、同じ `ocr_dpi`、同じ OCR の版のときだけ移す。描画の識別は「不明」とし、移したときの描画の識別を残す。同じ元からもう一度は移さない（`ocr/adopted.json`）。
- 判定を OCR の前にページごとに保存し（`judge-*.json`）、`page_report` を保存した記録から作る。`job_status` に `page_report`（`page_report_from` で続き）と抽出の識別を、`status` に OCR の設定を足す。失敗したジョブも、それまでの `page_report` を返す。
- 依存を固定する（`pdfminer.six==20260107`、`pypdfium2==5.15.2`）。rag 0.6.0、wiki 0.22.0。
- 契約の試験 3、4、5 を `tests/contract/test_rag_contract.py` に書く。確信度と確認（試験 8）は段階 3 である。

## 見てほしいこと

- **使い回しの正しさ:** 抽出の結果の鍵（`Config.extraction_key`）と OCR の鍵（`Config.ocr_key`）と指紋（`Config.fingerprint`）が、ADR の「何が変われば何をやり直すか」を満たすか。古い結果を新しい版の結果として使ってしまう経路、逆に使えるのに OCR をやり直す経路がないか。
- **移し方:** `OcrStore.adopt_legacy` の条件、印、途中で止まったとき、複数の元（`auto` と `always`）、移したあとに描画が変わったとき。`OcrStore.load` の判定。
- **再開と並行:** `extract_pages` を途中で止めて再開したとき、判定の記録とページの記録がずれないか。抽出のロック（`Engine._extraction_lock`）の外で保存先を触る経路がないか。2 つの wiki で同じ PDF を取り込むとき。
- **page_report:** 成功、失敗、取り込み済み（`unchanged`）で、記録から正しく作られるか。保存の大きさ（22,000 ページ）。`Jobs.status` と `Jobs.list` での切り方。失敗したジョブの `result` に `page_report` だけが入ることで、呼ぶ側が困らないか。
- **索引と取り込み直し:** 指紋が変わることで、既存の利用者の索引で何が起きるか（ADR-0014 の取り込み直し、`existing` の分岐、`_legacy_generations`、`_remove_extraction` の後始末）。0.4.0 の結果を移す処理が動かなくなったことの影響。
- **試験:** 契約の試験 3〜5 が ADR の言うことを確かめているか。抽出の試験から消した 4 件（0.4.0 の結果を移す試験）を消してよいか。`tests/rag/test_extraction.py` の指紋の固定値。
- **wiki の手順:** `page_report` を使う経路と、古い rag の経路の書き分け。
- **共有のファイル:** `rag_pdf_layer.py` は変えていない（wiki と同じバイト列）。

## 読むファイル

- `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`
- `info-hive-rag/scripts/rag_config.py`、`rag_pdf.py`、`rag_index.py`、`rag_jobs.py`、`rag_worker.py`、`rag_server.py`、`rag_pdf_layer.py`
- `info-hive-rag/CHANGELOG.md`、`info-hive-rag/README.md`
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`（手順 1 の「PDF と rag の連携」、手順 2 の「PDF を読む」）
- `tests/contract/test_rag_contract.py`、`tests/rag/test_extraction.py`、`.github/workflows/rag.yml`
- 差分は `git -C info-hive-rag diff origin/main..HEAD`、`git -C info-hive-wiki diff origin/main..HEAD`、`git diff origin/main..HEAD`（親）で見られる。

## 確かめた事実（参考）

- Windows 11、Python 3.12 で、`tests/rag/test_jobs.py`（33）、`test_indexes.py`（4）、`test_extraction.py`（26）、`tests/contract/test_rag_contract.py`（9）、`tests/contract/test_pdf_layer.py`（22）が通った。
- 契約の試験 5 は、info-hive-rag の v0.5.3 のタグの `rag_pdf.py` と `rag_config.py` をそのまま動かし、`ocr_mode` が `always` で 1 ページ目（判定は `text`）の OCR の結果が空になる応答を作っている。
