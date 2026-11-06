# 埋め込みモデルとベクター DB の統一: 計測の記録

wiki と rag の埋め込みモデルとベクター DB を統一するために、モデル × DB の組を計測した記録である。結論と考察は、同じ階層にある HTML のレポート（`../embedding-backend-unification-2026-11-05.html`）に書く。この README には、再現の手順、計画との違い、計測の条件を残す。

## ファイル

| ファイル | 内容 | 作るスクリプト |
| --- | --- | --- |
| `candidates.json` | M0。候補ごとに 10,000 件の投入と検索を確かめた結果と、除外した候補の理由 | `check_candidates.py` |
| `onnx-feasibility.json` | M3。Ruri v3 の ONNX 書き出しの可否と、torch との一致 | `export_ruri_onnx.py` |
| `model-accuracy.json` | M2。8,275 チャンク・119 問での、モデルごとの再現率@30 と nDCG@10 | `model_accuracy.py` |
| `runtime-parity.json` | 製品の CPU 実行系（fastembed、ONNX、torch）と GPU の埋め込みの一致、クエリの p95 | `runtime_parity.py` |
| `lexical-bench-<dataset>.json` | 語彙検索のエンジン（SQLite FTS5 と Tantivy）の比較 | `lexical_bench.py` |
| `db-bench-subset.json` | M1 段階 1。100,682 チャンクで、全組のつまみを掃引した結果 | `db_bench.py` |
| `db-bench-full.json` | M1 段階 2。全量 761,915 チャンクで、上位と現行の組を測った結果 | `db_bench.py` |
| `scores.json` | 3 つのスコアと採用の判定 | `summarize.py` |
| `wiki-scale.json` | M5。wiki 規模での起動費用、ウォーム検索、2 プロセスの同時アクセス | `wiki_scale.py` |
| `install-results.json` | M4（副次）。空の uv キャッシュからの準備時間と容量 | `measure_install.py` |

スクリプトはすべて `poc/rag/unification/` にある。

## 再現の手順

作業データは `.rag-poc-data/unification-20261105/`（gitignore 済み）に置く。全量のデータは `.rag-poc-data/full-20261104/`、評価セットは `.rag-poc-data/natural-20261104/` を使う（どちらも 2026-11-04 の PoC で作ったもの）。

1. 計測用の venv を `.rag-poc-data/unification-20261105/venv` に作り、`candidates.json` の `packages` にある版を入れる（Python 3.12）。Ruri の ONNX 書き出しには `onnx==1.19.1` も入れる。Qdrant は公式の Windows バイナリ 1.20.0 を `.rag-poc-data/unification-20261105/qdrant/` に置く。
2. `poc/rag/unification/` で、次の順に実行する。GPU の埋め込みには `info-hive-rag/.rag-gpu-venv`（sentence-transformers + CUDA の torch）を使う。

```bash
python check_candidates.py
python export_ruri_onnx.py
# GPU の venv で、モデルごとに natural・parity・subset・full を埋め込む
python embed_models.py --model R-30 --dataset natural
python model_accuracy.py
python runtime_parity.py
python lexical_bench.py --dataset subset
python db_bench.py --model R-130 --dataset subset
python db_bench.py --model R-130 --dataset subset --lexical tantivy
python lexical_bench.py --dataset full
python db_bench.py --model R-130 --dataset full --lexical tantivy --candidates "FAISS IVF_SQ8" "usearch HNSW f16" "sqlite-vec f32"
python rescore_rankings.py --dataset subset   # 精度の定義を直したときだけ
python rescore_rankings.py --dataset full
python summarize.py
python wiki_scale.py
python measure_install.py
python build_report.py   # JSON から HTML のレポートを作る
```

`db_bench.py` は計測済みの組（`status` が `ok`）を飛ばすので、途中で止めても続きから再開できる。`--keep` を付けない限り、計測した索引は消す。

## 3 つのスコアの決め方

- 検索スピード: 製品の CPU 実行系でのクエリ埋め込みの p95（`runtime-parity.json`）と、動作点での DB の p95（dense + 語彙 + RRF、1 問ごとの合計）の和。2 つの p95 の和なので、1 問ごとの合計の p95 より大きめに出る。MCP の通信の時間は含めない。
- DB サイズ: ベクトル索引、全文索引、最小限のメタデータ（id と世代）のディスク容量。
- 精度: 端から端までの、60 問（全量の人手承認ラベル）のページ再現率@30。融合した順位の上位 30 チャンクで打ち切ってからページの重複を除き、上位 30 ページの再現率を測る（`poc/rag/remaining/evaluate_mcp.py` の `limit=30` と同じ）。

