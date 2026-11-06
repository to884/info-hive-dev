# ADR-0011：wiki と rag の埋め込み、ベクトル索引、語彙検索をそろえる

| 項目 | 内容 |
| --- | --- |
| 状態 | 承認 |
| 決定日 | 2026年11月6日 |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0007、ADR-0012、[統一の測定](../research/embedding-backend-unification-2026-11-05.html)、[統一の決定のための追加測定](../research/embedding-backend-decision-2026-11-06.html) |

## 背景

wiki と rag は、埋め込みモデルとベクター DB をそれぞれ別に持っている。

- wiki: fastembed の `intfloat/multilingual-e5-small`、sqlite-vec、純 Python の BM25（かな・漢字の bigram）
- rag: sentence-transformers（torch）の `cl-nagoya/ruri-v3-130m`、LanceDB、Sudachi の語の BM25

両方を入れた PC には、モデルと DB が 2 組ずつ並ぶ。統一の測定（2026-11-05）は、6 つのモデルと 13 の DB の方式を全量 761,915 チャンクで比べ、ruri-v3-130m の ONNX、usearch、Sudachi + Tantivy、RRF の組を推した。ただし、融合の効果、Windows での書き込み、wiki での再埋め込みの時間、常駐メモリ、世代の絞り込みの費用、wiki の評価ゲート、ONNX の配布を確かめていなかった。

2026-11-06 の追加測定（E1〜E11）でこれらを測った。モデルと索引の選択は変わらなかった。閾値を外れたのは語彙検索の統一、初回の再埋め込みの時間、MCP の上乗せの 3 点で、どれもユーザーが追加の測定の結果を見て決めた。

## 決定

| 対象 | 決定 |
| --- | --- |
| 埋め込みモデル | `cl-nagoya/ruri-v3-130m` を ONNX fp32 で動かす。重みは `onnx-community/ruri-v3-130m-ONNX`（revision `cbd305d`）、トークナイザーは `cl-nagoya/ruri-v3-130m`（revision `e3114c6`）から取る。接頭辞はクエリが `検索クエリ: `、文書が `検索文書: `。実行系は onnxruntime（fastembed の独自モデルとして登録する） |
| ベクトル索引 | usearch、f16、コサイン。ベクトルが 50,000 件以下の索引は総当たりで探し、それを超える索引は HNSW（`connectivity` 16、`expansion_add` 256、検索時の `expansion_search` 1,024）で探す |
| 語彙検索 | Tantivy の BM25 にそろえる。wiki の索引には wiki の `tokenize()`（bigram）のトークンを、rag の索引には Sudachi（SplitMode C、normalized_form）のトークンを入れる。エンジン、書き込みの規則、世代の削除は共通にし、トークンの作り方だけを索引の集まりごとに変える |
| 融合 | RRF。k は 30、語彙の重みは 0.5、候補は片側 200 件 |
| wiki の距離の上限 | R-130 の `max_distance` を 0.208 にする |
| 世代 | 古い世代の行は、取り込みのときに usearch の `remove` と Tantivy の削除で消す。消し終わるまでの検索は、候補を 1.25 倍取ってから無効な世代を除く |
| 書き込みの規則 | 索引の書き手は 1 つのプロセス（ADR-0012 の wiki の MCP サーバー）だけにする。usearch は一時ファイルに保存してから `os.replace` で置き換え、同じプロセスの検索とは書き手を優先する読み書きロックで分ける。Tantivy の commit が失敗したら rollback し、同じ文書を入れ直す。失敗した writer をそのまま使い続けない |
| fingerprint | 抽出用と索引用に分ける。抽出用は OCR の方式、dpi、OCR の revision から作り、抽出結果の再利用に使う。索引用はモデル、revision、実行系、接頭辞、チャンクの切り方、トークンの作り方、索引の種類とパラメーターから作る |
| 再埋め込み | wiki は 1 度だけ再埋め込みが要る。初回は時間がかかってよい（目安の 20 分を緩める）。そのことを upgrade の案内に書く。rag は既存のベクトルを使い回し、usearch と Tantivy の索引だけを作り直す |

## 理由

