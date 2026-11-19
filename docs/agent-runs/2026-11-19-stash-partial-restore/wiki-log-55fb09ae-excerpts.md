# stash 55fb09aeに保存されていたwikiログの抜粋

2026-11-19に復元。以下は当時の記録であり、現在の作業ツリーで処理を再実行した証拠ではない。記載された件数・版・完了判定は当時の対象に限る。現行の記事はその後の追記を保持し、今回の復元操作は現在のwiki/log.mdへ別に記録する。

元stash: `55fb09ae3e3b9c200f9c15340464ae7877998b2d`。元ログのSHA-256: `d8ce4cb965d208ed26c88c347081c43ea1ae37e69d5912f77379f8ec8b062921`。現行ログに同じ見出しがなかった11区間を選び、抜粋本文の文言を変更せず、改行をLFへそろえた。

## [2026-11-17] ingest | Building an Ontology Agent: Which Parts Actually Need an LLM?
   ページ: sources/building-an-ontology-agent、concepts/オントロジー候補の生成と採用の分離（新規）。concepts/エージェントに守らせる決まりの書き方、index を更新
   raw: Codex が自分のモデル（GPT-6）で作った。訳: GPT-6、補足: GPT-6（図 1 点）。HTTP 403 のため、ユーザーがブラウザで保存した全文の HTML を使用。raw の検査は誤り・警告ともに 0 件
   グラフ: ノード +2、型付きエッジ +0

## [2026-11-17] ingest | 企業 AI のオントロジー設計と LLM の推論の根拠付け
   ページ: sources/ontology-engineering-for-enterprise-ai、concepts/オントロジーと知識グラフの役割（新規）。concepts/オントロジー候補の生成と採用の分離、index を更新
   raw: Codex が自分のモデル（GPT-6）で作った（`wiki:web-raw` がなかった）。訳: なし。著作権のある外部記事の全文訳は生成せず、英語原文を保持し、日本語の要約を wiki に保存した。補足: GPT-6（図 1 点）
   取得: HTTP 403 のため、Edge で開いていた同じ URL の記事を HTML のみで保存し、`--html-file` で本文を抽出した。`source_sha256_of: dom`。`language_override: keep` の検査は誤り・警告ともに 0 件、作業用の写しは削除済み
   留保: 記事中の効果の数値は元の研究を未確認。クラス数などの推奨値は著者の設計上の目安とした。型付きの関係は追加しない
   グラフ: ノード +2、型付きエッジ +0（合計 87 ノード、453 エッジ）。再抽出済み。構造の lint に追加の問題はなく、既存のソフト上限超過 1 件と未登録のタグを持つ 20 ページは変更なし

## [2026-11-18] ingest | myKG でナレッジグラフを作り、Claude Desktop に接続する
   ページ: sources/mykgとclaude-desktopの接続、entities/mykg（新規）。concepts/既存リンクからのグラフ検索の出典と原文照合の事例、index を更新
   raw: 自分のモデル（GPT-6）で作った（Codex には `wiki:web-raw` がない）。訳: GPT-6、補足: GPT-6（画像 11 点）。英語本文を段落ごとに日本語化し、コード・リンク・画像の対応を検査した
   取得: HTTP 403 とブラウザ操作ツールのエラーの後、利用者が指定した `wiki/.wiki-cache/browser/bring-your-mykg-knowledge-graph-to-claude-desktop.html` から `--html-file` で抽出。`source_sha256_of: dom`、HTML の SHA-256 は ea1aa3545adfa4e834d12d530d7426037dc0c815bb249a5afa155e41ef0309d0。取得時刻は 2026-11-17T23:56:27+09:00
   警告を受理する理由: `new_tokens` 2 件（raw の 71、79 行の README と FastMCP）。両語とも原文のリンクの表示名として存在するが、元の Markdown の前後に空白がなく、検査器の単語分割で隣の英語と結合されるため「原文にない」と出る。リンク先と表記を保持し、内容を追加していないことを確認した
   留保: 記事の小規模なデモと現行版の仕様を区別した。グラフのチームの誤統合を原文で分け直す説明は画像 11 にあるが、元のデモファイルでの再現確認はしていない。架空の会社・人物のページと型付きの関係は作らない
   検査: raw の `needs_translation: true`、`language_override: null`、誤り 0 件。上記の警告 2 件を理由付きで受理し、`--finish --accept-warnings` で作業用の写しを削除した。raw の SHA-256 は 4622eaf2731b061573d0f80b77096feffb80f1802c197c7846f848f3ffd6345f。画像と補足は各 11 点
   グラフ: ノード +2、型付きエッジ +0（合計 89 ノード、463 エッジ）。再抽出し、`product:mykg` から出典と既存のコンセプトをたどれることを確認した。構造とグラフの lint に追加の問題はなく、既存のソフト上限超過 1 件と未登録のタグを持つ 20 ページは変更なし
   検索: MCP の `query` で新しいソースと myKG のページが返ることを確認した。確認時は埋め込みモデルの準備中（`index.state: embedding`、587 セクション、埋め込み済み 0）だったため、語彙検索のみの結果を使った

