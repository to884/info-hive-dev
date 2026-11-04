あなたは総括の書き手です。
同じタスクに 2 体のエージェントが独立して取り組み、その後、各エージェントが自分以外の成果をレビューしました。
成果とレビューを読み、作者（このリポジトリの所有者）が判断できる総括を 1 本書いてください。
あなたの最終メッセージだけが `summary.md` として保存されます。
エージェントは記号で呼びます（エージェント C、エージェント D）。記号とモデルの対応は末尾に表として付けるので、本文ではモデル名で優劣を語らないでください。

## タスク

# タスク：グラフとオントロジーの機能を別プラグインに分けるべきか検討する

## 作者の指示

> グラフ、オントロジーの機能を別プラグインとして分割するべきか検討してください

対象は、info-hive の wiki プラグイン（`info-hive-wiki`、プラグイン名 `wiki`、導入名 `wiki@info-hive`）が今持っている型付きグラフ層である。オントロジー（`graph/ontology.yaml`）、ページの frontmatter の `graph:` メタデータ、抽出・lint・問い合わせのスクリプト、`/wiki:graph` コマンド、取り込み・問い合わせ・lint・アップグレードの各手順に組み込まれたグラフの段を含む。図表（ADR-0005 の mermaid と svg）は対象外である。

## 現状として分かっていること

- グラフ層は移植元 llm-wiki-plugin v0.3.0 で加わった任意の層で、`graph/ontology.yaml` がなければ何もしない。正本は Markdown で、`graph/` の生成物（`nodes.jsonl`、`edges.jsonl`、`graph.sqlite`、`graph.graphml`）はいつでも作り直せる。
- 2026-11-04 に、日本語のノード（`person:山田太郎` など）で extract、lint、`neighbors`・`edges`・`facts`・`path` が動くことを手作業で確かめた。グラフ層の専用のテストは `eval/` にない（判定レイヤーのテスト `eval/decisions/` がグラフの lint の一部を使う）。
- 別のプラグインに依存するプラグインの前例として、`rag`（`info-hive-rag`）が `plugin.json` の `dependencies` に `wiki@info-hive` を宣言している。
- プラグインを足すときの手順は `AGENTS.md` の「リポジトリの役割」にある。

## 読むべき文書とコード

- `AGENTS.md`（リポジトリの役割、プラグインを足す手順、リリースとバージョン、日本語と機械が読む文字列の方針）
- `docs/porting-plan.html`（wiki の移植方針。方針 A・G など）
- `docs/adr/` の 0003（マーケットプレイスの分割）、0006（日々の記録を別プラグインにした判断）、0007（rag の構成）、0008（作業領域の構成）
- `info-hive-wiki/skills/info-hive/references/graph-workflow.md`、`info-hive-wiki/docs/graph.md`、`info-hive-wiki/commands/graph.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`、`wiki_graph_lint.py`、`wiki_graph_query.py`
- グラフに触れている wiki 側のファイル：`skills/info-hive/SKILL.md`、`references/ingest-workflow.md`、`references/query-workflow.md`、`references/lint-workflow.md`、`references/architecture.md`、`references/decision-models.md`、`scripts/init_wiki.py`（graph のテンプレートと `SCHEMA_SECTION_MARKERS`）、`scripts/wiki_text.py`、`scripts/wiki_lint.py`・`wiki_search.py`・`wiki_stats.py`（`graph/` の除外）、`scripts/wiki_decide.py` と `eval/decisions/`、`assets/SCHEMA.md.template`、`assets/ontology.yaml.template`、`commands/ingest.md`・`query.md`・`lint.md`・`upgrade.md`
- `info-hive-rag/.claude-plugin/plugin.json`（依存の宣言の例）、`info-hive-marketplace/.claude-plugin/marketplace.json`
- Claude Code のプラグインの依存と、プラグインどうしでスクリプトや `${CLAUDE_PLUGIN_ROOT}` を参照できるかについての公式の文書

## 成果に含めるもの

1. 結論：分けるべきか、分けないべきか、条件付きか。一文で書く。
2. 判断の根拠。少なくとも次の観点を扱う：wiki の手順（取り込み・問い合わせ・lint・アップグレード）との結び付きの強さ、利用者が導入する手間と得られる軽さ、依存の向き（グラフが wiki に依存するのか、wiki がグラフの有無で分岐するのか）、PyYAML などの依存パッケージ、`${CLAUDE_PLUGIN_ROOT}` とスクリプトの置き場所、テストとリリース（SemVer とマーケットプレイス）、移植元の修正の取り込みやすさ、log と rag など今後のプラグインとの関係。
3. 分ける場合の構成案：プラグイン名、リポジトリ、wiki 側に残すもの・移すもの、wiki とのつなぎ方（依存の宣言、フック、コマンドの名前）、既存の wiki と利用者の移行。
4. 分けない場合に、境界をはっきりさせるため wiki の中で整理すべきこと。
5. 判断を変える条件（どうなったら分ける、または戻すべきか）。
6. 作者が決める必要のある未決事項。

リポジトリのファイルは書き換えないこと。成果は日本語で書く。


## 成果

### エージェント C

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

### エージェント D

## 結論

**現時点では別プラグインに分けず、wiki 内でグラフ層の有効化・依存・更新責務を整理し、wiki 以外からの利用や独立したリリースの必要性が具体化した時点で分割を再検討すべきです。**

## 根拠

以下では、`W` を `info-hive-wiki/`、`S` を `info-hive-wiki/skills/info-hive/` の略記とします。構成案や改善案は提案であり、実装済みの仕様とは区別します。

### 1. 処理本体は分離しやすいが、利用手順は wiki と強く結び付いている

