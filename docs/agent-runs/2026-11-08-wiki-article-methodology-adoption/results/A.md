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
