あなたは総括の書き手です。
同じタスクに 4 体のエージェントが独立して取り組み、その後、各エージェントが自分以外の成果を敵対的にレビューし、欠陥、反例、崩れる前提を挙げました。
成果とレビューを読み、作者（このリポジトリの所有者）が判断できる総括を 1 本書いてください。
あなたの最終メッセージだけが `summary.md` として保存されます。
エージェントは記号で呼びます（エージェント A、エージェント B、エージェント C、エージェント D）。記号とモデルの対応は末尾に表として付けるので、本文ではモデル名で優劣を語らないでください。

## タスク

# タスク：wiki の記事作成の方法論の提案を、info-hive に導入すべきか検討する

## 作者の指示

> 以下は Codex と Claude に wiki の記事を作成する際に提案した方法である。
> これらを導入すべきか multi-agent-dispatch で検討してください

「以下」は、本書の末尾の「検討対象の提案」に原文のまま写した文書である。作者が Codex と Claude に相談して得た 2 つの回答（ChatGPT の KM 理論の整理と、Claude の LLM 運用の整理）を、作者がまとめたものである。文書の中の画像の 1 か所（「導入フェーズ · 4 段階と 3 つの移行条件」）は貼り付けで失われている。

## 決めたいこと

1. 提案を構成する要素のそれぞれについて、info-hive の wiki プラグイン（`info-hive-wiki`）に**導入するか、変えて導入するか、導入しないか**。
2. 導入するものの**順序と条件**（いつ、何が起きたら入れるか）と、プラグインのバージョン（SemVer）への影響。
3. 提案と、現行のプラグイン、承認済みの ADR、直前の検討（記事の単位）との**衝突**と、その解き方。

提案は info-hive の現状を知らずに書かれている。提案のコマンド名（`/wiki:ingest`、`/wiki:query`、`/wiki:lint`、`/wiki:graph`）は現行のコマンドと名前が同じだが、中身が同じとは限らない。名前が同じことを、導入済みの根拠にしないこと。

## 現状として分かっていること

### wiki プラグイン（`info-hive-wiki`、プラグイン名 `wiki`、スキル名 `info-hive`）

- LLM が保守する Markdown の wiki。移植元は praneybehl/llm-wiki-plugin v4.0.1 で、Karpathy の「LLM Wiki」の gist にもとづく。3 層は raw（変更不可の原本）、wiki（LLM が書くページ）、`SCHEMA.md`（wiki ごとの規約。スキルの記述より優先）。任意で `graph/`（型付きエッジの派生データ）。
- 現行のコマンド: `init`、`ingest`、`query`、`lint`、`graph`、`learn`、`evolve`、`stats`、`upgrade`、`help`。`plan`、`decide`、`promote` はない。
- ページの `type` は `source`、`entity`、`concept`、`synthesis`。`learn` は `concept` に `kind: "experience-pattern"`、`status: hypothesis|supported|superseded` のページを作る。それ以外のページに `status` はない。`id` キーはなく、ファイル名（スラッグ）がページの識別子である。
- frontmatter のキー、`type`・`kind` の値、述語名は英語、本文は日本語（方針 B）。frontmatter は平坦なキーが前提で、`wiki_text.py` のパーサーは入れ子を読まない（直前の検討で 3 体が確認）。
- グラフ層: 本文の `[[wikilink]]` から `mentions`、`sources:` から `sourced_from` のエッジが自動でできる。型付きの述語（`depends_on`、`contradicts`、`supersedes` など）は `graph/ontology.yaml` で宣言し、`evidence`（原文の引用）、`confidence`、`status` が必須。
- 取り込み（`ingest-workflow.md`）: raw を置く → 読む → 要点をユーザーと話す → 関係するページを洗い出す → source の要約ページ → 既存ページを `str_replace` で部分更新 → 新しいページ（被リンク必須）→ インデックス → グラフ → `log.md` → 報告。矛盾は `## 矛盾` に並記し、上書きしない。
- query は回答を `synthesis/` に保存することを提案する。lint は孤立、リンク切れ、大きすぎるページ、frontmatter の誤り、古い日付、グラフの矛盾を検出する。`--suggest-pages` で専用ページのない語を挙げる。

### 承認済みの決定

- ADR-0006: 日々の記録（日付ノート、タスク）は wiki と別のプラグイン `log`（未実装）にする。wiki の lint は日付ノートを孤立として毎日報告してしまうため。
- ADR-0008: 作業領域は `~/info-hive/` の下の番号付きディレクトリ。作業領域の根を VS Code と Foam で開き、`.foam/templates/` を根に置く。ユーザースコープとプロジェクトの作業領域を分け、ユーザースコープにはプロジェクト固有の情報を置かない。
- ADR-0009: グラフ層とオントロジーは wiki プラグインの中の任意の索引であり、横断的な基盤にはしない。
- 処理はローカルで完結する。PC 固有の値は仕様に書かない。

### 直前の検討（記事の単位、2026-11-08）

`docs/research/wiki-note-granularity-2026-11-08.md`（このリポジトリ。未コミット）と `docs/agent-runs/2026-11-08-wiki-note-granularity-atomic-evergreen/summary.md` に結論がある。要点は次のとおり。

- Atomic Notes と Evergreen Notes は変えて採る。全面的な 1 主張 1 ページは採らない。用語とエンティティのページを残し、再利用できる知見だけを `type: "concept"`、`kind: "claim"` のページに昇格させる。主張の既定の置き場所は用語ページの中の `###` の節。
- 単位は「1 文」ではなく「条件、根拠、適用範囲を同じ場所で更新できる 1 つの判断」。
- 「ソース固有か、再利用できるか」の判断は機械化できておらず、PoC で振り分けの一致を測ってから既定にする。
- 作者の wiki は source 37、concept 17、entity 1、synthesis 2。SemaSynth の作業記録が source に溜まり、concept に育っていない。

提案の区分 2（構造化）はこの検討と重なる。直前の結論を前提にしてよいが、提案のほうが優れている点があれば、そう書いてよい。

### 作者の wiki

`D:\Users\toshiki\info-hive\W0_Wiki\`（このリポジトリの外。読んでよいが書き換えない）。`SCHEMA.md`、`index.md`、`log.md`、`concepts/`、`sources/`、`synthesis/` を見れば、提案の各要素が今の wiki で何を変えるかを具体的に確かめられる。

## 検討の観点（少なくとも次を扱う）

- **分解**: 提案を、独立に採否を決められる要素に分ける。少なくとも次を含める。5 区分の方法論マップ、きっかけ別のコマンド分け、成熟度フェーズと移行条件、`type` と `status` でモードを分けて lint が検査する設計、frontmatter の各フィールド（`id`、`scope`、`status`、`relations` の `broader`・`related`・`answers`、`reviewed_at`）、`type` の追加（`howto`、`decision`、`moc`、`journal`、`graph`）、`questions.md` と Competency Questions、`/wiki:plan`、`/wiki:decide`、`/wiki:promote`、`/wiki:lint --fix` と `--relations`、共通ルール 8 項目、`/wiki:ingest` の手順（特に source ページの「主張の一覧」）、Diátaxis の「手順と概念を混ぜない」、Middle-out の分類、KCS と出典必須の両立。
- **現行との差分**: 各要素が、現行のプラグインで既にあるか、一部あるか、ないか。あるなら何が違うか。
- **衝突**: ADR-0006（`journal` を wiki に入れる案）、ADR-0008、ADR-0009（SKOS 風 `relations` と既存の型付きエッジ・オントロジーの二重化）、方針 B、平坦な frontmatter、ファイル名と `id` を一致させて改名しない規則と日本語のスラッグ、`status` と既存の `experience-pattern` の `status` の値の衝突、直前の検討の `kind: "claim"`。
- **LLM が保守する前提**: 人が運用する KM の手法（Competency Questions、KCS、正典化のレビュー）を、取り込みのたびに LLM が書く wiki に入れたときに、作者の手間が増えるか減るか。誰が `reviewed` を判断するのか。
- **再現性と検査可能性**: 各要素のうち、lint で機械的に検査できるものと、LLM の判断に頼るもの。
- **提案自体の誤りや不整合**: 文書の中の食い違い（コマンドの数、名前の表記、`type` の綴り、スキーマの置き場所など）があれば指摘する。採否の判断には影響させず、別の節に分ける。

## 評価の基準

要素ごとに次の基準で 1〜10 点で採点し、合計（各点数 × 重みの和 ÷ 100）で並べる。点数の根拠を短く添え、重みを 2 通り変えて結論が変わるかも確かめる。基準への異議は成果に書いてよい。ただし、点数だけで採否を決めず、導入の条件（何が起きたら入れるか）を必ず添える。

| 基準 | 重み | 高く評価する条件 |
| --- | --- | --- |
| 利用者が得る価値 | 25 | 現行のコマンドと規約では得られない結果が出る。作者の wiki の実際の問題（source に溜まる偏り、索引の分類の誤りなど）を解く |
| 既存設計との整合 | 20 | Markdown が正本、ローカル完結、方針 B、平坦な frontmatter、ADR-0006・0008・0009、直前の検討と矛盾しない |
| 検査可能性 | 20 | lint やスクリプトで機械的に検査できる。LLM の判断に頼る部分が小さい、または PoC で測れる |
| 運用の手間 | 20 | 作者が毎回判断・記入する量を増やさない。増やすなら見返りが明確 |
| 実装と移行の軽さ | 15 | SCHEMA.md と references の改訂で回るか、スクリプトの変更が小さい。既存の 56 ページを壊さない |

## 読むべき文書とコード

プラグインの本体はサブモジュール `info-hive-wiki/` だが、作業ディレクトリによっては空なので、`C:\Works\info-hive-dev\info-hive-wiki\` を読む。

- `AGENTS.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`architecture.md`、`lint-workflow.md`、`query-workflow.md`、`graph-workflow.md`、`evolution-workflow.md`、`scaling-playbook.md`
- `info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template`、`ontology.yaml.template`、`page.md.template`
- `info-hive-wiki/commands/*.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`、`wiki_text.py`、`wiki_graph_extract.py`
- `docs/adr/0006-daily-journal-is-separate-plugin.md`、`0008-numbered-workspace-layout.md`、`0009-graph-layer-stays-in-wiki.md`
- `docs/research/wiki-note-granularity-2026-11-08.md`
- 作者の wiki: `D:\Users\toshiki\info-hive\W0_Wiki\` の `SCHEMA.md`、`index.md`、`log.md` と、ページのいくつか

## 成果に含めるもの

成果は 1 本の Markdown で、次の順に書く。

1. **結論の要約**: 導入する、変えて導入する、導入しない、保留の 4 区分で、要素を一覧にする。最初に入れる 3 つ以内と、その理由を 5 行以内で。
2. **要素の分解と現行との差分**: 要素ごとに、提案の内容、現行の対応（ある / 一部 / ない）、差分を表にする。
3. **採点**: 上の基準での採点表と、重みを変えたときの結果。
4. **衝突と解き方**: ADR、方針 B、直前の検討との衝突ごとに、提案側を変えるか、既存を変えるか、導入しないかを書く。既存の ADR を変えるべきと判断したら、その ADR と変える箇所を明記する。
5. **導入する要素の詳細**: frontmatter のキーと値（英語。方針 B）、`SCHEMA.md` と references の改訂の要点、コマンドを足すならその入出力、lint で検査する項目。作者の wiki の実在のページ 2〜3 本で、導入後の frontmatter がどうなるかの例を示す（ファイルは書かない）。
6. **導入の順序と条件**: 段階ごとに、入れるもの、入れる合図（何が起きたら）、SemVer（パッチ、マイナー、メジャー）、既存の wiki の移行。
7. **提案自体の誤りや不整合**。
8. **確認できなかったこと**と、基準や重みへの異議。

リポジトリのファイルと作者の wiki は書き換えないこと。成果は日本語で書き、コマンド名、frontmatter のキー、`type` の値、述語名、ファイル名は英語の原文のまま書く。

---

## 検討対象の提案（作者が貼り付けたもの。原文のまま）

````markdown
# LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計

Nov 8, 2026 · @Toshiki Hayashi

## 目的と前提

LLM Wiki の記事を「思いついた順」ではなく、きっかけと成熟度に応じた決まった手順で生成・維持するための設計をまとめる。手法の網羅ではなく、**どの状況でどれを使い、どれを使わないか**の判断基準と、それを Claude Code の Skill に落とし込む設計が主題である。

想定環境は次のとおり。

| 項目 | 内容 |
| --- | --- |
| エージェント | Claude Code（Skill / スラッシュコマンドとして手順を定義） |
| 編集環境 | VS Code + Foam（YAML フロントマター、Wiki リンク、バックリンク） |
| 管理 | Git リポジトリ。LLM Wiki・日々のタスク・アイデア・個別プロジェクト知識を同居させる |
| 最終目標 | フロントマターからナレッジグラフを生成し、一覧・探索できるようにする |

参照した 2 つの整理は視点が異なる。ChatGPT の回答は KM 理論の網羅（Taxonomy、SKOS、Competency Questions、KCS、DITA）で「何を書くべきか」の設計に強く、Claude の回答は LLM 運用の実務（ingest → query → lint、暫定 → 正典の昇格、日誌統合）で「LLM にどう書かせ・保たせるか」に強い。本書は前者の 5 区分を骨格に、後者の運用手順を組み込む。

## 方法論マップ（5 区分）

記事作成は別々の 5 つの問題から成る。一つの手法で全部を解くのではなく、区分ごとに選んで組み合わせる。

| 区分 | 問い | 主な手法 | 先に採用 | 後回し |
| --- | --- | --- | --- | --- |
| 1. 発見 | 何について書くか | Source-driven ingest、Query-driven、Competency Questions、Gap Analysis、Task-driven | ingest、Query-driven | Competency Questions（領域が見えてから） |
| 2. 構造化 | どの単位に分けるか | Zettelkasten / Atomic Notes、Evergreen Notes、ページタイプ（source / concept / entity / decision） | Atomic Notes + ページタイプ | DITA |
| 3. 体系化 | どう分類・関連付けるか | MOC、Taxonomy、Middle-out、SKOS 風リレーション、Knowledge Graph | MOC（index.md）、SKOS 風 relations | Taxonomy の事前設計、OWL / 完全なオントロジー |
| 4. 執筆 | どう書くか | Diátaxis、ADR、テンプレート、Progressive Summarization、出典必須 | テンプレート + 出典必須、ADR | Diátaxis 4 種の完全適用 |
| 5. 維持 | 重複・矛盾・陳腐化をどう防ぐか | lint、Single Source of Truth、Lifecycle status、暫定 → 正典昇格、KCS、Docs as Code、日誌 → 定期統合 | lint、status、Docs as Code | KCS（利用が増えてから） |

区分 1、3 が「何が足りないか」を決め、区分 2、4 が「どう書くか」を決め、区分 5 が書いた後を支える。Skill 設計では、区分 1 の「きっかけ」ごとにコマンドを分け、区分 2〜4 を共通のスキーマ・テンプレートで固定し、区分 5 を lint に集約する。

## 状況別の使い分け

記事が生まれる「きっかけ」が手法を決める。きっかけごとに Skill のコマンドを対応させれば、手法の切り替えを意識しなくてよくなる。

| きっかけ・状況 | 使う手法 | 使わない / 後回し | 対応コマンド |
| --- | --- | --- | --- |
| 未知の領域を学び始めた（何があるか分からない） | ボトムアップ。Source-driven ingest → Atomic Notes。ソースを入れると概念ページが生える | Taxonomy の事前設計、Competency Questions（問いがまだ立てられない） | `/wiki:ingest` |
| 既知の領域を網羅的に整備したい | Competency Questions で問いを列挙 → MOC に赤リンク → Gap Analysis で埋める | 日誌駆動（遅すぎる） | `/wiki:plan` |
| 外部ソースを継続的に取り込む（論文・記事・仕様書） | ingest + 出典必須 + 暫定 → 正典の昇格。raw/ は不変 | 正典ページへの直接書き込み | `/wiki:ingest` → `/wiki:promote` |
| 質問に答えた・調べ物をした | Query-driven / KCS。回答を draft 記事に。答えられなかった問いを記録（Retrieval-driven improvement） | — | `/wiki:query` |
| 個別プロジェクトの知識 | ADR + Task-driven + Continuous Documentation。`scope: project` で共通 Wiki と分離 | Diátaxis 4 種の強制 | `/wiki:decide`、`/wiki:ingest` |
| 手順・操作が主の技術知識 | Diátaxis（How-to と Reference を分離） | 概念中心の領域では type を explanation 一択でよい | `/wiki:query --type howto` |
| 定期メンテナンス | lint（孤立・矛盾・陳腐化・出典欠落）→ バックログ化。SSOT で重複統合 | — | `/wiki:lint` |
| ナレッジグラフ化の準備 | フロントマターに SKOS 風 `relations`（broader / related）と `type`。Middle-out で中核概念から整える | OWL / 完全なオントロジー | `/wiki:lint --relations`、`/wiki:graph` |

## 成熟度フェーズ別の重心

[embedded content: 導入フェーズ · 4 段階と 3 つの移行条件]

立ち上げ期はボトムアップと出典だけで回し、分類や問いの設計は記事が増えて困り始めてから入れる。正典化とグラフ化はさらに後で、それぞれ「参照される記事が出た」「relations が埋まった」を合図にする。

## 手法間の衝突点と解決策

複数の手法を組み合わせると 4 つの衝突が起きる。いずれも「どちらかを選ぶ」のではなく、状態やタイミングで分ければ両立する。

| 衝突 | 何がぶつかるか | 解決策 |
| --- | --- | --- |
| トップダウン分類 vs ボトムアップ | 先に Taxonomy を作ると実態とずれる。作らないと記事が散らばる | Middle-out。ingest はボトムアップで行い、lint 時に LLM が現状の記事から分類を再提案する。Taxonomy は「設計する」ではなく「発見して承認する」 |
| Atomic Notes vs エンティティページ | Karpathy 式は 1 ソースが 10〜15 ページに触れる。ソース要約と概念ページが混ざると粒度が崩れる | `type` で分離する。`source` は 1 ソース 1 ページ、`concept` / `entity` は 1 概念 1 ページ。ソースページから概念ページへリンクする方向を固定 |
| Diátaxis の過剰適用 | 個人 Wiki は Explanation が大半。Tutorial / Reference を揃えようとすると空ページが増える | 4 種を揃えることを目的にしない。採用するルールは「手順と概念を同じページに混ぜない」の 1 つだけ。`type: howto` は必要になったときに作る |
| KCS vs 出典必須 | KCS は「使いながら素早く書く」、Provenance は「根拠を揃える」。両方を毎回要求すると書かなくなる | `status` で分ける。`draft` は出典なしで入れてよい。`reviewed` への昇格時に出典を要求し、無ければ lint が指摘する |

共通する解決の形は「フロントマターの 1 フィールド（`type`、`status`）でモードを分け、lint がそのモードごとのルールを検査する」である。手法の選択を人間が毎回判断するのではなく、メタデータに埋め込む。

## 記事スキーマ

すべての記事が同じフロントマターを持ち、`type` と `status` で適用ルールが切り替わる。SKOS の RDF 表現ではなく、その考え方を借りた軽量な Markdown メタデータである。Foam の YAML フロントマターと Wiki リンクをそのまま使う。

```markdown
---
id: relational-primary-key
title: 主キー
type: concept          # source | concept | entity | graph | syntesis | howto | decision | moc | journal
scope: common          # common | project:<name>
status: draft          # draft | reviewed | canonical | deprecated
relations:
  broader: [database-constraints]
  related: [foreign-key, unique-constraint]
  answers: [cq-rdb-003]   # 対応する Competency Question
sources: [src-postgres-docs-constraints]
created: 2026-11-08
reviewed_at: 2026-11-08
---
```

| フィールド | 由来する手法 | lint が検査すること |
| --- | --- | --- |
| `type` | ページタイプ、Diátaxis、ADR | タイプごとの必須セクションがあるか。howto に概念説明が混ざっていないか |
| `scope` | 共通 Wiki / プロジェクト Wiki の分離 | project スコープから common への昇格候補がないか |
| `status` | Knowledge Lifecycle、暫定 → 正典 | reviewed 以上に `sources` があるか。draft が長期放置されていないか |
| `relations` | SKOS、Knowledge Graph | リンク先が存在するか。broader の循環がないか。孤立ページがないか |
| `answers` | Competency Questions | 未回答の CQ が残っていないか（Gap Analysis） |
| `sources` | Knowledge Provenance | raw/ に実体があるか |

ディレクトリは Karpathy 式の 3 層（raw / wiki / schema）を基本に、日誌とプロジェクトを足す。

## Skill 設計

1 つの Skill（`wiki`）に 8 コマンドを持たせ、「きっかけ」ごとに入口を分ける。共通ルール（スキーマ、テンプレート、リンク規約）は SKILL.md 本文に置き、コマンド固有の手順は `commands/<name>.md` に分ける。SKILL.md 本文は日本語で書く。

### コマンド一覧

| コマンド | きっかけ | 主な手法 | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| `/wiki:ingest <pathっurl>` | ソースを入手した | Source-driven Synthesis、Provenance | raw/ のファイルまたは URL | source ページ 1 件、concept / entity ページの新規・更新（draft）、index / log 追記 |
| `/wiki:plan <topic>` | 領域を網羅したい | Competency Questions、MOC、Gap Analysis | 領域名、任意で既存資料 | questions.md に CQ 追記、moc/\<topic>.md（赤リンク付き）、未作成記事の一覧 |
| `/wiki:query <question>` | 質問に答えたい | Query-driven、KCS | 自然言語の問い | 回答（チャット）、draft 記事、答えられなかった場合は questions.md に未回答 CQ として追記 |
| `/wiki:decide <title>` | 設計判断をした | ADR | 背景と選択肢 | decisions/\<id>.md（背景・選択肢・決定・影響）、関連 concept へのリンク |
| `/wiki:promote <id>` | draft を確定させたい | 暫定 → 正典、Provenance | 記事 id | 出典・リンク・必須セクションを検査して status を上げる。不足があれば理由を返す |
| `/wik:lint [--fix] [--relations]` | 定期メンテ | lint、Lifecycle、Gap Analysis | なし | 孤立・矛盾・出典欠落・未回答 CQ・relations 不整合のレポート。`--fix` で機械的に直せるものを修正 |

`/wiki:graph` はフロントマターからグラフを生成するコマンドだが、LLM ではなくスクリプトで済むため Skill の外（`scripts/`）に置く。

### 共通ルール（SKILL.md 本文に記述）

1. raw/ は読むだけ。書き換え・移動・削除をしない。
2. 新規記事は必ずテンプレート（`templates/<type>.md`）から作り、フロントマターを全フィールド埋める。
3. 記事を作る前に index.md と既存記事を検索し、同一概念があれば新規作成せず更新する（SSOT）。
4. 1 記事 1 概念。説明が 2 つの概念にまたがったら分割して `related` で結ぶ。
5. 手順（howto）と概念（concept）を同じ記事に混ぜない。
6. 新規記事は `status: draft`。`reviewed` 以上への変更は `/wiki promote` 経由のみ。
7. すべての操作を log.md に 1 行追記する（日付、コマンド、触った記事 id）。
8. リンクは Foam の `[[id]]` 形式。ファイル名と `id` を一致させ、改名しない。

### `/wiki:ingest` の手順（代表例）

1. ソースを読み、raw/ に無ければ保存する。
2. `sources/<id>.md` を作る。要約、主張の一覧、登場する概念の候補。
3. 概念候補ごとに既存記事を検索。あれば追記、なければ `concepts/<id>.md` を draft で作る。
4. 新規・更新した記事の `sources` にソース id を追加、`relations` を埋める。
5. questions.md の未回答 CQ に答えられるものがあれば `answers` を付けてマークする。
6. 既存記事と矛盾する主張があれば上書きせず、記事内に「矛盾」セクションとして並記し、lint 対象にする。
7. index.md と log.md を更新し、触った記事の一覧を返す。

### `/wiki:plan` の手順

1. 領域について「この Wiki が答えられるべき問い」を 10〜30 個列挙し、questions.md に id 付きで追記する。
2. 問いから概念を抽出し、既存記事と照合する。
3. `moc/<topic>.md` を作り、既存記事へのリンクと未作成記事への赤リンクを並べる。
4. 未作成記事を優先度付きで返す。記事本文はここでは書かない（ingest か answer で埋める）。

## 導入ロードマップ

最初から 8 コマンドを揃えず、フェーズごとに足す。各フェーズの入口は記事数ではなく、「その問題が実際に起きたか」で判断する。

- [ ] **フェーズ 0（立ち上げ）**：CLAUDE.md にスキーマと共通ルールを書く。`templates/` を source / concept / journal の 3 種だけ用意。`/wiki:ingest`、`/wiki:query` を実装。
- [ ] **フェーズ 1（成長期への切替え）**：「同じ概念の記事が 2 つできた」「どこに何があるか分からなくなった」が起きたら開始。`/wiki:lint`、`/wiki:plan` を追加。questions.md を導入し、`type: moc` と `decision` を有効化。
- [ ] **フェーズ 2（正典化）**：他人や別プロジェクトから参照される記事が出てきたら開始。`/wiki:promote` と `status` の三段階を有効化。lint に出典検査を追加。
- [ ] **フェーズ 3（グラフ化）**：`relations` が十分に埋まったら開始。`/wiki:lint --relations` で整合性を検査し、`scripts/graph` でフロントマターからグラフを生成。この段階で初めてオントロジー化を検討する。

次に検討するテーマは 2 つある。一つは `templates/<type>.md` の具体的なセクション構成（特に concept の必須セクションと source の「主張一覧」の書式）。もう一つは lint の検査項目をどこまでスクリプト化し、どこから LLM に判断させるかの境界である。
````


## 成果

### エージェント A

## 結論

提案は info-hive の外で書かれたもので、その骨格（きっかけ別のコマンド、ソースから始める取り込み、矛盾の並記、lint への集約）は現行のプラグインに**すでにある**。新しく持ち込もうとしている要素のうち、作者の wiki で実際に起きている問題を解き、機械的に検査でき、ADR とも衝突しないのは、lint の検査と source ページの書式だけである。frontmatter の拡張（`id`、`scope`、入れ子の `relations`）、`status` の 4 値、新しい `type`、`/wiki:plan`・`/wiki:decide`・`/wiki:promote` は、導入しないか、条件がそろうまで保留にする。

### 4 区分の一覧

| 区分 | 要素 |
| --- | --- |
| **導入する** | ① index の見出しとページの `type` の照合（lint）。② `sources` の解決と `raw` の実体の検査（lint）。③ ログの行の書式の検査（lint） |
| **変えて導入する** | ④ source ページの「主張の一覧」。`## 主な主張` を置き、主張ごとに行き先を書く。⑤ type ごとの必須の節。SCHEMA で宣言したときだけ lint が検査する（`type` でモードを分けて lint が検査する設計のうち、`type` の側だけを採る）。⑥ 正式なタグの一覧の検査と、内容の lint での分類の再提案（Middle-out）。⑦ 「改名しない」の規則。文言を直しただけでは改名せず、命名規則の違反だけ lint で指摘する。⑧ 答えられなかった問いの記録。`questions.md` ではなく `log.md` に操作名 `gap` で残す。⑨ type ごとのテンプレート。source と concept だけ用意し、「全フィールドを埋める」は採らない。⑩ 成熟度フェーズと移行条件。プラグインの機能にはせず、導入の判断の規則として使う。⑪ 5 区分の方法論マップ。開発側の設計文書としてだけ使う |
| **保留**（条件つき） | ⑫ 主張ページの `status`。`hypothesis`・`supported`・`superseded` を流用し、直前の検討の PoC と同時に決める。⑬ `kind: "decision"`。⑭ `broader`。入れ子の `relations` ではなく、オントロジーの述語にする。⑮ `kind: "howto"` と「手順と概念を混ぜない」。⑯ `/wiki:lint --fix`。機械的な書き損じだけを対象にし、差分を見せて承認を得る。⑰ `reviewed_at`。⑱ `/wiki:plan`、Competency Questions、`questions.md` |
| **導入しない** | `id` キー、`scope`、入れ子の `relations`（`broader`・`related`・`answers` をまとめて）、`/wiki:lint --relations`、`status: draft|reviewed|canonical|deprecated` と「`draft` は出典なしで可」、`/wiki:promote`（status を上げるもの）、`/wiki:decide` と `decisions/`、`type` の `moc`・`journal`・`graph`・独立した `howto`・独立した `decision`、ingest で「概念の候補ごとに concept を draft で作る」手順、共通ルール 2 の「全フィールドを埋める」と 6 の「新規は draft」 |

### 最初に入れる 3 つ

1. **①（index の見出しと type の照合）**。作者の index で、16 本の source が「シンセシス」の見出しの下に並んでいる（実測）。今の lint は index.md を走査の対象から外している（`wiki_lint.py:126`）ため、これに気づけない。
2. **④⑤（source の `## 主な主張` と行き先、必須の節の検査）**。SemaSynth の作業記録が source に溜まり、concept に育っていない問題に直接効く。見出しの有無は機械的に検査できる。`## 主な主張` があるのは source 37 本のうち 5 本だけである。
3. **②（`sources` と `raw` の実体の検査）**。SKILL.md は、出典をたどれない主張を lint が洗い出すと書いているが、実装がない。今の作者の wiki では 0 件だが、汚染を防ぐための土台になる。

## 根拠

### 1. 要素の分解と現行との差分

