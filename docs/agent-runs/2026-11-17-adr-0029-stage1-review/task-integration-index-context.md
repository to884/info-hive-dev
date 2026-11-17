前回の索引に関する小さな差分の続きです。integration-index-context.diff の8行程度の処理の変更だけを確認してください。変更禁止、委譲とCI待機は不要です。
refused_link の既定はページだけに戻し、articles=True の場合だけ、パスで指定する索引の記事も照合します。Core.resolve に同じ任意のキーワードを足し、_nav_item（Index の行）だけがTrueを渡します。本文・sources・lint・グラフはFalseのままです。
拒否したディレクトリの下のパスも、本文ではページとして有効なパスだけ、Index では記事として有効なパスだけを照合します。そのため indexes/blocked/x のような行き先も、本文とIndexで同じ誤りを再発させません。
試験は、Indexの[[indexes/topic|Topic]]が拒否として描かれること、Coreの通常の本文の解決は unresolved であること、lintの本文とsourcesの指摘は索引がリンクでも消えないこと、索引のディレクトリの下も文脈に従うことを検証します。関連246件が合格 skip9。
この差分が前回の後退を閉じるか、既存の照合に後退を作るかのみ結論にしてください。
