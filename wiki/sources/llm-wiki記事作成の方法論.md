---
type: "source"
title: "LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計"
tags: ["wiki設計", "取り込み"]
authors: ["to884"]
raw: "raw/llm-wiki記事作成の方法論.md"
ingested: 2026-11-14
created: 2026-11-14
updated: 2026-11-14
concepts: ["記事作成の5区分"]
---

# LLM Wiki 記事作成の方法論 — 使い分けと Skill 設計

LLM Wiki の記事を、思いついた順ではなく、きっかけと成熟度に応じた決まった手順で作り、保つための設計のメモである（2026-11-08）。手法を網羅するのではなく、どの状況でどの手法を使い、どれを使わないかの判断の基準と、それを Claude Code の Skill に落とし込む設計を主題にしている。原本は `raw/llm-wiki記事作成の方法論.md` である。

これは**設計の提案**であり、info-hive のいまの振る舞いではない。想定している環境は、Claude Code、llm-wiki-plugin（Karpathy 式の ingest、query、lint）、VS Code と Foam、Git のリポジトリで、最後にはフロントマターからナレッジグラフを作ることを目標にしている。ChatGPT と Claude の 2 つの回答を元にしたと書いているが、その回答は手元にない。その中身は、このメモを通して知っているだけである。

## 主な主張

- **5 つの区分で組み合わせる。** 記事作成を発見、構造化、体系化、執筆、維持に分け、区分ごとに手法を選ぶ。記事が生まれるきっかけが手法を決める（[[記事作成の5区分]]）。
- **フェーズを問題の発生で進める。** 立ち上げの時期は、ボトムアップと出典だけで回す。分類と問いの設計は、記事が増えて困り始めてから入れる。次のフェーズに進む合図は、記事の数ではなく「その問題が実際に起きたか」である（下の「導入のフェーズ」）。
- **手法の衝突は状態で分ける。** 4 つの衝突は、どちらかを選ぶのではなく、状態やタイミングで分ければ両立する。共通の形は、frontmatter の 1 つの欄（`type`、`status`）でモードを分け、lint がモードごとの規則を検査することである。手法を毎回人が選ぶのではなく、メタデータに埋め込む。

| 衝突 | 解き方 |
| --- | --- |
| トップダウンの分類とボトムアップ | Middle-out。取り込みはボトムアップで行い、lint のときに LLM が分類を提案し直す。Taxonomy は「設計する」のではなく「発見して承認する」 |
| Atomic Notes とエンティティのページ | `type` で分ける。`source` は 1 ソースで 1 ページ、`concept` と `entity` は 1 概念で 1 ページにし、ソースから概念へリンクする |
| Diátaxis の過剰な適用 | 4 種をそろえることを目的にしない。採る規則は「手順と概念を同じページに混ぜない」の 1 つだけにする |
| KCS と出典の必須 | `status` で分ける。`draft` は出典なしで入れてよく、`reviewed` に上げるときに出典を求める |

## 提案している記事のスキーマと Skill

- frontmatter に `id`、`type`（source、concept、entity、howto、decision、moc、journal）、`scope`（common か `project:<名前>`）、`status`（draft、reviewed、canonical、deprecated）、`relations`（SKOS 風の `broader`、`related`、`answers`）、`sources` を置く。lint は欄ごとに、必須のセクション、出典の有無、リンク先の有無、`broader` の循環、未回答の Competency Questions を調べる。
- ディレクトリは raw、wiki、スキーマの 3 層に、`journal/` と `projects/<名前>/` を足す。wiki の下に `questions.md`、`decisions/`、`moc/` を置く。
- 1 つの Skill（`wiki`）に 8 つのコマンド（ingest、plan、answer、journal、consolidate、decide、promote、lint）を持たせる。グラフの生成は、LLM の要らないスクリプトとして Skill の外に置く。
- 共通の規則は 8 つある。raw は読むだけにする。新しい記事はテンプレートから作る。作る前に既存の記事を探す（SSOT）。1 記事に 1 概念を書く。手順と概念を混ぜない。新しい記事は `draft` にする。すべての操作を `log.md` に記録する。リンクは `[[id]]` の形にする。
- 取り込みで既存の記事と矛盾する主張が出たら、上書きせずに「矛盾」のセクションに並べて書き、lint の対象にする。

## 導入のフェーズ