## [2026-11-18] ingest | オントロジーの記述例
   ページ: concepts/オントロジーの記述例、sources/オントロジーの記述例-2026-11-18（新規）。concepts/オントロジーと知識グラフの役割に参照を追加し、index を更新
   raw: この会話の記述例を整理した作成メモを raw/オントロジーの記述例-2026-11-18.md に保存。会話履歴の転載ではない
   留保: 不具合・実装・試験は架空の例。ontology.yaml は変更せず、型付き関係も追加しない
   検査: 記述例をメモリ上の試料に読み込み、2種類の型付き関係が lint を通ることを確認。実 wiki の構造・グラフの lint に追加の問題はなく、既存のソフト上限超過 1 件と未登録のタグを持つ 20 ページは変更なし
   グラフ: ノード +2、型付きエッジ +0（合計 91 ノード、473 エッジ）。コードフェンス内の架空の関係を実データにせず、記事の参照を再抽出した

## [2026-11-18] ingest | myKG のアーキテクチャ
   ページ: sources/mykgのアーキテクチャ、concepts/スキーマの導出と事実の抽出の分離（新規）。entities/mykg、concepts/オントロジーと知識グラフの役割、sources/mykgとclaude-desktopの接続、index を必要な箇所だけ更新
   ソース: GitHub の README と、コミット afb0a9c9bafdc49751563b9aa7f59bcf4bb787fb の設計文書・主要実装 14 ファイル。raw/mykg-source-afb0a9c9/manifest.json に取得元、Git blob SHA-1、保存ファイルの SHA-256 を記録し、15 ファイルすべてを Git blob の値と照合した
   raw: 自分のモデル（GPT-6）で作った（Codex には wiki:web-raw がない）。訳: GPT-6。補足: GPT-6（概要図と二段階の抽出図の 2 点）。HTTP で article の本文を取得し、飾りのロゴ・バッジ 14 点と目次だけを除去して freeze を通した。README の本文はブロック単位で全文を訳し、コード・リンク・画像と対応を照合した。補助のリポジトリの原文・コードは固定コミットのまま保存した
   取り込みの焦点: 二段階の抽出、12 段階の処理、JSONL とメモリ上のグラフ、セッションと再開、孤立ノードの補正、アダプター、差分更新・統合、MCP の探索。構成図と処理・責務の表を追加した
   留保: コードの読み取りによる調査で、LLM を使う抽出や性能の測定は行っていない。スキーマ検証が非停止であること、混合バッチの出所の過剰付与と更新後の残存、DiGraph が同じ両端の複数関係を独立した多重エッジとして持たないことを明記した。MCP のツール数は README・実装の 16、設計文書の一部の 15、以前の記事の 14 を分けた。info-hive の設計・実装や依存パッケージは変更していない
   検査の経路: 接続済みの wiki MCP は既にない 0.29.0 のパスを参照して起動に失敗したため、CLI へ戻った。作業中に指定版 0.30.0 のキャッシュのスクリプトも利用できなくなり、同じ開発リポジトリのスクリプトで検査を継続した
   raw の警告を受理する理由（missing_names 13 件）: 34 行の Use は使用するという動詞、52 行の Websites・Anything は Web サイト・許可リスト外という一般語、113 行はコマンド表セルの先頭の動詞、128 行は記事題名の一般語（Documents・Living・Knowledge・Graph）であり、日本語の訳と元のリンクを保った。固有の製品名・人名の脱落ではない
   raw の警告を受理する理由（続き）: 149 行の Recommended・Implicit・Access は推奨・暗黙・利用、192 行はオプション表の一般語と強調（NEW・MODIFIED・DELETED など）、328 行は出力形式の用途と一般名（Human・Network・Edge・Text・Adjacency・Topology）を訳したもの。原文のコード・製品名を保持したまま、文頭の大文字を名前として拾う警告である
   raw の警告を受理する理由（続き）: 541 行の LLM は元の claude-as-LLM を引用するコードと用途の訳であり、672 行は Wrong・Edit・Want・Bad という一般の動詞・形容詞、719 行は Locked・Exactly・None という比較表の一般語である。786 行の GB は multi-GB を数ギガバイトと訳した単位、863 行の Name・Skip・Locked・Force はオプションの説明、1026 行の Schema・Reconciles・Re はスキーマと再実行の説明である。内容の省略や新しい主張の追加はなく、日本語訳を保って受理する
   検査: raw の check は ok=true、誤り 0 件。上記の警告 13 件を理由付きで受理し、--finish --accept-warnings で作業用の写しを削除した。translated_by と caption_names は GPT-6、raw の SHA-256 は a362c5beeca3897c1909133903f759bfa0617234b6bb9c1d5a1ec87a7626d5cf。構造の lint は新しい検出なし（既存のソフト上限超過 1 件、未登録タグ 20 ページは不変）、グラフの lint は全項目 0 件、今回編集した既存ファイルの git diff --check は合格
   グラフ: ノード +2、型付きエッジ +0（合計 93 ノード、490 エッジ、全エッジは +17）。新規ページと更新した参照を再抽出した。製品固有の実装の説明から依存関係などの述語を無理に作らず、通常の参照と出典のリンクでつないだ

