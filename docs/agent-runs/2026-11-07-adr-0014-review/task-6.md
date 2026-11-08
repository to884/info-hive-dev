これは 6 回目の依頼で、5 回目の指摘を直したことの確認である。Codex のシェルではファイルを読めないので、読むべき本文をこの依頼に埋め込む。**シェルでファイルを読もうとしないこと。** 埋め込んだ本文と差分だけで判断してよい。

埋め込んだ差分は info-hive-rag の d82c3b1..967b2c1（5 回目の指摘への直し）である。

5 回目の指摘:
- 重大: ネットワークドライブが一時的に切れて os.path.exists が偽になると、その PDF を取り込み直しの一覧（previous-index.json）から永久に外し、抽出の結果も消しうる。
- 軽微: 取り込み直しの途中でもう一度設定を変えると、方針が変わった索引の _reingest() が pending.update(current) で場所を上書きし、まだ取り込み直していない場所が status から隠れる。

確かめてほしいこと: 直しで指摘が解消したか、新しい反例がないか（_gone() の判定の穴、Windows のドライブのルート、UNC にならない絶対パス、権限で見えないフォルダー、`_merge_documents()` を _reset_index() と _reingest() の両方で使うことの影響、_extraction_in_use() と _prune_previous() への影響）。前の回で崩せなかった点を蒸し返す必要はない。

## 直しのあとの ADR-0014 の該当の行

| 取り込み直しの一覧 | 索引を空にする前に、取り込み済みだった文書の SHA-256、題名、場所、ソースのページを `previous-index.json` に残す。すでに一覧があれば（取り込み直しの途中でもう一度設定を変えたとき）、今の台帳の文書と合わせる。同じ文書は、場所とソースのページの和をとる。`status` は、取り込み直すべき PDF の一覧を `reingest` で、あるかどうかを `reingest_required` で返す。方針が変わった索引では台帳の文書と一覧の文書を、空にしたあとは一覧の文書のうち、まだ取り込み直していない場所を返す。場所ごとに見るのは、同じ内容を 2 か所で登録していたとき、片方を取り込み直しても、もう片方の場所を失わないためである。台帳に載った場所（別の版を取り込んだ場所を含む）と、消えたと言える場所は外す。消えたと言えるのは、フォルダーはあるのにファイルだけがないときに限る。ネットワークドライブが切れているときのように、フォルダーごと見えないときは残す（一時的に見えないだけで、一覧と出典の情報を失わないため）。方針が変わった索引では、台帳の文書と一覧の文書の場所とソースのページの和をとる。場所が残らない文書は外す。取り込みのたびに一覧を書き直し、すべて外れたら `previous-index.json` を消す |

## 足した試験

```python
    def test_unreachable_folder_keeps_its_pdf_in_the_list(self):
        far = self.root / "network" / "資料.pdf"
        far.parent.mkdir()
        far.write_bytes(self.source.read_bytes())
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        first.ingest_pdf(str(self.wiki), str(far), "sources/資料.md")
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        hidden = self.root / "network-offline"
        os.replace(far.parent, hidden)  # ネットワークドライブが一時的に切れた（フォルダーごと見えない）
        try:
            self.make_pdf(other, "Edited while offline")
            second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
            state = second.status(str(self.wiki))
            self.assertEqual([item["paths"] for item in state["reingest"]], [[far.as_posix()]])
            self.assertTrue((second.config.extraction_root / hashlib.sha256(self.source.read_bytes()).hexdigest()).exists())
        finally:
            os.replace(hidden, far.parent)
        # ファイルだけが消えた（フォルダーはある）ときは、一覧から外す。
        far.unlink()
        self.make_pdf(other, "Edited again")
        second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        self.assertEqual(second.status(str(self.wiki))["reingest"], [])

    def test_second_change_before_reingest_keeps_every_path(self):
        copy = self.root / "refs" / "写し.pdf"
        copy.write_bytes(self.source.read_bytes())
        first = self.engine()
        self.ingest(first)
        first.ingest_pdf(str(self.wiki), str(copy), "sources/写し.md")
        self.ingest(self.engine(embedding_model="cl-nagoya/ruri-v3-70m"))  # 資料.pdf だけ取り込み直す
        third = self.engine(embedding_model="cl-nagoya/ruri-v3-130m")
        paths = [set(item["paths"]) for item in third.status(str(self.wiki))["reingest"]]
        self.assertEqual(paths, [{self.source.as_posix(), copy.as_posix()}])

```
