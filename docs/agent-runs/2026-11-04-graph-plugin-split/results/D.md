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
