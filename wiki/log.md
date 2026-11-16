# Wiki のログ

wiki に対する操作を時系列で記録する、追記専用のログである。各項目は `## [YYYY-MM-DD] <操作名> | <説明>` で始めるので、`grep "^## \[" log.md | tail -N` で抜き出せる。操作名は下の英語のまま書き、説明は日本語で書く（`## [2026-11-03] ingest | インボイス制度の手引き`）。補足の行は、3文字の空白で字下げして続ける（`   グラフ: ノード +4、型付きエッジ +2`）。

操作の種類:
- `ingest`: ソースを wiki に取り込んだ。
- `query`: wiki をもとに質問に答えた（通常は、回答をシンセシスとして保存したときだけ記録する）。
- `lint`: 健全性のチェックを実行した。
- `schema`: スキーマを変更した。
- `shard`: インデックスを分割した。

---

## [2026-11-11] schema | タグの体系に グラフ、browse、試験、リリース を足した

## [2026-11-11] ingest | wiki 0.9.2 のグラフの抽出の修正の記録
   ページ: sources/グラフの抽出の修正-0.9.2、concepts/グラフの抽出の契約、concepts/エッジの識別子、concepts/グラフのlintの期待値

## [2026-11-12] schema | タグの体系に rag を足した

## [2026-11-12] ingest | rag 0.5.1 の PDF のヘッダーの判定の修正の記録
   ページ: sources/pdfのヘッダーの判定の修正-rag-0.5.1、concepts/pdfのヘッダーの条件

## [2026-11-12] ingest | wiki 0.11.1 の取り込み手順の追従と、wiki 0.11.1・rag 0.5.1 のリリースの記録
   ページ: sources/取り込み手順の追従とリリース-wiki-0.11.1、concepts/リリースの確かめ方

## [2026-11-13] schema | タグの体系に windows を足した

## [2026-11-13] ingest | Git Bash のパス変換で git の引数が壊れる件
   ページ: concepts/git-bashのパス変換（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | rag 0.5.2 の PDF のヘッダーの境界の書き方の修正
   ページ: concepts/pdfのヘッダーの条件（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | rag 0.5.3 の PDF のヘッダーのエラーメッセージの修正
   ページ: concepts/pdfのヘッダーの条件（sources/pdfのヘッダーの判定の修正-rag-0.5.1 を更新）

## [2026-11-13] ingest | rag 0.5.2・0.5.3 の書き方とメッセージの修正、リリースの記録
   ページ: sources/pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3（concepts/リリースの確かめ方、concepts/pdfのヘッダーの条件 を更新）

## [2026-11-13] ingest | Windows の Python で書き戻すと LF が CRLF に変わる件
   ページ: concepts/pythonの書き戻しの改行（sources/取り込み手順の追従とリリース-wiki-0.11.1 を更新）

## [2026-11-13] ingest | browse のスコープ表示、wiki 0.12.0 のリリースと画面の確かめの記録
   ページ: sources/browseのスコープ表示とリリース-wiki-0.12.0、concepts/browseの画面の確かめ方（concepts/リリースの確かめ方 を更新）

## [2026-11-13] ingest | 検索の結果の tags と sources の修正、wiki 0.12.1 のリリースの記録
   ページ: sources/検索の結果のtagsとsourcesの修正-wiki-0.12.1、concepts/frontmatterのリストの値（concepts/リリースの確かめ方、concepts/git-bashのパス変換 を更新。SCHEMA.md のタグの体系に `検索` を足した）

## [2026-11-13] ingest | title が値なしや配列のときの修正、wiki 0.12.2 のリリースの記録
   ページ: sources/titleが値なしや配列のときの修正-wiki-0.12.2（concepts/frontmatterのリストの値、concepts/リリースの確かめ方、concepts/pythonの書き戻しの改行 を更新）

## [2026-11-13] ingest | 初期化していないディレクトリを wiki として扱わない修正、wiki 0.13.0 のリリースの記録
   ページ: sources/初期化していないディレクトリの扱い-wiki-0.13.0、concepts/初期化されたwikiの判定（concepts/リリースの確かめ方、sources/titleが値なしや配列のときの修正-wiki-0.12.2 を更新）