2026-11-06 の PR のレビューで、最初の集計が融合した最大 400 チャンクを打ち切らずに `metric` に渡していたことが分かった。`common.metric` で先に 30 チャンクに打ち切るよう直し、`rescore_rankings.py` で保存した動作点の順位から `db-bench-*.json` の精度を計算し直し、`model_accuracy.py` を実行し直した。動作点の選び方（厳密解に対する dense の recall）は変わらない。掃引の各点と絞り込みなしの行の精度は順位を保存していないので計算し直せず、`*_before_cutoff_fix` として旧定義の値を残した。全組の値が 1〜2 問ぶん下がり、判定は変わらなかった。

動作点: 各 DB のつまみ（`nprobes`、`hnsw_ef`、`expansion_search`、`nprobe`、`efSearch`、`ef_search`、sqlite-vec bit の倍率）を掃引し、厳密解に対する dense の recall@30 が 0.95 以上になる最も速い設定を選ぶ。届かなかった組は「未達」とし、3 つとも 7 点以上の判定と段階 2 の候補から外す。

点数: 3 つとも「最良を 10 点、閾値を 3 点」として間を補間し、下限を 1 点とする。速度と容量は対数で、精度は直線で補間する。閾値は、検索 1 秒（件数によらない）、容量 30 GB × 件数 / 761,915（部分集合では約 3.96 GB）、精度は現行（R-130 × LanceDB IVF_SQ）− 0.05 である。最良は表の全行から取る。

最初の実装では、速度と容量の点を `10 × 最良 / 値` にしていた。この式では、閾値を大きく下回る値どうし（17 ms と 58 ms）にも 7 点の差が付き、「閾値の内側で余裕がある」と「閾値すれすれ」を区別できなかった。そこで上の補間に置き換えた。`scores.json` の各行の `ratio_score` に、置き換える前の点を残してある。

60 問では、1 問の違いが再現率 0.017 にあたる。精度の 1〜2 点の差は、1 問の差と同じ程度でしかない。

## 計画との違い

- 製品の実行系との一致を確かめるチャンクは、計画の 1,000 件ではなく 300 件（最長の 20 件を含む）にした。CPU の torch で R-310 を 1,000 件埋め込むと 1 時間を超えるためである。
- FTS5 の `tokenchars` から `'` と `"` を外した。この 2 文字を含めると、`tokenize` の引数の引用が壊れる。
- 語彙検索のエンジンに Tantivy を加えた。FTS5 には上位 k 件で打ち切る仕組みがなく、頻出語（「の」「は」など）を含む OR の検索では、一致したすべての行の BM25 を計算する。100,682 件で p95 が約 0.5 秒、最悪で 5 秒を超え、ネイティブの全文検索を持たない DB（sqlite-vec、usearch、FAISS、Chroma）の組の速度を FTS5 が決めていた。Tantivy は block-max WAND で打ち切る。同じ Sudachi の語を空白で区切って索引するので、分かち書きの差は入らない。
- 段階 1 の「+ Tantivy」の組のうち、`db_bench.py --lexical tantivy` で測っていないものは、dense の実測の順位と `lexical_bench.py` の Tantivy の実測の順位を 1 問ごとに足して融合し直した値である（`measured` が「部品の実測を合成（容量は換算）」）。容量は、FTS5 の実測の容量を引いて Tantivy の容量を足した換算である。
- HNSW のつまみの上限を 512 から 2,048 に、sqlite-vec bit の倍率を `[2, 5, 10, 20]` にした。前者は 512 で目標に届かない組があったため、後者は vec0 の KNN が k ≤ 4,096 に制限されるためである。
- ONNX の書き出しのため、計測用の venv に `onnx==1.19.1` を入れた。
- Tantivy の IDF を BM25（FTS5）の式にそろえた。Tantivy の IDF は `log(1 + (N - n + 0.5) / (n + 0.5))` で常に正なので、「の」「は」のような頻出語も点を稼ぐ。FTS5 の IDF は `log((N - n + 0.5) / (n + 0.5))` で、半数以上の行にある語はほぼ 0 になる。そこで、語ごとに 2 つの IDF の比を重み（`boost_query`）として掛けた。自由に選べる値はない。全量の語彙だけの再現率@30 は、そろえる前が 0.306、そろえた後が 0.456 で、FTS5 は 0.461 だった。頻出語を文書頻度で切る案（20% で 0.533）も試したが、評価の質問で値を選ぶことになるので採らなかった。そろえる前の値でも（下の打ち切り位置を直す前の定義で）、全量の Tantivy の組は 3 つとも 7 点以上だった。判定は変わらず、LanceDB との差だけが変わる。
- 全量の Qdrant HNSW f32 は、`hnsw_ef` = 2,048 で厳密解に対する recall が 0.944 となり、目標に届かなかった。他の HNSW と同じく、つまみの上限を 4,096 に広げて測り直した。
- E-s の全量の GPU 埋め込みは、180,224 件で CUDA のメモリ不足で止まった。`embed_models.py` に `--budget` を足し、1 バッチのトークン数の上限を 16,384 に下げて続きから再開した（`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`）。
- 段階 2 の候補は、DB の系統が重ならないように選んだ。自前の組（usearch、FAISS IVF_SQ8）、サーバー（Qdrant HNSW f32）、wiki に近い組（sqlite-vec f32）、現行の rag（LanceDB IVF_SQ）、現行の wiki（E-s × sqlite-vec f32 + FTS5）である。FAISS HNSW は、部分集合で FAISS IVF_SQ8 とほぼ同じ点で容量が 3 倍だったので外した。R-310 は全量を埋め込むと約 5 時間かかり、精度の差が 1〜2 問なので外した。Qdrant の SQ と BQ は全量で測っていない。