## [2026-11-18] ingest | info-hive のプロジェクト用オントロジー設計
   原本は設計第2版の Markdown。[[プロジェクト用オントロジーの設計-2026-11-18]] と [[プロジェクト用オントロジーの設計案]] を作成し、一般例と役割の2ページを部分更新した。本番の ontology と試料の型付き関係は適用していない。
   グラフ: ノード +2、型付きエッジ +0（合計95ノード・507エッジ）。構造とグラフの lint を確認した。

## [2026-11-18] prepare | Web raw の警告の確認: MinerU
   README の本文を GPT-6 で日本語に訳し、コード、リンク、ブロックの構造を照合した。翻訳確認の 59 件は、形式や製品の名称、日本語の漢字見出し、数値・単位、原語の UI 表記であり、原文と訳文を対象ごとに確認した。理由・全文・両方の SHA-256 は raw/mineru-source-b4efa4b2/web-raw-review.json に保存した（独立モデルのレビューではない）。
   取得時に除いたもの: 飾りのロゴ、統計・デモのバッジ、言語とコミュニティのナビゲーション、貢献者の画像とスター数の図。freeze は削除だけであることを検査した。削除量が約 39% という警告は、画像 URL 内の長いエンコード文字列が主因であり、本文、インストール例、エージェント向けガイド、ライセンスと謝辞の内容は残した。デモのリストでは画像だけを除いて flash/basic の制限の文を残した。
   raw 15 行、missing_names: Use は使用するという動詞であり、冒頭の説明を日本語に訳した。
   raw 72 行、missing_names: Routers は複数形で、訳文は同じ製品を Router と単数形で表した。サーバー、SDK、クライアントを一緒に更新する条件は保った。
   raw 83 行、missing_names: Output Formats and Result Contract はリンク先の一般的な題名で、「出力形式と結果の契約」と訳し、URL を保った。
   raw 91 行、missing_names: Parsing Tiers Guide はガイド名の一般語で、「解析の段階のガイド」と訳し、MinerU 4.x とリンク先を保った。
   raw 97 行、missing_names: Due は ZeroGPU の制限による理由を導く一般語で、「制限により」と訳した。flash/basic の制約はそのままである。
   raw 165 行、missing_names: Tiers と Release はリンクの一般語で、品質の段階、リリースの履歴と訳した。すべての URL を保った。
   raw 167 行、new_tokens: 原文の non-NVIDIA を NVIDIA 以外と訳した。NVIDIA は元の複合語に含まれる同じ固有名であり、追加した対応機器ではない。
   raw 202 行、missing_names: Extensions、Images、Rich は入力表の一般語で、拡張子、画像、リッチテキストと訳した。各拡張子と製品名を保った。
   raw 432 行、missing_names: 品質表の Chinese/Quality/Use/Lowest/Discovery/Basic/Private/Standard/Default/Difficult は列名や説明の一般語である。中国語名、日本語の説明、各 tier 識別子と品質・速度・用途の対応を保った。
   raw 443 行、new_tokens: non-MinerU parser を MinerU 以外のパーサーと訳した。元の複合語中の製品名をそのまま表したもので追加の道具ではない。
   raw 444 行、new_tokens: non-MinerU parser を MinerU 以外のパーサーと訳した。選択を待つという制約を保ち、元の複合語中の製品名を保持した。
   raw 450 行、missing_names: Chinese は説明する言語を指す一般名で、中国語と訳した。UI 名の标准解析と standard は日本語の説明付きで保った。
   raw 466 行、missing_names: Model/How/Already/Install は追加機能表の列名や動詞で、実行エンジン、導入方法、既に含む、入れると訳した。実装名と extras は保った。
   raw 470 行、missing_names: Model/Min/Accelerator/None は資源表の一般語で、モデル、最小、アクセラレーター、不要と訳した。各数値、GB、GPU/MPS と対応を保った。
   raw 530 行、missing_names: 原文の文中の製品名 MinerU は訳文でコマンド識別子 mineru として説明している。同じブロックの mineru[full]、uv tool、二つの mineru、running=false のインラインコードは照合済みである。
   raw 546 行、missing_names: Recommended/Model/Extra は機器表の列名で、推奨、実行エンジン、追加機能と訳した。機器、段階、エンジン、extras の組合せを保った。
   raw 884 行、missing_names: Meaning は環境変数表の一般的な列名で、意味と訳した。MINERU_HOME/MINERU_API_KEY と既定パスを保った。
   raw 946 行、missing_names: Assess Local Hardware は手順の見出しで、ローカルの機器を調べる手順と訳した。未設定と機器非対応を区別する条件を保った。
   raw 947 行、missing_names: Quality Tiers は説明節の見出しで、品質の段階と訳した。機器の検査後に選択するという順序を保った。
   raw 955 行、missing_names: エラー表の Meaning/Agent と各文頭の動詞・普通名詞は、意味・対処と日本語のエラー説明へ訳した。全エラーコード、MinerU、API、各インラインコマンド、復旧と許可の条件を保ち、新しい対処は追加していない。
   raw 1054 行、missing_names: MinerU-Diffusion の副題の Document/Inverse/Rendering/Decoding は文書・逆・レンダリング・復号と訳した。製品名と URL は保持した。
   raw 1055 行、missing_names: Data/Preparation/Operators/Pipelines は DataFlow のリンクの説明の一般語で、データ準備・オペレーター・パイプラインと訳した。元の URL は保持した。
   raw 1057 行、missing_names: Lightweight/Multi/Data/Annotation/Tool は LabelU の説明で、軽量・マルチモーダルデータ・注釈・ツールと訳した。LabelU と URL は保持した。
   raw 1058 行、missing_names: Open/Dialogue/Annotation/Platform は LabelLLM の説明で、オープン・対話・注釈・基盤と訳した。LabelLLM と LLM と URL は保持した。
   raw 1059 行、missing_names: Comprehensive/Toolkit/High/Quality/Content/Extraction は PDF-Extract-Kit の説明で、総合・ツールキット・高品質・内容・抽出と訳した。製品名と URL は保持した。
   raw 1060 行、missing_names: Comprehensive/Benchmark/Document/Parsing/Evaluation は OmniDocBench の説明で、総合・ベンチマーク・文書・解析・評価と訳した。製品名と URL は保持した。
   raw 1061 行、missing_names: Mixed は Magic-HTML の説明の形容詞で、混在すると訳した。製品名と URL は保持した。
   raw 1062 行、missing_names: Fast は Magic-Doc の説明の形容詞で、高速と訳した。製品名、対応拡張子と URL は保持した。
   raw 1063 行、missing_names: Comprehensive/Data/Quality/Evaluation/Tool は Dingo の説明で、総合的・データ・品質・評価・ツールと訳した。Dingo と AI と URL は保持した。

