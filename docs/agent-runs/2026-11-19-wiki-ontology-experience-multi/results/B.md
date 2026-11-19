## 結論

**1. 機能はあるか。ない。**
wiki 0.35.1（`info-hive-wiki` の origin/main、2026-11-19 に fetch）には、wiki の内容を読んでオントロジーを提案し、適用する機能がない。あるのは次の 3 つである。

- `init_wiki.py` が、どの wiki にも同じひな形 `ontology.yaml` を置く。
- 利用者が `ontology.yaml` を手で編集する。
- lint、extract、query が、その定義でページを検査し、グラフを作り、問い合わせる。

近いものが 2 つあるが、どちらも語彙は提案しない。`/wiki:evolve` はスキルの改善案を扱う。取り込みの手順 7 は、採用済みの述語で型付きエッジを書く。開いている PR（info-hive-wiki の #96 と #71、info-hive-dev の #143）にも該当はない。未コミットの提供案 `docs/plans/wiki-ontology-feature-experience-2026-11-19.md` は、本文に未実装と書いてある。

**2. 提供の仕方。wiki プラグインに `/wiki:ontology` を足し、診断、提案、適用の 3 段にする。**

| 入口（Claude Code） | 何をするか | LLM | 書き込み |
| --- | --- | --- | --- |
| `/wiki:ontology`（引数なし） | 今の語彙がどれだけ使われているかを数値で示す | 使わない | なし |
| `/wiki:ontology propose` | 答えたい質問を決め、述語の案と実ページの関係の例を作り、隔離して試す | ホストのモデル | wiki の外だけ |
| `/wiki:ontology apply` | 承認した案だけを当て、lint、extract、試した質問の引き直しまで行う | 使う | `ontology.yaml` と選んだページ |

- **Codex の入口**: `$wiki:info-hive ontology …` にする。`wiki_codex.py` は `commands/<操作>.md` を読むので、`commands/ontology.md` を正本にすれば入口を共有できる見込みである。操作名の許可リストがあるかは確かめていない。
- **気づく経路**: `/wiki:stats` と `/wiki:lint` に 1 行の案内を出す。例は「オントロジーはひな形のままで、型付きの関係は 10 本です」。
- **対象の wiki**: 1 回に 1 つとし、既存の `/wiki:graph` と同じ順で決めて最初に表示する。プロジェクトとユーザースコープの語彙は独立させ、自動では持ち込まない。
- **「最適」の扱い**: 保証しない。利用者が選んだ 2〜3 個の質問に答えられるかと、診断の数値で「合っている度合い」を示す。「今の語彙で足りる」「まず関係を書くほうが先」も正常な結果にする。

**3. 利用者の使い方（5 段）**

1. **気づく。** stats、lint の案内か、「この wiki に合うつなぎ方を提案して」という依頼で始まる。
2. **診断を見る。** 数秒で、使われていない種類と述語、型付きエッジの比率、`kind` のないページの数、タグの分布が出る。続けるかをここで決める。
3. **提案を見る。** YAML ではなく日本語で、足す述語、その意味、実ページの引用つきの例 3〜5 件、ノード ID が変わる件数と切れる参照の件数を見る。
4. **選んで適用する。** 「適用」「一部を変える」「見送る」から選ぶ。適用の単位は「語彙と、選んだ少数のページの関係」である。
5. **育てる。** 以後の取り込みは採用済みの述語を使う（既存の手順 7）。ページが増えたら診断を引き直す。

**4. 初期版の範囲**

- 入れる: 診断、述語を中心にした提案、少数の事例の試行、承認した差分の適用。
- 入れない: 全ページへの一括付与、既存の述語の改名と削除、複数の wiki の一括変更、分野別の既製の語彙の配布、無人の継続的な変更。

**5. 既存の提供案と違う点**

- **引数なしは診断にする。** 既存案は提案の開始にしている。ひな形のままかどうかは LLM なしで分かり、全ページを読む費用をかける前に利用者が判断できる。
- **述語を先に足し、種類は後にする。** 理由は根拠の 3 に書く。
- **既存ページの種類の付け替えは、影響の一覧を計算したうえで許す。** 既存案は初期版で禁じている。この wiki では、禁じると新しい種類が既存のページに 1 つも付かない。

## 根拠

**1. このプロジェクトの wiki では、語彙がほとんど使われていない（作業ツリーの `wiki/graph/` を集計）。**

