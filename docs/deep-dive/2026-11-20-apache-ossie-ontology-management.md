# Apache Ossie を info-hive のオントロジー管理に使えるか

2026年11月20日に公式ドキュメント、リポジトリ、info-hive の既存試験を照合した。**Ossie は、型・関係・識別規則や集計定義を外部と交換する形式として使える。将来は意味定義の記述にも使えるが、現段階では本番 wiki の正本を切り替える根拠は揃っていない。** 出典付きの主張、名寄せ、承認を伴う再編・移行と公開は info-hive が担う。 [既存の設計案](../plans/wiki-ontology-ossie-design-2026-11-19.md)

## すでに行った検討

- 11月19日に比較調査、設計、段階1〜3の PoC、隔離環境での公開前試験を実施した。現行 `ontology.yaml` を Ossie の公式例に直接差し替えた試験では、認識される型と述語が 12・15 から 0・0 になり、既存 ID と型付き経路を解決できなかった。変換を挟む一方向の書き出しでは、SemaSynth の63ノード・477エッジを全列一致で保持した。 [置換調査](../research/2026-11-19-apache-ossie-wiki-graph-replacement.md) · [書き出し PoC](../research/2026-11-19-ossie-wiki-export-poc.md)
- 段階1・2では、実体、主張、根拠を別々に記録し、定義の改名・分割、履歴、保留を合成データで試した。段階3では info-hive の DuckDB アダプターで独立 Mapping を実行し、型付きリンク1,662件、期間別の顧客照会11件、重複しない集計、制約違反5箇所を SQLite の期待値と照合した。一般の式、多項関係全般、任意の結合経路、`derived_by` の実行は対象外だった。 [段階1・2](../research/2026-11-19-ossie-wiki-stages-1-2.md) · [段階3](../research/2026-11-19-ossie-wiki-stage-3.md)
- wiki v0.39.0 では、隔離環境で試した公開版の適用・復旧・切り戻しをリリースした。今回の `wiki_apply.py view` で、このプロジェクトの wiki は `release_id: null` のライブ状態だった。既存の受け入れ試験には版を固定した検索・引用・browse が含まれる。通常の ingest から意味上の主張と履歴を確定する機能と、本番の既定としての有効化は別の判断になる。 [公開前試験](../research/2026-11-19-ossie-wiki-publication-acceptance.md) · [ADR-0036](../adr/0036-wiki-published-release-journal-and-reader-pinning.md) · [v0.39.0](https://github.com/to884/info-hive-wiki/releases/tag/v0.39.0)

## 公式仕様と公開ツール

Apache Ossie は旧 Open Semantic Interchange（OSI）で、分析・AI・BI のツール間でセマンティックモデルを共有する Apache Incubator プロジェクトである。2026年11月20日に公式配布ページを確認した時点で Apache 版の正式配布はない。確認した `main` は本体 `344259a`、変換器 `92e6c57`。Core と Ontology の仕様は `0.3.0.dev0` である。 [公式サイト](https://ossie.apache.org/) · [配布ページ](https://ossie.apache.org/downloads/) · [本体コミット](https://github.com/apache/ossie/commit/344259a82b47bd48cb20043899f092e98fc327e4) · [変換器コミット](https://github.com/apache/ossie-converters/commit/92e6c5782400bb031444004430f7c8226f1bc1ba)

| 項目 | 仕様・実装で確認できた範囲 |
| --- | --- |
| Core | 表、列、結合、ディメンション、指標の定義を YAML / JSON で交換する。Layer 2・3 は集計と、指標・軸から結合を選ぶ問い合わせの意味を定める。 [仕様の構成](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/core-spec/spec_layers.md) |
| Ontology | 実体型・値型、継承、複合識別子、役割付きの多項関係、多重度を宣言できる。例えば「顧客・製品・契約」の三者の役割を保持できる。`requires` は制約、`derived_by` は導出を記述する。 [Ontology 仕様](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/ontology/ontology.md) |
| Mapping | Core の項目を実体と関係に対応付ける。公式検証器は独立文書とその参照を検査する。仕様は独立文書を推奨しているが、公式の変換器パーサーは対応していない。 [独立 Mapping](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/ontology/ontology.md#mapping-documents) |
| SDK・実行 | Python SDK は Core の文書を扱う。別リポジトリの変換器には Ontology のパーサーと PyRel 出力がある。PyRel の実行先は Snowflake 上の RelationalAI で、確認した変換コードは `derived_by` を扱う。既存の根拠つきグラフ探索に当たる API は確認できず、Ontology Access Layer は提案段階である。 [Core SDK](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/python/README.md) · [PyRel 変換器](https://github.com/apache/ossie-converters/blob/92e6c5782400bb031444004430f7c8226f1bc1ba/relationalai/README.md) · [Ontology Access Layer の提案](https://github.com/apache/ossie/issues/107) |

## 上流の変更と再確認

前回固定した本体 `0f458de` から、オントロジー全体・概念・関係定義・役割に自由形式の `annotations` を付けられるようになった。これは定義を説明する欄であり、関係の個々の記録に出典、引用、有効期間、訂正履歴を結ぶ契約は引き続き info-hive 側で定める。 [注記の仕様](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/ontology/ontology.md#annotations) · [前回検証版からの差分](https://github.com/apache/ossie/compare/0f458de...344259a)

| 再確認したもの | 結果 |
| --- | --- |
| info-hive PoC の既存出力 | 本体 `344259a` の公式検証器を直接実行し、SemaSynth と合成データの7バンドル、Ontology・Core・Mapping 各7件の計21文書を受理。存在しない列を指定した負例は拒否。 |
| 公式サンプルを読む経路 | 公式検証器は注記付き FOAF の Ontology と Flights の独立 Mapping を受理。Flights の Mapping では解析できない2式の列参照検査を省略した。変換器 `92e6c57` の `OssieParser` は Flights の単体 Ontology を受理し、独立 Mapping と注記付き FOAF を追加フィールドエラーで拒否。構文を崩した `requires` は公式検証器を通過し、`OssieParser` が拒否した。 |
| ローカル回帰 | 既存の書き出し、意味モデル・移行、DuckDB アダプターの16テストがすべて通過。 |

テストは `uv run --offline --with duckdb==1.4.4 --with pyyaml==6.0.3 python -B -X utf8 -m unittest tests/wiki/test_ossie_export.py tests/wiki/test_ossie_semantic_trial.py tests/wiki/test_ossie_consumer.py -v` で実行した。段階3の実行スクリプトは前回コミットを要求するため、新しい仕様の検査は公式 CLI を直接使用した。変換器での試験は文書の読み込みまでで、外部エンジンでの実行は今回の対象外である。 [公式検証器](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/validation/validate.py) · [公式 FOAF 例](https://github.com/apache/ossie/blob/344259a82b47bd48cb20043899f092e98fc327e4/examples/foaf_owl_import.yaml) · [変換器の入力モデル](https://github.com/apache/ossie-converters/blob/92e6c5782400bb031444004430f7c8226f1bc1ba/ontology/src/ossie_ontology/spec.py)

## 採用できる範囲

- **外部交換には使える。** 既存の Markdown・SQLite グラフから Ontology・Core・Mapping を生成する一方向の方式は検証済み。利用先ごとに対応する仕様、変換器、実行器のコミットを固定し、文書が読めることと、結果が一致することを別に検査する。
- **意味定義の正本にする場合は、互換性を設計する。** 顧客や製品を記事から独立して識別する規則と関係の役割は Ossie に書ける。旧 ID と述語の対応、複数の根拠を区別する主張 ID、既存の `neighbors`・`facts`・`path` と browse への互換グラフは info-hive に持たせる。
- **見直し・移行と本番運用は info-hive の仕事になる。** ユーザーの指示で提案する改名・分割、旧版の解釈、判定できない主張の保留、承認と公開を info-hive で実装する。通常 ingest から意味レコードを確定する製品経路と、復旧・保持・運用負荷を評価する本番条件が残る。 [既存の設計案](../plans/wiki-ontology-ossie-design-2026-11-19.md) · [本番有効化の記録](../research/2026-11-19-wiki-production-storage-validation.md)
