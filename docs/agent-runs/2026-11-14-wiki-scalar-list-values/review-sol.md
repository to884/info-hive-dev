## 判定

**条件付きで採用可。確信度：中。** 致命的・重大な欠陥は確認できなかった。ただし、lint の診断を元の形で返す要件への違反、文書と実装の食い違い、判定処理の試験の抜けがある。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **比較用の正規化が診断値に影響しない。** 実際には、正規化した `type` を診断にも流用しており、元の配列が失われる。
- **`--decide` を付けた試験で、判定処理のソース認識も検証できる。** 証拠が本文の部分文字列なら判定候補から除かれる。今回の fixture はこの条件に当たり、候補数はゼロになる。

## 見落としと軽微な問題

1. **軽微：lint の診断に、書かれた形が残らない。**

   `target.md` を `type: [concept]` とし、entity の索引から参照するか、別ページの `sources: [target]` から参照する。

   修正前後の `lint()` を同じ入力で実行すると、`index_type_mismatch[].type` と `unresolved_sources[].type` が、どちらも `["concept"]` から `"concept"` に変わった。配列だったことを診断から判別できなくなる。

   根拠：`skills/info-hive/scripts/wiki_lint.py:485`、`:490`、`:509`、`:575`。`CHANGELOG.md:26` の「今までどおり書かれた形のまま出す」と食い違う。新試験の `eval/scripts/test_scalar_values.py:194` は `non_iso_dates` だけを確認しており、この変更を検出しない。

2. **軽微：グラフの空値は、記載された `null` にならない。**

   `type:`、`kind:`、`created:`、`updated:` を値なしで与えて `build_nodes()` を実行すると、ノードの `page_type`、`kind`、`created`、`updated` はすべて `""` になる。共通関数が返した `None` を、呼び出し側の `or ""` が置き換えている。

   根拠：`skills/info-hive/scripts/wiki_graph_extract.py:583`、`:585`、`:589`、`:590`。`CHANGELOG.md:23` の空値を `null` にする規則を、`:25` でグラフにも「同じ規則」として適用した説明とは一致しない。

3. **軽微：複数要素の type が「どの `--type` にも当たらない」という説明は誤り。**

   `type: [concept, entity]` に対して、`--type "concept, entity"` は一致する。実際に同条件の `passes_filters()` が `True` を返した。CLI の `--type` に選択肢の制限はない。

   根拠：`skills/info-hive/scripts/wiki_search.py:496`、`:1127`。`CHANGELOG.md:24` と食い違う。

4. **軽微：`--decide` の追加試験は、変更したソース認識処理の回帰を検出できない。**

   fixture の証拠 `"共通語の本文"` は、ソース本文 `"共通語の本文。…"` に含まれるため、`decide_evidence()` の候補に入らない。同条件の関数実行でも `candidates: 0`、`checked: 0` だった。さらに試験はバックエンドを `off` に固定し、通常の lint の検出項目だけを検査している。

   このため、`decide_evidence()` の source 判定を修正前の生の比較へ戻しても、今回の assertion では検出できない。

   根拠：`eval/scripts/test_scalar_values.py:90`、`:220`、`:226`、`skills/info-hive/scripts/wiki_graph_lint.py:356`、`:372`。

## 検証した事実

- 提示された差分と実際の `origin/main..HEAD` の対象ファイルは一致した。
- `ValueFunctionTest` の2試験は成功。全15 fixture の `type`・`updated` の正規化結果も、ファイルを作らず確認した。
- 数・真偽値・日付・入れ子を含む値を共通関数へ直接渡しても例外は発生せず、文字列または `None` になった。入れ子は文字列表現として結合された。
- MCP の `query` は `wiki_index.Index.search()` 経由で `passes_filters()` と `json_result()` を使う。確認した検索経路に、生の値による同種の取り違えは残っていなかった。
- **全試験・CLI の実行確認は未実施。** 読み取り専用環境であり、PyYAML も未導入だった。グラフの空値と判定候補数は、対象ソースから取り出した関数で確認した。

## 崩せなかった点

- 共通関数による文字列の保持。`""` と前後に空白を含む文字列も保持された。
- 通常の読み込み経路での日本語別名の処理。文字列は `canonical_meta()`、配列は追加された共通関数で英語になった。
- 確認した範囲で、今回の変更が新たに起こす例外や、検索・統計・グラフの主要処理を停止させる反例は見つからなかった。
