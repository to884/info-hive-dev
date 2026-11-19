---
type: "source"
title: "MinerU と現在の日本語 PDF 抽出の比較（2026-11-18）"
tags: ["取り込み", "rag", "試験"]
authors: ["Codex"]
raw: "raw/mineru日本語pdf比較-2026-11-18.md"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
---

# MinerU と現在の日本語 PDF 抽出の比較（2026-11-18）

[[mineru|MinerU]] 4.2.3 の `standard` と、wiki の pdfminer による文字層抽出、rag の PDFium と画像ページへの NDLOCR-Lite を、手元の日本語 PDF で比較した。記録の正本は `raw/mineru日本語pdf比較-2026-11-18.md`。作成した調査レポートは `docs/research/mineru-japanese-comparison-2026-11-18.md` にもある。

PDFium 5.15.2、pdfminer.six 20260107、固定版 NDLOCR-Lite を使った。MinerU は RTX 3080、ONNX DirectML、llama.cpp、rag の OCR は 150 DPI・CPU で実行した。抽出結果は `C:/Works/info-hive-dev-data/mineru-benchmark/` に保存されている。

## 観測したこと

| 対象 | MinerU Standard | 現在の方式 |
| --- | --- | --- |
| スキャンの縦書き 3 列 | 右から正しい順に抽出 | NDLOCR-Lite も正しい順に抽出 |
| 画像の 2 段組み | 左列を読んでから右列へ進んだ | NDLOCR-Lite は見出しを結合し、本文を左右交互に並べた |
| 画像の表 | 行・列の対応を保つ Markdown 表を出力 | NDLOCR-Lite は文字を抽出したが、行と列の対応を保てなかった |
| 文字層の 2 段組み | 左段から右段へ読み、表も構造化 | rag の PDFium は段ごとに読めた。wiki の pdfminer は左右を途中で混ぜた |
| 文字層の表 | 1 ページ目は値の対応を保ったが、2 ページ目では人数の `12`・`15`・`9`、見出し、月曜日が欠けた | PDFium と pdfminer は 2 ページ目の見出し・曜日・人数を出力した。pdfminer は列単位、PDFium は一部が改行で分かれた |
| ルビ付き合成 PDF | 親文字とルビを取り出したが、対応を構造として表せなかった | PDFium と pdfminer も対応を構造として表せず、本文の続きが分断された |

> Codex 補足: 表は、それぞれの試料で観測した結果である。MinerU の Markdown はページ区切りを保持しなかった。文字層の表の `########` は原本 PDF にある表示で、抽出で生じた誤りではない。

## 範囲と判断

元の資料は `complex-cases.pdf`、`handbook-2col.pdf`、`expenses.pdf` と、今回作った 2 文のルビ付き PDF である。原本と試料の SHA-256、コマンド、出力の保存場所は raw に記録した。`complex-cases.pdf` は 6 ページを MinerU で一度に解析し、rag の OCR は比較対象の 1・2・5 ページで実行した。

少数の合成文書の観測であり、日本語文書全体の精度を代表しない。ルビ付き実文書、旧字体、手書き、Basic と Advanced の差は調べていない。速度も同条件で測定していない。MinerU の画像の表と段組みは有望だが、数値欠落があるため無条件に現在の方式を置き換える根拠にはならない。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| 1 | 少数の試料で、MinerU は画像の表と段組みを復元した一方、文字層付きの表で人数を欠落させた | raw の「結果」「判断」 | update | [[mineru]] の日本語対応に実測と限界を反映する |
| 2 | ルビのある 2 文の合成 PDF では、どの方式もルビと親文字の対応を構造として表さなかった | raw の「結果」のルビの行 | update | [[mineru]] に実文書との違いを明記する |
| 3 | 構造化した表にも欠落があり、文字層と OCR・VLM の出力を原本と照らす必要がある | raw の「結果」の文字層の表と「判断」 | update | [[抽出の品質の測り方]] に、次の評価で確認する反例を追加する |
| 4 | MinerU の Markdown にページ区切りがなかった | raw の「結果」の直後 | source_only | 今回は他の構造化出力や閲覧 API でのページ情報を検証していない |

> Codex 補足: 行き先は今回実際に更新したページである。性能の一般的な順位や採用の決定を示すものではない。

## 関係するページ

- [[mineru]]
- [[抽出の品質の測り方]]
- [[抽出の方式の比較-markitdown-2026-11-15]]
