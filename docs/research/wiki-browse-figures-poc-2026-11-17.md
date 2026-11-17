# browse の図の描画の PoC（2026年11月17日）

`/wiki:browse` のページに Mermaid の図と svg を出す方式を、試作（`poc/browse-figures/`）で 5 つのブラウザに流して確かめた記録である。方式の選択と計画は、作者が承認した計画（Mermaid は sandbox の枠で描いて `<img>` で見せる、同梱は `@mermaid-js/tiny` 12.3.0）に従った。

## 結論

- **サーバーの方式は成り立つ。** Chromium、Firefox、WebKit、Edge、Chrome の 5 つで、10 種類の図が描け、ページの CSP の違反、`[style]`、ID の重複、外への要求がどれも 0 件だった。図の側からの上書き（`htmlLabels`、`theme`、`themeCSS`、`themeVariables`）は通らなかった。配色を変えると描き直し、図の色が Fluent のトークンに追従した。
- **静的の書き出し（`file://`）では、Mermaid を描けない。** 5 つのブラウザすべてで、sandbox の枠（不透明なオリジン）が隣のファイルのスクリプトを読めなかった。枠の CSP に `file:` を足しても同じだった。静的版では、Mermaid を今と同じコードのまま出す。
- **svg は両方の方式で出せる。** `<img>` で読んだ svg は、5 つのブラウザの 2 方式で、中の `<style>` が効き、中のスクリプトは動かなかった。
- **方式に 2 つの直しが要った。** WebKit は、sandbox で不透明になった文書の `'self'` を配信元と一致させない。枠の CSP は、サーバーの応答ヘッダーだけで付け（`<meta>` を置かない）、`script-src` に配信元（`http://127.0.0.1:<ポート>`）を書き足す。

## 環境

| 項目 | 値 |
| --- | --- |
| OS | Windows 11 |
| Playwright | 1.56.1（`tests/wiki/browse/` の `npm ci`） |
| ブラウザ | Chromium 141.0.7390.37、Firefox 142.0.1、WebKit 26.0（Playwright の版）、Edge 157.0.4341.60、Chrome 157.0.8103.79 |
| Mermaid | `@mermaid-js/tiny` 12.3.0、`dist/mermaid.tiny.js` 2,852,578 バイト、SHA-256 `c41f5236091b83f524c4940f97a16b2b14a76f21ff84aea4fd6b66421d8a2a9a`。tarball の integrity（sha512）は registry.npmjs.org の公表値と一致した |
| Fluent 2 | プラグインに同梱の `browse_assets/fluent2.css`（v0.25.2 の時点） |

全部入りの `mermaid.min.js` 12.3.0 は、elkjs（EPL-2.0 OR GPL-3.0-or-later）を束の中に含んでいた（`Eclipse Layout Kernel` の文字列と、`ELK Layered` などの登録）。tiny には含まれない（同じ文字列が 0 件）。これを作者に伝え、tiny に替えた。

## 試作の方式

- ページの CSP は、今の browse の値に `frame-src 'self'` だけを足した。
- `figures.js`（親）は、`#_body pre > code.language-mermaid` があるときだけ、見えない `<iframe sandbox="allow-scripts">` を 1 つ作る。枠に図のソースと配色を `postMessage` で送り、SVG の文字列を受け取り、`data:` の `<img>` にして出す。受け取るときは `event.source` を照らす。
- 枠（`mermaid-frame.html`、`mermaid-frame.js`）は、`securityLevel: 'strict'`、`htmlLabels: false`、`theme: 'base'` で描く。`secure` に `theme`、`themeVariables`、`themeCSS`、`fontFamily`、`htmlLabels`、`darkMode`、`look` を足した。描いた SVG は `XMLSerializer` で文字にし、`viewBox` から `width` と `height` を決める。
- 配色は、親が `fluent2.css` のトークン（`--colorNeutralForeground1`、`--colorBrandBackground2`、`--colorBrandStroke1`、`--fontFamilyBase` など 21 個）を `getComputedStyle` で読み、16 進の色にして送る。暗さは背景の輝度で決める。
- 入れ物は `fui-Card`、画像は `fui-Image`、コードは Accordion の形 A（`<details class="fui-AccordionItem">`）、描けなかったときは `fui-MessageBar`（warning）。手書きの svg の入れ物には `data-theme="light"` を付けた。

## 門ごとの結果（サーバーの方式、5 つのブラウザ）

