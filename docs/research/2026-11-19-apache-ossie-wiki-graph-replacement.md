# info-hive-wiki のオントロジーとグラフを Apache Ossie に置き換えられるか

調査日 2026-11-19。現行は info-hive-wiki 0.35.1（`8c451e6d`）。Ossie は同日確認した `main` の `0f458de`、Core `0.3.0.dev0` を基準にした。変換器は `93fb75c`。Ossie の公式ダウンロードには、Apache Incubator 移行後の配布版がまだない。Core の履歴には移行前の `0.1.1` がある。 [プラグイン定義](../../info-hive-wiki/.codex-plugin/plugin.json) · [Ossie の確認改訂](https://github.com/apache/ossie/commit/0f458dee0718b701930bf4597e1d84e427f0c8fc) · [Core の版履歴](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/spec.md#version-history) · [公式配布ページ](https://ossie.apache.org/downloads/)

## 結論

**Ossie の定義ファイルや公開ツールですぐに置き換えることはできない。** 型定義を Ossie に寄せる方式は、既存のページ対応や証拠の規則を引き継ぐ変換層を作れば可能。グラフの実行部まで移す場合は、既存の問い合わせ、出典の照合、閲覧画面への接続も実装する必要がある。増える価値は、複合識別子、多項関係、制約・導出の宣言と、外部ツールと共有できる集計の定義にある。最初に試すなら、現行のグラフから Ossie を生成する一方向の出力が妥当。

## 現行で使える機能と置換の影響

| 機能 | 現行の動作 | Ossie に移す条件 |
| --- | --- | --- |
| ページからの抽出と ID | Markdown の `type`・`kind`・`graph` からノードと型付きエッジを作る。本文リンク、`sources`、`raw` から `mentions`、`sourced_from`、`summarizes_raw` も生成する。日本語の ID・参照は NFC に正規化する。 | ページと実体・型の対応、既存 ID、別名、曖昧な参照の扱いを変換で保持する。Ossie の IRI は概念・関係の定義を外部語彙へ結ぶ。個別実体の識別には `identify_by` など、対応する識別規則が要る。 [現行の抽出](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L502) · [Ossie の識別](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#identifying-relationships) · [IRI](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#global-identifiers) |
| 出典・証拠と履歴 | 同じ主語・述語・目的語でも、記述元ページ、出典、引用、確信度、状態、有効期間、原本参照、訂正・置換の参照を区別して保持する。lint が型、根拠の要否、参照の曖昧さなどを調べ、通常の query が出典本文を確認する。 | Ossie のリンクは集合として扱う。同じ二項タプルに縮めると、どの主張にどの根拠が付くかを復元できない。主張と根拠を別の実体やデータとして表し、旧エッジ ID と `contradicts`・`supersedes` の参照も保持する。 [現行エッジの識別](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L617) · [グラフ lint](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py#L232) · [通常の query](../../info-hive-wiki/commands/query.md#L16) · [Ossie の関係](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#relationships) |
| グラフ問い合わせ | CLI と MCP が `neighbors`、`edges`、`facts`、有向最短経路の `path` を提供する。`path` の既定上限は6ホップ。状態や有効期間は記録されるが、時点指定は公開 API にない。 | 同じ応答形式と探索を実装する必要がある。Ossie Layer 3 は集計データセット間の結合を選び、必要な結合に複数の経路があればエラーを返す。Layer 4 は再帰的な導出の書き方を示す。証拠つきのエッジ列を返す最短経路の契約は、今回確認した Ossie 仕様・実装の範囲では見つからなかった。 [現行の問い合わせ](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_query.py#L119) · [Layer 3 の結合パス](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/wide_table_semantics.md#4-paths) · [Ontology Access Layer の提案 #107](https://github.com/apache/ossie/issues/107) |
| 閲覧・再生成 | `browse` のページ別関係表は、Markdown のスナップショットに抽出関数を適用する。別途 JSONL・SQLite・GraphML を生成する。取り込み手順もグラフの lint と再生成に接続している。 | SQLite の差し替えだけでは閲覧側に反映されない。抽出と閲覧が共用する対応付け、入出関係の表示、生成物の互換性も必要になる。 [browse の実装](../../info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py#L1285) · [出力の実装](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L888) · [取り込み手順](../../info-hive-wiki/commands/ingest.md#L21) |

本文のハイブリッド検索には専用の索引がある。グラフを置き換える際に影響するのは、主に関係を問う回答の裏づけや、関連ページへの案内である。 [wiki MCP の検索とグラフ](../../info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py#L295) · [検索とグラフの使い分け](../../info-hive-wiki/skills/info-hive/references/graph-workflow.md#L145)

## 差し替えの実測

SemaSynth の同じ Markdown 63ページを現行の抽出器と lint に渡し、オントロジーだけを変更した。差し替えに使ったのは前日に取り込んだ Ossie の公式 Flights オントロジー（`4d82209`）。問い合わせは試験用の SQLite で実行した。 [Flights オントロジー](https://github.com/apache/ossie/blob/4d82209682b5b5095026897e6c7bab03bc3c5c58/examples/flights.ontology.yaml) · [現行パーサー](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L443)

| 確認項目 | 現行の定義 | Flights 定義を直接入力 |
| --- | --- | --- |
| 認識した型／述語 | 12／15 | 0／0 |
| ノード／エッジ件数 | 63／477 | 63／477 |
| lint が検出した未知の述語 | 0件 | 2件 |
| `neighbors(product:apache-ossie)` | Apache Ossie の隣接ノードを取得 | ノードが見つからない |
| 変換器から Apache Ossie への `path` | `depends_on` が1辺、出典つき | 旧 ID への型付き経路を解決できず、新しい `concept:` ID 同士では `mentions` が返る |

現行パーサーは Flights YAML を読み取ったうえで、`node_types` と `predicates` を空の辞書として補った。ファイルを読めることも、ノードやエッジの件数が一致することも、互換性の判定には使えない。逆方向も調べた。`0f458de` の Ossie JSON Schema は公式 Flights の文書を受理し、info-hive-wiki の `node_types`・`predicates` を持つ現行 YAML を拒否した。Ossie の関係定義に `source`・`evidence`・`confidence`・`status`・`valid_from`・`raw_ref`・`supersedes` を加える試験も拒否された。`Claim` と `Evidence` を明示的な型として分けた試料は構造検査を通った。 [Ossie の JSON Schema](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.json) · [現行のノード ID の規則](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L546)

## 増やせる機能と、公開実装で確認した範囲

- **実体の識別と関係の表現。** Layer 4 はエンティティ型と値型、継承、複合識別子、役割付きの多項関係、`ManyToOne`・`OneToOne` を宣言できる。たとえば「顧客・製品・契約」の組を保ったまま、どの契約で利用しているかを表せる。既存の二項エッジで表示する際は、各役割の組を保持したうえで、表示に使う関係を定義する必要がある。 [Layer 4 の関係](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#relationships)
- **制約と導出。** `requires` で満たす条件、`derived_by` で導く関係を記述できる。実測では、壊した `requires` 式を公式 `validate.py` が受理し、変換器の `OssieParser` が構文エラーとして拒否した。ルールを実データに適用するには評価器が要る。公式 PyRel 変換は解析済みの `derived_by` を変換する。確認した式の変換処理は `requires` を変換せず、生成物の実行は Snowflake 上の RelationalAI が担う。 [Layer 4 の条件と導出](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md) · [オントロジーパーサー](https://github.com/apache/ossie-converters/blob/93fb75c47c294db811ba49e5832c0cb857704306/ontology/README.md) · [PyRel の生成と実行](https://github.com/apache/ossie-converters/blob/93fb75c47c294db811ba49e5832c0cb857704306/relationalai/README.md) · [式変換](https://github.com/apache/ossie-converters/blob/93fb75c47c294db811ba49e5832c0cb857704306/relationalai/src/ossie_relationalai/converter.py#L544-L570)
- **独立マッピングの検査。** 公式バリデーターは `0f458de` の Flights の Core・Ontology・独立 Mapping を検証できた。Mapping の式2箇所では解析できず列参照の検査を省略した。宣言されていない列を入れた別試験ではエラーになった。この時点の Core Python SDK は Core 文書を読める。変換器の `OssieParser` は単体オントロジーと埋め込みマッピングを読めたが、独立 Mapping は拒否した。 [バリデーターの実装](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/validation/validate.py#L2340) · [Core SDK](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/python/src/ossie/models.py#L393) · [変換器のパーサー](https://github.com/apache/ossie-converters/blob/93fb75c47c294db811ba49e5832c0cb857704306/ontology/src/ossie_ontology/parser/__init__.py#L34)
- **集計と外部交換。** Core は表・列・結合・指標の定義を交換する。Layer 2 は各グループで同じメジャーの元行を高々1回評価し、Layer 3 は指定した指標と分類軸から結合を選ぶ。「利用顧客数」と「根拠文書数」を別に定義して、外部でも同じ集計を検証できる。どの行を顧客、主張、根拠として数えるかは info-hive 側で決める。公式の適合性試験は期待挙動を示す。独立 DuckDB 拡張にはクエリ実行機能があるが、確認した版は表のみ、単一の集計粒度、`INNER JOIN` などの対応範囲に限られる。 [Core の定義](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/spec.md) · [Layer 2 の集計](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/relational_semantics.md#8-measure-evaluation-and-guarantees) · [公式の適合性試験](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/compliance/README.md) · [DuckDB 拡張の制限](https://github.com/iqea-ai/duckdb-ossie/blob/90716de41de268a0f21150f3712608da69edf2fa/docs/limitations.md)

## 採用方式の判断

| 方式 | 判断 |
| --- | --- |
| 定義ファイルを直接差し替える | 既存 ID、型付きの経路、述語の検査に回帰が出る。実測で確認した。 |
| 型・関係の定義を Ossie に移す | 対応表を作れば実装可能。Ossie の型ごとに修飾された関係名を既存述語へ対応付け、`maps_from` や証拠の要否を互換規則として持つ。実データの検査や導出は、別途選んだ評価器につなぐ。 |
| 実行部まで移す | 新しい実行基盤と互換 API を作る開発になる。Markdown の抽出、出典へのリンク、`path`、`browse` の表示、生成物まで回帰試験を通す必要がある。 |
| 一方向の Ossie 出力を追加する | 既存機能を保ちながら効果を測りやすい。Markdown と現行のグラフ定義から Ossie Ontology を生成し、集計や実データの連携が必要な場合に Core・Mapping と対象データを加える。出力先が対応する型・式・項目を固定して試験する。 |

実際に導入を判断できる試験は、同一実体を別名で記した記事、同じ主張を支える複数の根拠、時期や状態の異なる主張、訂正と置換の参照を含む少数のデータで行う。既存 ID、4つの問い合わせ、最短経路の述語と引用、browse の入出関係を結果単位で照合する。Ossie 側では多項関係、識別制約、指標の値が受け手で一致するかを確認する。今の調査で確認したのは直接差し替え時の回帰、文書の検証、公開ツールの読み込み範囲まで。互換変換の往復、ルールの実データ評価、実行基盤を移したときの性能は未検証。

## 調査資料

- info-hive-wiki の [グラフワークフロー](../../info-hive-wiki/skills/info-hive/references/graph-workflow.md)、親 wiki の [[グラフの抽出の契約]]、[[エッジの識別子]]、[[グラフのlintの期待値]]。
- SemaSynth wiki の [[apache-ossie-ontology-json-schema-4d82209]]、[[apache-ossie-flights-mapping-4d82209]]、[[duckdb-ossie-community-extension]]。
- Apache Ossie の [レイヤー構成](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/spec_layers.md#the-layers)、[独立マッピング](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#mapping-documents)、[式の評価に関する議論](https://github.com/apache/ossie/issues/361)。
