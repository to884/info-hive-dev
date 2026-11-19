# Pele SVG と PNG の図種・CSS・フォント互換性

2026-11-19。親の main 5616398ce8618a9e5edcc216bf0fcd397afec86a と wiki プラグイン b8596d1888035769528cb74e35bda51c9d9c40a0 で実施した。[前回の CSS・角丸・フォント調査](../2026-11-19-pele-resvg-investigation/report.md) の範囲を広げた。

## 対象と条件

- 実際の wiki のフロー図 3 件とシーケンス図 1 件、追加の状態図・クラス図・ER 図・円グラフ・ガントチャート・マインドマップ・明示色のフロー図・条件分岐を含むシーケンス図を使った。12 原稿すべてを製品の render_sources で明暗 SVG にできた。
- CSS の継承と important による上書き、入れ子の var フォールバック、循環する変数の代替値、百分率の rx と px の ry を使う対照 SVG を 3 件加えた。計 27 画像を両ブラウザで比較した。
- Node.js と @resvg/resvg-js 2.6.2、Playwright 1.56.1 の Chromium 141.0.7390.37 と Windows 版 WebKit 26.0 を使った。
- ブラウザには NotoSansJP-Regular.otf と NotoSansJP-Bold.otf を @font-face で読み込み、400 と 700 を明示的にロードした。resvg にも同じファイルを渡し、システムフォントの読み込みを止めた。元の SVG も同じフォントで表示した。ファイルのハッシュは results/results.json にある。
- 比較は deviceScaleFactor 1、SVG の自然寸法で行った。PNG は自然寸法の 1 倍と両辺を 2 倍にした画像を作った。2 倍 PNG は自然寸法へ縮小してブラウザで比較した。閲覧時の高 DPI や拡大操作は今回の条件に含めていない。

## 変換方法と見つかった問題

Chromium が解決した塗り、線、文字のプロパティと矩形の rx・ry を各要素の SVG 属性に書き出した。CSS の変数を文字列として置き換える処理に比べ、今回の継承・上書き・循環・代替値の対照図を扱えた。スタイルシートと style 属性を取り除き、フォント名を resvg が読む Noto Sans JP にした。背景は resvg の background オプションで固定した。

最初の試作は computed style の ry の値 auto を、そのまま属性に書き出した。この場合、Chromium では状態図やマインドマップなどの角丸が失われ、WebKit では保たれた。変換前後の画素差が最も大きかったのはマインドマップで、RGB のいずれかの差が 16 を超える画素は約 4.84% だった。フォントを明示的にロードしても同じ差が残り、フォント読み込み待ちだけでは解決しなかった。rx・ry が auto の場合に属性を省くようにすると、この差は解消した。

この方法は書き出し時に Playwright と Chromium を必要とする。現在の製品の書き出し条件への組み込みは検討していない。取得するプロパティは試験対象に合わせて限定しており、一般の SVG や CSS の変換を保証するものではない。

## 結果

- 修正後の 27 画像を両ブラウザで確認した 54 条件で、変換前と属性に固定した後の SVG のスクリーンショットは RGB がすべて一致した。
- SVG の text 要素の文字列を前後で比較し、変化は検出されなかった。文字の境界が SVG の表示領域から 1 CSS px を超えて外に出る例も検出されなかった。
- 1 倍と 2 倍 PNG のデコードは両ブラウザの 54 条件で完了した。PNG の RGB には SVG との差が残った。下表は画像全体で、いずれかの RGB 成分の差が 16 を超えた画素の割合の中央値。

| ブラウザ | PNG 1 倍 | PNG 2 倍を自然寸法へ縮小 |
| --- | ---: | ---: |
| Chromium | 4.56% | 4.85% |
| Windows WebKit | 3.35% | 3.75% |

この値は知覚的な画質の点数や合否の基準ではない。ラスタライザや縮小時のアンチエイリアスの違いも含むため、割合だけで画質を順位付けしない。クラス図、ER 図、ガントチャート、明示色のフロー、注記と条件分岐を含むシーケンス図、対照図を代表例として目視した。PNG 内の全ラベルの文字認識による照合、ノード内への収まり、重なり、クリップパスやフィルターの網羅検査は未実施である。

## 画像ファイルのサイズ

Pele が生成した明暗各 12 枚、計 24 枚の合計。CSS 対照図 3 枚を除く。

| 形式 | 合計バイト |
| --- | ---: |
| 元の Pele SVG | 84,436 |
| 属性に固定した SVG | 494,449 |
| PNG 1 倍 | 362,019 |
| PNG 2 倍 | 774,573 |

属性に固定した SVG は各要素に描画値を書いた試験用の出力である。配布物の最適化、HTTP 圧縮後の転送量、メモリ、初回表示時間は測っていない。

## 保存先と再実行

- inputs.json と隣の SVG は原稿・生成状況と比較に使った Pele 出力。
- results/ は修正後の出力、スクリーンショット、PNG デコード結果、ラベルの境界と画素差。summary.json は analyze.py で再生成できる。
- explicit-auto-radius/ はフォントを明示ロードし、rx・ry の auto を属性に書いた段階の出力。first-pass-font-loading/ は明示ロード追加前の出力。同じ角丸差が残ったことの記録として保存した。
- compare.cjs は属性固定と比較、verify-png.cjs は PNG の表示確認、regenerate.py は原稿からの SVG 再生成の照合。gantt の現在時刻マーカーは生成時刻で動くため、再生成照合では pele-today グループを除いた。保存済み画像を使う比較では、元と変換後に同じマーカー位置が使われる。
- フォント本体を配布物に同梱していない。再実行には Windows の C:/Windows/Fonts に上記の同名フォントが必要。

リポジトリのルートで実行する。出力先は空のディレクトリを指定する。

```powershell
npm ci --prefix tests/wiki/browse
npm install --no-save --no-package-lock --prefix "$env:TEMP/pele-png-tools" @resvg/resvg-js@2.6.2
& ./tests/wiki/browse/node_modules/.bin/playwright.cmd install chromium webkit
python -X utf8 -B docs/agent-runs/2026-11-19-pele-png-compatibility/regenerate.py
$env:PELE_COMPAT_OUT = Join-Path $env:TEMP ("pele-compat-" + [guid]::NewGuid().ToString('N'))
node docs/agent-runs/2026-11-19-pele-png-compatibility/compare.cjs
node docs/agent-runs/2026-11-19-pele-png-compatibility/verify-png.cjs
python -X utf8 -B docs/agent-runs/2026-11-19-pele-png-compatibility/analyze.py
```

analyze.py は保存済みの results/ を集計する。新しい測定先はスクリプトの出力 JSON を直接確認する。今回の品質確認から、PNG の既定採用や性能上の優位は判断していない。