| 項目 | 値 | 式 |
| --- | --- | --- |
| ひな形との差 | なし | `wiki/graph/ontology.yaml` と `assets/ontology.yaml.template` の diff が空 |
| ノードの種類 | source 77、concept 31 | 宣言 12 種のうち、ページがあるのは 2 種 |
| エンティティのページ | 0 | `wiki/` に `entities/` がない。person など 6 種は未使用 |
| 型付きエッジ | 10 本、約 1.6% | 10 ÷ 631。内訳は mentions 428、sourced_from 117、summarizes_raw 76、cites 10 |
| 使われた型付きの述語 | 12 個のうち 1 個 | `cites` だけ。10 本とも目的語は `source:*` |
| `graph:` を書いたページ | 5、約 4.6% | 5 ÷ 108。どれも Claude API の資料のソースページ |
| `kind` のないページ | 105、約 97% | 105 ÷ 108。残る 3 は `experience-pattern` |
| タグ | 25 種 | リリース 43、試験 29、取り込み 26、wiki設計 19、browse 19 |

ひな形の語彙は人、会社、製品の関係（`founded`、`owns` など）が中心である。この wiki の中身はリリース、試験、設計判断の記録なので、合っていない。

**2. 語彙だけを足しても、問い合わせの結果は変わらない。**
型付きエッジは `graph.relationships[]` からしか作られず、extract は作り出さない（`graph-workflow.md` 23 行）。そのため、適用の単位にページの関係を含める必要がある。この点は既存案と同じ判断である。

**3. 述語を先にする理由。**

- query の操作は `neighbors`、`edges`、`path`、`facts` の 4 つで、ノード ID と述語で引く（`wiki_graph_query.py` 271〜283 行）。種類で一覧する操作はない。
- 種類の役目は、ノード ID の接頭辞と、lint の主語と目的語の制約である（`wiki_graph_extract.py` 555 行、`wiki_graph_lint.py` 253〜268 行）。
- 新しい種類は `maps_from` の `type` が必須なので、ページの `kind` か `graph.node_type` でしか付かない（`wiki_graph_extract.py` 516〜521 行）。`kind` のないページが 97% なので、種類を足すとページの分類の編集が要る。
- browse の 2 つのスクリプトに `node_type` の語は出ない（grep）。閲覧は関係表のためにオントロジーを読むが、種類での表示への影響は確かめていない。

**4. 例はページどうしの関係にする。**
目的語は、述語の `object_types` に `"*"` がなければ、ページのノードに解決しなければ `broken_object_refs` になる（`wiki_graph_lint.py` 242〜250 行）。既存案の例「版 → 変更 → 問題」は、版や問題のページがこの wiki にないので、そのままでは書けない。

**5. 種類の付け替えの影響は機械で数えられる。**

- 既存の道具で試せる。`lint --ontology <候補>` と `extract --ontology <候補> --out <一時の場所>` を実行し、`nodes.jsonl` を比べる。問い合わせは `query --db` で一時の DB を引く。
- 例として、`kind: experience-pattern` を新しい種類に対応させると、3 ページの ID が `concept:…` から変わる。コードと集計から読んだ結果で、実行はしていない。
- このとき切れる型付きの参照は 0 件である。10 本の目的語がすべて `source:*` だからである。
- 関係の試行にはページの写しが要る。extract は wiki のディレクトリを読むためである。

**6. スコープごとに独立させてよい。**

- 2 つの wiki を引く問い合わせの設計は「2 つの wiki のグラフをつなげない。`node_id` が同じでも同じノードとはみなさない」としている（`wiki-query-two-wikis-2026-11-16.md` 111 行）。
- ページを写す検討は「`graph:` の欄は写さず、写す先で抽出し直す」としている（`wiki-cross-scope-copy-options-2026-11-15.md` 第 1 節の 6）。
- どちらも未実装の設計だが、今の設計の範囲では、語彙が違っても費用は生じない。

**7. 別プラグインにしない。**
ADR-0009 が、グラフ層とオントロジーを wiki プラグインに残すと決めている。「分野別の語彙を複数配る需要も確認できない」とも書いている。

**8. 提案は全ページを読まない形にする。**
`wiki/` の Markdown は 112 ファイル、397,842 文字である（`SCHEMA.md`、`index.md`、`log.md` を含む）。全部を読むと数十万トークンになる見込みである（推定）。診断の数値、`index.md` の 1 行要約、frontmatter から候補を絞り、引用を取るページだけを読む。

**9. 診断は新しいコードである。**
`wiki_stats.py` にグラフの出力はない（grep で 0 件）。lint はページからノードとエッジをメモリ上で作るので、同じ作り方にすれば、古い生成物に頼らない。

