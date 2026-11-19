# MinerU と現在の日本語 PDF 抽出の比較（2026-11-18）

MinerU 4.2.3 の `standard`、wiki の文字層抽出（pdfminer.six 20260107、PDFium 5.15.2 によるページ判定）、rag の文字層抽出（PDFium 5.15.2）と画像ページ用 NDLOCR-Lite を、手元の試料で比較した。原本のページ画像と抽出結果を照合した。MinerU は Windows、RTX 3080、ONNX DirectML、llama.cpp で動かした。rag の OCR は既定の 150 DPI、CPU で行った。

この結果は少数の合成文書についての観測であり、日本語文書全体の精度や処理速度を代表しない。ルビ付き実文書はなかったため、2 行のルビ付き合成 PDF を別途作った。既存の PDF は変更していない。

## 結果

| 対象 | MinerU Standard | 現在の方式 |
| --- | --- | --- |
| スキャン画像の縦書き（complex-cases p.5） | 3 列を右から正しい順に抽出 | NDLOCR-Lite も 3 列を正しい順に抽出 |
| 文字層の縦書き（同 p.6） | 文と列の順を保持 | rag の PDFium も保持。wiki の pdfminer は文字ごとに空白を挿入し、縦書きの注意を表示 |
| 画像の 2 段組み（同 p.1） | 左列の 3 行を読んでから右列を読む | NDLOCR-Lite は両列の見出しを同じ行に連結し、本文も行単位で左右を交互に出力 |
| 画像の表（同 p.2） | 3 列×3 行の Markdown 表を作り、値と列の対応を保持 | NDLOCR-Lite は文字を抽出したが列ごとの並びになり、行と列の対応は出力だけでは保てない |
| 文字層の 2 段組み（handbook-2col p.1） | 左段を読んでから右段に進み、表も構造化 | rag の PDFium は本文を段ごとに読めた。wiki の pdfminer は左右の段を途中で混ぜた |
| 文字層の表（expenses p.1） | 6 列×4 行の Markdown 表を作り、値の対応を保持 | rag の PDFium は行ごとに値を抽出。wiki の pdfminer は列単位に分散して出力 |
| 文字層の表（expenses p.2） | `######## 火` と `######## 水` だけを出力。見出し、月曜、人数 `12`・`15`・`9` が欠けた | PDFium と pdfminer は見出し、曜日、人数を出力。pdfminer は列単位、PDFium は改行で一部が分かれる |
| ルビ（合成 PDF） | `とうきょう`、`東京へ行く。`、`きょう`、`今日は晴れ。` の順。親文字とルビの対応を構造として表していない | PDFium は `東京`→`とうきょう`→`へ行く。`、pdfminer は `とうきょう`→`東京`→`きょう`→`今日`→残りの文。どちらも対応を構造として表していない |

expenses p.2 の `########` は元の Excel の列幅不足が PDF に現れたもので、各方式の文字認識の誤りではない。一方、人数の 12、15、9 は PDF 上で目視でき、MinerU の出力から欠落した。MinerU の合計 Markdown はページ区切りを保持していないため、ページ単位の出典追跡が必要なら別の構造化出力の検証が必要である。

## 判断

今回の試料では、MinerU は画像の表と複数段の読み順で有望だった。ただし、文字層付き PDF の表で実際に数値を落としたため、現時点で無条件に現在の抽出方式を置き換える根拠にはならない。ルビは 2 例とも親文字との対応が表現されず、本文の続きも両方式で分断された。実際の書籍や論文を使い、ページの区切り、欠落、表のセルと数値、縦書き、ルビを採点して再比較する必要がある。

## 試料と成果物

- `C:/Works/info-hive-dev-data/rag-poc-data/ocr-remaining-20261104/complex-cases.pdf`、SHA-256 `68f264076366110da8330b8c8424e318de2b18745c7935f4f39e001c1aafe0b3`。p.1・2・5 は画像、p.6 は文字層の縦書き。MinerU は PDF 6 ページ全体を一度に解析した。
- `docs/research/markitdown-benchmark-2026-11-15/corpus/handbook-2col.pdf`、SHA-256 `80687ffbfec4d8ab9de8482ab9789dfd2e37eddaceb5bc4168ac0f3c4f96186b`。
- `docs/research/markitdown-benchmark-2026-11-15/corpus/expenses.pdf`、SHA-256 `55d2f35e788c8c2d243ff892b7b50b88ddd02f40aa7c5415f0d608751686c7cd`。
- `C:/Works/info-hive-dev-data/mineru-benchmark/ruby-synthetic.pdf`、SHA-256 `33257589487be42ff973677ffbbef343d388d84a836f7c82520cefb76931fff2`。目視でルビと親文字の表示を確認した。
- `C:/Works/info-hive-dev-data/mineru-benchmark/` に MinerU の Markdown、wiki の出力、rag のページ判定・抽出と OCR の JSON、確認用画像を保存した。`rag-complex.json` の OCR 実行対象は p.1・2・5 であり、p.3・4 は比較対象ではない。

## 実行方法

MinerU は各 PDF を `mineru-kit parse <PDF> -o <出力> --tier standard` でローカル解析した。wiki はインストール済みの `wiki_pdf.py <PDF> --max-chars 100000`、rag の文字層は `rag_pdf_layer.inspect_page`、画像は PDFium で 150 DPI に描画後、固定版 `rag_ocr.py` を使用した。MinerU の初回実行ではモデルを取得した。実行時間を同じ条件で測定していないため、速度の比較は行わない。
