# 調査・リサーチ系 Agent Skill 調査レポート

- 作成日：2026-11-03
- 調査実施日：2026-10-31（インストール数・スター数・機能は調査時点の情報）
- 対象：SKILL.md 形式（Agent Skills 標準）で配布されているスキル

---

## 目次

1. [要約](#1-要約)
2. [Web リサーチ系スキルの全体比較](#2-web-リサーチ系スキルの全体比較)
3. [他サービスに依存しないリサーチスキル](#3-他サービスに依存しないリサーチスキル)
4. [用途別のおすすめスキル](#4-用途別のおすすめスキル)
5. [スキルで使われている方法論](#5-スキルで使われている方法論)
6. [スキルの調査に使えるスキル](#6-スキルの調査に使えるスキル)
7. [導入時の注意点](#7-導入時の注意点)
8. [参考資料](#8-参考資料)

---

## 1. 要約

- Web リサーチ系スキルは、大きく 3 種類に分けられる。
  - **外部 API 型**：Tavily、Exa、Firecrawl、Gemini、You.com などの外部サービスに検索・調査を任せる
  - **方法論型**：調査手順だけを記述し、エージェント標準の WebSearch / WebFetch で動く
  - **ライブラリ型**：GPT Researcher のように、Python ライブラリを呼び出して動く
- 他のサービスに依存しない条件では、**claude-deep-research-skill**（品質重視）、**claude-superskills の deep-research**（バランス型）、**deep-dive**（並列サブエージェント型）、**DeerFlow deep-research**（軽量・改造向き）が有力。
- 選択肢の列挙スキルと比較スキルは「考え方の枠組み」であり、自分では Web 検索をしない。リサーチ系スキルと組み合わせて使う。
  - 推奨の流れ：列挙 → 調査 → 比較 → 結論の頑健性確認
- すべての用途に共通する設計原則は次の 2 つ。
  - **作る工程と評価する工程を分けること**（発散と収束、下書きと批評、重み決めと採点）
  - **根拠の弱い部分を隠さないこと**
- スキルは「エージェントが従う指示」と「ユーザー権限で実行されるスクリプト」のセットである。導入前に監査すること。

---

## 2. Web リサーチ系スキルの全体比較

### 2.1 候補一覧

| # | スキル | 提供元 | 方式 | 必要なもの |
|---|---|---|---|---|
| ① | tavily-search / tavily-research ほか | tavily-ai/skills（公式） | 外部 API ＋ CLI | Tavily API キー |
| ② | exa-search ほか | exa-labs/agent-skills（公式） | 外部 API（意味検索） | Exa API キー（無料クレジットあり） |
| ③ | firecrawl | firecrawl/cli（公式） | 外部 API（スクレイピング中心） | Firecrawl API キー・クレジット |
| ④ | deep-research | sanjay3290/ai-skills | Gemini Deep Research Agent に委託 | GEMINI_API_KEY、Python 3.8 以上 |
| ⑤ | deep-research | 199-biotechnologies/claude-deep-research-skill | 方法論＋スクリプト（標準の WebSearch を使用） | 基本的な使い方では不要 |
| ⑥ | deep-research | bytedance/deer-flow | 方法論のみ | 不要 |
| ⑦ | Deep Research Skill | You.com | MCP 経由 | You.com MCP サーバー・キー |
| ⑧ | gpt-researcher | assafelovic/gpt-researcher | Python ライブラリ | LLM・検索 API のキー |

### 2.2 各候補の概要

- **① Tavily**
  - 検索（search）、本文抽出（extract）、クロール（crawl）、URL 探索（map）、リサーチ（research）を、別々のスキルとして提供する。
  - search はドメインの絞り込み、期間の指定、検索深度の切り替えに対応する。
  - research は引用付きの多ソース統合を 30〜120 秒で行う。
- **② Exa**
  - 意味検索（ニューラル検索）が中心。
  - 企業調査スキルや、リード一覧を CSV で出力するスキルなど、用途別のスキルがある。
- **③ Firecrawl**
  - scrape・search・crawl・map を CLI から使う。
  - クリックやログインが必要なページは、interact で操作して取得する。
- **④ Gemini Deep Research**
  - 計画から統合までを外部エージェントに丸投げする。
  - 1 件あたり 2〜10 分、費用は 1 タスク 2〜5 ドル程度。
- **⑤ claude-deep-research-skill**
  - 8 フェーズのパイプラインで調査する。
  - Quick / Standard / Deep / UltraDeep の 4 モードを持ち、情報源の信頼性スコアリングと引用検証を行う。
- **⑥ DeerFlow**
  - 多角的な調査を指示する方法論型のスキル。
  - 呼び出し条件が非常に広く、簡単な質問でも起動しやすい。
- **⑦ You.com**
  - 深いリサーチが必要かを判断し、you-research ツールに処理を渡す。
  - 単発の事実確認には使わないよう明記している。
- **⑧ GPT Researcher**
  - Web とローカル文書を横断して調査する自律型エージェント。
  - レポート形式と情報源（web / local / hybrid）を選べる。

### 2.3 比較表

| 候補 | 主なメリット | 主なデメリット | 向いているケース | 向いていないケース |
|---|---|---|---|---|
| ① Tavily | 公式で保守が安定。段階的に使い分けられる。research が速い | API キーと従量課金が必要 | 最新ニュース、技術調査、短時間の引用付きレポート | API を契約したくない、完全オフライン |
| ② Exa | 曖昧なキーワードでも関連ページを拾いやすい | 汎用の長文レポート生成は弱め | 類似サイト探し、論文・GitHub 探索、企業リスト作り | ニュース速報、日本のローカル情報が中心の調査 |
| ③ Firecrawl | JS で描画されるページやログインが必要なページも取れる | クレジット消費が速い。調査の段取りは自分で組む | ドキュメントサイトの一括取得、特定サイトの深掘り | 多数の情報源を広く浅くまとめる調査 |
| ④ Gemini | 丸投げでき、Claude のコンテキストを消費しにくい | 費用が高め。数分待つ。過程が見えにくい | 市場分析、競合調査、デューデリジェンス | 対話しながら進める調査、低予算 |
| ⑤ 199-bio | 外部 API 不要。品質担保の仕組みが充実 | 時間とトークンを多く使う | 意思決定のための網羅的レポート | 軽い質問 |
| ⑥ DeerFlow | 軽量で改造しやすい | 過剰に起動しやすい。検証機能がない | 自作スキルの土台、下調べ | 日常的な質問 |
| ⑦ You.com | 呼び出し条件の線引きが明確 | MCP 環境が必要 | MCP 環境でのブリーフィング作成 | MCP を使えない環境 |
| ⑧ GPT Researcher | Web とローカル文書の横断。設定が細かくできる | 環境構築が重い | 社内文書と Web の横断調査 | 手軽さ重視 |

---

## 3. 他サービスに依存しないリサーチスキル

条件：外部 API の契約やキーが不要で、エージェント標準の WebSearch / WebFetch だけで動くこと。

> 注：検索そのものはエージェント内蔵の WebSearch に依存する。WebSearch を持たないエージェント環境では動かない。

### 3.1 候補一覧

- **A. claude-deep-research-skill**（199-biotechnologies）
  - 基本的な使い方なら追加の依存関係は不要。スクリプトは Python 標準ライブラリのみで書かれている。
  - ネットワーク通信は、DOI・URL の引用検証に限られる。
  - 長いレポートは、状態ファイルを使って続きを書く仕組みがある。
- **B. claude-superskills の deep-research**（ericgandrade）
  - 外部 API 不要と明記されている。
  - 5 フェーズで進み、進捗ゲージを表示する。所要時間は 5〜20 分。
  - 根拠を先に示す、矛盾を隠さない、といった品質基準が明確。
  - 55 個のスキルをまとめたプラグインの一部として配布されている。
- **C. deep-dive**（rohitg00/awesome-claude-code-toolkit）
  - DAG（依存グラフ）によるクエリ計画、サブエージェントの並列実行、足りない情報の追加調査を繰り返す方式。
  - 外部依存なしで動く。
- **D. DeerFlow deep-research**（bytedance）
  - 手順だけを記述した方法論型。SKILL.md だけで完結する。
- **E. search**（htlin222/dotfiles）
  - 検索演算子（site:、filetype:）やドメイン絞り込みなど、検索クエリの質を上げることに特化した軽量スキル。
- **F. Anthropic のサンプル deep-research**
  - claude.ai 環境に最初から入っている。サブエージェントを指揮して報告書にまとめる。

除外したもの：openclaw の deep-research-pro は API キーこそ不要だが、裏で DuckDuckGo に依存するため外した。

### 3.2 比較表

| 候補 | 重さ | メリット | デメリット | 向いているケース | 向いていないケース |
|---|---|---|---|---|---|
| A | 重い | 品質が最も高い。深さを選べる。中断しても再開できる | 時間・トークンの消費が大きく、改造しにくい | 意思決定用の網羅的レポート | 日常的な調べもの |
| B | 中くらい | 品質基準が明確で、進捗も見える | 単体で入れるには取り出す手間がある | 規制動向のまとめ、比較メモ | すぐに答えが欲しい質問 |
| C | 中〜重 | 速く、広く調べられる。穴を自動で埋める | サブエージェント機能が前提。トークンが膨らみやすい | 論点が多い網羅的な調査 | サブエージェントのない環境 |
| D | 軽い | 読みやすく改造しやすい | 検証機能がない。過剰に起動しやすい | 自作スキルの土台 | 引用の正確さが重要な調査 |
| E | とても軽い | どんな環境でも使える | レポートを組み立てる手順がない | ファクトチェック、ピンポイント検索 | 多数のソースの統合 |
| F | 中くらい | 公式で、インストール不要 | 細かい調整ができない | この環境でまず試したいとき | Claude Code 以外の環境 |

### 3.3 選び方

- バランス重視なら **B**
- 品質重視なら **A**
- 自作の土台にするなら **D ＋ E**

---

## 4. 用途別のおすすめスキル

いずれも外部 API を前提としないもの。新しく利用実績の少ないスキルも含まれる。

### 4.1 技術調査

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| research-lib（del-taiseiozaki/claude-code-orchestra） | サブエージェントがライブラリの最新版、機能、制約、既知の問題を調べ、`.claude/docs/libraries/` に保存する | 導入前のライブラリ調査、調査結果をプロジェクトに残したいとき | サブエージェント機能が前提 |
| search（htlin222） | 検索テクニックに特化。技術的な主張の裏取りにも使える | API 仕様の確認、真偽チェック | レポート機能はない |
| claude-deep-research-skill | 網羅的な技術選定レポートを作る | 技術選定の根拠資料 | 重い |

除外したもの：Linus Torvalds 風の技術調査スキル（Exa に依存するため）。

### 4.2 マーケティング調査

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| market-research（affaan-m/everything-claude-code） | 市場規模、競合比較、デューデリジェンスを出典付きでまとめ、意思決定向けに要約する | 参入判断、TAM/SAM/SOM の推定、競合比較 | 価格・流通・ポジショニングまで比べるよう指示すると効果が高い |
| market-researcher（nickcrew/claude-ctx-plugin） | TAM/SAM/SOM、一次・二次調査の設計、セグメンテーション、アンケート作成 | 調査計画やアンケートの設計 | 方法論ガイドとしての色合いが強い |
| market-intelligence（travcjohnson） | 資料集を作る market-corpus と、そこに分析をかける market-lens の 2 段構成 | 同じ市場を何度も違う切り口で分析したいとき | 1 回きりの調査には手間がかかる |

### 4.3 選択肢の列挙

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| brainstorm-diverge-converge（lyndonkl/claude） | 発散してから収束する構造化ブレインストーミング | 可能性を広く洗い出したいとき | ― |
| nw-brainstorming（nWave） | SCAMPER と Crazy 8s で案を出し、似た案は統合する | 似た案ばかりになるのを避けたいとき | ― |
| brainstorming（obra/superpowers） | 質問を重ね、代替案を探りながら設計を少しずつ固める | 開発での実装方針の検討 | 開発ワークフロー寄り |

除外したもの：johnlindquist の brainstorm（Gemini API キーが必要なため）。

### 4.4 選択肢の比較

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| decision-matrix（lyndonkl/claude） | 重み付き基準での比較、感度分析、ルーブリックによる自己評価（合格基準 3.5 以上） | 説明責任のある技術・ツール選定 | ― |
| options-comparator（travisjneuman/.claude） | 重み付きスコア表、一対比較、MoSCoW 法、採点前の重み固定 | 重み付けそのものに納得感が欲しいとき | ― |
| think-decision-option-review（product-on-purpose） | 見せかけの精度を警戒し、何が変われば推奨が覆るかを明示する | 僅差の比較 | 公開されたばかりで実績が少ない |
| decision-helper（jmsktm/claude-settings） | 意思決定フレームワーク、バイアスの除去、可逆性の記録 | 製品・採用・戦略など技術以外の判断 | ― |

### 4.5 組み合わせ方

列挙と比較のスキルは、自分では Web 検索をしない。次のようにつなげて使う。

1. **列挙**：brainstorm-diverge-converge で候補を広く出す
2. **調査**：research-lib や market-research で、各候補の事実を集める
3. **比較**：decision-matrix で重み付けして比べる（1 と同じ作者なので形式が揃う）
4. **仕上げ**：僅差なら think-decision-option-review で、何が変われば結論が覆るかを確認する

---

## 5. スキルで使われている方法論

### 5.1 調査プロセス

| 方法論 | 概要 | 使用スキル |
|---|---|---|
| フェーズ分割型パイプライン | 範囲決め → 計画 → 収集 → 検証 → 統合 → 批評 → 改善 → 納品のように段階を分け、段階ごとに完了条件を設ける。手抜きを防ぎ、中断後の再開もしやすい | A（8 段階）、B（5 段階） |
| トライアンギュレーション（三角検証） | 1 つの主張を、互いに独立した複数の情報源で確かめる。社会科学の調査法に由来する | A |
| 情報源の信頼性スコアリング | 権威性、新しさ、一次情報かどうか、利害関係で情報源を評価する（CRAAP テストと同系統） | A |
| DAG によるクエリ計画 | 小さな問いの依存関係をグラフで表す。依存のない問いは並列に調べる | C |
| ギャップ駆動の反復 | まだ答えられていない点を洗い出し、そこだけを追加で調べる。穴がなくなるまで繰り返す | C |
| 多角的な分解と言い換え検索 | 観点ごとに言い回しを変えて検索し、1 回の結果に引きずられないようにする | D |
| 検索演算子の活用 | site:、filetype:、期間指定などで検索範囲を絞り込む | E |
| エビデンスファーストと自己批評 | 根拠を先に集め、矛盾は隠さない。下書きを反論する立場で読み直す | A、B |

### 5.2 マーケティング調査

| 方法論 | 概要 | 使用スキル |
|---|---|---|
| TAM / SAM / SOM | 市場全体（TAM）、狙える範囲（SAM）、現実的に獲得できる分（SOM）の 3 段階で市場規模を見積もる | market-research、market-researcher |
| 一次調査と二次調査 | 自分で集めるデータ（アンケート、インタビュー）と、既存の資料を使い分ける | market-researcher |
| 顧客セグメンテーション | 属性、行動、ニーズで顧客をグループに分け、狙う層を決める | market-researcher |
| 競合ポジショニング分析 | 機能だけでなく、価格・流通・訴求点・実際の使われ方を比べて、空いている位置を探す | market-research |
| ICP / GTM | 理想の顧客像（ICP）と、誰に・何を・どの経路で・いくらで売るかという市場投入戦略（GTM） | market-intelligence |
| 資料集と分析の分離 | 出典付きの資料集を作り、その上に切り口ごとの分析を繰り返しかける。再現性が高い | market-intelligence |

### 5.3 選択肢の列挙

| 方法論 | 概要 | 使用スキル |
|---|---|---|
| 発散と収束 | 数を出す段階と絞る段階をはっきり分ける。ギルフォードの発散的・収束的思考に由来し、ダブルダイヤモンドの基礎でもある | brainstorm-diverge-converge、nw-brainstorming |
| クラスタリング（アフィニティ法） | 似たアイデアをまとめてテーマ別に整理する（KJ 法と同じ発想） | brainstorm-diverge-converge |
| HMW（How Might We） | 課題を「どうすれば〜できるか？」という問いに言い換え、発想しやすい範囲に整える | nw-brainstorming |
| SCAMPER | 置き換える、組み合わせる、応用する、変える、他の用途に使う、取り除く、逆にする・並べ替える、の 7 つの問いで案を作る | nw-brainstorming |
| Crazy 8s | 8 分間で 8 案を出す。時間の圧力で、頭の中での評価を抑える | nw-brainstorming |
| 構造的に異なる案の判定 | 前提・ユーザー行動・コスト構造がすべて同じなら、別案ではなくバリエーションとして統合する | nw-brainstorming |
| 対話による段階的な具体化 | 質問で要件を明らかにし、代替案を示し、設計を少しずつ確認しながら固める | superpowers brainstorming |

### 5.4 選択肢の比較

| 方法論 | 概要 | 使用スキル |
|---|---|---|
| 重み付きスコアリング（多基準意思決定分析） | 「点数 × 重み」の合計で順位を付ける（ピュー・マトリクスと同系統） | decision-matrix、options-comparator、decision-helper |
| 一対比較 | 基準を 2 つずつ比べ、勝った回数から重みを決める。比較回数は n(n−1)/2。AHP を簡単にしたもの | options-comparator |
| MoSCoW 法 | Must / Should / Could / Won't に分け、Must を満たさない案を先に除外する | options-comparator |
| 強制順位付け | 同順位を認めず、必ず順番を付ける | options-comparator |
| 重みの事前固定 | 採点前に重みを決めて固定し、結論からの逆算を防ぐ | options-comparator |
| 感度分析 | 重みや点数を少し変えて、順位が入れ替わるかを確かめる | decision-matrix |
| 覆る条件の明示と偽の精度への警戒 | 根拠の弱い点数に印を付け、何が変われば推奨が覆るかを示す | think-decision-option-review |
| 可逆性の評価 | 取り消せる決定か、取り消せない決定かを記録する（一方通行のドアと双方向のドア） | decision-helper、options-comparator |
| 前提の検証とバイアス除去 | 成功に必要な前提を書き出して確かめ、思い込みを点検する | decision-helper |
| ルーブリックによる自己評価 | あらかじめ決めた採点基準で成果物を自己採点し、基準に届かなければ作り直す | decision-matrix |

### 5.5 用途別の要点

| 用途 | 中心となる方法論 |
|---|---|
| 技術調査 | フェーズ分割、三角検証、ギャップ駆動の反復 |
| マーケティング調査 | TAM/SAM/SOM、セグメンテーション、ポジショニング分析 |
| 選択肢の列挙 | 発散と収束、SCAMPER、HMW |
| 比較 | 重み付きスコアリング、感度分析、覆る条件の明示 |

---

## 6. スキルの調査に使えるスキル

### 6.1 探す（発見）

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| find-skills（vercel-labs/skills） | Skills CLI で検索とインストールを行う。推薦前にインストール数（1,000 以上が目安）、提供元、スター数を確認する | スキル名は分からないが、やりたいことは決まっているとき | skills.sh 中心。人気指標に偏りがち |
| skill-finder（aktsmm/agent-skills） | ローカル索引、GitHub API、Web 検索の順に探す。タグで絞り込み、お気に入り管理ができる。スキル化が最適かどうかも判断する | スキルを継続的に集めて管理したいとき | Python が前提 |
| agent-skill-discovery（ericgandrade/cli-ai-skills） | インストール済みのものとリポジトリ内のものを棚卸しする | 手元にあるスキルの把握、重複の整理 | 外部のスキルは探せない |

### 6.2 評価・比較する

| スキル | 概要 | 向いているケース | 注意 |
|---|---|---|---|
| skills-curator-lite | 信頼度付きのカタログを持ち、プロジェクトを解析して合うスキルを長所・短所付きの順位表で返す。困りごとからの逆引きもできる | プロジェクトに合うスキルを比較して選びたいとき | カタログに偏りがある可能性 |
| skill-creator（Anthropic 公式） | 評価（eval）の実行や、ばらつきを含めた性能のベンチマークができる | 候補を同じ課題で試して比べたいとき、自作スキルの品質を測りたいとき | ― |

### 6.3 安全性を確かめる（導入前の監査）

| スキル | 概要 | 注意 |
|---|---|---|
| skill-security-review（dkleptsov） | 依存なしの Node 製スキャナで怪しい箇所を特定し、エージェントが手で読んで判定する。対象を実行せず、対象の指示にも従わない | 最も安全側に寄せた設計 |
| skill-auditor（ki-stuff） | プロンプトインジェクション、データ持ち出し、権限昇格を検査する。自動スキャンのあとに手作業の確認段階がある | スキャンで何も出なくても、安全の保証ではない |
| skill-auditor（Plastikelectrik） | スキルと MCP 設定を、ファイル名と行番号の証拠付きで判定する | ― |
| skill-security-auditor（alirezarezvani） | PASS / WARN / FAIL で判定し、CI に組み込める | このスキル自体がスキャナ 3 つのうち 1 つしか通過していない |

### 6.4 推奨の流れ

1. **探す**：find-skills で候補を出す。プロジェクトに合わせた比較が必要なら skills-curator-lite を使う
2. **監査する**：skill-security-review などで、インストール前に静的にチェックする
3. **試す**：skill-creator の評価機能で、候補を同じ課題で比べる

---

## 7. 導入時の注意点

- **スキルは依存パッケージと同じように扱う**
  - SKILL.md はエージェントのコンテキストに注入される。プロンプトインジェクションの入り口になりうる。
  - 同梱のスクリプトは、ユーザーの権限で実行される。
- **監査の基本**
  - リポジトリはブランチではなく、特定のリビジョンに固定する。
  - SKILL.md だけでなく、参照されているファイル、スクリプト、依存パッケージまで確認する。
  - 機密情報を置いていない使い捨て環境で試す。
  - 自動スキャナの結果だけで判断しない。
- **インストール数とスター数は参考程度にとどめる**
  - 紹介サイトによって集計日が異なる。
  - フォークや複製が多く、同名のスキルが複数存在する。
- **呼び出し条件（description）に注意する**
  - 範囲が広すぎるスキル（例：DeerFlow）は、簡単な質問でも重い処理を始めてしまう。

---

## 8. 参考資料

### Web リサーチ系（外部 API 型）

- Tavily Agent Skills：https://docs.tavily.com/documentation/agent-skills
- tavily-ai/skills README：https://awesome.ecosyste.ms/projects/github.com%2Ftavily-ai%2Fskills
- Exa Agent Skills：https://exa.ai/docs/reference/agent-skills
- Introducing Firecrawl Skill and CLI：https://www.firecrawl.dev/blog/introducing-firecrawl-skill-and-cli
- Firecrawl AGENTS.md：https://firecrawl.dev/AGENTS.md
- sanjay3290 deep-research：https://skills.sh/sanjay3290/ai-skills/deep-research
- You.com Deep Research Skill：https://you.com/docs/examples/deep-research
- gpt-researcher skill：https://smithery.ai/skills/assafelovic/gpt-researcher

### 外部依存のないリサーチスキル

- claude-deep-research-skill：https://agskills.dev/199-biotechnologies/claude-deep-research-skill/deep-research
- claude-deep-research-skill（SourcePulse）：https://www.sourcepulse.org/projects/26894272
- ericgandrade deep-research：https://skills.sh/ericgandrade/claude-superskills/deep-research
- deep-dive：https://skillsmp.com/skills/rohitg00-awesome-claude-code-toolkit-skills-deep-dive-skill-md
- DeerFlow deep-research：https://skills.browseract.com/skills/bytedance-deer-flow-deep-research
- htlin222 search：https://agent-skills.md/skills/htlin222/dotfiles/search

### 用途別スキル

- research-lib：https://skills.sh/del-taiseiozaki/claude-code-orchestra/research-lib
- affaan-m market-research：https://skillselion.com/skills/affaan-m/everything-claude-code/market-research
- nickcrew market-researcher：https://skillselion.com/skills/nickcrew/claude-ctx-plugin/market-researcher
- market-intelligence-skills：https://skillselion.com/skills/travcjohnson/market-intelligence-skills/plugins/market-intelligence
- brainstorm-diverge-converge：https://www.aimcp.info/CLAUDE.md/skills/a009a542-1c95-403b-9f27-1b1d5c6a944d
- nw-brainstorming：https://openskillindex.com/skills/nwave-ai-nwave-nw-brainstorming
- decision-matrix：https://skillselion.com/skills/lyndonkl/claude/decision-matrix
- options-comparator：https://llmbase.ai/de/skills/travisjneuman/options-comparator/
- think-decision-option-review：https://www.skills.sh/product-on-purpose/thinking-framework-skills/think-decision-option-review
- decision-helper：https://skillselion.com/skills/jmsktm/claude-settings/decision-helper

### スキル調査・監査

- find-skills：https://llmbase.ai/skills/vercel-labs/find-skills/
- aktsmm skill-finder：https://skillselion.com/skills/aktsmm/agent-skills/skill-finder
- agent-skill-discovery：https://www.skills.sh/ericgandrade/cli-ai-skills/agent-skill-discovery
- skills-curator-lite：https://claudskills.com/skills/skills-curator-lite/SKILL.md
- skill-security-review：https://github.com/anthropics/skills/discussions/1411
- ki-stuff/skill-auditor：https://github.com/ki-stuff/skill-auditor
- Plastikelectrik skill-auditor：https://dev.to/plastikelectrik/your-ai-agent-obeys-any-skill-you-install-i-built-an-auditor-to-check-them-first-4a2o
- skill-security-auditor：https://skillselion.com/skills/alirezarezvani/claude-skills/skill-security-auditor
- How to Audit an Agent Skill Before You Install It：https://aident.ai/blog/audit-agent-skill-before-installing
