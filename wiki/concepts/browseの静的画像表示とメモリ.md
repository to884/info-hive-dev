---
type: "concept"
kind: "experience-pattern"
status: "supported"
title: "browse の静的画像表示とメモリ"
tags: ["browse", "試験", "windows"]
sources: ["browseの静的描画の調査記録-2026-11-19", "browseの図の描画とリリース-wiki-0.26.0-0.27.0"]
created: 2026-11-19
updated: 2026-11-19
---

# browse の静的画像表示とメモリ

Windows 版 Playwright WebKit で合成フローチャート 50 図を明暗 2 配色で表示した。閲覧時に Mermaid を再実行すると、同じタブで配色を切り替えるたびに私有コミットが GiB 単位で増えた。事前生成した SVG と PNG を `<img>` で表示すると、10 周とも観測ピークが 862 MiB 未満だった。製品の静的版は Pele の SVG を採用した。 [採用方式](../../docs/adr/0035-wiki-browse-prerenders-diagrams-with-pele.md) [測定条件と結果](../../docs/research/wiki-browse-static-svg-vs-png-2026-11-19.md)

## 繰り返し表示を比較する

1. 配色の切り替えと記事の往復を別々に測る。同じタブでも、記事に戻ると文書が作り直されることがある。文書と Web プロセスの寿命を記録する。
2. 描画前、表示中、各周の待機後の私有コミットを採る。ピークは採取した標本の最大値とし、絶対値、描画前との差、開始時のプロセス構成を保存する。SVG の 2 回目は描画前の GPU プロセスが約 32 MiB 小さかった。開始値を引くと PNG のピーク増分は両方の反復で約 30 MiB 小さかった。 [測定の集計](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/ten-rounds/summary.json)
3. メモリの保持先を調べるときは、画像解放、GC、空白ページへの移動、追加 GC、タブ終了を区別する。Chrome・Edge と Chromium Headless Shell では同じ描画枠のプロセス配置が異なった。Windows WebKit ではアドレス範囲ごとに稼働中の割り当てと空きを照合すると、追加 GC 後に残った増分の約 81% が libpas の空きと分かった。
4. 画像形式の比較では、同じ SVG から同じ寸法の PNG を生成し、両配色の全画像をデコードしたことを確認する。初回の先頭図と、同じ URL を再表示した後の先頭図は別に集計する。今回の PNG は合計 77.6% 小さかったが、初回のデコード時間にはばらつきがあり、代表図の表示には文字や縁の差があった。 [画像の記録](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/images/manifest.json) · [初回の集計](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/first-round/summary.json)

## 閲覧時に Mermaid を動かす場合

静的版の `relay-srcdoc` 試作では、描画枠に渡す情報をその図の入力と設定に絞り、図ごとの枠を 1 組ずつ作って破棄した。60 項目が通った範囲は単独の最上位ページである。埋め込みと `opener` を含む入口では別ページをまたぐ反例があり、サーバー版ではこの検証を受け、タブ間の排他制御と入口の制限を追加した。 [サーバー版の設計](../../docs/adr/0030-wiki-browse-shows-figures-as-images.md)

可視の 4 図だけを先に描く試作では、一括描画と比べて待機後の保持量が `srcdoc` で 5.30 から 1.40 GiB、Blob で 3.89 から 1.28 GiB に下がった。明暗を戻したときに画像を再利用する試作では、同一文書内で 50 図のキャッシュが当たり、再描画は 0.23 秒以内だった。文書が作り直されるとキャッシュも失われた。

## 次のセッション

SVG／PNG 比較の報告、原標本、集計スクリプト、再測定用画像は親リポジトリに保存した。親リポジトリのルートで次の2件を再集計できる。 [保存した原標本と画像](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/)

```powershell
$run = 'docs/agent-runs/2026-11-19-wiki-static-svg-vs-png'
python -X utf8 -B "$run/analysis/analyze-figure-followup.py" "$run/ten-rounds/results.json"
python -X utf8 -B "$run/analysis/analyze-figure-followup.py" "$run/first-round/results.json"
```

再測定は Windows の PowerShell で親リポジトリのルートから行う。前回は Node.js 24.15.0、Playwright 1.56.1 の Windows 版 WebKit 26.0（リビジョン 2215）を使った。各形式で専用ブラウザを起動し、同じ文書で明暗各50枚を10周表示する。各形式を2回測り、2回目は順序を逆にする。暗色表示後は5秒待つ。手動 GC は使わない。 [測定スクリプト](../../poc/browse-static-image/performance-experiment.mjs) · [11 月 18 日の測定レビュー](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/2026-11-18-repeat-tab-review.md)

Playwright を準備する。WebKit の取得先はこの測定用のディレクトリにする。

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location).Path 'poc/browse-static-image/out/browsers'
npm ci --prefix tests/wiki/browse
& './tests/wiki/browse/node_modules/.bin/playwright.cmd' install webkit
```

保存済みの画像を展開し、今回の標本を新しいディレクトリに書き出す。OS 全体のコミット余力が 4 GiB 未満になった場合や、標本が15秒以上更新されない場合は、測定専用ブラウザを止めて以後のケースを打ち切る。採取済みの標本と停止理由を確認できる。 [再測定用 ZIP](../../docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/static-image-assets-r2-20261119.zip)

```powershell
$run = 'docs/agent-runs/2026-11-19-wiki-static-svg-vs-png'
$work = Join-Path ([IO.Path]::GetTempPath()) ('wiki-static-image-' + [guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath "$run/static-image-assets-r2-20261119.zip" -DestinationPath (Join-Path $work 'fixture')
$env:STATIC_IMAGE_FIXTURE = Join-Path $work 'fixture'
$env:PERF_OUT = Join-Path $work 'results'
$env:COUNTS = '50'
$env:ROUNDS = '10'
$env:REPEATS = '2'
$env:IDLE_MS = '5000'
$env:MIN_COMMIT_HEADROOM_MIB = '4096'
node poc/browse-static-image/performance-experiment.mjs
python -X utf8 -B "$run/analysis/analyze-figure-followup.py" "$env:PERF_OUT/results.json"
```

時間は先頭画像と全画像の `img.decode()` が解決するまでを記録する。この版の WebKit は SVG のラスタライズを待たず、PNG ではビットマップのデコードを待つ。測定では画面外の画像にも `decode()` を呼ぶため、時間とメモリはこの表示条件での値として扱う。 [測定に使った WebKit の実装](https://github.com/WebKit/WebKit/blob/db897909f7c31d9b38793374c66427b6a4cb3dd3/Source/WebCore/loader/ImageLoader.cpp#L550-L575)

将来 PNG を検討する場合は、対象の図種・拡大時の画質・初回表示を確かめる。CairoSVG との実測比較は未着手。実機 Safari は依頼により検証対象から外した。Windows の領域別コミットに現れなかった 7.34〜8.20 MiB をページテーブルの課金と確定するには、カーネルのカウンターを直接読む測定が残っている。

## 関係するページ

- [[browseの静的描画の調査記録-2026-11-19]]
- [[browseの画面の確かめ方]]
- [[browseの図の描画とリリース-wiki-0.26.0-0.27.0]]
