# MinerU の表の数値欠落の調査（2026-11-18）

[[mineru日本語pdf比較-2026-11-18]] で、`expenses.pdf` の 2 ページ目にある人数 12、15、9 が MinerU 4.2.3 Standard の Markdown から欠けた件を調べた。対象 PDF は `docs/research/markitdown-benchmark-2026-11-15/corpus/expenses.pdf`、SHA-256 は `55d2f35e788c8c2d243ff892b7b50b88ddd02f40aa7c5415f0d608751686c7cd`。原本は変更していない。

## 原因

元の全文書解析を `middle_json` で再現すると、`parse_mode` は `txt` で、2 ページ目の結果に `######## 火` と `######## 水` の 2 ブロックしかない。数値と見出しは Markdown 描画より前に失われている。元 PDF の文字層には見出し、曜日と 12、15、9 が存在する。

`_prepare_pdf_window` の戻り値を読み取る計測用スクリプトで、Standard のレイアウト検出結果を保存した。原本のページ全体を 1654×2339 に描画したとき、2 ページ目に検出されたのは火曜・水曜付近の `text` 領域 2 個だけであり、表候補はなかった。正規化した横座標は約 0.095〜0.201。人数の文字は約 0.327〜0.345 にあり、検出領域の外にある。見出しと月曜も領域に入らない。表候補がないため、表としての後段処理へその領域全体が渡っていない。

したがって直接の原因は、Standard のレイアウト検出が表全体とそこにある文字を覆う領域を生成できなかったことである。`txt` として読んでいても、文字層のすべてが最終ブロックに自動的に入るわけではない。検出器のどの内部要因が見落としを生じさせたかまでは確定していない。元ページでは表が小さく、周囲に大きな余白がある。表付近を切り出した別試料では Standard が数値を回収したが、切り出しはページ座標とモデル入力の見え方を同時に変えるため、余白や文字サイズの一方だけを原因とは断定できない。

ページ 2 だけを `auto` で指定すると `ocr`、全文書を `auto` で指定すると `txt` になった。ただし全文書の元の欠落は `txt` で再現し、ページ単独に `txt` を強制しても欠落した。したがって自動判定の差だけが元の欠落の原因ではない。

## 対処の実測

| 条件 | 処理モード | 2 ページ目の結果 |
| --- | --- | --- |
| Standard、全文書、auto | txt | 見出し、月曜、人数 12・15・9 を欠落。元の結果を再現 |
| Standard、ページ 2、txt 強制 | txt | 同じ 2 ブロックだけで、人数を欠落 |
| Standard、ページ 2、auto または ocr 強制 | ocr | 見出しと人数を欠落 |
| Flash または Basic、ページ 2、auto | ocr | 人数を欠落 |
| Flash、ページ 2、txt 強制 | txt | 人数 12・15・9 と見出しを回収。表構造はなく、本文中に値が分散 |
| Advanced、全文書、auto | txt | 見出し、月・火・水、12・15・9 を正しい列の表として出力 |
| Advanced、ページ 2、auto | ocr | 同じ数値・列を回収。独立した再実行でも同じ結果 |
| Advanced、ページ 2、txt 強制 | txt | 同じ数値・列を回収 |
| Standard、ページ 2 の表周辺を切り出した別 PDF、txt 強制 | txt | 見出しと 12・15・9 を行として出力。表ではなく index と分類 |

Advanced は Standard の既存レイアウトを使った抽出とは異なる `batch_two_step_extract` を使う。元ページ全体を扱う Advanced の経路が、この試料では失われた表を回収した。コードの分岐は [MinerU の該当実装](https://github.com/opendatalab/MinerU/blob/b4efa4b2b76ebb012c476b79bdfc6f18a95aacd6/mineru/backend/analysis/pdf/window.py#L645-L653) を参照。

ただし Advanced も完全ではない。原本の `########` は 8 個だが、表の 3 行ではいずれも `#######` と 7 個になった。これは原本の Excel で列幅不足により表示された文字列で、元の日付は PDF に表示されていない。実際の数値・表での精度や、他の文書の全体品質はこの 1 試料からは保証できない。Flash と txt の結果は数値の欠落検知や照合の候補になるが、それだけでは表の行・列の対応を保証しない。

## 再現と証拠

Windows、RTX 3080、ONNX DirectML と llama.cpp を用い、隔離した `C:/Works/info-hive-dev-data/mineru-benchmark-env/` の MinerU 4.2.3 でローカル解析した。たとえば Advanced の全文書の Markdown は次のコマンドで取得した。

```powershell
mineru-kit parse expenses.pdf -o advanced.md --tier advanced
```

比較には `--format middle_json` と `--pages 2`、`--ocr-mode auto|txt|ocr` を適宜指定した。`middle_json` の表 HTML を解析して、見出しと 12・15・9 の列を全文書・単独ページ・txt・再実行の 4 結果で照合し、3 行の `#` がいずれも 7 個であることも確かめた。Advanced の全文書 Markdown も実際に生成し、同じ表が表示されることを確認した。

出力、中間 JSON、ログ、切り出し画像、計測用スクリプトは `C:/Works/info-hive-dev-data/mineru-benchmark/diagnosis-20261118/` に置いた。`trace-standard-all.json` は Standard のレイアウト検出と後段に渡すブロックの記録で、SHA-256 は `ca47929eec971dbdc3633e3afb9c14eacd4f0f05c7186546e52c5dce7fa5aba4`。`pdf-words-page2.json` は PDF の文字列と正規化座標である。抽出モデルへの入力内容の記録であり、モデル内部の判断理由を説明するものではない。
