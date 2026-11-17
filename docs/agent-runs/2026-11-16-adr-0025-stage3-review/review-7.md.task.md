# ADR-0025 の段階 3 の実装のレビュー（7 回目）

## 目的

6 回目（`review-6.md`、却下）の重大な指摘 1 つを直した。`Jobs.finish` の中で、作り直しのジョブの受け持つ版を変える文だけに、「自分が持つ処理中のジョブ」という条件（`owner` と `status='running'`）がなかった。完了を書く前に取り消されたジョブの受け持つ版まで変えていた。ほかの更新と同じ条件を付けた。

`tests/contract/test_rag_review.py`（32 件）に、`deferred` で戻ってから完了を書くまでに取り消したとき、受け持った版を持ったままにする試験を足した。

範囲と前提は `task-1.md`〜`task-6.md` のとおりである。今回は、`Jobs` のすべての状態の更新（`register`、`register_rebuild`、`claim`、`progress`、`begin_publication`、`finish`、`pause`、`cancel`、`retry`、`recover`）を、作り直しのジョブと取り込みのジョブの両方について、2 つの接続とワーカーが並行するときの順序で、もう一度通して見てほしい。

## 見てほしいこと

- 6 回目の反例が通らなくなったか。
- 上の更新のどれかが、自分の持たない行や、ほかの接続が状態を変えた行を書き換える経路がないか。
- 確認を取りこぼす経路と、取り消しや失敗を覆す経路が残っていないか。
- 1〜6 回目に挙げられなかった欠陥。

## 確かめた事実（参考）

- Windows 11、Python 3.12 で、`tests/contract/test_rag_review.py`（32）と `tests/rag/test_jobs.py`（33）が通った。