| 門 | 結果 |
| --- | --- |
| 1. 枠が `mermaid.tiny.js` を読む | 枠の `<meta>` の CSP を外し、ヘッダーの `script-src` に配信元を足した版で、5 つすべて読めた。`<meta>` に `script-src 'self'` を残した版では、WebKit だけが拒んだ（`Refused to load .../mermaid.tiny.js because it does not appear in the script-src directive`）。CSP は重なって効くので、ヘッダーに配信元を足しても `<meta>` の `'self'` で止まる |
| 2. 親の `frame-src 'self'` と `img-src` | 違反 0 件。手書きの svg の `naturalWidth` は 240 |
| 3. `'unsafe-eval'` なしで動く、隠した枠で文字を測る | 枠の違反は、外の画像の図（下の `external`）の `img-src` の 1 件だけ。枠は 1200×800 の大きさで画面の外に置いた。gantt と sequence の形は崩れなかった |
| 4. 画像の中のスタイルが効く | 厳格な CSP のページの `<img>` と、CSP のない対照のページの同じ `data:` の `<img>` を撮り比べた。上下左右 1 px のずれを許して、違う画素は 0〜0.6%（Firefox の class が 4.1%、timeline が 1.1%）。`<style>` を抜いた版とは 2.5〜61% 違った。4% と 6% の組と、大きさが 2 px 違った override の図は、目で見て同じだった |
| 4. 図の側の上書き | `%%{init}%%` で `htmlLabels`、`theme: forest`、`themeCSS`、`themeVariables` を変えようとした図で、`foreignObject` も赤の塗りも出なかった。`<b>` は文字のまま出た |
| 4. 図の種類 | flowchart（`<br>` の改行を含む）、sequence、state、class、ER、gantt、timeline、pie、accTitle つきの flowchart が描けた。mindmap は tiny にないので失敗し、コードと警告が残った |
| 5. `postMessage` | 往復でき、`event.source` で枠のほかからの送り主を捨てた |
| 6. 枠の中の違反を数える | 枠が自分で数えた件数と、Playwright で枠を評価した件数が、5 つで一致した（1/1）。違反のイベントは非同期に届くので、枠は描き終えてから 100 ms 待って件数を返す |
| 7. 外へ出ない | 外への要求は 0 件。`img: "https://..."` の節点を持つ図は、枠の `img-src data:` が画像を止め、Mermaid が「画像を decode できない」で失敗した。コードと警告が残った。`click ... href` は strict で無効になった |
| 8. `[style]`、ID、配色 | 親の `[style]` は 0 件、ID の重複は 0 件。`data-theme` を `dark` にすると描き直し、図の背景が `#292929`（`--colorNeutralBackground1` の暗い値）になった。手書きの svg の入れ物は明るいまま |
| 9. 構文の誤り | 描けず、コードと警告（`fui-MessageBar`）が残った |
| 10. 時間 | 下の表 |

撮り比べの値は、試験の都合で入れ物に `style` を付けてから外したので、試験の後半の `[style]` の数（Chromium 系で 11）は試験が作ったものである。撮る前の値は 5 つとも 0 件だった。WebKit は、撮るたびに Playwright のスタイルシートを CSP が拒む（既知。`wiki/concepts/browseの画面の確かめ方.md`）。

## 時間（サーバーの方式、ページを開いてから）

| ブラウザ | 枠の準備（ms） | 最初の図（ms） | 13 個を描き終える（ms） |
| --- | --- | --- | --- |
| Chromium | 1,746 | 2,129 | 2,230 |
| Firefox | 323 | 662 | 752 |
| WebKit | 179 | 627 | 732 |
| Edge | 170 | 577 | 834 |
| Chrome | 146 | 603 | 708 |

Chromium は、その回で最初に起動したブラウザで、ほかの回（115〜187 ms）より準備が遅かった。応答は `no-store` なので、Mermaid のあるページを開くたびに 2.85 MB を取り直す。

1 回目の流しでは、Chrome の gantt が 1 度だけ「不正な応答」で失敗し、コンソールに `<rect> attribute width: A negative value` が出た。同じ Chrome で gantt だけを描き直した試し（`debug_gantt.mjs`）と、その後の 2 回の流しでは再現しなかった。原因は分かっていない。

## file:// の方式

| 確かめたこと | 結果（5 つすべて） |
| --- | --- |
| 枠が隣の `mermaid.tiny.js` を読む | 読めなかった。Chromium 系と WebKit は `Not allowed to load local resource`、Firefox は `Security Error: Content at moz-nullprincipal:... may not load or link to file:///...` |
| 枠の CSP に `file:` を足す | 同じ。CSP ではなく、不透明なオリジンから `file:` を読むことをブラウザが止めている |
| 手書きの svg の `<img>` | 出た。対照との違いは 0% |
| svg のファイルを直接開く | 中のスクリプトが動いた（`onload`）。ページから svg へのリンクを作らない |

`allow-same-origin` を足して枠を不透明でなくする案は試していない。枠の中の Mermaid の欠陥が親の文書に届く道を開くので、計画で退けた。

## サーバーで svg を直接開く

`Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` を付けて返すと、5 つすべてで中のスクリプトが動かなかった（コンソールに `Blocked script execution ... sandboxed`）。

## 確かめていないこと

- 実機の Safari（macOS）。Playwright の WebKit は Safari と同じではない。
- Linux の WebKitGTK と、アプリの方式（独自スキーム）。
- 印刷とハイコントラスト。
- 大きな図（節点が数百）や、図が数十あるページの時間。
- Chrome の gantt の 1 度の失敗の原因。