グラフは、wiki のページ、frontmatter、wikilink、ソースの要約ページを入力にします。オントロジーも、wiki の `type` と `kind` をノード型へ対応付けています。さらに、通常の操作に次の段が組み込まれています。

| wiki の操作 | グラフとの接点 | 根拠 |
|---|---|---|
| 取り込み | 型付き関係をページに記録し、lint、extract、操作ログへの追記を行う | `W/commands/ingest.md` 19–21行、`S/references/ingest-workflow.md` 130–142行 |
| 問い合わせ | 関係を問う質問でグラフを参照し、元ページを読んで回答する。古い索引は再生成する | `W/commands/query.md` 19–21行、`S/references/query-workflow.md` 31–40行 |
| lint | 構造検査にグラフ検査を追加し、修正後に再生成する。任意の D2 証拠判定も使う | `W/commands/lint.md` 13–21行 |
| 初期化・アップグレード | オントロジーなどの配置、SCHEMA の節の検出、利用者のメモリへの案内を扱う | `S/scripts/init_wiki.py` 47–89、220–231行、`W/commands/upgrade.md` 18–45行 |

したがって、別プラグインにしても、wiki 側にはグラフが利用可能かを確認する分岐と、処理を呼ぶ段が残ります。**配布を分けるだけでは、手順上の結び付きは減りません。**

一方、抽出・検査・問い合わせが別スクリプトになっている点は、将来の分割に有利です。今はこの処理境界を明確にする段階が妥当と判断します。

### 2. 「任意の層」は、実装全体では徹底されていない

文書の説明を、そのまま全入口の動作と見なすことはできません。

- **初期化・アップグレードはグラフのファイルを常に配置します。** `SUBDIRS` に `graph` があり、テンプレートのコピー対象にもオントロジー、README、`.gitignore` が含まれます。既存ファイルは上書きしませんが、グラフを作らない引数はありません。`S/scripts/init_wiki.py` 47、93–103、220–231、273–281行。
- **PyYAML は必須セットアップにも入っています。** `setup_wiki.py` は `pyyaml==6.0.3` を宣言し、読み込みを確認します。グラフの extract と lint だけが必要時に取得する構成にはなっていません。`S/scripts/setup_wiki.py` 2–19、42–48行、`S/references/retrieval-setup.md` 27–36行。
- **オントロジー欠落時の CLI の挙動が異なります。** extract は空のオントロジーを返して生成へ進み、lint はエラー終了します。query は SQLite の存在を確認し、オントロジーを確認しません。「なければ何もしない」は主としてエージェント向け手順の規則です。`S/scripts/wiki_graph_extract.py` 198–208、602–625行、`wiki_graph_lint.py` 487–497行、`wiki_graph_query.py` 248–252行。

分割の前に、**導入済み・有効・未構築・更新が必要という状態と、それぞれの入口の動作を揃える必要があります。** この整理は同一プラグインのまま実施できます。

### 3. 分割による軽量化はあるが、現時点では効果を過大評価できない

グラフ利用者には、追加プラグインの導入・有効化、コマンド名の変更、wiki との組み合わせ確認が発生します。非利用者には、グラフ用の説明、コマンド、テンプレート、明示的な PyYAML 依存を減らせる利点があります。

ただし、次の点を考慮すべきです。

- 通常のグラフ問い合わせは標準ライブラリと共通の `wiki_text` で動きます。グラフ専用のモデルや外部データベースサーバーは要求していません。`S/scripts/wiki_graph_query.py` 29–39行。
- wiki の初期化には FastEmbed と sqlite-vec のセットアップが残ります。グラフ分割でモデルの導入費用までなくなるわけではありません。`S/scripts/init_wiki.py` 145–165行、`setup_wiki.py` 2–8行。
- PyYAML の明示的な要求を外しても、検索側の推移的依存として残るかは今回確認していません。
- ディスク容量、起動時間、プロンプトのトークン削減量は未測定です。現段階の軽量化評価は、依存宣言と文書構成に基づく推論です。

そのため、まず内部整理で得られる改善を確かめるほうが、追加の配布単位を持つ判断をしやすくなります。

### 4. 依存宣言と、Python のコード共有には別の設計が要る

現在の実装には、次のコード依存があります。

```text
wiki_graph_lint
  ├─ wiki_graph_extract
  ├─ wiki_text
  └─ wiki_decide                 --decide 使用時
       ├─ wiki_text
       └─ assets/decision-questions.json

wiki_graph_extract ─ wiki_text
wiki_graph_query   ─ wiki_text
```

`wiki_text` は、日本語の別名、Unicode 正規化、引用照合などを wiki 全体で共有します。`wiki_decide` は D1〜D5 を扱い、グラフ専用部分は D2 です。グラフのスクリプトだけ移すと、これらの import と相対パスが成立しなくなります。根拠は `S/scripts/wiki_graph_extract.py` 52–55行、`wiki_graph_lint.py` 55–60、304–307、460–465行、`wiki_graph_query.py` 36–39行、`wiki_decide.py` 54–76行です。

Claude Code の公式文書では、`dependencies` は依存先の導入・有効化とバージョン解決を扱います。`rag` の宣言は分割の前例になりますが、Python の import パスを共有する契約にはなりません。[Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)

