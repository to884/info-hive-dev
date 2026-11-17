# 第5回レビュー前の確認（2026年11月17日）

コードは変更せず、第4回の review-4.md.target.diff と現在の git diff HEAD を照合した。プラグインの差分だけでなく、未追跡の wiki_links.py と親の試験をレビュー対象に含める。

| 第4回の指摘 | 現在の対応 | 確認の限界 |
| --- | --- | --- |
| 根のリンクの実体側で read_user_file を迂回できる | _article_rel が根の綴りと realpath、入力の綴りと親の realpath を比較する | 境界条件まで正しいかは第5回で再確認 |
| 字幕 --page と evolve --candidate の直接読み取り | 前者は read_user_file、後者は article_path の検査後に読む | candidate 用の個別の回帰試験はない |
| コピー前に corpus のリンクの記事を読む | run の先頭で find_links の結果を検査する | 専用の回帰試験はソース内の順序を検査するもので、実行時の反例検査ではない |
| Windows の CLI の大小文字で警告が消える | _same_dir は samefile、失敗時 normcase。サーバー名は lower | 専用試験は _same_dir 単体の検査 |
| test_walk の indexes のハードリンクの誤分類 | model_index/expected_calls の扱いを変更 | test_walk 全体の通過を確認 |
| Path.open の分類漏れ | AST で属性の open も拾う | 分類の内容が妥当かは別途レビューが必要 |

実行した試験:
- python tests/wiki/test_wiki_links.py: 40件、成功、3件 skip（4.635秒）
- python tests/wiki/test_walk.py: 18件、成功、2件 skip（5.261秒）

現時点の照合では第4回の6件すべてに対応する変更がある。修正の閉鎖判定と新たな欠陥の探索は、Astra の独立した第5回レビューで行う。リリース、コミット、バージョン変更は行っていない。
