# LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計

Nov 8, 2026 · @Toshiki Hayashi

## 目的と前提

LLM Wiki の記事を「思いついた順」ではなく、きっかけと成熟度に応じた決まった手順で生成・維持するための設計をまとめる。手法の網羅ではなく、**どの状況でどれを使い、どれを使わないか**の判断基準と、それを Claude Code の Skill に落とし込む設計が主題である。

想定環境は次のとおり。

| 項目 | 内容 |
| --- | --- |
| エージェント | Claude Code（Skill / スラッシュコマンドとして手順を定義） |
| Wiki 基盤 | llm-wiki-plugin（Karpathy 式 ingest / query / lint） |
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

区分 1、3 が「何が足りないか」を決め、区分 2、4 が「どう書くか」を決め、区分 5 が書いた後を支える。Skill 設計では、区分 1 の「きっかけ」ごとにコマンドを分け、区分 2〜4 を共通のスキーマ・テンプレートで固定し、区分 5 を lint と consolidate に集約する。

## 状況別の使い分け

記事が生まれる「きっかけ」が手法を決める。きっかけごとに Skill のコマンドを対応させれば、手法の切り替えを意識しなくてよくなる。

| きっかけ・状況 | 使う手法 | 使わない / 後回し | 対応コマンド |
| --- | --- | --- | --- |
| 未知の領域を学び始めた（何があるか分からない） | ボトムアップ。Source-driven ingest → Atomic Notes。ソースを入れると概念ページが生える | Taxonomy の事前設計、Competency Questions（問いがまだ立てられない） | `/wiki ingest` |
| 既知の領域を網羅的に整備したい | Competency Questions で問いを列挙 → MOC に赤リンク → Gap Analysis で埋める | 日誌駆動（遅すぎる） | `/wiki plan` |
| 外部ソースを継続的に取り込む（論文・記事・仕様書） | ingest + 出典必須 + 暫定 → 正典の昇格。raw/ は不変 | 正典ページへの直接書き込み | `/wiki ingest` → `/wiki promote` |
| 質問に答えた・調べ物をした | Query-driven / KCS。回答を draft 記事に。答えられなかった問いを記録（Retrieval-driven improvement） | — | `/wiki answer` |
| 日々のタスク・アイデア | 日誌に書く → 週次統合で概念ページへ昇格 | 毎回の Atomic Note 化（ノイズが増える） | `/wiki journal` → `/wiki consolidate` |
| 個別プロジェクトの知識 | ADR + Task-driven + Continuous Documentation。`scope: project` で共通 Wiki と分離 | Diátaxis 4 種の強制 | `/wiki decide`、`/wiki ingest --scope project` |
| 手順・操作が主の技術知識 | Diátaxis（How-to と Reference を分離） | 概念中心の領域では type を explanation 一択でよい | `/wiki answer --type howto` |
| 定期メンテナンス | lint（孤立・矛盾・陳腐化・出典欠落）→ バックログ化。SSOT で重複統合 | — | `/wiki lint` |
| ナレッジグラフ化の準備 | フロントマターに SKOS 風 `relations`（broader / related）と `type`。Middle-out で中核概念から整える | OWL / 完全なオントロジー | `/wiki lint --relations`、`/wiki graph` |

## 成熟度フェーズ別の重心

&#91;embedded content: 導入フェーズ · 4 段階と 3 つの移行条件\]

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
type: concept          # source | concept | entity | howto | decision | moc | journal
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

```markdown
.
├── CLAUDE.md            # スキーマとルール（LLM への指示）
├── .claude/skills/wiki/ # 本書の Skill
├── raw/                 # 元ソース。不変。LLM は書き換えない
├── wiki/
│   ├── index.md         # MOC のルート。LLM がナビゲーションに使う
│   ├── log.md           # 操作の時系列ログ（追記のみ）
│   ├── questions.md     # Competency Questions と回答状況
│   ├── sources/         # type: source
│   ├── concepts/        # type: concept / entity / howto
│   ├── decisions/       # type: decision（ADR）
│   └── moc/             # type: moc（領域ごとの案内ページ）
├── journal/             # type: journal。日付ごと。consolidate の入力
└── projects/<name>/     # scope: project:<name>。構造は wiki/ と同じ
```

## Skill 設計

1 つの Skill（`wiki`）に 8 コマンドを持たせ、「きっかけ」ごとに入口を分ける。共通ルール（スキーマ、テンプレート、リンク規約）は SKILL.md 本文に置き、コマンド固有の手順は `commands/<name>.md` に分ける。SKILL.md 本文は日本語で書く。

### コマンド一覧

