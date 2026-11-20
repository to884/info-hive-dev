# Pele SVG と 1 倍・2 倍 PNG の性能比較

2026-11-20。親の main ccc36dd3c029b5a5ce3a71a1b914e6eafe40217c と wiki プラグイン eae9a19c8ffd7fecdb89e3eadb31a38160ec2c6d で実施した。書き出しには製品の Pele を使った。

## 原稿と比較する方式

前回と同じ合成フロー図 50 件を使った。原稿 JSON の SHA-256 は f882a73df7f2836ca48331909d35c7d2941b874c0709015fb59a202fbfcf1741。各図は「入力 i」「判定」「保存」の 3 ノードで、明暗各 50 枚を生成した。実際の多様な図種を扱った [ラベル検証](../2026-11-20-pele-label-validation/report.md) とは試料が異なる。

現行の Pele SVG に加え、Chromium が解決した 23 プロパティと font-family を、継承や要素ごとの必要性を絞らず各要素の属性に固定し、auto の rx・ry を省いた SVG を生成した。固定後の SVG に背景の矩形を加え、同じ SVG から resvg-js 2.6.2 で自然寸法の PNG と、両辺を 2 倍にした PNG を作った。元 SVG の自然寸法は 319 × 68 または 334 × 68 px。画像の表示寸法は 4 方式で一致させた。変換用のフォントは NotoSansJP-Regular.otf と NotoSansJP-Bold.otf を使い、SHA-256 を記録した。画像として開く SVG は指定した Noto Sans JP を含む端末のフォント環境を使う。実際に選ばれたフォントファイルの特定は行っていない。

現行 SVG は採用中の方式の基準である。形式を比較する組は、描画属性固定 SVG（今回の試作） とそこから生成した PNG とする。現行 SVG との間には属性の重複、style と CSS 変数の除去、背景の矩形の追加が同時にある。数値はこの書き出し方の結果であり、属性固定という手法一般のコストは示していない。

## 測定条件

- Playwright 1.56.1 の Windows 版 WebKit 26.0、file:// のページを使った。viewport は 1200 × 900 CSS px。
- ケースごとに新しい専用ブラウザを起動し、同じ文書・同じタブで明暗各 50 枚を 10 周表示した。各方式を 2 反復し、2 回目は方式の順を逆にした。暗色のデコード後に 5 秒待機し、同じ画像 URL を再利用した。GC は要求していない。
- 全 50 枚に img.decode() を呼び、全画像の自然寸法、表示寸法、URL を照合した。2 倍 PNG の自然寸法と CSS 寸法は別々に確認した。
- 専用ブラウザと列挙できた子プロセスの私有コミットを採取した。主な比較値は、最初の明色差し替え処理の開始から 10 周目の待機後の確認までに採取を開始・完了し、子プロセスの列挙漏れがない全標本の最大値である。フェーズをまたぐ境界標本も含め、描画前との差を求めた。標本間隔の中央値はケースごとに 0.269〜0.281 秒、最大は 0.407 秒だった。安定した描画中フェーズの標本は各ケース 0 件で、一時的な描画中の真のピークは測れていない。
- OS 全体のコミット余力が 4 GiB 未満、監視標本が 15 秒以上更新されない場合は専用ブラウザを止める既存の処理を使った。全 8 ケースが正常終了し、途中の打ち切りはなかった。
- メモリ測定ではスクリーンショットを取得しなかった。別走行で初回の先頭画像を取得した。画像ファイルはハッシュ照合等で事前に読んでおり、OS のファイルキャッシュを消去していない。使用中の端末での測定である。

## 観測したメモリ

単位は MiB。2 反復の値と中央値を示す。

| 方式 | 観測最大の増分 1 回目 | 2 回目 | 中央値 | 安定標本のみの最大増分中央値 | 10 周目の待機後の増分中央値 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 現行 Pele SVG | 1.93 | 1.62 | 1.78 | 0.35 | -4.30 |
| 描画属性固定 SVG（今回の試作） | 31.20 | 30.98 | 31.09 | 29.61 | 25.39 |
| PNG 1 倍 | 35.39 | 35.49 | 35.44 | 34.95 | 26.83 |
| PNG 2 倍 | 98.91 | 99.45 | 99.18 | 98.24 | 91.83 |

