# SemaSynth wiki の Apache Ossie 書き出し PoC

2026-11-19 に SemaSynth の `C:/Works/semasynth-dev/wiki` で検証した。入力は info-hive-wiki 0.35.1（`8c451e6`）の `graph/graph.sqlite`。同じ 63 ページを現行の抽出器で一時領域に再生成し、入力と全行・全列が一致することを確かめた。検証した Ossie は `0.3.0.dev0`（`0f458de`）。 [前回の置換調査](2026-11-19-apache-ossie-wiki-graph-replacement.md) · [Apache Ossie の検証対象コミット](https://github.com/apache/ossie/commit/0f458dee0718b701930bf4597e1d84e427f0c8fc)

## 実データで保持できたもの

| 項目 | 結果 |
| --- | --- |
| ID と関係 | 63 ノード、477 エッジの元 ID と全列が SQLite の出力と一致。述語の内訳も一致し、`cites` 1 件、`depends_on` 1 件、`mentions` 336 件、`sourced_from` 92 件、`summarizes_raw` 47 件。 |
| 関係の参照先 | 主語 477 件、ノードを指す目的語 430 件を型付きで参照できた。原本への 47 件は `raw:…` の文字列 ID を保持した。 |
| 根拠と出典 | 出典 94 件を元の表記と型付き参照で保持した。うち引用付きの `cites` と `depends_on` は、引用・確信度・状態・記載ページ・`raw_ref` が一致した。両方の引用が入力 wiki の `raw_ref` の指定行に含まれることも確かめた。 |
| 状態と履歴 | 477 件が `current`。状態は保持できた。有効期間、注記、訂正・置換リンクを持つ関係は実データに 0 件だった。 |
| 別名 | 元のグラフに別名行は 0 件だった。Markdown のトップレベルに `aliases` を持つページは 2 件あり、その値は現行のグラフ SQLite に収録されていない。 |

合成 wiki を現行の抽出器で SQLite に変換し、同じ主語・述語・目的語を持つ 3 件を試した。個別の ID と根拠、`superseded`・`current`・`disputed`、有効期間、注記、原本行、エッジ同士の `supersedes` と `contradicts`、ソースのスラッグへの参照、`graph.aliases` を出力先で確認した。 [合成試験](../../tests/wiki/test_ossie_export.py)

## 出力の構造と検証範囲

既存ノードを `WikiNode`、個別の関係を `WikiEdge` の実体として定義し、元の `id` で識別する。述語は文字列属性、主語・目的語・出典や解決できた訂正・置換先は型付きリンクにする。解決不能・曖昧な参照は元の値と解決結果を収録する。日付は元の値を保てる文字列とし、元の `metadata_json` もそのまま収録する。原本と本文は入力側に置き、述語の型や根拠の要否は現行の `ontology.yaml` と lint で管理する。 [Ossie の識別](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#identifying-relationships) · [独立 Mapping](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#mapping-documents)

- 公式の `validate.py` で Ontology・Core・Mapping の 3 文書が通った。固定した変換器版のパーサーで Ontology を、Core SDK で Core を読み込めた。変換器のパーサーは独立 Mapping を拒否した。 [公式検証器](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/validation/validate.py) · [変換器のパーサー](https://github.com/apache/ossie-converters/blob/93fb75c47c294db811ba49e5832c0cb857704306/ontology/src/ossie_ontology/parser/__init__.py#L34)
- PoC は書き出した Core と Mapping の列参照を SQLite で評価し、`WikiNode` と `WikiEdge` の 6,532 個の属性・リンクが期待値と一致することを確認した。列参照を超える Ossie 式・制約・導出の評価と、外部エンジンへの通しの取り込みは未検証。
- レビューで、旧い関係の状態を後から変更し、変更前の ID を参照した場合にリンク先が見つからないことを再現した。出力には元の ID を残し、`verification.json` で `unresolved` として報告する。明示関係の `source` は現行 lint の契約どおりソースのスラッグで照合する。トップレベルの `sources` にあるパスや wikilink は、現行抽出器が解決した `sourced_from` の目的語を使う。 [現行の lint](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py#L276) · [回帰試験](../../tests/wiki/test_ossie_export.py)

## 現行グラフを修正する必要はあるか

**現在のグラフにある値を一方向で書き出すには、修正は不要。** 入力を SQLite の読み取りトランザクションで取得するので、現行の抽出・lint・query・browse に変更を加えず実行できる。

- トップレベルの `aliases` も対象に広げるなら、現行の抽出器でそれらをグラフに載せるか、出口で Markdown から補う必要がある。現行のグラフ別名欄は `graph.aliases` を使う。 [現行のノード抽出](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L583)
- 自動的な変更履歴や編集前後で不変の関係 ID が必要なら、別途保存方法を決める必要がある。現行のエッジ ID は根拠・状態・有効期間などから生成されるため、それらを編集すると ID が変わり得る。PoC はスナップショットに現存する版と参照を保持する。 [現行のエッジ ID](../../info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py#L617)

## 実行と成果物

Python 3.9 以降の標準ライブラリで書き出せる。親リポジトリのルートから、入力 wiki の外にある新規ディレクトリを指定する。

```powershell
python -B -X utf8 poc/ossie/export_wiki_graph.py --wiki C:/Works/semasynth-dev/wiki --output poc/ossie/runs/semasynth-rerun
uv run --with pyyaml==6.0.3 python -B -X utf8 -m unittest discover -s tests/wiki -p test_ossie_export.py -v
```

実データの出力は `poc/ossie/runs/semasynth` に置いた。出力ディレクトリは Git の除外対象にした。 [実装](../../poc/ossie/export_wiki_graph.py)

| ファイル | 用途 |
| --- | --- |
| `wiki.ontology.json` | `WikiNode` と `WikiEdge` の型、識別子、リンク |
| `wiki.semantic_model.json` | SQLite 3 表のデータセット、列、結合 |
| `wiki.mapping.json` | データセットから実体とリンクへの対応 |
| `wiki-data.sqlite` | 元の値と追加した参照列 |
| `verification.json` | 照合結果と件数 |

公式の文書検証も行う場合は、上記コミットの Ossie チェックアウトを `--ossie-checkout` に指定する。PoC が `uv` で公式の検証器を実行し、結果を `verification.json` の `official_validation` に記録する。

```powershell
python -B -X utf8 poc/ossie/export_wiki_graph.py --wiki C:/Works/semasynth-dev/wiki --output poc/ossie/runs/semasynth-validated --ossie-checkout C:/path/to/ossie
```
