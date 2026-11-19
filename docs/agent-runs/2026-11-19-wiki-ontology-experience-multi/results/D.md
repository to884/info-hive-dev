## 結論

`wiki@info-hive` 0.35.1 では、**プロジェクトの wiki とユーザーの wiki に、それぞれ独自のオントロジーを持たせられます**。各 wiki の `graph/ontology.yaml` に、扱う対象の種類と、その間に記録できる関係を定義できます。一方、**その wiki の内容を調べて語彙を提案し、利用者が選んだ案を検証して適用する専用機能は、確認した版にはありません**。現在の手順は、ひな形を配置し、分野固有の語彙を編集して `lint` と `extract` を実行するところまでです。[グラフの現行コマンド](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/commands/graph.md#L9-L22)・[オントロジーの編集手順](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/references/graph-workflow.md#L78-L101)

**既存の `/wiki:graph` に、利用者が「この wiki で答えたい問い」から始められる操作を加える案を推します。** 利用の流れは次のとおりです。コマンド名は提案です。

| 段階 | 利用者の操作 | 表示・動作 |
|---|---|---|
| 対象を選ぶ | プロジェクトでは `/wiki:graph suggest`、個人用では `/wiki:graph suggest --user`。Codex では `$wiki:info-hive graph suggest` に同じ引数を渡す | 対象のスコープと解決した wiki のパスを表示し、その wiki の語彙とページを調べる |
| 提案を見る | たとえば「どのリリースが、どの設計判断を実装したか知りたい」と添える | 実際のページと根拠文、既存語彙で表せるか、候補の関係を使うと何を引けるかを示す。既存語彙で足りれば「追加不要」、根拠が薄ければ「保留」と返す |
| 選んで適用する | 候補ごとに「採用」「名前を変える」「見送り」を選ぶ | 採用分の日本語説明、英語の識別子、主語と目的語の型、確定する差分を表示する。承認後に対象 wiki の語彙を更新し、検査・再抽出する |
| 効果を確かめる | 同じ問いで結果を確認する | 語彙の登録と、過去のページへの関係の追記を区別する。既存ページにも適用したい場合は、出典のある追記候補を別に選べる。次回の取り込みでは採用済みの語彙を使える |

## 根拠

- **個別化の保存先はすでにあります。** `init_wiki.py` は選んだ wiki の `graph/ontology.yaml` にテンプレートを配置します。実例として、公開されているこのプロジェクトの `wiki/graph/ontology.yaml` とプラグインのテンプレートを比較すると、改行を `LF` に統一した全文は一致しました。このプロジェクトには標準語彙が置かれていると確認できます。個人の wiki が同じ内容かは未確認です。[初期化の実装 264–277 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/scripts/init_wiki.py#L264-L277)・[プロジェクトの定義](https://github.com/to884/info-hive-dev/blob/1a665190b9515d9945e26bdaa3af6169f7536b31/wiki/graph/ontology.yaml)・[配布テンプレート](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/assets/ontology.yaml.template)
- **語彙を増やさずに済む提案にも価値があります。** たとえばユーザーの wiki で「誰がどの論文を書いたかを引きたい」なら、標準の `authored` がすでに `person → paper` を扱えます。足りないのは述語か、ページ上の関係の記録かを切り分けられます。対して、プロジェクトで「リリースが設計判断を実装した」を繰り返し調べたいなら、実際に両者を結び付ける出典を示せた場合に `implements_decision` を候補にできます。後者は利用例で、今回の調査で採用を決めた語彙ではありません。[既定の述語 75–123 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/assets/ontology.yaml.template#L75-L123)
- **語彙を登録しただけでは、過去の事実は増えません。** 現行の抽出器は本文の `[[wikilink]]` から `mentions` を作り、具体的な型付き関係はページの `graph.relationships` から読みます。現行の取り込みも、ソースが明示的に裏付ける場合に型付き関係を追加します。そのため、提案では「語彙を登録した件数」と「出典付きで関係を記録した件数」を分けて示すのが適切です。[抽出手順 121–129 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/references/graph-workflow.md#L121-L129)・[取り込み手順 21 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/commands/ingest.md#L21)
- **適用前の試験には既存の仕組みを使えます。** `wiki_graph_lint.py --ontology <候補> --json` で対象 wiki を候補の語彙に照らし、現行語彙での検出結果と比較できます。`extract --ontology <候補> --out <一時出力先>` で変更後のグラフも試せます。特に `maps_from` の追加・変更では既存ページのノード ID が変わり得るため、影響するページと参照を承認前に示す必要があります。`extract` は不正な型のエッジがあっても動くので、成否は終了の有無だけで決めず、検査結果と代表質問の回答先で判断します。[lint の実装 518–555 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/scripts/wiki_graph_lint.py#L518-L555)・[抽出とノード ID の規約](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/references/graph-workflow.md#L121-L129)・[[グラフの抽出の契約]]

## 検討した代替案

| 案 | 採らなかった理由 |
|---|---|
| 初期化時に「研究用」「開発用」などの語彙セットを選ぶ | 新規 wiki には、実際に繰り返し現れる関係や利用者の問いを判断する材料が乏しい。標準語彙で始め、資料が蓄積した時点で同じ案内を出すほうが、既存 wiki にも役立つ |
| 取り込みのたびに新しい述語を自動追加する | 一つの資料での言い換えが別の述語として定着すると、同じ問いに複数の述語が必要になる。取り込みでは採用済みの語彙を使い、新しい語彙の採否は利用者がまとめて判断できるほうがよい |
| 二つのスコープをまとめて分析・適用する、あるいは別プラグインとして配る | 個人で蓄積した関係や根拠文を共有プロジェクトへ持ち込むおそれがある。各 wiki にすでに独立した正本があり、ADR-0009 でもグラフを wiki 内の任意の索引とする判断が記録されている。[ADR-0009「決定」「検討した案」](https://github.com/to884/info-hive-dev/blob/1a665190b9515d9945e26bdaa3af6169f7536b31/docs/adr/0009-graph-layer-stays-in-wiki.md#L24-L47) |

## 前提と不確実性

- 「最適」は、対象 wiki で利用者が繰り返す問いに、少数の語彙で出典までたどれること、と仮定しました。空の wiki では標準語彙から開始し、資料が少ない wiki では候補を保留できます。グラフを無効にしている wiki では、有効化を別の選択として提示するのが既存の規約に合います。[有効化の規約 7–15 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/references/graph-workflow.md#L7-L15)
- 初版は**既存語彙の再利用、新しい述語の追加、出典付きの少数ページでの試行**までを推します。既存ノード型の再割り当てや過去ページの一括移行まで提供するかは、作者の判断事項です。個人 wiki の実データでの提案品質は未評価です。
- ローカルの読み取りプロセスを起動できなかったため、GitHub 上の親リポジトリ `1a66519` が指すプラグイン `8c451e6`（0.35.1）を調べました。未公開の作業ツリーとの差分は未確認です。`multi-agent-dispatch` の独立回答を担当する一体として判断しており、他モデルの成果や合意はこの回答に含めていません。

## 参照

- 現行版と操作範囲を確認した箇所は、[`plugin.json` 1–5 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/.claude-plugin/plugin.json#L1-L5)、[`commands/` の操作一覧](https://github.com/to884/info-hive-wiki/tree/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/commands)、[`commands/init.md` 11–17 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/commands/init.md#L11-L17)、[`wiki_codex.py` 29–39、64–69 行](https://github.com/to884/info-hive-wiki/blob/8c451e6d009b42ac51e2626a090e3ed8a9a27e75/skills/info-hive/scripts/wiki_codex.py#L29-L69)です。
- プロジェクトの設計根拠は、[`wiki/index.md` 102–106 行](https://github.com/to884/info-hive-dev/blob/1a665190b9515d9945e26bdaa3af6169f7536b31/wiki/index.md#L102-L106)、[[グラフの抽出の契約]] の[「契約」「実装での解釈」](https://github.com/to884/info-hive-dev/blob/1a665190b9515d9945e26bdaa3af6169f7536b31/wiki/concepts/グラフの抽出の契約.md#L16-L34)、[移植計画の機械識別子に関する決定](https://github.com/to884/info-hive-dev/blob/1a665190b9515d9945e26bdaa3af6169f7536b31/docs/porting-plan.html#L930-L931)です。独立回答の扱いは [`multi-agent-dispatch/SKILL.md` 6–19 行](https://github.com/to884/dev-agent-skills/blob/1a015e0983915244a5e9f320849bda8da0b5900f/.agents/skills/multi-agent-dispatch/SKILL.md#L6-L19)に従いました。

使用した MCP サーバー: GitHub  
使用した Agent Skills: multi-agent-dispatch
