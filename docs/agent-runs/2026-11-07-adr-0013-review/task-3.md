rag プラグイン 0.4.0 と wiki プラグイン 0.6.0 の実装の敵対的レビューである。設計は ADR-0013（`docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md`）で、Sol による設計のレビューを 2 回受けた（`docs/agent-runs/2026-11-07-adr-0013-review/review-1.md`、`review-2.md`）。2 回目の指摘 5 件は実装で塞いだつもりである。

決定済みで覆さないこと: 参照ルートを廃止する。PDF の場所は絶対パスと内容の SHA-256 で記録する。0.3.0 との互換は捨てる。

差分:
- rag: `docs/agent-runs/2026-11-07-adr-0013-review/rag.diff`（info-hive-rag の origin/main..HEAD）。変更後のファイルは `info-hive-rag/scripts/` にある。
- wiki: `docs/agent-runs/2026-11-07-adr-0013-review/wiki.diff`（取り込みの手順の文言と版）。
- 試験: `tests/rag/test_jobs.py`、`tests/wiki/test_frontmatter_raw.py`。Windows で 28 件と 3 件が通った（rag は `test_jobs.py` と `test_indexes.py`）。

崩してほしいこと:
1. 実装が ADR-0013 の決定と食い違っているところ。
2. 2 回目の指摘 5 件（別名、H→G→H、ローカルから UNC へのリンク、親フォルダーの差し替え、失敗したジョブ）が、実装で本当に塞がったか。
3. 実装で新しく入った欠陥（SQL、トランザクションの境界、例外のときの状態、`file_id` を文字列にしたことの影響、`_location` が `None` を返すときの呼び出し側、`ingest_pdf` の `expected`、ワーカーの経路、`legacy_data`、`configure` の引数を変えたことによる MCP の呼び出し側への影響）。
4. 試験が実際には何も確かめていない、または環境によって黙って飛ばされるところ。
