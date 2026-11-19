# Apache Ossie 一方向 PoC の段階3

[設計案](../plans/wiki-ontology-ossie-design-2026-11-19.md) の段階3を、[段階1・2の出力](2026-11-19-ossie-wiki-stages-1-2.md) に対して試した。SemaSynth の既存グラフと意味モデル、合成 wiki の v1・改名後・v2・v3・別 wiki の7バンドルを入力にした。

## 公式の文書検証

Apache Ossie `0.3.0.dev0`（`0f458de`）の公式検証器で、元の Ontology・Core・Mapping 21文書と、段階3で追加した制約の例および顧客指標の Core を検証した。存在しない列を指定した独立 Mapping は拒否された。制約に違反するデータを入れたバンドルも、文書が同一なので公式検証は通った。 [公式検証器](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/validation/validate.py) · [独立 Mapping の仕様](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#mapping-documents)

## データを読み込んで実行した結果

DuckDB 1.4.4 をメモリ内で動かし、外部アクセスを無効にした。アダプターは独立 Mapping の参照から Ontology・Core を解決し、それらに従って SQLite の元列から実体と型付きリンクを構築する。顧客照会はこの実行結果を使う。顧客数・主張数・根拠数は、根拠結合後の行に対し、段階3の Core に宣言した指標を適用する。比較には段階1・2の SQLite の計算と固定済みの期待結果を使った。

| 検証 | 結果 |
| --- | --- |
| 型付きリンク | SemaSynth は既存グラフ1,001件・意味モデル83件。合成の5バンドルを含めた1,662件の主語・関係・型・参照先が SQLite と一致。SQLite 側は元列と外部キーの宣言を直接読んだ。 |
| 期間別の顧客一覧 | 11件の照会で顧客 ID・各件数・保留理由が一致。製品Aは開始日に1社、開始前と終了日に0社。代理販売のみの製品Bは0社、v2 では反証参照の保留を表示し、v3 でその留保が解消した。 |
| 根拠結合後の重複防止 | 製品Aは根拠結合後に2行。Core の `COUNT(DISTINCT ...)` を評価して顧客1社・主張1件・根拠2件を得た。同じ入力で顧客の指標を `COUNT(...)` に変更すると2になり、指標宣言の違いが実行結果に反映されることも確かめた。 |
| 制約違反 | `requires` の必須リンク欠落、型付き参照先の不在、Core の参照先の不在、`OneToOne` の重複を検出。SQLite で独立に求めた違反箇所5件と一致した。 |

対応範囲はこの PoC が使う列参照、単一の文字列 ID、2項の型付きリンク、`ManyToOne`・`OneToOne`、単一の関係の存在を要求する `requires`、単一データセットの `COUNT`・`COUNT(DISTINCT ...)`。Core の結合先はこの出力が宣言する主キーへの等値参照に限る。期間や保留の判定は info-hive の照会規則を DuckDB SQL で実行する。顧客照会の定義は合成 wiki の述語名の列挙（配列、または値が `null` のオブジェクト）に限る。一般の Ossie 式、任意の結合経路の推定、`derived_by`、本番の公開と並行取り込みは今回の実行範囲外である。 [Core の指標の仕様](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/core-spec/spec.md#metrics) · [Ontology の条件](https://github.com/apache/ossie/blob/0f458dee0718b701930bf4597e1d84e427f0c8fc/ontology/ontology.md#requires)

レビューで、元の合成 wiki だけでは定義の非互換や型違反の退行を検出できないことが分かった。別の合成試験に、候補と確定した反証、旧定義からの移行保留、背景資料と支持根拠の区別を加え、SQLite と固定した期待値の両方で照合した。主キー・対象型・参照先・多重度を崩した入力も追加した。

## 再実行

SemaSynth の出力には元の wiki に由来するデータが含まれるため、ここでは集計値を記録する。公開リポジトリから再現できるのは合成バンドルの結果であり、実データとの照合には元の出力にアクセスできる環境が要る。

リポジトリのルートで、依存がローカルにある状態で実行する。API キーと外部 DB は不要。公式検証を再実行する場合は、上の改訂のチェックアウトを指定する。`UV_OFFLINE` は公式検証器を呼ぶ子プロセスにもオフライン指定を伝える。

```powershell
$env:UV_OFFLINE = '1'
uv run --offline --with duckdb==1.4.4 python -B -X utf8 poc/ossie/consume_ossie.py --semasynth poc/ossie/runs/stages12-semasynth --synthetic poc/ossie/runs/stages12-synthetic --output poc/ossie/runs/stage3-rerun --ossie-checkout C:/path/to/ossie
uv run --offline --with duckdb==1.4.4 python -B -X utf8 -m unittest tests/wiki/test_ossie_consumer.py -v
```

今回の出力は `poc/ossie/runs/stage3/` にある。`verification.json` の `official_validation` と `execution` に結果を分け、指標文書と制約の正例・負例を同じフォルダーに保存した。 [実行スクリプト](../../poc/ossie/consume_ossie.py) · [ローカルアダプター](../../poc/ossie/ossie_adapter.py) · [回帰テスト](../../tests/wiki/test_ossie_consumer.py)
