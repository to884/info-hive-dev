# ADR-0025 の段階 1 の実装のレビュー

## 目的

`docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`（ADR-0025、提案）の実装の段階 1 を壊してほしい。段階 1 の範囲は次のとおりである。

- wiki と rag に、同じ中身のファイル（`info-hive-wiki/skills/info-hive/scripts/wiki_pdf_layer.py` と `info-hive-rag/scripts/rag_pdf_layer.py`）を置く。中身は、PDFium によるページの判定（rag の今の `inspect_page` を移したもの）、pdfminer.six による文字の層の取り出し、本文の崩れの数え方、確かめるべきページ、ページの一覧の形、抽出の識別である。
- pdfminer の `group_textboxes` は、距離の同じ組の順を `id(obj)` で決めるので、プロセスごとに本文が変わる。ADR の「本文を毎回同じにする」のとおり、モジュールの変数を書きかえず、同じ手順で組の順を決まった番号で決める関数を持つ（`_stable_group_textboxes` と、`LTPage` の子クラスを使う `TextConverter`）。測定で使った置きかえ（`docs/research/adr-0025-measurement-2026-11-15/scripts/stable_text.py`）と同じ本文を返すことが前提である。
- wiki に `wiki_pdf.py` を足す（ADR の「wiki（rag を使わないとき）」）。本文の出力、`--from` による分けた読み、`--json`。
- wiki の取り込みの手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md` の手順 2「PDF を読む」と手順 9）を書きかえる。
- rag の取り込みの動きは変えない。`rag_pdf.inspect_page` は共通のファイルの関数を使う。pdfminer の本文への切りかえ、`EXTRACT_REVISION` の更新、OCR の保存の分離、`page_report` は段階 2 で行う。
- 契約の試験 1、2、6、7 を `tests/contract/test_pdf_layer.py` に書く（ADR の「wiki と rag のそろい方」）。試験 3〜5、8 は段階 2、3 で足す。

## 見てほしいこと

- `_stable_group_textboxes` が、pdfminer.six 20260107 の `LTLayoutContainer.group_textboxes` と、組の順以外で同じ手順か。組の順が `stable_text.py` の置きかえと同じになるか。pdfminer のほかの場所で `id()` や、まとめる順に依存する箇所が残っていないか（`Plane`、`group_textlines`、`LTFigure` など）。
- `analyze_pages` のページの対応（PDFium と pdfminer のページの数が違うとき）、`start` と `stop` の扱い、途中で止めたときの振る舞い。
- `wiki_pdf.py` の `render` で、分けて読んだ出力をつなぐと一度に出した出力と同じになるか。反例（空の本文、見出しだけで上限を超えるページ、改行の位置、最後のページ、`--from` の位置の検査）を探してほしい。
- 続きの位置を標準エラーに出す設計で、エージェントが続きを読み落とさないか。
- 契約の試験が、ADR の試験 1、2、6、7 の言うことを本当に確かめているか。とくに試験 7 の「決め方を外すと違いが出る」を、列の順の番号に置きかえることで示している点が妥当か。
- 取り込みの手順の書きかえが、ADR の「読めないページの扱い」と矛盾しないか。rag を使ったときの代わりの手順（rag が `page_report` を返さないとき）を、段階 1 で手順に入れてよいか。
- Windows と Linux の違い、UTF-8、uv の有無、Python 3.12〜3.14。

## 読むファイル

- `docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md`
- `info-hive-rag/scripts/rag_pdf_layer.py`（`wiki_pdf_layer.py` と同じバイト列）
- `info-hive-rag/scripts/rag_pdf.py`
- `info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py`
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`（手順 1 の「PDF と rag の連携」、手順 2、手順 9）
- `tests/contract/test_pdf_layer.py`、`tests/contract/pdf_fixtures.py`、`tests/contract/pdf_text_hashes.py`、`tests/contract/fetch_corpus.py`
- `.github/workflows/pdf-contract.yml`
- `docs/research/adr-0025-measurement-2026-11-15/scripts/stable_text.py`
- pdfminer.six 20260107 のソース（手元の uv のキャッシュにある。たとえば `C:/UserData/toshiki/Cache/uv/archive-v0/APdsIj0phmPwZr6r/pdfminer/layout.py` と `converter.py`）

## 確かめた事実（参考）

- 契約の試験 18 件は、Windows 11、Python 3.12、合成の PDF と公開の 7 つの PDF で通った。rag の `tests/rag/test_extraction.py` の 30 件も通った。
- `wiki_pdf.py` の依存は、`uv sync --script` で Python 3.12、3.13、3.14 のどれでも入った。
