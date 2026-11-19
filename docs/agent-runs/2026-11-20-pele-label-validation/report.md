# Pele のラベルの収まり・重なり・PNG 文字の検証

2026-11-20。親の main b59fd6d41a18c1fab27431bdb6a4b87f6aa59eae から作った専用 worktree で実施した。[前回の図種・CSS・フォント検証](../2026-11-19-pele-png-compatibility/report.md) で保存した 27 画像を使った。内訳は 12 原稿の明暗 24 画像と CSS 対照図 3 画像である。

## 条件

Playwright 1.56.1 の Chromium 141.0.7390.37 と Windows 版 WebKit 26.0 で SVG を自然寸法、deviceScaleFactor 1 で表示した。前回と同じ Noto Sans JP の Regular と Bold を明示的に読み込んだ。元のフォントと PNG の SHA-256 を照合し、resvg-js 2.6.2 による全 54 枚の PNG 再生成が保存済みと一致することを確認した。自然寸法の 1 倍 PNG と両辺を 2 倍にした PNG を調べた。

## 図形への収まり

両ブラウザでそれぞれ 173 ラベルを検査した。ノードやエッジラベル等の意味上のグループ内に矩形・多角形・円・楕円がある 132 ラベルは、最も面積の大きい図形を外枠として文字の外接矩形を比較した。凡例、図の見出し、枠を持たないラベル、CSS 対照図など 41 ラベルはこの検査の対象外とした。

両ブラウザとも 32 ラベルの外接矩形が枠内に完全には収まらなかった。多くはフロー図や状態図の小さいエッジラベル背景で、文字の外接矩形には文字を描かない余白も含まれる。この 32 件を、PNG と文字を除いた PNG の差分から得た文字描画画素で調べ直した。2 倍 PNG の画素の RGB 差が 16 を超えた部分を対象に、外枠を 2 画素（1 CSS px）広げた範囲から外れる例は見つからなかった。図形マスクの再確認は Chromium の座標を使った。これは余白ゼロの厳密な境界一致の検査ではない。

## 重なり

両ブラウザで、異なるラベルの非空白文字の外接矩形が縦横とも 1 CSS px を超えて交わる組は 0 件だった。Chromium の座標で、文字領域の中心・四隅・各辺の中点の 9 点で他のノード等の図形に入る候補も 0 件だった。この確認は点を標本にしており、任意の曲線との交差をすべて判定するものではない。

外枠内の区画線との距離、文字とすべての接続線の交差、任意のパスや複雑なクリップ・フィルターとの関係までは検査していない。今回の結果は保存した原稿と固定フォントの範囲で扱う。

## PNG の文字

各 PNG から、全 text 要素を除いて同じ条件で描いた画像との差分を求めた。SVG の文字ごとの境界を 1 CSS px 広げた領域で、1 倍・2 倍とも全 1,326 非空白文字に描画の寄与があった。描画の寄与がゼロとなる文字は検出されなかった。SVG と API の文字数の不一致もなかった。

この方法は文字が完全に消えている候補を探す補助検査である。隣の文字が領域に入る場合があり、画素の存在だけで文字の同一性や細い線の欠けを保証するものではない。

さらに Windows の日本語 OCR（Windows.Media.Ocr、言語 ja）で 2 倍 PNG 27 枚を読み、文字領域と行の位置を基準に SVG の期待文字列と照合した。NFKC と空白除去後に 136 ラベルが一致し、37 ラベルが不一致だった。後者には「パス」を「バス」と読む例、英数字の正規表現や記号を認識できない例、句読点・行順の違いが含まれた。

不一致の 37 ラベルは、2 倍 PNG の文字領域を期待文字列と並べた一覧で目視し、文字の欠落を認めなかった。OCR の不一致を PNG 欠落の件数には数えていない。1 倍 PNG の全文字について OCR と目視の照合をしたものではなく、微細な字形の差や他のフォント・縮小率まで検証した結果でもない。

[目視一覧 1](ocr/review-1.png) · [一覧 2](ocr/review-2.png) · [一覧 3](ocr/review-3.png) · [一覧 4](ocr/review-4.png) · [目視の記録](ocr/manual-review.json)

## 検出器の対照試験

はみ出す文字列、同じ位置に重なる文字列、opacity 0 の文字を含む図を追加した。両ブラウザではみ出しと重なりを、1 倍・2 倍 PNG で非表示文字の描画寄与ゼロを検出した。negative-fixture/ と negative-results/ に保存した。これは検出器が既知の例に反応することの確認で、任意のレイアウトの検査能力を保証するものではない。

## 保存と再実行

results/ にブラウザ別の座標、文字を除いた画像、文字ごとの画素数、外枠の再確認を保存した。ocr/ に日本語 OCR の出力、行位置を考慮した比較、目視用画像を保存した。summary.json は analyze.py で再集計できる。

再実行は Windows の PowerShell から、リポジトリのルートで行う。OCR スクリプトは UTF-8 BOM 付きで保存し、Windows PowerShell 5.1 で実行する。日本語 OCR と前回の同名フォントが必要。出力先を変えると保存済み結果を保って再検証できる。

```powershell
npm ci --prefix tests/wiki/browse
npm install --no-save --no-package-lock --prefix "$env:TEMP/pele-png-tools" @resvg/resvg-js@2.6.2
& ./tests/wiki/browse/node_modules/.bin/playwright.cmd install chromium webkit
$run = 'docs/agent-runs/2026-11-20-pele-label-validation'
$env:PELE_LABEL_RUN = Join-Path $env:TEMP ("pele-label-" + [guid]::NewGuid().ToString('N'))
$env:PELE_LABEL_OUT = Join-Path $env:PELE_LABEL_RUN 'results'
node "$run/audit.cjs"
node "$run/refine.cjs"
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$run/ocr.ps1" -OutputDirectory (Join-Path $env:PELE_LABEL_RUN 'ocr')
python -X utf8 -B "$run/analyze.py"
node "$run/review.cjs"
node "$run/negative-control.cjs"
```

保存済みの結果を再集計するときは PELE_LABEL_RUN を未設定にして analyze.py を実行する。再実行後の目視確認は一覧画像を開いて行い、manual-review.json を自動生成した検証結果とは扱わない。
