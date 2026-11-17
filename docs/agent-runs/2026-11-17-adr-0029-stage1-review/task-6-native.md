# 第6回の残る軽微な指摘の確認：OS 上の名前の受け渡し

同じ第6回の継続。直前の review-6-final.md は条件付きで採用可、重大なし、軽微1件（walk_pages が OS 上の名前を native=True で分類していない）だった。これを修正し、同じ原因が残る実ファイルの呼び出し元もそろえた。

親: C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl
プラグイン: 親の info-hive-wiki/
記録: 親の docs/agent-runs/2026-11-17-adr-0029-stage1-review/

今回の差分は review-6-native.delta.diff。前回からの実ファイルの差分である。対象はこの差分と、その呼び出し元のデータの意味の一致。既に照合した無関係なモジュールを最初から再調査する必要はない。規範・段階1の範囲、これまでの閉鎖判定は維持する。

OS 上の名前を渡す箇所:
- walk_pages が走査の f.rel を is_page_path に渡す箇所。
- wiki_stats が走査の found.rel を is_page_path に渡す箇所。
- wiki_lint が走査の link_report にある item.path を is_page_path に渡す箇所。
- propose の根拠ページの Path から作った相対名を article_path に渡す箇所。
- WikiIndex.get_page で、マッチした物理的な path を相対化して article_path に渡す箇所。
- list_index が走査の f.rel を article_path に渡す箇所。
以上を native=True にした。利用者が入力するコマンド表記の相対名、検索が返す canonical rel_path、生成する固定名等の既存の表記は、そのままのモードにしている。native の定義そのもの、根の判定、ディレクトリの検査、onerror の例外伝播、途中の .. の拒否は前回と同じ。

回帰の追加:
- POSIX 条件の paths/属性を差し替えた既存の試験で、assets\p.md を含む走査結果が walk_pages でも記事として残り、文字列/バイト列の入口の記事判定と一致すること。
- 実際の propose の根拠ページの分岐を動かし、指定した native 名から ORIGINAL を読み、デコイを読まないこと。ハードリンクなら本文を読まず拒むこと。書き込みを始める直前で止めている。
- 実際の WikiIndex.get_page のマッチ後の分岐でも、同じ native 名の本文を返し、ハードリンクなら拒むこと。物理ファイルの path と表示用の名前を区別した検査である。
- POSIX 実機用の既存の試験に、propose の根拠の本文と list_index のファイル名/題名の一致を追加した。この Windows 環境では skip。

最新結果: test_wiki_links 63件(skip6)、test_walk 18件(skip2)、test_wiki_evolve_newlines 12件、test_page_set 30件(skip1)、PyYAML を用意した test_uninitialized_wiki 41件(skip2)、すべて成功。計164件(skip11)。評価のライフサイクルとアダプターの実行可能な統合チェック2本も PASS。親とプラグインの git diff --check も成功した。

日本語で指定書式の最終報告を全文で返す。残った軽微な指摘の閉鎖と、今回の受け渡しの変更による副作用を確認する。既存の第5回5件・第6回で閉鎖した重大な指摘は、過去の確認と今回の確認を分けて判定を記す。対象のファイルは変えず、他のモデルへの再委譲はしない。必要な検証に絞り、理由なく全試験を繰り返さない。今回確認していない機能まで検証済みとはしない。