- フェーズ 0（立ち上げ）: スキーマと共通の規則を書く。テンプレートは source、concept、journal の 3 種だけにし、ingest、answer、journal を作る。
- フェーズ 1（成長期）: 「同じ概念の記事が 2 つできた」「どこに何があるか分からなくなった」が起きたら始める。lint、consolidate、plan と、`questions.md`、`moc`、`decision` を加える。
- フェーズ 2（正典化）: ほかの人やプロジェクトから参照される記事が出たら始める。promote、`status` の 3 段階、出典の検査を加える。
- フェーズ 3（グラフ化）: `relations` が十分に埋まったら始める。relations の整合を検査してグラフを作り、ここで初めてオントロジーを考える。

原本の「成熟度フェーズ別の重心」の節には、この 4 段階と 3 つの移行条件を描いた埋め込みの図があったが、原本には埋め込みの印しか残っていない。上の内容は「導入ロードマップ」の節から取った。

## 未解決の問い

ソースは、次に考えることとして 2 つを挙げている。1 つは、種類ごとのテンプレートのセクションの構成（特に concept の必須のセクションと、source の主張の一覧の書式）である。もう 1 つは、lint の検査のどこまでをスクリプトにし、どこから LLM に判断させるかの境目である。

## info-hive の現状との差

2026-11-14 の origin/main（wiki 0.13.0 のあと）と比べた。ソースは提案なので、矛盾としては扱わない。

| 項目 | ソースの提案 | info-hive の現状 |
| --- | --- | --- |
| コマンド | 1 つの Skill に `/wiki <名前>` で 8 つ | プラグイン `wiki` に `/wiki:<名前>`。ingest、query、lint、graph、learn、evolve、browse、stats、init、upgrade、help。answer の一部（出典つきで答え、役に立つ回答をシンセシスに残す）は `/wiki:query` が担うが、答えられなかった問いを残す仕組みはない。plan、journal、consolidate、decide、promote はない |
| ページの種類 | source、concept、entity、howto、decision、moc、journal | source、entity、concept、synthesis の 4 つ。グラフのオントロジーには、明示したときだけ使う `decision` のノードの種類がある |
| 状態 | ページの `status` で出典の要否を分ける | ページの `status` はない。`status` は型付きの関係と、経験のパターンにある |
| 関係 | SKOS 風の `relations`。オントロジーはフェーズ 3 まで後回し | `graph.relationships`。述語は `ontology.yaml` で宣言し、証拠の引用と確信度が要る |
| 共通と個別の分け方 | 1 つの wiki で、`scope` の欄で分ける | ユーザースコープの wiki とプロジェクトの wiki を、別のルートに置く |
| 主張の一覧 | 書式は未解決の問い | 要約ページの `## 主張と行き先` の表 |

矛盾の並記（`## 矛盾`）、raw を変えないこと、作る前に既存のページを探すこと、1 ページで 1 つの話題にすることは、info-hive の取り込みの手順にすでにある。

## 原本についての注記

- コマンドの一覧の `/wiki ingest <pathっurl>` は、`<path|url>` の打ち誤りとみられる。raw は直していない。
- `status` の値は記事のスキーマで 4 つ（draft、reviewed、canonical、deprecated）と定めているが、フェーズ 2 では「`status` の三段階」と書いている。廃止の `deprecated` を数えていないのかもしれないが、原本からは分からない。

## 主張と行き先

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | 記事作成を 5 つの区分に分け、区分ごとに手法を選んで組み合わせる | 「方法論マップ（5 区分）」 | `create` | [[記事作成の5区分]] を作った |
| c2 | 記事が生まれるきっかけが、使う手法と使わない手法を決める | 「状況別の使い分け」 | `create` | [[記事作成の5区分]] の「きっかけで手法を選ぶ」に載せた |
| c3 | 手法の 4 つの衝突は、`type` と `status` でモードを分け、lint がモードごとに検査すれば両立する | 「手法間の衝突点と解決策」 | `source_only` | 作者がページにしないことを選んだ |
| c4 | 次のフェーズに進む合図は、記事の数ではなく、その問題が実際に起きたかである | 「導入ロードマップ」 | `source_only` | 作者がページにしないことを選んだ |
| c5 | 記事のスキーマ（`status`、`scope`、`relations` など）と 8 つのコマンドの Skill | 「記事スキーマ」「Skill 設計」 | `source_only` | 提案で、info-hive の現状ではない。差はこのページに書いた |

## 関係するページ

- [[記事作成の5区分]]
- [[ingestに使うモデル]]: info-hive の `/wiki:ingest` の運用の決定
