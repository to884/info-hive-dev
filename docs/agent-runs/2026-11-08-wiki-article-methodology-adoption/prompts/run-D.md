あなたは、同じタスクに独立して取り組む 4 体のエージェントの 1 体です。
他のエージェントが誰で、何を書くかは知らされません。
あなたの最終メッセージだけが成果物として保存され、後で他のエージェントに読まれます。途中のメッセージは保存されないので、根拠と結論は最終メッセージにすべて書いてください。

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


## 制約

- 調査と判断のタスクである。リポジトリのファイルを書き換えない。読むための道具は使える。ビルドはしない。
- `docs\agent-runs\2026-11-08-wiki-article-methodology-adoption` の配下は読まない。他のエージェントの成果が置かれる場所である。
- 質問はできない。足りない情報は妥当な仮定を置いて最後まで進め、仮定であることを明記する。
- 主張には根拠を添える。読んだファイルはパスと該当箇所、計算は式と値、推測は推測と書く。
- 作業ログではなく、判断に要る情報を書く。
- 日本語で書き、結論を先に書く。

## 最終メッセージの形式

Markdown で、次の見出しをこの順に置く。

1. `## 結論`：タスクへの答え
2. `## 根拠`：結論を支える事実と推論
3. `## 検討した代替案`：採らなかった案と、採らなかった理由
4. `## 前提と不確実性`：依存している仮定、確かめられなかったこと、作者の判断が要ること
5. `## 参照`：読んだファイルと文書