## [2026-11-13] ingest | /wiki:ingest のモデルの比較（2026-11-13）
   ページ: sources/ingestのモデルの比較-2026-11-13、concepts/ingestに使うモデル（SCHEMA.md のタグの体系に `取り込み` を足した）

## [2026-11-14] ingest | /wiki:help の個別のヘルプと、wiki 0.14.0 のリリースの記録
   ページ: sources/helpの個別のヘルプとリリース-wiki-0.14.0、concepts/コマンドの引数の渡し方、concepts/コマンドの出力のリンク（concepts/リリースの確かめ方 を更新。SCHEMA.md のタグの体系に `コマンド` を足した）

## [2026-11-14] ingest | LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計
   ページ: sources/llm-wiki記事作成の方法論、concepts/記事作成の5区分（SCHEMA.md のタグの体系に `wiki設計` を足した）
   グラフ: ノード +2、型付きエッジ +0

## [2026-11-14] ingest | type と updated を配列や値なしで書いたページの扱いの修正、wiki 0.14.1 のリリースの記録
   ページ: sources/typeとupdatedの配列の扱いの修正-wiki-0.14.1（concepts/frontmatterのリストの値、concepts/リリースの確かめ方 を更新）
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-14] ingest | Claude Code のセッションを wiki に取り込む設計の記録（ADR-0020）
   ページ: sources/セッションの取り込みの設計-2026-11-14、concepts/セッションの記録の構造、concepts/editとwriteの書き込みの競合（新規）
   グラフ: ノード +3、型付きエッジ +0

## [2026-11-14] update | /wiki:ingest に使うモデル（raw の段だけを Sonnet にする）
   ページ: concepts/ingestに使うモデル（グローバルの指示を消し、0.15.0 からエージェント wiki:web-raw が raw の段を行うことを書いた）

## [2026-11-14] ingest | raw の段を任せるエージェントの実地の確かめ（2026-11-14）
   ページ: sources/rawの段を任せるエージェントの確かめ-2026-11-14（sources/ingestのモデルの比較-2026-11-13 にモデルごとの比較の表を足し、concepts/ingestに使うモデル を更新）

## [2026-11-14] ingest | 次の版に追い越されたあとの wiki 0.15.0 のリリースの記録
   ページ: sources/追い越された版のリリース-wiki-0.15.0（concepts/リリースの確かめ方 を更新）

## [2026-11-14] create | browse のデザインシステム（Fluent 2）
   ページ: concepts/browseのデザインシステム（ADR-0021 の決定と、設計のレビューで崩れた配色と折り返しの前提）。concepts/browseの画面の確かめ方 に配色の切り替えの確かめ方を足した

## [2026-11-15] ingest | wiki 0.16.0（セッションの取り込み）のリリースの記録
   ページ: sources/セッションの取り込みのリリース-wiki-0.16.0（concepts/リリースの確かめ方 を更新）

## [2026-11-15] ingest | wiki の書く段の設計の記録（ADR-0023）
   ページ: sources/wikiの書く段の設計-2026-11-15、concepts/敵対的レビューで設計を直す進め方（新規。concepts/editとwriteの書き込みの競合 を更新）
   グラフ: ノード +2、型付きエッジ +0

## [2026-11-15] ingest | wiki 0.17.0（browse の構造の直し）のリリースの記録
   ページ: sources/browseの構造の直しとリリース-wiki-0.17.0（concepts/リリースの確かめ方 を更新）

## [2026-11-15] update | browse の探しやすさと Fluent 2 の実装（wiki 0.18.0）
   ページ: concepts/browseのデザインシステム（実装の段で分かったこと）、concepts/browseの画面の確かめ方（0.18.0 のスコープの色）

## [2026-11-15] ingest | browse の探しやすさと Fluent 2 と wiki 0.18.0 のリリースの記録
   ページ: sources/browseの探しやすさとFluent2のリリース-wiki-0.18.0（concepts/リリースの確かめ方 を更新）

## [2026-11-15] update | raw の段を任せるエージェントの確かめの主張を狭めた
   ページ: sources/rawの段を任せるエージェントの確かめ-2026-11-14（ほかの担当が動かさなかったことは記録から示せないので、合否を決めない一覧に移したことを書いた）