## 段階 2 と M5 で分かったこと（レポートの補足）

- 全量では、精度を決めるのは語彙検索のエンジンだった。同じ R-130 の dense でも、LanceDB の native FTS と Qdrant の BM25 sparse は語彙だけの再現率@30 が 0.322、FTS5 と Tantivy は 0.456〜0.461 だった。dense だけの再現率は 0.75〜0.77 で、DB による差は小さい。
- 全量の FTS5 は p95 が 5.8 秒（最悪 40 秒）で、FTS5 を語彙側に使う組はすべて 1 秒の閾値を外れる。全量では、FTS5 は現行の wiki の基準（E-s × sqlite-vec f32）だけで測った。
- LanceDB、Qdrant、sqlite-vec、Chroma の行は、世代の絞り込み（`generation IN ...`）の費用を含む。usearch と FAISS の行は含まない（評価では全世代が有効なので、結果は同じになる）。LanceDB の全量の DB の p95 は、絞り込みありで 243.6 ms、なしで 203.3 ms だった。
- M5 の同時アクセスで、usearch は読み手が `view=True`（メモリ写像）で索引を開いている間、別プロセスの `save` が Windows で `Permission denied` になった。「開き直しても新しい行が見えない」は、この保存の失敗によるもので、可視性の性質ではない。
- usearch の f16 の索引は、ベクトルを f16 で持つ（`get` で取り出したベクトルと元の cosine は 0.99997）。FAISS IVF_SQ8 は 8 ビットに量子化した値だけを持つ。量子化の方式や索引の種類を変えるとき、usearch は索引から作り直せるが、FAISS では元のベクトルが要る。
- クエリ埋め込みの p95 は、`runtime-parity.json` の値が GPU の埋め込みと並行して測ったもので、大きめに出ている。M5 で他の処理を止めて測ると、R-130 の ONNX fp32 は 38 ms → 21 ms、R-30 は 10 → 4.7 ms、R-310 は 143 → 51 ms、E-s の fastembed fp16 は 66 → 8.5 ms だった。速度のスコアは並行時の値で付けたので、上限の値として読む。R-130 の組はすべて同じだけずれるので、順位は変わらない。
- 現行の wiki の検索（`uv run --script wiki_search.py`）は、W0_Wiki の複製（Markdown 13 ファイル、小さい標本）で 1 回あたり約 3.1 秒かかった。常駐したプロセスでのウォーム検索は、クエリ埋め込みと DB を合わせて数十 ms だった。

## 計測の条件と注意

- CPU は 4 スレッドに制限した（`common.limit_threads`）。計測した PC の CPU 名などは `candidates.json` の `platform` と各 JSON を参照する。仕様としては書かない。
- 段階 1 の計測は、全体を通して R-30 の全量の GPU 埋め込みと並行して動いた。GPU の埋め込みも CPU（トークナイズ）を使うので、段階 1 の時間は大きめに出ている可能性がある。とくに R-310 のクエリ p95（143 ms）は、GPU の別の仕事と並行して測った。段階 2 と M5 は、GPU の埋め込みが終わってから実行した。
- 文書のベクトルは GPU の sentence-transformers で作り、クエリのベクトルは製品の CPU 実行系で作った。両者が一致することは `runtime-parity.json` で確かめた（R-130 の ONNX fp32 で、上位 30 件の一致は 1.0）。
- 60 問の正解ラベルは 4 文書から作ったもので、網羅的ではない。一般的な日本語の PDF の精度を代表しない。
- wiki の現行の語彙検索は純 Python の BM25 である。この計測では、SQLite 側の代わりとして FTS5 を使った。