## [2026-11-18] ingest | MinerU のアーキテクチャと日本語対応
   ページ: sources/mineru-readme、entities/mineru（新規）。concepts/抽出の品質の測り方、sources/抽出の方式の比較-markitdown-2026-11-15、index を必要な箇所だけ更新した。
   ソース: 公式 README と固定コミット b4efa4b2b76ebb012c476b79bdfc6f18a95aacd6 の設計文書・実装など 20 ファイル。mineru/version.py は 4.2.3。各ファイルを Git blob SHA-1 と SHA-256 で検証し、raw/mineru-source-b4efa4b2/manifest.json に取得元を残した。
   raw: 自分のモデル（GPT-6）で作った（Codex には wiki:web-raw がない）。訳: GPT-6。補足: なし（ロゴ・バッジ・スター数などの飾りを除き、内容の図はなかった）。README のエージェント向けの指示は資料として保存し、実行していない。375 ブロック、コードとリンクを照合し、completed=true、translation.state=checked、translation.pending_reviews=0、work_dir_removed=true を確認した。59 件の翻訳の確認と 29 件の警告受理の理由は直前の prepare と raw/mineru-source-b4efa4b2/web-raw-review.json、完了 JSON は web-raw-check.json に保存した。
   焦点: DocVortex と MinerU の分担、PDF の txt/ocr と 4 段階の処理、モデルと実行エンジン、Tasks/Router/Doclib、日本語 OCR の japan→ch の正規化。構成図と処理の比較表を保存した。
   留保: 文書解析を実行した精度・速度の測定はしていない。日本語の縦書き、ルビ、旧字体、読み順、表・数式の品質と VLM の日本語精度は未検証。以前の OCR を除いた MarkItDown 比較から MinerU の優劣を判断せず、info-hive の方式・依存・版は変更していない。
   検査: 構造の lint に新しい検出なし（既存のソフト上限超過 1 件）、グラフの lint は全項目 0 件。新規ページはそれぞれ 100 行未満。今回編集した既存ファイルの git diff --check は合格。検索を使った時点では wiki MCP の索引が embedding で、意味の検索は一部のみの状態だったため、関連ページは先に読んだ index の候補から選んだ。
   グラフ: ノード +2、型付きエッジ +0（合計 97 ノード、519 エッジ、全エッジは +12）。新規ページ・出典・関連リンクを再抽出した。