現行 Pele SVG の 1 回目は描画前の私有コミットが 766.33 MiB で、他ケースは約 798 MiB だった。最初の WebKitNetworkProcess の描画前の値が約 32 MiB 小さかった。表では各ケース内の開始値を引いた。待機後に開始値を下回るケースもあり、待機中の割り当ての減少も差分に含まれる。

各ケースで、各周の待機後に観測した WebKitWebProcess の PID は同じだった。この条件では、境界標本を含む観測最大の増分は 1 倍 PNG が今回の SVG 試作より約 4.35 MiB、2 倍 PNG が約 68.09 MiB 大きかった。現行 SVG と今回の試作の差について、属性の重複、背景の矩形、CSS の除去の寄与は切り分けていない。

WebKitWebProcess だけの増分も示す。全プロセスの合計とは、他のプロセスの増減が混ざる範囲が異なる。絶対値の中央値は参考値として summary.json に残し、方式間の比較には使っていない。

| 方式 | Web プロセスの観測最大増分中央値 | 10 周目の増分中央値 |
| --- | ---: | ---: |
| 現行 Pele SVG | 1.38 | -2.19 |
| 描画属性固定 SVG（今回の試作） | 31.76 | 27.46 |
| PNG 1 倍 | 36.55 | 29.62 |
| PNG 2 倍 | 100.26 | 94.55 |

比較する最大値は明暗を一度ずつ表示した後の保持も含む。全画像の初回明色 decode() 後と、暗色への差し替え後の値は memory/ のチェックポイントで区別できる。

## 初回のデコードと描画確認

メモリ測定の先頭図の decode() 完了時間と、別走行での先頭図のスクリーンショット取得完了時間を示す。単位は ms。値は 2 回分を並べる。

| 方式 | 初回明色 decode() | 明色の画像取得完了 | 暗色の画像取得完了 |
| --- | ---: | ---: | ---: |
| 現行 Pele SVG | 110、115 | 456、344 | 302、324 |
| 描画属性固定 SVG（今回の試作） | 126、161 | 407、379 | 338、355 |
| PNG 1 倍 | 90、108 | 339、339 | 305、309 |
| PNG 2 倍 | 86、97 | 363、364 | 290、263 |

スクリーンショットの時間は、API 呼び出し、50 枚の画像作成と読み込み、全画像の decode()、2 回の animation frame、先頭画像の取得と転送を含む。ページ自体を開く時間は除いた。初めて画面に出た瞬間の時刻は求めていない。自動の非背景画素の検査は矩形だけでも通るため、取得した代表画像で「入力 0」「判定」「保存」と矢印を目視した。各方式・配色の 2 反復の取得画像は画素単位で同じで、現行 SVG と今回の試作 SVG の先頭図も同じ画素だった。paint/validation.json に照合結果を保存した。

この版の WebKit では SVG の decode() はラスタライズ完了前に解決し得る。画面外の PNG にもデコードを要求するため、画像形式ごとの処理の範囲にも差がある。decode() の値をそのまま描画完了の速度比較には使わない。2〜10 周目の先頭図 decode() の中央値は 4 方式とも 6 ms だった。このデータでは先頭図と全画像の decode() 時間が近接しており、50 枚を同時に読み込む処理の完了目安として扱う。2 反復の結果から初回表示の優劣は確定しない。

## 画像ファイルのサイズ

明暗各 50 枚、計 100 枚の合計バイト数。gzip と Brotli はファイルごとに圧縮した合計で、gzip level 9、Brotli quality 11 を指定した。HTML・CSS・HTTP ヘッダーを含めていない。実際の HTTP 通信量と通信時間は未測定。

| 方式 | 元の画像 | gzip | Brotli |
| --- | ---: | ---: | ---: |
| 現行 Pele SVG | 226,460 | 85,323 | 71,133 |
| 描画属性固定 SVG（今回の試作） | 1,017,160 | 86,075 | 68,011 |
| PNG 1 倍 | 331,384 | 307,307 | 304,890 |
| PNG 2 倍 | 702,724 | 584,494 | 582,895 |

