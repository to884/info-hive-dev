# browse の図の描画の試作

`/wiki:browse` のページに Mermaid の図と svg を出す方式を確かめる試作である。配布対象ではない。結果は `docs/research/wiki-browse-figures-poc-2026-11-17.md` にある。

確かめる方式は次のとおりである。

- ページは今の browse と同じ厳格な CSP（`style-src 'self'`）に `frame-src 'self'` だけを足す。
- Mermaid は、見えない `<iframe sandbox="allow-scripts">` の枠の文書（`mermaid-frame.html`）で描く。枠の CSP だけが `style-src 'unsafe-inline'` を許す。
- 親（`figures.js`）は枠から SVG の文字列を受け取り、DOM には入れず、`data:` の `<img>` にして出す。
- 色と書体は、`fluent2.css` のトークンから Mermaid の `base` テーマの変数を作る。

## ファイル

- `setup.py`: `site/` を組み立てる。ページ、枠の文書、手書きの svg を書き、`src/` と同梱の `fluent2.css`、`mermaid.tiny.js` を写す。CSP の値もここにある。
- `serve.py`: `site/` を 127.0.0.1 で配る。応答の種類ごとに CSP を変える。
- `src/figures.js`: 親の側。`src/mermaid-frame.js`: 枠の側。`src/poc.css`: 試作の CSS。
- `test.mjs`: サーバーと `file://` の 2 方式を、5 つのブラウザで流す。結果は `out/` に書く。

## 使い方

`mermaid.tiny.js` は、npm の `@mermaid-js/tiny@12.3.0` の tarball から取り出す（`npm pack @mermaid-js/tiny@12.3.0`）。tarball の integrity は、レジストリの公表値と照らす。Playwright は `tests/wiki/browse/` に `npm ci` で入れたものを使う。

```bash
python -X utf8 setup.py <mermaid.tiny.js のパス>
node test.mjs
FRAME=file MODES=file node test.mjs
```

環境変数 `BROWSERS`（既定は 5 つ）と `MODES`（既定は `server,file`）で絞れる。`FRAME=file` は、`file://` の枠の CSP に `file:` を足した版を使う。
