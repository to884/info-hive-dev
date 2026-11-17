# 第2回の軽微の修正と main 統合の最終レビュー

同じ段階2の続きです。第2回は採用可・重大なしでした。今回はその軽微を閉じた差分と、並行公開の概要機能を統合した差分に絞って敵対的に確かめてください。編集・再委譲はしないでください。分担・範囲外は前回と同じです。

read: review-2-disposition.md（この task と同じディレクトリ）、docs/plans/adr-0029-stage2-raw-links.md。

プラグインは別Gitリポジトリです。mainの d761c62（0.32.0）をrebaseで取り込み、今回は0.33.0にしました。raw の差分は `git -C info-hive-wiki diff d761c62..HEAD` で見られます。最終の軽微の直しはコミット8005b39です。wiki_lint の概要とrawの検査、SERVER_FILES の両方の依存を残した競合解消も対象です。概要機能全体の再レビューは要求しません。

主な直し:
- セッションとYouTubeのwriteで、`..` のある根を取得・保存の前に拒否。
- 訂正の根拠のsourceの拒否・不確かさを、使うときの bad_definition の理由に保持（EvidenceUnavailable）。
- url/session_id の1要素配列をそろえ、複数要素はunknown。
- mismatches に版・身元の不一致の候補と理由を保持し、lintで欠落と区別。
- rootless lint の links 件数を一覧に合わせ、links_wiki / links_raw で未検査を区別。
- 根を省いた外の原本の判定の未確認を scope_unverified として警告へ保つ。
- 1つの一致候補の実体の比較にはFileIdInfoを要求しない。複数候補の同一性とディレクトリの輪の検査には要求。

追加した試験は tests/wiki/test_raw_links.py、test_wiki_youtube.py、test_wiki_session.py の該当メソッド。統合後の関連252件（skip7）が成功しました。原本・記事のリンクを読む迂回、拒否を欠落へ落とす経路、今回の直しによる退行があれば、再現と根拠を示してください。第2回の指摘の閉鎖と判定を短くまとめ、既に閉じた大きな部分の説明の繰り返しは不要です。
