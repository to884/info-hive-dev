# wiki の MCP 検索と ruri の初回取得

2026-11-21、Windows 11 の Claude Desktop 6.6395.0.0、Code、wiki 0.39.1 で確認表の確認 6 を実行した。確認 5 と別の試行で、e5 と ruri のキャッシュがない初期状態を復元した。Code で練習用 wiki を初期化し、味噌を取り込むと、e5 のキャッシュが 252,425,348 バイトになった。この時点で ruri は未取得だった。

1. 08:22:28.698（JST）に Code が MCP の `mcp__plugin_wiki_wiki__query` で「味噌」を検索した。結果は `mode: lexical`、`index.state: embedding`、埋め込み済み 0/14。語彙検索で `sources/味噌.md` が返った。
2. 08:22:45.007 に `ruri-v3-130m-onnx-cbd305d/verified.json` が書かれた。呼び出しから 16.31 秒で、ディレクトリは 535,699,472 バイトだった。利用者によるモデルの操作なしに取得された。
3. 同じ検索をもう一度行うと、`mode: hybrid`、`index.state: ready`、埋め込み済み 14/14 になり、結果に `bm25` と `embedding` が付いた。

確認 5 のチュートリアルでは、質問に対して索引とページを読んだため、3 回とも ruri は取得されなかった。上の時間とサイズは、今回の Windows VM、モデルの版と通信環境での観測。証拠は `C:\stage2-records\autotest` の `06-ruri-watch.json`、`06-ruri-first-verified.json`、`06-ruri-warm-verified.json` と対応する検索の出力。
