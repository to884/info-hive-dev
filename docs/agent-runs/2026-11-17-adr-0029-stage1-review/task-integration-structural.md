前回の3件を直した同じレビューの続きです。この差分のみを敵対的に確認してください。変更禁止、委譲不要、大規模なテストやCI待機は不要です。
差分 integration-structural-fixes.diff。プラグイン HEAD 8b69eb3。
1. _article_rel の外の別名の解決を構造から変更しました。既知の根そのものの realpath は計算しますが、入力の祖先には realpath を使いません。lstat でリンクの種類を見て os.readlink の行き先を1つずつ展開します。既知の根に到達したら残りは解決せず article_path に渡します。リンクから根へ戻る道も、一度に samefile で根へ飛ばさず、リンクを先に展開します。外の相対的なリンクの .. は根に届く前だけ処理し、根に届いた時点で残りに .. があれば拒否します。64回を超えるリンクは循環等として拒否します。Windows の外の view が wiki/concepts/jump -> ext を指す反例は、手元で拒否しました。POSIX の相対的な別名と循環も回帰テストに加えています。
2. graph.collect_pages は同じ walk_pages の1回の走査のページと拒否を GraphPages に載せて返します。build_edges はその拒否情報、browse は snapshot 由来の拒否情報を明示して渡します。本文の mentions と sources の sourced_from は、拒否した名前を別ページに結び付けず、拒否を unresolved_source ともしません。CLI と MCP は既存の走査の通知を保ちます。
3. lint は resolve_available を被リンク、索引の種類、本文のリンク切れで共用し、拒否を先に判定します。明示的に読める別のパスを指すリンクは有効です。
回帰: 262件合格（Windows skip10）、plugin eval/scripts116件合格、文字コード61ファイル合格です。CI の links 試験に PyYAML も加え、グラフの分岐を6構成で実行します。
残る実装の欠陥があれば再現条件付きで示してください。新たな設計要件や、未実行のCIを待つことは依頼に含みません。
