結論は、現時点では wiki 内に残す案です。分割によって独立したリリースは可能になりますが、共有する日本語正規化と判定処理をどう呼ぶか、新たな境界が必要です。最終成果には、分割する場合の構成・移行案と、分割せずに整理できる点の両方を示します。
## 結論

**現時点では別プラグインに分けず、wiki 内の任意モジュールとして境界を整理し、wiki 外からの実利用や独立した依存・リリース要件が生じた時点で分割を再検討すべきです。**

## 根拠

**1. グラフの実装にはまとまりがある一方、利用者の操作は wiki の手順と強く結び付いています。**

抽出・検証・問い合わせは専用のスクリプトに分かれています。しかし、グラフの入力は独立したデータセットではなく、wiki のページ型、`kind`、`sources:`、`raw:`、本文の wikilink、`graph:` メタデータです。抽出は、明示された関係に加え、通常のページからもノードと暗黙のエッジを作ります。したがって、グラフ機能を分割しても、wiki のデータ形式との結び付きは残ります。〔R4、R5：`wiki_graph_extract.py:143–190, 211–277, 306–414`〕

| wiki の操作 | 現在の結び付き | 分割後も必要になる連携 |
|---|---|---|
| 取り込み | 関係の記述、graph lint、extract、`log.md` への件数記録 | ページの編集完了と、検証・再生成の順序 |
| 問い合わせ | 関係を問う質問でグラフを使い、元のページを読む | グラフの利用可否・鮮度・出典の確認 |
| lint | 構造 lint と graph lint の結果を一緒に仕分ける | 検出結果と修正後の再生成 |
| upgrade | オントロジーなどの追加と、`SCHEMA.md` の不足検出 | wiki とグラフ、それぞれの更新責任 |

根拠は、`commands/ingest.md:21`、`query.md:20`、`lint.md:14–21`、`upgrade.md:12–20`、対応する workflow 文書です。〔R7〕

**推論：** 分割の難所はファイルの移動ではなく、「いつグラフを使い、いつ更新するか」という手順の引き継ぎです。現在は同じプラグインの中で完結する操作に、別プラグインの有効・無効と互換性の判定が加わります。

**2. 軽くなる余地はありますが、別プラグイン化を必要とするほどの効果は確認できていません。**

グラフの問い合わせは標準ライブラリだけを使い、抽出と graph lint は PEP 723 のメタデータで `pyyaml==6.0.3` を指定しています。グラフ専用の常駐サーバーはありません。〔R5：各スクリプト冒頭と import〕

ただし、**現在の通常セットアップも PyYAML を導入します。** `setup_wiki.py:4–19` は PyYAML を依存に含め、import で確認し、`:42–49` は準備結果にその版を含めます。`init_wiki.py:254` はこのセットアップを呼びます。よって、「グラフを使わなければ PyYAML の導入もない」とは言えません。〔R6、R8〕

分割すれば、グラフのコマンド・説明・テンプレートと PyYAML の準備を別にできます。一方、利用者には `graph@info-hive` の追加導入、有効化、更新、トラブル時の切り分けが増えます。プラグインを分けても Python パッケージの導入処理が自動的に分離するわけではなく、セットアップの変更が必要です。

**推論：** 初期化と依存の準備を選択式にするだけでも、軽量化の一部は得られます。容量、起動時間、コンテキスト量の削減は測定しておらず、大きな性能改善を分割の根拠にはできません。

**3. 「任意の層」という方針を、先にコード上の境界にする必要があります。**

確認した文書と実装には、次の差があります。

- 文書は、`ontology.yaml` がなければグラフ処理を実行しない方針です。しかし `init_wiki.py` は、通常の初期化と upgrade のどちらでも `graph/` とオントロジーを追加します。ファイルの存在だけでは、利用者がグラフを選んだことを表せません。〔R4：`graph-workflow.md:5`、R8：`init_wiki.py:47, 203–239, 256–263`〕
- 抽出スクリプト自体は、オントロジーがなくても空の定義を返し、生成を続けます。「何もしない」は主にエージェントへの手順指示であり、全 CLI 共通の制約ではありません。〔R5：`wiki_graph_extract.py:198–208, 606–624`〕
- 問い合わせ前の鮮度確認は workflow の指示で、問い合わせスクリプト自体には再生成の判定がありません。また、抽出は通常の wikilink や `sources:` も使うため、型付き関係の追加だけを更新契機にすると不十分です。〔R7：`query-workflow.md:40, ingest-workflow.md:138`、R5：`wiki_graph_query.py:248–252`〕

