# ADR-0030：`/wiki:browse` は図を画像として見せ、Mermaid はサーバーの方式でだけ sandbox の枠で描く

| 項目 | 内容 |
| --- | --- |
| 状態 | 提案 |
| 決定日 | （承認の日を入れる） |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0002（必要なときだけ起動するサーバー）、ADR-0005（図は mermaid と svg で書く）、ADR-0010（閲覧の中核と届け方を分ける）、ADR-0016（第 1 段階は 2 方式で合格とする）、ADR-0021（Fluent 2 を再現した CSS）、[図の描画の設計](../plans/wiki-browse-figures-2026-11-17.md)、[PoC の記録](../research/wiki-browse-figures-poc-2026-11-17.md) |

## 背景

ADR-0005 は、知識ページの図を mermaid のフェンスと `wiki/assets/<スラッグ>-NN.svg` で書くと決め、`/wiki:browse` での表示を将来の作業にした。作者が、この表示を足すことを求めた。

browse のページは、`style-src 'self'` と `script-src 'self'` の CSP の下で、インラインの `style` とスクリプトを出さずに描く。試験は `[style]` と CSP の違反が 0 件であることを数える。Mermaid は、描いた SVG に `<style>` 要素と `style` 属性を入れ、CSP 向けの設定を持たない。過去には、図のソースから CSS やスクリプトを注入できる欠陥が何度も見つかっている。Mermaid 自身の `securityLevel: 'sandbox'` は data: の iframe を使い、親の CSP を継承するので、スタイルが止まる。

## 決定

| 項目 | 決定 |
| --- | --- |
| svg | `wiki/assets/` の直下の svg を入力に加え、`![説明](../assets/<名前>.svg)` を `<img>` で見せる。2 方式で表示する。サーバーは svg を `image/svg+xml` と CSP の `sandbox` を付けて返す。svg へのリンクは作らない |
| Mermaid の描き方 | ページの中では描かない。同梱の枠の文書を、見えない `<iframe sandbox="allow-scripts">` で読み、その中で Mermaid を `securityLevel: 'strict'`、`htmlLabels: false` で描く。親は SVG の文字列を受け取り、DOM に入れず、`data:` の `<img>` にして見せる |
| 描く方式 | サーバーの方式でだけ描く。静的の書き出し（`file://`）では、ブラウザが sandbox の枠に隣のファイルのスクリプトを読ませないので、今と同じコードを出す |
| CSP | 応答の種類ごとに決める。ページは今の値に `frame-src 'self'` だけを足す。枠の文書だけが `style-src 'unsafe-inline'` を許し、`script-src` に配信元を書き、`sandbox allow-scripts` を付ける（ヘッダーだけ。`<meta>` を置かない）。svg は `default-src 'none'; style-src 'unsafe-inline'; sandbox` |
| 画面の契約 | `figures.js` が iframe を 1 つ作り、`postMessage` でやり取りすることを足す。どちらも classic な `<script src>` で読む。要素の `style` に触らない約束は保つ |
| 同梱 | `@mermaid-js/tiny` 12.3.0（MIT）を書き換えずに同梱する。全部入りの版は、EPL-2.0 OR GPL-3.0-or-later の elkjs を含むので使わない |
| 見た目 | `fluent2.css` の部品（Card、Image、Accordion、MessageBar）とトークンで組む。Mermaid の色と書体は、Fluent のトークンから作る |

## 理由

- 枠に閉じ込めると、ページの CSP を緩めずに済む。Mermaid に欠陥があっても、不透明なオリジン、枠の CSP（`default-src 'none'`）、sandbox、親の `frame-src 'self'` が、親の文書と外への送信を止める。
- 画像として見せると、SVG の中の `<style>` が効き、中のスクリプトは動かない。PoC で、5 つのブラウザについて、厳格な CSP のページの画像と CSP のないページの画像が同じに描かれることを確かめた。
- 枠の CSP をヘッダーだけで付け、配信元を書くのは、WebKit が sandbox で不透明になった文書の `'self'` を配信元に一致させないからである（PoC）。
- 静的版で描かないのは、5 つのブラウザすべてで枠がスクリプトを読めず、`allow-same-origin` を足して枠を不透明でなくすと、枠の中の欠陥が親に届く道を開くからである。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| ページの CSP に `style-src 'unsafe-inline'` を足し、ページの中で描く | `[style]` 0 件の約束を捨て、Mermaid の CSS の注入がページ全体に及ぶ |
| Mermaid の `securityLevel: 'sandbox'` | data: の iframe は親の CSP を継承し、スタイルが止まる。`frame-src data:` も要る |
| `<style>` に nonce を付ける | `style` 属性が止まり、攻撃者が書いた CSS まで許す |
| サーバー側（Python）で描く | Node か QuickJS の依存が増え、本物の Mermaid との一致とフォントの差に不安が残る |
| 図ごとに見える iframe を置く | 図の数だけ Mermaid を読み直し、高さを合わせるのに `style` が要る |
| 全部入りの `mermaid.min.js` | elkjs のライセンス（EPL-2.0 OR GPL-3.0-or-later）を同梱物に持ち込む |

## 影響

- 2 方式で描けるものが初めて違う。ADR-0016 の「2 方式で同じ手順の結果が一致する」は、図を除く部分について保つ。
- ADR-0010 の「classic な `<script src>` だけ」に、iframe と `postMessage` が加わる。
- ADR-0005 の「browse での表示は将来の作業」は、この決定で置き換わる。svg の範囲は ADR-0005 の形だけで、生の `<svg>` は今も出さない（ADR-0002 の `html: False`）。
- プラグインの同梱物が約 2.85 MB 増え、Mermaid のあるページを開くたびに取り直す（応答は `no-store`）。
- 図の中の文字は選べず、検索に当たらない。ADR-0005 の「補足」の引用が文字の側を受け持つ。

## 参照

- [図の描画の設計](../plans/wiki-browse-figures-2026-11-17.md)
- [PoC の記録](../research/wiki-browse-figures-poc-2026-11-17.md)
- Mermaid の設定の文書: https://mermaid.js.org/config/schema-docs/config.html
- CSP Level 3: https://w3c.github.io/webappsec-csp/
