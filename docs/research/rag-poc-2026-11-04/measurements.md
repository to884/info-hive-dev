# 検索の実測比較

同じコーパス SHA と質問数の行だけを直接比較する。

| 入力 | 埋め込み | リランカー | 件数 | Python peak GiB | LanceDB p95 ms | Qdrant p95 ms | Recall@30 | nDCG@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [47 問 / 542 チャンク](benchmark-30m-int8-tiny.json) | Ruri 30m | japanese-reranker-tiny-v2 int8 | 30 | 1.16 | 1039.6 | 983.4 | 1.0000 | 0.8154 |
| [47 問 / 542 チャンク](benchmark-30m-int8.json) | Ruri 30m | japanese-reranker-xsmall-v2 int8 | 30 | 1.20 | 2794.9 | 2655.4 | 1.0000 | 0.9071 |
| [47 問 / 542 チャンク](benchmark-30m.json) | Ruri 30m | japanese-reranker-xsmall-v2 fp32 | 30 | 1.25 | 3690.7 | 3296.3 | 1.0000 | 0.9315 |
| [107 問 / 602 チャンク](benchmark-v2-130m-int8-tiny-r20.json) | Ruri 130m | japanese-reranker-tiny-v2 int8 | 20 | 2.45 | 677.3 | 675.5 | 0.9813 | 0.8068 |
| [107 問 / 602 チャンク](benchmark-v2-30m-int8-r8.json) | Ruri 30m | japanese-reranker-xsmall-v2 int8 | 8 | 1.21 | 749.2 | 743.9 | 0.9439 | 0.8460 |
| [107 問 / 602 チャンク](benchmark-v2-30m-int8-tiny-r20.json) | Ruri 30m | japanese-reranker-tiny-v2 int8 | 20 | 1.33 | 673.4 | 665.4 | 0.9439 | 0.7680 |
| [107 問 / 602 チャンク](benchmark-v2-70m-int8-tiny-r20.json) | Ruri 70m | japanese-reranker-tiny-v2 int8 | 20 | 1.97 | 522.9 | 525.2 | 0.9626 | 0.8165 |

Recall と nDCG はこの表では LanceDB の値。Qdrant の個別値は各 JSON を参照。

## 同じ 107 問の埋め込み速度

| モデル | チャンク数 | 秒 | チャンク / 秒 |
| --- | --- | --- | --- |
| 130m | 602 | 448.63 | 1.34 |
| 30m | 602 | 80.55 | 7.47 |
| 70m | 602 | 157.48 | 3.82 |
