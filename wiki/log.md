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

## [2026-11-16] ingest | /wiki:query の検索の説明への外の語の漏れの直しと wiki 0.21.2 のリリース
   ページ: sources/queryの検索の説明への外の語の漏れの直しとリリース-wiki-0.21.2（新規）、concepts/エージェントに守らせる決まりの書き方（新規）。sources/queryの確からしさの決め方の分離とリリース-wiki-0.21.1、concepts/リリースの確かめ方 を更新

## [2026-11-16] ingest | YouTube の字幕の取り込みの実装と wiki 0.23.0 のリリース
   ページ: sources/youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0（新規）。sources/youtubeの字幕の取り込みの設計-2026-11-15、concepts/敵対的レビューで設計を直す進め方、concepts/リリースの確かめ方 を更新

## [2026-11-16] ingest | /wiki:query の確からしさの規則の直しと wiki 0.23.1 のリリース
   ページ: sources/queryの確からしさの規則の直しとリリース-wiki-0.23.1（新規）。concepts/エージェントに守らせる決まりの書き方、sources/queryの確からしさの未測定の規則の測定-2026-11-16 を更新

## [2026-11-16] update | 2 つのスコープの wiki の間で写す機能の検討に、ユーザー → プロジェクトの伏せ字の決定を足した
   ページ: sources/2つのスコープのwikiの間で写す機能の検討-2026-11-15 を更新

## [2026-11-16] update | ADR-0029（wiki と raw の記事にリンクを置かない）の承認を記録した
   ページ: sources/2つのwikiを引く問い合わせの設計-2026-11-16 を更新

## [2026-11-16] ingest | YouTube の取り込みを使い捨ての wiki で試した結果と wiki 0.23.2 のリリース
   ページ: sources/youtubeの取り込みの試しと直しとリリース-wiki-0.23.2（新規）。sources/youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0、concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-16] update | /wiki:query の回答の「確からしさ」を「確信度」に名前を変えた
   ページ: 確からしさを扱う 11 ページ（index を含む）の地の文と title を「確信度」にした。ページ名（スラッグ）、リンク、当時の版の決まった 1 行などの字句、この log の過去の行は変えていない

## [2026-11-16] ingest | /wiki:query の回答の「確からしさ」を「確信度」に変えた wiki 0.24.0 のリリース
   ページ: sources/queryの回答の確信度への名前の変更とリリース-wiki-0.24.0（新規）。concepts/リリースの確かめ方 を更新

## [2026-11-16] ingest | browse の木をタグでまとめ、左のペインを Tree にした wiki 0.25.0 のリリース
   ページ: sources/browseのタグの段とTreeのリリース-wiki-0.25.0（新規）。concepts/browseのデザインシステム、concepts/browseの画面の確かめ方、index を更新

## [2026-11-16] ingest | browse の同梱の fluent2.css をスキルの 0.1.5 に写し直した wiki 0.25.1 のリリース
   ページ: sources/browseの同梱のfluent2のcssの更新-wiki-0.25.1（新規）。index を更新

## [2026-11-16] ingest | The components of agent memory（Anthropic）
   ページ: sources/components-of-agent-memory、concepts/エージェントのメモリの階層（新規）。concepts/editとwriteの書き込みの競合、concepts/エージェントに守らせる決まりの書き方、index を更新
   raw: `wiki:web-raw` に任せた（報告したモデル: Claude Sonnet 5.5）。訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5
   グラフ: ノード +2、型付きエッジ +0

## [2026-11-16] ingest | Dreaming with a dynamic workflow（Claude の cookbook）
   ページ: sources/managed-agents-cma-dreaming-with-a-dynamic-workflow（新規）。concepts/editとwriteの書き込みの競合、concepts/エージェントのメモリの階層、sources/components-of-agent-memory、index を更新
   raw: `wiki:web-raw` に任せた（報告したモデル: Claude Sonnet 5.5）。訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-16] ingest | Knowledge wiki with a dynamic workflow（claude-quickstarts）
   ページ: sources/claude-quickstarts-managed-agents-knowledge-wiki（新規）。concepts/editとwriteの書き込みの競合、concepts/エージェントのメモリの階層、sources/managed-agents-cma-dreaming-with-a-dynamic-workflow、index を更新
   raw: `wiki:web-raw` に任せた（報告したモデル: Claude Sonnet 5.5）。訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5。README だけで、ファイルの一覧の表は 1 段落につぶれて英語のまま残った
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-17] ingest | browse の種類とグループの絞り込みの直しと wiki 0.25.2 のリリース
   ページ: sources/browseの種類とグループの絞り込みの直しとリリース-wiki-0.25.2（新規）。index を更新

## [2026-11-17] update | 2 つの wiki を引く問い合わせの設計の 18 版目（ADR-0029 に合わせ、4 体の見直しで読み手に確かめを移し、レビューを止めた）
   ページ: sources/2つのwikiを引く問い合わせの設計-2026-11-16、concepts/2つのwikiの分離の確かめ方、concepts/敵対的レビューで設計を直す進め方 を更新

## [2026-11-17] ingest | browse の svg と Mermaid の図と wiki 0.26.0、0.27.0 のリリース
   ページ: sources/browseの図の描画とリリース-wiki-0.26.0-0.27.0（新規）、concepts/敵対的レビューで設計を直す進め方、concepts/browseの画面の確かめ方、concepts/リリースの確かめ方 を更新。index を更新

## [2026-11-17] update | リリースの確かめ方のページを分け、版ごとの導入の確かめの記録を別のページにした
   ページ: concepts/リリースごとの導入の確かめの記録（新規）、concepts/リリースの確かめ方 を更新（101 行から 95 行）。index を更新

## [2026-11-17] ingest | Codex のプラグインと会話の取り込みに対応した wiki 0.29.0 のリリース
   ページ: sources/codexのプラグインと会話の取り込みのリリース-wiki-0.29.0（新規）、concepts/リリースの確かめ方、concepts/リリースごとの導入の確かめの記録 を更新。index とグラフを更新

## [2026-11-17] ingest | Codex 対応と会話の取り込み、wiki 0.29.0 の公開と導入
   ページ: sources/codex対応と会話の取り込み-wiki-0.29.0（新規）。concepts/リリースの確かめ方の出典と参照リンク、index を更新
   セッション: ターン 349、手で伏せた区間 0、消したターン 0。過去の Codex の応答モデルは API で確認できないため不明とした
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-18] ingest | Playwright の取り込みとログイン状態の利用、wiki 0.30.0 の公開
   ページ: sources/playwrightの取り込みとログイン状態の利用-wiki-0.30.0（新規）、concepts/リリースごとの導入の確かめの記録 を更新。index とグラフを更新
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-18] ingest | wiki の記事のリンクの拒否と wiki 0.31.0 のリリース
   ページ: sources/wikiの記事リンクの拒否とリリース-wiki-0.31.0（新規）、concepts/リリースの確かめ方、concepts/リリースごとの導入の確かめの記録、index を更新
   グラフ: ノード +1、型付きエッジ +0

## [2026-11-18] ingest | 翻訳を省略した取り込みの完了の防止（wiki 0.31.1）
   ソースの要約と、エージェントに守らせる決まりの書き方を更新した。原本は開発の検証の記録。
   グラフ: ノード +1、型付きエッジ +0（通常の参照を含むエッジ +5）。lint の新しい指摘はなし。

## [2026-11-18] ingest | wiki 0.31.1 の公開とマーケットプレイス導入の確かめ
   翻訳修正のソースと版ごとの導入の記録に追記。Claude Code / Codex とも全 11 変更ファイルがタグと一致し、導入先の必須翻訳の検査が働くことを確認。index とグラフを更新。
   グラフ: ノード +0、型付きエッジ +0、通常の参照 +4。lint の新規指摘なし。

## [2026-11-18] ingest | 保存済みのグラフ検索記事の日本語版を登録
   ページ: sources/build-an-agentic-knowledge-graph-from-scratch-ja、concepts/既存リンクからのグラフ検索。エージェントに守らせる決まりの書き方、index とグラフを更新。
   raw: 保存済みの英語版と日本語版、画像 6 点を登録。日本語訳と図の補足は GPT-6。原本のバイト列を変更せず、再取得はしていない。
   留保: 当初 keep で翻訳を省略して完了扱いにした記録は誤りだった。後の比較用ファイルを手作業で作った旧検査の結果も、正規の W8 の受領記録とは扱わない。公開した 0.31.1 の検査による一時 fixture の検証は、翻訳修正の記録を参照。
   検証範囲: 著者による部品の検証と設計提案であり、実 Wikipedia による全工程と回答検査器の実証は含まない。