## 検討した代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 既存の提供案のまま（引数なしで提案、既存ページの付け替えは禁止） | 入口の独立、wiki ごとの対象、少数の事例の試行、承認した案の固定には同意する。違いは結論の 5 の 3 点である |
| `/wiki:graph` のサブコマンドにする | `/wiki:graph` は決まったスクリプトの実行で、extract のほかは書かない。ページを編集する操作を混ぜると、危険の度合いが違うものが 1 つの入口に並ぶ |
| stats と lint の診断だけを出す | 費用は最小だが、「提案して実装する」に答えない。案内の 1 行として取り込んだ |
| `/wiki:init` と `/wiki:upgrade` に入れる | init の時点ではページがなく、内容にもとづく提案ができない。upgrade は既存のオントロジーを書き換えない決まりである（`graph-workflow.md` 168 行） |
| 分野別の既製の語彙を配る | 個別の内容に合わせる依頼と合わない。需要も確認されていない（ADR-0009） |
| 取り込みのたびに語彙を自動で足す | 語彙が取り込みごとに揺れる。`graph-workflow.md` 186 行は、エッジに合わせて項目を作ることを禁じている |
| 手での編集のまま | 今の状態である。結果は根拠の 1 の数値で、ひな形のまま 1 述語しか使われていない |

## 前提と不確実性

- **依頼の 3 行目は実行していない。** 私が 4 体のうちの 1 体なので、multi-agent-dispatch、ask-codex、サブエージェントは呼んでいない（仮定）。
- **ユーザースコープの中身は確かめていない。** この PC の既定の場所 `~/info-hive/wiki` に wiki がなく、グローバルの指示にも場所の記載がない。複数の分野が混ざるという見立ては推測である。この PC の状態を仕様にしないこと。
- **数値は作業ツリーのものである。** `wiki/graph/` には未コミットの変更がある。提供案と `docs/agent-runs/2026-11-19-wiki-ontology-experience/` は別のセッションの未コミットの成果で、並行して変わりうる。
- **適用の仕組みは作者の判断が要る。** ADR-0023 は承認済みだが、0.35.1 のスクリプトに `wiki_apply.py` と `wiki_fsguard.py` がない。ADR の対象もページ、索引、ログで、`ontology.yaml` を含まない。書く段の完成を待つか、差分の表示と上書き前の写しで始めるかを決める必要がある。ユーザースコープの wiki は Git にないことがある。
- **付け替えを許すかは作者の判断が要る。** 利用者が保存したノード ID（メモや外部のツール）は、影響の一覧で数えられない。
- **「述語を先に」の弱点がある。** 種類が source と concept だけだと、lint の型の制約はほとんど働かない。誤った関係を防ぐのは、証拠の引用と `--decide` の照合になる。
- **確かめていないこと。** 有用さの測り方、提案の保存場所、Codex の操作名の許可リスト、browse への影響。保存場所の候補は `graph/` の下か `.wiki-cache/` で、どちらもページの走査から外れる（`wiki_pages.py` 46 行）。
- **過去の検討との関係。** 2026-11-06 の発散の一覧に、22「分野の述語を足す」（★つき）、23、28「オントロジー変更の影響検査」がある。採点の行は見つけていない。
- **記録は残していない。** 制約に従い、wiki にも文書にも書いていない。

## 参照

- `wiki/graph/ontology.yaml`、`wiki/graph/nodes.jsonl`、`wiki/graph/edges.jsonl`、`wiki/index.md`、`wiki/SCHEMA.md`（137、158、182 行）
- `wiki/concepts/2つのwikiの分離の確かめ方.md`
- `info-hive-wiki/skills/info-hive/assets/ontology.yaml.template`
- `info-hive-wiki/skills/info-hive/references/graph-workflow.md`、`evolution-workflow.md`、`page-conventions.md`（56 行）、`retrieval-setup.md`（27 行）
- `info-hive-wiki/commands/graph.md`、`ingest.md`（21 行）、`query.md`（16〜18 行）、`init.md`、`upgrade.md`
- `info-hive-wiki/docs/graph.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`（443〜555 行）、`wiki_graph_lint.py`（150〜300 行）、`wiki_graph_query.py`（265〜283 行）、`wiki_graph_common.py`、`wiki_pages.py`（45〜46 行）、`wiki_codex.py`（68 行）
- `wiki_stats.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`（grep だけ）
- `docs/adr/0009-graph-layer-stays-in-wiki.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- `docs/plans/wiki-ontology-feature-experience-2026-11-19.md`、`docs/agent-runs/2026-11-19-wiki-ontology-experience/review-response.md`
- `docs/plans/wiki-query-two-wikis-2026-11-16.md`（111 行）、`docs/research/wiki-cross-scope-copy-options-2026-11-15.md`（第 1 節）
- `docs/research/wiki-knowledge-utilization-2026-11-06/brainstorm-diverge-converge.md`（162〜171 行）
- Git と GitHub: `info-hive-wiki` の origin/main（8c451e6、0.35.1）と開いている PR の一覧。`origin/fix/graph-ontology-handling` は extract の置き換えと排他の修正で、オントロジーの提案ではない
- 読んでいない: `docs/agent-runs/2026-11-19-wiki-ontology-experience-multi/`

このタスクに最適なモデルとエフォート: Fable または Opus、high。次のタスク（`/wiki:ontology` の設計書と診断の指標の確定）: Opus または Fable、high。

使用した MCP サーバー: なし
使用した Agent Skills: なし
