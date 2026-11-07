rag 0.4.0 の実装の 2 回目の敵対的レビューである。1 回目（`docs/agent-runs/2026-11-07-adr-0013-review/review-3.md`、判定は却下）の重大な指摘 3 件と軽微な指摘を受けて、実装と試験を直した。設計は `docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md`。

決定済みで覆さないこと: 参照ルートを廃止する。PDF の場所は絶対パスと内容の SHA-256 で記録する。0.3.0 との互換は捨てる。

差分は `docs/agent-runs/2026-11-07-adr-0013-review/rag.diff`（info-hive-rag の origin/main..HEAD、変更後は `info-hive-rag/scripts/`）。試験は `tests/rag/test_jobs.py`（Windows で `test_indexes.py` と合わせて 33 件が通り、飛ばした試験はなかった）。

崩してほしいこと:
1. 1 回目の重大な 3 件（切れたハードリンク、ネットワークドライブの UNC への解決とワーカーの確かめ直し、区切りを混ぜた UNC）と、軽微な指摘（制御文字、差し替えの試験、同じ大きさと更新時刻の試験）は塞がったか。
2. 今回の修正で新しく入った欠陥はないか（`pdf_source` と `pdf_path` の組み合わせ、ジョブの `source` を渡されたままにしたことの影響、別名の判定で `os.stat` を呼ぶことの影響）。
3. 重大な欠陥がなければ、判定を採用可か条件付きで採用可にしてよい。
