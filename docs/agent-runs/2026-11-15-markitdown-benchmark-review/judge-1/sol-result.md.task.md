# 抽出の品質の判定

あなたは、文書をテキストに変換した結果の品質を判定する審査員である。
LLM が管理する wiki（info-hive）では、取り込むソースをまず Markdown かテキストに変換し、LLM がそれを読んで要約ページを書く。変換の方式を選ぶために、同じ原本を別々の方式で変換した出力を比べたい。

## 読むもの

- `docs/research/markitdown-benchmark-2026-11-15/scripts/content.py`: 原本の中身（正解）。すべての試料は、このファイルの文から作った。
- `docs/research/markitdown-benchmark-2026-11-15/judge/<試料>/<記号>.md`: 変換した出力。記号（A〜D）は試料ごとに無作為に付けてあり、方式の名前は伏せてある。
- 原本そのもの（`docs/research/markitdown-benchmark-2026-11-15/corpus/`）は読んでもよい。PDF の見た目を確かめたいときに使う。

`judge/` と `scripts/content.py` と `corpus/` のほかは読まない。とくに、方式の名前が分かるファイル（計測のスクリプトの出力や結果の表）を探さない。判定は出力の中身だけで行う。

## 試料

| フォルダ | 原本 | 正解（content.py） | 注意 |
| --- | --- | --- | --- |
| `handbook_docx` | Word の文書。見出し、段落、箇条書き、番号付きの手順、表（4 列 5 行）。ヘッダーに「社外秘・試料」、フッターにページ番号 | `doc_truth(long=True)` | ヘッダーとフッターは本文ではない |
| `handbook_pdf` | 上の Word 文書を Word で PDF に書き出したもの（1 段組み、3 ページ） | 同上 | 各ページのヘッダーとフッターは本文ではない |
| `handbook-2col_pdf` | 同じ文書を 2 段組みにして PDF に書き出したもの（2 ページ） | 同上 | 左の段を読み終えてから右の段に進むのが正しい読み順 |
| `slides_pptx` | PowerPoint のスライド 5 枚。2 枚目に発表者のノート、3 枚目に表、4 枚目に左右 2 つの本文 | `slide_truth(with_notes=True)` | ノートは本文に含めてよい |
| `slides_pdf` | 上のスライドを PDF に書き出したもの | `slide_truth(with_notes=False)` | PDF にはノートがない |
| `expenses_xlsx`、`expenses_xls` | Excel のブック。シート「経費」（合計の列は =SUM の式）とシート「日別」（日付のセル） | `sheet_truth()` | 合計の値（24500 など）が出ていれば式の値を読めている |
| `expenses_pdf` | 上のブックを PDF に書き出したもの | 同上 | PDF の上で日付の列が「########」と表示されている（列の幅が足りない）。日付が出ないことを抽出の欠点として数えない |
| `article_html` | Web ページ。本文（`<article>`）のほかに、ナビゲーション、広告、フッター、スクリプトがある | `doc_truth(long=False)` と `HTML_NOISE` | ナビ、広告、フッター、スクリプトは雑音 |
| `staff-utf8_csv`、`staff-cp932_csv` | CSV。UTF-8 と Shift_JIS（CP932） | `CSV_ROWS` | 文字化けがないか |
| `policy_json`、`policy_xml` | JSON と XML | `JSON_DATA`、`XML_TEXT` | |
| `story_epub` | EPUB。2 章の短い物語。題名は「在宅の春（試料）」 | `EPUB_CHAPTERS` | |
| `bundle_zip` | ZIP。中に handbook.docx、staff-utf8.csv、policy.json | それぞれの正解 | 中のファイルの区切りが分かるか |

出力が 1 つしかない試料もある。その場合も、同じ基準で絶対評価する。

## 判定の軸

それぞれの出力に、次の 6 つの軸で 1〜5 の点を付ける（5 が最良）。当てはまらない軸は `null` にする。

1. `coverage`（網羅）: 本文の欠落、重複、取り違えがないか。数値の誤りは重く見る。
2. `order`（読み順）: 原本の論理的な順に読めるか。段の混線、表のセルの散らばりは減点する。
3. `structure`（構造）: 見出し、箇条書き、表が、読み取れる形で残っているか。原本にない表や見出しを作って意味を壊していたら、何も構造がないより悪いとみなす。
4. `noise`（雑音）: 本文でないもの（ヘッダー、フッター、ナビ、広告、スクリプト）が混ざっていないか。
5. `location`（位置）: ページ、スライド、シートなど、出典の位置を示す手がかりが残っているか。原本にその単位がない形式（HTML、CSV、JSON、XML）は `null`。
6. `usability`（総合）: LLM がこの出力だけを読んで要約ページを書くとき、誤解せずに使えるか。

点のほかに、致命的な誤り（意味を変える混線、誤った表、数値の取り違え）があれば、出力の行を挙げて具体的に書く。推測は推測と書く。

## 出力の形

最終メッセージに、次の 2 つをこの順に書く。

1. 次の形の JSON を、```json のコードブロックに 1 つだけ書く。

```
{
  "handbook_pdf": {
    "A": {"coverage": 5, "order": 4, "structure": 2, "noise": 2, "location": 4, "usability": 3,
          "fatal": ["…"], "comment": "…"},
    "B": {…}
  },
  …
}
```

`fatal` と `comment` は日本語で書く。`comment` は 2 文以内にする。

2. `## 総評` の見出しのあとに、日本語で、形式ごとに分かった傾向を箇条書きで 10 項目以内にまとめる。方式の名前は推測しない。
