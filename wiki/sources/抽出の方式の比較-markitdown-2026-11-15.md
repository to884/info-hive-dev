---
type: "source"
title: "今の取り込みと MarkItDown の抽出の比較（2026-11-15）"
tags: ["取り込み", "rag"]
authors: ["to884"]
raw: "docs/research/markitdown-benchmark-2026-11-15.md"
ingested: 2026-11-15
created: 2026-11-15
updated: 2026-11-19
---

# 今の取り込みと MarkItDown の抽出の比較（2026-11-15）

wiki と rag の取り込みで MarkItDown を使うかを決めるために、今の抽出と MarkItDown 0.1.9 を、速度、機械的な指標、GPT-6.1 Sol の判定で比べた調査である。原本は `docs/research/markitdown-benchmark-2026-11-15.md` で、試料、スクリプト、出力、判定は同じ名前のディレクトリにある。レビューの記録は `docs/agent-runs/2026-11-15-markitdown-benchmark-review/` にある。

まだ何も決めていない。対応したい形式を MarkItDown で広げる構想（PDF、Office、HTML、CSV、JSON、XML、ZIP、EPUB、画像、音声、YouTube）の前に、手がかりを得るために測った。

## 進め方

- 試料は、架空の社内文書から作った 15 個である。DOCX、PPTX、XLSX、XLS、それらを Office で書き出した PDF 4 つ（2 段組みを含む）、HTML、UTF-8 と Shift_JIS の CSV、JSON、XML、EPUB、ZIP を作った。正解の文字列が分かっているので、機械的に数えられる。作者の書籍は使っていない。
- 今の方式として、pdftotext、pdfminer、rag 0.5.3 の PDFium の抽出（OCR なし）、`wiki_fetch.py`、`wiki_encoding.py` で判定してそのまま読む方法を比べた。作者の指示で OCR は使わず、画像、音声、YouTube は外した。
- 品質は、方式の名前を伏せて Sol に 6 つの軸で採点させた。指標と判定の作り方は、2 回の敵対的レビューで直した（[[抽出の品質の測り方]]）。

## 分かったこと

- Office が書き出した PDF では、rag の PDFium の抽出がもっとも良かった（Sol の総合 4、4、5、5、順に読めた割合はすべて 1.0）。2 段組みでも左の段から右の段へ読んだ。
- MarkItDown は、3 つの PDF で意味を変える誤りを作った。2 段組みでは左右の段を 1 つの表に混ぜ、スライドでは左右の本文を語の途中でつなぎ、表計算では値を隣の列に入れた。ページの区切りも出さない。
- MarkItDown は、DOCX、PPTX、XLSX、XLS、EPUB、ZIP（中身は DOCX、CSV、JSON）では総合 5 だった。XLSX と XLS の式の計算済みの値、PPTX のノートとスライドの区切りも残した。
- 同じ中身なら、元の形式のまま MarkItDown にかけるほうが、PDF にしてから抽出するより良かった。
- HTML では、`wiki_fetch.py` が雑音を除き、MarkItDown はナビ、広告、フッターを残した。CSV、JSON、XML は、どちらでも差がなかった。
- MarkItDown の起動は、`import` までで 3.3〜3.8 秒かかった。変換は 0.34 秒以下。依存は追加の依存を含めて 189 MiB で、今の wiki の抽出は標準ライブラリだけで動く。
- wiki の手順にある `pdftotext` は、この PC では Git for Windows の Xpdf 4.00 だった。Poppler ではない。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| 1 | Office が書き出した PDF では、PDFium の抽出が pdftotext、pdfminer、MarkItDown より読み順と表で良い。書籍などの PDF では確かめていない | レポートの「結果」の「PDF」 | source_only | まだ決定ではない。書籍の PDF で確かめてから決める |
| 2 | Office の形式と EPUB には MarkItDown が使える（今回の試料で総合 5） | レポートの「結果」の「Office の形式、EPUB、ZIP」 | source_only | 採るかどうかは、起動の時間と依存の置き場所と合わせて決める |
| 3 | 抽出の品質を文字列の有無で測ると、数値の境目、表の列、読み順を見誤る。判定は採点した中身に結び付ける | レポートの「計測の方法」と「レビュー」 | create | [[抽出の品質の測り方]]。次に別の抽出を比べるときにも使う |
| 4 | MarkItDown の起動は約 3.5 秒、依存は約 190 MiB | レポートの「速度」と「依存の大きさ」 | source_only | 数値で、ほかのページから引く場面がまだない |

## 関係するページ

- [[抽出の品質の測り方]]
- [[mineru-readme]]（後日調べた別の候補。今回のベンチマークでは測っていない）
- [[pdfのヘッダーの条件]]（rag が PDF を確かめる段階）
- [[敵対的レビューで設計を直す進め方]]
- [[youtubeの字幕の取り込みの選択肢-2026-11-15]]（構想の 1 つ、YouTube の字幕の取り方の調査）
