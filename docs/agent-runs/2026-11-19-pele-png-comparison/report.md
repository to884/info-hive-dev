# Pele SVG と resvg PNG の表示比較

2026-11-19。親リポジトリの main 82b9b671898134dfc6124999426edae1a0010aa4、wiki プラグイン b8596d1888035769528cb74e35bda51c9d9c40a0 で実施した。製品の render_sources を使い、実際の wiki のフロー図 3 件とシーケンス図 1 件から明暗の SVG を作った。原稿と出典は inputs.json にある。

## 変換と表示

@resvg/resvg-js 2.6.2 を使用し、YuGothR.ttc を指定してシステムフォントの自動読み込みを無効にした。1 倍は SVG の自然寸法、2 倍は両辺を 2 倍にした。Chromium 141.0.7390.37 と Windows 版 Playwright WebKit 26.0 を headless で使用し、file:// ページで各形式を並べた。390 CSS px 幅、deviceScaleFactor 1 の表示に加え、画像を 668 CSS px 幅で表示した。16 条件すべてで 3 画像の decode が完了し、pageerror はなかった。結果と寸法は results.json、manifest.json にある。

最初に Pele SVG を直接 resvg に渡したところ、明暗の PNG がそれぞれ同一のバイト列になった。フロー図のノードが黒く塗りつぶされ、文字が読めない。元の結果を raw-resvg/ に残した。SVG に含まれる CSS カスタムプロパティを解決できていないことと整合する。直接変換の結果は実用できない。

次に、比較用スクリプトで SVG のルート style にある変数を反復展開し、resvg に渡した。これは対象の図に対する試験的処理であり、一般の SVG に対応した変換器ではない。SVG は元のまま表示し、PNG は変数展開後のものを表示した。この条件では両配色の図形、矢印、文字が現れた。

画像の目視では、PNG の日本語文字が SVG より細く小さく見え、角丸も失われた。SVG のブラウザ側のフォント解決と、resvg に指定したフォントや SVG の CSS 解釈の差が混在するため、差の原因は個別に確定していない。2 倍表示の 1 倍 PNG はぼやけ、2 倍 PNG は輪郭が改善するが、文字と角丸の差は残った。図形と矢印が表示されることは代表画像で確認した。全ラベルの内容一致やクリッピングの網羅検査は行っていない。

## サイズ

対象 4 図の明暗計 8 枚の画像ファイル合計。

| 形式 | 合計バイト |
| --- | ---: |
| Pele SVG | 40,522 |
| 変数展開後 PNG 1 倍 | 202,536 |
| 変数展開後 PNG 2 倍 | 471,625 |

この結果は今回の 4 図、指定フォントと変換条件に限る。HTTP 圧縮後の転送量、メモリ、初回表示時間は測っていない。

## 保存した画像

- chromium-0-light.png は初期化判定の通常表示、chromium-1-light-zoom.png は引数の図の拡大表示。
- webkit-3-dark.png はシーケンス図の暗色表示。各図、両配色、両ブラウザの通常・拡大スクリーンショットを同じディレクトリに保存した。
- raw-resvg/ は CSS 変数の展開前の PNG とスクリーンショット。
- compare.cjs は PNG 生成とブラウザ確認のスクリプト。保存済みの SVG を読み、結果を指定した空のディレクトリに書く。実験後、結果の上書き防止、直接変換の選択、PNG 実寸の記録を加えた。
- inputs.json は図の原稿と出典、manifest.json は PNG の画素寸法・バイト数・SHA-256、results.json はブラウザでの表示寸法とエラーを記録する。

## 再実行

Windows、Node.js 24.15.0 と Playwright 1.56.1 を使用した。PowerShell でリポジトリのルートから実行する。

```powershell
npm ci --prefix tests/wiki/browse
npm install --no-save --no-package-lock --prefix "$env:TEMP/pele-png-tools" @resvg/resvg-js@2.6.2
& ./tests/wiki/browse/node_modules/.bin/playwright.cmd install chromium webkit
$env:PELE_COMPARE_MODE = 'resolved'
$env:PELE_COMPARE_OUT = Join-Path $env:TEMP ("pele-compare-" + [guid]::NewGuid().ToString('N'))
node docs/agent-runs/2026-11-19-pele-png-comparison/compare.cjs
```

直接変換を調べるときは、別の空ディレクトリを指定し、`PELE_COMPARE_MODE` を `raw` にする。Windows の `C:/Windows/Fonts/YuGothR.ttc` を使う。別のフォントやブラウザ環境では文字の見え方が変わりうる。
