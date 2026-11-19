# Pele SVG の resvg 変換とフォントの調査

2026-11-19。親リポジトリの main 491bce00216405c96b82ffb825f273cb8b5239b1 で実施した。前回保存した 4 図のうち、初期化判定のフロー図とツール利用のシーケンス図を使い、明暗各 2 枚を比較した。変換は Windows の @resvg/resvg-js 2.6.2、ブラウザは Playwright 1.56.1 の Chromium 141.0.7390.37 と Windows 版 WebKit 26.0 を使った。元の SVG と前回の条件は [比較報告](../2026-11-19-pele-png-comparison/report.md) にある。

## CSS 変数

元の SVG を resvg に直接渡すと、明色と暗色の PNG がそれぞれ同じ SHA-256 になり、図形が黒くなった。前回と同じくルート style のカスタムプロパティとフォールバックを試験的に反復展開すると、図の明暗色が分かれた。resvg の色に対する var のサポートは上流の未解決課題でもある。 [resvg issue #821](https://github.com/linebender/resvg/issues/821)

試作の展開処理はこの標本のルート変数を対象にした文字列置換で、CSS の継承、入れ子、循環、複雑な値、上書きや不正入力を一般に扱うものではない。製品で使うには、Pele の出力を限定して検証するか、CSS の構文とカスケードを扱う実装が必要になる。

## 角丸

変数展開後の `style="rx:4px"` の矩形は、resvg の中間 SVG で角丸を持たないパスになった。同じ矩形に `rx="4"` を書くと、角丸のあるパスになり、生成画像でも角丸を確認した。今回の処理は値が単純な px の矩形に限って変換した。複数の宣言、単位、ry、値の継承などを一般に扱うものではない。

## 文字

前回の resvg はシステムフォントの自動読み込みを止め、YuGothR.ttc だけを登録していた。今回 Chromium の SVG をインラインで調べると、代表ラベルの computed font-weight は 400、font-size は 14px で、実際のグリフには Noto Sans JP Regular が使われていた。Windows の YuGothR.ttc に含まれる Yu Gothic Regular も weight 400 であり、指定された太さが異なるとは限らない。

resvg に NotoSansJP-Regular.otf を読み込ませると、同じ weight のまま PNG の文字の形と濃さが変わり、代表図では Chromium の表示に近づいた。Yu Gothic の regular と medium・bold でも PNG のハッシュが変化した。4 つの Yu Gothic ファイルを登録した場合は regular 単独と同じ PNG だった。書体の違いが前回の見た目の差に寄与したことを示すが、差のすべてや別環境の原因を確定するものではない。WebKit では computed font-family と weight を読んだが、実際に使用したフォントの特定は行っていない。SVG の表示フォントは閲覧環境に依存する。

## 背景

今回の resvg PNG は背景が透明だった。前回の比較ページではページ側の背景色の上に載っていた。resvg-js の `background` に明暗の色を指定すると、代表図 2 枚で色付き背景を生成できた。透過と背景固定のどちらを使うかは画像の利用条件で決める必要がある。

## 再現と保存

`results/` に変換画像、resvg の中間 SVG、ブラウザのスクリーンショットと結果 JSON を収めた。Noto と Yu Gothic のファイルの SHA-256 は `font-hashes.json` にある。フォント本体は含めていない。再実行時は Windows の `C:/Windows/Fonts` に同名フォントが必要。

PowerShell で親リポジトリのルートから実行する。

```powershell
npm ci --prefix tests/wiki/browse
npm install --no-save --no-package-lock --prefix "$env:TEMP/pele-png-tools" @resvg/resvg-js@2.6.2
& ./tests/wiki/browse/node_modules/.bin/playwright.cmd install chromium webkit
$env:PELE_PROBE_OUT = Join-Path $env:TEMP ("pele-probe-" + [guid]::NewGuid().ToString('N'))
node docs/agent-runs/2026-11-19-pele-resvg-investigation/probe.cjs
```

28 条件の PNG のハッシュと、代表フロー図の背景付き PNG 2 枚は再実行で一致した。ブラウザでの目視は代表画像に限る。残りの図種やラベル、文字の折り返し、他の OS・フォント環境、配布時のフォントライセンスは未検証。
