# 第6回の最終確認：直前の2件の修正と、その副作用

同じ第6回の継続である。直前の review-6-continued.md で、第5回の5件と第6回の最初の3件の元の反例は閉鎖と確認された。ただし、新しく重大B（tree の一覧エラーが空に化ける）と重大D（POSIX の名前のバックスラッシュを区切りに変えて別ファイルを読む）、対応する試験不足が残った。この2件を修正した。

今回のレビュー対象は、直前の報告の2件の閉鎖と、以下の差分が既存の読み取りの境界を崩していないかである。既に照合した無関係なモジュールを最初から再調査する必要はない。

親: C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl
プラグイン: 親の info-hive-wiki/
記録: 親の docs/agent-runs/2026-11-17-adr-0029-stage1-review/

読むもの:
- review-6-final.delta.diff: 直前の報告の時点から、現在までの実ファイル3本の差分（差分どうしの比較ではない）。
- 現在の wiki_pages.py、wiki_evolve.py、親の tests/wiki/test_wiki_links.py。
- review-6-continued.md: 直前の最終報告。
規範と段階1の範囲は task-6.md、前回までの閉鎖の根拠は既存の報告のまま。

修正:
1. tree の os.walk に onerror を渡し、一覧取得で失敗したら元の例外を呼び出し元へ伝える。evaluate/run と copy_tree が、一覧できなかった木を空の入力として受け取らず、そのまま止まる。CLI は既存の OSError のエラー処理で理由と場所を表示する。
2. コマンドの相対パス表記と、OS 上のファイル名の表現を分けた。is_page_path/is_article_path/article_path は native キーワードを持ち、既存のコマンド表記は従来どおり。一方 _article_rel が OS 上のパスから作った相対名は user_file_path が native=True で分類・検査する。POSIX ではファイル名中のバックスラッシュを残し、Windows では既存の区切りの扱いを保つ。コロン・途中の ..・根と部分木の所属・ディレクトリの検査は保持している。

回帰:
- 実際の os.walk に対して os.scandir の PermissionError を注入し、根と途中のディレクトリのどちらが一覧不可でも tree/copy_tree が例外を伝え、空のコピー先を作らないこと。
- evaluate/run の両入口が、この一覧不可で契約検査より前に止まり、入力や実行の記録を開始しないこと。
- POSIX のパスと属性を差し替え、concepts/a\b.md と assets\p.md について、文字列・バイト列の両入口が指定した同じファイルを読むこと。指定したファイルの属性がハードリンクなら、デコイに逃げず拒むこと。
- POSIX の実ファイルの候補とデコイを使う試験も追加したが、Windows のため skip。

最新の検証結果: test_wiki_links 62件(skip6)、test_walk 18件(skip2)、test_wiki_evolve_newlines 12件、test_page_set 30件(skip1)、PyYAML を用意した環境の test_uninitialized_wiki 41件(skip2)、すべて成功。計163件(skip11)。eval/evolution/test_evolution.py と test_adapters.py の実行可能な統合チェック2本も PASS。両リポジトリの git diff --check も通過した。POSIX の実ファイルを使う3件は Windows で skip しており、属性等を差し替えた確認と混同しない。

日本語で、指定書式の最終報告を全文で返す。直前の2件と試験不足を個別に判定し、今回の差分による問題があれば具体的な反例と現在の行番号を示す。第5回の5件と前ターンまでの閉鎖を含む全体の判定は、今回の確認と過去の確認を区別して記載する。対象ファイルは変更せず、再委譲や別モデルの起動をしない。必要な検証に絞り、理由なく全試験を繰り返さない。修正案を出さず、重大の発生度 A〜D、実測・モック・推論の区別を保つ。