この 50 図では、現行 Pele SVG の観測最大のメモリ増分と画像ファイル合計が最も小さかった。PNG 1 倍への変更を支えるメモリや配布サイズの利点は得られなかった。2 倍 PNG は 1 倍よりメモリとファイルサイズを増やした。図種・寸法・表示範囲が変わる場合の結果は、この実験から一般化しない。

## 保存と再実行

- sources.json は原稿、fixture/ は 4 方式の画像と寸法・SHA-256 のマニフェスト。regenerate.py で現行の製品処理と Pele SVG 100 枚を照合できる。
- memory/ は 8 ケースの原標本、チェックポイント、監視用の制御・最終状態と実行条件。測定スクリプト・画像・フォントのハッシュとブラウザのインベントリーを含む。測定中の入力の一致を確認済み。
- paint/ は別走行の画像と初回時間。converter-environment.json は resvg-js の版とネイティブライブラリの SHA-256。フォント本体は含めていない。
- summary.json は境界標本を含めた analyze.py の集計。summary-stable-only.json はレビュー前の安定標本だけの集計として残した。asset-sizes.json は asset-sizes.cjs で再生成できる。
- preparation-recheck.json は版とハッシュの記録を加えた生成処理で再生成し、元の 400 画像のハッシュがすべて一致した記録。測定時のマニフェストは変更していない。
- poc/browse-static-image/pele-performance-experiment.mjs は保存済みの performance-experiment.mjs の採取処理を基にしている。4 方式の読み込みと寸法検証は pele-image-fixture.mjs で行う。元の 2 方式用スクリプトは維持した。

Windows の PowerShell でリポジトリのルートから実行する。実測時の Node.js と OS・CPU は memory/results.json にある。ブラウザは事前に用意する。

```powershell
npm ci --prefix tests/wiki/browse
npm install --no-save --no-package-lock --prefix "$env:TEMP/pele-png-tools" @resvg/resvg-js@2.6.2
& ./tests/wiki/browse/node_modules/.bin/playwright.cmd install chromium webkit
$run = 'docs/agent-runs/2026-11-20-pele-png-performance'
python -X utf8 -B "$run/regenerate.py"
$work = Join-Path $env:TEMP ("pele-perf-" + [guid]::NewGuid().ToString('N'))
$env:PELE_PERF_FIXTURE = Join-Path $work 'fixture'
node "$run/prepare.cjs"
$env:STATIC_IMAGE_FIXTURE = $env:PELE_PERF_FIXTURE
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA 'ms-playwright'
$env:PELE_PERF_RUN = $work
$env:PAINT_OUT = Join-Path $work 'paint'
node "$run/paint-check.mjs"
$env:PERF_OUT = Join-Path $work 'memory'
$env:COUNTS = '50'
$env:ROUNDS = '10'
$env:REPEATS = '2'
$env:IDLE_MS = '5000'
$env:MIN_COMMIT_HEADROOM_MIB = '4096'
node poc/browse-static-image/pele-performance-experiment.mjs
python -X utf8 -B "$run/analyze.py"
node "$run/asset-sizes.cjs"
node "$run/validate-paint.cjs"
```

PELE_PERF_RUN が未設定の場合、集計スクリプトはこのディレクトリの保存済み標本を読む。

## レビュー

[Opus の初回レビュー](review-opus.md) は REJECTED だった。境界標本を含む再集計、Web プロセスの増分、試作に限定した解釈、生成物の再現確認と時間指標の定義を反映した。指摘ごとの判断は [対応記録](review-response.md) に残した。修正後の再レビューは実施していない。

## 保存後の確認

保存した原標本から summary.json、asset-sizes.json、paint/validation.json を再生成し、すべて同じ内容になった。測定入力 408 件の SHA-256 と、製品から再生成した Pele SVG 100 枚も一致した。JavaScript 6 ファイルの構文検査は通った。原標本は採取時の CRLF を維持し、改行を考慮した git -c core.whitespace=cr-at-eol diff --cached --check も通った。wiki lint のページ検査は変更前と同じで、リンク切れ・サイズ超過はなく、既存の孤立ページ 1 件が残る。原本の版の未確認 86 件と原本パスの未確認 48 件は今回の修正対象に含めていない。[検証記録](verification.json)