`${CLAUDE_PLUGIN_ROOT}` は、そのコンポーネントを提供するプラグインの配置先を指します。更新で場所が変わり、manifest のコンポーネントパスにはプラグイン内への制限があります。相手の配置先を得る専用変数は、確認した文書では見つかりませんでした。推論として、隣接ディレクトリやキャッシュの形を推測する設計は避け、公開した窓口を使うべきです。[Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference#environment-variables)

### 5. log・rag の分割理由を、そのままグラフに適用するのは難しい

- **log** は、日付ノートの更新頻度や孤立ページの扱いが wiki の前提と合わないことが、分割の理由です。グラフは wiki の既存ページと出典管理を利用するため、この理由の当てはまり方が異なります。`docs/adr/0006-daily-journal-is-separate-plugin.md` 21、84–91行。
- **rag** は、PDF の抽出・OCR・埋め込み、永続ジョブ、再開処理という独立した実行責務を持ち、MCP の明示的な登録 API があります。グラフにも同様の接続方法は作れますが、現状の三つの CLI に追加の実装が必要です。`docs/adr/0007-rag-uses-mcp-core-and-persistent-jobs.md` 22–39行。
- **作業領域の共有とプラグイン分割は別に扱えます。** ADR-0008 は `wiki`、日付ノート、`92_RAG` を区別し、共通の場所解決については同じ入力への一致試験を求めています。グラフを分割しても、既存の `<WIKI_ROOT>/graph/` を使い続ける構成が自然です。`docs/adr/0008-numbered-workspace-layout.md` 79–90、118–127、191–192行。

log や rag が将来グラフを直接利用する可能性はあります。ただし、今回確認した設計には、日付ノートや PDF チャンクを共通オントロジーへ統合する具体的な要件はありません。現時点でそれを分割理由にする部分は推測です。

### 6. テストと更新管理の負担が、先に増える

`W/eval/decisions/test_decisions.py` 352–375行には、グラフ lint の既存出力、D2、バックエンド不在時の試験があります。PyYAML がなければ、このクラスはスキップされます。`eval/scripts/test_frontmatter.py` は入れ子を通常の解析器が読み込まないことを、`test_help.py` は graph コマンドの掲載を検査しています。

一方、extract から四つの問い合わせまでを通す専用の回帰試験は、確認した `eval/` では見つかりませんでした。ユーザーから提示された日本語での手動確認は有用ですが、分割後の import、配置、旧データ、バージョンの組み合わせを保証する範囲には届きません。

分割すると、wiki と graph の互換性確認、二つの CHANGELOG、リリース順序、マーケットプレイスからの導入確認が必要です。移植元の修正も、スクリプトと wiki の手順にまたがる変更を二つのリポジトリへ振り分けることになります。

移植計画の方針 A は必要な修正を選択的に取り込む方式なので、分割自体は方針に反しません。ただし、対応パスと変更履歴の管理が増えるという推論になります。方針 G のホスト型機能を削る判断は、今回の分割とは独立して維持できます。根拠は `docs/porting-plan.html` 485–499、545–555行、`W/UPSTREAM.md`「移植元の修正を取り込む手順」です。

### 分けない場合に整理すべきこと

1. **有効化の条件を統一する。**  
   新規作成でグラフを選んだ場合のテンプレート配置と依存準備を明確にし、既存 wiki のオントロジーは保全する。オントロジー欠落時の通常ワークフローと明示的な CLI 呼び出しについて、それぞれの終了状態を決める。

2. **グラフの規約と手順の正本をまとめる。**  
   `graph-workflow.md` に有効化、更新、検査、問い合わせ、再生成の規約を集約し、ingest・query・lint・upgrade は呼ぶ時点と結果の扱いを記述する。SCHEMA のグラフ節と `SCHEMA_SECTION_MARKERS` は対応を明示する。英語の検出見出しは維持する。

3. **更新が必要になる条件を修正する。**  
   現在の取り込み手順には、型付きメタデータや新規ページが増えなければ再生成を省く説明があります。しかし抽出は既存ページの wikilink、`sources`、`raw` からもエッジを作ります。これらの編集でも索引が変わるため、変更検出の対象に含める必要があります。`S/references/ingest-workflow.md` 138行、`S/scripts/wiki_graph_extract.py` 360–414行。

4. **共通処理とグラフ固有処理の境界を保つ。**  
   日本語の別名と正規化は `wiki_text`、判定バックエンドは `wiki_decide` に集約する。グラフ側は入力・出力・必要な関数を明示する。`wiki_lint.py`、`wiki_search.py`、`wiki_stats.py` の `graph/` 除外も、派生データを通常ページとして扱わない契約として残す。

5. **分割判断にも使える回帰試験を親リポジトリに追加する。**  
   日本語・NFC/NFD、旧ページ、独自オントロジー、暗黙のエッジ、四つの問い合わせ、D2 の有無、無効状態、初期化・アップグレードの冪等性を対象にする。配置は `info-hive-dev/tests/graph/` を提案する。中断後の再生成も対象にし、既存 DB を先に削除する実装を踏まえて公開途中の状態を検証する。`S/scripts/wiki_graph_extract.py` 447–451行。

## 検討した代替案

### A. 今すぐ `graph@info-hive` に分割する

独立して導入・更新できる利点があります。ただし、現時点では接続と共有コードの設計、移行試験の負担が先行すると判断します。

将来この案を選ぶ場合は、次の構成を提案します。

#### 配布単位と依存方向

- プラグイン名は `graph`、導入名は `graph@info-hive`。
- リポジトリは `to884/info-hive-graph`。親リポジトリのサブモジュールにする。
- `graph/.claude-plugin/plugin.json` に `"dependencies": ["wiki@info-hive"]` を宣言する。
- wiki は graph を必須依存に加えず、グラフの窓口が利用可能かによって連携する。
- 設計書とテストは `info-hive-dev` に置く。マーケットプレイスには GitHub source の項目を追加し、`version` は書かない。AGENTS.md に graph の開発節を追加する。

これは `AGENTS.md`「リポジトリの役割」と、ADR-0003 の配置方針に沿う構成です。

#### 移すものと残すもの

| graph に移す責務 | wiki に残す責務 |
|---|---|
| オントロジーのテンプレートと管理手順 | 通常のページ、frontmatter、wikilink、出典の規約 |
| `wiki_graph_extract.py`、`wiki_graph_lint.py`、`wiki_graph_query.py` | 取り込み・問い合わせ・lint の全体進行 |
| `graph-workflow.md`、利用者向け graph 文書 | グラフ連携を行う時点と、結果を利用者へ示す処理 |
| graph README、`.gitignore`、SCHEMA のグラフ部分の更新処理 | SCHEMA 全体の管理、通常部分の upgrade |
| 型付き関係の記述・検査規約 | 通常の構造 lint、検索、統計と `graph/` の除外 |

利用者の `graph:` メタデータは、引き続き wiki ページ内に保存します。`ontology.yaml` は利用者が編集する正本であり、四つの生成物とは別扱いにします。独自オントロジーをテンプレートで置き換える移行は避けます。根拠は `S/references/graph-workflow.md` 114–124行です。

共有する日本語処理と判定クライアントは、配布時に各プラグイン内へ同梱する小さな共通部分として切り出し、同一の入力に対する一致試験を設ける案を提案します。D2 の呼び出し部分は graph が持ち、他の判定処理も利用する通信・設定部分は共有対象にします。この整理には、現状の `wiki_decide.py` の分解が必要です。

#### wiki とのつなぎ方

具体案として、graph に薄い MCP 窓口を置き、CLI と同じ処理本体を呼ばせます。これは新規実装です。

- graph 自身のコマンドと MCP 設定は、graph 自身の `${CLAUDE_PLUGIN_ROOT}` からスクリプトを参照する。
- wiki の手順は、利用可能な graph のツールへ明示的に `<WIKI_ROOT>` を渡す。
- 取り込み後と承認された修正後は lint・extract、関係の問い合わせでは query を呼ぶ。
- グラフのデータがあるのに窓口が利用できない場合は、グラフの検査・更新を実施していないことを報告する。通常の wiki 操作は継続できる設計にする。
- コマンドは `/graph:init`、`/graph:extract`、`/graph:lint`、`/graph:query`、`/graph:upgrade` とし、query の下で既存の四操作を受け付ける。

初期案では、汎用の `PostToolUse` に抽出を任せるフックは設けません。公式フックはツール実行などのイベントで発火するため、複数ページにまたがる取り込みの完了を別途判定する必要があります。wiki の手順から明示的に呼ぶほうが、lint と利用者の確認の順序を維持しやすいという判断です。[Hooks reference](https://code.claude.com/docs/en/hooks#hook-lifecycle)

#### 既存利用者の移行とリリース

1. まず既存版で回帰試験を整え、現在のデータ形式と CLI 出力を基準にする。
2. graph を追加し、同じ Markdown とオントロジーから同じ結果を得られることを確認する。
3. wiki に移行案内を追加する。移行期間は `/wiki:graph` を互換入口として残し、graph 導入済みの場合の委譲先を一つにする。
4. 利用者の SCHEMA、エージェントのメモリ、独自スクリプトに残る旧パス・コマンドを確認して移行する。
5. データの置き場所は `<WIKI_ROOT>/graph/` を継続し、必要な生成物だけ再生成する。
6. 互換期間を終える版で wiki 内の実装を除去する。

現在の wiki は `0.2.0` です。既存コマンドの除去や追加導入の必須化は、利用者にとって互換性のない変更として扱うべきです。0.x での具体的な番号と互換期間は作者が決め、`plugin.json` と CHANGELOG に明示します。1.x 以降なら major 更新に相当する判断です。

リリースは graph の提供を先行させ、wiki の除去版を後にします。main、タグ、GitHub リリース、マーケットプレイスからの導入確認までを完了条件とします。依存にバージョン範囲を指定する場合、現行公式文書は `<plugin-name>--v<version>` タグによる解決を説明しているため、現在の `vX.Y.Z` タグ運用との整合確認も必要です。[Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies#release-a-plugin-that-others-depend-on)

### B. オントロジーだけを別プラグインにする

現時点では採りません。オントロジーは型、述語、証拠要求を宣言し、extract と lint がその規約を解釈します。別配布にすると、小さな設定と実装の互換性管理が新たに必要です。

分野別の語彙を複数配る需要が出た場合は、オントロジーのテンプレート集として独立させる余地があります。その需要は今回の資料から確認できませんでした。根拠は `S/assets/ontology.yaml.template` の `node_types` と `predicates`、`S/references/graph-workflow.md` 49–56行です。

### C. wiki・log・rag 共通のグラフ基盤へ直ちに拡張する

将来候補として残します。現行のノード ID、ソース参照、引用照合は wiki のページを前提にしています。日付ノート、PDF チャンク、複数 wiki を扱うなら、識別子の名前空間、出典の位置、削除・更新の通知を先に設計する必要があります。

この案を採る条件が整えば、独立プラグインの価値は大きくなります。

## 前提と不確実性

### 判断を変える条件

次のいずれかが具体化したら、分割を再検討します。

- log・rag・複数 wiki から、共通の関係問い合わせやオントロジー管理を直接利用する要件ができた。
- グラフ専用のストレージ、推論処理、大きな依存パッケージが必要になった。
- グラフだけの更新が頻繁になり、wiki 全体のリリース待ちが実際の支障になった。
- 内部整理後も、非利用者の導入時間やコンテキスト負担が問題として測定された。
- 公開窓口、共有コード、旧データの互換試験が揃い、分割による連携費用を受け入れられるようになった。

分割後、主要な変更のたびに両プラグインの同時更新が必要となり、独立利用も増えず、連携障害が継続するなら、wiki への再統合を検討すべきです。判断材料は変更履歴、障害記録、実際の利用状況です。

### 作者が決める必要のある事項

1. **グラフの対象範囲**  
   当面は wiki の任意索引として育てるか、log・rag を含む知識基盤を目指すか。

2. **「使わない」の意味**  
   新規 wiki にテンプレートだけ配置するか、オントロジーと依存準備も選択時に限定するか。現在の既定動作からの変更を含みます。

3. **分割時の公開窓口**  
   上記の MCP 案に必要な実装・依存を受け入れるか。公式文書には `bin/` の実行ファイルを Bash の `PATH` に載せる方式もあり、公開 CLI 案との選択には対象環境での確認が必要です。[Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference#standard-layout)

4. **対応する導入形態**  
   Claude Code プラグインだけでなく、現在の skills.sh 経由や他のエージェントでのスキル利用にも、分割後のグラフを提供するか。

5. **互換期間とリリース規則**  
   `/wiki:graph` と旧スクリプトパスをいつまで残すか、0.x の破壊的変更をどの版で出すか、依存のバージョン範囲を使うか。

### 調査の限界

- 本判断はローカルファイルの静的な読解と公式文書に基づきます。ファイル編集、ビルド、テスト実行は行っていません。
- 日本語ノードの手動動作確認は、依頼文で提示された結果を前提にしています。
- Claude Code のインストール済みバージョンと、提案したプラグイン間接続の実動作は未確認です。
- 「今は単一 wiki の索引としての価値を優先する」という仮定を置きました。作者が横断グラフを近い将来の中核機能に据える場合、分割の優先度は上がります。
- 軽量化や保守費用について、測定値に基づく数値評価はしていません。

## 参照

### 運用・設計

- `AGENTS.md` の「リポジトリの役割」「wiki プラグインの開発」「rag プラグインの開発」「リリース」。
- `docs/porting-plan.html` の方針 A・B・G、485–499、545–555行。
- `docs/adr/0003-split-marketplace-repo.md` の決定・理由、18–30行。
- `docs/adr/0006-daily-journal-is-separate-plugin.md` の背景・分割理由、21、84–91行。
- `docs/adr/0007-rag-uses-mcp-core-and-persistent-jobs.md` の決定・理由、22–39行。
- `docs/adr/0008-numbered-workspace-layout.md` のディレクトリの役割、場所解決、共通部分、79–104、118–127、183–192行。
- `info-hive-wiki/UPSTREAM.md` の起点と修正取り込み手順。
- `info-hive-wiki/.claude-plugin/plugin.json`、`info-hive-rag/.claude-plugin/plugin.json`、`info-hive-marketplace/.claude-plugin/marketplace.json`。

### 文書・コード

- `S/SKILL.md` のグラフ層、初期化、付属スクリプトとテンプレート。
- `S/references/graph-workflow.md`、`W/docs/graph.md`、`W/commands/graph.md`。
- `S/references/ingest-workflow.md` の手順 8b・9、`query-workflow.md` の手順 2b、`lint-workflow.md` のグラフ検査。
- `S/references/architecture.md` の任意のグラフ層、`decision-models.md` の D2、`retrieval-setup.md` の依存準備。
- `W/commands/ingest.md`、`query.md`、`lint.md`、`upgrade.md` のグラフに関する段。
- `S/scripts/wiki_graph_extract.py` のページ収集・正規化・ノードとエッジ生成・出力・CLI。
- `S/scripts/wiki_graph_lint.py` の共有処理・構造検査・`decide_evidence`・CLI。
- `S/scripts/wiki_graph_query.py` の SQLite 接続・四つの問い合わせ・CLI。
- `S/scripts/init_wiki.py` の `SCHEMA_SECTION_MARKERS`、テンプレート配置、`install_runtime`。
- `S/scripts/setup_wiki.py` の固定依存と準備完了の出力。
- `S/scripts/wiki_text.py` の別名と正規化、`wiki_decide.py` の設定・質問ファイル・D2。
- `S/scripts/wiki_lint.py`、`wiki_search.py`、`wiki_stats.py` の `graph/` 除外。
- `S/assets/SCHEMA.md.template`、`ontology.yaml.template`、`graph_README.md.template`、`graph_gitignore.template`。
- `W/eval/decisions/test_decisions.py` の `GraphLintTests`、`W/eval/scripts/test_frontmatter.py`、`test_help.py` の関連検査。

### 公式文書

2026年11月4日に参照しました。

- 依存の宣言・解決・ローカル導入・リリースタグ。[Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)
- プラグインのパス、環境変数、標準配置。[Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- フックの発火時点と実行方式。[Hooks reference](https://code.claude.com/docs/en/hooks)

使用した MCP サーバー: なし  
使用した Agent Skills: なし


## 相互レビュー

### エージェント C

D 案の主要な事実は、確認したコードと一致しています。特に、再生成中の DB と skills.sh 経由の利用まで扱った点は、自分の案より検討範囲が広いです。一方、共有コードを二つのプラグインへ同梱するときの版のずれと、MCP を追加する費用は、まだ設計・検証が必要です。
## エージェント D のレビュー

**「今は分割せず、wiki 内の境界を整理する」という結論を支持します。主要な事実はコードと一致しており、自分の案より、再生成中の障害とプラグイン以外の導入経路をよく扱っています。**

### 長所

- **文書上の任意性と、実装の動作を区別しています。** 初期化によるオントロジーの配置、必須セットアップへの PyYAML の混入、CLI ごとの欠落時動作を確認し、「別プラグインにすれば解決する」と短絡していません。
- **分割後に残る結び付きを具体的に示しています。** 手順への組み込み、Python の import、`${CLAUDE_PLUGIN_ROOT}` を別々に扱い、依存宣言だけではコード共有を解決できないと説明しています。
- **将来案と確認済みの事実を区別しています。** 横断グラフの需要や軽量化の効果を推測として扱い、測定していない性能を分割の根拠にしていません。
- **自分の案より検討範囲が広い部分があります。** 既存 DB を削除して再生成する実装から中断時の試験を挙げ、skills.sh や他エージェントでの利用も移行判断に含めています。共有コードを各プラグインへ同梱する案も、実行時に相手の配置先を探す問題を避けられる候補です。

### 短所

**1. 共有コードの同梱案には、保守元と版のずれへの対策が不足しています。**

ADR-0008 の同梱方針は、作業領域の設定を読む部分についての決定です。一方、移植計画の方針 B は、日本語別名の対応表を1か所に置く方針です。D 案の同梱を直ちに方針違反とは判断しませんが、次の区別が必要です。

- 一つの保守元から配布用コピーを作るのか。
- 二つのリポジトリで個別に編集するのか。
- wiki と graph が異なる版の対応表を持つ場合、許容するのか。

同じ版のコード同士の一致試験だけでは、独立更新後の不一致を防げません。保守元、取り込み元の版、対応する組み合わせを明示すべきです。〔[ADR-0008:192](C:/Works/info-hive-dev/docs/adr/0008-numbered-workspace-layout.md:192)、[移植計画:499](C:/Works/info-hive-dev/docs/porting-plan.html:499)〕

また、D2 は通信・設定だけでなく、質問定義と閾値にも依存します。`decision-questions.json` をどちらが所有・配布するかまで決めないと、判定クライアントだけを共有しても分割は完結しません。〔[wiki_graph_lint.py:460](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py:460)、[wiki_decide.py:59](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:59)〕

**2. MCP 案の追加費用と、索引更新の競合が未整理です。**

MCP は相手のスクリプト配置先に依存しない窓口として有効です。ただし、接続失敗、タイムアウト、ツールの互換性、CLI との同時実行を扱う責任が増えます。「薄い窓口」であっても、この部分は省けません。

D 案は中断時の試験を挙げていますが、現行実装は既存の `graph.sqlite` を削除してから作り直します。MCP からの問い合わせや複数の extract を許すなら、試験に加えて、更新の直列化や完成した DB への切り替え方式が必要になります。これは**コードから推測できる競合リスクであり、今回障害を再現したわけではありません。**〔[wiki_graph_extract.py:447](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:447)〕

したがって、将来の接続方式は、まず共通コアと CLI の契約を固め、MCP は必要性を確認して追加する順序が妥当です。

**3. skills.sh 対応は、新規機能の選択ではなく既存利用者の互換性として扱うべきです。**

D 案がこの導入経路を見つけた点は優れています。ただし、README は現在すでに `npx skills add` と他ランタイムへのコピーを案内しています。分割後の対応を未決にする場合も、「継続」「CLI 経由へ変更」「対応終了」のいずれかを明示し、リリースの移行条件に含める必要があります。〔[README.md:54](C:/Works/info-hive-dev/info-hive-wiki/README.md:54)、[README.md:78](C:/Works/info-hive-dev/info-hive-wiki/README.md:78)〕

MCP を唯一の接続経路にする案では、これらの利用者が自動的に同じ機能を使えるとは確認できません。

**4. `bin/` 案の環境制約を、比較材料に加える必要があります。**

D 案は環境確認の必要性を認めており、誤りではありません。ただし公式文書には、sandbox 内の PowerShell では PATH に載らないこと、トップレベルの `bin/` を持つプラグインは claude.ai・Cowork では導入されないことが明記されています。採用候補として挙げるなら、この制約も併記すると判断しやすくなります。[公式文書：Executables](https://code.claude.com/docs/en/plugins/components#executables)

以上は主に分割時の設計不足であり、**「現時点では分割しない」という結論を覆す短所ではありません。**

### 検証した事実

以下の `S` は `info-hive-wiki/skills/info-hive/` を指します。確認範囲では、D 案の主要な事実記述に食い違いはありませんでした。

| 主張 | 結果 | 確認箇所 |
|---|---|---|
| 初期化・upgrade はグラフ用ファイルを配置する | **一致**。upgrade の分岐より先に配置する | `S/scripts/init_wiki.py:47, 203–239, 254–263` |
| 必須セットアップに PyYAML がある | **一致**。固定依存、import、準備結果への掲載がある | `S/scripts/setup_wiki.py:4–19, 42–49` |
| オントロジー欠落時の CLI 動作が異なる | **一致**。extract は空定義で続行、lint はエラー、query は DB を確認する | `wiki_graph_extract.py:198–208, 606–624`、`wiki_graph_lint.py:487–497`、`wiki_graph_query.py:248–252` |
| graph lint は共通処理・判定処理に依存する | **一致**。extract、wiki_text、任意の wiki_decide と質問ファイルを使う | `S/scripts/wiki_graph_lint.py:55–60, 304–307, 460–465` |
| GraphLintTests は PyYAML がなければスキップする | **一致**。既存出力と D2 の試験がある | `info-hive-wiki/eval/decisions/test_decisions.py:352–375` |
| 通常の解析器は入れ子の graph を解析しないという試験がある | **一致**。`graph` の値が空リストになることを検査する | `info-hive-wiki/eval/scripts/test_frontmatter.py:50–52` |
| 共通コードの同梱と一致試験の前例がある | **一致**。対象は作業領域設定の読み取り処理 | `docs/adr/0008-numbered-workspace-layout.md:192` |
| 再生成前に既存 DB を削除する | **一致**。中断・同時実行への影響は未検証 | `S/scripts/wiki_graph_extract.py:447–451` |
| skills.sh・他ランタイム向け導入が存在する | **一致**。README に現在の導入手順がある | `info-hive-wiki/README.md:54–78` |
| 提案した MCP 接続が実際に動き、費用に見合う | **確かめられず**。新設案であり実装・測定がない | D 案自身も未検証と明記 |

## 自分の結論の見直し

**「今は分割せず、wiki 内を整理する」という結論は維持します。** 両案とも、現在の負担の多くは配布単位を増やさずに改善できることを、コードから説明できています。

一方、自分の案は次の点を修正します。

- **skills.sh と他ランタイムを、分割時の互換性確認に追加します。** 現行の案内があるため、単なる将来対応として扱いません。
- **再生成時の中断・同時実行を、索引更新の設計に追加します。** 自分の案は更新契機と形式の版に重点があり、公開途中の DB の扱いが不足していました。
- **共有処理を必ず公開 CLI/API にするという提案を弱めます。** 自分の「wiki 側で解決した絶対パスを渡す」案にも、発見・引き継ぎ・更新後の再解決という未検証の手順があります。D 案の保守元を一つにした配布時同梱も比較し、対応環境と保守費用から選ぶべきです。

D 案の MCP 窓口をそのまま採用する判断はしません。分割が必要になった時点で、CLI と MCP の実動作・費用を比較する位置付けに改めます。

## 順位と確信度

| 順位 | 案 | 評価 |
|---|---|---|
| **1 位** | **エージェント D** | 主結論と根拠が妥当で、既存の導入経路、共有コードの同梱、中断時の再生成まで扱っている |
| **2 位** | **自分の案** | 主結論と内部整理案は妥当だが、導入経路と DB 更新途中の扱いが不足し、公開 CLI の追加を早く選びすぎていた |

**順位の確信度は「中」です。** D 案のほうが判断材料は広いものの、両案とも静的な調査が中心で、分割後の接続や運用費用を実証していません。

ファイル変更、ビルド、テスト実行は行っていません。指定された他エージェントの成果保存先も読んでいません。

使用した MCP サーバー: なし  
使用した Agent Skills: なし

### エージェント D

## エージェント C のレビュー

**「現時点では wiki 内に残して境界を整理する」という結論を支持します。主要な事実認識はコードと一致しており、分割案には公開 CLI の起動経路と移行対象を補う必要があります。**

以下では `S` を `info-hive-wiki/skills/info-hive/` と略記します。

### 長所

1. **分割しても残る結び付きを具体的に捉えています。**  
   ページ形式への依存に加え、取り込み完了、検査、索引更新、問い合わせ時の鮮度確認を整理しています。別プラグイン化の費用を、ファイル移動以外の部分まで評価できています。

2. **「任意機能」という説明と実装の差を正確に指摘しています。**  
   初期化時のオントロジー配置、通常セットアップの PyYAML、オントロジー欠落時にも進む extract を確認しています。この問題を分割前に整理する提案は妥当です。

3. **分割案でも共有処理の所有者を明確にしています。**  
   日本語正規化と汎用判定処理を wiki に残し、公開 CLI から使う案には、実装の二重管理を抑える利点があります。私の共有コード同梱案より、修正箇所を集約しやすい方向です。

4. **性能や将来需要を事実として扱っていません。**  
   軽量化を未測定と明記し、GraphRAG や wiki 外の利用を再検討条件にしています。現在の結論と将来の選択肢が区別されています。

### 短所

#### 1. 公開 CLI の受け渡しが、すべての入口をカバーしていません

「wiki 側のスキルが解決した CLI の絶対パスを graph に渡す」という案は、wiki から graph を呼ぶ経路では成立し得ます。しかし、利用者が `/graph:lint` を直接起動する場合や、CLI を単独実行する場合に、誰が wiki 側のパスを解決するかが未定義です。

依存宣言は、依存先の導入や有効化を扱います。CLI のパスを引数として渡す契約は追加設計になります。初回起動、更新後、`--plugin-dir` による開発時を含めた入口の確認が必要です。[Plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies)、[Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference#environment-variables)

これは実装不能という指摘ではなく、**提示された接続案に残る未検証部分**です。

#### 2. 公開 CLI の費用と互換性契約が十分に示されていません

現在の D2 は、引用の一致判定、対象エッジの収集、並列判定、個別エラーの処理、`failed_open` などの集計を組み合わせています。JSON 化するなら、これらをどちらが担当するかを固定する必要があります。根拠は `S/scripts/wiki_graph_lint.py` 304–385行です。

また、グラフが共有している処理には、日本語別名変換以外にも NFC、相対パスの正規化、表示幅、argparse の日本語化があります。公開 CLI に載せる処理と graph 内に置く処理の整理も必要です。根拠は `wiki_graph_extract.py` 55行、`wiki_graph_lint.py` 60行、`wiki_graph_query.py` 39行です。

ページごとに子プロセスを起動する設計なら起動回数が増えるため、バッチ入力を含めて検討すべきです。性能への影響は未測定です。

#### 3. 既存利用者の移行範囲が Claude Code に寄っています

現行 README は、`npx skills add` による導入と、Codex・Cursor・OpenCode などでの利用を案内しています。C の移行案は `graph@info-hive` の追加を中心にしており、これらの利用者について次が未決です。

- graph スキルの配布・導入方法
- wiki スキルとの場所解決
- グラフを含む既存の `info-hive` スキルからの移行案内

分割で影響を受ける既存の導入経路として扱う必要があります。根拠は `info-hive-wiki/README.md` 7、57–78行です。

#### 4. PyYAML の切り離しは、準備完了の契約変更も伴います

C の提案する依存準備の分離は妥当ですが、変更範囲には次も含まれます。

- `setup_wiki.py` が返す `dependencies`
- セットアップ完了を判定する手順
- PyYAML の存在を期待する既存テスト
- init・upgrade の説明

実際に `info-hive-wiki/eval/retrieval/test_setup.py` 75行は、結果に `pyyaml` があることを検査しています。`S/references/retrieval-setup.md` 60–64行も依存一覧を完了条件にしています。

さらに、検索側の推移的依存として PyYAML が残るかは未確認です。確実に主張できる効果は、グラフ用の明示的な要求と検証責務を分けられることです。

### 検証した事実

| C の主張 | 結果 | 確認箇所・補足 |
|---|---|---|
| init と upgrade はグラフのテンプレートを配置する | **一致** | `S/scripts/init_wiki.py` 47、220–239、254–263行。upgrade の判定より前に共通の配置処理がある |
| 通常セットアップにも PyYAML が含まれる | **一致** | `S/scripts/setup_wiki.py` 4–19、42–48行 |
| extract はオントロジー欠落時に空の定義を使う | **一致** | `S/scripts/wiki_graph_extract.py` 198–208行 |
| query 自体には鮮度確認がない | **一致** | `S/scripts/wiki_graph_query.py` 239–252行。鮮度確認は `S/references/query-workflow.md` 40行にある |
| 型付き関係の追加だけを更新契機にすると不十分 | **一致** | `wiki_graph_extract.py` 360–414行は wikilink、`sources`、`raw` も入力にする。一方、`ingest-workflow.md` 138行には再生成を省く説明がある |
| グラフ lint は共通処理と D2 に依存する | **一致** | `wiki_graph_lint.py` 59–60、307、460–465行 |
| `GraphLintTests` は PyYAML 不在時にスキップする | **一致。ただし補足が必要** | `eval/decisions/test_decisions.py` 352–375行。CI は Linux・Windows とも PyYAML を明示導入しているため、通常の CI がこの理由で検査を省くという意味ではない |
| 抽出・問い合わせの専用試験群が不足している | **一致** | `info-hive-wiki/eval/` の関連ファイルと `GraphLintTests` を確認。既存の一部検査と、extract から問い合わせまでの回帰試験は区別できている |
| wiki の現在版は `0.2.0`、rag は wiki に依存する | **一致** | 両プラグインの `.claude-plugin/plugin.json` |
| パスを受け渡す公開 CLI 案が対象環境で動く | **確かめられず** | 新設案であり、実装・実動作の証拠はない。C 自身も新設が必要と明記している |

主要な現状認識に明確な食い違いは見つかりませんでした。上の短所は、主として構成案の不足と追加費用です。検証は静的な読解で行い、ファイル編集・ビルド・テスト実行はしていません。

## 自分の結論の見直し

**当面は wiki 内に残すという結論を維持し、将来分割するときの接続方式の優先順位を見直します。**

C と私の結論は、同じコード上の事実から導かれています。特に、初期化、有効化、更新条件を整理する必要性は、配布を分けるかどうかに先立ちます。

見直す点は二つあります。

- **MCP 窓口を分割案の既定候補にする判断を弱めます。**  
  私の案は、ツールの発見と構造化された呼び出しを説明しやすい一方、接続管理と新しい実行経路を追加します。まず公開 CLI で直接起動・パス解決・バッチ処理を満たせるかを確かめ、満たせない要件が具体化した段階で MCP を比較する順序が妥当です。

- **共有コードを双方へ同梱する案の保守費用を重く見ます。**  
  私の案では、一致試験を設けても複数のリリースに修正を配る必要が残ります。C の公開インターフェース案は、共有処理の実装を集約できる点で優れています。ただし、公開仕様の互換性管理は必要です。

直近の提案は、**有効化と準備完了の契約、索引更新の条件、回帰試験を wiki 内で整えること**です。将来の接続方式は、直接の `/graph:*` 起動と skills.sh 経由の利用を含む確認結果で選びます。

## 順位と確信度

| 順位 | 案 | 評価 |
|---|---|---|
| **1位** | **エージェント C** | 内部整理を優先する結論が妥当で、将来の共有処理を wiki に集約する方向を僅差で評価する。公開 CLI の入口と移行範囲の補完が必要 |
| **2位** | **自分の案** | CLI 間の挙動差、skills.sh、再生成中断まで扱う点は強い。一方、MCP の追加と共有コードの複数同梱を選ぶ根拠が不足していた |

**順位の確信度は中です。** 両案の当面の判断はほぼ一致しており、順位差は将来案の設計方針によります。公開 CLI と MCP の実装・運用費用を比較した結果はまだありません。

使用した MCP サーバー: なし  
使用した Agent Skills: なし


## 規則

- 票数ではなく根拠の質で優劣を付ける。複数が同じ結論でも、同じ資料を写しただけなら独立に同じ結論へ至ったとは言えない。
- レビューで確かめられた事実（一致、食い違い）を、レビュー前の主張より優先する。
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
（エージェント C、エージェント D の結論を 1 段落ずつ。レビューで受けた指摘のうち当たっていたものを添える）

## 残るリスクと未確定事項
- （作者の判断が要ること。選択肢と帰結）

## 記号とモデルの対応
| 記号 | モデル |
| --- | --- |
| C | GPT-6.1 Sol（`gpt-6.1-sol`） |
| D | GPT-6 Astra（`gpt-6-astra`） |
```
