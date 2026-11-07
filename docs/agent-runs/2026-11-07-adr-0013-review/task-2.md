ADR-0013（`docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md`）の 2 回目のレビューである。1 回目のレビュー（`docs/agent-runs/2026-11-07-adr-0013-review/review-1.md`、判定は却下）の 8 件の指摘を受けて、ADR を書き直した。まだ実装していない。

決定済みで覆さないこと: 参照ルートの設定を廃止する。PDF の場所は絶対パスと内容の SHA-256 で記録する。0.3.0 との互換は捨てる。

崩してほしいこと:
1. 1 回目の 8 件の指摘は、書き直した決定で本当に塞がったか。塞がっていない反例はないか。
2. 書き直して新しく入れた決定（場所のキーを正規化しない、`documents` に代表のパスを持たず `locations` から最後に確かめた場所を引く、完了・失敗・キャンセルのジョブしかなければ新しいジョブを作る、`jobs-v2.sqlite` と `wikis-v2/`、`lstat` と `fstat` の比較、UNC とデバイスのパスを拒む、`raw` を `/` 区切りにする）に、新しい欠陥はないか。
3. 「同意の層はホストのツールの許可と wiki の手順」とした前提の弱さを、ADR が正しく書いているか。

読むファイルは 1 回目と同じ（`info-hive-rag/scripts/`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/scripts/wiki_text.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`）に、書き直した ADR と 1 回目のレビューを加える。