これらは、プラグインを分けても残ります。分割前に、有効化・更新・失敗時の扱いを統一するほうが効果的です。

**4. プラグインの依存宣言と、Python の import は別の問題です。**

分けるなら、宣言する依存の向きは **`graph → wiki`** が自然です。グラフは wiki のデータを利用し、wiki の通常操作はグラフなしでも成立するためです。`rag/.claude-plugin/plugin.json:5–7` に同じ方向の前例があります。〔R10〕

公式文書でも、他プラグインのスキルや MCP を使う依存を宣言できます。しかし、それだけで Python モジュールの import 経路が共有されるとは説明されていません。[Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)

現在のグラフコードには、次の内部依存があります。

- 3 本とも、同じディレクトリの `wiki_text.py` を使う。
- graph lint は抽出スクリプトの解析・エッジ生成を再利用する。
- `--decide` は `wiki_decide.py` を import する。
- 判定処理は `assets/decision-questions.json` を参照する。〔R5、R6〕

`${CLAUDE_PLUGIN_ROOT}` は、そのコンポーネントを持つプラグイン自身の導入先です。wiki の文面に書いた `${CLAUDE_PLUGIN_ROOT}/…` を、そのまま graph のファイル参照にはできません。また、manifest のコンポーネントパスはプラグイン内に収まる必要があります。[Manifest reference：パス規則・環境変数](https://code.claude.com/docs/en/plugins-reference)

**推論：** 隣のリポジトリやプラグインキャッシュを探索して import する実装は避けるべきです。分割には、共有処理を呼ぶ公開インターフェースか、配布時に共有するコードの管理方法が必要になります。

**5. 独立リリースの利点より、当面は互換性確認の負担が増えます。**

専用の抽出・問い合わせテスト群は `eval/` に見当たりません。`eval/decisions/test_decisions.py:352–375` は graph lint の既存出力と D2 を確認しますが、PyYAML がなければスキップします。日本語ノードの手作業確認は有用ですが、分割後の連携を保証するものではありません。〔R9。手作業確認については依頼文の情報〕

新プラグインにすると、コードのテストに加えて、wiki 単独、wiki＋graph、graph 無効、互換性のない組み合わせ、旧 wiki の移行を確認する必要があります。

リリースは `plugin.json` と CHANGELOG、タグ、GitHub リリース、マーケットプレイス導入確認までが対象です。分割後もマーケットプレイスの項目に `version` は書きません。独立更新は可能になりますが、両者が同じ `SCHEMA.md` や手順を更新するなら、調整は残ります。〔R1、R3、R10〕

なお、公式のバージョン制約付き依存は `<plugin-name>--v<version>` タグで解決します。リポジトリの現在の `vX.Y.Z` 方針だけを前提に制約を追加することは避け、採用前に整合を確認する必要があります。[Plugin dependencies：Release tags](https://code.claude.com/docs/en/plugins/dependencies#release-a-plugin-that-others-depend-on)

**6. log・rag の分割理由を、そのままグラフに当てはめることはできません。**

ADR-0006 の log は、日付ノートの記録頻度・型・孤立判定が wiki の前提と合わないために分割されました。グラフは、同じ wiki ページを別の方法で調べる機能であり、この不一致がありません。〔R3：ADR-0006「理由」〕

rag には PDF の抽出・OCR・埋め込み・永続ジョブ・再開という独立した処理と、MCP の窓口があります。現在のグラフは短命な CLI と再生成可能な索引が中心です。〔R3：ADR-0007「決定」、R5〕

ADR-0008 は wiki、日付ノート、ノート、RAG データの所有者を分けています。現行の抽出コードを作業領域全体へ広げるだけでは、log の型やソースの扱いに対応できません。〔R3：ADR-0008「各ディレクトリの役割」、R5：`derive_node_type`, `collect_pages`〕

**推論：** 将来の GraphRAG やノート横断検索は分割を検討する理由になりますが、現時点では実利用が確認されていない将来案です。

## 検討した代替案

**A. 今すぐ `graph@info-hive` に分割する**

独立した更新や無効化が可能になる利点はあります。ただし、現在は wiki の手順との連携を作り直す負担が先に生じるため、採りません。

分割を選ぶ場合の構成案は、次のとおりです。

| 項目 | 構成案 |
|---|---|
| 名前 | プラグイン `graph`、導入名 `graph@info-hive` |
| リポジトリ | `to884/info-hive-graph`。親リポジトリのサブモジュールにする |
| 宣言する依存 | graph の `dependencies` に `wiki@info-hive`。wiki は graph を必須にしない |
| コマンド | `/graph:init`、`/graph:extract`、`/graph:lint`、`/graph:query`、`/graph:upgrade` |
| 移すもの | 抽出・graph lint・問い合わせ、オントロジーと graph 用テンプレート、詳細仕様、グラフ固有の手順、D2 のエッジ収集・検出結果への変換 |
| wiki に残すもの | 通常のページ形式、wikilink、`sources:`・`raw:`、構造 lint・検索・統計、共通の日本語正規化、汎用の判定処理 |
| データの場所 | 引き続き `<WIKI_ROOT>/graph/`。ユーザーの `ontology.yaml` とページの `graph:` は移動しない |
| 開発資料・テスト | `info-hive-dev` の `docs/`、`tests/graph/`。プラグイン本体に開発資料を追加しない |

graph を wiki の依存にすると、wiki を導入した利用者へ graph も付いてくるため、選択導入の利点が薄れます。**宣言する依存は一方向、wiki の操作からの利用は任意**とします。

つなぎ方は次の案です。

1. graph 自身のスキル・コマンドが、自身の `${CLAUDE_PLUGIN_ROOT}` でスクリプトを参照する。wiki の手順からは、そのスキルを明示的に呼ぶ。
2. wiki の日本語別名変換と D2 を利用するため、版を持つ JSON の公開 CLI を用意する。wiki 側のスキルが、そのセッションで解決した CLI の絶対パスを渡す。graph は wiki の内部モジュールを直接 import しない。これは**新設が必要な設計案**であり、現在存在する API ではない。
3. ontology が存在しても graph が無効なら、型付き関係の作成・更新は止め、テキストの操作を続ける。索引が更新されなかったことを明示する。
4. 一般的なファイル編集を拾う `PostToolUse` フックを、取り込み完了の代用にはしない。ページを編集中の段階で lint・抽出してしまうためである。必要なら、明示的な完了通知で索引を古い状態にする仕組みを設計する。

Claude Code のフックはツール・ターン・セッションなどのイベントに反応します。「wiki の取り込みが完了した」という意味は別途定義する必要があります。[Hooks reference：イベント一覧](https://code.claude.com/docs/en/hooks#hook-events) この考え方は、PDF 閲覧から登録を推測しない ADR-0007 とも一致します。

移行は、**データ形式を変えず、実行担当だけを段階的に移す**案です。

- 先に日本語・NFC/NFD・既存 wiki の回帰テストと公開 CLI の契約を固める。
- graph を公開した後、wiki の移行版で `/wiki:graph` を互換用の入口にする。graph が有効なら委譲し、旧実装との二重実行を防ぐ。
- 取り込み・問い合わせ・lint・upgrade の呼び先、README、マーケットプレイスの説明を更新する。
- 利用者は `graph@info-hive` を追加する。オントロジー、ページ、カスタマイズ済み `SCHEMA.md` は保持し、生成物を再作成する。
- 互換期間の終了後に旧実装を撤去する。無効化・削除時にもユーザーのグラフデータは消さない。

現行 wiki は `0.2.0` です。撤去を伴う版は、例えば `0.3.0` として破壊的変更を明記し、新 graph は `0.1.0` から始める案が考えられます。具体的な版と互換期間は作者が決める必要があります。〔R10〕

**B. オントロジーだけを独立させる**

採りません。オントロジーはノードの対応付け、許可する述語、証拠の要否を決め、抽出と lint が解釈します。ここだけを別配布にすると、解釈するコードと仕様の互換性管理が増えます。利用者が編集する `ontology.yaml` と、配布するテンプレートも区別する必要があります。〔R4、R5〕

**C. wiki 内に残し、任意モジュールとして整理する――推奨案**

次を整理すれば、今の操作を保ちながら分割に備えられます。

1. **有効化を統一する。** 新規 wiki ではグラフを選択式にし、通常の upgrade が無効状態を勝手に変えないようにする。既存の ontology は保持する。
2. **依存の準備を分ける。** 基本の検索セットアップからグラフ用 PyYAML の確認を切り離し、グラフの初期化時に準備する。新しいプラグインは不要。
3. **仕様の所有箇所を決める。** `graph-workflow.md` を手順の中心とし、各コマンドには条件と呼び出しを残す。`SCHEMA.md` のグラフ節と upgrade 用マーカーは一組として管理する。
4. **共有部分を明確にする。** 日本語別名・NFC・引用照合は引き続き共通処理に置く。グラフ固有の解析・モデル構築と、共通テキスト処理の境界を明文化する。ファイルの物理移動は必須としない。
5. **索引の更新規則を統一する。** 型付き関係だけでなく、リンク、参照先、ページの追加・削除、オントロジーの変更も扱う。生成形式の版と入力の変更を識別できるようにする。
6. **テストを先に補う。** 親リポジトリの `tests/graph/` で、日本語の extract→lint→4 種の問い合わせ、無効状態、再生成、基本検索との解釈の一致、D2 の有効・無効を確認する。
7. **`graph/` の走査除外は残す。** `graph/README.md` を通常の wiki ページとして扱わないための規則であり、プラグイン分割の有無にかかわらず必要である。〔R6：lint・search・stats の除外定義〕

**判断を変える条件**

次の必要性が実利用で確認され、公開インターフェースと移行テストが整ったら、分割を再検討します。

- log、ノート、別の資料群など、wiki 以外にも型付きグラフを提供する。
- グラフ専用のデータベース、モデル、常駐処理などが増え、依存や実行負荷を分離する必要がある。
- wiki とグラフの変更頻度・担当・互換性方針が分かれ、独立リリースの利益が調整費用を上回る。
- 内部整理後も、不要なコマンドや説明の量が利用者の明確な負担として残る。

逆に、分割後も毎回 wiki と同時更新になり、連携不良による索引の更新漏れが続くなら、同梱へ戻す判断が妥当です。これらは測定済みの閾値ではなく、見直しの提案条件です。

## 前提と不確実性

- 今回はファイルと公式文書の読み取りによる判断です。ファイル変更、ビルド、テスト実行はしていません。指定された他エージェントの成果保存先も読んでいません。
- 日本語ノードの手作業確認結果は依頼文を前提とし、今回は再現していません。
- グラフの利用率、実際の wiki の規模、容量・処理時間・コンテキスト量は未測定です。軽量化の効果は定量化できません。
- 分割によって移植元の修正を取り込む際の変更先は増えます。ただし、方針 A は必要な修正だけを個別に取り込む方針なので、移植元との同じ配置を守るためだけに同梱を維持する必要はありません。分割時は移動対応表と取り込み履歴を残す案です。〔R2「方針 A」、R1「移植元の修正」〕
- 方針 G のローカル運用は維持します。プラグイン分割を、ホスト型サービス導入の理由にはしません。〔R2「方針 G」〕
- 公式仕様は閲覧時点のものです。利用対象の Claude Code の版におけるスキル間呼び出し、ローカル開発、依存解決は、実装前の確認が必要です。

作者が決める必要のある事項は、次のとおりです。

1. **グラフの提供範囲**：wiki の索引に限定するか、作業領域全体を扱う製品に育てるか。
2. **軽さの優先順位**：依存パッケージ、コマンド数、説明の量のどれを減らしたいか。
3. **新規 wiki の既定**：グラフを明示的な選択式に変えるか。既存の ontology がある利用者は、有効状態を維持するか。
4. **共有処理の公開範囲**：将来分割する場合、日本語正規化と D2 を公開 CLI/API として支えるか。
5. **移行の約束**：`/wiki:graph` の互換期間、旧版との対応範囲、SemVer、依存制約とタグの運用。

## 参照

本文の R 番号は以下に対応します。コードの行番号は今回確認した作業ツリーのものです。

- **R1 — 運用規則**：[AGENTS.md](C:/Works/info-hive-dev/AGENTS.md)。「リポジトリの役割」「日本語と機械が読む文字列」「リリース」「rag プラグインの開発」。
- **R2 — 移植方針**：[docs/porting-plan.html](C:/Works/info-hive-dev/docs/porting-plan.html)。方針 A（485–488 行）、B（493–501 行）、G（545 行以降）、P1・P4・P5。
- **R3 — 既存の設計判断**：[ADR-0003](C:/Works/info-hive-dev/docs/adr/0003-split-marketplace-repo.md) の決定・理由・影響、[ADR-0006](C:/Works/info-hive-dev/docs/adr/0006-daily-journal-is-separate-plugin.md) の決定・理由、[ADR-0007](C:/Works/info-hive-dev/docs/adr/0007-rag-uses-mcp-core-and-persistent-jobs.md) の決定・未決事項、[ADR-0008](C:/Works/info-hive-dev/docs/adr/0008-numbered-workspace-layout.md) の作業領域・各ディレクトリの役割・理由。
- **R4 — グラフの仕様**：[graph-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md) の3–13、43–56、92–124行、[docs/graph.md](C:/Works/info-hive-dev/info-hive-wiki/docs/graph.md) の5–9、28–32、85–91行、[commands/graph.md](C:/Works/info-hive-dev/info-hive-wiki/commands/graph.md) の11–22行。
- **R5 — 実装**：[wiki_graph_extract.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)、[wiki_graph_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py)、[wiki_graph_query.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_query.py)。解析・モデル構築・出力・CLI、lint の共有 import と D2。
- **R6 — 共通処理と基本機能**：[wiki_text.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py) の1–103、181–309、396–411行、[wiki_decide.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py) の54–76、335–412行、[setup_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/setup_wiki.py) の1–49行。[wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py):111、[wiki_search.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py):288、[wiki_stats.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_stats.py):56 の走査除外。
- **R7 — 組み込まれた手順**：[SKILL.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md):43–53、[ingest-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md):130–138、[query-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md):31–40、[lint-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/lint-workflow.md):15–23、[architecture.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/architecture.md):38–42、[decision-models.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/decision-models.md):19–40。コマンドの [ingest.md](C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md):21、[query.md](C:/Works/info-hive-dev/info-hive-wiki/commands/query.md):20、[lint.md](C:/Works/info-hive-dev/info-hive-wiki/commands/lint.md):14–21、[upgrade.md](C:/Works/info-hive-dev/info-hive-wiki/commands/upgrade.md):12–45。
- **R8 — 初期化とテンプレート**：[init_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py):47–90、203–263、[SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template):113–141、161–185、[ontology.yaml.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/ontology.yaml.template):11–123。
- **R9 — テスト**：`info-hive-wiki/eval/` のファイル一覧、[test_decisions.py](C:/Works/info-hive-dev/info-hive-wiki/eval/decisions/test_decisions.py):26、352–375、対応する `fixtures/graph_wiki/` と `graph_lint_golden.json`。[wiki-tests.yml](C:/Works/info-hive-dev/info-hive-wiki/.github/workflows/wiki-tests.yml):22、62 の依存導入。
- **R10 — 配布定義**：[wiki/plugin.json](C:/Works/info-hive-dev/info-hive-wiki/.claude-plugin/plugin.json):2–4、[rag/plugin.json](C:/Works/info-hive-dev/info-hive-rag/.claude-plugin/plugin.json):2–7、[marketplace.json](C:/Works/info-hive-dev/info-hive-marketplace/.claude-plugin/marketplace.json):9–51。
- **公式文書**：本文中にリンクした [Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)、[Manifest reference](https://code.claude.com/docs/en/plugins-reference)、[Plugin components](https://code.claude.com/docs/en/plugins/components#reference-plugin-paths-and-store-data)、[Hooks reference](https://code.claude.com/docs/en/hooks)。

使用した MCP サーバー: node_repl（読み取り試行のみ。タイムアウト）  
使用した Agent Skills: なし
