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
