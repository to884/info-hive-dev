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