## [2026-11-15] update | W8 の終わりを JSON の出力で決めるようにした（wiki 0.18.1）
   ページ: sources/rawの段を任せるエージェントの確かめ-2026-11-14（文字の出力ではページの本文と見分けられないので、W8 を --json で動かし、値の中の改行のあとを字下げしたことを書いた）

## [2026-11-15] ingest | raw の段の取り直しと W8 の出力の直しと wiki 0.18.1 のリリースの記録
   ページ: sources/rawの段の取り直しとW8の出力のリリース-wiki-0.18.1（concepts/リリースの確かめ方 を更新）

## [2026-11-15] ingest | browse の記事のページの Fluent 2（段 F2）と wiki 0.19.0 のリリースの記録
   ページ: sources/browseの記事のページのFluent2のリリース-wiki-0.19.0（concepts/browseのデザインシステム、concepts/リリースの確かめ方 を更新）

## [2026-11-15] ingest | browse の stop の記録の読み取りの直し（wiki 0.19.1）
   ページ: sources/stopの記録の読み取りの直し-wiki-0.19.1、concepts/windowsのファイルの共有と削除待ち（新規）

## [2026-11-15] ingest | 今の取り込みと MarkItDown の抽出の比較（2026-11-15）
   ページ: sources/抽出の方式の比較-markitdown-2026-11-15、concepts/抽出の品質の測り方（新規）

## [2026-11-15] ingest | /wiki:learn で、ベンチマークの作業の経験 5 つを記録した
   ページ: sources/extraction-metrics-string-presence-2026-11-15、sources/blind-judge-binding-and-form-feed-2026-11-15、sources/office-com-word-export-2026-11-15、sources/powershell-select-first-stops-writer-2026-11-15、sources/evolve-capture-writes-crlf-2026-11-15（新規）、concepts/officeのcomでの書き出し、concepts/powershellのパイプの打ち切り（新規）、concepts/抽出の品質の測り方、concepts/pythonの書き戻しの改行（更新）

## [2026-11-15] ingest | capture の記録の改行と sha256 の直し（wiki 0.19.2）と、0.19.1 と 0.19.2 のリリース
   ページ: sources/captureの記録の改行の直しとリリース-wiki-0.19.2（concepts/リリースの確かめ方、sources/stopの記録の読み取りの直し-wiki-0.19.1 を更新）

## [2026-11-15] update | 確かめのスクリプトが、読めない証拠を合格にしないようにした
   ページ: sources/rawの段を任せるエージェントの確かめ-2026-11-14（14 回目の指摘への Sol の修正案との総括で、読めた回に違反がないことと、要る回をすべて読めたことを分けたことを書いた）

## [2026-11-15] update | browse を 5 つのブラウザで確かめ、favicon.ico の 404 を直した（wiki 0.19.3）
   ページ: concepts/browseの画面の確かめ方

## [2026-11-15] ingest | browse を 5 つのブラウザで確かめた記録と wiki 0.19.3 のリリース
   ページ: sources/browseを5つのブラウザで確かめた記録とリリース-wiki-0.19.3（新規。concepts/リリースの確かめ方 を更新）

## [2026-11-15] ingest | raw の段の確かめのスクリプトで、証拠を読み切ることと、レビューを打ち切った記録
   ページ: sources/rawの段の確かめの証拠の読み切りとレビューの打ち切り-2026-11-15（concepts/敵対的レビューで設計を直す進め方、sources/rawの段を任せるエージェントの確かめ-2026-11-14、sources/rawの段の取り直しとW8の出力のリリース-wiki-0.18.1 を更新）

## [2026-11-15] ingest | 古い uv の UV_SYSTEM_CERTS の直しと wiki 0.19.4 のリリース
   ページ: sources/古いuvのUV_SYSTEM_CERTSの直しとリリース-wiki-0.19.4（新規）

## [2026-11-15] ingest | YouTube の動画の字幕を wiki に取り込む方法の選択肢
   ページ: sources/youtubeの字幕の取り込みの選択肢-2026-11-15（新規。sources/抽出の方式の比較-markitdown-2026-11-15 にリンクを追加）

