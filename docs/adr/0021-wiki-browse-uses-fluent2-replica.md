# ADR-0021：`/wiki:browse` の画面は、Fluent 2 を再現した CSS を書き換えずに同梱して描き、配色を選べるようにする

| 項目 | 内容 |
| --- | --- |
| 状態 | 提案 |
| 決定日 | （承認の日を入れる） |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0010（閲覧の中核と届け方を分ける）、ADR-0016（第 1 段階は 2 方式で合格とする）、ADR-0017（閲覧は自分が作ったものだけを置き換える）、[browse の画面を Fluent 2 にする設計](../plans/wiki-browse-fluent2-2026-11-14.md)、[探しやすさの設計](../plans/wiki-browse-findability-2026-11-13.md) |

## 背景

`/wiki:browse` の画面は、第 1 段階で作った独自の CSS（GitHub に似た配色）で描いている。作者は、画面のレイアウトとデザインを、Microsoft の Fluent 2 の Web 版のデザインシステムに書き換えたいと考えた。

画面は厳しい CSP（`default-src 'none'; script-src 'self'; style-src 'self'`）の下で、`file://` の静的版と 127.0.0.1 のサーバーの 2 方式で描く。外へ通信せず、classic な `<script src>` だけを使い、スクリプトなしでも読める（ADR-0010）。

Fluent 2 の公式の実装は、React の `@fluentui/react-components`（v9）と、Web Components の `@fluentui/web-components`（v3）である。作者は、React を使わない HTML と CSS で Fluent 2 を再現した非公式のスキル `fluent2-html-replica` を持っている。その `fluent2.css` は、トークン、FluentProvider に当たる土台、部品、書体のプリセットを 1 つにまとめた生成物で、info-hive-wiki の browse と同じ CSP の下で使えることが確かめてある。

## 決定

| 項目 | 決定 |
| --- | --- |
| デザインの元 | スキル `fluent2-html-replica` の `fluent2.css`（`@fluentui/react-components` 9.75.2 の再現）を使う |
| 同梱 | `fluent2.css` を書き換えずに、全体をプラグインの `browse_assets/` に写す。出どころ、基準の版、SHA-256、写し直す手順を `browse_assets/README.md` に記録し、ライセンスの文書を `browse_assets/licenses/` に置く。プラグインの実行と試験は、スキルの場所を読まない |
| スクリプト | スキルの `fluent2.js` は使わない。要るふるまい（ToggleButton の `aria-pressed`、SearchBox の消去）は `app.js` が受け持つ |
| 独自の CSS | `style.css` に、トークンの CSS 変数だけで書く。Fluent の部品にない拡張（深い木、今のページの印、種類の印の色など）は、独自の拡張として設計書に書く |
| 配色 | `<html data-theme="auto">` を既定にし、ライトとダークを選べるようにする。選んだ値は、http ではポートを区別しない cookie に、`file://` では localStorage に置く。`theme.js` が `<head>` で描く前に当てる |
| 画面の契約 | `theme.js` と `app.js` が `<html>` の `data-theme` を書き換えることだけを、例外として足す |
| 進め方 | 索引、サイドバー、検索と共通の部分は、探しやすさの実装と一緒に当てる（F1）。記事のページの部品は、そのあとに当てる（F2） |

## 理由

- **CSP と外への通信の約束を変えずに済む。** `fluent2.css` には `url()`、`@import`、`@font-face` がなく、ファイルとして読めば CSP の違反も外への要求も出ない。試作で 27 の画面を撮り、`[style]`、CSP の違反、外への要求が 0 件だった。
- **書き換えずに全体を写すと、出どころを確かめやすい。** SHA-256 が写した元と一致すればよい。部品の群をまたぐ依存（Divider、Button、at-rule の置き場所）を切り分ける手順を作ると、その手順の誤りを確かめる手間が増える。使わない群は一部だけである。
- **`fluent2.js` は画面の契約に反する。** 要素の `style` に書き込むので、`[style]` が 0 件であることの試験が通らない。使う部品の見た目は CSS だけで出せ、要るふるまいは 2 つだけである。
- **配色の保存先を方式で分ける。** サーバーは起動ごとにポートが変わり、localStorage はポートごとに分かれるので、サーバーを起動し直すと選んだ配色が消える。cookie はポートを区別しない。`file://` では Chromium が cookie を使わないので、localStorage に置く。
- **プラグインが自分で持つ。** スキルは開発用のリポジトリにあり、利用者の環境にはない。閲覧の出力は再配布物なので、ライセンスの表示が付いて回る必要がある。`fluent2.css` は先頭のコメントに表示を持つ。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| 今の独自の CSS を保つ | 作者の依頼は Fluent 2 への書き換えである |
| `@fluentui/web-components` を CDN から読む | CSP（`script-src 'self'`）と、外へ通信しない約束に反する。同梱すると、ES モジュールが要り、classic な `<script src>` だけを使う契約に反する |
| React の `@fluentui/react-components` | ビルドの段と React の実行が要る。事前に描いた HTML をスクリプトなしで読める作りと合わない |
| `fluent2.css` から使う部品の群だけを切り出す | 大きさは減るが、群をまたぐ依存を切り分ける手順と、その確かめが要る。出どころを SHA-256 で照らせなくなる |
| トークンの CSS 変数だけを使い、部品の CSS は自分で書く | Fluent の部品の見た目（高さ、フォーカス、強制カラー）を、自分で写し直すことになる |
| 配色を localStorage だけに置く | サーバーを起動し直すたびに、選んだ配色が消える |

## 影響

- 閲覧の出力の `assets/` に、`fluent2.css`（約 626KB）と `theme.js` が増える。サーバーは資産をキャッシュさせないので、ページを移るたびに `fluent2.css` を読む。起動の速さの試験で測る。
- 書体が、system-ui から始まる並びから、Segoe UI と日本語の書体（Yu Gothic UI、Meiryo UI ほか）の並びに変わる。Segoe UI は同梱しない。
- スコープの札の色が変わる（ユーザースコープは brand、プロジェクトは中立）。文字は同じである。
- Fluent の CSS 変数の名前は内部の実装で、版で変わりうる。同梱した版に固定し、写し直すときは画面を確かめ直す。
- Microsoft の製品ではないこと、商標の帰属、Segoe UI を同梱しないことを、`browse_assets/README.md` とプラグインの `README.md` に書く。

## 参照

- [browse の画面を Fluent 2 にする設計](../plans/wiki-browse-fluent2-2026-11-14.md)
- 試作: `poc/browse-fluent2/`、撮った画面と確かめの結果: `docs/agent-runs/2026-11-14-wiki-browse-fluent2/shots/`
- スキル `fluent2-html-replica`（to884/fluent2-html-replica）の `references/08-plain-html.md`（厳しい CSP の下で使う、ライセンスと商標の表示）
