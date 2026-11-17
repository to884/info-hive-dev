# 段階2の手元の検証

2026-11-18、Windows。プラグインの基点は `ce2b610af7dafdd09b9d162128ce67904e001665`（0.31.1）。親の基点は `6e58fa49b5d6fcd7596f6af101e4425f968db615`。

- 関連229件成功、7件スキップ。`test_walk.py`、`test_page_set.py`、`test_wiki_links.py`、`test_raw_links.py`、`test_wiki_lint.py`、`test_wiki_youtube.py`。PyYAML、numpy、usearch、tantivy の依存を入れて実行した。
- 新規の `test_raw_links.py` は31件成功、1件スキップ。実際のハードリンク、ファイルの symlink、ディレクトリのジャンクションを含む。スキップは POSIX の制御文字と Unicode 正規化の違う名前の試験で、Windows では名前を作れない。
- `test_mcp_server.ScriptToolTests` 5件成功。実際のサーバーと中継を通す。追加した raw_root の試験は CLI と全結果が一致し、リンクを missing_raw に落とさず、原本が変わらないことを検査する。
- プラグイン内の `eval/scripts` は116件成功。
- `eval/check_encoding.py` は63ファイルを検査し、encoding の付け忘れなし。compileall と両リポジトリの `git diff --check` も成功。

最初の実行では依存なしのため PyYAML の試験が実行できず、段階1の「raw の検査はまだない」という2つの期待値と、読み取り箇所の目録も落ちた。依存を入れ、意図して変わった期待値を更新し、上記の実行で成功した。失敗を含めた数を成功数に加算していない。

他 OS の CI と、Opus の敵対的レビューは別の記録とする。これらを手元の成功から推定しない。
