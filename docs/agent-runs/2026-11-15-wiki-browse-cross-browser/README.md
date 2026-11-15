# browse の画面を 5 つのブラウザで確かめた記録（2026-11-15）

wiki 0.19.0 と 0.18.0 のリリースで残した「Chromium のほかのブラウザでの確かめ」を行った記録である。対象は `info-hive-wiki` の `6d712a8`（0.19.1）である。

## 何をしたか

1. ブラウザの試験 `browse.test.mjs` と `findability.test.mjs` を、Firefox、WebKit、Edge、Chrome のそれぞれで、静的（`file://`）とサーバー（`http://127.0.0.1`）の両方の方式で流した（`run.sh`）。Chromium は CI で流している。
2. この開発リポジトリの wiki（41 ページ）を静的に書き出し、索引と記事のページ 2 つを、5 つのブラウザで撮った（`shoot.mjs`）。配色はライトとダーク、幅は 1280 と 360 である。撮った 60 枚を、ページと配色と幅ごとに 5 つを横に並べた 12 枚にまとめ（`sheet.py`）、目で見比べた。
3. 落ちた試験の原因を、`probe.mjs` で切り分けた。

道具の版: Node 24.15.0、Playwright 1.56.1（Firefox は `firefox-1495`、WebKit は `webkit-2215`）。Edge と Chrome は、この PC に入っている版を `channel` で使った。

## 試験の結果

| ブラウザ | `browse.test.mjs` | `findability.test.mjs` | 原本 |
| --- | --- | --- | --- |
| WebKit | 失敗 0 | 失敗 0 | `browse-webkit.json`、`findability-webkit.json` |
| Firefox | 静的で 1 件 | 静的で 3 件。サーバーは失敗 0 | `browse-firefox.json`、`findability-firefox.json` |
| Edge | 失敗 0 | サーバーで 1 件 | `browse-msedge.json`、`findability-msedge.json` |
| Chrome | 失敗 0 | サーバーで 1 件 | `browse-chrome.json`、`findability-chrome.json` |

所要時間は、4 つを同時に流して `findability.test.mjs` が 4〜8 分、`browse.test.mjs` が 30 秒前後だった（`summary-*.txt`）。

### Firefox の静的の 4 件は、試験の道具の制約

落ちたのは、次の 4 件である。

- `browse.test.mjs`: 世代の不一致を知らせない
- `findability.test.mjs`: フォーカスしても `search.js` を読まない、読めない検索の索引の表示、遅れて届く検索の索引の扱い

どれも、`page.route` で `file://` の要求を差し替えるか、`page.on("request")` で `file://` の要求を見る試験である。`probe.mjs` で、Firefox の Playwright が `file://` の要求を 1 件も見ないこと（Chromium は 8 件、Firefox は 0 件）を確かめた。同じ確かめは、Firefox のサーバーの方式ではすべて通った。画面のふるまいは Firefox でも同じで、`file://` での差し替えだけが試験できない。0.19.0 の記録で「確かめてはいない」とした 3 件は、これで原因が分かった。

### Edge と Chrome のサーバーの 1 件は、ファビコンの 404

コンソールのエラーは `Failed to load resource: the server responded with a status of 404 (Not Found)` で、URL は `http://127.0.0.1:<ポート>/favicon.ico` だった（`probe.mjs`）。Playwright に同梱の Chromium はファビコンを要求しないので、CI では出ない。製品の Edge と Chrome は、ページが `<link rel="icon">` を持たないと `/favicon.ico` を要求し、サーバーが 404 を返す。画面は壊れないが、利用者のブラウザの開発者ツールに毎回エラーが出る。0.19.3 で直した（下の「直し」）。

## 直し（0.19.3）

閲覧のページ（`wiki_browse_core.py` の `_head`）と、サーバーの「見つからない」のページ（`wiki_browse.py`）の `<head>` で、`<link rel="icon" href="data:,">` を出し、アイコンがないことを宣言した。CSP は変えていない（`img-src 'self' data:`）。

- 直したあと、`browse.test.mjs` と `findability.test.mjs` は、Chromium、Chrome、Edge、WebKit（両方の方式）と Firefox（サーバーの方式）で、失敗 0 だった（`after-fix/`）。
- 製品の Chrome と Edge で、エラーの画面を `probe-errors.mjs` で開いた。
  - 404 の HTML: `/favicon.ico` を要求しなくなった。コンソールには、文書そのものの 404 だけが出る。
  - 503 のテキスト（組み立てられないとき）: 今までどおり `/favicon.ico` を要求し、404 になる。テキストの応答は宣言を持てない。文書そのものの 503 のエラーもコンソールに出る画面なので、範囲の外とした。500 も同じである。

### Sol のレビュー

Sol の敵対的レビューを 1 回受けた（`favicon-review-1.md`）。致命と重大は 0 件だった。

| 指摘 | 扱い |
| --- | --- |
| 503 と 500 のテキストの画面では、要求が残る（推測） | 測って確かめた（上）。残るが、その画面は応答そのもののエラーがもともと出る。どの画面でも出ないことを約束するには、トークンのないパス（`/favicon.ico`）にサーバーが答える必要があり、要求の境界（構造の直しの設計 8.1）を変える。0.19.3 の約束は、ふつうに描いたページと 404 の HTML にとどめ、CHANGELOG に書いた |
| 404 の HTML に CSP の `<meta>` がない | 直す前からで、HTTP のヘッダーで CSP を出している。範囲の外とした |
| 試験が 503 と 500 の経路を捕まえない | 上のとおり約束の外なので、試験も足さない。ブラウザの要求そのものは、CI の Chromium が要求しないので、CI では捕まえられない |

## 画面の見比べ

- 5 つのブラウザとも、`[style]` は 0 件、幅 360 でも横のはみ出しは 0 だった（`shots-report.json`）。
- `data-theme` はどれも `auto` で、地の色はライトが `rgb(255, 255, 255)`、ダークが `rgb(41, 41, 41)` で同じだった。
- 配置、色、部品の形に、ブラウザごとの違いは見えなかった。WebKit だけ、日本語の行の高さがわずかに詰まる。代わりの書体の違いで、崩れではない。
- WebKit では、撮るたびにコンソールに CSP の違反（`Refused to apply a stylesheet ...`）が出る。ページを読み込んだだけでは出ず、`page.screenshot` のあとにだけ出るので、Playwright が撮影のときに足すスタイルシートが拒まれたものである。

撮った画像は大きい（12 枚で 4.5 MB）ので、リポジトリには入れていない。`shoot.mjs` と `sheet.py` で作り直せる。

## 確かめていないこと

- 手で操作する確かめ（キーボードでのフォーカスの移動、IME での実際の入力、印刷）は、自動の試験の範囲を超える分を行っていない。
- 強制カラーの画面は撮っていない。`findability.test.mjs` の強制カラーの確かめが、各ブラウザでどこまで効いているかも調べていない。