## [2026-11-18] ingest | 概要の生成とbrowse表示をwiki 0.32.0で公開。両ホストの25変更ファイルとタグの一致、保存・表示を確認。sources/ページの概要の生成と表示-wiki-0.32.0、導入の確認記録、索引とグラフを更新。

## [2026-11-18] ingest | プロンプトの候補とモデル選定をwiki 0.33.0で公開。両ホストの17変更ファイル、スキル単体170ファイルとタグの一致、フックとMCPの語彙検索を確認。sources/プロンプトの候補とモデル選定-wiki-0.33.0、導入の確認記録、索引とグラフを更新。

## [2026-11-18] ingest | rawのリンク検証をwiki 0.34.0で公開。Opus6回、公開前CI21構成、3経路の配布とタグの一致を確認。sources/rawのリンクの検証とリリース-wiki-0.34.0、リリースの確かめ方と導入記録、索引とグラフを更新。

## [2026-11-18] update | wiki 0.34.1 の公開と導入の確認

- wiki プラグインの main の `98cf743` に注釈付きタグ `v0.34.1` を付けて push し、2026-11-18 21:38:53（日本時間）に公開した。本文は CHANGELOG の該当節と一致した。[GitHub リリース](https://github.com/to884/info-hive-wiki/releases/tag/v0.34.1)
- 公開マーケットプレイス `to884/info-hive-marketplace` から、Claude Code 2.1.325 と Codex CLI 0.166.0 に `wiki@info-hive` の 0.34.1 をそれぞれ導入した。両方で v0.34.0 から変わった 14 ファイルの SHA-256 がタグと一致し、導入されたひな形の新見出しと字幕検査の新旧見出しへの対応を確認した。検証用の一時設定を削除した。

## [2026-11-18] update | wiki 0.34.1 で東大の模擬講義の YouTube 字幕取り込みを再検証。実取得から要約・関連ページの保存、検査までの結果を [[youtubeの取り込みの試しと直しとリリース-wiki-0.23.2]] に追記し、索引を更新。

## [2026-11-18] prepare | Web raw の警告の確認: Effort
   - 24 行目 推論と effort と訳したリンクに、参照先の英語の節名を併記した。
   - 26 行目 Set the effort level を effort の指定方法と訳した見出し。
   - 226 行目 Thinking (when active) を推論（有効な場合）と訳した。
   - 230 行目 Effort levels を effort の段階と訳した見出し。
   - 232 行目 表の列名 Level を段階と訳した。
   - 232 行目 表の列名 Description を説明と訳した。
   - 232 行目 表の列名 Typical use case を主な用途と訳した。
   - 234 行目 max の対応モデル 16 種の製品名を保持した。
   - 235 行目 xhigh の対応モデル 13 種の製品名を保持した。
   - 282 行目 応答前の推論を省く方法と訳したリンクに、参照先の英語の節名を併記した。
   - 314 行目 推奨設定の対象モデル Claude Opus 5 の製品名を保持した。
   - 330 行目 推奨設定の対象モデル Claude Opus 4.8 の製品名を保持した。
   - 340 行目 推奨設定の対象モデル Claude Opus 4.7 の製品名を保持した。
   - 358 行目 推奨設定の対象モデル Claude Sonnet 5 の製品名を保持した。
   - 370 行目 推奨設定の対象モデル Claude Sonnet 4.6 の製品名を保持した。
   - 397 行目 Effort with thinking を effort と推論と訳した見出し。
   - 401 行目 推論と effort と訳したリンクに、参照先の英語の節名を併記した。
   - 425 行目 推論とプロンプトキャッシュと訳したリンクに、参照先の英語の節名を併記した。
   - 427 行目 Next steps を、続けて読める資料を示す関連資料と訳した。
   - 433 行目 関連資料のリンク Steering thinking を推論の調整と訳した。
   - 437 行目 関連資料のリンク Thinking を推論と訳した。
   - 441 行目 Availability を提供状況と訳した節の見出し。
   - 447 行目 製品名 Messages API を保持し、利用方法へのリンクと分かる語を添えた。
   - 452 行目 Messages API の表の列名 Status を提供状況と訳した。
   - 454 行目 Messages API の表の Available を利用可能と訳した。
   - 454 行目 Messages API に対応するモデル 17 種の製品名とリンクを保持した。
   - 456 行目 製品名 Managed Agents を保持し、概要へのリンクと分かる語を添えた。
   - 461 行目 Managed Agents の表の列名 Status を提供状況と訳した。
   - 463 行目 Managed Agents の表の Available を利用可能と訳した。
   - 463 行目 Managed Agents を使える 2 つのプラットフォームの製品名を保持した。
   - 463 行目 Managed Agents に対応するモデル 17 種の製品名とリンクを保持した。
   - 469 行目 データの表の列名 Item を項目と訳した。
   - 471 行目 データの表の行見出し Status を状態と訳した。
   - 471 行目 HIPAA 欄の Eligible を対象と訳した。

## [2026-11-18] ingest | Effort（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。通常の HTML 取得では最初のモデルタブだけが抽出されたため、公式 Markdown 版を HTML に変換して取得器に渡し、モデル別の説明と 9 件のコード例を収録した。raw の `source_sha256` は変換後の HTML の値。公式 Markdown の SHA-256 は `ed97da9bd61afde31998c4f3e5885c620c6992b8e39fd10d01f1d81baf7efd9b`。画像の補足は 0 件。
   検査: W8 は `completed: true`、翻訳は `checked`（173 ブロック、要確認箇所 34 件は直前の prepare に記録、未解決 0 件）。追加・更新した記事は構造とグラフの lint で新規指摘なし。
   ページ: [[claude-api-effort]] と [[claude-effort]] を追加し、[[ingestに使うモデル]] に公式の評価指針への参照を追加。索引を更新し、タグ「モデル設定」をスキーマに追加。
   グラフ: 今回の追加はノード 2、型付きエッジ 0。再抽出後は合計 104 ノード、552 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Per-message effort
   - 310 行目 Bedrock の会話途中のシステムメッセージと訳したリンクに、参照先の節名を併記した。
   - 322 行目 Availability を提供状況と訳した節の見出し。
   - 328 行目 製品名 Messages API を保持し、利用方法へのリンクを示す語を添えた。
   - 332 行目 対応表の列名 Status を提供状況と訳した。
   - 334 行目 対応表の 1 行目のプラットフォーム名を保持し、Google Cloud の運用主体を訳した。
   - 334 行目 対応表の 1 行目のモデル名 Claude Fable 5.1 と Claude Opus 5.5 を保持した。
   - 335 行目 プラットフォーム名 Amazon Bedrock と識別子 bedrock-runtime を保持した。
   - 335 行目 対応表の 2 行目のベータ対応モデル 4 種の製品名を保持した。
   - 336 行目 対応表の 3 行目の 5 プラットフォームの名前を保持し、Google Cloud の運用主体を訳した。
   - 336 行目 対応表の 3 行目のベータ対応モデル 4 種の製品名を保持した。
   - 337 行目 対応表の 4 行目で Claude API、Amazon Bedrock、Google が運用する Claude Models on Google Cloud の製品名を保持した。
   - 337 行目 対応表の 4 行目で Microsoft Foundry とホスト主体 Anthropic の名前を保持した。
   - 337 行目 対応表の 4 行目のモデル名 Claude Mythos 5.1 を保持した。
   - 338 行目 対応表の 5 行目で Claude API、Anthropic が運用する Claude Models on Google Cloud の製品名を保持した。
   - 338 行目 対応表の 5 行目で Google が運用する Claude Models on Google Cloud の製品名を保持した。
   - 338 行目 対応表の 5 行目で Microsoft Foundry とホスト主体 Anthropic の名前を保持した。
   - 338 行目 対応表の 5 行目のモデル名 Claude Mythos 5.2 を保持した。
   - 342 行目 製品名 Managed Agents を保持し、概要へのリンクを示す語を添えた。

## [2026-11-18] ingest | Per-message effort（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コード例 9 件とクラウド別の対応表を収録。`source_sha256` は変換後の HTML の値。公式 Markdown の SHA-256 は `93b4ac69511466561cfae337b556922bc3d51d329f0d0c6d4a309a25cfc19195`。画像の補足は 0 件。
   検査: W8 は `completed: true`、翻訳は `checked`（53 ブロック、確認した 18 件は直前の prepare に記録、未解決 0 件）。コード例 9 件は公式 Markdown と一致。構造とグラフの lint に新規指摘なし。
   ページ: [[claude-api-effort-per-message]] を追加し、[[claude-effort]] と [[claude-api-effort]] から参照。索引を更新。
   グラフ: ノード +1、型付きエッジ +0。再抽出後は合計 105 ノード、558 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Thinking
   - 13 行目 見出し Thinking を推論と訳し、公式の題名を併記した。
   - 28 行目 節名 How thinking works を「推論の仕組み」と訳した。
   - 64 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 5.5 を保持した。
   - 65 行目 モデル別の設定表の行見出しでモデル名 Claude Sonnet 5.5 を保持した。
   - 66 行目 モデル別の設定表の行見出しでモデル名 Claude Haiku 5.5 を保持した。
   - 67 行目 モデル別の設定表の行見出しでモデル名 Claude Fable 5.2 を保持した。
   - 68 行目 モデル別の設定表の行見出しでモデル名 Claude Mythos 5.2 を保持した。
   - 69 行目 モデル別の設定表の行見出しでモデル名 Claude Fable 5.1 を保持した。
   - 70 行目 モデル別の設定表の行見出しでモデル名 Claude Mythos 5.1 を保持した。
   - 71 行目 モデル別の設定表の行見出しでモデル名 Claude Fable 5 を保持した。
   - 72 行目 モデル別の設定表の行見出しでモデル名 Claude Mythos 5 を保持した。
   - 73 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 5 を保持した。
   - 74 行目 モデル別の設定表の行見出しでモデル名 Claude Sonnet 5 を保持した。
   - 75 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 4.8 を保持した。
   - 76 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 4.7 を保持した。
   - 77 行目 モデル別の設定表の行見出しでモデル名 Claude Mythos Preview を保持した。
   - 77 行目 Claude Mythos Preview の設定表で Extended thinking を「拡張推論を使う」と訳した。
   - 78 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 4.6 を保持した。
   - 79 行目 モデル別の設定表の行見出しでモデル名 Claude Sonnet 4.6 を保持した。
   - 80 行目 モデル別の設定表の行見出しでモデル名 Claude Opus 4.5 を保持した。
   - 80 行目 Claude Opus 4.5 の設定表で Extended thinking を「拡張推論を使う」と訳した。
   - 81 行目 モデル別の設定表の行見出しでモデル名 Claude Sonnet 4.5 を保持した。
   - 81 行目 Claude Sonnet 4.5 の設定表で Extended thinking を「拡張推論を使う」と訳した。
   - 82 行目 モデル別の設定表の行見出しでモデル名 Claude Haiku 4.5 を保持した。
   - 82 行目 Claude Haiku 4.5 の設定表で Extended thinking を「拡張推論を使う」と訳した。
   - 88 行目 適応型推論を明示する必要がある 4 モデルの名前を保持した。
   - 474 行目 推論を無効にできない 8 モデルの名前を保持した。
   - 486 行目 表示設定 summarized の既定値を説明する段落で、Claude Opus 4.6 と Claude Sonnet 4.6 の名前を保持した。
   - 487 行目 表示設定 omitted が既定の 14 モデルの名前を保持した。
   - 520 行目 節名 Summarized thinking を「推論の要約」と訳した。
   - 527 行目 推論出力の書き出しの詳しさを説明する段落で、Claude Opus 4.6 と Claude Sonnet 4.6 の名前を保持した。
   - 533 行目 内部推論を回答テキストに求めると拒否を返す場合がある 6 モデルの名前を保持した。
   - 891 行目 節名 Thinking and effort を「推論と effort」と訳した。
   - 908 行目 適応型推論で強制ツール利用が例外となる 6 モデルの名前を保持した。
   - 946 行目 ツール利用中の推論ブロックの返送を示す Required を「必須」と訳した。
   - 947 行目 ターン間の推論ブロックの返送を示す Recommended を「推奨」と訳した。
   - 968 行目 ツール呼び出し間の推論がブロックに現れる 12 モデルの名前を保持した。
   - 976 行目 ツール呼び出し間の進捗報告に対応する 7 モデルの名前を保持した。
   - 988 行目 ベータヘッダーの指定方法を案内する段落で、Amazon Bedrock と Claude Models on Google Cloud の名前を保持し、運用主体を訳した。
   - 1056 行目 全ターンの推論を保持するモデルの一覧で、Sonnet 系列の名前と Claude Haiku 5.5 以降に列記したモデルの名前を保持した。
   - 1068 行目 相互に推論を読めるモデル Claude Mythos 5.2 と対応プラットフォーム Claude API の名前を保持した。
   - 1068 行目 Fable 5.2 と Mythos 5.2 の相互読み取りに対応する Google Cloud の製品名と運用主体を保持した。
   - 1068 行目 Fable 5.2 と Mythos 5.2 が読める推論を生成する例として挙がる 3 モデルの名前を保持した。
   - 1069 行目 Fable 5.2 と Mythos 5.2 が前世代の推論を読める Google Cloud の製品名と運用主体を保持した。
   - 1070 行目 対応を説明する Claude Opus 5.5 と、推論を読める切り替え元の Claude Opus 5 の名前を保持した。
   - 1070 行目 Opus 5.5 が推論を読める旧世代の Claude Opus、Claude Sonnet、Claude Haiku の系列名を保持した。
   - 1070 行目 Opus 5.5 が Sonnet 5.5 と Haiku 5.5 の推論を読める Google Cloud の製品名と運用主体を保持した。
   - 1070 行目 Fable 5.2 と Mythos 5.2 が Opus 5.5 の推論を読める Google Cloud の製品名と運用主体を保持した。
   - 1071 行目 対応を説明する Claude Sonnet 5.5 と、推論を読める切り替え元の 3 モデルの名前を保持した。
   - 1071 行目 Sonnet 5.5 が推論を読める旧世代の Claude Opus、Claude Sonnet、Claude Haiku の系列名を保持した。
   - 1071 行目 Sonnet 5.5 が Haiku 5.5 の推論を読める Google Cloud の製品名と運用主体を保持した。
   - 1071 行目 Sonnet 5.5 が推論を読めない Claude Opus 5、Claude Opus 5.5、Claude Fable などの名前を保持した。
   - 1071 行目 Sonnet 5.5 の推論を読める切り替え先の 3 モデルの名前を保持した。
   - 1072 行目 対応を説明する Claude Haiku 5.5 と、推論を読める切り替え元の 3 モデルの名前を保持した。
   - 1072 行目 Haiku 5.5 が推論を読める旧世代の Claude Opus、Claude Sonnet、Claude Haiku の系列名を保持した。
   - 1072 行目 Haiku 5.5 が推論を読めない Claude Opus 5、Claude Opus 5.5、Claude Sonnet 5.5、Claude Fable などの名前を保持した。
   - 1072 行目 Haiku 5.5 の推論の読み取りに対応する Google Cloud の製品名と運用主体を保持した。
   - 1072 行目 Haiku 5.5 の推論を読める切り替え先の 4 モデルの名前を保持した。
   - 1082 行目 推論ブロックの先頭部分の照合に対応する 7 モデルの名前を保持した。
   - 1084 行目 トラブルシューティングで照合できるよう、別の会話にひも付いたブロックを示す英語のエラー本文を保持した。
   - 1092 行目 トップレベルの effort 変更がキャッシュに及ぼす影響を説明する段落で、例示する 4 モデルの名前を保持した。
   - 1154 行目 節名 Thinking encryption を「推論の暗号化」と訳した。
   - 1165 行目 署名に互換性のある Claude API、Amazon Bedrock、Claude Models on Google Cloud の製品名を保持した。
   - 1165 行目 推論ブロックの使用にアカウントの条件がある 4 モデルの名前を保持した。
   - 1184 行目 節名 Limits and feature compatibility を「制限と機能の互換性」と訳した。
   - 1188 行目 サンプリングパラメーターの制約が適用される 14 モデルの名前を保持した。
   - 1190 行目 節名 Response prefill and forced tool use を「応答の事前入力とツール利用の強制」と訳した。
   - 1192 行目 強制ツール利用を拒否する例外の 6 モデルの名前を保持した。
   - 1194 行目 節名 Output limits を「出力の上限」と訳した。
   - 1200 行目 出力上限の表の行見出しでモデル名 Claude Fable 5.2 を保持した。
   - 1201 行目 出力上限の表の行見出しでモデル名 Claude Mythos 5.2 を保持した。
   - 1202 行目 出力上限の表の行見出しでモデル名 Claude Fable 5.1 を保持した。
   - 1203 行目 出力上限の表の行見出しでモデル名 Claude Mythos 5.1 を保持した。
   - 1204 行目 出力上限の表の行見出しでモデル名 Claude Fable 5 を保持した。
   - 1205 行目 出力上限の表の行見出しでモデル名 Claude Mythos 5 を保持した。
   - 1206 行目 出力上限の表の行見出しでモデル名 Claude Mythos Preview を保持した。
   - 1207 行目 出力上限の表の行見出しでモデル名 Claude Opus 5.5 を保持した。
   - 1208 行目 出力上限の表の行見出しでモデル名 Claude Opus 5 を保持した。
   - 1209 行目 出力上限の表の行見出しでモデル名 Claude Opus 4.8 を保持した。
   - 1210 行目 出力上限の表の行見出しでモデル名 Claude Opus 4.7 を保持した。
   - 1211 行目 出力上限の表の行見出しでモデル名 Claude Opus 4.6 を保持した。
   - 1212 行目 出力上限の表の行見出しでモデル名 Claude Opus 4.5 を保持した。
   - 1213 行目 出力上限の表の行見出しでモデル名 Claude Sonnet 5.5 を保持した。
   - 1214 行目 出力上限の表の行見出しでモデル名 Claude Sonnet 5 を保持した。
   - 1215 行目 出力上限の表の行見出しでモデル名 Claude Sonnet 4.6 を保持した。
   - 1216 行目 出力上限の表の行見出しでモデル名 Claude Sonnet 4.5 を保持した。
   - 1217 行目 出力上限の表の行見出しでモデル名 Claude Haiku 5.5 を保持した。
   - 1218 行目 出力上限の表の行見出しでモデル名 Claude Haiku 4.5 を保持した。
   - 1226 行目 節名 Next steps を「関連資料」と訳した。
   - 1228 行目 関連資料のリンク Steering thinking を「推論の調整」と訳した。
   - 1248 行目 節名 Availability を「提供状況」と訳した。
   - 1254 行目 Messages API の製品名を保持し、利用情報へのリンクと分かる語を添えた。
   - 1259 行目 Messages API の表の列名 Status を「提供状況」と訳した。
   - 1263 行目 Managed Agents の製品名を保持し、製品概要へのリンクと分かる語を添えた。
   - 1268 行目 Managed Agents の表の列名 Status を「提供状況」と訳した。
   - 1276 行目 データの取り扱い表の列名 Item を「項目」と訳した。
   - 1278 行目 データの取り扱い表の行見出し Status を「状態」と訳した。
   - 1278 行目 HIPAA 欄の Eligible を「対象」と訳した。
   - 36 行目 Thinking encryption は節名「推論の暗号化」として訳した。
   - 54 行目 Controlling thinking display は節名「推論の表示を設定する」として訳した。
   - 56 行目 Thinking with tool use は節名「ツール利用時の推論」として訳した。
   - 60 行目 Troubleshooting thinking は文書名「推論のトラブルシューティング」として訳した。
   - 333 行目 Cost control と Thinking and the context window はそれぞれ「費用の調整」と「推論とコンテキストウィンドウ」として訳した。
   - 468 行目 Running with thinking disabled は節名「推論を無効にして実行する」として訳した。
   - 470 行目 Running without up-front thinking は節名「回答前の推論を省いて実行する」として訳した。
   - 472 行目 Use で始まる 2 つの節名を「effort で推論を調整する」と「JSON 出力と独自ツールで適応型推論を使う」として訳した。
   - 478 行目 Extended thinking と Troubleshooting thinking は文書名「拡張推論」と「推論のトラブルシューティング」として訳した。
   - 487 行目 Thinking encryption は節名「推論の暗号化」として訳した。
   - 513 行目 Preserving thinking blocks は節名「推論ブロックを保持する」として訳した。
   - 514 行目 Progress updates は節名「進捗報告」として訳した。
   - 516 行目 Streaming thinking は節名「推論のストリーミング」として訳した。
   - 533 行目 What a refusal looks like と Keep reasoning in thinking blocks は節名「拒否時の応答」と「推論を推論ブロックに収める」として訳した。
   - 889 行目 Streaming messages は文書名「メッセージのストリーミング」として訳した。
   - 895 行目 Steering thinking と Budget rules and tuning は「推論の調整」と「予算の規則と調整」として訳した。
   - 900 行目 Steering how often Claude thinks は節名「推論の頻度を調整する」として訳した。
   - 908 行目 Response prefill and forced tool use は節名「応答の事前入力とツール利用の強制」として訳した。
   - 909 行目 Preserving thinking blocks は節名「推論ブロックを保持する」として訳した。
   - 935 行目 Thinking and prompt caching は節名「推論とプロンプトキャッシュ」として訳した。
   - 950 行目 Thinking block preservation by model は節名「モデル別の推論ブロックの保持」として訳した。
   - 956 行目 Walk through a two-turn tool-use round trip は節名「ツール利用を 2 ターンで往復する例」として訳した。
   - 972 行目 How interleaved thinking changes the flow は節名「呼び出し間の推論による流れの変化」として訳した。
   - 988 行目 Beta features on other platforms は節名「他のプラットフォームでのベータ機能」として訳した。
   - 1049 行目 Streaming thinking は節名「推論のストリーミング」として訳した。
   - 1050 行目 Ask と User で始まる節名、Prompting で始まるガイド名、Keep で始まる節名を訳し、Claude Opus 5.5、Claude Sonnet 5.5 と Claude Fable 5.2 の製品名を保持した。
   - 1064 行目 Thinking and the context window と Preserving thinking blocks は節名「推論とコンテキストウィンドウ」と「推論ブロックを保持する」として訳した。
   - 1066 行目 Switch models and back は節名「モデルを切り替えて元に戻す」として訳した。
   - 1080 行目 Switch models and back と Accounts and cloud platforms は節名「モデルを切り替えて元に戻す」と「アカウントとクラウドプラットフォーム」として訳した。
   - 1084 行目 Prefix checks on thinking blocks と Fix a thinking block bound to a different conversation は文書と節のタイトルを訳し、本文のエラー文言は英語のまま残した。
   - 1128 行目 Stop reasons and fallback は文書名「停止理由とフォールバック」として訳した。
   - 1160 行目 Thinking block preservation by model は節名「モデル別の推論ブロックの保持」として訳した。
   - 1165 行目 Accounts and cloud platforms は節名「アカウントとクラウドプラットフォーム」として訳した。
   - 1180 行目 Preserving thinking blocks は節名「推論ブロックを保持する」として訳した。
   - 1188 行目 Remove sampling parameters は節名「サンプリングパラメーターを取り除く」として訳した。
   - 1192 行目 Prefill not supported と Thinking with tool use は節名「事前入力の対応状況」と「ツール利用時の推論」として訳した。
   - 1220 行目 Using the Models API は文書名「Models API の利用」として訳した。
   - 1224 行目 API は「検証はクライアント側で行われます」で API 側との違いが伝わる。Get the final message without handling events は節名「イベントを処理せずに最終メッセージを取得する」として訳した。

## [2026-11-18] ingest | Thinking（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、図 4 枚とコード・イベント例 40 ブロックを収録。図の補足は GPT-6。raw の `source_sha256` は変換後の HTML の値。公式 Markdown の SHA-256 は `7017002bb0a8d33fdf63c676f1117db41c854587ca80ef13697482cde7c4879b`。
   検査: W8 は `completed: true`、翻訳は `checked`（406 ブロック、確認 98 件、未解決 0 件）。訳した節名の警告 38 件を含め、理由は直前の prepare に記録。コード・イベント例 40 ブロックは公式 Markdown と一致。構造とグラフの lint に新規指摘なし。
   ページ: [[claude-api-thinking]] と [[claude-thinking]] を追加。[[claude-effort]]、[[claude-api-effort]]、[[claude-api-effort-per-message]] から参照し、索引を更新。
   グラフ: ノード +2、型付きエッジ +0。再抽出後は合計 107 ノード、574 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Steering thinking
   - 13 行目 題名 Steering thinking を「推論の調整」と訳した。
   - 17 行目 zero data retention を「データ保持なし」と訳し、原語と略称 ZDR を併記した。
   - 52 行目 節名 Effort levels を「effort の段階」と訳した。
   - 56 行目 表の列名 Effort level を「effort の段階」と訳した。
   - 56 行目 表の列名 Thinking behavior を「推論の挙動」と訳した。
   - 113 行目 キャッシュやターンの扱いを解説する節名 Mechanics を「仕組み」と訳した。
   - 866 行目 課金対象を説明する節名 Pricing を「料金の仕組み」と訳した。
   - 880 行目 入力トークン欄の Same as summarized を「要約時と同じ」と訳した。
   - 881 行目 課金対象の出力トークン欄の Same as summarized を「要約時と同じ」と訳した。
   - 883 行目 表の行見出し Summary generation を「要約の生成」と訳した。
   - 903 行目 続けて読む資料を示す節名 Next steps を「関連資料」と訳した。
   - 905 行目 関連資料のリンク Thinking を「推論の概要」と訳した。
   - 23 行目 ガイド名 Thinking をリンク内で「推論の概要」と訳した。
   - 31 行目 節名 Effort levels を「effort の段階」と訳した。
   - 37 行目 節名 Thinking and effort を「推論と effort」と訳した。
   - 48 行目 Prompting で始まるガイド名を各モデルの「プロンプトの書き方」と訳し、3 モデルの製品名は保持した。
   - 68 行目 節名 Set the effort level を「effort の指定方法」と訳した。
   - 119 行目 節名 Turn structure in manual mode を「手動モードでのターンの構造」と訳した。
   - 127 行目 ガイド名 Thinking をリンク内で「推論の概要」と訳した。
   - 131 行目 節名 Thinking and prompt caching を「推論とプロンプトキャッシュ」と訳した。
   - 141 行目 cURL の案内で Prompt caching を「プロンプトキャッシュ」と訳した。
   - 145 行目 CLI の案内で Prompt caching を「プロンプトキャッシュ」と訳した。
   - 901 行目 料金ページへのリンク Pricing を「料金表」と訳した。

## [2026-11-18] ingest | Steering thinking（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コードと出力例 12 ブロックを収録。公式 Markdown の SHA-256 は `30d7f7587ecd92b22578d9a200680868e49a76e48fdacb1373544b4f5aab7a0a`。raw の `source_sha256` は変換後の HTML の値。図は 0 枚。
   検査: W8 は `completed: true`、翻訳は `checked`（104 ブロック、確認 12 件、未解決 0 件）。訳した節名の警告 11 件を含め、理由は直前の prepare に記録。コードと出力例は公式 Markdown と照合し、取得器が TypeScript 例の冒頭の空行 1 行を省いたことを確認した。構造とグラフの lint に新規指摘なし。
   ページ: [[claude-thinking-steering-and-cost]] を追加し、[[claude-thinking]]、[[claude-effort]]、[[claude-api-thinking]]、[[claude-api-effort]] に相互参照を追加。索引を更新。
   グラフ: ノード +1、型付きエッジ +0。再抽出後は合計 108 ノード、586 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Thinking in tool and multi-turn workflows
   - 17 行目 zero data retention を「データ保持なし」と訳し、原語と略称 ZDR を併記した。
   - 27 行目 適応型推論でツール利用を強制すると 400 になる 6 モデルの製品名を保持した。
   - 33 行目 手動の拡張推論に置き換える対象として挙げた Claude Opus 4.5、Claude Sonnet 4.5、Claude Haiku 4.5 の名前を保持した。
   - 755 行目 手順の見出し Read the final response を「最終応答を読む」と訳した。
   - 818 行目 続けて読む資料を示す節名 Next steps を「関連資料」と訳した。
   - 820 行目 関連資料のリンク Thinking を「推論の概要」と訳した。
   - 824 行目 関連資料のリンク Steering thinking を「推論の調整」と訳した。
   - 828 行目 関連資料のリンク Extended thinking を「拡張推論」と訳した。
   - 19 行目 節名 Preserving thinking blocks を「推論ブロックを保持する」と訳した。
   - 294 行目 節名 Controlling thinking display を「推論の表示を設定する」と訳した。
   - 772 行目 節名 Interleaved thinking を「ツール呼び出しの間に行う推論」と訳した。

## [2026-11-18] ingest | Thinking in tool and multi-turn workflows（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コード・応答例・処理の比較を 20 ブロック収録。公式 Markdown の SHA-256 は `6d4c9649eb15c34cdde2f011cb9169370a99c9a00fd55032251c3bfced4ad69e`。raw の `source_sha256` は変換後の HTML の値。図は 0 枚。
   検査: W8 は `completed: true`、翻訳は `checked`（43 ブロック、確認 8 件、未解決 0 件）。訳した節名の警告 3 件を含め、理由は直前の prepare に記録。コードと出力例を公式 Markdown と照合し、取得器が Python 例 2 件の冒頭から空行を各 1 行省いたことを確認した。構造とグラフの lint に新規指摘なし。
   ページ: [[claude-thinking-tool-workflows]] を追加し、[[claude-thinking]]、[[claude-api-thinking]]、[[claude-thinking-steering-and-cost]] に相互参照を追加。索引を更新。
   グラフ: ノード +1、型付きエッジ +0。再抽出後は合計 109 ノード、594 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Troubleshooting thinking
   - 17 行目 zero data retention を「データ保持なし」と訳し、原語と略称 ZDR を併記した。
   - 29 行目 モデル別の表の列名 Thinking types を「推論の種類」と訳した。
   - 29 行目 モデル別の表の列名 Default を「既定の挙動」と訳した。
   - 31 行目 モデル別の設定表で、行見出しの製品名 Claude Fable 5.2 を保持した。
   - 31 行目 Claude Fable 5.2 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 32 行目 モデル別の設定表で、行見出しの製品名 Claude Mythos 5.2 を保持した。
   - 32 行目 Claude Mythos 5.2 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 33 行目 モデル別の設定表で、行見出しの製品名 Claude Fable 5.1 を保持した。
   - 33 行目 Claude Fable 5.1 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 34 行目 モデル別の設定表で、行見出しの製品名 Claude Mythos 5.1 を保持した。
   - 34 行目 Claude Mythos 5.1 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 35 行目 モデル別の設定表で、行見出しの製品名 Claude Fable 5 を保持した。
   - 35 行目 Claude Fable 5 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 36 行目 モデル別の設定表で、行見出しの製品名 Claude Mythos 5 を保持した。
   - 36 行目 Claude Mythos 5 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 37 行目 モデル別の設定表で、行見出しの製品名 Claude Mythos Preview を保持した。
   - 37 行目 Claude Mythos Preview の行で、Adaptive, extended を「適応型と拡張推論」と訳した。
   - 37 行目 Claude Mythos Preview の行で、既定値欄の Always on を「常に有効」と訳した。
   - 38 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 5.5 を保持した。
   - 38 行目 Claude Opus 5.5 の行で、既定値欄の Always on を「常に有効」と訳した。
   - 39 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 5 を保持した。
   - 39 行目 Claude Opus 5 の行で、既定値欄の On を「既定で有効」と訳した。
   - 39 行目 Claude Opus 5 の行で、disabled の条件を説明する注 2 への参照を保持した。
   - 40 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 4.8 を保持した。
   - 40 行目 Claude Opus 4.8 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 41 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 4.7 を保持した。
   - 41 行目 Claude Opus 4.7 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 42 行目 モデル別の設定表で、行見出しの製品名 Claude Sonnet 5.5 を保持した。
   - 42 行目 Claude Sonnet 5.5 の行で、Adaptive, between_tools の設定名を保持して訳し、注 3 への参照を保持した。
   - 42 行目 Claude Sonnet 5.5 の行で、既定値欄の On を「既定で有効」と訳した。
   - 43 行目 モデル別の設定表で、行見出しの製品名 Claude Sonnet 5 を保持した。
   - 43 行目 Claude Sonnet 5 の行で、既定値欄の On を「既定で有効」と訳した。
   - 44 行目 モデル別の設定表で、行見出しの製品名 Claude Haiku 5.5 を保持した。
   - 44 行目 Claude Haiku 5.5 の行で、既定値欄の On を「既定で有効」と訳した。
   - 44 行目 Claude Haiku 5.5 の行で、disabled の条件を説明する注 2 への参照を保持した。
   - 45 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 4.6 を保持した。
   - 45 行目 Claude Opus 4.6 の行で、Adaptive, extended (deprecated) を訳し、注 1 への参照を保持した。
   - 45 行目 Claude Opus 4.6 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 46 行目 モデル別の設定表で、行見出しの製品名 Claude Sonnet 4.6 を保持した。
   - 46 行目 Claude Sonnet 4.6 の行で、Adaptive, extended (deprecated) を訳し、注 1 への参照を保持した。
   - 46 行目 Claude Sonnet 4.6 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 47 行目 モデル別の設定表で、行見出しの製品名 Claude Opus 4.5 を保持した。
   - 47 行目 Claude Opus 4.5 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 48 行目 モデル別の設定表で、行見出しの製品名 Claude Haiku 4.5 を保持した。
   - 48 行目 Claude Haiku 4.5 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 49 行目 モデル別の設定表で、行見出しの製品名 Claude Sonnet 4.5 を保持した。
   - 49 行目 Claude Sonnet 4.5 の行で、既定値欄の Off を「既定で無効」と訳した。
   - 51 行目 拡張推論が非推奨である条件を説明する脚注の番号を「注 1」と示した。
   - 51 行目 disabled に対応する effort の範囲を説明する脚注の番号を「注 2」と示した。
   - 51 行目 between_tools に対応する effort の範囲を説明する脚注の番号を「注 3」と示した。
   - 55 行目 disabled を受理する Claude Opus 5、Claude Sonnet 5、Claude Haiku 5.5 の製品名を保持した。
   - 57 行目 拡張推論だけに対応する 3 つの旧モデルの名前を保持した。
   - 57 行目 データ保持なしで使うには明示的な許可が必要な 6 モデルの名前を保持した。
   - 73 行目 disabled で例示の 400 エラーを返す 7 モデルの名前を保持した。
   - 167 行目 以前の推論ブロックの再送で署名の 400 エラーが起き得る 7 モデルの名前を保持した。
   - 249 行目 続けて読む資料を示す節名 Next steps を「関連資料」と訳した。
   - 251 行目 関連資料のリンク Thinking を「推論の概要」と訳した。
   - 259 行目 関連資料のリンク Migrating to adaptive thinking を「適応型推論への移行」と訳した。
   - 19 行目 ガイド名 Thinking をリンク内で「推論の概要」と訳した。
   - 57 行目 節名 Model deprecations を「モデルの廃止予定」と訳した。
   - 87 行目 節名 Controlling thinking display を「推論の表示を設定する」と訳した。
   - 149 行目 ガイド名 Extended thinking を「拡張推論」と訳した。
   - 163 行目 Preserving thinking blocks と Thinking in tool and multi-turn workflows を「推論ブロックを保持する」と「ツール利用と複数ターンの処理における推論」と訳した。
   - 179 行目 節名 What must stay the same, and why を「同じ内容を保つ必要がある箇所と理由」と訳した。
   - 186 行目 節名 Which models run the prefix check を「先頭部分を照合するモデル」と訳した。
   - 201 行目 節名 Controlling thinking display を「推論の表示を設定する」と訳した。
   - 203 行目 Controlling thinking display と Progress updates between tool calls を「推論の表示を設定する」と「ツール呼び出し間の進捗報告」と訳した。
   - 205 行目 節名 Send assistant turns back exactly を「アシスタントターンを受け取ったとおりに返す」と訳した。
   - 213 行目 節名 Steering how often Claude thinks を「Claude が推論する頻度を調整する」と訳した。
   - 223 行目 節名 Running with thinking disabled を「推論を無効にして実行する」と訳した。
   - 231 行目 Cost control と Thinking and the context window を「費用を調整する」と「推論とコンテキストウィンドウ」と訳した。
   - 239 行目 節名 Thinking and prompt caching を「推論とプロンプトキャッシュ」と訳した。
   - 247 行目 Thinking and effort と Budget rules and tuning を「推論と effort」と「予算の規則と調整」と訳した。

## [2026-11-18] ingest | Troubleshooting thinking（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、モデル別の対応表とエラーメッセージ例 10 ブロックを収録。公式 Markdown の SHA-256 は `dbacf611790416291ab75fd2001c5cb37078086965d5170d8f2e9911e7ff11be`。raw の `source_sha256` は変換後の HTML の値。図は 0 枚。
   検査: W8 は `completed: true`、翻訳は `checked`（168 ブロック、確認 58 件、未解決 0 件）。訳した節名の警告 15 件を含め、理由は直前の prepare に記録。エラーメッセージ例 10 ブロックは公式 Markdown と一致。追加・更新・復元したページについて構造とグラフの lint に指摘なし。
   ページ: [[claude-thinking-troubleshooting]] を追加し、[[claude-thinking]]、[[claude-api-thinking]]、[[claude-thinking-tool-workflows]] から参照。main の同期時に一時退避されていた関連ソース 5 件とコンセプト 2 件を、対応する raw・図、索引・ログの記録とともに復元した。
   グラフ: 復元したページのノード +7、今回の新規ノード +1、型付きエッジ +0。再抽出後は合計 100 ノード、570 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Extended thinking
   翻訳検査で抽出された 28 件を原文と照合。公開名称と API 識別子は原綴りを保持し、見出し、状態、説明は文脈に合わせて訳した。残る警告 10 件はリンクの表示名を日本語にした箇所。リンク先と API の仕様を示す識別子は原文のまま。
   - 26・339 行目 Thinking を「推論の概要」と訳した。
   - 288 行目 Migrating to adaptive thinking を「適応型推論への移行」と訳した。
   - 314 行目 Thinking with tool use を「ツール利用時の推論」と訳した。
   - 335 行目 Prompt caching を「プロンプトキャッシュ」と訳した。
   - 347 行目 Steering thinking を「推論の調整ガイド」と訳した。
   - 386 行目 Effort levels を「effort の段階」と訳した。
   - 390 行目 Prompt caching in manual mode を「手動モードのプロンプトキャッシュ」と訳した。
   - 392 行目 Thinking、Effort、Migration guides を「推論の概要」、小文字の「effort」、「移行ガイド」とした。
   - 426 行目 リンクラベル Effort をパラメーター表記に合わせ、小文字の「effort」とした。

## [2026-11-18] ingest | Extended thinking（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、SDK 別のコード、キャッシュの検証結果、移行前後の設定例を含む 12 ブロックを収録。公式 Markdown の SHA-256 は `ef065bf685c676e645c14cb74637769c16613a52912958d713a422d9a8b390c9`。raw の `source_sha256` は変換後の HTML の値。図は 0 枚。
   検査: W8 は `completed: true`、翻訳は `checked`（86 ブロック、確認 28 件、未解決 0 件）。訳したリンク表示名の警告 10 件の理由は直前の prepare に記録。コードなど 12 ブロックは公式 Markdown と一致。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-api-extended-thinking]] を追加し、[[claude-api-thinking]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。[[claude-thinking]] に手動予算の制約と適応型推論への切り替え手順を追記。作業中に一時退避されたこの取り込みと前回までの関連ファイルを復元して検査した。
   グラフ: ノード +1、型付きエッジ +4。各ガイドが相手を直接参照する方向を `cites` として記録。再抽出後は合計 101 ノード、584 エッジ。

## [2026-11-18] ingest | Migration guides（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、モデル別ガイド 4 本と参照資料 3 件へのリンクを保持。公式 Markdown の SHA-256 は `0fad7eafec3ec7e15ebcd2a017d9a00f4e3f8604b334a7eb32ab98451569812e`。raw の `source_sha256` は変換後の HTML の値。
   検査: W8 は `completed: true`、翻訳は `checked`（11 ブロック、未解決 0 件、警告 0 件）。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-api-model-migration]] を追加し、[[claude-api-extended-thinking]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。ソースは移行先を選ぶための索引で、各モデルのガイドはリンク先として記録した。
   グラフ: ノード +1、型付きエッジ +1。拡張推論から一覧への公式の参照を `cites` として記録。再抽出後は合計 102 ノード、590 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Claude Fable 5.2 and Claude Mythos 5.2 migration guide
   翻訳検査で抽出された 46 件を原文と照合。モデル名、サービス名、認証プログラム名は原綴りを維持した。残る 69 件はリンクの表示名や節名の英語を日本語にした箇所。各リンクの行き先 199 件を公式 Markdown と照合した。行番号は検査対象ブロックの先頭を示す。
   - 27・134・260 行目。What を「Claude Fable 5.2 の新機能（27 行）と変更と見なされる操作（134・260 行）」として訳した。
   - 27 行目。Prompting を「Claude Fable 5.2 のプロンプトガイド」として訳した。
   - 34 行目。Recommended を「Claude Fable 5.2 の推奨 effort」として訳した。
   - 36 行目。Sampling を「サンプリングパラメーター」として訳した。
   - 39 行目。Which を「Claude API でモデルを切り替えても推論が保持される組み合わせ」として訳した。
   - 40・102・133・175・221・259・309 行目。Accounts を「アカウントとクラウドプラットフォーム」として訳した。
   - 42・156・208・286 行目。Pricing を「料金」として訳した。
   - 45・157・176・288・312・335・346 行目。Availability を「高速モードの提供状況」として訳した。
   - 50 行目。Rate を「レート制限」として訳した。
   - 54・72 行目。Thinking を「別の会話にひも付いた推論ブロック」として訳した。
   - 72・198 行目。Test を「先頭部分の照合に失敗する処理を検出するテスト」として訳した。
   - 72・198 行目。Change を「先頭部分の照合を保ったままツールや指示を変更する」として訳した。
   - 75・112・201・241・281 行目。Switch を「モデルを切り替えて元に戻す」として訳した。
   - 78 行目。Migrate を「computer_20251124 から移行する」として訳した。
   - 79・152・287 行目。Model を「モデルの互換性（79 行）とモデル別のデータ保持要件（152・287 行）」として訳した。
   - 79・333 行目。Result を「結果の種類」として訳した。
   - 79 行目。Give を「セッションにアドバイザーを設定する」として訳した。
   - 87 行目。Calibrate を「effort を調整する」として訳した。
   - 88 行目。Set を「サブエージェントの利用を見込む」として訳した。
   - 91 行目。Behavior を「挙動の違い」として訳した。
   - 104・137・180・228・263・315 行目。Review を「旧モデル向けのプロンプトと実行環境を見直す」として訳した。
   - 110・134・260・280・305 行目。Editing を「過去のターンを編集すると推論ブロックが無効になる」として訳した。
   - 116・203・284 行目。Use を「computer_20251124 からツールセットに移す」として訳した。
   - 135・155・261・285 行目。Refusals を「拒否とフォールバック、または拒否、フォールバック、課金」として訳した。
   - 157・288 行目。Fast を「高速モードの料金」として訳した。
   - 172 行目。Failed を「先頭部分の照合に失敗すると 400 エラーになる」として訳した。
   - 184・234・319 行目。Migrating を「移行元と移行先を示す節見出し」として訳した。
   - 195・279 行目。Forced を「ツール選択を強制すると 400 エラーになる、または強制ツール利用に対応していない」として訳した。
   - 195 行目。Strict を「厳密なツール利用」として訳した。
   - 195・198・216・218 行目。Mid を「会話途中のシステムメッセージに関する節名」として訳した。
   - 195 行目。Forcing を「ツール利用の強制」として訳した。
   - 210 行目。Per を「メッセージ単位の effort」として訳した。
   - 283 行目。Progress を「ツール呼び出し間の進捗報告」として訳した。
   - 303 行目。Preserving を「推論ブロックの保持」として訳した。
   - 331 行目。Prompt を「プロンプトキャッシュ」として訳した。

## [2026-11-18] ingest | Claude Fable 5.2 and Claude Mythos 5.2 migration guide（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コードとエラー例 8 ブロックおよびリンク先 199 件を原文と照合した。公式 Markdown の SHA-256 は `d5e20ba369480fdf64908540b08ca9b1c1402984104c5eb6d6f8fbe19321334f`。raw の `source_sha256` は変換後の HTML の値。
   検査: W8 は `completed: true`、翻訳は `checked`（200 ブロック、確認 46 件、未解決 0 件）。訳したリンク表示名と節名の警告 69 件は直前の prepare に記録。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-fable-5-2-migration]] を追加し、[[claude-api-model-migration]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。[[claude-thinking]] にモデルを切り替える方向による推論ブロック保持の違いを追記。一時退避されていた前回までの関連ファイルを復元し、更新済みの main の索引とログに統合した。
   グラフ: 今回の新規ノード +1、型付きエッジ +1。モデル移行ガイド一覧からの公式参照を `cites` として追加。再抽出後は合計 103 ノード、599 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Claude Opus 5.5 migration guide
   翻訳検査で抽出された 41 件を原文と照合。モデル名、サービス名、API 識別子は原綴りを維持した。残る 43 件は見出し、リンクの表示名、またはプロンプトの例を日本語にした箇所。リンク先 142 件を公式 Markdown と照合した。行番号は検査対象ブロックの先頭を示す。
   - 25・27・341・354・871・1148・1154・1173・1682 行目。What を含む表現は「すべてのリクエストに共通する要件、Claude Opus 5.5 の新機能、または変更点」に対応する。
   - 25・283・341・1148・1158・1173・1190・1450・1682 行目。Handle を含む表現は「各応答の推論を処理する」に対応する。
   - 27 行目。Pricing を含む表現は「料金」に対応する。
   - 27・1143・1468 行目。Prompting を含む表現は「Claude Opus 5.5 のプロンプトガイド」に対応する。
   - 33・350 行目。Availability を含む表現は「提供状況」に対応する。
   - 35・1448 行目。Recommended を含む表現は「Claude Opus 5.5 の推奨 effort」に対応する。
   - 223 行目。Cost を含む表現は「費用の調整」に対応する。
   - 223・1143 行目。Prompts を含む表現は「推論を無効にする前提で書いたプロンプト」に対応する。
   - 225 行目。Preserving を含む表現は「推論ブロックの保持」に対応する。
   - 263 行目。Controlling を含む表現は「推論の表示を設定する」に対応する。
   - 264・1460・1562 行目。Text を含む表現は「ツール呼び出し間のテキストは推論ブロックで返る（264・1460 行）とテキストエディターツール（1562 行）」に対応する。
   - 280・871 行目。Preserved を含む表現は「推論の保持」に対応する。
   - 354 行目。Breaking を含む表現は「互換性を損なう変更」に対応する。
   - 358・871 行目。Thinking を含む表現は「推論は常に有効（358 行）と推論ブロックはモデルと会話にひも付く（871 行）」に対応する。
   - 555 行目。Forced を含む表現は「強制ツール利用は非対応」に対応する。
   - 867 行目。Prefix を含む表現は「推論ブロックの先頭部分の照合」に対応する。
   - 1134・1460 行目。User を含む表現は「利用者向けの進捗報告」に対応する。
   - 1138 行目。Refusals を含む表現は「拒否とフォールバック」に対応する。
   - 1138 行目。Safeguard を含む表現は「安全対策による拒否」に対応する。
   - 1142・1181 行目。Effort を含む表現は「effort」に対応する。
   - 1148・1173・1175・1476・1497・1682 行目。Migrating を含む表現は「移行元と移行先を示す節名」に対応する。
   - 1159・1694 行目。Prompt を含む表現は「プロンプトキャッシュ」に対応する。
   - 1184 行目。Stop を含む表現は「停止理由とフォールバック」に対応する。
   - 1184 行目。Safety を含む表現は「安全性分類器とフォールバック」に対応する。
   - 1451 行目。Token を含む表現は「トークン数を数える」に対応する。
   - 1460 行目。After を含む表現は「ツールを 3 回呼び出すごとに進捗を要約する、という指示の例」に対応する。
   - 1465 行目。High を含む表現は「Claude Opus 4.7 の高解像度画像対応」に対応する。
   - 1502 行目。Sampling を含む表現は「サンプリングパラメーターの廃止」に対応する。
   - 1563 行目。Code を含む表現は「コード実行ツール」に対応する。

## [2026-11-18] ingest | Claude Opus 5.5 migration guide（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コード例 111 ブロックとリンク先 142 件を原文と照合した。公式 Markdown の SHA-256 は `1ce7e78cc1ba79a08b17fa19c4bc78cf9a1acd31eb128d53334ab5b8e6e544ce`。raw の `source_sha256` は変換後の HTML の値。
   検査: W8 は `completed: true`、翻訳は `checked`（201 ブロック、確認 41 件、未解決 0 件）。訳した見出し、リンク表示名、プロンプト例の警告 43 件の確認結果は直前の prepare に記録。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-opus-5-5-migration]] を追加し、[[claude-api-model-migration]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。一時退避されていた前回までの関連ファイルを復元した。
   グラフ: ノード +1、型付きエッジ +1。モデル移行ガイド一覧からの公式参照を `cites` として追加。再抽出後は合計 104 ノード、606 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Claude Sonnet 5.5 migration guide
   翻訳検査で抽出された 44 件を原文と照合。モデル名、サービス名、API 識別子を維持した。残る 27 件はリンクの表示名を訳した箇所。リンク先 84 件を公式 Markdown と照合した。行番号は検査対象ブロックの先頭を示す。
   - 27・1240 行目。Pricing を含む表示名は「料金」に対応する。
   - 27・886 行目。What を含む表示名は「Claude Sonnet 5.5 の新機能」に対応する。
   - 27・890 行目。Prompting を含む表示名は「Claude Sonnet 5.5 のプロンプトガイド」に対応する。
   - 221・898 行目。Turn を含む表示名は「最初の応答前の推論を省く」に対応する。
   - 235 行目。Preserving を含む表示名は「推論ブロックの保持」に対応する。
   - 236 行目。Cost を含む表示名は「費用の調整」に対応する。
   - 238 行目。Controlling を含む表示名は「推論の表示を設定する」に対応する。
   - 250 行目。Running を含む表示名は「最初の応答前の推論を省いて実行する」に対応する。
   - 514 行目。Availability を含む表示名は「提供状況」に対応する。
   - 841 行目。Switch を含む表示名は「モデルを切り替えて元に戻す」に対応する。
   - 843 行目。Mid を含む表示名は「会話途中のシステムメッセージとツールの変更」に対応する。
   - 845 行目。Prefix を含む表示名は「推論ブロックの先頭部分の照合」に対応する。
   - 849 行目。Preserved を含む表示名は「推論の保持」に対応する。
   - 855 行目。Migrate を含む表示名は「computer_20251124 から移行する」に対応する。
   - 861 行目。Model を含む表示名は「モデルの互換性」に対応する。
   - 867 行目。User を含む表示名は「利用者向けの進捗報告」に対応する。
   - 879 行目。Refusals を含む表示名は「拒否とフォールバック」に対応する。
   - 879 行目。How を含む表示名は「拒否時の課金」に対応する。
   - 885 行目。Prompt を含む表示名は「プロンプトキャッシュ」に対応する。
   - 890・1192・1217 行目。Recommended を含む表示名は「推奨する変更、または Claude Sonnet 5.5 の推奨 effort」に対応する。
   - 898 行目。Thinking を含む表示名は「推論は既定で有効」に対応する。
   - 1187 行目。Handle を含む表示名は「応答の推論を処理する」に対応する。
   - 1193 行目。Resolution を含む表示名は「解像度とトークンの消費量」に対応する。
   - 1221 行目。Fine を含む表示名は「細かな単位でのツール入力のストリーミング」に対応する。
   - 1230 行目。Stop を含む表示名は「停止理由とフォールバック」に対応する。
   - 1237 行目。Migrating を含む表示名は「Claude Sonnet 4.5 以前からの移行」に対応する。

## [2026-11-18] ingest | Claude Sonnet 5.5 migration guide（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コード例・エラーメッセージ 68 ブロックとリンク先 84 件を原文と照合した。公式 Markdown の SHA-256 は `4819f3cb7d3e483cb7a87eaf65e1731affea937af72a1bf7506862a3d95e17e1`。raw の `source_sha256` は変換後の HTML の値。
   検査: W8 は `completed: true`、翻訳は `checked`（155 ブロック、確認 44 件、未解決 0 件）。リンク表示名を訳した箇所の警告 27 件の確認結果は直前の prepare に記録。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-sonnet-5-5-migration]] を追加し、[[claude-api-model-migration]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。一時退避されていた前回までの関連ファイルを復元した。
   グラフ: ノード +1、型付きエッジ +1。モデル移行ガイド一覧からの公式参照を `cites` として追加。再抽出後は合計 105 ノード、613 エッジ。

## [2026-11-18] prepare | Web raw の警告の確認: Claude Haiku 5.5 migration guide
   翻訳検査で抽出された 17 件を原文と照合。モデル名、プラットフォーム名、API 識別子を維持した。残る 25 件はリンクの表示名を訳した箇所。リンク先 44 件を公式 Markdown と照合した。行番号は検査対象ブロックの先頭を示す。
   - 25・48 行目。Migrating を含む表示名は「Claude Haiku 3.5 以前から Claude Haiku 5.5 への移行」に対応する。
   - 25 行目。Migration を含む表示名は「モデル移行ガイド一覧」に対応する。
   - 25 行目。Model を含む表示名は「モデルの廃止予定」に対応する。
   - 33・110・172 行目。Use を含む表示名は「Claude Haiku 5.5 のモデル ID を使う（33・172 行）、effort で推論を調整する（110 行）」に対応する。
   - 34 行目。Recount を含む表示名は「トークンを数え直す」に対応する。
   - 35・36 行目。Configure を含む表示名は「推論を設定する」に対応する。
   - 37 行目。Remove を含む表示名は「サンプリングパラメーターを取り除く」に対応する。
   - 38 行目。Replace を含む表示名は「アシスタントの応答の事前入力を置き換える」に対応する。
   - 39 行目。Move を含む表示名は「コンピューター操作をツールセットに移行する」に対応する。
   - 40 行目。Replay を含む表示名は「生成元アカウントで推論ブロックを再送する」に対応する。
   - 41 行目。Keep を含む表示名は「過去のターンを保持する」に対応する。
   - 42 行目。Safeguard を含む表示名は「安全対策による拒否」に対応する。
   - 77 行目。Pricing を含む表示名は「料金」に対応する。
   - 77 行目。Long を含む表示名は「長いコンテキストの料金」に対応する。
   - 79 行目。Resolution を含む表示名は「解像度とトークンの消費量」に対応する。
   - 114 行目。Thinking を含む表示名は「モデル別の推論ブロックの保持」に対応する。
   - 129 行目。Switch を含む表示名は「モデルを切り替えて元に戻す」に対応する。
   - 129 行目。Which を含む表示名は「Claude API でモデルを切り替えても推論が保持される組み合わせ」に対応する。
   - 148 行目。Migrate を含む表示名は「computer_20251124 から移行する」に対応する。
   - 156 行目。Accounts を含む表示名は「アカウントとクラウドプラットフォーム」に対応する。
   - 162 行目。Prefix を含む表示名は「推論ブロックの先頭部分の照合」に対応する。
   - 173 行目。Upgrade を含む表示名は「最新のツールバージョンに更新する」に対応する。
   - 174 行目。Text を含む表示名は「テキストエディターツール」に対応する。
   - 175 行目。Stop を含む表示名は「停止理由とフォールバック」に対応する。
   - 177 行目。Prompting を含む表示名は「Claude Haiku 5.5 のプロンプトガイド」に対応する。

## [2026-11-18] ingest | Claude Haiku 5.5 migration guide（Claude Platform Docs）
   raw: Codex（GPT-6）で翻訳。公式 Markdown 版を HTML に変換して取り込み、コード例 3 ブロックとリンク先 44 件を原文と照合した。公式 Markdown の SHA-256 は `ec102aa9b2468f8ecec1649a165b2ce3e88c058be5953f2bdcc308ff00ca7aef`。raw の `source_sha256` は変換後の HTML の値。
   検査: W8 は `completed: true`、翻訳は `checked`（96 ブロック、確認 17 件、未解決 0 件）。リンク表示名を訳した箇所の警告 25 件の確認結果は直前の prepare に記録。対象ページの構造とグラフの lint に指摘なし。
   ページ: [[claude-haiku-5-5-migration]] を追加し、[[claude-api-model-migration]] と [[claude-thinking-troubleshooting]] に相互リンクを追加。モデル移行ガイド一覧の 4 件はすべて取り込み済み。
   グラフ: ノード +1、型付きエッジ +2。公式ガイドと一覧が相互に参照する関係を `cites` として追加。再抽出後は合計 106 ノード、621 エッジ。

## [2026-11-19] ingest | wiki 0.35.1 のリリースと公開マーケットプレイスからの導入の記録
   ページ: [[リリースごとの導入の確かめの記録]] に、Claude Code と Codex での導入と変更15ファイルの照合結果を追記。

## [2026-11-19] ingest | wiki 0.36.0 のリリースと公開マーケットプレイスからの導入の記録
   ページ: [[リリースごとの導入の確かめの記録]] に、Claude Code と Codex での導入、変更41ファイルの照合、原本・MCP 起動ファイル・グラフの検証結果を追記。

## [2026-11-19] ingest | wiki 0.37.0 の公開と静的版 browse の図の確認を [[リリースごとの導入の確かめの記録]] に追記。

## [2026-11-19] ingest | オントロジーの要件・レビュー・Ossieへの引継ぎ
   出典2ページ、概念2ページ、引継ぎの入口1ページを追加。エッジの識別子と書く段の設計を関連付け、原文2件の写しをrawに保存。採用・実装・本番移行は未決定または未実施と明記。
   グラフ: ノード +5、型付きエッジ +0（既存の語彙を維持、wikilinkと出典を再生成）。

## [2026-11-19] ingest | wiki 0.38.0 の公開と Codex セッションの会話版の導入確認を [[リリースごとの導入の確かめの記録]] に追記。
