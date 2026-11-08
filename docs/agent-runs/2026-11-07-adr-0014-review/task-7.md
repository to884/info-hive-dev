これは 7 回目の依頼で、6 回目の指摘を直したことの確認である。Codex のシェルではファイルを読めないので、読むべき本文をこの依頼に埋め込む。**シェルでファイルを読もうとしないこと。** 埋め込んだ本文と差分だけで判断してよい。

埋め込んだ差分は info-hive-rag の 967b2c1..2a9fba8 である。

6 回目の指摘（重大）: `_gone()` は os.path.exists() を使うので、権限の不足でファイルを確かめられないときも偽になる。フォルダーは見えるのにファイルに届かないとき、残っている PDF を取り込み直しの一覧から外す。

直し: os.stat(place) が FileNotFoundError のときだけ、親フォルダーが見えることを確かめて消えたとみなす。それ以外の OSError（PermissionError など）では消えたとみなさない。

確かめてほしいこと: 指摘が解消したか、新しい反例がないか（Windows の ERROR_PATH_NOT_FOUND と FileNotFoundError の対応、切れたネットワークドライブで stat がどの例外になるか、シンボリックリンクやジャンクションの先が消えたとき、NotADirectoryError）。前の回で崩せなかった点を蒸し返す必要はない。

## 足した試験

```python
    def test_gone_is_true_only_when_the_file_is_surely_missing(self):
        import rag_index
        place = self.source.as_posix()
        self.assertFalse(Engine._gone(place))
        original = os.stat

        def denied(path, *args, **kwargs):
            if os.fspath(path) == place:
                raise PermissionError(13, "アクセスが拒否されました", place)
            return original(path, *args, **kwargs)
        with patch.object(rag_index.os, "stat", denied):
            self.assertFalse(Engine._gone(place))  # 権限が足りず確かめられないときは、消えたとみなさない
        missing = (self.root / "refs" / "ない.pdf").as_posix()
        self.assertTrue(Engine._gone(missing))
        self.assertFalse(Engine._gone((self.root / "ないフォルダー" / "資料.pdf").as_posix()))

```