- R-130 は wiki の en と ja の評価ゲートを通った。正例が必要とする距離の最大は 0.1992、負例の最も近い距離は 0.2164 で、そのあいだの 0.208 で偽陽性を 0 にできる。公開版の ONNX は、測定に使ったファイルと sha256 が一致した。GPU の sentence-transformers との cosine の最小は 1.0000 だった。ライセンスは apache-2.0 である。
- usearch（M16、expansion_add 256）は、全量で DB の p95 が 34.0 ms で、FAISS IVF_SQ8（nlist 4,096）の 52.9 ms より速かった。採点の最小点は FAISS のほうが 0.3 点高い。差はすべて容量の点の差で、FAISS に替える規則（0.5 点以上の差）に届かない。
- HNSW のグラフは作るたびに少し変わる。wiki の評価セットの 103 件の索引でも、作り直すと 32 問中 13 問で意味の検索の順位が変わり、en の MRR が 0.731 と 0.699 のあいだで揺れた。総当たりにすると揺れは 0 問になった。小さな索引では順位が決まるほうを採る（[MCP サーバーの実装の記録](../research/wiki-mcp-server-2026-11-06.md)、2026年11月6日のユーザーの判断）。境の 50,000 件は、実装の定数 `EXACT_SEARCH_LIMIT` の値である。
- Sudachi に統一すると、ja のセクションの MRR が 0.901 から 0.849 に下がり、wiki の評価ゲートに落ちた。two-char、paraphrase、filter の種類で下がった。Tantivy に wiki の bigram を渡すと、en と ja のゲートを通り、指標は今の wiki の BM25 と小数第 3 位まで同じだった。
- 融合の設定を k 30、重み 0.5 にすると、全量の再現率@30 が 0.758 から 0.800 に上がった。natural、wiki、全量のどのセットでも、1 問を超えて悪化しなかった。
- Windows では、別のプロセスがメモリに写像した索引ファイルを置き換えられなかった（20 回とも PermissionError）。1 つのプロセスが持って保存・置き換えを繰り返す方式は、wiki 規模 200 回、全量 5 回でエラーがなかった。
- Tantivy の commit は Windows で約 2% の割合で「アクセスが拒否されました」で失敗した。失敗した writer を使い続けると、その後の commit が成功を返しても文書が残らなかった（14,550 件中 2,050 件）。rollback して入れ直すと、失われた文書は 0 だった。
- 世代の絞り込みの p95 の増分は、無効の文書が 1〜20% のどれでも誤差の範囲だった。文書の 10% の削除は、usearch で 0.023 秒、Tantivy で 0.014 秒だった。
- 今の rag の fingerprint はモデルを含むので、モデルや索引を替えるたびに 22,335 ページの OCR からやり直すことになる。抽出用と索引用に分ければ、OCR の結果を使い回せる。

## 検討した選択肢

| 選択肢 | 判断 |
| --- | --- |
| wiki の e5-small と sqlite-vec に rag を合わせる | 採らない。PDF の質問の精度が下がり、総当たりの検索が全量で 6,693 ms かかる（統一の測定） |
| rag の R-130（torch）と LanceDB に wiki を合わせる | 採らない。精度と容量の点が 7 点未満で、wiki に torch が入る（統一の測定） |
| FAISS IVF_SQ8 | 採らない。容量は usearch の半分以下だが、遅い。最小点の差は規則に届かない |
| 語彙検索を Sudachi に統一する | 採らない。wiki の ja の評価ゲートに落ちる |
| wiki の語彙検索を今の純 Python の BM25 のままにする | 採らない。ゲートは通るが、エンジンと書き込みの規則が 2 つ残る |
| wiki だけ R-30 にする | 採らない。初回の再埋め込みは短い（推定 10 分）が、wiki と rag でモデルが分かれる |
| スコアを min-max で正規化する融合（α=0.6） | 候補として記録だけ残す。全量で 0.808 だったが、RRF との差は 1 問未満で、natural では選んでいない |

## 影響

- rag は torch と LanceDB を外し、onnxruntime（fastembed）、usearch、tantivy を使う。wiki は sqlite-vec を外し、usearch と tantivy を加える。
- `SCHEMA.md` の目印の行 `- Semantic backend: local FastEmbed + sqlite-vec` を、新しい組を表す行に替える。`/wiki:upgrade` は古い行を見つけたら、再埋め込みと索引の作り直しを案内する。
- `--no-embed` の純 Python の BM25 は残す。MCP サーバーや依存が使えないときの代わりにする。
- wiki の評価ゲートの基準値（baselines）は、R-130 と Tantivy の構成で取り直す。
- 常駐メモリは、モデルを読み込んだ構成で wiki 規模 2.53 GiB、全量 2.56 GiB（private）だった。追加測定の提案値（1.0 GiB、2.5 GiB）はどの索引でも超えた。大半は、長い文書を 1 回で埋め込んだときに onnxruntime が確保した領域である。埋め込みのバッチの大きさと文書の長さの上限を決めるときに、値を決め直す。
- natural の負例 12 問は、R-130 でも e5 でも `max_distance` の内側に入る。答えを返さない判断（abstain）は別の作業として残る。
- 測定は Windows の 1 台の PC で行った。macOS と Linux での書き込みの規則と速さは確かめていない。

## 見直す条件

- 索引の書き手を複数のプロセスにする必要が出たとき。ADR-0012 の単一の書き手を前提にしているためである。版ごとのファイルと manifest を付け替える方式は、Windows では読み手が manifest を開いている間に置き換えが失敗したので、書き手と読み手の両方に入れ直しが要る。
- usearch と FAISS の最小点の差が 0.5 点以上になったとき。
- 総当たりで探す索引の検索の p95 が目安を超えたとき。`EXACT_SEARCH_LIMIT` を下げる。
- wiki の評価ゲートで、Tantivy の構成が今の BM25 より下がったとき。

## 参照

- [統一の決定のための追加測定](../research/embedding-backend-decision-2026-11-06.html)：E1〜E11 の結果と、2026-11-06 の判断
- [測定の JSON と再現の手順](../research/embedding-backend-decision-2026-11-06/README.md)
- [統一の測定](../research/embedding-backend-unification-2026-11-05.html)：モデル 6 つと DB の方式 13 の比較
- 2026年11月6日のユーザーの判断：再埋め込みは「目安を緩める」、語彙検索は「案 2: Tantivy にそろえる」
