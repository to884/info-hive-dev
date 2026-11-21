# 補助資料で確定できなかった点の描画

開発v71で出典待ちだった三つの点に限って、固定450 DPIで二票の位置に同じ成分を絞った。元PDFの通常描画が固定150 DPIと一致する状態で、文字の描画を非表示にした。防衛白書の2行では対象位置で画素が変わった。情報通信白書概要29行目では対象の36画素すべてが残り、画像オブジェクト一つを非表示にすると31画素が変わった。この点は元PDFでも画像として描かれている。

概要が参照するAI事業者ガイドライン第1.1版では、該当語句は表のセルにあり、概要の画像にある先頭の点を含まない。出典は本文の由来だけを確認でき、概要の先頭の符号は確定できない。既存の正規化と判定を維持した。[描画の結果](result.json)・[AI事業者ガイドライン第1.1版 別添の表3](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20250328_3.pdf#page=19)

同じ図表を載せた総務省説明者の公開講演資料にも、印刷上14スライド目に対象の行がある。PDFは物理15ページ。Popplerで見た点を、PDFiumで元の文字の描画だけを非表示にして確認した。56画素の範囲は変わらず、画像要素を消した場合に14画素が変わった。講演資料の点も画像として残っている。図表の隣接する項目の文言に版の差があるため、公開講演PDFは概要の原稿と同一とは扱わない。[公開講演の配布資料](https://www.glocom.ac.jp/wp-content/uploads/2025/09/GCQ20250919whitepaper_01_kato.pdf#page=15)・[配布元の開催記録](https://www.glocom.ac.jp/events/information/11024)・[画素の診断](presenter-slide.json)

総務省の公開サイトから取得した白書概要PDFの物理10ページを再確認した。ページ内の埋め込み画像5点は固定原本と同じSHA-256、通常の固定150 DPIの全画素も一致した。本文のデータ集にある同名の分類表では、同じ語句は表のセルで、概要に付けられた先頭の点がない。公開されているこれらの資料では、概要の当該符号に対応する文字の原データを確認できなかった。[総務省の白書概要](https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r07/summary/summary01.pdf#page=10)・[本文の分類表](https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r07/image/f00073.png)

公開ページの同じ資料へのリンクはPDF。元の概要PDFには構造タグも添付もなく、講演PDFの代替テキストにも対象の語句はなかった。公開PDF内から辿れる文字の原稿は見つからなかった。[白書の公開ページ](https://www.soumu.go.jp/johotsusintokei/whitepaper/r07.html)・[講演の公開ページ](https://www.glocom.ac.jp/events/information/11024)
