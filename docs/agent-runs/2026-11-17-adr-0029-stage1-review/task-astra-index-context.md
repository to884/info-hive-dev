公開前の最後の小差分の独立した敵対的レビューです。変更禁止、読み取り専用。再委譲や別モデルの追加レビューは不要です。レビュー作業なので実装完了時の自動レビューは発生しません。
Opus は main 統合後の大きな変更を複数回レビューし、重大なし・条件付き採用可でした。最後の索引の文脈分離の再確認だけ、5時間の利用上限で実行できなかったため、ユーザーが指定していた Astra で確認します。
対象は integration-index-context.diff（plugin fb4d6c4..4b751a2）と現ファイルです。refused_link の既定はページだけ。articles=True の場合だけ、パスで指定した索引の記事まで拒否を照合します。Core.resolve は本文でFalse、Index の _nav_item だけTrueを渡します。lint と sources の分類、グラフは既定のFalseです。
満たす条件:
- index.md の [[indexes/topic|Topic]] が、リンクで拒否した索引の記事を指すときは「ページがない」ではなく「リンクなので読まない」を描く。
- 同じ索引を、本文の [[indexes/topic]] や sources: ["[[indexes/topic]]"] に使うとページとしては誤りなので、索引がリンクになっても lint の指摘を消さない。
- 裸の [[topic]] は索引の記事に結び付けない。ページのパスとスラッグの照合は従来どおり。
- リンクの索引のディレクトリ indexes/blocked の下も、本文とIndexの文脈に従う。
追加した test_refused_index_article_matches_an_explicit_path_only は実ファイルのハードリンクを使い、Core.resolve/HTML/lint のすべてを検査します。関連246件合格、Windows skip9です。
前の全体の設計と生じていない仮定を広げず、この差分による後退や未対応の反例を指摘してください。未実行のCIは依頼元が待つので、自分で待つ必要はありません。
