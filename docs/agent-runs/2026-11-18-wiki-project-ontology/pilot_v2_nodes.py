"""第 2 版の対象と関係。node と rel は生成器から渡される。"""
node("product:info-hive-rag", "info-hive の rag プラグイン", ["pdf", "wording"], "版に依存しない製品の識別子。")
node("product:info-hive-wiki", "info-hive の wiki プラグイン", ["agent", "yt_impl"], "版に依存しない製品の識別子。")
node("product:claude-sonnet", "Claude Sonnet", ["models"], "5.5 は release ノードで記録する。製品と版を分離した登録。")
node("product:yt-dlp", "yt-dlp", ["yt_impl"], "特定の版は release_of でこの製品へ結ぶ。")
node("release:claude-sonnet-5.5", "Claude Sonnet 5.5", ["models"], "製品: Claude Sonnet。版: 5.5。使用された版の記録であり、公開日時はこの出典から確定しない。", [rel("release_of", "product:claude-sonnet", "E07", "比較で使用されたモデル名を製品と版に分けた登録。")])
node("release:yt-dlp-2026.8.19", "yt-dlp 2026.8.19", ["yt_impl"], "製品: yt-dlp。版: 2026.8.19。固定された依存の実体。", [rel("release_of", "product:yt-dlp", "E13", "PEP 723 の依存指定を製品と版に分けた登録。")])
node("component:rag-pdf-reader", "rag の PDF 読み取り", ["pdf"], "read_pdf という責務の構成要素。問題の有効な版は affects の release を読む。", [rel("part_of", "product:info-hive-rag", "E01", "rag の read_pdf という所属関係。現在の動作の保証ではない。")])
node("release:rag-0.5.0", "rag 0.5.0", ["pdf"], "製品: rag。版: 0.5.0。観測された問題が残る固定の版であり、現在の最新版を意味しない。", [rel("release_of", "product:info-hive-rag", "E01", "問題が観測された版。")])
node("issue:rag-pdf-prefix-rejected", "先頭に 1 バイトの改行がある PDF 2 件の拒否", ["pdf"], "対象版: rag 0.5.0。観測: seL4 の PDF 2 件の先頭に改行が 1 バイトあり、ヘッダー判定で拒否。任意長の前置きや、すべての不正 PDF を受け付ける要求ではない。", [rel("affects", "release:rag-0.5.0", "E24", "先頭 1 バイトの改行がある観測 2 件。read_pdf のヘッダー判定。版を固定して記録し、現在の rag への障害とは読まない。")])
node("change:rag-pdf-prefix-1024", "PDF の前置きを 1024 バイトまで受け付ける変更", ["pdf"], "実施済み: rag PR #7。ヘッダー判定の受け付け範囲を変更。1 バイトの改行で拒否された観測 2 件を解消した。1024 バイトを超える前置きは引き続き対象外。MCP→索引化は未確認。", [rel("changes", "component:rag-pdf-reader", "E02", "read_pdf のヘッダー判定。"), rel("fixes", "issue:rag-pdf-prefix-rejected", "E25", "対象は先頭 1 バイトの改行がある 2 件。任意の前置きの拒否全般を直したという意味ではない。")])
node("release:rag-0.5.1", "rag 0.5.1", ["pdf"], "製品: rag。版: 0.5.1。公開日: 2026-11-12。出荷した変更の記録は本試料では PDF の判定の修正だけを採録した。", [rel("release_of", "product:info-hive-rag", "E03", "rag v0.5.1 の公開。"), rel("delivers", "change:rag-pdf-prefix-1024", "E26", "受け付け範囲を変えた版が 0.5.1 と明記され、公開は E03 に記録。")])
node("evaluation:rag-051-pdf-direct", "rag 0.5.1 の実 PDF の直接抽出の確認", ["pdf"], "対象: PR #7 の修正後の read_pdf と extract_pages。方法: 実 PDF 2 件、OCR off。観測結果: 70 ページと 18 ページのテキスト。限界: register_pdf→索引化は未実施。変更・出典の本文を回答時に必ず読む。", [rel("evaluates", "change:rag-pdf-prefix-1024", "E04", "直接経路だけの確認。全経路の成功は未確認。")])
node("evaluation:ingest-models-20261113", "2026-11-13 の Web raw のモデル比較", ["models"], "対象: Sonnet 5.5 ほか 3 モデル × 4 Web ページ、各組 1 回。取り込み全体を各モデルで実行し、評価したのは raw。後段の記事の品質と費用比は評価していない。", [rel("evaluates", "release:claude-sonnet-5.5", "E07", "比較した特定版のモデル。一般の Sonnet 全版には広げない。")])
node("decision:ingest-sonnet-20261113", "比較後も取り込みを Sonnet 5.5 で続ける判断", ["models"], "記録日: 2026-11-13。当時の運用は取り込み全体を Sonnet にしていた。根拠の測定範囲は raw。11-14 の raw の分担とは別の判断であり、現在の全ホストの設定ではない。", [rel("selects", "release:claude-sonnet-5.5", "E08", "11-13 時点で継続したモデルの特定版。"), rel("motivated_by", "evaluation:ingest-models-20261113", "E17", "比較の紹介と結論が同じ段落に明記されている。測定は raw に限られる。")])
node("decision:web-raw-split-20261114", "raw の段を Sonnet のエージェントに分担する設計", ["trial"], "記録日: 2026-11-14。正確な決定日時は未確定。選択: raw を専用の Sonnet、後段をメインのモデルに分担する。前日の全体の継続とは別の範囲。正式な撤回・差し替えを示す一次記録がないため supersedes は補わない。", [rel("selects", "release:claude-sonnet-5.5", "E19", "raw だけの分担。11-13 の全工程への選択と混ぜない。")])
node("component:wiki-web-raw", "wiki の Web raw 作成", ["agent", "trial"], "専用エージェントの有無を超えた工程の責務。取得後の整理、訳、画像の補足。", [rel("part_of", "product:info-hive-wiki", "E18", "wiki の raw を作る段の所属。")])
node("change:wiki-web-raw-agent", "Web raw の段を専用エージェントに任せる変更", ["agent", "trial"], "実施済み。範囲は raw の分担。11-14 の分担の設計を実装した。", [rel("changes", "component:wiki-web-raw", "E18", "raw の作成の分担だけの変更。"), rel("implements", "decision:web-raw-split-20261114", "E19", "raw と後段を分けた実行が観測された。比較の判断の日付とは別。")])
node("release:wiki-0.15.0", "wiki 0.15.0", ["agent"], "製品: wiki。版: 0.15.0。タグ: 5adb069。marketplace では 0.16.0 が入ったため、この版の導入確認とは扱わない。採録は raw の分担の変更のみで、変更一覧の完全性は主張しない。", [rel("release_of", "product:info-hive-wiki", "E10", "タグの製品と版。"), rel("delivers", "change:wiki-web-raw-agent", "E10", "raw の変更のタグと公開という直接の報告。")])
node("concept:ingestに使うモデル", "/wiki:ingest に使うモデル", ["models", "trial"], "", [rel("applies_to", "component:wiki-web-raw", "E18", "現行の概念ページが説明する分担の範囲。概念は手順と条件、decision は日付のある選択であり同一対象ではない。")], existing="wiki/concepts/ingestに使うモデル.md")
node("component:wiki-youtube-ingest", "wiki の YouTube 字幕の取得", ["yt_impl"], "この試料では字幕を取得する責務だけを指す。query や lint の変更の全体とは区別する。", [rel("part_of", "product:info-hive-wiki", "E20", "wiki に足した字幕取得スクリプトの責務。")])
node("decision:adr-0027-captions", "ADR-0027 の字幕を固定した yt-dlp で取る判断", ["yt_design"], "具体的な選択: yt-dlp の版を 1 つに固定して字幕だけを取る。特定の数値の版を永続的に選ぶ判断とはしない。", [rel("selects", "product:yt-dlp", "E15", "製品の選択と版を固定する方式。実装で使った数値の版は release 間の depends_on へ記録する。")])
node("change:wiki-youtube-v0230", "PR #74 の字幕取得スクリプトの追加", ["yt_impl"], "実施済み。PR #74 全体ではなく、wiki_youtube.py を足し字幕取得を固定した依存で行う部分のみ。別の query/lint の変更はこの change の範囲外。", [rel("changes", "component:wiki-youtube-ingest", "E20", "字幕取得の追加。PR の変更全体の索引ではない。"), rel("implements", "decision:adr-0027-captions", "E13", "字幕の取得のスクリプトで yt-dlp を固定した実装。ADR の全要件の充足やレビュー合格は意味しない。")])
node("component:wiki-query-confidence", "wiki の回答の確信度の規則", ["yt_impl"], "query-confidence.md の表が扱う責務。", [rel("part_of", "product:info-hive-wiki", "E22", "wiki の回答の確信度の表。")])
node("artifact:wiki-query-confidence", "query-confidence.md", ["yt_impl"], "repository: info-hive-wiki。path: skills/info-hive/references/query-confidence.md。controlled artifact。記事の要約 source とは別。", [rel("part_of", "component:wiki-query-confidence", "E22", "回答の確信度の表を格納する文書。")])
node("change:wiki-youtube-confidence-v0230", "動画ソースの確信度の上限の表への追加", ["yt_impl"], "実施済み。PR #74 のうち query-confidence.md に動画のソースの行を足した変更。採録範囲を分離し、字幕の取得だけからこの変更を推論させない。", [rel("changes", "artifact:wiki-query-confidence", "E22", "文書の変更先を直接示す。")])
node("release:wiki-0.23.0", "wiki 0.23.0", ["yt_impl"], "製品: wiki。版: 0.23.0。タグ: 1252fda。PR #74 の変更のうち本試料は字幕取得と回答の確信度の表の 2 件だけを採録し、全件の変更一覧とはしない。", [rel("release_of", "product:info-hive-wiki", "E12", "wiki 0.23.0 の出荷。"), rel("delivers", "change:wiki-youtube-v0230", "E21", "#74 の字幕取得の追加 E20 を含むマージコミットをタグが指す。"), rel("delivers", "change:wiki-youtube-confidence-v0230", "E21", "#74 の表の追加 E22 を含むマージコミットをタグが指す。"), rel("depends_on", "release:yt-dlp-2026.8.19", "E13", "wiki 0.23.0 の字幕取得で固定した版。現在の製品全体への無版の依存とはしない。")])
artifacts = [
    ("rag-readme", "rag の README", "repository: info-hive-rag。path: README.md。"),
    ("rag-changelog", "rag の CHANGELOG", "repository: info-hive-rag。path: CHANGELOG.md。"),
    ("rag-index-comments", "rag_index.py のコメント", "repository: info-hive-rag。path: scripts/rag_index.py。変更範囲: PDF ヘッダーのコメント。"),
    ("rag-v051-release-notes", "rag v0.5.1 のリリース本文", "repository: to884/info-hive-rag。URL: https://github.com/to884/info-hive-rag/releases/tag/v0.5.1。対象は公開文面。"),
    ("dev-adr-0013", "親リポジトリの ADR-0013", "repository: info-hive-dev。識別子: ADR-0013。記事に正確なファイル名がないため、パスを推測で補わない。"),
]
for key, title, body in artifacts:
    node("artifact:" + key, title, ["wording"], body)
node("change:rag-header-wording-v052", "rag 0.5.2 の PDF ヘッダーの書き方の統一", ["wording"], "実施済み。コードの受け付け条件を変えず、README、CHANGELOG、コメント、リリース本文、親の ADR の記述をそろえた。v0.5.3 のエラーメッセージの変更とは別。", [rel("changes", "artifact:" + key, "E06", "E06 に列挙された文書・コメントの直接の変更。") for key, _, _ in artifacts])
node("release:rag-0.5.2", "rag 0.5.2", ["wording"], "製品: rag。版: 0.5.2。公開日: 2026-11-13 JST。採録は PDF ヘッダーの文書の変更のみ。", [rel("release_of", "product:info-hive-rag", "E23", "公開した製品と版。"), rel("delivers", "change:rag-header-wording-v052", "E06", "文書の修正を rag 0.5.2 で行ったと明記され、公開は E23 に記録。")])
