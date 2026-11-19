# ADR-0035：静的版 browse の Mermaid 図を Pele で書き出す

| 項目 | 内容 |
|---|---|
| 状態 | 承認 |
| 決定日 | 2026-11-19 |
| 決定者 | info-hive の開発者 |
| 関連 | [ADR-0005](0005-wiki-figures-use-mermaid-and-svg.md) · [ADR-0030](0030-wiki-browse-shows-figures-as-images.md) |

## 背景

静的版 browse の `file://` では、ADR-0030 の描画枠が同梱のスクリプトを読めず、Mermaid のコードを表示していた。Pele の試作では、既存の横向き Mermaid 原稿を修正せずに縦向き SVG を生成し、静的版の Chromium と Windows 版 WebKit で開けた。ブラウザ幅 390 px では図の表示幅が 334 px で、`/wiki:init` を含む複数行の日本語ラベルを読めた。SVG の元の幅は 432 px だったので、表示側で縮めた。

## 決定

- 静的の `build` で、記事本文と表示できる概要の `mermaid` フェンスを Pele 1.13.0 で描く。確定した写しの字句から重複を除いた図の原稿を集め、Node.js 20 以上に UTF-8 の JSON で渡す。Pele の束と配布元のライセンス文を同梱する。実行時の npm やブラウザ、ネット接続は必要ない。
- 画像の幅の目安を 334 px とする。対応する図種では Pele の狭幅向けの縦配置を使う。広い画面でも同じ図を使い、必要に応じて画面の幅まで縮める。標準色を明暗で固定し、原稿が図形や系列に明示した色は Pele の規則に従う。既存の `data-theme` と外部 CSS で表示する側を選ぶ。
- HTML に入れるのは SVG を参照する `<img>` と、元のフェンスを開ける「図のコード」。静的な出力は `figures.js` や描画器を含めず、HTTP で配信しても閲覧時の描画処理を起動しない。親ページの CSP は ADR-0030 の値を使う。サーバー版の図は ADR-0030 に従う。
- 原稿は信頼せず、Pele の `links` と `images` を無効にする。図に渡すコールバックや外部アイコン取得処理は設けない。SVG は XML として解析し、受動的な要素と属性だけを許す。文書型・処理命令・スタイルシート・イベント属性・HTML・アニメーション要素を拒む。`href` と CSS の `url()` は SVG 内の `#id` 参照だけを許す。SVG は内容のハッシュで名前を付けて書き出しの世代に含める。
- Node.js が使えないとき、構文や図種が未対応のとき、描画が失敗したときは、その図の元のコードを表示して書き出しを続ける。図が描けなかった件数を書き出しで知らせる。原稿は 50,000 文字、画像は 1 枚 2 MiB までとする。16 図ずつ処理し、1 回 12 秒、全体 60 秒まで待つ。時間切れ、子プロセスの異常終了、応答の破損があった組は分割して再試行する。Node.js は `PATH` にある絶対ディレクトリから探す。

## 理由

書き出し時に描くと、閲覧する側は画像だけを開けばよい。既存の原稿を保つと、GitHub などの Mermaid 対応環境でも図を読める。Pele は Mermaid のテーマや一部の構文との違いがあるので、描けない図では原稿を読めるようにする。固定配色を二つ生成しておくと、埋め込んだ SVG の `prefers-color-scheme` の扱いがブラウザで異なっても、browse 側の切り替えが効く。[Pele の幅指定](https://pele.run/api#narrow-screens) · [互換性](https://pele.run/compatibility)

## 検討した選択肢

- Mermaid で SVG を生成すれば、既存原稿の構文や配色に合わせやすい。Pele の試作では幅に応じた再配置ができ、既存の横向きフローを縦に並べられた。
- D2 の試作でも縦向きの図を作れた。既存原稿に適用するには Mermaid から D2 への変換か書き直しが必要になる。
- PNG の試作では Windows 版 WebKit でピーク私有コミット増分と画像サイズが小さかった。今回は拡大時も文字や線が鮮明な SVG を使う。Pele の出力について同条件での比較は行っていない。

## 影響

図を描く端末に Node.js 20 以上が必要になる。静的サイトの閲覧には通常のブラウザで足りる。図ごとに 2 配色の画像が加わるため、配布サイズは原稿だけを出す静的版から変わる。

## 確認すること

- 日本語を含むフローとシーケンス、構文が不正な図、Node.js 不在のときのコード表示、原稿の重複があるときの画像再利用。
- `file://` と HTTP の静的ページで明暗が切り替わり、CSP 違反、外への要求、描画枠、インラインの style 属性が生じないこと。
- SVG に外部参照や能動的な内容があるときの拒否、日本語の複数行ラベルと表示側のフォント差。
- サーバー版の図、元からある SVG、公開前の絶対パス検査、原子性が従来の試験を通ること。

## 同梱物の出典

`pele.mjs` は npm の [`pele-1.13.0.tgz`](https://registry.npmjs.org/pele/-/pele-1.13.0.tgz) にある `package/dist/pele.js` のバイト列を保持する。tarball の integrity は `sha512-Ie8UKY9x00MsuR3jO6AzUwzK2Z6MIV3Tf4EDdITiuk8Uaz8K7g0R082WqsqNaSU8DdgkrRvZThzhit83mi/uiw==`、束の SHA-256 は `37bea5005aa6d2dde929032ced5d2958cf642667cbc1fe675f9dfacf4ba15a51`。配布元の `LICENSE` は、Pele の MIT と Lucide アイコンの ISC を含み、`browse_assets/licenses/pele.LICENSE` に写した。[Pele 1.13.0](https://github.com/obsidianmd/pele/releases/tag/1.13.0)
