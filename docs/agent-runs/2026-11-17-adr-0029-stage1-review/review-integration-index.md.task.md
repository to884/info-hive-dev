GitHub の自動レビューの P2 を直しました。前の全体のレビューは繰り返さず、この小さな差分だけを確認してください。変更禁止、委譲とCI待機は不要です。
wiki_pages.refused_link の .md の項目を照合する条件について、kind == path のときは is_article_path、kind == slug のときは従来どおり is_page_path を使うようにしました。記事に含まれる indexes/topic.md の拒否を、[[indexes/topic|Topic]] で明示した場合も拒否と表示し、裸の [[topic]] は索引の記事と結び付けません。
新しい実行試験 test_refused_index_article_matches_an_explicit_path_only は、ハードリンクの indexes/topic.md と index.md の明示的な参照を作り、Core.resolve と描いた HTML の両方を検査しています。74件合格、Windows skip4です。
この条件と試験に既存規則の後退があるかだけ結論にしてください。前回の比較リンクは afa19f8 で修正済み、POSIX は CI の73件が通過し、今回の試験を追加したCIを別に確認します。
