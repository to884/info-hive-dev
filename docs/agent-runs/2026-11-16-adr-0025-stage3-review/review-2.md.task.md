# ADR-0025 の段階 3 の実装のレビュー（2 回目）

## 目的

1 回目（`review-1.md`、却下）の重大な指摘 7 つを直した。直し方が原因を取り除いているか、新しい欠陥が入っていないかを壊してほしい。範囲と前提は `task-1.md` のとおりで、今回は wiki の手順（`info-hive-wiki/skills/info-hive/references/ingest-workflow.md` の「OCR の確信度の低いページを確かめる」）も見てほしい。

## 1 回目の指摘と、原因の構造と、直し方

- **公開したものが、公開の識別で決まっていなかった（指摘 1、4、6、7）。**
  - 確認を当てた本文と確信度の要約は、`reviewed/<doc>/<generation>/`（generation は指紋と確認の版を含む）に置く。公開の前に書いても、公開している版のものを上書きしない（`Engine._write_published`、`rag_review.published_folder`）。
  - 公開したら、同じ文書のほかの generation の成果物を消す。
  - catalog の途中経過（`jobs`）に `doc_id` の列を足した。公開したら、同じ文書のほかの版の途中経過を消す。文書を外すときも、文書のすべての版の途中経過を消す。
  - 確認の状態（検索の印、`status`、`page_report` の確認の一覧）は、ジョブを保存したときの記録ではなく、その wiki で今公開している generation の要約から作る（`Jobs._with_review`）。`page_report.review` に、公開している版の確認を当てた本文のパスも返す。
  - 作り直し（`rebuild_reviewed`）は、何もしないときも `ingest_pdf` を通し、取り込み済みの分岐で、公開している版の結果をそのまま返す。
- **0 行の版と方針の変更（指摘 2）。** 索引を空にしたあとで、この版の途中経過の行を作り直す。表がないとき、索引の保守と検索と後始末を飛ばす。
- **2 つの DB にまたがる取りこぼし（指摘 3）。**
  - 作り直しが要るかを、ジョブの記録ではなく状態から導く。台帳（`reviews.sqlite`）に wiki のパスを残す。
  - ワーカーの起動時と、待っているあいだの 1 分おきに、台帳の版が公開した版より新しい文書を探し、作り直しのジョブを登録し直す（`rag_review.pending_rebuilds`、`rag_worker.reconcile_rebuilds`）。
- **読み取りの食い違い（指摘 5）。** `ocr_page_detail` は、台帳の版、ページの最新の結果、公開した版までの結果、履歴を、1 つの読み取りのトランザクションで読む（`Ledger.snapshot`）。
- **軽微。**
  - 作り直しのジョブの再試行は、同じ wiki と PDF の待ちか処理中のジョブがあれば、それを返す。
  - ページの記録に、確信度の数え方の版（`confidence_revision`）を入れた。版が今と違えば、確信度が不明として扱う。
- **試験。** `tests/contract/test_rag_review.py` の `ReviewRegressionTests` に、それぞれの反例を試験として足した（20 件）。

## 見てほしいこと

- 上の直しで、7 つの反例が通らなくなったか。
- 状態から登録し直す仕組みが、ほかの経路を壊さないか。
  - 方針が変わった索引で作り直しが `deferred` を返すとき、1 分おきに登録し直して回り続けないか。
  - wiki を消したとき。
  - 2 つの MCP の接続（同じ `data_dir`）があるとき。
- 公開の識別ごとの成果物の後始末で、公開している版のものを消す経路がないか。
- wiki の手順が、ツールの実際の振る舞い（返す値の名前、待ち方、受け付けないとき）と合うか。
- 1 回目に挙げられなかった欠陥。

## 確かめた事実（参考）

- Windows 11、Python 3.12 で、次の試験が通った。
  - `tests/contract/test_rag_review.py`（20）、`test_rag_contract.py`（12）
  - `tests/rag/test_jobs.py`（33）、`test_indexes.py`（4）、`test_extraction.py`（27）