## [2026-11-18] ingest | MinerU と現在の日本語 PDF 抽出の比較
   ソース: docs/research/mineru-japanese-comparison-2026-11-18.md の UTF-8 原文を raw/mineru日本語pdf比較-2026-11-18.md に保存。SHA-256: 229c2c0908252521bac87bb4bf04d2d9c26dac96ba452b82a9be8e280fad6d3b。比較試料と抽出結果は raw の記録を参照。
   ページ: sources/mineru日本語pdf比較-2026-11-18 を新規作成し、entities/mineru、concepts/抽出の品質の測り方、index を更新。少数の合成試料、ルビの実文書と速度の未検証、表の数値欠落を明記した。
   グラフ: ノード +1、型付きエッジ +0（合計 98 ノード、527 エッジ）。構造とグラフの lint では新しい検出なし。

## [2026-11-18] ingest | browse の静的 Mermaid の隔離と性能の検証
   セッション: ターン 440、手で伏せた区間 0、消したターン 0。2026-11-17 21:38〜2026-11-18 08:40（+09:00）、依頼より前で固定。当時の Codex のモデルは不明。
   ページ: ソース 1・コンセプト 2 を新規作成。browseの画面の確かめ方に関連リンクを追加し、index を更新。静的 PoC の範囲、未統制の時間差、製品化保留を記録。
   グラフ: ノード +3、型付きエッジ +0。出典と関連リンクを再抽出。

## [2026-11-18] ingest | browse の静的 Mermaid の隔離と性能の検証（会話版）
   セッション: ターン 74、手で伏せた区間 0、消したターン 0。前回と同じ範囲からツール呼び出し366件を省いた。
   ページ: sources/browseの静的mermaidの隔離と性能の検証-2026-11-18-会話版 を追加。隔離修正の結果、性能測定で残った課題、静的版の製品組み込みの保留を冒頭にまとめた。