「現行」は、`C:\Works\info-hive-dev\info-hive-wiki\`（v0.6.0、`plugin.json`）を読んで確かめた。

| # | 要素（提案の内容） | 現行 | 差分 |
| --- | --- | --- | --- |
| a | 5 区分の方法論マップ | ない | 設計の観点の整理である。プラグインの動作は変わらない |
| b | きっかけ別のコマンド分け | **ある** | `ingest`、`query`、`lint`、`learn`、`evolve` がすでにきっかけごとに分かれている（`commands/*.md`）。提案が足すのは `plan`、`decide`、`promote` |
| c | 成熟度フェーズと移行条件 | 一部 | `scaling-playbook.md` はページ数と行数（150 ページ、300 行）を合図にしている。提案は「問題が実際に起きたか」を合図にする |
| d | `type` と `status` でモードを分け、lint がモードごとに検査する | 一部 | lint は `type` を見ない。必須の frontmatter が全ページ共通（`DEFAULT_REQUIRED_FM`、`wiki_lint.py:278`）で、type ごとの検査はない |
| e | `id` | ない | ファイル名（スラッグ）が識別子である（`page-conventions.md` の「命名」） |
| f | `scope: common|project:<name>` | ない（別の手段がある） | ユーザースコープの wiki とプロジェクトの wiki を分けている（SKILL.md「保存の範囲」、ADR-0008） |
| g | `status: draft|reviewed|canonical|deprecated` | 一部（意味が別） | `experience-pattern` だけが `hypothesis|supported|superseded` を持つ（`assets/pattern.md.template`）。グラフのエッジは `current|historical|proposed|disputed|superseded` |
| h | `relations.broader`・`related`・`answers` | 一部（形が別） | 関係は本文の wikilink（`mentions`）と、入れ子の `graph.relationships`（型付き。オントロジーで宣言）で表す。`broader` という述語はない |
| i | `reviewed_at` | ない | `updated` だけがある |
| j | `type` の `howto`・`decision`・`moc`・`journal`・`graph` | 一部 | `decision` と `claim` は、オントロジーのノードの種類として `explicit_only` で宣言済みである（作者の `graph/ontology.yaml`）。ページの `type` は 4 種類だけ |
| k | `questions.md` と Competency Questions | ない | query で答えが足りないとき、取り込み候補を挙げるだけで、何も残らない（`query-workflow.md` 65 行） |
| l | `/wiki:plan` | ない | lint の `--suggest-pages` が、専用ページのない語を挙げる |
| m | `/wiki:decide` | ない | 名前の衝突がある。`wiki_decide.py` は判定レイヤーで、ADR とは無関係 |
| n | `/wiki:promote` | ない | 直前の検討でいう「昇格」は、source の知見を `kind: "claim"` のページに切り出すことで、別の操作である |
| o | `/wiki:lint --fix` | ない（方針で禁止） | 「ツールは wiki の Markdown を書き換えない」（SKILL.md 132 行）、「黙って書き換える」は避けるべきパターン（`lint-workflow.md`） |
| p | `/wiki:lint --relations` | ない | グラフの lint（`wiki_graph_lint.py`）が、型付きエッジの目的語と述語を検査している |
| q1 | 共通ルール 1：raw は読むだけ | **ある** | 現行は、Web ページの訳文の保存を例外にしている |
| q2 | 共通ルール 2：テンプレートから作り、全フィールドを埋める | 一部 | 汎用のテンプレートは `page.md.template` 1 つだけ。`url` などは該当するときだけ書く |
| q3 | 共通ルール 3：作る前に index を調べる（SSOT） | **ある** | `ingest-workflow.md` 手順 4 |
| q4 | 共通ルール 4：1 記事 1 概念、分割して `related` で結ぶ | **ある**（結び方が別） | アトミックなページと大きさの上限がある。結ぶのは wikilink |
| q5 | 共通ルール 5：手順と概念を混ぜない | ない | — |
| q6 | 共通ルール 6：新規は draft、reviewed は promote 経由 | ない | — |
| q7 | 共通ルール 7：すべての操作を log.md に 1 行 | 一部 | ingest、query、lint のログの書式は決まっている。書式の検査はない。作者の log には、書式から外れた行（`- 2026-11-07 ingest: ...`）が 1 行ある |
| q8 | 共通ルール 8：`[[id]]`、ファイル名と id を一致させ、改名しない | 一部 | リンクは `[[slug]]`。改名の規則はない。命名規則の違反（空白）も lint は見ない。作者の concepts には、空白を含むファイル名が 3 本ある |
| r | ingest：source の「主張の一覧」 | 一部 | `page-conventions.md` は source に「主な主張」の節を置くとしている。作者の wiki で実際にあるのは 37 本中 5 本（実測） |
| r2 | ingest：概念の候補ごとに concept を draft で作る | 別の規則がある | 手順 7 では、主要なトピックだけをページにする |
| r3 | ingest：矛盾を並記し、上書きしない | **ある** | 手順 6 の `## 矛盾` |
| r4 | ingest：`sources` の実体（raw）を lint が検査する | ない | `wiki_lint.py` の `links` は本文の wikilink だけで（245 行）、`sources:` と `raw:` を見ない |
| s | Diátaxis「手順と概念を混ぜない」 | ない | — |
| t | Middle-out の分類（lint で LLM が分類を再提案する） | 一部 | SCHEMA は、繰り返しのパターンに気づいたら追加を提案するとしている。`page-conventions.md` は「正式なタグ以外に lint が警告する」と書いているが、`wiki_lint.py` に該当の検査がない（findings の一覧に tag がない） |
| u | KCS と出典必須の両立（status で分ける） | 衝突する | SKILL.md の「防ぐべき失敗」の 1 つ目が、すべての主張に `sources:` を付けることである |

提案の ingest の手順は、現行と比べて**後退**している。ユーザーと要点を話す、被リンクを必須にする、更新の前に raw を読み直す、グラフを extract する、rag の PDF を扱う、といった手順が抜けている。新しく足しているのは「主張の一覧」だけである。

### 2. 作者の wiki での実測（`D:\Users\toshiki\info-hive\W0_Wiki\`、書き換えずに読んだ）

- ページは 57 本（source 37、concept 17、entity 1、synthesis 2）。直前の検討のあとに synthesis が 1 本増えている。
- index の照合：見出し（`## ソース` などを `type` の別名表で英語に直したもの）と、ページの `type` が食い違うものが **16 件**。index に載っていないページは 0 件。
- `sources:` で、存在しないページか source でないページを指すものは 0 件。`raw:`（wiki のルートからの相対パス `../W1_Raw/...`）で実体のないものは 0 件。
- source の `## 主な主張` は 5/37。`## 関係するページ` がない source は 6 本。
- タグ：source 37 本のうち 29 本が `["知識表現"]` だけである。SemaSynth の会計データの記録も含まれる。使われているタグは 4 つとも SCHEMA の一覧に載っているので、⑥ の機械的な検査は**今は 0 件**になる。問題はタグの粒度が粗いことで、機械的な検査では解けない。
- `graph:` を持つページは 1 本。`status`・`kind` を持つページは `kind: "person"` の 1 本だけで、`experience-pattern` はまだない。
- SCHEMA のページの大きさの上限は、ソフト 4,000 文字、ハード 8,000 文字で、既定より厳しい。

### 3. 採点

各要素を 1〜10 点で採点し、合計 = Σ(点 × 重み) ÷ 100 とした。重みは次の 3 通りである。

- 基準：価値 25、整合 20、検査 20、手間 20、軽さ 15
- 重み A（価値を重く）：価値 40、整合 15、検査 15、手間 15、軽さ 15
- 重み B（整合と軽さを重く）：価値 20、整合 25、検査 20、手間 15、軽さ 20。整合と軽さの合計は 45 で、直前の検討で指摘された「現状維持が構造的に有利になる」状態を再現した重みである

すでにある要素（b、q1、q3、q4、r3）は変更しないので、採点していない。

| 要素 | 価値 | 整合 | 検査 | 手間 | 軽さ | 基準 | A | B | 点数の根拠 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ① index と type の照合 | 8 | 10 | 10 | 9 | 8 | **9.00** | 8.75 | 9.05 | 実在する 16 件を見つける。別名表を流用できる |
| ② sources と raw の実体 | 5 | 10 | 10 | 9 | 8 | **8.25** | 7.55 | 8.45 | 今は 0 件で、予防のための検査。文書化済みで未実装 |
| ③ log の書式 | 4 | 10 | 10 | 9 | 9 | 8.15 | 7.30 | 8.45 | 1 件を見つける。価値は小さい |
| ⑤ type ごとの必須の節 | 6 | 9 | 10 | 8 | 7 | 7.95 | 7.50 | 8.05 | 見出しの照合だけで済む。SCHEMA で選んだときだけ有効 |
| ⑦ 改名しない＋命名の lint | 5 | 9 | 10 | 8 | 8 | 7.85 | 7.25 | 8.05 | 空白を含むファイル名 3 件を見つける |
| ④ source の主な主張と行き先 | 8 | 9 | 7 | 7 | 7 | 7.65 | **7.70** | 7.70 | source に溜まる問題に効く。行き先の判断は LLM による |
| ⑥ 正式タグの検査と再提案 | 5 | 10 | 9 | 7 | 8 | 7.65 | 7.10 | 7.95 | 機械的な検査は 0 件。再提案は LLM の判断 |
| ⑩ フェーズと移行条件（判断の規則として） | 6 | 9 | 5 | 8 | 10 | 7.40 | 7.20 | 7.65 | 文書だけで済む。合図の判定は人がする |
| ⑧ 未回答の問いを log に残す | 6 | 8 | 7 | 7 | 8 | 7.10 | 6.90 | 7.25 | 取り込みの候補が積み上がる |
| ⑫ claim の status（流用） | 6 | 7 | 8 | 6 | 7 | 6.75 | 6.60 | 6.85 | 値の検査は機械的にできる。どの値にするかは LLM の判断 |
| ⑨ type ごとのテンプレート | 5 | 8 | 7 | 7 | 7 | 6.70 | 6.35 | 6.85 | ④ の補助になる |
| ⑭ broader を述語にする | 4 | 8 | 8 | 5 | 8 | 6.40 | 5.95 | 6.75 | スクリプトを変えずに書ける。記入の手間が増える |
| ⑪ 5 区分マップ（開発文書） | 3 | 9 | 2 | 9 | 9 | 6.10 | 5.55 | 6.40 | 利用者に見える効果はない |
| ⑬ kind: "decision" | 5 | 7 | 6 | 6 | 7 | 6.10 | 5.90 | 6.25 | claim との境界があいまい |
| ⑯ lint --fix（承認つき） | 5 | 4 | 8 | 7 | 6 | 5.95 | 5.75 | 5.85 | 書き換えない方針と衝突する |
| ⑮ kind: "howto"＋混ぜない | 4 | 8 | 4 | 6 | 8 | 5.80 | 5.50 | 6.10 | 「混ざっていないか」は機械的に検査できない |
| ⑰ reviewed_at | 4 | 7 | 6 | 3 | 8 | 5.40 | 5.20 | 5.80 | 書くのは人だけで、手間が増える |
| id | 1 | 3 | 8 | 6 | 5 | 4.40 | 3.70 | 4.45 | スラッグと二重になる |
| --relations | 3 | 3 | 7 | 5 | 4 | 4.35 | 4.05 | 4.30 | 入れ子の relations が前提 |
| type: graph | 1 | 2 | 5 | 7 | 7 | 4.10 | 3.55 | 4.15 | グラフは派生データで、ページではない |
| 概念の候補ごとに draft を作る | 3 | 3 | 4 | 5 | 6 | 4.05 | 3.90 | 4.10 | 167 ページ規模に膨らむ（直前の検討） |
| /wiki:promote | 4 | 4 | 6 | 2 | 4 | 4.00 | 4.00 | 4.10 | ページごとに人の判断が要る |
| scope | 3 | 2 | 7 | 4 | 4 | 3.95 | 3.75 | 3.90 | ADR-0008 の分け方と二重になる |
| /wiki:plan、CQ、questions.md | 5 | 4 | 4 | 3 | 3 | 3.90 | 4.10 | 3.85 | 問いを 10〜30 個ずつ、人が判断することになる |
| type: moc（未作成の記事へのリンク） | 3 | 3 | 5 | 4 | 5 | 3.90 | 3.75 | 3.95 | lint がリンク切れとして毎回報告する |
| /wiki:decide、decisions/ | 5 | 2 | 5 | 4 | 3 | 3.90 | 4.10 | 3.70 | ADR-0008 の `70_ADR` と衝突する |
| 入れ子の relations | 4 | 2 | 5 | 4 | 3 | 3.65 | 3.70 | 3.50 | パーサーが入れ子を読まない |
| status 4 値＋出典なしの draft | 4 | 2 | 6 | 2 | 3 | 3.45 | 3.55 | 3.40 | SKILL.md の「防ぐべき失敗」に反する |
| type: journal | 2 | 1 | 5 | 4 | 4 | 3.10 | 2.90 | 3.05 | ADR-0006 に反する |

計算の例として、① の基準の重みでは (8×25 + 10×20 + 10×20 + 9×20 + 8×15) ÷ 100 = 900 ÷ 100 = 9.00 になる。

**重みを変えたときの結果**

- 採るか採らないかの境目は、どの重みでも動かない。「導入しない」の群は 3 通りとも最高で 4.45、保留の群は最低で 5.20 である。
- 上位の並びは重みで入れ替わる。重み A では ④ が 2 位（7.70）に上がり、③ は 7.30 に下がる。重み B では ③ が ② と並んで 2 位（8.45）に上がる。
- 最初の 3 つに ③ ではなく ④ を選んだのは、点数ではなく価値で判断したためである。③ は 1 件を直すだけで、④ は source に溜まる問題に効く唯一の要素である。

### 4. 衝突と解き方

| 衝突 | 内容 | 解き方 |
| --- | --- | --- |
| ADR-0006 と `journal` | 日付ノートは被リンクがなく、毎日孤立として報告される（ADR-0006 の背景）。提案のフェーズ 0 は journal のテンプレートを用意している | **導入しない**。日付ノートは `log` プラグインで書き、`50_Notes` を経て `/wiki:ingest` で wiki に入れる経路を残す。ADR は変えない |
| ADR-0008 と `scope` | ADR-0008 は、ユーザースコープとプロジェクトを作業領域と wiki で分けている。SKILL.md は「2 つの wiki を黙って混ぜてはならない」としている | **導入しない**。ただし、作者の wiki には SemaSynth の記録（プロジェクト固有）が 28 本あり、ADR-0008 の「ユーザースコープの作業領域にはプロジェクト固有の情報を置かず」と字面で食い違う。作者のグローバルの指示が、プロジェクトの知見をユーザースコープの wiki に残すよう求めているためである。`scope` で印を付けるのではなく、再利用できる知見だけを主張ページに昇格させ、進捗は source か `log` に置く運用で解く。ADR-0008 を変えるかどうかは作者の判断である（前提の節） |
| ADR-0008 と `/wiki:decide` | `decisions/<id>.md` は、ADR を書く場所 `70_ADR/`（書き手は人）と重なる | **導入しない**。ADR は `70_ADR` に書き、source として取り込む。決定をグラフのノードにしたければ、⑬ の `kind: "decision"` で表す（保留）。名前も `wiki_decide.py`（判定レイヤー）と紛らわしい |
| ADR-0009 と `relations` | 型付きのエッジとオントロジーに加えて、SKOS 風のキーを足すと、関係の表し方が 2 系統になる | **入れ子の `relations` は導入しない**。`broader` が要るなら、`ontology.yaml` に `broader: {subject_types: [concept, claim], object_types: [concept], requires_evidence: false}` を足し、既存の `graph.relationships` で書く。`wiki_graph_lint.py` は、利用者が定義した述語でも `requires_evidence: false` を尊重することを確かめた（246 行、337 行）。グラフ層は任意の索引のままなので、ADR-0009 は変えない |
| 平坦な frontmatter | `wiki_text.py:181,183` は入れ子を読まない。lint と検索から `relations` が見えない | 上と同じ。入れ子は、PyYAML で読む graph のスクリプトの `graph:` だけに限る |
| 方針 B | 提案のキーと値は英語で、方針 B と合っている。ただし、`id` の例（`relational-primary-key`）とソースの id（`src-...`）は英字が前提で、日本語のスラッグと合わない | キーと値は英語のまま採る。識別子は日本語のスラッグを続け、`id` は採らない |
| ファイル名と id を一致させ改名しない | id がスラッグと二重になり、ずれたときにどちらが正本か分からなくなる | `id` は採らない。「改名しない」は、文言を直しただけでは改名しない、という形にする（直前の検討の 6.4 と一致）。命名規則の違反（空白 3 件）は lint が指摘し、改名するときは被リンクを移す |
| `status` の値 | すでに 2 系統の値がある（`experience-pattern` とグラフのエッジ）。提案の 4 値を足すと 3 系統目になる | **3 系統目は作らない**。主張ページの状態は `hypothesis`・`supported`・`superseded` を流用する（⑫）。人が確かめたかどうかを `status` で表すことは採らない |
| 「`draft` は出典なしで可」 | SKILL.md の「防ぐべき失敗」の 1 つ目と、SCHEMA の必須項目（source 以外のページは `sources`）に反する | **導入しない**。info-hive の取り込みはソースから始まるので、出典のない下書きが生まれにくい。KCS の「使いながら書く」は、query の synthesis の保存がすでに受け持っている |
| 直前の検討の `kind: "claim"` | 提案は「1 記事 1 概念」と「候補ごとに concept を作る」で、ページが増える方向にある。どちらの「昇格」も同じ語で、意味が違う | 直前の検討を優先し、昇格させるのは条件を満たした主張だけにする。提案の「主張の一覧」は、直前の検討で欠けていた「何を source に残し、何を送ったかの記録」の置き場所として採る（④）。この点は提案のほうが具体的である。「promote」という語は status の変更には使わない |
| lint は書き換えない | `--fix` は、SKILL.md 132 行と `lint-workflow.md` の方針に反する | 保留（⑯）。採るとしても CLI だけにし、既定は差分の表示だけにする。全角のコロン、「、」の区切り、引用符といった機械的な書き損じに限り、承認を得てから適用する。MCP のツールは読むだけのままにする |
| MOC の未作成記事へのリンクとリンク切れの検査 | 未作成の記事へのリンクは、lint の `broken_links` として毎回報告される。ADR-0006 が日付ノートで避けたのと同じ雑音になる | `type: moc` は導入しない。入口の役割は、用語の concept ページと index が持つ（直前の検討の 4 節） |
| `questions.md` の置き場所 | wiki のルートに置くと、`SKIP_TOP_LEVEL_FILES`（`wiki_lint.py:126`）の対象外なので、frontmatter の欠落と孤立として報告される | ⑧ で `log.md` に `gap` の行として残す。新しいファイルは作らない |

結論として、採る要素のために**変える ADR はない**。採った要素とその理由は、新しい ADR（ADR-0014「記事の作成と保守の方法論」）にまとめる。もし後で `/wiki:decide` を採るなら、ADR-0008 の「各ディレクトリの役割」の表の `70_ADR` の行（書き手が「人」）を改める必要がある。journal を採るなら、ADR-0006 を置き換える必要がある。どちらも今は勧めない。

### 5. 導入する要素の詳細

**lint の追加（`--json` のキーは英語）**

| キー | 検査すること | 作者の wiki での件数 |
| --- | --- | --- |
| `index_type_mismatch` | `index.md` と `indexes/*.md` の `## 見出し` を、`type` の値の別名表（`ソース`→`source` など。`wiki_text.py`）で英語に直す。見出しの下の wikilink の先のページの `type` と比べる。表にない見出しは見ない | 16 |
| `unindexed_pages` | どのインデックスにも載っていないページ | 0 |
| `unresolved_sources` | `sources:` の要素が、存在しないページか、`type: "source"` でないページを指す | 0 |
| `missing_raw` | `raw:` が相対パスで、実体がない。絶対パス（rag の PDF）は PC ごとに違うので既定では見ない。照合には `raw_sha256` を使う | 0 |
| `unknown_tags` | SCHEMA の正式なタグの一覧にないタグ。一覧はエージェントが SCHEMA から読み、`--allowed-tags` で渡す。`required_fm` と同じ渡し方である | 0 |
| `invalid_slugs` | 命名規則に反するスラッグ（空白、禁止の文字、全角の英数字） | 3 |
| `malformed_log_lines` | `log.md` の、`## [YYYY-MM-DD] <op> | ` でも 3 文字の空白で字下げしたサブ行でもない行 | 1 |
| `missing_sections` | `--required-sections "source=主な主張,関係するページ"` で渡した `##` の見出しがない。渡さなければ検査しない | 指定したときだけ。主な主張なら 32 |
| `invalid_status`（段階 3） | `kind: "claim"` か `"experience-pattern"` のページで、`status` が 3 つの値のどれでもない | 0 |

**SCHEMA.md と references の改訂の要点**

- `SCHEMA.md.template` に、アップグレードで検出する英語の見出しの節を足す。`## Required sections`（type ごとの必須の節。既定は空）と、段階 3 で `## Claim pages` である。`/wiki:upgrade` で既存の SCHEMA に冪等に足す。
- `page-conventions.md`：source の本文の規約を「主な主張」の節に置き換える。主張 1 つにつき箇条書き 1 行とし、行末に行き先を `→ [[スラッグ]]`（既存のページに入れた）か `→ ソースのみ` で書く。進捗、1 回の数値、固有の対象の属性は「ソースのみ」にする（直前の検討 6.3 の手順 2）。「改名しない」の規則も書き足す。
- `ingest-workflow.md`：手順 5 で主な主張と行き先を書き、手順 6 と 7 でその行き先どおりに更新する。
- `query-workflow.md`：wiki に答えが足りなかったら、`## [YYYY-MM-DD] gap | <問い>` を log に追記する（操作名は英語、問いは日本語）。
- `lint-workflow.md`：手順 4（足りない点）で `grep "] gap |" log.md` を読み、取り込みの候補にする。内容の lint で、タグの分類の改訂案（Middle-out。例：`知識表現` に 29/37 が偏っている）を、編集案として出す。
- `assets/`：`source.md.template` と `concept.md.template` を足し、`page.md.template` は汎用として残す。

**導入後の frontmatter の例（ファイルは書かない）**

1. `sources/semasynth再現性の検証-2026-11-06.md`（段階 2 のあと）。frontmatter に足すのは `concepts` だけで、本文に節が増える。

```yaml
---
type: "source"
title: "SemaSynth 再現性の検証"
authors: ["Codex"]
raw: "../W1_Raw/semasynth再現性の検証-2026-11-06.md"
ingested: 2026-11-06
created: 2026-11-06
updated: 2026-11-08
tags: ["知識表現"]
concepts: ["同一環境と異なる環境では再現性の判定を分ける"]
---
```

本文に足す節：

```markdown
## 主な主張
- 同一環境では全ファイルのバイト一致、異なる Python・SQLite では値・型の一致で再現性を判定する。→ [[同一環境と異なる環境では再現性の判定を分ける]]
- Python のネットワーク操作を audit hook で禁止するが、OS 全体の遮断は保証しない。→ ソースのみ
```

2. `concepts/編集要求の復元世代を最終適用まで保持する.md`（段階 3 で PoC に合格したあと）。

```yaml
---
type: "concept"
kind: "claim"
status: "hypothesis"
title: "編集要求の復元世代を最終適用まで保持する"
sources: ["output復元資格の設計-2026-11-04"]
created: 2026-11-04
updated: 2026-11-08
tags: ["並行処理"]
---
```

source は設計の 1 本だけなので、`hypothesis` にしている。このページは「決定」とも読めるので、⑬（`kind: "decision"`）を claim と分けない理由の例にもなる。

3. `concepts/オントロジー.md`（用語ページ）。frontmatter は変えない。`status` も `kind` も付けない。用語ページは状態の管理の対象外である。

### 6. 導入の順序と条件

| 段階 | 入れるもの | 入れる合図 | SemVer | 既存の wiki の移行 |
| --- | --- | --- | --- | --- |
| 0 | なし（作者の wiki の手直し） | 今 | なし | 16 本を「ソース」の見出しの下に移す。log の 1 行を直す。空白を含む 3 本の改名は作者が決める（主張の単位の導入とは抱き合わせない） |
| 1 | ①②③⑥（機械的な検査）⑦ と、ADR-0014 | 今。index の誤りがすでに起きていて、提案のフェーズ 1 の合図「どこに何があるか分からない」に当たる | マイナー 0.6.0 → 0.7.0。`--json` にキーを足すだけで後方互換 | ページは変えない。新しい指摘が出るだけである |
| 2 | ④⑤⑧⑨、references と SCHEMA のテンプレートの改訂 | 段階 1 を出したあと。直前の検討の PoC の入力（source の主張の一覧）にもなる | マイナー 0.8.0 | `## Required sections` は既定で空にし、作者が選んだら有効にする。主な主張のない 32 本は、LLM が raw から書き足す案を示し、承認を得て進める |
| 3 | ⑫（claim の `status`）、`kind: "claim"`、`ontology.yaml.template` に `maps_from: {type: concept, kind: claim}` | 直前の検討の PoC が合格の目安を満たしたとき | マイナー 0.9.0 | 既存の concept は自動では変えない。claim にするページは提案して承認を得る。`concept:x` が `claim:x` に変わると、明示エッジの目的語は直らない（直前の検討 10 節）ので、extract のあとにグラフの lint で確かめる |
| 4（保留） | ⑬ | claim ページが 10 本を超え、そのうち決定の形のものが 3 本以上になったとき | マイナー | — |
| 4（保留） | ⑭ | concept と claim が 50 本を超えるか、index を下位のカテゴリに分ける必要が出たとき（`scaling-playbook.md`） | マイナー | `ontology.yaml` に 1 項目足すだけ |
| 4（保留） | ⑮ | 手順が主のページが 3 本以上たまったとき | マイナー | — |
| 4（保留） | ⑯ | 機械的な書き損じが、1 回の lint で 10 件以上出ることが続いたとき | マイナー | — |
| 4（保留） | ⑰ | wiki を他人と共有するか、人が確かめた印が実際に要る場面が出たとき | マイナー | — |
| 4（保留） | ⑱ | 同じ領域で `gap` の行が 10 件以上たまったか、作者が領域を決めて網羅したいと言ったとき | マイナー | — |

メジャーの更新が要る要素はない。既定の動作を変えるもの（必須の節）は、SCHEMA で選んだときだけ有効にする。

### 7. 提案自体の誤りや不整合

採否の判断には使っていない。

- コマンドの数：「8 コマンド」と書いているが、表にあるのは 6 つである（`ingest`、`plan`、`query`、`decide`、`promote`、`lint`）。`graph` を足しても 7 つにしかならない。
- 表記の誤り：`syntesis`、`/wik:lint`、`/wiki promote`（空白）、`<pathっurl>`。
- 名前：「1 つの Skill（`wiki`）」とあるが、info-hive ではプラグイン名が `wiki`、スキル名が `info-hive` である。
- スキーマの置き場所：フェーズ 0 は CLAUDE.md、Skill 設計は SKILL.md 本文、Karpathy の 3 層は schema 層と、3 か所に分かれている。`templates/<type>.md` と Foam の `.foam/templates/`（ADR-0008）の関係も書かれていない。
- 段階のずれ：方法論マップでは `status` と SKOS 風の `relations` を「先に採用」としているが、ロードマップではそれぞれフェーズ 2 と 3 に置いている。lint も、マップでは先に採用、ロードマップではフェーズ 1 である。
- 「`status` の三段階」と書きながら、値を 4 つ挙げている。`deprecated` に変える経路も決まっていない。
- Diátaxis の行で「type を explanation 一択でよい」と書いているが、`type` の一覧に `explanation` がない。
- `/wiki:query --type howto`：答える操作に、記事の種類を作る役割を負わせている。
- `sources` の lint を「raw/ に実体があるか」としているが、`sources` が指すのは source ページで、raw ではない。
- `relations` の lint に「孤立ページがないか」が入っているが、孤立は wikilink の問題である。
- `/wiki:graph` を「Skill の外（`scripts/`）に置く」としながら、コマンドとしても挙げている。
- ingest の手順 1「raw に無ければ保存」と、共通ルール 1「raw は読むだけ」の関係が書かれていない。
- 画像「導入フェーズ · 4 段階と 3 つの移行条件」が失われている。本文からは、合図は 3 つ（同じ概念の記事が 2 つ／どこに何があるか分からない、参照される記事が出た、relations が埋まった）と読める。

## 検討した代替案

- **提案をフェーズ 0 からそのまま入れる**：採らない。frontmatter の拡張（`id`、`scope`、`relations`、`status`）が、パーサー、ADR-0006・0008・0009、出典必須の規則と衝突する。また 57 ページすべてに `status: "draft"` が付き、作者が 1 本ずつ判断することになる。
- **`status` を全ページに入れ、LLM に `reviewed` を判断させる**：採らない。LLM が書いて LLM が「確かめた」と印を付けても、SKILL.md の 2 つ目の失敗（wiki が自分の出力を読むことによるずれ）を強めるだけである。人が判断するなら、取り込みのたびに手間が増える。
- **`questions.md` を作り、lint の走査の対象から外す**：⑧ の `gap` の行と比べて、ファイルの規約と `SKIP_TOP_LEVEL_FILES` の変更が余分に要る。答えられなかった問いが 10 件を超えるまでは、log で足りる。
- **`broader` を平坦なキーにし、`sources` と同じように extract が暗黙のエッジにする**：スクリプトの変更が要る。オントロジーの述語にすれば変更が要らないので、そちらを保留の案にした。
- **新しい `type` の `howto` と `decision` を足す**：ディレクトリ、index の見出し、別名表、`maps_from` を増やすことになる。`(type, kind)` の照合（`wiki_graph_extract.py` 245〜258 行）を使う `kind` のほうが軽いので、保留にするのは `kind` の形だけにした。
- **最初の 3 つにタグの検査（⑥）を入れる**：作者の wiki では、機械的な検査が 0 件になる（4 つのタグがすべて一覧に載っている）。偏りは LLM の再提案でしか解けないので、段階 1 に入れるが、最初の 3 つからは外した。

## 前提と不確実性

- **仮定**：`raw:` の基準は、作者の wiki に合わせて wiki のルートと解釈した（`../W1_Raw/` は sources からではなく、ルートから解決すると実在する）。テンプレートの `raw: "raw/..."` は、プロジェクトの根を基準に読める。基準のディレクトリが仕様で決まっていないので、`missing_raw` を実装する前に決める必要がある（要確認）。
- `index_type_mismatch` は、見出しが `type` の別名と一致する wiki だけで働く。見出しを自由に付けた wiki では 0 件になる。
- ⑭ の述語で、`confidence` と `status` を必須として検査するかは、`wiki_graph_lint.py` の該当箇所を最後まで読んでいない。
- Foam が日本語のファイル名の `[[slug]]` を解決することは、確かめていない。
- **作者の判断が要ること**：
  - SemaSynth の記録をユーザースコープの wiki に置き続けるか。ADR-0008 の字面と、グローバルの指示が食い違っている。
  - 空白を含む 3 本を改名するか。
  - 必須の節を作者の wiki で有効にし、32 本を書き足すか。
- **基準への異議**：
  - 「実装と移行の軽さ」と「既存設計との整合」は、すでにある要素を導入しないときにも高く出る。そのため、既存の要素は採点から外した。
  - 「利用者が得る価値」は、今の wiki で見つかる件数と、予防の価値を区別していない。② の 0 件と ① の 16 件は、同じ点数の幅で比べにくい。
  - 直前の検討と同じく、「検査可能性」の点数は機械的な検査の部分だけを表す。④ の行き先の判断の再現性は、PoC で測るしかない。

## 参照

- 開発用のリポジトリ（作業ツリー）：`AGENTS.md`、`docs/adr/0006-daily-journal-is-separate-plugin.md`、`docs/adr/0008-numbered-workspace-layout.md`（作業領域、ディレクトリの役割、`70_ADR`）、`docs/adr/0009-graph-layer-stays-in-wiki.md`、`docs/research/wiki-note-granularity-2026-11-08.md`（4〜11 節）
- プラグイン（`C:\Works\info-hive-dev\info-hive-wiki\`）：
  - `.claude-plugin/plugin.json`（0.6.0）、`commands/` の一覧、`commands/lint.md`
  - `skills/info-hive/SKILL.md`（11 行、99 行、132 行、「防ぐべき失敗」）
  - `references/page-conventions.md`（frontmatter、タグ、命名、本文の構成）、`ingest-workflow.md`（手順 4〜9）、`lint-workflow.md`、`query-workflow.md`（65 行、67〜115 行）、`graph-workflow.md`（23 行、53 行）、`scaling-playbook.md`
  - `assets/page.md.template`、`pattern.md.template`、`SCHEMA.md.template`（194 行）
  - `scripts/wiki_lint.py`（126〜127 行、225〜256 行、278 行、281〜420 行）、`wiki_text.py`（181〜309 行）、`wiki_graph_extract.py`（240〜262 行、409〜423 行）、`wiki_graph_lint.py`（236〜262 行、325〜345 行）、`wiki_search.py`（848 行）
- 作者の wiki（`D:\Users\toshiki\info-hive\W0_Wiki\`。読んだだけ）：`SCHEMA.md`、`index.md`、`log.md`（末尾）、`graph/ontology.yaml`、`sources/semasynth再現性の検証-2026-11-06.md`、`sources/semasynth管理会計サンプル-2026-11-06.md`、`sources/part-1-what-is-an-ontology-classes-properties-and-axioms.md`、`concepts/編集要求の復元世代を最終適用まで保持する.md`、`concepts/オントロジー.md`
- 実測には、作業ディレクトリの外で Python のワンライナーを実行した。数えたのは、index の見出しと `type` の食い違い、index に載っていないページ、`sources` と `raw` の解決、節とタグの件数である。

使用した MCP サーバー: なし
使用した Agent Skills: なし

### エージェント B

読み込みと検証が終わりました。lint は `index.md`・`log.md` など名前で決めたルート直下のファイルだけを飛ばし、被リンクは本文の wikilink だけから数えること、グラフの暗黙エッジは `sources:` と `raw:` だけから作られることを確かめました。以下が成果です。

## 結論

### 結論の要約（4 区分）

| 区分 | 要素 |
| --- | --- |
| **導入する** | Middle-out の「分類は発見して承認する」を lint の検査に落とす（`index.md` の見出しと `type` の食い違いの検出）。「問題が実際に起きたら入れる」というロードマップの原則。共通ルール 1・3・4・7（現行で既にある。差分だけ揃える） |
| **変えて導入する** | source ページの「主張の一覧」（行き先 `create` / `update` / `source_only` を添える）。`/wiki:promote`（status の昇格ではなく、source の主張を `type: "concept"`、`kind: "claim"` のページに昇格させる操作に変える）。`status`（全ページではなく `kind: "claim"` と既存の `experience-pattern` に限る。値は `hypothesis` / `supported` / `disputed` / `superseded`）。`questions.md`（人が CQ を列挙するのではなく、query が答えられなかった問いを自動で追記する台帳に変える）。`/wiki:lint --fix`（機械的に直せる日本語の書き損じに限り、差分を見せて承認を得てから書く）。Diátaxis の「手順と概念を混ぜない」（1 行の規約として、`type: howto` は作らない）。共通ルール 8（「改名しない」ではなく「改名は被リンクの移し替えと一緒に」）。5 区分の方法論マップ（ADR の背景の整理として使う。プラグインは変えない） |
| **導入しない** | `id`、`scope`、`reviewed_at`、入れ子の `relations`（`broader` / `related` / `answers`）、`type` の `howto` / `decision` / `moc` / `journal` / `graph`、`/wiki:decide`、`/wiki:plan`、`/wiki:lint --relations`、`draft` は出典なしでよいという規則、`reviewed` / `canonical` の人によるレビュー段階、きっかけ別に 8 コマンドへ分ける設計 |
| **保留** | `broader` を平坦なキーで持ち、オントロジーの述語に写す案（インデックスの分割の閾値、約 150 ページに達したら再検討）。Competency Questions の人手による列挙（作者が「網羅したい領域」を明示したら再検討） |

**最初に入れる 3 つ**（採点と条件の両方で先頭に来るもの）:

1. **`index.md` の見出しと `type` の食い違いを lint で検出する。** 作者の wiki では「シンセシス」の欄に `type: "source"` が 16 本並び、今の lint は 0 件を返す。機械的に検査でき、既存ページを壊さない。
2. **source ページに「主張の一覧」と行き先を書く。** 37 本の source のうち 28 本が SemaSynth の記録で concept に育っていない偏りに、取り込みの時点で手を打つ唯一の要素である。直前の検討の 6.3 の手順 6 と同じ方向で、提案のほうが書式が具体的である。
3. **`kind: "claim"` と限定した `status`、それを作る `/wiki:promote`。** ただし直前の検討が求めた PoC（振り分けの一致率）を通ってから入れる。

### 導入の順序と条件（SemVer と移行）

| 段階 | 入れるもの | 入れる合図 | SemVer | 既存の 57 ページの移行 |
| --- | --- | --- | --- | --- |
| **1** | lint に `index_type_mismatch`（インデックスの見出しと `type` の食い違い）。`ingest-workflow.md` の手順 5 に `## 主張` の表と行き先を追加。`page-conventions.md` に「手順と概念を同じページに混ぜない」の 1 行。ADR（記事の作成の方法論）に 5 区分と「問題が起きたら入れる」の原則を書く | 条件なし。食い違いは作者の wiki で既に起きている | **マイナー**（0.7.0）。lint の検出項目とページの規約が増える | `index.md` の 16 項目を「ソース」の欄に移す。既存の source ページに `## 主張` を遡って足すことは求めない |
| **2** | `kind: "claim"`、`status`（4 値）、`superseded_by`、`ontology.yaml.template` に `claim` の `maps_from`、`/wiki:promote <source-slug>`、lint の status 検査。`SCHEMA.md` でオプトイン | 直前の検討の PoC（配置先の一致率と SemaSynth から出る concept の本数）が合格したら。または、段階 1 の `## 主張` で `source_only` 以外の行き先が 10 件以上たまったら | **マイナー**（0.8.0）。オプトインなので既存の wiki は変わらない | 題名が主張の形の既存 concept 3 本（`編集要求の復元世代を最終適用まで保持する`、`Windows での Tantivy の commit の失敗`、`BM25 の IDF の式の違い`）に `kind` と `status` を付ける。`maps_from` を足すと node ID が `concept:x` から `claim:x` に変わるが、作者の wiki の型付きエッジは `authored` 5 本だけで concept を目的語にするものがないので、extract のやり直しだけで済む |
| **3a** | `questions.md`（query が答えられなかった問いを追記。ingest が照合し、答えたら `answered` と日付を書く） | 「wiki に答えがない」と報告した query の実例が 3 件たまったら（作者の synthesis「LLM Wiki で蓄積した情報の活用方法」の見直す条件と同じ） | **マイナー**。ルート直下のファイルを飛ばす一覧（`wiki_lint.py` の `SKIP_TOP_LEVEL_FILES` など）にも足す必要があり、スクリプトの変更を含む | なし |
| **3b** | `/wiki:lint --fix`（`unquoted_strings`、全角の「：」、「、」の区切り、日付の形、`index_type_mismatch` に限る。`--dry-run` の差分を示し、承認後に書く） | 1 回の lint で機械的な指摘が 20 件を超え、1 件ずつの `str_replace` が負担になったら | **マイナー** | なし |
| **3c** | `broader: ["slug"]` の平坦なキーを `broader` 述語（`requires_evidence: false`）に写す。lint で循環を検査 | ページ数が約 150 を超え、`indexes/` に分けるとき | **マイナー**。`wiki_graph_extract.py` の `build_edges` に 1 種類の暗黙エッジを足す変更 | 既存ページには付けない |

**メジャーにすべき変更は推さない。** `id` の導入や `status` の全ページ必須化はメジャーになるが、どちらも導入しない。

## 根拠

### 1. 要素の分解と現行との差分

| # | 提案の要素 | 現行の対応 | 差分 |
| --- | --- | --- | --- |
| E01 | 5 区分の方法論マップ | 一部。`SKILL.md` の「3 つの層と 3 つの操作」が同じ役割 | 現行は操作（ingest / query / lint）で切り、提案は問題（発見 / 構造化 / 体系化 / 執筆 / 維持）で切る。整理としては補い合う |
| E02 | きっかけ別に 8 コマンド | 一部。`init`、`ingest`、`query`、`lint`、`graph`、`learn`、`evolve`、`stats`、`upgrade`、`help` の 10 個 | `plan`、`decide`、`promote` がない。提案の `graph` を「Skill の外」に置く案は、現行の `/wiki:graph` + `scripts/` と同じ形 |
| E03 | 成熟度フェーズと移行条件 | 一部。`scaling-playbook.md` の閾値 1〜5 は「ページ数」で切る | 提案は「問題が起きたか」で切る。現行の lint・graph は提案のフェーズ 1・3 の機能だが、初期化で全部入る |
| E04 | `type` と `status` でモードを分け lint が検査 | 一部。`type` でディレクトリと必須項目が変わる（`SCHEMA.md` の「種類ごとに」）。`status` は `experience-pattern` だけで、`wiki_lint.py` は `status` を一切検査しない（grep で確認） | ページ単位の `status` 検査は新しいコード |
| E05 | `id` | なし。スラッグ（ファイル名）が識別子 | `id` は必ずファイル名と同じ値になり、冗長 |
| E06 | `scope: common / project:<name>` | なし。ADR-0008 がユーザースコープとプロジェクトを**ディレクトリで**分ける | 1 つの wiki の中にスコープを混ぜる前提が ADR-0008 と逆 |
| E07 | `status: draft / reviewed / canonical / deprecated` | 一部。`experience-pattern` に `hypothesis / supported / superseded`。グラフのエッジに `current / historical / proposed / disputed / superseded` | 3 つ目の語彙になる。`reviewed` を判断する人が運用にいない |
| E08 | `relations.broader / related / answers`（入れ子） | 一部。`related` は本文の wikilink（`mentions` エッジ）、型付きの関係は `graph.relationships`。`broader` と `answers` はない | `wiki_text.py` のパーサーは入れ子を読まない（`parse_frontmatter_text` の docstring、`_FM_KEY_RE` が行頭の空白を拒む）。`graph:` だけが PyYAML を使うスクリプトで読まれる例外 |
| E09 | `reviewed_at` | なし。`updated` がある | レビュー者がいないので値が決まらない |
| E10 | `type: howto` | なし。`SCHEMA.md` で種類を足せる（`architecture.md` 26 行目） | 作者の wiki に手順主体のページはない |
| E11 | `type: decision`、`/wiki:decide` | なし。ADR-0008 がプロジェクトの作業領域に `70_ADR/`（人が書く）を置く。作者の wiki は SemaSynth の ADR 0002〜0010 を **source** として取り込んでいる | 二重になる |
| E12 | `type: moc` | 一部。`index.md` と `indexes/` が MOC。用語の concept が入口を兼ねる（直前の検討の 4 節） | 新しい種類は要らない |
| E13 | `type: journal` | なし。ADR-0006 で `log` プラグインに分離 | 衝突 |
| E14 | `type: graph` | なし。グラフは層でありページの種類ではない | 提案の誤り |
| E15 | `questions.md` と Competency Questions | 一部。query の手順 7「wiki に内容がなければ取り込む候補を挙げる」、lint の手順 4「まったく扱われていないものを探す」はあるが、**どこにも記録されない** | 未回答の問いの台帳がない |
| E16 | `/wiki:plan` | 一部。`lint --suggest-pages` が Gap Analysis の機械的な部分 | CQ の列挙と MOC への赤リンクはない |
| E17 | `/wiki:promote` | なし | 直前の検討が「欠けているのは source から知見へ昇格させる判定手順」と結論している。提案の promote は status の昇格で、中身が違う |
| E18 | `/wiki:lint --fix` | なし。`architecture.md` と `lint-workflow.md` は「検出するが修正しない」を契約にしている | 契約との衝突 |
| E19 | `/wiki:lint --relations` | 一部。`wiki_graph_lint.py` が型付きエッジの参照切れと値を検査 | 入れ子 `relations` を採らないので対象がない |
| E20 | 共通ルール 1〜8 | 1（raw 不変）、3（作る前に検索）、4（1 ページ 1 コンセプト）、7（log.md）は既にある。2 は `page.md.template` があるが「全フィールドを埋める」は任意項目と合わない。5、6、8 は差分 | 6（新規は `draft`、`promote` 経由でのみ昇格）は E07 と同じ理由で採らない |
| E21 | ingest の source ページの「主張の一覧」 | 一部。`ingest-workflow.md` 手順 5 の「主な主張」の節。作者の source ページは `## 主な主張` の箇条書き（Part 1）か、見出しなしの段落（SemaSynth の 28 本。`## ` の数は 0〜1） | 主張ごとの**行き先**の記録がない |
| E22 | Diátaxis「手順と概念を混ぜない」 | なし | 1 行の規約で足りる |
| E23 | Middle-out（lint 時に分類を再提案） | 一部。lint 手順 3 の内容確認。ただし分類の誤りを機械的に見つける検査はない | `index.md` の見出しと `type` の照合がない |
| E24 | KCS と出典必須を `status` で両立 | なし。`sources` は source 以外の全ページで必須（`SCHEMA.md`）。「気づかれない汚染」対策の要（`SKILL.md` 防ぐべき失敗 1） | `draft` に出典を免除すると汚染対策が崩れる。素早い記録は `log` プラグインと `50_Notes`（ADR-0008）、`/wiki:learn` が受け持つので、wiki 側で緩める必要がない |

### 2. 採点

基準と重み（W1 = 課題の既定）: 価値 25、整合 20、検査 20、手間 20、軽さ 15。合計 = Σ(点 × 重み) ÷ 100。
W2（価値重視）: 35 / 15 / 15 / 20 / 15。W3（安定重視）: 15 / 30 / 20 / 15 / 20。

| # | 要素 | 価値 | 整合 | 検査 | 手間 | 軽さ | W1 | W2 | W3 | 根拠（短く） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E23 | index の見出しと `type` の食い違いの lint、分類の再提案 | 7 | 9 | 8 | 9 | 8 | **8.15** | **8.00** | **8.30** | 実在の 16 件を今の lint が見逃す。検査は `index.md` の見出しと frontmatter の照合だけ |
| E21 | source の「主張の一覧」と行き先 | 9 | 8 | 7 | 6 | 7 | **7.50** | **7.65** | **7.45** | source 偏りへの直接の手当て。行き先スラッグの存在は検査できるが「再利用できるか」は LLM の判断 |
| E03 | 「問題が起きたら入れる」原則 | 6 | 9 | 5 | 9 | 9 | 7.45 | 7.35 | 7.75 | `scaling-playbook.md` の「先回りしない」と同じ思想。文書だけで入る |
| E15′ | `questions.md`（自動追記に変形） | 6 | 7 | 7 | 8 | 6 | 6.80 | 6.70 | 6.80 | 件数と経過日数は検査できる。作者の手間は増えない。スクリプトの skip 一覧の変更が要る |
| E18′ | `lint --fix`（機械的な修正に限定） | 6 | 5 | 9 | 8 | 5 | 6.65 | 6.55 | 6.40 | 検査性は最高だが「修正しない」契約を緩める |
| E07′ | `status` を claim 限定に変形 | 6 | 7 | 7 | 7 | 6 | 6.60 | 6.50 | 6.65 | 値の集合、`supported` の出典数、`superseded_by` の存在は検査できる。独立性は検査できない |
| E17′ | `/wiki:promote`（source → claim に変形） | 8 | 7 | 5 | 7 | 5 | 6.55 | 6.75 | 6.35 | 偏りの遡及的な解消に唯一効く。核の判断は LLM |
| E01 | 5 区分マップ（文書） | 4 | 8 | 3 | 9 | 9 | 6.35 | 6.20 | 6.75 | 枠組みであり機能ではない |
| E22 | 手順と概念を混ぜない | 4 | 8 | 4 | 8 | 9 | 6.35 | 6.15 | 6.80 | 作者の wiki に該当がなく、価値は将来のもの |
| E08′ | `broader` を平坦キーで（保留） | 5 | 7 | 8 | 6 | 5 | 6.20 | 5.95 | 6.35 | extract の変更が要る。150 ページ未満では効果がない |
| E20-8′ | 改名は被リンクの移し替えと一緒に | 3 | 5 | 8 | 7 | 8 | 5.95 | 5.60 | 6.20 | 既にスクリプトがある（`--backlinks`） |
| E10 | `type: howto` | 2 | 7 | 4 | 7 | 7 | 5.15 | 4.80 | 5.65 | 対象のページがない |
| E04 | `type` / `status` の一般的なモード切替 | 5 | 5 | 7 | 4 | 4 | 5.05 | 4.95 | 5.05 | 考え方は良いが全ページに status を書く手間が大きい |
| E16 | `/wiki:plan`、CQ の列挙 | 5 | 6 | 5 | 3 | 5 | 4.80 | 4.75 | 5.00 | 10〜30 問を作者が承認する手間 |
| E12 | `type: moc` | 2 | 5 | 5 | 6 | 6 | 4.60 | 4.30 | 4.90 | index と用語ページが兼ねる |
| E06 | `scope` | 4 | 2 | 7 | 5 | 5 | 4.55 | 4.50 | 4.35 | ADR-0008 と逆向き |
| E09 | `reviewed_at` | 2 | 5 | 7 | 3 | 7 | 4.55 | 4.15 | 5.05 | 値を決める人がいない |
| E02 | 8 コマンドへの分割 | 5 | 4 | 4 | 5 | 3 | 4.30 | 4.40 | 4.10 | 入口を増やすだけで中身は既存の 3 操作 |
| E19 | `lint --relations` | 2 | 3 | 6 | 7 | 4 | 4.30 | 4.05 | 4.25 | 対象が入らない |
| E24 | `draft` は出典なし可 | 3 | 2 | 6 | 6 | 5 | 4.30 | 4.20 | 4.15 | 汚染対策を崩す |
| E11 | `type: decision`、`/wiki:decide` | 3 | 3 | 5 | 5 | 5 | 4.10 | 4.00 | 4.10 | `70_ADR/` と source の二重化 |
| E05 | `id` | 1 | 3 | 8 | 5 | 3 | 3.90 | 3.45 | 4.00 | ファイル名と常に同値 |
| E14 | `type: graph` | 1 | 2 | 2 | 8 | 8 | 3.85 | 3.75 | 3.95 | 層をページ型と混同 |
| E07 | `status` 全ページ（draft / reviewed / canonical） | 4 | 4 | 5 | 2 | 3 | 3.65 | 3.60 | 3.70 | 全ページが `draft` のまま止まる見込み |
| E08 | 入れ子 `relations` | 3 | 2 | 3 | 4 | 2 | 2.85 | 2.90 | 2.65 | パーサーが読まない。ADR-0009 の二重化 |
| E13 | `type: journal` | 1 | 1 | 3 | 3 | 3 | 2.10 | 2.00 | 2.10 | ADR-0006 と衝突 |

**重みを変えても上位 3 つ（E23、E21、E03）は入れ替わるだけで動かない。** W3 では E03 が E21 を抜く。もっとも重みに敏感なのは `/wiki:promote` で、W2 で 4 位、W3 で 10 位になる。点数は採否の決め手にしておらず、上の表の「入れる合図」で決める。

### 3. 衝突と解き方

| 衝突 | 内容 | 解き方 |
| --- | --- | --- |
| ADR-0006 と `journal` | 日付ノートを wiki の型にすると孤立の指摘が毎日増える（ADR の背景、`wiki_lint.py` 349 行目の孤立判定） | **提案側を落とす。** ADR は変えない |
| ADR-0008 と `scope`、`decision`、`templates/<type>.md` | 作業領域はディレクトリで分け、ADR は `70_ADR/`、Foam の `.foam/templates/` は日付ノート用 | **提案側を変える。** `scope` は使わず、プロジェクト固有の source は `tags` で見分けるか、プロジェクトの wiki に置く。提案の `templates/<type>.md` に当たるものは `assets/page.md.template` と `SCHEMA.md` の種類ごとの構成であり、Foam のテンプレートとは別物として扱う |
| ADR-0009 と SKOS 風 `relations` | 型付きエッジは `ontology.yaml` で宣言し、証拠が必須。別系統の関係を frontmatter に足すと二重化する | **提案側を変える。** 入れ子は採らない。将来 `broader` を入れるなら、`sources:` → `sourced_from` と同じ暗黙エッジとしてオントロジーの中に 1 述語を足す。ADR は変えない |
| 方針 B と `id` | キーは英語、スラッグは日本語でよい | `id` はファイル名と常に同じになるので落とす。提案の「ファイル名と `id` を一致させる」は、スラッグが識別子である現行と実質同じ |
| 平坦な frontmatter | `relations`、入れ子の `evidence` はパーサーが読めない（直前の検討で 3 体が確認。今回も `_FM_KEY_RE` で確認） | 新しいキーは平坦に限る（`kind`、`status`、`superseded_by`、将来の `broader`） |
| 「改名しない」と日本語スラッグ、lint のマージ | lint は重複スラッグを「一方を正本にして被リンクを移し替える」で解く | 「改名は `wiki_search.py --backlinks` で被リンクを移し替えると同時に行う」に書き換える |
| `status` の語彙 | 3 系統が衝突 | claim ページは `experience-pattern` の 3 値に `disputed` を足した 4 値にそろえる。エッジの語彙は時点の有効性を表すもので、ページの証拠の状態とは別物として分けたままにする。提案の `reviewed` / `canonical` は判断する人がいないので採らない |
| 直前の検討の `kind: "claim"` | 直前の検討は「`status` の値、根拠の持ち方、グラフの移行」を未決にしていた | `status` は上の 4 値、根拠は本文の `## 根拠` 節（平坦キーで持たない）、グラフは `maps_from` 追加後に extract をやり直し、`concept:x` を目的語にする既存の明示エッジがあれば手で直す。作者の wiki には該当がない（`edges.jsonl` の述語は `authored` 5、`mentions` 229、`sourced_from` 32、`summarizes_raw` 37） |

**既存の ADR を変えるべきと判断したものはない。**

### 4. 導入する要素の詳細

**frontmatter のキーと値（英語。方針 B）**

| キー | 値 | 対象 | lint で検査すること |
| --- | --- | --- | --- |
| `kind` | `"claim"` | `type: "concept"` のうち主張の形のページ | `kind: "claim"` なら `status` が必須 |
| `status` | `"hypothesis"` / `"supported"` / `"disputed"` / `"superseded"` | `kind: "claim"` と `"experience-pattern"` | 値がこの集合にあるか。`supported` なら `sources` が 2 本以上。`superseded` なら `superseded_by` が存在するスラッグ。`disputed` なら本文に `## 矛盾` の見出し |
| `superseded_by` | `"<slug>"` | `status: "superseded"` のページ | リンク先の存在 |
| `concepts` | `["<slug>", ...]` | source ページ（既存の任意キー） | 挙げたスラッグが存在するか。新しいコード（今の lint は frontmatter のリストを被リンクに数えない） |

**`SCHEMA.md.template` と references の改訂の要点**

- `SCHEMA.md.template`「ページの種類」に `concept` の `kind: "claim"` を書く。オプトインの節として「主張ページを使う」を足し、`status` の 4 値と意味を表にする。「インデックスの構成」に「見出しの欄と `type` を一致させる。lint が検査する」を足す。
- `ingest-workflow.md` 手順 5: source ページの本文に `## 主張` の表を置く。列は「主張」「条件」「行き先」「ページ」。行き先は `create`（新しい claim ページ）、`update`（既存ページの節に追記）、`source_only`（進捗、1 回の数値、固有の属性）。frontmatter の `concepts:` に `create` と `update` の先を書く。
- `page-conventions.md`: 「手順と概念を同じページに混ぜない。手順が主のページを作るときは `SCHEMA.md` に種類を足してから作る」の 1 行。「改名は被リンクの移し替えと同時に行う」の 1 行。
- `lint-workflow.md` 手順 1 に `index_type_mismatch` と `invalid_status` を追加。手順 4 に `questions.md` の未回答の件数と経過日数を足す（段階 3a）。
- `query-workflow.md` 手順 7: 「wiki に内容がない」と答えたとき `questions.md` に `- [ ] YYYY-MM-DD <問い>` を 1 行追記する（段階 3a）。

**コマンドを足すなら**

- `/wiki:promote <source-slug> [<source-slug> ...]`: 入力は source ページのスラッグ。処理は `## 主張` の表（なければその場で作る）を読み、`create` の行ごとに `concepts/<主張の文>.md` を `kind: "claim"`、`status: "hypothesis"` で作り、source と用語ページから被リンクを張り、`index.md` の「コンセプト」に 1 行足し、`log.md` に `## [YYYY-MM-DD] promote | <source の題名>` を書く。出力は作ったページ、更新したページ、`source_only` に残した理由の一覧。既存の同じ主張があれば作らず `update` に落とす（対象、条件、肯定か否定か、断定の強さで照合。直前の検討 6.3）。

**作者の wiki の実在ページでの frontmatter の例（ファイルは書かない）**

`concepts/編集要求の復元世代を最終適用まで保持する.md`（段階 2 で `kind` と `status` を足す。`sources` が 1 本なので `hypothesis`）:

```yaml
---
type: "concept"
kind: "claim"
status: "hypothesis"
title: "編集要求の復元世代を最終適用まで保持する"
sources: ["output復元資格の設計-2026-11-04"]
created: 2026-11-04
updated: 2026-11-08
tags: ["並行処理"]
---
```

`sources/semasynth再現性の検証-2026-11-06.md`（段階 1 で本文に `## 主張` を足し、段階 2 の promote で `concepts:` を埋める。frontmatter の他のキーは変わらない）:

```yaml
---
type: "source"
title: "SemaSynth 再現性の検証"
authors: ["Codex"]
raw: "../W1_Raw/semasynth再現性の検証-2026-11-06.md"
ingested: 2026-11-06
created: 2026-11-06
updated: 2026-11-08
tags: ["知識表現"]
concepts: ["同一環境と異なる環境では再現性の判定を分ける"]
---
```

本文の `## 主張` の表の例:

| 主張 | 条件 | 行き先 | ページ |
| --- | --- | --- | --- |
| 再現性の判定は同一環境ではバイト一致、異なる環境では値と型の一致で行う | 配布形態が Git を含まない場合は環境情報が null になる | `create` | `同一環境と異なる環境では再現性の判定を分ける` |
| 再生成の比較と、基準 manifest による改変検出は目的が別 | なし | `update` | `semasynth会計データの再検証-2026-11-06` の節 |
| 処理時間とピーク常駐メモリを保存する | 少数回の測定から保証値を決めない | `source_only` | なし |

新しい `concepts/同一環境と異なる環境では再現性の判定を分ける.md`:

```yaml
---
type: "concept"
kind: "claim"
status: "hypothesis"
title: "同一環境と異なる環境では再現性の判定を分ける"
sources: ["semasynth再現性の検証-2026-11-06"]
created: 2026-11-08
updated: 2026-11-08
tags: ["手法"]
---
```

`questions.md`（段階 3a）の行の例: `- [ ] 2026-11-08 Tantivy の commit の失敗はウイルス対策の走査が原因か` と、答えたら `- [x] 2026-11-08 ... → [[Windows での Tantivy の commit の失敗]] 2026-11-20`。

**lint で機械的に検査できるものと LLM に頼るもの**

| 機械的 | LLM の判断 |
| --- | --- |
| index の見出しと `type` の食い違い、`status` の値、`supported` の出典数、`superseded_by` と `concepts:` の存在、`## 主張` の表の有無、`questions.md` の未回答数と経過日数、`broader` の循環 | 主張を `create` / `update` / `source_only` に振り分ける、同じ主張かどうか、出典が「独立」か、手順と概念が混ざっているか、分類の再提案 |

### 5. 提案自体の誤りや不整合（採否には影響させていない）

- コマンドの数: 「8 コマンド」と書くが、表には 6 個しかなく、`/wiki:graph` を足しても 7 個。
- 表記: `/wik:lint`（`/wiki:lint`）、`/wiki promote`（`/wiki:promote`）、`<pathっurl>`（`<path|url>`）、`syntesis`（`synthesis`）。
- `/wiki:plan` の手順 4 が「ingest か answer で埋める」と書くが、`answer` というコマンドは定義されていない。
- `type` の候補に `graph` と `journal` が入っている。`graph` は層であってページの種類ではなく、`journal` は提案自身が「日誌とプロジェクトを足す」とディレクトリの話として扱っている。
- スキーマの置き場所: ディレクトリ構成では「3 層（raw / wiki / schema）」と書くが、フェーズ 0 では「CLAUDE.md にスキーマと共通ルールを書く」としている。
- `answers` が `relations` の下にありながら、フィールドの表では独立した行になっている。
- 「導入フェーズ · 4 段階と 3 つの移行条件」の図は失われている。ロードマップの 4 フェーズと、その間の 3 つの開始条件がそれにあたると仮定した。
- `/wiki:promote` の入力「記事 id」と、ingest の出力「concept / entity ページ（draft）」から、新規ページがすべて draft で始まり promote で上がる設計だと読めるが、「KCS vs 出典必須」の表では draft が出典なしでよいとしており、ingest の手順 4「`sources` にソース id を追加」と食い違う。

## 検討した代替案

| 採らなかった案 | 理由 |
| --- | --- |
| 提案どおり全ページに `status: draft` を付け、`reviewed` 以上を promote 経由にする | `reviewed` を判断する人が運用にいない（wiki は LLM が書き、作者はソースと質問を受け持つ。`architecture.md`「wiki の層を LLM が受け持つ理由」）。全ページが `draft` に留まり、フィールドが意味を失う |
| `status` の語彙をグラフのエッジ（`current` / `proposed` / `disputed` / `superseded`）に合わせる | エッジの `current` / `historical` は時点の有効性で、ページの証拠の状態と意味が違う。`experience-pattern` との二重語彙も残る |
| `relations` を入れ子のまま入れ、PyYAML で読む | `wiki_text.py` を使う lint・search・stats の全部が読めず、`graph:` と同じ例外を増やす。ADR-0009 の「グラフは任意の索引」と、frontmatter に関係を二重に持つ形がぶつかる |
| `scope` でユーザースコープ wiki の中のプロジェクト知識を見分ける | ADR-0008 がディレクトリで分けると決めている。作者の wiki に SemaSynth が 28 本あるのは `scope` を足して解く問題ではなく、置き場所の問題（下の「前提と不確実性」） |
| `/wiki:decide` と `type: decision` | ADR は人が `70_ADR/` に書く（ADR-0008）。wiki への反映は `/wiki:ingest` で source になり、再利用できる判断は claim に昇格する。作者の wiki が既にこの形で動いている |
| `/wiki:plan` を今入れる | 作者の wiki はボトムアップで育っており、「網羅したい領域」の表明がない。提案自身も「問いが立てられないうちは使わない」と書いている |
| `kind: "claim"` を既定にして全利用者に配る | 直前の検討が「モデルが変わっても同じページ割りになる」ことを示せていない。オプトインで PoC を待つ |
| 「主張の一覧」を frontmatter の平坦キー（`claims: [...]`）で持つ | 条件と行き先の理由を書けない。本文の表のほうが人が読め、`concepts:` の既存キーで行き先の存在だけを検査できる |
| `lint --fix` を内容の修正まで広げる | 「黙って書き換えない」契約（`architecture.md`、`lint-workflow.md`）が崩れる。機械的な書き損じに限り、差分の承認を挟む |
| `index.md` の分類誤りを LLM の内容確認に任せる | 直前の検討で B が lint を走らせて 0 件、すなわち LLM の確認でも見逃されてきた。機械的な検査にする |

## 前提と不確実性

- **ページ数。** 課題の文では 56 ページだが、`W0_Wiki/` を数えると source 37、concept 17、entity 1、synthesis 2 の 57 ページだった。差の 1 本は 2026-11-08 に保存された synthesis「wikiの記事の単位とatomic-notesとevergreen-notes」と推測する。
- **source の偏りは置き場所の問題を含む。** ADR-0008 は「ユーザースコープの作業領域にはプロジェクト固有の情報を置かない」と決めているが、作者のユーザースコープ wiki の source 37 本のうち 28 本は SemaSynth の記録である。段階の完了やテスト件数は、直前の検討も `log` プラグイン（ADR-0006）の対象かもしれないと書いている。これらをプロジェクトの wiki（`<semasynth>/wiki/`）か `50_Notes` に移すか、ユーザースコープに残して `tags` で見分けるかは、作者の判断が要る。本書の提案（主張の一覧、promote）は、どちらを選んでも効く。
- **PoC は未実施。** `/wiki:promote` と `kind: "claim"` の導入条件にした「配置先の一致率」の PoC は、直前の検討の提案値（一致 85%、F1 0.90、重複 0）のままで、達成の見込みは分からない。
- **lint を作者の wiki に実行していない。** 読むだけに留めた。「今の lint が 16 件の分類誤りを見逃す」は直前の検討の B の実測に依存している。
- **`questions.md` の skip 一覧。** `wiki_lint.py` の `SKIP_TOP_LEVEL_FILES` と `wiki_graph_extract.py` の `SKIP_TOP_LEVEL_DIRS` は確かめたが、`wiki_search.py`、`wiki_stats.py`、MCP サーバーの `wiki_index.py` がルート直下のファイルをどう扱うかは確かめていない。段階 3a の実装では全スクリプトを見る必要がある。
- **Foam のリンク解決。** 提案の「Foam の `[[id]]`」は、Foam がファイル名でリンクを解く前提と読んだ。Foam の文書で確かめていない。
- **失われた図。** 「4 段階と 3 つの移行条件」はロードマップの 4 フェーズとその間の 3 条件と仮定した。
- **基準と重みへの異議。** 直前の検討と同じく、「既存設計との整合」と「実装と移行の軽さ」で 35 の重みがあり、文書だけで入る要素（E01、E03、E22）が機能より高く出る。「検査可能性」は `id` や `reviewed_at` のような価値の低いフィールドにも 7〜8 点を与えるので、検査できることと役に立つことを分けて読む必要がある。出典への忠実さは加重点ではなく必須条件として扱った（`draft` の出典免除を点数にかかわらず落とした理由）。

## 参照

リポジトリ（`C:\Works\info-hive-dev\`）:

- `AGENTS.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`（3 層と 3 操作、スケーラビリティの規律、防ぐべき失敗 1「気づかれない汚染」）
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`（手順 4〜7、手順 5 の frontmatter に `entities:`・`concepts:`）、`page-conventions.md`（frontmatter、命名、本文の構成）、`architecture.md`（26 行目の種類の追加、「wiki の層を LLM が受け持つ理由」）、`lint-workflow.md`（「検出結果を報告するが、修正はしない」）、`query-workflow.md`（手順 7、保存の判断）、`graph-workflow.md`（57・65・68・110 行目）、`scaling-playbook.md`（閾値 1〜5）、`evolution-workflow.md`
- `info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template`、`ontology.yaml.template`（`claim: explicit_only: true`）、`page.md.template`、`pattern.md.template`（`status: "hypothesis"`）、`index.md.template`
- `info-hive-wiki/commands/ingest.md`、`query.md`、`lint.md`、`graph.md`、`init.md`、`upgrade.md`、`learn.md`、`evolve.md`、`stats.md`、`help.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（126〜127 行目の skip 一覧、245 行目の本文 wikilink のみの収集、278 行目 `DEFAULT_REQUIRED_FM`、349 行目の孤立判定。`status` の検査なし）、`wiki_text.py`（180〜300 行目の平坦な frontmatter パーサー）、`wiki_graph_extract.py`（`build_edges` の `sources:` と `raw:` からの暗黙エッジ、`derive_node_type`）、`wiki_graph_lint.py`（`ALLOWED_STATUS`、`orphan_typed_nodes`）、`wiki_stats.py`
- `info-hive-wiki/.claude-plugin/plugin.json`（0.6.0）、`CHANGELOG.md`、`UPSTREAM.md`
- `docs/adr/0006-daily-journal-is-separate-plugin.md`、`0008-numbered-workspace-layout.md`、`0009-graph-layer-stays-in-wiki.md`、`0010-wiki-browse-separates-core-from-delivery.md`（冒頭のみ）
- `docs/research/wiki-note-granularity-2026-11-08.md`、`docs/agent-runs/2026-11-08-wiki-note-granularity-atomic-evergreen/summary.md`

作者の wiki（`D:\Users\toshiki\info-hive\W0_Wiki\`。読むだけ）:

- `SCHEMA.md`、`index.md`（104 行。「シンセシス」の欄に source 16 本）、`log.md`
- `concepts/オントロジー.md`、`編集要求の復元世代を最終適用まで保持する.md`、`BM25 の IDF の式の違い.md`、`Windows での Tantivy の commit の失敗.md`
- `sources/part-1-what-is-an-ontology-classes-properties-and-axioms.md`、`semasynth再現性の検証-2026-11-06.md`、`semasynth汎用コア分離g1-2026-11-07.md`
- `entities/yuan-an.md`（`authored` エッジ 5 本）
- `synthesis/LLM Wiki で蓄積した情報の活用方法.md`、`wikiの記事の単位とatomic-notesとevergreen-notes.md`
- `graph/ontology.yaml`、`graph/README.md`、`graph/edges.jsonl`（述語の内訳: `authored` 5、`mentions` 229、`sourced_from` 32、`summarizes_raw` 37）
- `../W1_Raw/` の一覧、`../.info-hive/workspace.json`（存在しない）

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```

### エージェント C

## 結論

**提案は、現行の wiki を置き換える設計としては採らず、記事の発見・配置・検査を改善する手法として、選んで導入する。承認済みの ADR は変更しない。**

最初に取り組むものは次の 3 つとする。

1. **索引の分類検査**：作者の wiki では、`source` 16 本が「シンセシス」に分類されている。実在する誤りを機械的に検出できる。
2. **出典参照の検査**：規約にある出典必須を、`sources` → source ページ → `raw` の参照検査として実装する。
3. **source の「主張と配置先」の小規模 PoC**：主張を列挙するだけで終わらせず、用語ページ内の節・独立した主張ページ・source 内のいずれに置くかを試す。

| 判定 | 対象 |
|---|---|
| **導入する** | 5 区分の方法論マップを説明用に使う。既存記事の検索と更新、raw の確定後の不変性、変更時のログ、Markdown を正本とする運用を維持する。出典参照と索引分類の lint を補う |
| **変えて導入する** | きっかけ別の入口、問題の発生に応じた段階導入、`type`・`kind` 別の構造検査、Atomic／Evergreen、source の主張一覧、Diátaxis、Middle-out、MOC、Competency Questions、KCS。詳細は以下 |
| **導入しない** | 全ページへの `id`・`scope`・共通 `status` の必須化、入れ子の `relations`、`type: decision|journal|graph` の標準追加、正典ページの直接更新禁止、全件 draft 化、リンク方向の一方向固定、`/wiki:graph` の撤去、重複する `--relations`、DITA・OWL の全面導入 |
| **保留** | `/wiki:plan`、`/wiki:promote`、`reviewed_at`、手順ページ専用の形式、限定的な `/wiki:lint --fix`、Progressive Summarization の追加工程。利用上の問題と検証結果を導入条件にする |

ここでいう「導入する」には、既存の有効な規約を維持する判断を含む。**既存機能を残す判断と、新規実装の優先順位は別である。**

## 根拠

### 1. 現状の確認

作者の wiki を、`sources/`、`concepts/`、`entities/`、`synthesis/` の Markdown の `type` で再集計した結果は次のとおりだった。

\[
37+17+1+2=57\text{ページ}
\]

| `type` | ページ数 |
|---|---:|
| `source` | 37 |
| `concept` | 17 |
| `entity` | 1 |
| `synthesis` | 2 |

「既存の 56 ページ」という記述は、直前の検討結果を保存する前の集計と考えられる。今回確認した実体は 57 ページである。`indexes/` はなく、`index.md` が全ページの索引になっている。

`index.md` の「シンセシス」には、実際には `type: "source"` のページが 16 本並んでいる。該当箇所は 74、76、78、80、82、84、86、88、90、92、94、96、98、100、102、104 行である。これは名称の揺れではなく、索引の分類と frontmatter の不一致である。

現行の `wiki_lint.py` は、通常ページの本文にある wikilink、必須 frontmatter、サイズ、日付などを検査するが、索引見出しとページの `type` の対応は検査しない。また、既定の必須キーは `type,title,tags,created,updated` であり、source 以外の `sources` 必須や、参照先の種類までは検査していない。**規約として存在することと、スクリプトで検査できることには差がある。**［P3「frontmatter」、P8 `DEFAULT_REQUIRED_FM`・`lint`］

### 2. 要素の分解と現行との差分

採点表と対応させるため、要素に番号を付けた。「ある」は内容上の対応を確認したものを指し、コマンド名が同じだけの場合は含めない。

| ID | 提案の要素 | 現行 | 採否・差分と導入条件 |
|---|---|---|---|
| 01 | 5 区分の方法論マップ | 一部 | **導入**。説明と設計レビューの見取り図に使う。毎回 5 区分を処理する手順にはしない |
| 02 | きっかけごとにコマンドを分ける | 一部 | **変更**。既存の `ingest/query/learn/lint` を案内表で整理する。入口追加は手順が既存コマンドで表現できなくなった場合 |
| 03 | 成熟度フェーズと移行条件 | 一部 | **変更**。wiki 全体を一段階に分類せず、分類・問い・レビュー・グラフを独立に有効化する |
| 04 | `type` と `status` による lint の切替え | 一部 | **変更**。まず既存の `type`・`kind` に応じた検査。共通 `status` は導入しない |
| 05 | `id` を追加し、ファイル名と一致・固定 | ない | **不採用**。既にスラッグが識別子。重複する値と整合検査が増える |
| 06 | `scope: common|project:<name>` | ない | **不採用**。作業領域で分離する。ページ属性は保存先の境界を保証しない |
| 07 | 全ページ共通の `status` | 一部 | **不採用**。既存の `experience-pattern` の `status` と意味・値が異なる |
| 08 | `relations.broader` | ない | **不採用**。分類上の親は当面、索引の見出し・リンクで表す。意味的な上下関係が必要なら既存グラフで別途定義 |
| 09 | `relations.related` | 一部 | **不採用**。本文リンクと既存 `mentions` に対する追加価値が小さい。意味的な関係と単なる参照も混同しやすい |
| 10 | `relations.answers` | ない | **変更**。CQ 台帳から回答箇所へリンクする。一方向を正本とし、ページ側に同じ対応を二重記入しない |
| 11 | `reviewed_at` | ない | **保留**。レビュー責任者、対象版、変更後の失効規則が必要 |
| 12 | `type: howto` | ない | **保留・変更候補**。まず必要な手順を独立した回答ページにする。専用形式が必要なら `synthesis` の `kind: "howto"` を試す |
| 13 | `type: decision` | グラフ型のみある | **不採用**。ADR はプロジェクト側の正本に置き、wiki は source として取り込む。グラフのノード型はページ型の実装済みを意味しない |
| 14 | `type: moc` と MOC | 索引がある | **変更**。MOC の役割は既存の `index.md`・分割索引・話題別のリンク集で実現する。新しい `type` は不要 |
| 15 | `type: journal` | ない | **不採用**。ADR-0006 に反する。日付ノートと wiki の操作ログも別物 |
| 16 | `type: graph` | グラフ層がある | **不採用**。グラフはページの種類ではなく派生索引 |
| 17 | `questions.md`、Competency Questions、Gap Analysis | 未解決の問い・不足提案が一部ある | **変更**。実際の問いを少数登録し、回答基準を付ける。未知の分野に 10〜30 問を自動生成することは既定にしない |
| 18 | `/wiki:plan` | ない | **保留**。CQ 台帳による手動運用で価値を確認してから追加 |
| 19 | `/wiki:decide` | ない | **不採用**。意思決定の正本管理を wiki に重複実装しない。既存 `wiki_decide.py` は判定モデル用であり別機能 |
| 20 | `/wiki:promote` | ない | **保留**。主張の独立化と、内容のレビュー承認を別の操作として設計し直す必要がある |
| 21 | `/wiki:lint --fix` | ない | **保留・限定採用候補**。意味を変えない修正だけ。内容統合・分類判断・状態昇格は対象外 |
| 22 | `/wiki:lint --relations` | グラフ lint がある | **不採用**。既存 `/wiki:graph lint` と MCP `lint` のグラフ結果を使う |
| 23 | 共通ルール1：raw は読むだけ | ある | **維持**。新規保存・取得時の加工と、確定後の不変性を区別する。PDF の参照運用も維持 |
| 24 | 共通ルール2：テンプレートと全フィールド必須 | 一部 | **変更**。型に必要な項目だけ埋める。source に `sources`、一般ページにレビュー情報を強制しない |
| 25 | 共通ルール3：既存検索・SSOT | ある | **維持**。同じ名前だけでなく、条件と適用範囲を読んで統合を判断する |
| 26 | 共通ルール4：1 記事1概念、またがれば分割 | 一部 | **変更**。直前の結論に従い、条件・根拠・範囲を同じ場所で更新できる判断を単位にする |
| 27 | 共通ルール5：手順と概念を混ぜない | ない | **変更**。独立して利用する長い手順を分ける。短い例や必要条件まで追い出す絶対規則にはしない |
| 28 | 共通ルール6：全件 draft、昇格専用経路 | ない | **不採用**。現行の取り込み時の既存ページ更新を妨げ、毎回のレビュー待ちを作る |
| 29 | 共通ルール7：すべての操作をログへ | 一部 | **変更**。変更と重要な保守結果を記録する。検索・閲覧まで毎回追記しない |
| 30 | 共通ルール8：`[[id]]`、改名禁止 | 一部 | **変更**。既存の日本語スラッグと `[[slug]]` を維持。改名は被リンクとグラフを直す管理操作として許す |
| 31 | source に主張一覧を作る | 主な主張を要約する規約がある | **変更**。「主張・条件・根拠箇所・配置先・理由」の短い表にする。source の偏りに対する PoC を先行 |
| 32 | ingest の一連の手順 | 多くがある | **変更**。既存の対話、影響範囲の確認、部分更新、被リンク、矛盾並記、グラフ更新を保持する |
| 33 | Middle-out で分類を提案する | 手動の分類・分割がある | **変更**。探索失敗や分類の不一致を合図に候補をまとめて提案。毎回の lint で再分類しない |
| 34 | KCS と出典必須を状態で両立 | `query`・`learn` に一部ある | **変更**。利用時に改善する原則を採る。出典なしの推測を wiki の事実ページに流入させない |
| 35 | 出典を lint で検査 | 規約はあるが通常 lint は不足 | **導入**。型別の必須項目、`sources` の参照先と型、`raw` の参照を検査 |
| 36 | グラフはスクリプトなので Skill の外へ | スクリプトとコマンドがある | **変更**。実処理はスクリプト、入口は `/wiki:graph` を維持する |
| 37 | Progressive Summarization | source 要約はある | **保留**。既存の要約に加えて段階的な強調工程を持つ利益が未確認 |
| 38 | DITA | ない | **不採用**。複数成果物への構造化再利用の要求が確認できない |
| 39 | OWL・完全なオントロジー | ない | **不採用**。現在の任意索引を越える推論基盤は今回の問題を解かない |
| 40 | Docs as Code | Git と Markdown を利用 | **維持**。差分確認を使う。個人 wiki の毎回の取り込みに PR・CI を要求しない |
| 41 | source から概念へのリンク方向を固定 | 双方向の参照がある | **不採用**。概念の `sources` と本文から出典へ戻る経路を維持する |
| 42 | 索引分類を機械的に検査 | ない | **導入**。提案の索引更新・分類維持を現状に合わせて補う。既に 16 件の具体例がある |

現行対応の根拠は、取り込みが P2、ページと出典の規約が P3、query が P4、lint が P5・P8、グラフが P6・P10、経験学習が P7 である。

### 3. 採点と感度分析

**点数は実測された効果ではなく、コード・規約・作者のページを根拠にした設計上の評価である。** 特に LLM の意味判断に依存する効果は未検証として減点した。

- `価`：利用者が得る価値
- `整`：既存設計との整合
- `検`：検査可能性
- `手`：運用の手間の少なさ
- `軽`：実装と移行の軽さ

重みは次の 3 通りとした。

| 重み | 価 | 整 | 検 | 手 | 軽 |
|---|---:|---:|---:|---:|---:|
| 基本 B | 25 | 20 | 20 | 20 | 15 |
| 価値重視 V | 40 | 15 | 15 | 20 | 10 |
| 整合・検査重視 C | 15 | 25 | 25 | 15 | 20 |

計算式は、例えば ID42 なら次のとおりである。

\[
B=(9\times25+10\times20+10\times20+9\times20+9\times15)/100=9.40
\]

変更採用する要素は、**上表に示した変更後の案**を採点した。不採用の要素は原案を採点した。したがって「原案と修正版の効果差を実証した表」ではない。

| ID・要素 | 価 | 整 | 検 | 手 | 軽 | B | V | C | 点数の主な根拠 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 42 索引分類 lint | 9 | 10 | 10 | 9 | 9 | **9.40** | 9.30 | 9.50 | 16 件の実在する分類誤りを検出可能 |
| 35 出典参照 lint | 8 | 10 | 10 | 9 | 8 | **9.00** | 8.80 | 9.15 | 既存規約と実装の不足を埋める |
| 29 変更時ログ | 5 | 10 | 9 | 9 | 10 | 8.35 | 7.65 | 8.85 | 既存運用を軽く保てる |
| 14 既存索引による MOC | 7 | 10 | 8 | 8 | 9 | 8.30 | 8.00 | 8.55 | 新型なしで探索経路を改善 |
| 31 主張・配置表 | 10 | 9 | 6 | 8 | 8 | 8.30 | 8.65 | 8.05 | source 偏重に直接対応。ただし意味判断 |
| 36 graph 入口維持 | 4 | 10 | 10 | 9 | 10 | 8.30 | 7.40 | 8.95 | 既存の使える入口を維持 |
| 04 型別 lint | 8 | 9 | 9 | 8 | 7 | 8.25 | 8.20 | 8.30 | 必須項目の機械検査を増やせる |
| 32 既存 ingest 維持 | 6 | 10 | 6 | 10 | 10 | 8.20 | 7.80 | 8.40 | 二段階承認を増やさず統合できる |
| 30 slug・wikilink | 4 | 9 | 10 | 9 | 10 | 8.10 | 7.25 | 8.70 | 新 ID が不要 |
| 23 raw 不変 | 3 | 10 | 9 | 10 | 10 | 8.05 | 7.05 | 8.70 | 既存の基礎的な保護 |
| 34 利用時改善・根拠保持 | 8 | 9 | 6 | 8 | 9 | 7.95 | 7.95 | 7.95 | 利用価値に沿うが意味判断は残る |
| 03 問題別フェーズ | 6 | 9 | 7 | 9 | 9 | 7.85 | 7.50 | 8.05 | 不要な工程を導入せずに済む |
| 40 Docs as Code | 4 | 10 | 9 | 8 | 9 | 7.75 | 6.95 | 8.35 | 既存の差分管理を利用 |
| 24 型別テンプレート | 5 | 9 | 9 | 8 | 8 | 7.65 | 7.10 | 8.05 | 不要項目の記入を避ける |
| 26 条件付き粒度 | 9 | 9 | 5 | 7 | 8 | 7.65 | 7.90 | 7.50 | 価値は高いが配置判断は未検証 |
| 17 CQ 台帳 | 8 | 9 | 6 | 7 | 8 | 7.60 | 7.65 | 7.60 | 問いから不足を特定。ただし網羅性判断 |
| 01 方法論マップ | 5 | 10 | 5 | 9 | 10 | 7.55 | 7.05 | 7.85 | 説明は改善するが直接成果は小さい |
| 25 SSOT 検索 | 5 | 10 | 5 | 9 | 10 | 7.55 | 7.05 | 7.85 | 重複予防はあるが意味同一性は判断 |
| 02 きっかけ別入口 | 6 | 9 | 6 | 8 | 9 | 7.45 | 7.15 | 7.65 | 案内を改善。新コマンドの利益は未確認 |
| 10 CQ と回答の対応 | 6 | 8 | 9 | 7 | 7 | 7.35 | 7.05 | 7.60 | 参照の存在は検査可能 |
| 33 Middle-out | 7 | 9 | 5 | 7 | 9 | 7.30 | 7.20 | 7.40 | 分類の妥当性は LLM・作者判断 |
| 27 手順と概念の分離 | 6 | 9 | 5 | 8 | 9 | 7.25 | 7.00 | 7.40 | 目的別に読む利益。完全検査は困難 |
| 18 `/wiki:plan` | 7 | 9 | 6 | 7 | 7 | 7.20 | 7.15 | 7.25 | 有望だが既存 query との差が未検証 |
| 12 howto 形式 | 6 | 8 | 6 | 8 | 8 | 7.10 | 6.90 | 7.20 | 必要時の独立化には価値 |
| 21 限定 `--fix` | 6 | 6 | 9 | 8 | 5 | 6.85 | 6.75 | 6.85 | 修正器と失敗時の保護が必要 |
| 22 `--relations` 追加 | 2 | 8 | 9 | 7 | 9 | 6.65 | 5.65 | 7.40 | 実装は軽いが既存入口と重複 |
| 11 `reviewed_at` | 4 | 7 | 8 | 4 | 6 | 5.70 | 5.25 | 6.15 | 日付の検査とレビューの妥当性は別 |
| 37 Progressive Summarization | 3 | 8 | 5 | 5 | 8 | 5.55 | 4.95 | 6.05 | 要約後の追加工程の利益が不明 |
| 20 `/wiki:promote` | 5 | 5 | 6 | 3 | 4 | 4.65 | 4.65 | 4.75 | 昇格の意味と責任が未定義 |
| 05 `id` 追加 | 2 | 3 | 10 | 5 | 3 | 4.55 | 4.05 | 4.90 | 一致検査は容易だが冗長 |
| 13 `type: decision` | 4 | 3 | 7 | 4 | 4 | 4.40 | 4.30 | 4.50 | ADR 正本を二重化 |
| 09 `relations.related` | 3 | 2 | 7 | 4 | 4 | 3.95 | 3.75 | 4.10 | 既存リンク・グラフと重複 |
| 19 `/wiki:decide` | 3 | 3 | 6 | 3 | 4 | 3.75 | 3.55 | 3.95 | wiki 外の責務を増やす |
| 41 一方向リンク固定 | 2 | 2 | 8 | 4 | 3 | 3.75 | 3.40 | 4.00 | 出典に戻る既存経路を損なう |
| 06 ページ `scope` | 4 | 2 | 4 | 3 | 5 | 3.55 | 3.60 | 3.55 | 保存境界の代わりにならない |
| 08 `relations.broader` | 4 | 2 | 5 | 3 | 3 | 3.45 | 3.55 | 3.40 | 第二の関係モデルを作る |
| 07 全ページ `status` | 5 | 2 | 5 | 2 | 2 | 3.35 | 3.65 | 3.20 | 値の衝突と全件の状態管理 |
| 16 `type: graph` | 2 | 2 | 7 | 3 | 3 | 3.35 | 3.05 | 3.60 | 派生索引を記事型に混在 |
| 39 OWL 全面導入 | 3 | 2 | 7 | 2 | 1 | 3.10 | 3.05 | 3.20 | 現在の課題に対して過大 |
| 38 DITA | 2 | 2 | 8 | 2 | 1 | 3.05 | 2.80 | 3.30 | 構造化再利用の需要が未確認 |
| 28 全件 draft・専用昇格 | 4 | 2 | 4 | 2 | 2 | 2.90 | 3.10 | 2.80 | 取り込みごとの判断待ちを増やす |
| 15 `type: journal` | 2 | 1 | 7 | 2 | 2 | 2.80 | 2.60 | 3.00 | 承認済みの責務分離に反する |

**感度分析の結果**：新規作業の最優先である索引分類と出典検査は、3 通りすべてで 1・2 位だった。主張・配置表は価値重視で上がり、整合・検査重視で下がる。これは意味判断の未検証部分を反映している。

一方、既存ログや graph 入口維持の順位は大きく変わる。これらは「維持するか」の判断であり、得点が高くても新しい開発作業を先に発生させる理由にはならない。`--relations` も C で 7.40 まで上がるが、重複する入口を増やす必要はない。

0.05〜0.25 程度の差は、素点 1 点の変更で容易に逆転する。小差から採否を決めず、依存関係と PoC を優先する。

### 4. 衝突と解き方

| 衝突 | 判断と解決 |
|---|---|
| **ADR-0006 と `journal`** | **提案側を変更する。** 日付ノート・タスクは `log`。ノウハウの抽出は `50_Notes` を経て、利用者が `ingest` を選ぶ既定を維持する。日誌全体の自動取り込みはしない |
| **ADR-0008 と `scope`** | **提案側を変更する。** ユーザーとプロジェクトは作業領域で分ける。`scope: common` を付けても、プロジェクト固有情報が共通知識にはならない |
| **ADR-0008 と `decisions/`・テンプレート** | **提案側を変更する。** ADR は設定されたプロジェクトの ADR 領域に置く。Foam テンプレートは作業領域の根。wiki 内の `templates/` を全テンプレートの新しい正本にしない |
| **ADR-0009 と `relations`** | **入れ子の新設をしない。** 人がたどる分類は索引、意味的関係は既存 `graph.relationships` に分ける。後者には既存どおり出典・引用・確信度・状態を要求する |
| **方針 B** | 英語キー・英語の識別値、日本語本文を維持する。文字列は二重引用符、日付は `YYYY-MM-DD`。新項目を正式採用する場合は、書き出す英語名と読み取り別名を定義する |
| **平坦な frontmatter** | 通常パーサーを維持する。`relations` の入れ子を通常 lint に読ませるための YAML 全面移行はしない。グラフの入れ子は既存の専用パーサーの責務 |
| **スラッグと `id`** | 既存のスラッグを識別子として使う。日本語スラッグは維持する。改名は関連参照を更新する操作として許し、「永久に改名不可」は採らない |
| **既存 `status`** | `experience-pattern` の `hypothesis|supported|superseded` と、エッジの `current|historical|proposed|disputed|superseded` を維持する。ページレビューの意味を上書きしない |
| **直前の `kind: "claim"`** | 主張の独立化はこの案を前提にする。一般的な取り込みから `experience-pattern` を作らず、`learn` の観測証拠の契約を保つ |
| **正典化と ingest の既存更新** | 「正典は直接更新しない」は採らない。取り込みは出典付きで既存ページを部分更新する。別途レビュー制度を入れる場合も、編集可能性とレビュー済み表示を分離する |

通常の frontmatter パーサーは、入れ子を読まず空の配列として扱うことを明記している。一方、グラフ抽出は PyYAML を使う。したがって、**「グラフが YAML を読めるから、新しい `relations` も既存 lint が検査できる」という推論は成立しない。**［P9 `parse_frontmatter_text`:281–298、P10 `parse_frontmatter`:149–167］

`kind: "claim"` を追加しただけでは、現在のオントロジーでは引き続き `concept` ノードになる。`claim` の `maps_from` を追加するとノード ID が `concept:<slug>` から `claim:<slug>` に変わる可能性がある。さらに `depends_on` の主語・目的語には現在 `claim` が含まれていない。**本文の粒度改善とグラフの型変更は、別の移行として扱う。**［P10 `derive_node_type`:238–258、P11 `node_types`・`depends_on`］

既存 ADR を変更すべき根拠は、今回の提案にはない。

### 5. 導入後の具体的な仕様

#### frontmatter は最小限にする

当面の標準は次のままとする。

| 対象 | キー・値 |
|---|---|
| 全ページ | `type`、`title`、`tags`、`created`、`updated` |
| source | `type: "source"`、`authors`、`raw`、`ingested`。URL がある場合だけ `url` |
| source 以外 | 根拠となる source ページのスラッグを `sources` に記録 |
| 選別した主張ページ | `type: "concept"`、`kind: "claim"`。適用条件・根拠・留保は本文 |
| 経験パターン | 既存の `kind: "experience-pattern"` と、その専用 `status` |
| 保存した回答 | `type: "synthesis"`、任意で `question`、`asked`、`sources_consulted` |

`id`、ページの `scope`、共通 `status`、`relations`、`reviewed_at` は追加しない。

将来、正式なレビューが必要になった場合は、既存 `status` と分けた任意の `review_state` を検討する。ただし、次を先に定義する。

- 誰が内容をレビューするか。
- どの本文の版をレビューしたか。
- 内容変更時に、レビュー済み表示をどう失効させるか。
- `reviewed_at` が、確認日・最終編集日・有効期限のどれなのか。
- `canonical` が、組織の採用表現なのか、正しさの認定なのか。

**出典・リンク・必須セクションの合格は、内容のレビュー合格ではない。** 作者または作者が明示的に委任した主体が内容判断を担う。LLM が自分の生成物を形式検査して `reviewed` にする設計は採らない。

#### source の「主張一覧」を配置判断に結び付ける

現行の source 要約に「主な主張」は既にある。追加価値は一覧という形式自体ではなく、**再利用可能な知見をどこへ反映したかを残すこと**にある。［P2 手順5:147–175］

PoC では、重要な候補に限って次の表を試す。

| 候補 | 主張と成立条件 | 根拠箇所 | 配置 | 理由 |
|---|---|---|---|---|
| c1 | 同一環境では生成物のバイト一致を確認する | 元資料の該当節 | 用語ページ内の節、または source 内 | 環境条件を省略しない |
| c2 | 異なる Python・SQLite では値・型・CSV の一致を確認する | 元資料の該当節 | c1 と区別して判断 | 一致条件が異なる |
| c3 | audit hook による禁止は OS 全体の通信遮断を保証しない | 元資料の該当節 | 再利用可能性を判定 | 適用範囲を明示する |

これは実在する `semasynth再現性の検証-2026-11-06.md` の 14〜18 行をもとにした**候補の例**である。今回、raw 原文との照合は行っていないため、引用文や昇格済みの知見としては扱わない。

配置値は `source_only`、`section`、`page` のような英語の識別値にできる。ただし、すべての候補を独立ページにせず、`source_only` にも理由を付ける。配置表の行数や文字数を、知見の量の代理指標にしない。

取り込み順序は次のようにする。

1. 対象 wiki と `SCHEMA.md` を確定する。
2. 既存の取得・PDF 登録手順で原資料を扱う。
3. 読解し、既存ページと適用条件を照合する。
4. source の要約と、必要な候補の配置を作る。
5. 既存ページの該当節を部分更新し、必要な場合だけ独立ページを作る。
6. 出典、被リンク、矛盾、索引を更新する。
7. 有効な場合は既存グラフを更新し、ログと結果を返す。

現行の対話を省く一括取り込みの規則も維持する。新たに毎回、分類・CQ・昇格の承認を追加しない。［P2 手順3:129–133、手順6〜8:177–207］

#### CQ は「答えられるべき問い」の小さな台帳にする

導入する場合は、`questions.md` を**記事ではなく管理用ファイル**にする。検索・統計・通常ページ lint・グラフ抽出の対象から適切に除外する必要がある。新しいファイル名を置くだけでは不十分である。

初期の問いは、作者が必要としている問いや、繰り返し回答できなかった問いから 3〜5 件程度を選ぶ。これは提案値であり、上限の根拠が実測されたわけではない。

各項目には次を持たせる。

- wiki 内で一意な CQ 識別子。
- 問いと、回答できたとみなす条件。
- `open|partial|answered|retired` の状態。
- 回答となる既存ページ・節へのリンク。
- 不足している根拠。

`answers` に相当する対応の正本は台帳側に置く。ページ側にも同じ配列を必須化しない。

機械は、CQ 識別子の重複、状態値、回答リンクの存在、`answered` なのに回答がない不整合を検査できる。**その回答で問いが解けるか、問いの集合が領域を網羅するかは意味判断である。**

`/wiki:plan` を追加する場合の仕様は次のように限定する。

| 項目 | 仕様案 |
|---|---|
| 入力 | topic、対象 wiki、必要なら既存 CQ |
| 出力 | CQ の追加・統合案、既存の回答箇所、不足する根拠、優先順位 |
| 保存 | 明示的に依頼された場合だけ台帳と索引を更新 |
| 行わないこと | 本文の自動大量生成、通常のリンク切れと区別できない赤リンクの大量作成 |

`plan` は新しい名前を付ける前に、既存 query の「足りないものは？」という使い方で試せる。［P4「特殊なクエリの種類」］

#### lint の検査範囲

| 機械的に検査するもの | LLM・作者の判断を残すもの |
|---|---|
| 型別必須キー、日付・配列・文字列の形式 | 主張が原資料を正確に表すか |
| `sources` の参照先が存在し、`type: "source"` か | 出典が主張の根拠になっているか |
| source の `raw` が解決できるか | 原資料の信頼性・独立性 |
| 索引の種別見出しとリンク先 `type` の一致 | 話題別分類の妥当性 |
| 配置表の対象ページ・節の存在 | `source_only/section/page` の選択 |
| CQ 識別子・状態・回答リンク | CQ の回答充足・網羅性 |
| 既存グラフの型・引用・参照の検査 | 分類リンクを意味的関係とみなせるか |
| 将来の修正器の対象差分と冪等性 | 手順と概念を分けるべき境界 |

`raw` の解決は `raw/` 固定ではなく、設定されたルート、既存の相対パス、rag が使う PDF の絶対パスを扱う。別 PC で見つからない PDF は、その事実を報告し、「出典が虚偽」とは判定しない。

`--fix` を将来追加する場合は、変更前後の意味が変わらないと保証できる修正に限定する。重複記事の統合、分類の決定、出典の推測、関係の追加、レビュー状態の昇格は含めない。明示的な `--fix` は、その限定範囲への実行指示として扱えるよう、現在の「検出のみ」との契約変更を文書化する。

#### 作者の実在ページでの frontmatter 例

以下はすべて**導入後の仮例**であり、ファイルは変更していない。

**用語ページ `concepts/オントロジー.md`**

既存の用語ページとして維持する。概念が複数の節に展開されていることだけを理由に分割しない。

```yaml
---
type: "concept"
title: "オントロジー"
aliases: ["ontology"]
sources: ["ontology-and-knowledge-graphs-and-ai-agents", "part-1-what-is-an-ontology-classes-properties-and-axioms", "part-4-extracting-ontologies-from-sources"]
created: 2026-11-04
updated: 2026-11-06
tags: ["知識表現", "AIエージェント"]
---
```

**主張形の既存ページ `concepts/編集要求の復元世代を最終適用まで保持する.md`**

PoC と内容確認によって、限定した適用範囲を持つ独立ページとして維持する判断になった場合だけ `kind` を付ける。題名が文であることだけでは判定しない。

```yaml
---
type: "concept"
kind: "claim"
title: "編集要求の復元世代を最終適用まで保持する"
sources: ["output復元資格の設計-2026-11-04"]
created: 2026-11-04
updated: 2026-11-08
tags: ["並行処理"]
---
```

このページの 31〜34 行には、同じゲートを共有する実装を前提とし、OUTPUT の 2 操作についての設計であるという限定がある。これを題名の一般化やページ分割で落とさない。

**source ページ `sources/semasynth再現性の検証-2026-11-06.md`**

配置表を追記した場合の例。`sources` や `status` を機械的に追加しない。

```yaml
---
type: "source"
title: "SemaSynth 再現性の検証"
authors: ["Codex"]
raw: "../W1_Raw/semasynth再現性の検証-2026-11-06.md"
ingested: 2026-11-06
created: 2026-11-06
updated: 2026-11-08
tags: ["知識表現"]
---
```

SemaSynth の source がユーザースコープにある事実は、`scope` 追加では解決しない。プロジェクト記録として移すか、残す価値のある一般知識だけを選ぶかは、別の整理として作者が判断する。

#### `SCHEMA.md` と references の改訂箇所

- `SCHEMA.md`：主張の既定の配置、出典の型別規則、索引の分類、任意の CQ 管理を追加する。作者固有のサイズ上限やパスは維持する。
- `page-conventions.md`：用語ページと `kind: "claim"`、条件・根拠・留保、手順を分ける基準を説明する。
- `ingest-workflow.md`：重要な主張の配置、`source_only` の理由、配置表と本文更新の同期を追加する。
- `lint-workflow.md`：構造検査と意味判断を明記し、検出結果を修正済み・レビュー済みと混同しない。
- `query-workflow.md`：利用時の改善、未回答の問いの選別、既存回答の更新を追加する。回答の全件保存はしない。
- `graph-workflow.md`：新しい `relations` は作らず、既存の正本を維持する。主張ノードへの移行は別途扱う。
- `architecture.md`・`scaling-playbook.md`：方法論マップと独立した導入条件を補う。既存の規模・コンテキスト対策は残す。

### 6. 導入の順序・条件・SemVer

確認した `plugin.json` のバージョンは **`0.6.0`** だった。以下の番号は、そのスナップショットから進める場合の例であり、公開済み最新版を確認したものではない。

| 段階 | 入れるもの | 入れる合図・完了条件 | SemVer と既存 wiki |
|---|---|---|---|
| A：既存契約の不足を補う | 出典必須の説明と実装の整合、方法論の案内、既存手順の参照整理 | 今回、規約と通常 lint の差を確認済み | 説明の訂正・既存規約の警告追加なら **パッチ**候補。例 `0.6.1`。既存ページを書き換えない。終了コードなど既存契約を変えるなら別扱い |
| B：分類検査を追加 | 索引見出しと `type`、出典参照の詳細診断 | 作者の 16 件を検出し、独自の索引見出しで誤検出しない | 新しい診断能力として **マイナー**。例 `0.7.0`。修正案を示し、一括移行しない |
| C：配置 PoC | source の主張・配置表、用語内の `###`、選別した `kind: "claim"` | 固定した資料で、条件・根拠を失わず配置を比較できる | PoC 自体はリリース不要。合格後の任意機能として **マイナー**。既存ページを全件再生成しない |
| D：問いによる整備 | 少数 CQ、台帳、既存 MOC の改善 | 同じ未回答の問いが再発する、または作者が特定領域の整備を求める | 管理ファイルと検査の追加は **マイナー**。旧 wiki は台帳なしで有効 |
| E：専用入口・手順形式 | 必要なら `/wiki:plan`、howto 形式、限定 `--fix` | 手動試行で利益があり、同じ操作が繰り返される | オプトインの追加として **マイナー**。既存コマンドの既定動作は維持 |
| F：レビュー制度 | 必要ならレビュー情報と専用操作 | 外部利用で誤解・責任分担の問題が実際に発生し、レビュー担当者と失効規則を決定 | 任意の追加なら **マイナー**。既存ページの全件状態付与はしない |
| G：グラフの主張型移行 | 必要なら `claim` の `maps_from` と述語型の調整 | 主張を関係として問い合わせる具体的要求が生じる | ID・エッジ移行を伴うため、本文変更と別に版を決める。既存参照を維持できる移行を優先 |

配置 PoC は、直前の検討を利用し、まず source 3 本 × 2 モデル × 3 回の **18 件の配置計画**程度から始める案が妥当である。現行手順との対照を取る。これは検証の提案であり、今回実施していない。

合格条件は少なくとも次を含める。

- 原資料に対する忠実さと適用条件の保持を必須条件にする。
- 同じ入力の再処理で重複を増やさない。
- 別モデル・別実行での配置一致を測る。
- 全件 `source_only` で合格できないよう、再利用可能な知見の取りこぼしも評価する。
- 作者が修正に要した時間と、読まされる候補の量を現行と比べる。

直前の検討が挙げる一致率 85% などは提案値であり、達成済みの基準ではない。［R1 §8、R2「残るリスクと未確定事項」］

**メジャー変更が問題になるのは**、全ページへの新必須項目、既存 `status` の意味変更、ID 解決方法の置換、既存更新の禁止など、既存利用者の契約を壊す案である。今回は採らない。なお `0.x` は安定 API を保証しない段階なので、「破壊的変更なら必ず `1.0.0`」とは機械的に決められない。破壊的変更と版番号の方針は、明示して決定すべきである。

採用する変更では、プロジェクト規則どおり `plugin.json` と `CHANGELOG.md` を同時更新する。マーケットプレイスに `version` は追加しない。リリース完了の報告条件も既存規則を維持する。［A「リリース」］

### 7. 提案自体の誤り・不整合

以下は採否の理由とは分けて扱う。

| 箇所 | 問題 |
|---|---|
| コマンド数 | 「8 コマンド」とあるが、一覧表は 6 本。本文で `graph` を加えても 7 本で、8 本目が示されない |
| コマンド名 | `/wik:lint` は `/wiki:lint` と不一致。共通ルールの `/wiki promote` は `/wiki:promote` と不一致 |
| 入力表記 | `<pathっurl>` は区切りの誤記と考えられる |
| `type` | `syntesis` は `synthesis` の誤記。`explanation` も本文に現れるが、スキーマの候補にはない |
| 状態数 | `draft|reviewed|canonical|deprecated` は 4 値だが、ロードマップでは「三段階」と記載 |
| 状態の導入時期 | 共通スキーマでは最初から全ページに `status`、ロードマップではフェーズ2から有効化。初期段階での扱いが不明 |
| リレーションの導入時期 | 先に採用するものとされる一方、検査はフェーズ3まで待つ。未検査の関係を蓄積する期間が生じる |
| スキーマの正本 | 共通ルールを `SKILL.md` に置く説明と、フェーズ0の `CLAUDE.md` にスキーマを書く説明が一致しない |
| `answers` の位置 | 例では `relations.answers`、説明表では独立したフィールドのように扱う |
| `sources` の意味 | スキーマ例は source ページ ID だが、検査説明は「raw/ に実体があるか」。間に source ページと `raw` の参照解決が必要 |
| `plan` の後続操作 | 「ingest か answer」とあるが、`answer` コマンドは定義されていない |
| `decision` の入口 | ロードマップで型を有効化するが、`decide` を追加する段階が明示されない |
| 「手順と概念を混ぜない」 | 「How-to と Reference を分離」という説明とも粒度が一致しない。独立した利用目的と、必要な短い説明を区別する必要がある |
| 初期テンプレート | source・concept・journal の 3 種だけでは、初期 ingest が生成する entity に対応しない |
| 素材の保存 | raw を読むだけという共通ルールと、新規 raw を保存する ingest の権限の区別が説明されていない |
| フェーズ画像 | 画像が失われており、4 段階・3 移行条件の図の具体的な内容を確認できない |

方法論についても、提案の簡略化と原典の性質を分けたい。

- SKOS の `related` は対称関係で、`broader` 自体は推移的なプロパティではない。提案の軽量な分類規約を使うなら、その意味を独自に定義し、「SKOS だから循環禁止などが自動的に決まる」と扱わない。[W3C SKOS Reference §8](https://www.w3.org/TR/skos-reference/#semantic-relations)
- Diátaxis は、空の四分類構造を先に作る運用を求めていない。必要になったときに目的の異なる内容を分ける方針は、原典とも整合する。[Diátaxis as a guide to work](https://www.diataxis.fr/how-to-use-diataxis/)
- KCS の状態は、出典の有無だけでは決まらない。内容への確信、利用結果、標準への適合、担当者の役割を含み、状態遷移も単純な直線ではない。「draft は出典不要、reviewed は出典必須」は、KCS そのものではなく今回の提案独自の設計である。[KCS Article State](https://library.serviceinnovation.org/KCS/Knowledge-Centered_Success_Practices_Guide/301-Evolve_Loop/Practice_5_Content_Health/Technique_5.2)

## 検討した代替案

| 代替案 | 採らなかった理由 |
|---|---|
| **提案をそのまま全面導入する** | 型・状態・関係・入口を同時に増やし、既存 ADR と衝突する。作者の source 偏重を解く前に、新メタデータの保守を増やす |
| **現状を維持し、何も追加しない** | 索引の 16 件の誤分類と、出典規約に対する検査不足が残る。主張の配置を明示する改善にも試す価値がある |
| **全面的な 1 主張1ページ** | 条件の脱落、重複、断片化を増やす可能性があり、直前の検討の反例が未解消。用語ページと節を残す併用案を選ぶ |
| **全ページに lifecycle を導入してから運用を始める** | 状態の正しさを誰が判断するか未定義。取り込みのたびに作者のレビュー待ちを作る |
| **SKOS 風の平坦な `broader`・`related` に書き換える** | 入れ子問題は避けられるが、索引・本文リンク・既存グラフに加えて第四の関係記録を維持する問題は残る |
| **すべて既存グラフの型付きエッジに変換する** | ナビゲーション上の都合による分類に、原資料の引用を無理に付けることになる。編集上の分類と事実関係は分ける |
| **未回答の query をすべて CQ として保存する** | 一時的な質問や検索語の失敗まで backlog になり、作者の確認量が増える。再発・重要性・整備意図で選ぶ |
| **形式検査を通ったページを LLM が自動で `reviewed` にする** | 出典の存在と根拠の妥当性を混同する。未検証の確信を蓄積する危険がある |
| **日誌を wiki に入れ、lint の例外で処理する** | ADR-0006 の分離理由を再び抱える。今回は日誌運用を変更する必要がない |

提案の中で直前の粒度検討を補える点は、**「何を独立させるか」だけでなく、「問いに答えられるか」「既存ページへ何を反映したか」を確認対象にした点**である。一方、`type` と共通 `status` だけでこれらを解けるという整理は弱い。ページの形式と知識の妥当性は別の軸である。

## 前提と不確実性

- 今回は独立した検討担当として読み取りと計算だけを行った。ファイル変更、ビルド、取り込み PoC、レビュー制度の試行は行っていない。禁止された今回の成果保存ディレクトリも読んでいない。
- 作者の wiki の `index.md`、`SCHEMA.md`、`log.md`、ページ一覧、代表ページを確認した。57 ページ全件の本文・raw を監査したわけではない。
- 直前の研究文書と総括は、結論の前提として使った。そこに記載された原典調査や実験を今回すべて再実施したわけではない。
- `0.6.0` は指定された本体ディレクトリの値である。GitHub の公開状態やマーケットプレイス導入状態は確認していない。
- `reviewed_at` や `promote` が将来不要だと断定していない。レビューの対象、責任者、対象版、編集後の失効を決める要求が生じたら再検討する。
- 提案の失われたフェーズ図は復元していない。本文から確認できるロードマップだけを評価した。
- PoC の規模、CQ の初期件数、状態導入の合図は本報告の提案であり、達成済み・合意済みの条件ではない。

評価基準には次の留保がある。

1. **整合と移行の軽さに計 35% があり、現状維持が有利になる。** このため価値重視の重みも計算した。
2. **運用の手間と実装の軽さは別の負担である。** 実装が簡単でも、作者が全ページに状態を付け続ける方式は低く評価した。
3. **検査可能性と正しさは一致しない。** `id` 一致は容易に検査できても、利用価値が増えるとは限らない。
4. **出典への忠実さ、適用条件の保持、保存先境界の保全は加重点で相殺すべきでない。** これらは採用の必須条件とする。
5. **点数の小差に精度はない。** 小数第2位は計算を追跡するための表示であり、判断の確実さを示さない。

作者の判断が必要なのは、再利用可能な知見とプロジェクト記録の境界、PoC の許容誤り、レビュー制度の責任者である。現時点の資料からは、これらを新しいメタデータで自動解決できるとは判断できない。

## 参照

本体の参照先は、空の可能性がある worktree 内サブモジュールではなく、指定された `C:\Works\info-hive-dev\info-hive-wiki\` とした。

| 記号 | 読んだファイル・該当箇所 |
|---|---|
| A | [AGENTS.md](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/AGENTS.md:27)：名前、方針 B、リリース、変更時の規則 |
| P1 | [SKILL.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md:31)：3 層、グラフ、保存範囲、スケーラビリティ、lint、経験学習 |
| P2 | [ingest-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:129)：手順3〜8。併せて冒頭の PDF 連携・raw 取得・翻訳規則 |
| P3 | [page-conventions.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md)：frontmatter、`sources`、命名、本文構成、留保 |
| P4 | [query-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md)：回答の保存、特殊なクエリ、避けるべきパターン |
| P5 | [lint-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/lint-workflow.md)：構造検査、内容判断、提案と承認、頻度 |
| P6 | [graph-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md)：有効化、3 種のエッジ、証拠、更新、問い合わせ |
| P7 | [evolution-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/evolution-workflow.md:121)：証拠、経験記録、通常ページとの対応 |
| P8 | [wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:278)：`DEFAULT_REQUIRED_FM`、`lint`、CLI 引数。`collect_pages` も確認 |
| P9 | [wiki_text.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:281)：平坦な frontmatter パーサー |
| P10 | [wiki_graph_extract.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:149)：PyYAML の解析、`derive_node_type`、エッジ生成 |
| P11 | [ontology.yaml.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/ontology.yaml.template)：`maps_from`、`explicit_only`、述語の型と証拠要求 |
| P12 | [SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template)：種類、必須項目、任意グラフ、経験学習 |
| P13 | [page.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/page.md.template)：共通テンプレート |
| P14 | [architecture.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/architecture.md)、[scaling-playbook.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/scaling-playbook.md)：正本、拡張、索引分割、独自型 |
| P15 | [commands](C:/Works/info-hive-dev/info-hive-wiki/commands)：`*.md`。特に `ingest/query/lint/graph/init/upgrade/learn/evolve` の入出力と手順 |
| P16 | [plugin.json](C:/Works/info-hive-dev/info-hive-wiki/.claude-plugin/plugin.json)：`version: "0.6.0"` |
| D6 | [ADR-0006](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0006-daily-journal-is-separate-plugin.md:26)：日誌の責務分離、ノート抽出と取り込み |
| D8 | [ADR-0008](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0008-numbered-workspace-layout.md:19)：作業領域、保存先、テンプレート、設定 |
| D9 | [ADR-0009](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0009-graph-layer-stays-in-wiki.md:24)：グラフを wiki 内の任意索引に限定する決定 |
| R1 | [wiki-note-granularity-2026-11-08.md](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/research/wiki-note-granularity-2026-11-08.md:83)：併用案、frontmatter、PoC、移行 |
| R2 | [直前の粒度検討の summary.md](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/agent-runs/2026-11-08-wiki-note-granularity-atomic-evergreen/summary.md)：反例、残るリスク、主張型とグラフ |
| R3 | [porting-plan.html](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/porting-plan.html)：方針 B、日本語スラッグ、移植・互換性の方針 |
| W1 | [作者の index.md](D:/Users/toshiki/info-hive/W0_Wiki/index.md:70)：シンセシス欄の 16 件の source |
| W2 | [作者の SCHEMA.md](D:/Users/toshiki/info-hive/W0_Wiki/SCHEMA.md)：パス、サイズ上限、型別必須項目、グラフ、経験学習 |
| W3 | [作者の log.md](D:/Users/toshiki/info-hive/W0_Wiki/log.md)：取り込みと query 保存の実例 |
| W4 | [編集要求の復元世代を最終適用まで保持する.md](D:/Users/toshiki/info-hive/W0_Wiki/concepts/編集要求の復元世代を最終適用まで保持する.md:31)：独立した判断と適用範囲 |
| W5 | [semasynth再現性の検証-2026-11-06.md](D:/Users/toshiki/info-hive/W0_Wiki/sources/semasynth再現性の検証-2026-11-06.md:14)：環境別の一致条件と保証範囲 |
| W6 | [オントロジー.md](D:/Users/toshiki/info-hive/W0_Wiki/concepts/オントロジー.md:13)：用語ページ内の複数の説明と留保 |
| S | [decision-matrix/SKILL.md](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/.agents/skills/decision-matrix/SKILL.md)：重み付き評価、感度分析。付属評価ルーブリックも確認 |
| 提案原文 | 本依頼に貼り付けられた「LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計」 |

使用した MCP サーバー: なし  
使用した Agent Skills: decision-matrix

### エージェント D

## 結論

**提案は一括導入せず、記事の振り分けと検査を先に導入する。全面的な `status` 管理、入れ子の `relations`、ページ型・コマンドの一斉追加は採らない。** ADR-0006・0008・0009 は変更せず、直前の「用語ページ＋選別した `kind: "claim"`」の方針を継承する。

最初に入れるのは次の三つである。

1. **索引の分類検査**：作者の wiki では、「シンセシス」欄に `type: "source"` が 16 本混在している。
2. **source の主張一覧と振り分け記録**：新規作成・既存更新・source に残す理由を明示し、知見の取り出し漏れを調べられるようにする。
3. **型別の出典検査**：既存の `sources` 必須規約と、通常の lint が実際に検査している内容の差を埋める。

| 採否 | 要素 |
|---|---|
| **導入する／既存を維持する** | 5 区分の方法論マップを説明用に採用。raw の確定後の不変性、既存ページの検索と更新優先、出典・矛盾の併記、Markdown を正本とする管理を維持。補足提案として索引分類検査を追加 |
| **変えて導入する** | きっかけ別の案内、問題発生を合図にする導入条件、`type`・`kind` 別 lint、source の主張一覧、Atomic／Evergreen の併用、MOC、Middle-out、Diátaxis、KCS、CQ と回答の対応、テンプレート、ログ、スラッグ安定化 |
| **導入しない** | 全記事の `id`、記事単位の `scope` による保存領域の分離、全記事共通の四値 `status`、入れ子の `relations`、標準型としての `decision`・`journal`・`graph`、標準コマンド `/wiki:decide`、重複する `/wiki:lint --relations`、`/wiki:graph` の入口削除、全回答の自動記事化、正典ページへの直接更新禁止 |
| **保留** | 独立した `/wiki:plan`、レビュー用途に限定して再設計する `/wiki:promote`、`reviewed_at`、`type: "howto"`、既存グラフへの `broader` 追加、限定的な `/wiki:lint --fix`。いずれも後述する具体的な需要・検証条件を満たしてから判断 |

「保留」は、原案のまま後日導入する意味ではない。特に `/wiki:promote` は、**知見を独立ページにする判断と、内容をレビュー済みにする判断を分離してから**検討する。

## 根拠

### 1. 現状の確認

以下は、指定された本体 `C:/Works/info-hive-dev/info-hive-wiki/` と作者の wiki を読み、確認した事実である。参照記号の実際のパスと該当箇所は末尾にまとめた。

| 確認した事実 | 判断への意味 |
|---|---|
| 本体の `plugin.json` は **0.6.0**。既存コマンドは 10 本で、`plan`・`decide`・`promote` はない［P1］ | 同名のコマンドがあることと、提案された機能があることを区別する |
| 作者の wiki は **source 37、concept 17、entity 1、synthesis 2、計 57 ページ**。source のうち `semasynth` で始まるものは 28 本［W1］ | 直前レポートの 56 ページは過去の集計。今回の移行対象は 57 ページを基準にする |
| `index.md` の「シンセシス」欄は 18 項目で、うち 16 本の実体は `sources/` の `type: "source"`［W1］ | 新しい分類体系より、既存分類の整合を先に直す価値がある |
| `wiki_lint.py` は `index.md`・`indexes/` を通常ページの収集から除外する［P5］ | 現行 lint に索引の見出しとページ型の照合はない |
| 通常の lint の既定必須項目は `type,title,tags,created,updated`。型別に `sources`・`raw` を必須化する分岐はない［P5］ | 文書上の出典必須を、そのまま「機械検査済み」と扱ってはいけない |
| 通常の frontmatter パーサーは入れ子を空配列として扱う。一方、グラフ専用パーサーは `yaml.safe_load` を使う［P6・P7］ | 「入れ子が全面的に使えない」ではなく、**通常メタデータと既存グラフで解析経路が違う** |
| `ingest` は既存ページを部分更新し、矛盾を併記する。新規ページには既存ページからの被リンクを求める［P2］ | 全更新を draft と正典化に分ける必要性はまだ示されていない |
| `query` は価値のある回答の保存を提案し、情報がない場合はその旨を答える［P4］ | KCS のために全回答を記事化するのは、現行の選別を弱める |
| 作者の `SCHEMA.md` は独自の上限・保存先を持つ。`indexes/` の分割ファイルはない［W2］ | テンプレートの更新だけでは既存 wiki の規約は変わらない。上書き移行は不適切 |

今回の件数は、`sources/`・`concepts/`・`entities/`・`synthesis/` の Markdown を読み、frontmatter の `type` ごとに集計した。索引の 16 本は、「シンセシス」見出し以下の wikilink を実在ページと照合した値である。ビルド、ファイル変更、取り込みの実行はしていない。

### 2. 要素の分解と現行との差分

「ある」は同じ目的の機能があるという意味であり、原案と完全に同じという意味ではない。採点表の ID はこの表に対応する。

#### 方法論・メタデータ・ページ型

| ID | 提案の要素 | 現行 | 差分、採否、導入条件 |
|---|---|---|---|
| M1 | 発見・構造化・体系化・執筆・維持の 5 区分 | 一部 | 各機能はあるが説明の分類はない。**導入**。`SKILL.md` の短い案内に使い、別々の必須工程にはしない。説明整理として軽いが、直接の新機能ではない |
| M2 | きっかけごとにコマンドを分ける | 一部 | ingest/query/learn/evolve 等が既に担う。**変更導入**。既存 10 コマンドの案内を整理し、入口追加は繰り返し需要が確認された場合だけ |
| M3 | 4 段階の成熟度と移行条件 | 一部 | 現行にも規模・問題に応じた変更条件がある［P9］。**変更導入**。問題発生を合図にする考えは採るが、正典化→グラフ化という一方向の順序にはしない |
| F1 | `type` と `status` で lint を切り替える | 一部 | 共通項目の検査とグラフ専用検査はある。**変更導入**。まず `type`・`kind` 別の構造・出典検査。全記事の `status` は要求しない |
| F2 | `id` | ない | スラッグと重複し、検索・リンクの別の識別子にもならない。**不採用**。改名を支える独立 ID が必要になったときは別設計 |
| F3 | `scope: common/project:<name>` | ない | 作業領域・wiki ルートで分ける設計と重複。**不採用**。内容の適用範囲は本文に書く |
| F4 | `status: draft/reviewed/canonical/deprecated` | 一部 | `experience-pattern` の別の三値 `status` がある。**共通化は不採用**。編集状態、確からしさ、失効を一列に混ぜない |
| F5 | `reviewed_at` | ない | `updated` はあるが内容レビュー日ではない。**保留**。レビュー主体・対象版・失効条件が決まり、参照頻度に応じた見直し需要が出たら導入 |
| F6 | `relations.broader` | ない | 型付き関係の仕組みはあるが、この述語は標準にない。**保留**。階層関係への実際の問い合わせが必要になったら、既存 ontology 内で定義する |
| F7 | `relations.related` | 一部 | 本文の関連リンクと `mentions` がある。**変更導入**。探索上の関連は本文の wikilink を使う。対称な意味関係と `mentions` は同一視しない |
| F8 | `relations.answers` | ない | synthesis の `question` はある。**変更導入**。最初は CQ 台帳の回答先欄を正本にし、記事側への二重記入を避ける |
| T1 | `type: howto` | ない | 独自型の追加は許されている。**保留**。独立した操作手順が繰り返し使われ、検索・必須節を分ける利点が確認されたら任意追加 |
| T2 | `type: decision` | 一部 | 独自型の例、グラフの明示ノード型はある。標準ページ型ではない。**標準追加は不採用**。プロジェクト ADR を正本として ingest する |
| T3 | `type: moc` | 一部 | `index.md`・`indexes/`、用語ページが入口を担う。**変更導入**。MOC の機能を既存の入口に持たせ、新型を必須にしない |
| T4 | `type: journal` | ない | ADR-0006 が別プラグインと決定。**不採用**。日誌から選別した素材を明示的に ingest する経路を維持 |
| T5 | `type: graph` | ない | `graph/` は派生索引。**不採用**。グラフを説明する知識ページは通常の concept/synthesis でよい |
| Q1 | `questions.md` と Competency Questions | 一部 | 未解決の問いの記述と不足分析はあるが、問いの台帳はない。**変更導入**。実際の未回答・反復質問から少数を始め、10〜30 問の生成を必須にしない |
| D1 | Diátaxis の「手順と概念を混ぜない」 | 一部 | 現行は節で分けられる。**変更導入**。読者の目的が異なる独立した説明と実行手順を分ける。前提・安全条件まで排除しない |
| D2 | Middle-out による分類 | 一部 | 成長後の分割とスキーマ見直しがある。**変更導入**。既存ページを示して分類案をまとめ、ユーザーが一括確認する。lint ごとの自動再分類はしない |
| K1 | KCS と、draft の出典免除 | 一部 | query の回答保存、learn の経験記録がある。**変更導入**。利用時に改善する思想を採り、出典なしの断定を知識として保存する例外は作らない |

#### コマンド・取り込み

| ID | 提案の要素 | 現行 | 差分、採否、導入条件 |
|---|---|---|---|
| C1 | `/wiki:plan` | ない | query の不足分析と重なる。**保留**。CQ 台帳を使う計画作成が反復し、自然文の query では手順が安定しない場合に追加 |
| C2 | `/wiki:decide` | ない | ADR の正本と wiki 内の decision が競合しうる。**不採用**。既存の ADR 作成と `/wiki:ingest` を使う |
| C3 | `/wiki:promote` | ない | 知見の独立化とレビュー承認が混同されている。**保留**。レビュー対象版と承認主体を定義し、後者だけを扱う入口として再検討 |
| C4 | `/wiki:lint --fix` | ない | 現行は報告・提案後に修正［P3］。**保留**。同じ機械的修正の反復が負担になり、限定した修正規則の安全性・冪等性を確認できたら追加 |
| C5 | `/wiki:lint --relations` | 一部 | `/wiki:graph lint` と MCP lint のグラフ結果がある。**新オプションは不採用**。必要な関係検査を既存のグラフ lint に追加 |
| I1 | ingest の source「主張の一覧」と概念への展開 | 一部 | 現行も主な主張を書くが、候補別の行き先・理由を残さない［P2］。**変更導入**。候補の自動ページ化をやめ、振り分け表を加える |
| X1 | 索引の見出しと `type` の照合〔本評価の補足〕 | ない | 作者の実際の誤分類に直接効く。**導入**。型別索引と明示された見出しだけを検査し、テーマ別 MOC を誤検出しない |

#### 共通ルール 8 項目

| 番号／採点 ID | 原案 | 現行との差分と採否 |
|---|---|---|
| 1／R1 | raw は読み取り専用 | **原則維持**。ただし初回の保存・Web 翻訳等の確定処理と、その後の不変性を区別する。rag の PDF は原本を移動・複製しない［P2］ |
| 2／R2 | 型別テンプレートを使い、全フィールドを埋める | **変更導入**。既存テンプレートを使い、型別の必要項目だけ必須にする。未知の `reviewed_at` や不要な `relations` を埋めさせない |
| 3／R3 | index と既存記事を調べ、同一概念は更新 | **維持**。同じ語かどうかだけでなく、対象・条件・断定の強さを照合する。反対説を SSOT の名目で統合・削除しない |
| 4／R4 | 1 記事 1 概念、またがれば分割 | **変更導入**。直前の併用案を採る。source・entity・synthesis に概念単位の機械的分割を適用しない |
| 5／D1 | 手順と概念を混ぜない | **変更導入**。別の利用目的なら分ける。短い手順例や適用条件の同居まで禁止しない |
| 6／F4・C3 | 全記事 draft、promote だけで昇格 | **不採用**。通常更新に恒常的な承認待ちを作る。レビュー機能が必要なら独立した任意機能にする |
| 7／R7 | 全操作を log に記録 | **変更導入**。既存の操作名・書式を維持し、変更・保存・検査を記録する。読み取りだけの検索をすべて追記しない |
| 8／R8 | `[[id]]`、ファイル名=id、改名禁止 | **変更導入**。`[[slug]]` と日本語スラッグを維持。題名の推敲だけで改名しないが、重複解消等に必要な改名は禁止しない |

### 3. 採点と重みの感度分析

採点対象は、原案に記された要素である。変更導入後の完成形を先取りして高得点にはしていない。X1 だけは本評価の追加案である。点数は設計評価であり、実測値ではない。根拠は直前の差分表に示した。

五つの素点を、順に価値 \(V\)、整合 \(C\)、検査 \(T\)、手間の少なさ \(O\)、軽さ \(L\) とする。

- **基本**：\(S=(25V+20C+20T+20O+15L)/100\)
- **価値重視 A**：重みを `(40,15,15,15,15)` に変更
- **運用・検査重視 B**：重みを `(15,20,25,25,15)` に変更

例として I1 は、基本では  
\((25×10+20×8+20×6+20×7+15×8)/100=790/100=7.90\)。

基本点の降順で示す。同点に優劣は付けない。共通ルール 5・6 は D1、F4・C3 と同じ要素なので重複採点しない。

| ID・要素 | V | C | T | O | L | 基本 | A | B |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X1 索引分類検査 | 9 | 10 | 10 | 9 | 8 | **9.25** | 9.15 | 9.30 |
| I1 主張一覧・振り分け | 10 | 8 | 6 | 7 | 8 | **7.90** | 8.35 | 7.55 |
| R1 raw 不変 | 4 | 9 | 9 | 9 | 10 | 7.90 | 7.15 | 8.40 |
| M1 5 区分マップ | 5 | 10 | 5 | 9 | 10 | 7.55 | 7.10 | 7.75 |
| R3 SSOT・既存検索 | 5 | 10 | 5 | 9 | 10 | 7.55 | 7.10 | 7.75 |
| M2 きっかけ別入口 | 6 | 9 | 6 | 8 | 9 | 7.45 | 7.20 | 7.55 |
| F5 reviewed_at | 6 | 8 | 8 | 6 | 8 | 7.10 | 6.90 | 7.20 |
| C4 lint --fix | 7 | 6 | 9 | 8 | 4 | 6.95 | 6.85 | 7.10 |
| Q1 questions・CQ | 8 | 8 | 5 | 5 | 7 | 6.65 | 6.95 | 6.35 |
| R7 全操作ログ | 4 | 7 | 8 | 6 | 8 | 6.40 | 5.95 | 6.70 |
| D2 Middle-out | 7 | 8 | 4 | 5 | 8 | 6.35 | 6.55 | 6.10 |
| F1 type/status 別 lint | 8 | 5 | 7 | 5 | 5 | 6.15 | 6.50 | 5.95 |
| T1 howto | 5 | 7 | 7 | 6 | 6 | 6.15 | 5.90 | 6.30 |
| R8 ファイル名一致・改名禁止 | 4 | 5 | 10 | 5 | 4 | 5.60 | 5.20 | 5.95 |
| T3 moc | 5 | 6 | 7 | 5 | 5 | 5.60 | 5.45 | 5.70 |
| K1 KCS・出典猶予 | 8 | 3 | 4 | 6 | 5 | 5.35 | 5.90 | 5.05 |
| F8 answers | 6 | 4 | 7 | 5 | 4 | 5.30 | 5.40 | 5.30 |
| M3 4 段階の順序 | 5 | 5 | 4 | 6 | 7 | 5.30 | 5.30 | 5.30 |
| C1 plan | 6 | 6 | 5 | 4 | 5 | 5.25 | 5.40 | 5.10 |
| C5 lint --relations | 3 | 4 | 8 | 5 | 5 | 4.90 | 4.50 | 5.25 |
| D1 手順・概念の混在禁止 | 5 | 6 | 3 | 4 | 6 | 4.75 | 4.85 | 4.60 |
| F6 broader | 5 | 3 | 8 | 4 | 3 | 4.70 | 4.70 | 4.80 |
| F2 id | 2 | 3 | 10 | 5 | 3 | 4.55 | 3.95 | 5.10 |
| R4 1 記事 1 概念の強制 | 5 | 5 | 3 | 4 | 6 | 4.55 | 4.70 | 4.40 |
| R2 全フィールド必須 | 5 | 3 | 8 | 3 | 3 | 4.50 | 4.55 | 4.55 |
| T2 decision | 4 | 3 | 7 | 4 | 4 | 4.40 | 4.30 | 4.55 |
| F7 related | 3 | 3 | 8 | 4 | 3 | 4.20 | 3.90 | 4.50 |
| F4 status 四値 | 6 | 2 | 5 | 3 | 3 | 3.95 | 4.35 | 3.75 |
| C2 decide | 4 | 2 | 6 | 4 | 3 | 3.85 | 3.85 | 3.95 |
| C3 promote | 5 | 3 | 5 | 2 | 4 | 3.85 | 4.10 | 3.70 |
| F3 scope | 4 | 2 | 5 | 4 | 4 | 3.80 | 3.85 | 3.85 |
| T4 journal | 3 | 1 | 7 | 3 | 2 | 3.25 | 3.15 | 3.45 |
| T5 graph | 2 | 1 | 4 | 3 | 3 | 2.55 | 2.45 | 2.70 |

**重みを変えると中位の順序は動くが、採否の結論は変わらない。**

- X1 は三通りとも首位。
- I1 は基本・A で上位。B では既存原則 R1・R3 や説明整理 M1 が上に来るが、それらの多くは既に存在する。追加投資先として I1 を後回しにする理由にはならない。
- Q1 は A では F5・C4 より上がり、B では下がる。したがって CQ は一律必須にせず、未回答の再発を導入条件にする。
- `reviewed_at` は高得点でも、誰が何をレビューしたかが未定義なら使えない。依存する設計が先である。
- `id` は検査しやすいため B で上がるが、スラッグと同じ値を照合するだけでは利用価値が増えない。

### 4. 衝突と解き方

| 衝突 | 解き方 |
|---|---|
| **ADR-0006 と `journal`・日誌からの自動昇格** | **提案側を変更**。日付ノートは `log`、選別した素材は `50_Notes`、wiki への取り込みは明示的な ingest。ADR-0006 の決定表・知識の取り出し規則を維持する |
| **ADR-0008 と `scope` による同居** | **提案側を変更**。保存先は作業領域で分離する。`scope: project` を付けても、ユーザースコープにプロジェクト固有情報を置く問題は解消しない |
| **ADR-0008 と `decisions/`・テンプレート配置** | ADR の正本はプロジェクト側に置く。プラグイン内の配布用テンプレートと、Foam 用 `.foam/templates/` を区別する。wiki 内に ADR の第二の編集正本を作らない |
| **ADR-0009 とグラフ中心の最終目標** | **提案側を変更**。グラフは wiki 内の任意索引のまま。`/wiki:graph` を残し、生成は既存スクリプトに任せる |
| **`relations` と `graph.relationships` の二重化** | `relations` は導入しない。探索上の関連は本文リンク、出典で明示された意味関係は既存の型付きエッジとする |
| **平坦な frontmatter と入れ子** | 一般メタデータは平坦を維持。既存 `graph:` は専用処理が読む例外。新しい `relations` を PyYAML が読めるだけでは検索・通常 lint が対応したことにならない |
| **方針 B と全フィールドの記入** | キー・`type`・`kind`・述語は英語で書き、文字列値を引用符で囲む。日本語の本文・題名・スラッグは維持。新しい型・kind を導入するなら読み取り別名も整合させる |
| **`id` とスラッグ** | `id` を増やさない。既存の日本語スラッグを維持し、改名時は本文リンク・frontmatter 参照・索引・明示グラフ ID を点検する |
| **全記事 `status` と experience-pattern** | `status: hypothesis|supported|superseded` を維持。編集レビュー状態とは別軸とする。`ingest` が `/wiki:learn` の経験則ページを作ることも避ける |
| **1 記事 1 概念と `kind: "claim"`** | 直前の併用案を優先。条件・根拠・適用範囲を一緒に更新できる判断を単位とし、通常は用語ページの節、必要時だけ独立ページにする |
| **正典ページの更新禁止と現行 ingest** | **更新禁止を不採用**。出典付きの部分更新を継続する。将来レビュー状態を付ける場合は、内容更新でレビューを失効させる |
| **source→concept のリンク方向固定** | 一方向に限定しない。concept の `sources` と本文の出典参照、source の関連ページ、被リンクを維持する |
| **赤リンクと現行 lint** | 初期の計画では未作成候補を普通の文字列で書く。意図的な赤リンクを導入するなら、計画項目と偶発的リンク切れを区別する仕様を先に作る |

**承認済み ADR を変える必要はない。** 一方、直前の粒度検討のグラフ移行には修正を提案する。

`kind: "claim"` の追加と、ノード ID の `concept:<slug>`→`claim:<slug>` 変更は別々に進める。現行 ontology のままなら `type: concept` の対応付けが残るため、`kind` の追加だけでノード ID を変える必要はない。`claim` の `maps_from` は、既存の明示エッジの移行と `depends_on` 等の型制約を点検してから追加する［P7・P8］。

作者の通常ページを調べた範囲では、明示的な `graph:` を持つのは `entities/yuan-an.md` で、五つの `authored` エッジの目的語はいずれも source だった。ただし、これは他の利用者の wiki の移行安全性を保証しない。

### 5. 導入する要素の詳細

#### 5.1 frontmatter は最小限にする

| 対象 | 採用するキー・値 |
|---|---|
| 全ページ | 現行の `type`、`title`、`tags`、`created`、`updated` |
| source | `type: "source"`、`authors`、`raw`、`ingested`、該当時だけ `url`。PDF 連携時の既存項目を維持 |
| entity/concept/synthesis | `sources` は source ページのスラッグの配列 |
| 独立した主張 | `type: "concept"`、`kind: "claim"`。PoC 後のオプトイン |
| 経験則 | `kind: "experience-pattern"` と既存の `status`。通常の主張からは独立 |
| CQ の回答 | 当初は記事側に `answers` を付けず、台帳の回答先欄を使う |
| 追加しない項目 | 全記事の `id`、`scope`、共通 `status`、`relations` |

適用範囲は本文の `## 適用範囲` に置く。保存領域を表す `scope` と、主張が成り立つ条件を同じフィールドに押し込めない。

`reviewed_at` は任意機能として保留する。後日導入するなら、少なくとも以下が必要である。

- `review_state: "unreviewed"|"reviewed"|"needs_review"` のように、既存 `status` と別名にする。
- `reviewed_at` は実際にレビューした日だけを書く。未実施なら省略する。
- レビュー担当と対象版を記録する。日付だけでは同日中の再編集を検出できないため、対象内容のハッシュ等が必要。
- 構文検査の成功だけで LLM が `reviewed` に上げない。LLM は根拠照合と差分を提示し、初期導入では作者が再利用価値の高い記事だけをまとめて確認する。
- 本文・出典・適用範囲が変わったら、その版のレビューは失効する。

`canonical` は採用しない。「別名を持つ同一対象の代表ノード」という既存の `graph.canonical` とも意味が違い、内容の正しさを過大に示すためである。

#### 5.2 source の「主張の一覧」を、振り分けまで含む記録にする

原案の最も有用な追加はここである。ただし一覧を作るだけでは、source 偏重は解消しない。

source の本文に `## 主張と振り分け` を設け、主要な候補について次を残す。

| 欄 | 内容 |
|---|---|
| 候補 | 条件と断定の強さを含む主張 |
| 根拠 | 原資料の節・ページ・行等と、必要な短い引用 |
| 扱い | `create`、`update`、`source_only` |
| 行き先 | 実在するページと、必要なら節 |
| 理由 | 再利用できる理由、既存に統合する理由、source に残す理由 |

主張をすべて列挙するノルマは設けない。対象は要約に残す主要な判断・定義・観測であり、ソース全体の書き直しにしない。

実在する `semasynth再現性の検証-2026-11-06.md` の raw 7 行目は、同一環境のバイト一致と異なる環境の値・型比較を分けている。この内容は「再現性はバイト一致で判定する」と一般化してはいけない。まず条件付きの一つの判断として抽出し、既存の適切な節があれば `update`、なければ独立化候補として検討する。**この調査だけでは、新規ページ作成が妥当だと確定していない。**

同 raw 11 行目の測定値・測定範囲、個別の工程完了等は、再利用できる規則と切り分けて `source_only` にできる。すべてを concept に変えることを成功指標にしない。

振り分け表は最終実行後に確定し、計画と実際の行き先が違ったら更新する。後日ページを移動・統合した場合も行き先を直す。表が存在するだけで取り出し漏れがなくなるわけではないため、候補の抽出漏れは別途 PoC で評価する。

#### 5.3 ingest の順序

既存の手順を保ち、次の位置に変更を入れる。

1. 対象 wiki と `SCHEMA.md` を確定する。
2. 現行の raw 保存・PDF 参照規則で原資料を読み、重要点を把握する。
3. index と既存ページの本文を読んで重複・適用条件・矛盾を調べる。
4. source 要約に主要な主張と振り分け候補を作る。
5. 用語の定義、対象固有の属性、再利用できる判断、個別の進捗を区別する。
6. 既存ページを部分更新し、必要な場合だけ新規ページを作る。
7. source の振り分け結果、出典、被リンク、型別索引を確定する。
8. グラフが有効なら既存の lint/extract、最後に log と報告。

現行の「要点をユーザーと話し合う」工程は維持するが、一括取り込みで省略できる現行例外も維持する［P2:129–133］。主張ごとの承認は増やさない。

#### 5.4 CQ・MOC・Middle-out

CQ は「この wiki が何に答えるために存在するか」を明確にする道具として採用する。原典も、問いは網羅的である必要はないとしている。最初から 10〜30 問を生成する必要はない。[Ontology Development 101, p.5](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)

初期案は `indexes/questions.md` を管理文書として置き、`index.md` から Markdown リンクで案内する。通常ページの型を増やさず、通常の知識検索・孤立検査と区別する。ただし現在は `indexes/` が通常 lint の対象外なので、**専用の台帳検査を追加する必要がある**。

台帳の列は以下とする。

- 問いの識別子、問い、必要な回答の範囲
- `open`、`partial`、`answered`、`out_of_scope`
- 回答先のページ・節、根拠、不足部分

これは台帳の状態であり、記事の `status` ではない。リンク先があるだけで `answered` にしない。回答の範囲と根拠を照合する。

Middle-out は、既存の用語ページを中核として、必要な上位・下位分類を提案する形にする。提案には対象ページと分類理由を添え、毎回の ingest ではなく、迷子・重複・誤分類が発生したときにまとめて確認する。原典にも中核の概念から一般化・特殊化する組み合わせ方式があるが、info-hive での改善効果は未測定である。[Ontology Development 101, p.7](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)

#### 5.5 Diátaxis と KCS の適用範囲

Diátaxis の利点は、読者の「理解したい」と「実行したい」を区別することにある。how-to は具体的な目的に集中し、長い説明は参照先へ分けるという原則を採る。ただし、それを全 wiki ページの混在禁止に一般化しない。[Diátaxis: How-to guides](https://diataxis.fr/how-to-guides/)

例えば `編集要求の復元世代を最終適用まで保持する.md` には、理由・三つの境界・適用範囲が同居する。これは設計判断を理解するために必要な一体性であり、番号付きの記述があることを理由に howto へ分割しない。

KCS からは「使うときに見直し、役立った知識を育てる」を採る。KCS 自体も状態を単純な直線的昇格に限らず、利用需要に応じたレビューを重視している。[KCS Article State](https://library.serviceinnovation.org/KCS/Knowledge-Centered_Success_Practices_Guide/301-Evolve_Loop/Practice_5_Content_Health/Technique_5.2)

出典は外部の出版物に限らない。作者の観測、再現結果、意思決定の記録も、その性質と範囲を明記すれば根拠になる。逆に、LLM の推測だけなら CQ・未確認事項として残し、出典のない確定知識にしない。これにより、記録を速くすることと根拠を保つことを両立させる。

#### 5.6 コマンドを追加する場合の入出力

当面、新コマンドは不要である。保留を解除する場合の契約は以下とする。

| コマンド | 入力 | 出力・変更 |
|---|---|---|
| `/wiki:plan <topic>` | 領域、必要な判断、既存 CQ、任意の対象 wiki | 既存回答・不足資料・優先順位を含む計画と CQ 台帳の差分。記事本文と空ページは作らない |
| `/wiki:promote <slug>` | レビュー対象の実在記事 | 根拠・適用範囲・矛盾・対象版の検査結果。合格候補を示し、定義済みの承認後にレビュー状態だけ更新。ページ分割や共通 wiki への移動はしない |
| `/wiki:lint --fix` | 明示した対象と許可済み修正規則 | 限定した機械的変更の差分・適用結果。意味の書き換え、主張の統合、出典の生成、改名を対象にしない |

`--fix` の指定は定義済みの機械的修正への指示として扱い、同じ承認を何度も求めない。ただし現行の `commands/lint.md`・`lint-workflow.md` にある修正手順との整合を明文化する。原案のように「機械的に直せるもの」という無限定の説明では実装しない。

#### 5.7 lint と LLM 判断の境界

| 機械的に検査できるもの | LLM・作者の判断が残るもの |
|---|---|
| 型別必須キー、列挙値、日付形式 | 主張が原資料の意味を保っているか |
| `sources` の存在、参照先が `type: "source"` か | 異なる source が独立した裏づけか |
| `raw` の指定先の存在。PDF の絶対パスも扱う | 引用が主張を支持しているか |
| 主張一覧の欄、行き先ページ・節の存在 | 主張の抽出漏れ、独立ページの再利用価値 |
| 型別索引の分類不一致 | テーマ別分類や MOC の良し悪し |
| CQ ID の重複、回答先の存在、状態値 | 問いに十分答えているか、必要な問いか |
| 将来のレビュー対象ハッシュの一致 | 誰の判断でレビュー済みと認めるか |
| 将来の `broader` の循環、許可した型の組 | 階層関係そのものが適切か |
| 修正処理の冪等性、許可範囲外の変更 | how-to に説明が「混ざりすぎている」か |

引用の文字列一致は根拠の存在確認であり、含意の証明ではない。`reviewed` を機械検査だけで付ける根拠にはならない。

#### 5.8 改訂する規約・参照文書

- **`SCHEMA.md`**：採用する主張単位、オプトイン範囲、source の振り分け欄、型別索引の対応、CQ の配置、レビューを使う場合の責任を記す。個別 wiki の規約を上書きしない。
- **`ingest-workflow.md`**：主張抽出・配置判断・実行後の表更新を追加。既存ページの部分更新、矛盾併記、PDF の扱いを維持する。
- **`page-conventions.md`**：用語ページと主張ページの併用、条件・根拠・適用範囲、型別必須項目を明確にする。
- **`lint-workflow.md`**：機械検査と意味判断を分け、索引・型別出典・振り分け表を追加する。
- **`query-workflow.md`**：保存価値の判断を維持し、未回答の問いを必要時だけ台帳へ送る。
- **`graph-workflow.md`・ontology**：新しい関係表現を重ねず、`claim` ノード対応は移行を検証してから変更する。
- **`architecture.md`・`scaling-playbook.md`**：方法論マップと、ページ数だけではない導入条件を説明する。
- **`evolution-workflow.md`**：経験則の `kind`・`status` 契約を維持する。
- **テンプレート**：source の振り分け節、任意の claim の節を追加する。全型への空メタデータ追加はしない。

#### 5.9 実在ページの frontmatter 例

以下は将来適用する場合の例であり、ファイルは変更していない。`updated: 2026-11-08` は、その日に例の変更を適用する場合を示す。

**① `sources/semasynth再現性の検証-2026-11-06.md`**

本文に主張・振り分けを追加する。新しい frontmatter キーは必要ない。

```yaml
---
type: "source"
title: "SemaSynth 再現性の検証"
authors: ["Codex"]
raw: "../W1_Raw/semasynth再現性の検証-2026-11-06.md"
ingested: 2026-11-06
created: 2026-11-06
updated: 2026-11-08
tags: ["知識表現"]
---
```

`scope: "project:semasynth"` を加えて保存領域の問題を解決したことにはしない。このページの置き場所の妥当性は、ADR-0008 と照らして別途確認する。

**② `concepts/編集要求の復元世代を最終適用まで保持する.md`**

PoC と分類確認後、既存の主張型ページに `kind` を付ける例である。

```yaml
---
type: "concept"
kind: "claim"
title: "編集要求の復元世代を最終適用まで保持する"
sources: ["output復元資格の設計-2026-11-04"]
created: 2026-11-04
updated: 2026-11-08
tags: ["並行処理"]
---
```

本文の適用範囲には、OUTPUT の二操作と同じゲートを使う実装という制限が既にある［W4］。この制限を残す。`reviewed` や一般的な正しさを示す状態は自動付与しない。ノード型は初期段階では現行の `concept` のままにする。

**③ `concepts/オントロジー.md`**

用語ページはそのまま残す。ここを claim に変えたり、見出しごとにページへ分解したりしない。

```yaml
---
type: "concept"
title: "オントロジー"
aliases: ["ontology"]
sources: ["ontology-and-knowledge-graphs-and-ai-agents", "part-1-what-is-an-ontology-classes-properties-and-axioms", "part-4-extracting-ontologies-from-sources"]
created: 2026-11-04
updated: 2026-11-06
tags: ["知識表現", "AIエージェント"]
---
```

この例は frontmatter を変えない場合である。将来、ページ内の主張を更新したときだけ `updated` を変える。

### 6. 導入の順序・条件・SemVer

現在の 0.6.0 を起点にした例であり、実際の次版は他の変更と調整する。**ページや `SCHEMA.md` だけを個別 wiki で試すことと、プラグインを配布することを区別する。**

| 段階 | 入れるもの | 開始・完了の条件 | SemVer と既存 wiki |
|---|---|---|---|
| 0：既存契約の整理 | 5 区分の案内、現行機能との対応、出典検査の未実装範囲を明示 | 今すぐ。文章が実装と一致すること | 挙動を変えない訂正なら **パッチ**、例 0.6.1。既存ページの移行なし |
| 1：実際の欠陥を検査 | X1、型別の出典・参照検査 | 作者の 16 件を検出し、テーマ別 MOC を誤検出しない。グラフなしでも検査可能 | 新しい検査機能として **マイナー**、例 0.7.0。まず報告・警告。既存ページを拒否・自動修正しない |
| 2：振り分けを試す | 主張一覧、`create/update/source_only`、任意の `kind: "claim"` | 固定した資料・初期 wiki で、現行との比較 PoC に合格 | 個別試行だけなら配布版変更なし。スキルの新手順として配るなら **マイナー**。新規 ingest と選定した数ページから開始 |
| 3：探索の不足を補う | CQ 台帳、必要な MOC、Middle-out | 同じ未回答質問が再発する、既存ページが見つからない等の具体例がある | 任意機能の追加は **マイナー**。全 57 ページへの `answers` 等の追記なし |
| 4：需要別の拡張 | howto、plan、限定 fix、レビュー機能、broader | それぞれの需要・責任・検査条件を満たす。相互に必須の前段階にはしない | 個別の **マイナー**。対象 wiki のオプトインと差分移行 |
| 非推奨：一括再設計 | 必須 id/status、旧型・コマンド廃止、全スラッグ変更 | 今は開始条件を満たさない | **破壊的変更**として扱う。安定版ならメジャー相当。今回は行わない |

SemVer では 0.y.z は初期開発段階で、安定した公開 API を保証する段階ではない。ただし、それを既存 wiki を壊してよい理由にはしない。info-hive ではページ形式・コマンド・規約を利用者との契約として扱い、破壊的変更なら別の移行計画を要求すべきである。[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)

配布時は AGENTS.md に従い、`plugin.json` と `CHANGELOG.md` を同時に更新する。marketplace の項目に `version` は加えない。今回、リリース作業はしていない。

**PoC の提案条件**

- 固定した三つの資料を使う。オントロジー系、SemaSynth の設計判断、進捗中心の記録を含める。
- 現行と変更案を、独立した初期状態・複数回で比較する。保存済み振り分け表を再読して得た一致を、独立一致と数えない。
- 根拠の捏造・条件の脱落・無断の適用範囲拡張は **0 件を必須条件**にする。
- 再処理による重複・不要な改名も 0 件を求める。
- 配置一致率 85% など、直前の検討で提示された値は暫定値として扱う。
- 全件 `source_only` で一致率を稼ぐことを避け、人が再利用可能と判断した知見の取り出しと、質問への回答改善を測る。
- 作者の確認時間、訂正回数、読んだページ数、トークン量を現行と比較する。ページ数の増加だけでは成功としない。

## 検討した代替案

| 代替案 | 採らない理由 |
|---|---|
| 原案をまとめて導入する | 保存範囲・識別子・状態・関係表現を同時に変え、効果と移行不具合の原因を分けられない。ADR とも衝突する |
| 文書の改訂だけで済ませる | 主張の振り分けは改善できるが、索引分類と型別出典検査の穴はコードを変えないと埋まらない |
| 全面的な 1 主張 1 ページ | 直前の検討に反する。条件付き判断や用語の入口が分散し、作者の確認負担も増える |
| すべて現行のまま | 既存の機能は多いが、source の振り分け記録と実際の索引誤分類を放置する |
| `relations` を平坦な `broader`・`related` に置き換えるだけ | 解析上の問題は減るが、本文リンク・型付きエッジとの二重管理、意味・根拠・同期責任は残る |
| 全記事を人がレビューしてから使う | LLM が整理を受け持つ利点を失い、作者が恒常的なボトルネックになる |
| LLM が自分の記事を自動で正典化する | 生成と確認が同じ誤りを共有しうる。構文適合や出典の存在だけでは、内容の正しさを確定できない |
| CQ を全領域で先に大量生成する | 作者の需要より LLM が想像した網羅性を優先し、未回答バックログと空ページを増やす |

### 提案自体の誤り・不整合

以下は校正・仕様の不足として扱い、方法論の採否とは分けた。

1. **「8 コマンド」と一覧が一致しない。** 一覧は 6 本で、外に置くとされた `graph` を加えても 7 本である。
2. **表記の誤り**がある。`/wik:lint`、`/wiki promote`、`<pathっurl>`、`syntesis` は、それぞれ既存の表記と合わない。
3. `/wiki:plan` の説明に **`answer`** が現れるが、そのコマンドは一覧にない。
4. スキルを `wiki` と呼んでいるが、現行はプラグイン名 `wiki`、スキル名 `info-hive`。
5. スキーマ例の状態は **四値**だが、ロードマップは「三段階」とする。また初期から全記事 draft としながら、status の有効化はフェーズ 2 としている。
6. 「正典ページへの直接書き込みをしない」と、ingest の既存記事への追記が両立する条件を定めていない。
7. 全フィールド必須なのに、作成直後の draft に `reviewed_at` を書く例になっている。未レビュー日付を作る原因になる。
8. `answers` は YAML では `relations` の下だが、説明表では独立フィールドのように扱われる。
9. `scope` は一方で `project`、他方で `project:<name>`。保存先・検索範囲をどう切り替えるかも未定義。
10. スキーマの置き場所が `SCHEMA.md`、`SKILL.md`、`CLAUDE.md` に分散し、優先順位が不明。
11. `sources` は source ページ ID の例なのに、検査説明は「raw/ に実体があるか」。**記事→source→raw** の二段階を混同している。
12. `type` の選択肢とロードマップの初期テンプレートが対応しない。`entity` が必要な ingest に対し、初期テンプレートは source/concept/journal だけである。
13. 「出典とリンクを検査すれば正典化できる」「howto の説明混在を lint が検査できる」という記述は、構造検査と意味判断を分けていない。
14. 「SKOS 風」とするなら、`broader` の向き、`related` の対称性などを明示する必要がある。また循環禁止は SKOS 自体の必須制約ではなく、採用するアプリ側の規則である。[SKOS Reference §8](https://www.w3.org/TR/skos-reference/#semantic-relations)
15. 失われた画像の内容は確認できない。本文に書かれた四段階と合図だけを評価し、画像を推測で補っていない。

## 前提と不確実性

- **これは独立評価である。** 指定された今回の他エージェント成果ディレクトリは読んでいない。追加エージェントも起動していない。
- 本体は指定された別パスを読んだ。確認したのはその作業ツリーの 0.6.0 であり、インストール済み版や公開 main と同一かは確認していない。
- 直前の粒度検討は前提にしたが、文書自身の状態は「提案、ADR 未作成」である。承認済み ADR と同じ確定度ではない［D4］。
- 作者の wiki の件数と索引分類は再確認したが、全ページの内容・原資料を完全監査したわけではない。raw まで読んだ作例は、SemaSynth 再現性と OUTPUT 復元資格の二件である。
- `broader`・レビュー状態・新型を加えた場合の検索、Foam、グラフ、MCP の一連の互換性は実行検証していない。
- 作者の wiki にプロジェクト固有の記録が存在することは、ADR-0008 を変更すべき証拠にはならない。既存記録をどこまで残すか、一般化した知見と製品固有情報をどこで分けるかは、作者の方針確定が必要である。
- `log` は未実装だが、その不在を理由に journal を wiki に暫定収容する案は採らなかった。既存の作業領域のノートを素材として保持できるためである。
- 型別索引検査では、任意の見出し名を自動でページ型と断定できない。`SCHEMA.md` の対応表、または既定の型別索引だけを検査対象にする必要がある。
- 今回の提案には `reviewed` の責任者・効果の測定結果がない。レビュー機能を採る際は、作者の確認時間と実際の誤回答の減少を測る必要がある。

**評価基準への異議は三つある。**

第一に、「既存設計との整合」と「実装・移行の軽さ」で 35% を占めるため、現行の維持が有利になる。価値重視 A はこの偏りへの感度確認だが、完全には解消しない。

第二に、「検査可能性」は、**値を検査できることと、知識の正しさを検査できることを分けるべき**である。`id` の一致は簡単に検査できても、重要な問題を解くとは限らない。

第三に、出典への忠実さ、条件の保持、保存領域の遵守は加重平均で相殺すべきではない。これらを満たした案について、価値・手間・軽さを比較するのが妥当である。

## 参照

パスは今回読んだ実体を示す。本文の行番号は今回のファイル内容に基づく。

### プラグイン・コード

- **P1**：[plugin.json](C:/Works/info-hive-dev/info-hive-wiki/.claude-plugin/plugin.json:3)、`commands/*.md` の全 10 本。特に [lint.md](C:/Works/info-hive-dev/info-hive-wiki/commands/lint.md:1)、[graph.md](C:/Works/info-hive-dev/info-hive-wiki/commands/graph.md:1)、[upgrade.md](C:/Works/info-hive-dev/info-hive-wiki/commands/upgrade.md:1)。
- **P2**：[ingest-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:129)：手順 3〜10、147–175 行の source 要約、177–201 行の更新・新規作成、209–221 行のグラフ・ログ。PDF は 11–31 行。
- **P3**：[lint-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/lint-workflow.md:9)：構造と内容の分担、修正提案、58–80 行の意味判断と候補抽出。
- **P4**：[query-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md:59)：回答、矛盾、不足、保存提案。95–115 行の特殊クエリ・避けるべきパターン。
- **P5**：[wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:126)：除外対象、215–263 行の収集、276–419 行の必須項目・検査、541 行以降の引数。
- **P6**：[wiki_text.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:259)：`_fm_raw_values`、`parse_frontmatter_text`。
- **P7**：[wiki_graph_extract.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:149)：PyYAML の解析、238–298 行の型・ID、333–441 行のエッジ生成。
- **P8**：[graph-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:30)、[ontology.yaml.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/ontology.yaml.template:11)：必須証拠、型付き関係と wikilink の区別、`claim`・`decision`、`depends_on` の型。
- **P9**：[scaling-playbook.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/scaling-playbook.md:74)：独自型を追加する条件、規約の見直し。
- **P10**：[SKILL.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md:21)、[page-conventions.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md:7)、[architecture.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/architecture.md:1)：wiki の選択、SCHEMA の優先、必須項目、スラッグ、正本。
- **P11**：[SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template:55)、[page.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/page.md.template:1)、[evolution-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/evolution-workflow.md:121)：型別項目、既存テンプレート、経験の記録。

### 設計・直前の検討

以下の相対名は、今回の作業ツリー `C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/` にある。

- **D1**：[ADR-0006](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0006-daily-journal-is-separate-plugin.md:26)：決定表、40 行の知識取り出し、83 行以降の理由。
- **D2**：[ADR-0008](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0008-numbered-workspace-layout.md:19)：作業領域、77–105 行の配置と役割、設定・移行規則。
- **D3**：[ADR-0009](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0009-graph-layer-stays-in-wiki.md:24)：任意索引としての決定、50 行以降の境界、66 行以降の見直し条件。
- **D4**：[粒度検討レポート](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/research/wiki-note-granularity-2026-11-08.md:18)：併用案、100–127 行の振り分け・frontmatter、138–171 行の PoC と移行。[その総括](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/agent-runs/2026-11-08-wiki-note-granularity-atomic-evergreen/summary.md:3)も参照。
- [AGENTS.md](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/AGENTS.md:1)、[porting-plan.html](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/porting-plan.html:493)：方針 B、スラッグ、リリース規則。
- 検討対象の提案：本タスクに貼り付けられた「LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計」。

### 作者の wiki・原資料

- **W1**：[index.md](D:/Users/toshiki/info-hive/W0_Wiki/index.md:70)。件数照合のため `sources/`、`concepts/`、`entities/`、`synthesis/` の Markdown を読み取った。
- **W2**：[SCHEMA.md](D:/Users/toshiki/info-hive/W0_Wiki/SCHEMA.md:1)、[log.md](D:/Users/toshiki/info-hive/W0_Wiki/log.md:1)：保存先・型・必須項目・graph・経験則、操作ログ。
- **W3**：[semasynth再現性の検証-2026-11-06.md](D:/Users/toshiki/info-hive/W0_Wiki/sources/semasynth再現性の検証-2026-11-06.md:1)、[対応する raw](D:/Users/toshiki/info-hive/W1_Raw/semasynth再現性の検証-2026-11-06.md:7)。
- **W4**：[編集要求の復元世代を最終適用まで保持する.md](D:/Users/toshiki/info-hive/W0_Wiki/concepts/編集要求の復元世代を最終適用まで保持する.md:1)、[対応する raw](D:/Users/toshiki/info-hive/W1_Raw/output復元資格の設計-2026-11-04.md:3)。
- **W5**：[オントロジー.md](D:/Users/toshiki/info-hive/W0_Wiki/concepts/オントロジー.md:1)、[yuan-an.md](D:/Users/toshiki/info-hive/W0_Wiki/entities/yuan-an.md:1)。

### 外部の一次資料

- [Diátaxis — How-to guides](https://diataxis.fr/how-to-guides/)
- [W3C — SKOS Reference, §8 Semantic Relations](https://www.w3.org/TR/skos-reference/#semantic-relations)
- [Noy & McGuinness — Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)
- [Consortium for Service Innovation — KCS Article State](https://library.serviceinnovation.org/KCS/Knowledge-Centered_Success_Practices_Guide/301-Evolve_Loop/Practice_5_Content_Health/Technique_5.2)
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)

使用した MCP サーバー: なし  
使用した Agent Skills: なし


## 相互レビュー

### エージェント A

## エージェント B への攻撃

### 判定
**条件付きで採用可（確信度：中）。** 段階 1（index の検査、source の主張の一覧）は使える。段階 2（`status` の 4 値と `/wiki:promote`）は、下の 2 つの欠陥を直すまで採用できない。

### 致命的・重大な欠陥
1. **重大：`experience-pattern` の契約を黙って書き換えている。** B の frontmatter の表は、`status` の 4 値（`disputed` を追加）と「`supported` なら `sources` が 2 本以上」という lint の検査を、`kind: "claim"` と `"experience-pattern"` の両方にかけている。一方で、要約と衝突の表では「既存の experience-pattern を維持」と書いており、自分の中で食い違っている。
   - 現行の契約は `SCHEMA.md.template:194` の `status: hypothesis|supported|superseded` だけである。
   - `evolution-workflow.md` にも `wiki_evolve*.py` にも、「supported なら 2 本以上」に当たる規則はない（grep で確かめた）。
   - 反例：検証済みの経験 1 件をまとめた正当な `supported` のパターンが、B の lint では誤りとして報告される。
2. **重大：段階 2 の合図が PoC を迂回している。** 合図は「PoC が合格したら。**または**、`source_only` 以外の行き先が 10 件以上たまったら」である。
   - 後者の件数は、LLM が付けた `create`/`update` の判定そのものを数えている。直前の検討が「機械化できていないので PoC で測る」とした判定である。検証していない判定の件数を、その判定の制度化の根拠にしており、循環している。
   - 要約の 3 番目「PoC を通ってから入れる」とも矛盾する。
3. **重大：「最初に入れる 3 つ」が自分の採点と食い違う。** 「採点と条件の両方で先頭に来るもの」と書いているが、3 番目の claim、`status`、`promote`（E07′ 6.60、E17′ 6.55）は W1 で 6〜7 位である。B 自身が上位 3 つを E23、E21、E03 と書いている。しかもこの項目は PoC 待ちなので、「最初に」入れることもできない。

### 崩れる前提
- 「同じ source の数が 2 本以上なら裏づけがある」という前提。直前の検討の 7 節 2 が、同じプロジェクトの複数の記録は独立した裏づけではないことを示している。作者の wiki では SemaSynth の G0〜G3 が同じ事実を何度も記録しているので、2 本以上という条件はすぐに満たされる。lint の検査は必要条件にすぎないが、文書に書けば十分条件として読まれる。
- 「題名が主張の形の既存 concept が 3 本ある」という前提。`BM25 の IDF の式の違い` と `Windows での Tantivy の commit の失敗` の題名は名詞句である（frontmatter を確かめた）。直前の検討 6.4 の「主張ページの題名は文にする」に反するまま `kind: "claim"` を付けることになる。さらに、この 2 本はスラッグに空白を含み、命名規則に違反している。

### 検証した事実
- 一致：`edges.jsonl` の述語の内訳（`mentions` 229、`summarizes_raw` 37、`sourced_from` 32、`authored` 5）。index の誤分類 16 本。`wiki_lint.py` が本文の wikilink だけを集めること。
- 食い違い（軽微）：「SemaSynth の 28 本は `## ` の数が 0〜1」は誤りである。実測すると、0 個が 3 本、1 個が 15 本、2〜6 個が 10 本ある。
- 食い違い（軽微）：「lint を走らせて 0 件だった、すなわち LLM の確認でも見逃されてきた」は推論として成り立たない。lint はスクリプトであり、LLM の確認を表していない。

### 崩せなかった点
「`index_type_mismatch` を最初に入れる」「`id`、`scope`、入れ子の `relations`、`journal` は採らない」「ADR は変えない」の 3 点は崩せなかった。`maps_from` を足したときのグラフの移行も、作者の wiki に関しては B の言うとおり安全である。concept を目的語にする明示エッジは 0 本だった。

## エージェント C への攻撃

### 判定
**採用可（確信度：中〜高）。** 4 体の中で、直前の検討との整合がもっとも崩れにくい。

### 致命的・重大な欠陥
- 致命的・重大なものは見つからなかった。
- 軽微：採点の偏り。変えて導入する要素は変更後の案で、導入しない要素は原案で採点している（C 自身が明記している）。これでは採用する側が高く出ることが初めから決まり、重みを変えても結論が変わらないのは当然である。開示しているので軽微とするが、採点は採否の根拠になっていない。同じ攻撃は B、D、私にも当たる（後述）。
- 軽微：SemVer の段階 A と B の境目があいまいである。出典の検査は、段階 A（「出典必須の説明と実装の整合」、パッチ）にも段階 B（「出典参照の詳細診断」、マイナー）にも入っている。lint の新しい指摘は MCP の `lint` と `--json` の出力を変えるので、パッチとするのは無理がある。
- 軽微：`raw` の検査で「rag の PDF の絶対パスを扱い、別の PC で見つからなければ報告する」としている。`ingest-workflow.md` は「別の PC では PDF の場所が違うことがある」と認めているので、2 台目の PC では lint のたびに同じ指摘が出続ける。ADR-0006 が日付ノートで避けた、毎回の雑音と同じ形である。

### 崩れる前提
「source の主張と配置先の表は PoC のあとに入れる」を、他の 3 体（私を含む）は誤りと見るかもしれない。しかし、配置先を決めることこそ、直前の検討が「機械化できていない、PoC で測る」とした判断である。この点では C がもっとも忠実であり、私はこれを崩せなかった。その代わり、source に溜まる偏りへの手当てが PoC が終わるまで止まる。これは C の弱点である。

### 検証した事実
- 一致：index の 74〜104 行の偶数行に、source が 16 本並んでいること。
- 一致：`DEFAULT_REQUIRED_FM` に `sources` がなく、型ごとの分岐もないこと。
- 一致：`kind: "claim"` を付けるだけでは、ノードは `concept` のままであること（`claim` は `explicit_only`）。
- 一致：作者の wiki は 57 ページで、`plugin.json` は 0.6.0 であること。
- 確かめられず：SKOS と KCS の外部の文書（Web は読んでいない）。SKOS の `broader` が推移的でないという記述は、私の知識とは一致する。

### 崩せなかった点
次の 4 点は崩せなかった。
- `status` を全ページに入れないこと。
- 「形式検査に合格することは内容のレビューの合格ではない」という分離。
- CQ の対応の正本を台帳の側に置き、ページの側に二重に記入しないこと。
- 本文の粒度の改善と、グラフの型の移行を別々に進めること。

## エージェント D への攻撃

### 判定
**条件付きで採用可（確信度：中）。** 結論の骨格は C とほぼ同じだが、CQ の台帳の置き場所に実装上の欠陥がある。

### 致命的・重大な欠陥
1. **重大：`indexes/questions.md` は index の層を汚す。**
   - MCP の `list_index` は、`index.md` と `indexes/` の下の全ファイルを「インデックス」として返す（`wiki_index.py:953–974`）。インデックスを先に読むナビゲーションで、エージェントが問いの台帳を目録として読むことになる。
   - `wiki_stats.py` は `has_indexes = (wiki/"indexes").exists()` で判定し（189 行）、分割の助言を `not has_indexes` のときだけ出す（99 行）。`indexes/questions.md` を 1 つ置くだけで、150 ページか 300 行に達しても `stats` は index の分割を勧めなくなる。
   - D は「indexes/ が通常の lint の対象外なので、専用の検査が要る」までは書いているが、この 2 つの副作用には触れていない。
2. **重大：採点が採否を支えていない。** D は原案を採点したが、採否は点数と逆に動いている。D1（4.75）、F7（4.20）、F8（5.30）、R2（4.50）、R4（4.55）、K1（5.35）は変えて導入するのに、F5 `reviewed_at`（7.10）と C4 `--fix`（6.95）は保留である。さらに、最初の 3 つの 3 番目「型別の出典検査」は、独立した要素として採点表にない（F1 には `status` が混ざっていて 6.15）。「重みを変えても採否の結論は変わらない」は、点数で採否を決めていない以上、何も言っていない。

### 崩れる前提
- 主張の表の「根拠」の列に「原資料の節・ページ・行」と引用を書かせているが、rag 連携の PDF では `raw:` が絶対パスで、行を定義できない（直前の検討の 10 節）。PDF の取り込みでは、この列が埋まらないか、場当たりの値になる。
- 作者の SCHEMA のソフト上限は 4,000 文字である。Part 2 と Part 3 の source は、すでに空白を除いて約 2,990 文字ある（実測）。5 列の表に引用を付けた行を 5〜8 行足すと上限を超える見込みが高い（推測。行あたり 150〜250 文字と仮定した）。この攻撃は B、C、私にも当たる。
- 5 区分のマップを `SKILL.md` の案内に入れると、毎回読み込まれる文脈が増える（`SKILL.md` は 233 行ある）。軽微。

### 検証した事実
- 一致：「シンセシス」の欄は 18 項目で、そのうち 16 本が source であること。
- 一致：`graph.canonical` が既存の意味（別名の代表ノード）を持つこと。
- 一致：作者の wiki の明示エッジは `authored` の 5 本だけで、目的語はすべて source であること。
- 一致：`indexes/` が lint、search、extract、stats の走査対象から外れていること。
- 確かめず：raw の 7 行目と 11 行目の内容。

### 崩せなかった点
次の 4 点は崩せなかった。
- `kind` の追加と、ノード ID の変更（`maps_from`）を別々に進めること。
- `canonical` を採らない理由（`graph.canonical` との意味の衝突）。
- レビューの状態を `status` と別のキーにし、内容が変わったら失効させること。
- `scope` は保存場所の問題を解かないこと。

## 自分の成果の見直し

- **事実の誤り（軽微。結論は変えない）**：私は「使われているタグは 4 つとも SCHEMA の一覧に載っているので、⑥ の機械的な検査は今は 0 件」と書いた。これは source のタグだけを数えた誤りだった。wiki 全体を数えると、`Windows`（2 件）、`Claude Code`（1 件）、`MCP`（1 件）が SCHEMA の一覧にない。`手法`（2 件）と `未解決`（1 件）は「構成の例」として載っているだけである。⑥ の検査は 4〜7 件を見つけるので、価値は少し上がる。段階 1 に入れるという結論は変わらない。
- **採点の偏り**：C と D への攻撃は私にも当たる。私も、変えて導入する要素は変更後の案で（⑭ の述語の `broader`、⑬ の `kind: "decision"` など）、導入しない要素は原案で採点した。B も同じである。4 体とも、採点は採否の根拠になっていない。
- **PoC の前に制度化している（中）**：私は段階 2 で、取り込みの手順 6 と 7 を「行き先どおりに更新する」と改訂した。これは、検証していない配置の判断を PoC の前に手順に組み込むことであり、C の立場から見れば直前の検討に反する。反論はある。今も手順 6 と 7 で同じ判断をしていて、それを記録して見えるようにするだけである。ただし、この反論で C の指摘を崩しきれてはいない。結論は「記録は段階 2 で入れ、行き先に従う規定は PoC のあと」に改める。
- **source の上限**：作者の wiki のソフト上限 4,000 文字への影響は、私の主張の一覧（`→` の印を付けた箇条書き）でも同じように起きる。表より軽いが、検証していない。
- **グラフの移行**：段階 3 で `kind: "claim"` と `maps_from` を一緒に入れる計画は、作者の wiki では安全だった（concept を目的語にするエッジは 0 本）。ただし他の利用者の wiki では、C と D が言うように分けて入れるほうが安全である。そちらに改める。

## 生き残った案と確信度

| 案 | 判定 | 確信度 |
| --- | --- | --- |
| C | 攻撃に耐えた。直前の検討ともっとも整合し、致命的・重大な欠陥はない | 中〜高 |
| D | 骨格は耐えた。CQ の台帳を `indexes/` に置く案は耐えなかった（`list_index` と `stats` への副作用） | 中 |
| A（私） | 骨格は耐えた。タグの件数の誤りを直し、行き先に従う規定は PoC のあとに回す | 中 |
| B | 段階 1 は耐えた。段階 2 は耐えなかった（`experience-pattern` の契約の書き換え、PoC の迂回、最初の 3 つと採点の食い違い） | 中〜低 |

4 案に共通して攻撃に耐えた核は次のとおりで、ここの確信度は高い。
- index の見出しと `type` の照合を最初に入れる。
- `sources` と `raw` の参照の検査を入れる。
- `id`、`scope`、入れ子の `relations`、`journal`、全ページの `status`、出典なしの `draft` は採らない。
- ADR は変えない。

使用した MCP サーバー: なし
使用した Agent Skills: なし

### エージェント B

## エージェント A への攻撃

### 判定
**条件付きで採用可（確信度 中）。** 採否の区分と ADR を変えない結論は妥当だが、未回答の問いを `log.md` に置く設計（⑧）は検査できず、実測値に 1 件の誤りがある。

### 致命的・重大な欠陥

1. **重大：⑧「未回答の問いを `log.md` に `gap` の行で残す」は、A 自身が検査 7 点を付けた「未回答 CQ の検査」を成立させない。** `log.md` は追記専用（作者の `log.md` 冒頭、`log.md.template`）で、問いに答えたあとに行を「回答済み」に変える手段がない。lint 手順 4 で `grep "] gap |"` を読むと、答えた問いも永久に候補として再報告される。「回答済み」の行を別に追記して照合する規則も書かれていない。A が代替案で `questions.md` を「ファイルの規約と `SKIP_TOP_LEVEL_FILES` の変更が余分」と退けた理由は、`log.md` 側に状態がない欠点と釣り合っていない。
2. **重大：⑭「`broader` を既存の `graph.relationships` の述語にすればスクリプトを変えずに書ける」は、文書の契約と食い違う。** `wiki_graph_lint.py` 246〜250 行は `requires_evidence: false` なら `evidence` と `source` を要求しないことを確かめた（A の記述は正しい）。しかし `SCHEMA.md.template` と作者の `SCHEMA.md` は「すべての関係に必須のフィールドは `predicate`、`object`、`source`、`evidence`、`confidence`、`status`」と書いており、`graph-workflow.md` も型付きエッジに明示的なソースと引用を求める。A の案は、分類の関係を証拠なしの型付きエッジとして書く新しい規約を `SCHEMA.md`・`graph-workflow.md`・`ingest-workflow.md` 手順 8b に足すことを意味し、「スクリプトを変えずに済む」だけで「軽さ 8」とは言えない。さらに、各 concept ページに入れ子の `graph:` ブロックを書く入力の手間は、平坦な 1 キーより大きい。A は手間 5 としており、代替案で退けた「平坦な `broader` キー」より手間が重い案を選んだ理由が、スクリプト変更の有無だけになっている。
3. **軽微（事実の誤り）：`invalid_slugs` の件数 3 は誤り。** 空白を含むファイル名は `concepts/` の 3 本に加えて `synthesis/LLM Wiki で蓄積した情報の活用方法.md` があり、wiki 全体で **4 本**（`find . -name "* *"` で確認）。A は「作者の concepts には 3 本」と範囲を限って書いているが、lint の検査は wiki 全体に当たるので、採点表の「3 件を見つける」は 4 件になる。なお直前の検討の総括が「B の 4 件は誤り」としたのも誤りで、A はそれを引き継いだと推測する。
4. **軽微：② `sources`・`raw` の実体検査を「最初の 3 つ」に入れているが、A 自身が価値 5、作者の wiki で 0 件と認めている。** 課題の「価値」は「作者の wiki の実際の問題を解く」ことなので、0 件の予防検査を ⑤（必須の節。32 件に当たる）より先に置く根拠が点数にも実測にもない。
5. **軽微：`--fix` の禁止根拠として `SKILL.md` 132 行を引いているが、その行は MCP のツールが書き換えないことを述べた文である。** スクリプトの契約は `lint-workflow.md` 42 行「検出結果を報告するが、修正はしない」であり、結論は変わらないが引用先が違う。

### 崩れる前提

- 「`index.md` の見出しは `type` の別名表と一致する」。作者の wiki では成り立つが、`index.md` の冒頭の説明文に `[[消費税]]` という例のリンクがある（3 行目）。見出しの下の wikilink だけを読む実装にしないと、存在しないページへの参照として誤検出する。A はこの前処理を書いていない（他の 3 体も同じ）。
- 「作者のグローバルの指示が、プロジェクトの知見をユーザースコープの wiki に残すよう求めている」。A が唯一これを挙げた点は正しい（`~/.claude/CLAUDE.md` に「どのプロジェクトの作業でも…`~/info-hive/W0_Wiki/` に残す」とある）。ただし A はそれを ADR-0008 の「字面」との食い違いと呼び、どちらを直すべきかを作者に委ねている。これは判断として妥当だが、提案の `scope` を退ける理由（ADR-0008）と、作者の運用（ユーザースコープに混在）が逆向きである点を明示していない。

### 検証した事実

| A の主張 | 結果 |
| --- | --- |
| `## 主な主張` がある source は 37 本中 5 本 | **一致**（`grep -l "^## 主な主張"` で 5） |
| `## 関係するページ` がない source は 6 本 | **一致** |
| source 37 本のうち 29 本が `["知識表現"]` だけ | **一致** |
| `log.md` に書式から外れた行が 1 行（`- 2026-11-07 ingest: ...`） | **一致**（140 行目） |
| index に載っていないページは 0 件 | **一致**（57 ページすべてが index の wikilink にある） |
| 空白を含むファイル名は 3 本 | **食い違い**（wiki 全体では 4 本） |
| `wiki_graph_lint.py` は `requires_evidence: false` で `evidence`・`source` を要求しない | **一致**（246〜250 行） |
| `page-conventions.md` は正式なタグ以外に lint が警告すると書くが、実装がない | **一致**（`page-conventions.md` 39 行、`wiki_lint.py` の findings に tag の項目なし） |
| `wiki_lint.py` は `index.md` を走査から外す（126 行） | **一致** |

### 崩せなかった点

- 4 区分の振り分け、ADR を変えないという結論、`id`・`scope`・入れ子 `relations`・全ページ `status` を退ける理由は、コードと ADR の引用に裏づけがあり崩せなかった。
- 「提案の ingest の手順は現行より後退している」という指摘は、`ingest-workflow.md` 手順 3・6・7・8b との比較で正しい。

## エージェント C への攻撃

### 判定
**条件付きで採用可（確信度 中）。** 衝突の解き方と不採用の理由は堅いが、採点表が「維持する既存機能」で膨らんで順位が読めず、主張ページの失効を表す手段がない。

### 致命的・重大な欠陥

1. **重大：`kind: "claim"` のページに `status` を一切付けない設計で、古くなった主張を機械的に見つける手段がない。** C は「共通 `status` は導入しない」とし、frontmatter の例（`編集要求の復元世代を最終適用まで保持する.md`）にも `status` がない。しかし直前の検討の総括は「流用しないと、グラフを有効にしない wiki で古い主張を query から除く手段がなくなる」を残る論点として挙げている（`summary.md` 残るリスク）。C の lint の表には主張の失効・置き換えの検査がなく、`experience-pattern` だけが `superseded` を持つ非対称が残る。「編集状態、確からしさ、失効を一列に混ぜない」なら、失効だけを表す別のキーが要るが、C はそれも示していない。
2. **重大：採点表の上位が「既存機能を維持する判断」で占められ、新規投資の順位として読めない。** 42 要素のうち、23（raw 不変）、25（SSOT）、29（ログ）、36（graph 入口維持）、40（Docs as Code）、32（既存 ingest 維持）、14（既存索引による MOC）は何も変えない判断で、基本重みで 3〜9 位に並ぶ。C は「既存機能を残す判断と新規実装の優先順位は別」と断っているが、課題が求めたのは提案の要素の採否であり、「維持」を 7 件採点に混ぜると、本来の 2 位（31 主張・配置表 8.30）が 14 と 36 と同点に見える。
3. **重大：「出典参照 lint」を価値 8 で 2 位に置いているが、作者の wiki では 0 件である。** C 自身が A・D と同じく `sources` と `raw` の不整合を見つけていない（見つけたとは書いていない）。課題の「価値」の定義は「作者の wiki の実際の問題を解く」であり、0 件の検査に価値 8 を付けるのは基準の読み替えである。これが最初の 3 つの 2 番目を決めているので、順位に影響する。
4. **軽微：SemVer の判断が段階 A と B で食い違う。** 段階 A は「既存規約の警告追加ならパッチ候補」とし、段階 B は「新しい診断能力としてマイナー」とする。lint に新しい検出項目を足すのは、`--json` に新しいキーが増える後方互換の機能追加であり、SemVer 2.0.0 ではマイナーである。この repo の `CHANGELOG.md` でも 0.5.0・0.6.0 は同種の追加でマイナーにしている。
5. **軽微：`/wiki:promote` を「レビュー承認」としてだけ読み、直前の検討が求めた「source から知見へ昇格させる判定手順」としての読み替えを検討していない。** 提案の promote が status 昇格であることは正しいが、採否の表で「変える」余地を 20 行目で「保留。設計し直す必要」と止めており、何に変えるかがない。

### 崩れる前提

- 「CQ 台帳は 3〜5 件から始めれば作者の手間は小さい」。台帳の列（識別子、回答条件、4 値の状態、回答先、不足根拠）を全部埋めるのは作者か LLM かが書かれていない。LLM が埋めるなら「問いが解けたか」の意味判断を LLM が書くことになり、C 自身の「意味判断は作者」と矛盾する。
- 「`questions.md` を検索・統計・lint・グラフから除外すれば済む」。除外先を名指ししていないが、`wiki_lint.py` 126 行、`wiki_graph_extract.py` 174 行、`wiki_search.py` 287 行の 3 か所がそれぞれ独自の skip 一覧を持ち、さらに MCP サーバー（`wiki_index.py`）がある。1 か所の変更では済まない。
- 外部の一次資料（SKOS Reference、Diátaxis、KCS）はこの環境で取得できず、**確かめられず**。`skos:broader` が推移的でないこと、`skos:related` が対称であることは記憶と一致する（推測）。

### 検証した事実

| C の主張 | 結果 |
| --- | --- |
| 「シンセシス」の誤分類は 74〜104 行の偶数行の 16 件 | **一致**（照合スクリプトで同じ行番号） |
| 57 ページ（37/17/1/2） | **一致** |
| `/wiki:plan` は query の「トピック X について足りないものは？」で試せる | **一致**（`query-workflow.md` 95〜97 行に同じ特殊なクエリがある） |
| `kind: "claim"` を足しただけでは現行オントロジーで `concept` ノードのまま | **一致**（`derive_node_type` は `(type, kind)` を先に照合するが、テンプレートの `claim` に `maps_from` がない） |
| 通常パーサーは入れ子を空配列にする | **一致**（`wiki_text.py` 282〜298 行の docstring と `_FM_KEY_RE`） |

### 崩せなかった点

- 衝突の表（ADR-0006・0008・0009、方針 B、平坦 frontmatter、`status` の 3 系統）の解き方は、どれも引用先と一致し崩せなかった。
- 提案自体の誤りの一覧は 4 体の中で最も網羅的で、「初期テンプレートに entity がない」「`sources` の検査が raw と source を混同」は他の 3 体にない指摘で正しい。

## エージェント D への攻撃

### 判定
**条件付きで採用可（確信度 中）。** 最も慎重で引用も正確だが、`indexes/questions.md` の置き場所が既存のスクリプトと手順を誤動作させ、主張ページの失効の手段が C と同じく欠けている。

### 致命的・重大な欠陥

1. **重大：`questions.md` を `indexes/` に置く案は、統計と手順の両方を壊す。**
   - `wiki_stats.py` 189 行は `has_indexes = (wiki / "indexes").exists()` で分割済みかを判定し、99 行で `has_indexes` が真なら `split_index` の助言を出さない。`indexes/questions.md` を作った時点で、150 ページに達しても「index.md を分けることを検討する」が二度と出なくなる。
   - MCP の `list_index`（`wiki_index.py` 953〜974 行）は `indexes/` のファイル一覧を返す。`query-workflow.md` 手順 1 と `commands/query.md` 手順 2 は「インデックスが `indexes/` に分割されている場合は該当する分割インデックスを読む」としているので、LLM は `questions.md` を索引の分割ファイルとして読む。
   - D は「`indexes/` が通常 lint の対象外なので専用の台帳検査が要る」とだけ書き、上の 2 つの副作用に触れていない。ルート直下に置く案（私）や `log.md` に置く案（A）に対する優位として挙げた「新型を増やさない」は、この副作用で相殺される。
2. **重大：主張ページに `status` を付けず、失効の手段がない。** C と同じ欠陥である。D は「編集状態、確からしさ、失効を一列に混ぜない」と書き、`review_state` の将来案は示したが、`superseded` に相当する印は示していない。D 自身が直前の検討の総括を参照しているのに、そこに残された「古い主張を query から外す手段」の論点に答えていない。
3. **軽微：最初の 3 つの 3 番目「型別の出典検査」は、D の採点表で独立した行を持たない。** 対応する F1（`type/status` 別 lint）は 6.15 で 12 位、D が保留にした F5 `reviewed_at`（7.10）と C4 `--fix`（6.95）より低い。D は「順位は決定的でない」と断っているが、最初の 3 つの選択が自分の採点に支えられていないことは示すべきだった。
4. **軽微：ADR-0008 とユーザースコープの混在について、作者のグローバルの指示が混在を指示していることを挙げていない。** D は「ADR-0008 を変更すべき証拠にはならない」と書くが、`~/.claude/CLAUDE.md` は「どのプロジェクトの作業でも…`~/info-hive/W0_Wiki/` に残す」と求めている。衝突は提案とではなく、作者の 2 つの決定の間にある。これを書かないと、作者は何を決めるべきかが分からない。

### 崩れる前提

- 「`index.md` から `indexes/questions.md` へ Markdown リンクで案内すれば lint の孤立に当たらない」。これは正しい（`index.md` は走査外）が、上記 1 の副作用のほうが大きい。
- 外部の一次資料（Diátaxis、SKOS、Ontology Development 101、KCS、SemVer）は取得できず**確かめられず**。SemVer 2.0.0 の「0.y.z は初期開発」は記憶と一致する（推測）。
- 「`--fix` は定義済みの機械的修正への指示として扱い、同じ承認を何度も求めない」。これは `lint-workflow.md` 手順 2「承認するのはユーザー」と `architecture.md`「変更はユーザーが承認する」の契約を変える。D は「整合を明文化」と書くが、契約の変更であることを採点（C=6）に十分反映していない（推測）。

### 検証した事実

| D の主張 | 結果 |
| --- | --- |
| 「シンセシス」欄は 18 項目、うち 16 本が source | **一致** |
| raw の 7 行目が同一環境と異環境の判定を分けている | **一致**（`W1_Raw/semasynth再現性の検証-2026-11-06.md` 7 行目） |
| 明示的な `graph:` は `yuan-an.md` だけで、5 本の `authored` の目的語はすべて source | **一致**（`edges.jsonl` の述語の内訳と frontmatter） |
| `canonical` は既存の `graph.canonical` と意味が違う | **一致**（`SCHEMA.md` の graph の例に `canonical: true`） |
| `scope` が `project` と `project:<name>` で揺れている | **一致**（提案の「状況別の使い分け」と「記事スキーマ」） |
| `indexes/` は lint の走査外 | **一致**（`SKIP_TOP_LEVEL_DIRS`） |
| `wiki_stats.py` が `indexes/` の存在で分割済みと判定する | **一致**（D は触れていないが、D の案に当たる） |

### 崩せなかった点

- 衝突の表と「承認済み ADR を変える必要はない」は崩せなかった。
- 「`kind` の追加だけではノード ID を変える必要はない。`maps_from` は別の移行にする」は、`derive_node_type` の実装と一致し、直前の検討のグラフ移行の論点を正しく分けている。
- 「`編集要求の復元世代…` の番号付きの三つの境界は手順ではなく設計の一体性」という Diátaxis への反例は、ページの本文（31〜34 行の適用範囲）と一致し、絶対規則として書いた側（私を含む）に当たる。

## 自分の成果の見直し

同じ攻撃が自分に当たるものを隠さず挙げる。

1. **`index_type_mismatch` の前処理を書いていない（A・C・D と共通）。** `index.md` 3 行目の説明文に `[[消費税]]` の例があり、見出しの下の項目だけを読む実装にしないと誤検出する。結論は変わらないが、段階 1 の lint の仕様に「`---` より後、`## ` 見出しの下の wikilink だけを対象にする」を足す。
2. **`questions.md` の置き場所。** 私はルート直下に置き、`SKIP_TOP_LEVEL_FILES` などの変更が要ると書いた。今回 `wiki_graph_extract.py` 174 行と `wiki_search.py` 287 行も独自の skip 一覧を持つことを確かめたので、変更は少なくとも 3 スクリプトと MCP サーバーに及ぶ。D の `indexes/` 案の副作用（統計、`list_index`）を見ると、ルート直下に置いて skip 一覧を直す私の案のほうが副作用は小さいが、「軽さ 6」は 5 に下げるべきである。段階 3a の位置づけは変えない。
3. **「手順と概念を混ぜない」を結論の要約で絶対規則のように書いた。** D の反例（`編集要求の復元世代…` の番号付きの境界）は私の E22 にも当たる。詳細の節では「手順が主のページ」と限定していたので、要約の文言を「別の目的で読む長い手順は分ける。設計の説明に含まれる番号付きの記述は対象外」に改める。採点は変えない（価値 4 のまま）。
4. **`supported ⇒ sources が 2 本以上` の検査は、同じプロジェクトの記録を独立した裏づけと数える。** 直前の検討の総括が指摘した穴で、私は「独立性は検査できない」と書いたが、作者の wiki では SemaSynth の 28 本が同一プロジェクトなので、この検査はほぼ常に `supported` を許してしまう。検査の価値を 7 から 6 に下げる。`status` を claim に限って入れる結論は変えないが、`supported` の条件を「異なる `tags` か異なる著者の source が 2 本以上」のように狭める必要がある（これも機械的には近似にすぎない）。
5. **C と D が主張ページに `status` を付けない点を攻撃したが、逆に私の 4 値には「3 系統目を作らない」という C・D の攻撃が部分的に当たる。** 私は `experience-pattern` の 3 値に `disputed` を 1 つ足しただけなので新しい系統ではないと主張できるが、`experience-pattern` の `pattern.md.template` と `evolution-workflow.md` には `disputed` がなく、同じ `kind` 族で値の集合が違うことになる。`disputed` を外して 3 値にそろえ、矛盾は本文の `## 矛盾` の見出しの有無で lint する案のほうが整合は高い。結論の要約の「4 値」は「3 値（`hypothesis` / `supported` / `superseded`）に `## 矛盾` の見出し検査」に改めてよい。確信度は中。
6. **私の `concepts:` キーを行き先の記録に使う案は、lint が frontmatter のリストを被リンクに数えないので新しいコードである**と書いたが、同時に `page-conventions.md` が「付属のスクリプトは `entities:`・`concepts:` のリストをスラッグへの参照として扱う」と書いている文書と実装のずれを、提案自体の誤りとは別の「現行の文書の誤り」として挙げるべきだった。A の「正式なタグの lint が未実装」と同種の指摘である。

結論の区分（導入する / 変えて導入 / 導入しない / 保留）と最初の 3 つは変えない。変えるのは上の 1〜5 の仕様の細部と 2 要素の点数で、順位の上位 3 つは動かない。

## 生き残った案と確信度

| 案 | 結果 | 確信度 |
| --- | --- | --- |
| **4 体の共通の骨格**：index の見出しと `type` の食い違いの lint を最初に入れる、source の主張の一覧と行き先を取り込みに足す、`id`・`scope`・入れ子 `relations`・全ページ `status`・`journal`・`graph` 型・`/wiki:decide` を退ける、ADR は変えない | **耐えた**。4 体が独立に同じ結論に達し、どの攻撃も崩せなかった | 高 |
| **A**：`gap` を `log.md` に残す案、`broader` を証拠なしの型付きエッジにする案 | **耐えなかった**。前者は回答済みの状態を表せず検査が成立しない。後者は文書の契約（全フィールド必須）と食い違い、入れ子の入力が要る | 高（この 2 要素について） |
| **A**：それ以外（lint の 7 項目、`## 主な主張` と行き先、`kind: "claim"` に 3 値の `status` を流用、段階と SemVer） | **耐えた**。実測値は 1 件（空白のファイル名 4 本）を除き一致 | 中〜高 |
| **C**：衝突の解き方、不採用の理由、提案自体の誤りの一覧 | **耐えた** | 高 |
| **C**：主張ページに状態を持たせない設計、「維持」を混ぜた採点表、0 件の出典検査を 2 位に置く順位 | **耐えなかった**。失効の手段がなく、順位が新規投資の判断に使えない | 中 |
| **D**：`indexes/questions.md` | **耐えなかった**。`wiki_stats.py` の分割判定と MCP の `list_index` が誤動作する | 高 |
| **D**：主張ページに状態を持たせない設計 | **耐えなかった**（C と同じ） | 中 |
| **D**：衝突の表、`kind` と `maps_from` を別の移行にする判断、Diátaxis を絶対規則にしない反例、PoC の必須条件 | **耐えた** | 高 |
| **私（B）**：区分、最初の 3 つ、段階と SemVer、`/wiki:promote` を source → claim の昇格に読み替える案 | **耐えた**。ただし `questions.md` の軽さ、`supported` の検査、「混ぜない」の文言、`disputed` の追加は上の見直しのとおり直す | 中〜高 |
| **私（B）**：`status` を 4 値にする細部 | **弱い**。3 値にそろえて `## 矛盾` の見出しで補うほうが整合が高い | 中 |

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```

### エージェント C

## エージェント A への攻撃

### 判定

**条件付きで採用可。確信度：高。**  
索引・出典検査を優先する結論は崩せなかった。ただし、追加するログ検査と `broader` の設計は、現行機能との互換性を保てていない。

### 致命的・重大な欠陥

**A-1【重大】ログの検査が、既存機能の正規の出力を不正と判定する。**

A は `malformed_log_lines` について、次のどちらでもない行を検出するとしている。

- `## [YYYY-MM-DD] <op> | ...`
- 3 文字の空白で始まる補足行

しかし、現行の評価ループは次を生成する。

```text
- 2026-11-08: 評価ループ example の 1 回目の学習の記録を取り込んだ。
```

生成箇所は [wiki_evolve_loop.py:474](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:474)。さらに [evolution-workflow.md:129](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/evolution-workflow.md:129) は、この形式を移植元のまま残していると明記している。

したがって、**正常な `/wiki:evolve` の実行後に、新しいログ検査が必ず不正行を増やす**。作者の手書きの逸脱 1 件を検出するだけの変更ではない。

**A-2【重大】`requires_evidence: false` が動くことを、既存の型付き関係の契約と整合する根拠にしている。**

A が提案する `broader` は、出典も引用も持たない明示的な `graph.relationships` を許す。しかし現行の [graph-workflow.md:53](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:53) は、関係に `source`・`evidence`・`confidence`・`status` を必須とし、同文書の「型付きエッジを追加するか」では、ソースが明示する関係と引用を要求している。

コードが `requires_evidence: false` を尊重する、という確認自体は正しい。だが、それは**コードが許す範囲と文書上の契約に差がある**という事実であり、「オントロジーに 1 項目足すだけで既存設計を保てる」証拠ではない。

反例として、A の述語定義に次の関係を与えた。

```text
concept:a --broader--> concept:b
concept:b --broader--> concept:a
```

両エッジとも `source/evidence/confidence/status` を省略した。現行関数の結果は次のとおりだった。

```text
missing_evidence: 0
missing_source_field: 0
invalid_confidence: 0
invalid_status: 0
その他の検出: 0
生成エッジ: 2
```

生成された各エッジでは、四項目すべてが空文字だった。循環も検出されない。なお、循環禁止を SKOS 自体の必須条件だとは主張していない。**原提案にあった循環検査まで、既存グラフ lint が代替できるわけではない**という指摘である。

**A-3【重大】claim のグラフ移行が、参照先 ID の変更だけでは完了しない。**

A の段階 3 は `claim` の `maps_from` を追加し、extract 後の lint で確認する。しかし、次の既存状態では ID の参照切れがなくても壊れる。

```text
a: type=concept, kind=claim
a --depends_on--> concept:b
```

現在の ontology では `a` は `concept:a` となり、この関係は有効である。`claim` の対応付けを追加すると主語が `claim:a` になる一方、`depends_on.subject_types` は `[product, concept]` のままである。

現行関数に入力すると、移行前は検出 0、移行後は次の 1 件になった。

```text
subject_type_mismatch:
  subject: claim:a
  subject_type: claim
  allowed: [product, concept]
```

A は ID 変更の危険には言及しているが、**型制約まで含む移行の完了条件を示していない**。extract と lint は不整合を報告するだけで、移行を成立させない。

### 崩れる前提

- 「現行ログの例外は作者の逸脱 1 件だけ」  
  → 評価ループが別形式を継続的に生成する。
- 「ontology で許可すれば、既存の証拠契約とも整合する」  
  → 通常の明示エッジに対する文書上の必須条件は残る。
- 「ノード ID の移行を確認すれば十分」  
  → 主語・目的語の許容型も変わる。
- 「正式タグの検査は作者の wiki で 0 件」  
  → source だけの集計なら使用タグは 4 種だが、通常ページ全体では 9 種だった。少なくとも `Windows` は正式一覧にないのに、[実在ページ](<D:/Users/toshiki/info-hive/W0_Wiki/concepts/Windows での Tantivy の commit の失敗.md:7>)で使われている。これは**軽微な集計範囲の不一致**だが、全 wiki を対象とする `unknown_tags: 0` の根拠にはならない。

### 検証した事実

| 主張 | 結果 |
|---|---|
| 出典不要の独自述語を現行コードで処理できる | **一致**。ただし契約上の妥当性とは別 |
| 既存ログは見出し形式だけで検査できる | **食い違い**。評価ループの正規出力が反例 |
| `maps_from` 追加で claim ノードになる | **一致**。同時に既存述語の型不一致が発生しうる |
| 作者の全ページのタグは正式な 4 種だけ | **食い違い**。source 集合と全ページ集合が異なる |

グラフの試験は、PyYAML が当該 Python 環境にないため CLI 全体では実行していない。実ファイルから AST で取り出した型解決・lint・エッジ生成関数を、ASCII のメモリ上の入力で実行した。YAML の読み書きは検証対象外である。

### 崩せなかった点

- 索引に混在する source 16 本を、型別索引の照合で検出する方向。
- 通常 lint が、文書上の `sources/raw` 規約を十分に検査していないという指摘。
- 全ページへの四値 `status`、`id`、入れ子の `relations` を採らない結論。
- source の主張に行き先を記録する案。ただし、知見の抽出漏れが減る効果までは実証されていない。

## エージェント B への攻撃

### 判定

**却下。確信度：高。**  
索引検査という部分案は残るが、主要な導入段階に検証を迂回する経路があり、作例も配置判断の前提を保てていない。このまま導入計画には使えない。

### 致命的・重大な欠陥

**B-1【致命】PoC 必須という結論を、導入条件自身が無効にしている。**

段階 2 の開始条件は次の OR 条件である。

> PoC が合格したら。**または** `source_only` 以外の行き先が 10 件以上たまったら。

10 件という件数は、配置の独立一致、条件の保持、再利用価値のいずれも検証しない。

具体的には、source 表に次を 10 行作れば条件を満たす。

```text
行き先: update
ページ: 既存の source ページ
```

これは B 自身の作例にもある配置である。concept が 1 本も育たず、複数モデルの一致も測らずに、claim・四値 status・promote・グラフ変更の導入条件を満たせる。

[直前の検討:109](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/research/wiki-note-granularity-2026-11-08.md:109) は、再利用可能性の意味判断が未検証だと明記する。**未検証の判断を何回出したかは、その判断の検証にはならない。**

**B-2【重大】作例の「条件」欄が、再現性判定の適用条件になっていない。**

B の表は、次の主張に対して、

> 同一環境ではバイト一致、異なる環境では値と型の一致

条件欄に、

> 配布形態が Git を含まない場合は環境情報が null

を置いている。

しかし [raw:7](D:/Users/toshiki/info-hive/W1_Raw/semasynth再現性の検証-2026-11-06.md:7) が定めるのは、次の具体的な比較である。

- 異なる **Python・SQLite**。
- **6 テーブルを主キー順**に読み、値と Python に読み戻した型を比較。
- **8 種類の CSV はパース後の全行**を比較。
- 環境情報と DB の物理配置の差は許容。

Git 情報の取得可否は別の 5 行目の話であり、判定方式を選ぶ条件ではない。

B の出力を使うと、「異なる環境」という広い表現から、DB の値・型以外の比較対象や許容差が落ちる。**条件を保持するための表が、原資料の別の話を条件欄に移した実例になっている。**

**B-3【重大】既存 concept 3 本への claim 付与が、本文による選別を飛ばしている。**

移行表は、次の 3 本を「題名が主張の形」として `kind/status` 付与対象にする。

- `編集要求の復元世代を最終適用まで保持する`
- `Windows での Tantivy の commit の失敗`
- `BM25 の IDF の式の違い`

後二つの題名は名詞句であり、条件付きの主張文ではない。特に [BM25 のページ](<D:/Users/toshiki/info-hive/W0_Wiki/concepts/BM25 の IDF の式の違い.md:12>)は、式の比較、実測、比較時の注意、RRF の挙動を含む。

それが一つの claim として適切かどうかを決める本文上の判定がないまま、移行対象を固定している。これは直前の「用語・話題ページを残し、必要な判断だけ選別する」という前提と一致しない。全体 PoC に合格しても、**この 3 本がその分類に適する証明にはならない**。

**B-4【重大】グラフの移行は、明示エッジの目的語を書き換えても完了しない。**

A-3 の反例がそのまま当たる。

B は他の利用者の wiki について、`concept:x` を目的語にするエッジがあれば手で直すとしている。しかし `claim:a --depends_on--> concept:b` では、目的語に変更はなく、主語の型が不正になる。

作者の現在の `authored` エッジに問題がないことは、この一般的な移行の欠落を解消しない。

### 崩れる前提

- 「非 `source_only` の件数は、PoC 合格の代わりになる」  
  → 不一致・誤配置を含む出力でも件数を満たせる。
- 「表に条件欄を作れば、条件を保持した抽出になる」  
  → 作例で、比較条件と Git メタデータの欠落条件が混同されている。
- 「主張形の既存ページを選んだ」  
  → 実際には名詞句の話題ページも含めている。
- 「`supported` は `sources` 2 本以上を必須にすれば検査できる」  
  → 一つの source が多数の再現結果を収める場合でも、ファイル数だけで不合格になる。逆に、ページを分割すると本数は増える。B は独立性の意味判断が別途必要と認めているため、「2 本で支持を自動認定する」とまでは読まない。ただし、**なぜファイル数が必要条件なのかは示されていない**。

### 検証した事実

| 主張 | 結果 |
|---|---|
| 新しい状態導入は PoC 通過後に限る | **成果内で食い違い**。10 件による迂回条件がある |
| 再現性の作例が条件を保持する | **食い違い**。raw の比較条件と表の条件欄が対応しない |
| 既存 3 本が主張形の題名 | **食い違い**。2 本は名詞句 |
| 作者に現在ある型付きエッジだけなら移行が軽い | **一般の移行安全性は確かめられず**。現在の一例と配布機能の互換性は別 |
| claim 対応付け後、ID の参照修正だけで足りる | **食い違い**。A-3 の主語型不一致を再現 |

### 崩せなかった点

- 原案の「状態昇格」と、source から知見を取り出す操作が別物だという指摘。
- 既存 source に主張の行き先が記録されていないという確認。
- 通常パーサーとグラフ専用パーサーを区別する説明。
- 全ページ draft 化、日誌の wiki 内収容、出典なしの断定保存を避ける結論。

## エージェント D への攻撃

### 判定

**条件付きで採用可。確信度：高。**  
主要方針を崩す致命的な反例は見つからなかった。ただし、CQ 台帳の具体的な配置案には、既存の規模判定を変える副作用がある。

### 致命的・重大な欠陥

**D-1【重大】`indexes/questions.md` を早期に作ると、未分割の索引を「分割済み」と誤認する。**

D は、まだ索引を分割していない wiki にも、管理文書として `indexes/questions.md` を作る案を示す。

しかし [wiki_stats.py:189](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_stats.py:189) は、分割状態を次だけで判定している。

```python
(wiki / "indexes").exists()
```

[scale_advice:99](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_stats.py:99) は、`indexes/` が存在すると索引分割の推奨を出さない。

実際の関数への入力結果は次のとおりだった。

```text
scale_advice(150, 301, False)
→ [{"code": "split_index", ...}]

scale_advice(150, 301, True)
→ []
```

つまり、型別索引は一つもなく、`index.md` が 301 行になった状態でも、CQ 台帳のディレクトリがあるだけで分割通知が消える。

「通常ページの検索・孤立検査から外せる」という性質は確認できるが、**除外対象の既存ディレクトリを利用することが、既存動作に影響しないわけではない**。

### 崩れる前提

- 「`indexes/` は管理文書の置き場として流用できる」  
  → 現行コードは、ディレクトリの存在を索引分割済みの印にも使っている。
- 「専用の台帳検査を加えれば既存との境界が保てる」  
  → 台帳そのものの検査とは別に、stats の既存判定に影響する。
- 「レビュー状態の対象版をハッシュで特定できる」  
  → これは保留仕様としては成立するが、本文・frontmatter・参照先 source のどこまでを含むかは未定義である。D は未完成と認めているため、現時点では欠陥と断定せず、**確認できなかった点**とする。

### 検証した事実

| 主張 | 結果 |
|---|---|
| `indexes/` は通常の検索・lint から除外される | **一致**。[wiki_search.py:289](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:289)、[wiki_lint.py:127](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:127) |
| そこに台帳を置いても既存の規模判定を保てる | **食い違い**。上記の関数入力で分割通知の消失を再現 |
| kind の追加とグラフ型変更を分けられる | **一致**。[derive_node_type:238](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:238) では現行の type 対応が残る |
| 原資料の条件を保持する必要がある | **一致**。再現性 raw 7 行目への説明は原文と対応していた |

### 崩せなかった点

- `kind: "claim"` の付与と `claim` ノードへの移行を分ける判断。A・B の型移行反例は、D が既に扱っている。
- source の振り分け結果を実行後に確定し、後の移動でも追随させる必要性。
- CQ の回答リンクがあることと、問いに答えられることを区別する説明。
- Diátaxis を絶対的な混在禁止にせず、判断に必要な条件・理由を一体で残す方針。
- レビュー機能を保留し、形式検査の成功を内容確認と同一視しない結論。

## 自分の成果の見直し

**自分の成果も、完成した導入仕様としては条件付きに下げる。ただし、優先する三つと、共通 status・relations の全面導入を避ける結論は変えない。**

1. **PoC の実行件数が曖昧だった。**  
   私は「3 source × 2 モデル × 3 回＝18 件」としながら、現行との対照も取ると書いた。現行・変更案それぞれを同じ条件で評価するなら、配置計画は  
   \[
   3\times2\times3\times2=36件
   \]
   になる。18 件が片側だけなのか、総数なのかを明示しておらず、作者の評価負担を正しく見積もれていない。

2. **「主張の配置表が偏りを解く」という価値評価は未実証である。**  
   私も高い価値点を付けたが、表を埋めても、全件 source に残す、既存 source だけを更新する、再利用可能な知見を抽出し損なう結果はありうる。配置先の存在確認ではこれを検出できない。私の得点は測定結果としては使えない。これは A・B・D にも当たる。

3. **グラフの反例は、自分の警戒を裏付けたが、移行仕様を完成させたわけではない。**  
   私は型制約の調整を別段階にしたため、A・B の「対応付け追加後の移行不足」は同じ形では当たらない。ただし、実際の移行手順や互換性は検証していない。

4. **台帳の除外は全処理での確認が必要である。**  
   私はルートの `questions.md` を管理ファイルとして各処理から除外する必要を記したが、変更後の検索・MCP・stats を通した試験はしていない。D の具体的な配置とは違っても、「除外すれば副作用がない」とはまだ言えない。

5. **新しい診断の SemVer 分類には確定していない部分がある。**  
   私は既存出典規約に対する警告追加をパッチ候補とした。ただし JSON 出力や利用者側の判定に与える影響を調べていない。「文書に既にある規約だからパッチで安全」とまでは結論できない。

A のログ形式検査、B の PoC 迂回、D の `indexes/questions.md` は、私の案では採っていない。同じ攻撃が直接当たるとは判断しなかった。

## 生き残った案と確信度

| 案 | 攻撃後の判定 | 確信度 |
|---|---|---|
| **エージェント A** | 索引・出典検査と source の配置記録は候補として残る。ログ検査、出典不要の明示 `broader`、グラフ移行は記載どおりには採用できない | 高 |
| **エージェント B** | 導入計画は耐えなかった。PoC の迂回条件が中核の安全条件を壊し、作例にも条件の誤配置がある。索引検査という部分案は残る | 高 |
| **エージェント D** | 主要方針は残る。CQ 台帳の配置案は、既存の索引分割判定との互換性を保てていない | 高 |
| **自分の案** | 主要方針は残るが、PoC 件数、台帳の処理範囲、診断追加の互換性は未完成。完成仕様としての確信度は下がる | 中 |

**四案すべてが一致したこと自体は、source の配置判断が再現可能だという証拠にはならない。** 攻撃に残ったのは、索引分類・出典参照の検査という限定された追加と、配置方法を検証対象として扱う方針である。claim の状態管理、正式なレビュー制度、分類関係の追加まで検証済みになったわけではない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし

### エージェント D

## エージェント A への攻撃

### 判定

**条件付きで採用可。確信度：高。**

索引分類と出典参照の検査を優先する結論は崩せなかった。ただし、ログ検査の仕様、タグ検査の実測結果、`broader` の導入費用には問題がある。A 全体をそのまま実装仕様にはできない。

### 致命的・重大な欠陥

**A-1【重大】ログ検査を記載どおり実装すると、正常な説明部分を誤検出する。**

A は `malformed_log_lines` を、次のいずれでもない行として定義している。

- `## [YYYY-MM-DD] <op> | ...`
- 3 文字の空白で始まる補足行

しかし、実在の [log.md](D:/Users/toshiki/info-hive/W0_Wiki/log.md:1) には、題名、書式の説明、操作名の一覧、区切り線がある。

空行を除外したうえで、この二条件をそのまま適用すると、**拒否される行は 10 行**だった。内訳は正常な前文 9 行と、A が挙げた 140 行目の書式違反 1 行である。「検出件数 1」という実測結果と、提示した検査仕様が一致しない。

これは未実装コードの不具合を断定したものではなく、**提示仕様を再現した結果**である。前文を除外した実測なら、その除外条件が成果に欠けている。

**A-2【重大】「タグ検査は現在 0 件」という判断は、source の集計を wiki 全体へ広げている。**

A は「使われているタグは 4 つとも SCHEMA の一覧に載っている」ことから、`unknown_tags` は 0 件とし、初手から外す理由にも使っている。

再集計すると、4 種類なのは **source ページのタグ**だった。全 57 ページでは 9 種類ある。SCHEMA の正式な一覧に加えて「構成の例」も許可した場合でさえ、次の 2 ページが残る。

| 実在ページ | SCHEMA に列挙されていないタグ |
|---|---|
| [Claude Code の stdio の MCP サーバーとジョブオブジェクト.md](<D:/Users/toshiki/info-hive/W0_Wiki/concepts/Claude Code の stdio の MCP サーバーとジョブオブジェクト.md:7>) | `Claude Code`、`MCP`、`Windows` |
| [Windows での Tantivy の commit の失敗.md](<D:/Users/toshiki/info-hive/W0_Wiki/concepts/Windows での Tantivy の commit の失敗.md:7>) | `Windows` |

許可リストの解釈によって追加件数は変わるが、A の仕様による**全ページで 0 件という結論は成立しない**。照合対象の範囲を取り違えた実測を、優先順位の根拠にしている。

**A-3【重大】`broader` を「オントロジーに一項目足すだけ」とする評価は、現行の運用契約との衝突を落としている。**

`requires_evidence: false` をスクリプトが受け入れる、という A の主張自体は一致した。しかし、手順の正本である [graph-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:53) は、関係に `source`、`evidence`、`confidence`、`status` を必須としている。同文書の 70 行目以降も、型付きエッジは引用可能な出典に基づくものとしている。

さらに、A のオントロジー定義を使い、次の二つの関係だけを与えた。

```text
concept:a --broader--> concept:b
concept:b --broader--> concept:a
```

両方とも `source`、`evidence`、`confidence`、`status` を省略した。既存の `lint()` の結果は、**全検出項目 0 件**だった。

これは YAML 解析を通さず、辞書を検査関数に渡した確認である。PyYAML が未導入だったため import 部分だけを代替し、検査関数とエッジ抽出は実コードを用いた。CLI 全体の試験ではない。

コードでは、証拠は `requires_evidence` が真の場合だけ必須、`confidence` と `status` は値が存在する場合だけ検査される。[wiki_graph_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py:246)

したがって、**「記述できる」と「既存契約を保ったまま検査できる」は別**である。原案の循環検査も、この追加だけでは得られない。「一項目だけ」という移行費用と検査可能性の評価には根拠が足りない。

**A-4【軽微】感度分析の説明が、自分の採否一覧と矛盾する。**

A は「保留の群は最低でも 5.20」と述べる。しかし、保留に分類した `/wiki:plan、CQ、questions.md` の素点は `[5,4,4,3,3]` であり、得点は次のとおりになる。

\[
(5×25+4×20+4×20+3×20+3×15)/100=3.90
\]

変更した重みでは **4.10、3.85**。A の表とも一致する。「不採用群と保留群が得点で分離している」という説明は成立しない。採否そのものを否定する反例ではないが、結論の頑健性を説明する根拠には使えない。

### 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| `log.md` の非空行はすべて操作記録である | 現行テンプレート由来の説明や題名がある |
| source のタグ集計が wiki 全体を代表する | concept に固有のタグがある。実在する |
| 設定をスクリプトが受理すれば、既存の手順とも整合する | `requires_evidence: false` と、手順の出典必須規則が食い違う |
| `## 主な主張` の欠落数が、そのまま内容の不足件数になる | 別の見出しや段落に主張が書かれている |

最後の点について、[page-conventions.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md:108) は本文の固定テンプレートを否定し、主な主張を含む構成を勧めている。**固定文字列 `## 主な主張` がない 32 本という数だけでは、主張が欠落した 32 本とは判定できない。**

### 検証した事実

| 主張 | 結果 |
|---|---|
| 57 ページ、内訳 37・17・1・2 | **一致** |
| シンセシス欄に source が 16 本 | **一致** |
| source の `## 主な主張` が 5 本 | **一致**。内容不足の件数とは別 |
| `unknown_tags` は全 wiki で 0 件 | **食い違い** |
| `requires_evidence: false` を既存コードが扱う | **一致**。必須項目・循環の保証は得られない |
| A の仕様によるログ違反は 1 行 | **食い違い**。前文を含めると非空行 10 行 |

### 崩せなかった点

- 索引の 16 件の不一致と、その検査不足。
- 全件への `id`・共通 `status` の追加を避ける判断。
- source の主張一覧に、反映先を記録する追加価値。
- 状態付与や主張ページの導入を、直前の粒度 PoC と切り離して既定化しないという基本方針。

## エージェント B への攻撃

### 判定

**却下。確信度：高。**

却下の対象は、特に段階 2 の主張ページ・状態管理・`/wiki:promote` を含む導入計画である。中心となる品質条件を回避でき、既存ページの互換性についても主張と仕様が一致しない。段階 1 の索引検査まで否定するものではない。

### 致命的・重大な欠陥

**B-1【致命】件数だけで PoC の品質条件を回避できる。**

B の段階 2 の導入条件は、

> PoC が合格したら。または、`source_only` 以外の行き先が 10 件以上たまったら

となっている。

次の入力状態が反例になる。

1. LLM が 10 件の候補を `create` に分類する。
2. 別実行では配置が一致せず、PoC に不合格となる。
3. それでも「10 件以上」の条件は満たす。
4. 段階 2 を開始できる。

件数は、分類の正確さや再現性を示さない。誤った `create` を多く出すほど導入しやすくなる。

直前の検討は、出典への忠実さと条件保持を必須条件とし、配置一致などを別途評価している。[粒度検討](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/research/wiki-note-granularity-2026-11-08.md:142)

B の冒頭にある「PoC を通ってから」という説明と、実際に適用できる導入条件が食い違う。**オプトインであっても、判定品質が確認されたことにはならない。**

**B-2【重大】「既存の wiki は変わらない」と言いながら、既存 `experience-pattern` の有効性を変える。**

B は新しい状態検査の対象を、`claim` だけでなく `experience-pattern` にも広げる。その検査は次を要求する。

- `supported` なら `sources` が 2 本以上。
- `superseded` なら `superseded_by` が必須。

一方、現行の [SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template:194) は、経験パターンの状態として `hypothesis|supported|superseded` を定義しているが、この二条件を定義していない。

したがって、現行仕様では禁止されていない次のページが、新しい検査では不正になる。

```yaml
type: "concept"
kind: "experience-pattern"
status: "supported"
sources: ["one-experiment-report"]
```

一つの実験記録に複数の観測や検証結果が含まれる場合でも、B の検査では出典ファイル数が足りない。実際、既存の [OUTPUT の原資料](D:/Users/toshiki/info-hive/W1_Raw/output復元資格の設計-2026-11-04.md:59) は、一つのファイルに複数の検証と適用範囲を記録している。

これは、その資料だけで一般化が正当化されるという意味ではない。**ファイル数と証拠の量・質は同じではない**という反例である。B の互換性の説明は、作者の wiki に現在 `experience-pattern` がないことを、プラグイン利用者全体へ広げている。

**B-3【重大】導入例で、原資料にない条件を主張へ付けている。**

B の「主張」の表は、環境別の再現性判定に次の条件を付ける。

> 配布形態が Git を含まない場合は環境情報が null になる

原資料の [5 行目](D:/Users/toshiki/info-hive/W1_Raw/semasynth再現性の検証-2026-11-06.md:5) にあるのは、**取得できない Git 情報や lock は null にする**という規則である。Python・SQLite・OS などを含む「環境情報」全体が null になるとは書かれていない。

さらに、環境別の比較方法は同資料の 7 行目にあり、Git を含まない配布であることを適用条件にしていない。

Git 情報を取得できる環境でも、同一環境・異なる環境に応じて比較方法を選ぶ必要がある。B の例を条件付き主張として保存すると、**別の事項を適用条件に誤結合した知識**になる。これは書式上の問題ではなく、導入しようとしている「条件を保持した主張抽出」が、提示例ですでに失敗している。

**B-4【重大】タグ付けを ADR-0008 の保存先分離の代案にしている。**

B の衝突解決表は、プロジェクト固有の source を、

> `tags` で見分けるか、プロジェクトの wiki に置く

としている。

しかし [ADR-0008](C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0008-numbered-workspace-layout.md:27) が定めるのは、ユーザースコープへプロジェクト固有情報を置かないという**保存先の境界**である。タグを追加して同じ場所に残す選択肢は、この境界を満たさない。

「ADR を変えない」という結論と、許している選択肢が両立していない。既存データに問題があることを認識するだけでは、この衝突は解消しない。

**B-5【軽微】調査済みとした二つの事実が実体と合わない。**

- 「暗黙エッジは `sources:` と `raw:` だけから作られる」は誤り。本文の wikilink から `mentions` を生成する。[wiki_graph_extract.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:387)
- 「作者の wiki に手順主体のページはない」という断定には反例がある。[オントロジー抽出パイプライン.md](D:/Users/toshiki/info-hive/W0_Wiki/concepts/オントロジー抽出パイプライン.md:13) は自らを「手順」と定義し、7 段階と各段階の操作を中心に構成されている。

後者は、ただちに `type: howto` が必要だという証明ではない。ただし、「対象が存在しない」ことを不採用の根拠にはできない。

### 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| 候補が増えれば分類手順を導入できる | 誤分類された候補が 10 件たまる |
| 出典ファイル数が証拠の充実度を表す | 一つの記録に複数の実験がある、または複数資料が同じ観測を転載する |
| `claim` のオプトインは既存ページに影響しない | 検査対象に既存の `experience-pattern` も含める |
| 同じ段落群にある条件を主張へ添えればよい | Git 情報の欠損規則を、再現性判定の適用条件へ誤結合する |
| タグで区別すれば保存先の責務も分離できる | ユーザースコープにプロジェクト固有資料を残す |

### 検証した事実

| 主張 | 結果 |
|---|---|
| 索引に source 16 本の誤分類がある | **一致** |
| 現行の経験パターンには B の出典数・後継参照条件がある | **食い違い**。現行スキーマにはない |
| B の再現性の条件例が原資料を保持している | **食い違い** |
| `mentions` は本文から生成される | **一致**。B 冒頭の説明と食い違う |
| ADR-0008 をタグで満たせる | **食い違い** |
| PoC の代わりに候補 10 件で進める | **B の本文で確認**。品質保証にはならない |

### 崩せなかった点

- source の主張に反映先を付けることで、取り込み後の作業を追跡できるという発想。
- 出典の独立性と、単なる参照先の存在を別問題として挙げている点。ただし、提示した状態検査はその区別を十分に保持していない。
- `questions.md` を通常ページから除外するには、複数の読み手を確認する必要があるという指摘。

## エージェント C への攻撃

### 判定

**条件付きで採用可。確信度：中。**

検討方針としての致命的・重大な欠陥は、今回の攻撃では崩せなかった。これは、提案した PoC や運用効果が実証されたという判定ではない。

### 致命的・重大な欠陥

**致命・重大に該当する反例は確認できなかった。**

確認できた不足は次の一点である。

**C-1【軽微】PoC の「18 件」は一方式分であり、対照を含む総数が明記されていない。**

C は、

\[
3\text{ソース}×2\text{モデル}×3\text{回}=18\text{件}
\]

とし、同時に「現行手順との対照を取る」としている。同じ実行条件を現行と変更案の両方に適用するなら、

\[
18×2=36\text{件}
\]

になる。

18 件を試行全体の工数として読むと、対照群を落とすか、各条件の反復数を減らすことになる。ただし、C は「程度から始める案」としており、18 件が必ず総数だとは断定していない。**実験計画の記述不足であり、品質条件が破綻したとまではいえない。**

### 崩れる前提

以下は、実証済みの欠陥ではなく、C の条件付き結論が依存する未検証事項である。

| 前提 | 崩れる条件 |
|---|---|
| 主張・配置表が作者の負担を減らす | 表の読解・修正時間が、現行の取り込みより増える |
| CQ を少数選べば管理負担が抑えられる | 選別・回答充足の判断自体が毎回必要になる |
| 形式検査と意味判断を分けて運用できる | 存在する出典や回答リンクを、内容の正しさと読み替える |
| 小規模 PoC が対象領域を代表する | 選んだ 3 ソースにはない条件・反例が実運用で頻出する |

C は、これらをすでに未検証事項や PoC の評価対象としている。そのため、**未検証であること自体を、無条件導入の欠陥として攻撃することはできない**。

### 検証した事実

| 主張 | 結果 |
|---|---|
| 57 ページ、索引誤分類 16 件 | **一致** |
| 通常 lint の既定必須キーに `sources` がない | **一致**。[wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:278) |
| 通常 frontmatter パーサーは入れ子を読まない | **一致**。[wiki_text.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:281) |
| `claim` のノード化と本文上の `kind` 追加は別の移行になる | **一致** |
| `depends_on` は現在 `claim` を許可しない | **一致**。[ontology.yaml.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/ontology.yaml.template:104) |
| 採点表の計算 | **42 行×3 通り、計 126 値を再計算し一致** |
| PoC、CQ、レビュー制度の実運用上の効果 | **確かめられず**。C も実証済みとはしていない |

### 崩せなかった点

- 同一環境・異なる環境を表の別候補にしたことを、直前の「一つの判断」という結論への違反として検討した。しかし C は別ページへの分割を確定しておらず、候補の配置を PoC に委ねている。**強制分割の反例にはならなかった。**
- 「規約にある」と「スクリプトが検査する」を区別している。
- 主張の独立化と、グラフのノード ID 変更を別の移行としている。
- レビュー済み表示の責任者、対象版、変更後の失効を未定義のまま導入しない。
- 索引検査を優先する根拠と、主張抽出の PoC を必要とする根拠を混同していない。

## 自分の成果の見直し

このレビューで照合できる入力には、**私自身の初回成果の本文が含まれていない**。したがって、記憶や推測で「自分は同じ誤りをしていなかった」とは判定しない。自分を含む四案の完全な順位付けは、その範囲ではできない。

同じ攻撃は、私自身の判断にも次のように当たる。

- **集計範囲の取り違え**：source の結果から wiki 全体の検査件数を推定していたなら撤回対象になる。今回、全ページのタグを調べるまでは「0 件」を支持できなかった。
- **文書上の必須条件と実装の保証の混同**：グラフで `confidence`・`status` が必須という規約だけから、欠落を lint が検出すると推定していたなら誤りである。今回のコード確認で、その推定は否定された。
- **原資料を確認しない主張例**：既存の source 要約に基づく例を、原資料との照合済みとして扱うことはできない。今回の B への攻撃は、raw の 5 行目と 7 行目を確認して初めて成立した。
- **件数による品質条件の代用**：候補数、ページ数、source 数だけで導入・支持状態を決める規則を自分が採っていたなら、B と同じ反例で崩れる。

今回の結論として、**「既存 lint が通る」「参照先が存在する」「候補が一定件数ある」を、意味上の妥当性や導入可能性の証明として使うことは支持しない。**

## 生き残った案と確信度

| 案 | 攻撃後の判定 | 生き残った部分／耐えなかった部分 | 確信度 |
|---|---|---|---|
| A | 条件付きで採用可 | 索引・出典検査の優先は残る。ログ検査仕様、タグ 0 件という根拠、`broader` の導入費用評価は耐えなかった | 高 |
| B | 却下 | 索引検査と反映先記録は残る。PoC を迂回する導入条件、既存経験パターンを含む状態検査、原資料と食い違う条件例は耐えなかった | 高 |
| C | 条件付きで採用可 | 段階導入、形式検査と意味判断の分離、配置 PoC、グラフ移行の分離は崩せなかった。運用効果は未実証 | 中 |
| 自分 | 初回成果の総合判定はできない | 初回本文を照合できないため、他案より上位とは判定しない。上記の共通攻撃は自分にも適用する | 低 |

今回、**最も崩れにくかったのは C の検討方針**である。ただし「未検証の機能まで導入してよい」という意味ではない。三案に共通する索引分類検査は残り、主張の配置を記録して PoC で評価する方向も残った。B の状態管理と導入条件は、そのままでは残らない。

検証は読み取り、再集計、計算、メモリ上の関数呼び出しに限定した。リポジトリと作者の wiki は変更せず、ビルドも行っていない。禁止された成果保存ディレクトリは読んでいない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし


## 規則

- 票数ではなく根拠の質で優劣を付ける。複数が同じ結論でも、同じ資料を写しただけなら独立に同じ結論へ至ったとは言えない。
- 根拠があり反証されていない攻撃を、成果の主張より優先する。「崩せなかった点」は独立した検証として扱う。推測と明記された攻撃で優劣を付けない。
- 正面から割れた論点は根拠で決める。決められないなら、決めるために何が要るかを書く。
- 作者の判断が要ることは、選択肢とそれぞれの帰結を並べる。
- 日本語で書き、結論を先に書く。

## 最終メッセージの形式

```markdown
# <タスクの主題> の総括

## 推奨
（決定を 1〜2 文で）

## 批評で動いたこと
- （他の成果を読んで結論を改めたエージェントと、その内容）
- （最も鋭い反論と、それが決定的だったか）

## 推奨案が残る理由
- （レビューで確かめられた根拠）

## エージェントごとの要約
（エージェント A、エージェント B、エージェント C、エージェント D の結論を 1 段落ずつ。レビューで受けた指摘のうち当たっていたものを添える）

## 残るリスクと未確定事項
- （作者の判断が要ること。選択肢と帰結）

## 記号とモデルの対応
| 記号 | モデル |
| --- | --- |
| A | Claude Opus 5.5（`claude-opus-5-5`） |
| B | Claude Fable 5.1（`claude-fable-5-1`） |
| C | GPT-6.1 Sol（`gpt-6.1-sol`） |
| D | GPT-6 Astra（`gpt-6-astra`） |
```