| コマンド | きっかけ | 主な手法 | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| `/wiki ingest <pathっurl>` | ソースを入手した | Source-driven Synthesis、Provenance | raw/ のファイルまたは URL | source ページ 1 件、concept / entity ページの新規・更新（draft）、index / log 追記 |
| `/wiki plan <topic>` | 領域を網羅したい | Competency Questions、MOC、Gap Analysis | 領域名、任意で既存資料 | questions.md に CQ 追記、moc/\<topic>.md（赤リンク付き）、未作成記事の一覧 |
| `/wiki answer <question>` | 質問に答えたい | Query-driven、KCS | 自然言語の問い | 回答（チャット）、draft 記事、答えられなかった場合は questions.md に未回答 CQ として追記 |
| `/wiki journal [text]` | 今日のメモ・タスク | 日誌駆動 | 短文 | journal/YYYY-MM-DD.md に追記。記事は作らない |
| `/wiki consolidate [--since]` | 週次・月次 | 日誌 → 概念ページ、SSOT | 期間 | 繰り返し登場する概念を concept ページ化、重複記事の統合提案、分類の再提案（Middle-out） |
| `/wiki decide <title>` | 設計判断をした | ADR | 背景と選択肢 | decisions/\<id>.md（背景・選択肢・決定・影響）、関連 concept へのリンク |
| `/wiki promote <id>` | draft を確定させたい | 暫定 → 正典、Provenance | 記事 id | 出典・リンク・必須セクションを検査して status を上げる。不足があれば理由を返す |
| `/wiki lint [--fix] [--relations]` | 定期メンテ | lint、Lifecycle、Gap Analysis | なし | 孤立・矛盾・出典欠落・未回答 CQ・relations 不整合のレポート。`--fix` で機械的に直せるものを修正 |

`/wiki graph` はフロントマターからグラフを生成するコマンドだが、LLM ではなくスクリプトで済むため Skill の外（`scripts/`）に置く。

### 共通ルール（SKILL.md 本文に記述）

1. raw/ は読むだけ。書き換え・移動・削除をしない。
2. 新規記事は必ずテンプレート（`templates/<type>.md`）から作り、フロントマターを全フィールド埋める。
3. 記事を作る前に index.md と既存記事を検索し、同一概念があれば新規作成せず更新する（SSOT）。
4. 1 記事 1 概念。説明が 2 つの概念にまたがったら分割して `related` で結ぶ。
5. 手順（howto）と概念（concept）を同じ記事に混ぜない。
6. 新規記事は `status: draft`。`reviewed` 以上への変更は `/wiki promote` 経由のみ。
7. すべての操作を log.md に 1 行追記する（日付、コマンド、触った記事 id）。
8. リンクは Foam の `[[id]]` 形式。ファイル名と `id` を一致させ、改名しない。

### `/wiki ingest` の手順（代表例）

1. ソースを読み、raw/ に無ければ保存する。
2. `sources/<id>.md` を作る。要約、主張の一覧、登場する概念の候補。
3. 概念候補ごとに既存記事を検索。あれば追記、なければ `concepts/<id>.md` を draft で作る。
4. 新規・更新した記事の `sources` にソース id を追加、`relations` を埋める。
5. questions.md の未回答 CQ に答えられるものがあれば `answers` を付けてマークする。
6. 既存記事と矛盾する主張があれば上書きせず、記事内に「矛盾」セクションとして並記し、lint 対象にする。
7. index.md と log.md を更新し、触った記事の一覧を返す。

### `/wiki plan` の手順

1. 領域について「この Wiki が答えられるべき問い」を 10〜30 個列挙し、questions.md に id 付きで追記する。
2. 問いから概念を抽出し、既存記事と照合する。
3. `moc/<topic>.md` を作り、既存記事へのリンクと未作成記事への赤リンクを並べる。
4. 未作成記事を優先度付きで返す。記事本文はここでは書かない（ingest か answer で埋める）。

## 導入ロードマップ

最初から 8 コマンドを揃えず、フェーズごとに足す。各フェーズの入口は記事数ではなく、「その問題が実際に起きたか」で判断する。

- [ ] **フェーズ 0（立ち上げ）**：CLAUDE.md にスキーマと共通ルールを書く。`templates/` を source / concept / journal の 3 種だけ用意。`/wiki ingest`、`/wiki answer`、`/wiki journal` を実装。
- [ ] **フェーズ 1（成長期への切替え）**：「同じ概念の記事が 2 つできた」「どこに何があるか分からなくなった」が起きたら開始。`/wiki lint`、`/wiki consolidate`、`/wiki plan` を追加。questions.md を導入し、`type: moc` と `decision` を有効化。
- [ ] **フェーズ 2（正典化）**：他人や別プロジェクトから参照される記事が出てきたら開始。`/wiki promote` と `status` の三段階を有効化。lint に出典検査を追加。
- [ ] **フェーズ 3（グラフ化）**：`relations` が十分に埋まったら開始。`/wiki lint --relations` で整合性を検査し、`scripts/graph` でフロントマターからグラフを生成。この段階で初めてオントロジー化を検討する。

次に検討するテーマは 2 つある。一つは `templates/<type>.md` の具体的なセクション構成（特に concept の必須セクションと source の「主張一覧」の書式）。もう一つは lint の検査項目をどこまでスクリプト化し、どこから LLM に判断させるかの境界である。