## [2026-11-15] ingest | Python の上限と依存の解決の失敗の直しと wiki 0.19.5 のリリース
   ページ: sources/Pythonの上限と依存の解決の失敗の直しとリリース-wiki-0.19.5（新規）

## [2026-11-15] ingest | ADR-0025 の承認の条件の測定と、pdfminer の本文の並びの揺れ
   ページ: sources/adr-0025の承認の条件の測定-2026-11-15、concepts/pdfminerの本文の並びの揺れ（新規）

## [2026-11-16] ingest | YouTube の字幕の取り込みの設計（ADR-0027）
   ページ: sources/youtubeの字幕の取り込みの設計-2026-11-15（新規。sources/youtubeの字幕の取り込みの選択肢-2026-11-15、concepts/敵対的レビューで設計を直す進め方 を更新）

## [2026-11-16] update | ADR-0025 の条件 1 を平均の時間で読むことにした
   ページ: sources/adr-0025の承認の条件の測定-2026-11-15

## [2026-11-16] update | ADR-0025 の直した版の時間を測った
   ページ: sources/adr-0025の承認の条件の測定-2026-11-15、concepts/pdfminerの本文の並びの揺れ

## [2026-11-16] update | ADR-0025 の判定した 10 ページを、直す前と後で比べた
   ページ: sources/adr-0025の承認の条件の測定-2026-11-15、concepts/pdfminerの本文の並びの揺れ

## [2026-11-16] update | ADR-0025 の確認の進め方の 2 つを作者が決めた
   ページ: sources/adr-0025の承認の条件の測定-2026-11-15

## [2026-11-16] ingest | ADR-0027 に自動字幕の訂正と confidence を足した
   ページ: sources/youtubeの字幕の取り込みの設計-2026-11-15、concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-16] ingest | /wiki:query の確からしさと wiki 0.20.0 のリリース
   ページ: sources/queryの確からしさとリリース-wiki-0.20.0（新規。concepts/リリースの確かめ方 を更新）

## [2026-11-16] ingest | ADR-0027 の回答の確からしさの上限の足し方を、承認された ADR-0028 に合わせた
   ページ: sources/youtubeの字幕の取り込みの設計-2026-11-15 を更新

## [2026-11-16] ingest | 2 つのスコープの wiki を引く問い合わせの設計と、写す機能の検討
   ページ: sources/2つのwikiを引く問い合わせの設計-2026-11-16、sources/2つのスコープのwikiの間で写す機能の検討-2026-11-15、concepts/2つのwikiの分離の確かめ方 を作成。concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-16] ingest | /wiki:query の確からしさの記録に ADR-0027 との分担と後始末を足した
   ページ: sources/queryの確からしさとリリース-wiki-0.20.0、concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-16] update | ADR-0025 の段階 1 の製品の関数と、揺れを確実に起こす試料
   ページ: concepts/pdfminerの本文の並びの揺れ

## [2026-11-16] ingest | ADR-0025 の段階 1 と wiki 0.21.0 のリリース
   ページ: sources/pdfの文字の層とリリース-wiki-0.21.0（新規。concepts/リリースの確かめ方 を更新）

## [2026-11-16] ingest | /wiki:query の確からしさを Sonnet 5.5 で測った記録
   ページ: sources/queryの確からしさのsonnetでの測定-2026-11-16（新規。sources/queryの確からしさとリリース-wiki-0.20.0、concepts/敵対的レビューで設計を直す進め方 を更新）

## [2026-11-16] ingest | /wiki:query の確からしさを 0.21.1 で測り直した結果
   ページ: sources/queryの確からしさのsonnetでの測定-2026-11-16、concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-16] ingest | /wiki:query の確からしさの決め方の分離と wiki 0.21.1 のリリース
   ページ: sources/queryの確からしさの決め方の分離とリリース-wiki-0.21.1（新規。concepts/リリースの確かめ方 を更新）

## [2026-11-16] ingest | /wiki:query の確からしさの未測定の規則を Sonnet 5.5 で測った記録
   ページ: sources/queryの確からしさの未測定の規則の測定-2026-11-16（新規。sources/queryの確からしさのsonnetでの測定-2026-11-16 を更新）
