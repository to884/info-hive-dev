# 図の描画の実装（PR 2: Mermaid）の 1 回目のレビュー

対象は、`/wiki:browse` に Mermaid の図の描画を足す実装である。設計は `docs/plans/wiki-browse-figures-2026-11-17.md` の 7 節（とくに 7.1 の「枠が知ってよいもの」と 7.4 の寿命）、8 節、9 節、10 節。決定は `docs/adr/0030-wiki-browse-shows-figures-as-images.md`（提案）。PoC は `docs/research/wiki-browse-figures-poc-2026-11-17.md`。svg（PR 1）はレビュー済みで、この PR の土台である。

差分は 2 つある。

- プラグイン（サブモジュール `info-hive-wiki`）: `docs/agent-runs/2026-11-17-wiki-browse-figures/impl-review-3.plugin.diff`（svg の PR のコミット `fd36292` との差）。新しいファイルは `skills/info-hive/scripts/browse_assets/` の `figures.js`、`mermaid-frame.html`、`mermaid-frame.js`、`mermaid.tiny.js`（第三者の束。中身は読まなくてよい）、`licenses/mermaid.*`。変わったのは `wiki_browse_core.py`（`CORE_VERSION`、`CSP`、`FRAME_*`、`frame_csp`、`ASSETS`、`_tail`、`load_frame_assets`）、`wiki_browse.py`（`App`、`serve`、`build` の検査の除外、`_route_inner` の `/_frame/`、`_frame`）、`style.css`、`.gitattributes`、文書。
- 開発リポジトリ: 埋め込んだ差分（`tests/wiki/test_browse.py` の `MermaidAssetsTest`、`tests/wiki/test_browse_server.py` の `FrameServeTest`、`tests/wiki/browse/figures.test.mjs` の Mermaid と枠の寿命の確かめ、ADR への追記、`AGENTS.md`）。

守るべき目的は次のとおりである。

1. ページの CSP（`style-src 'self'`、`script-src 'self'`）を緩めず、`[style]` と CSP の違反が 0 件のまま、図を見せる。
2. wiki の本文に Mermaid の欠陥を突く図があり、枠の中で任意のスクリプトが動いても、その図を書いた人がすでに知っている以上のもの（ほかの図、ページの本文、wiki のデータ、表示と操作のトークン、cookie）を知りえず、親の文書を操作できない。
3. 枠の寿命: 同時に生きている枠は 2 つまで。枠とのやり取りは使い切り。図の表示はコード、画像、警告のどれか 1 つ。
4. ADR-0001 の条件（127.0.0.1、Host の確かめ、書き込みの API なし）を、トークンなしの `/_frame/` が崩さない。
5. 見た目は `fluent2.css` の部品とトークンだけ。要素の `style` に触らない。

とくに次を崩せるか見てほしい。

- `figures.js` の `Run` と枠の状態の扱い（競合、`finish` の二重、`stop` の途中の `finish`、`restoreCode` で `<pre>` を元の場所に戻す処理、`it.next` が消えた場合）。
- 親の `message` の受け取り（`event.source` の照合、`ready` の前の `result`、型の違う値、巨大な値）と `imageUrl` の検査。
- `mermaid-frame.js` の `secure`、設定、`normalize`（innerHTML に入れる SVG、`getBBox`）と、枠の CSP の下で起きうること。
- サーバーの `/_frame/` の経路（パスの分け方、版の比べ方、Host、HEAD、キャッシュのヘッダー、リダイレクトがないこと）と、表示のトークンの経路との関係。
- 静的の書き出しに枠を入れないことと、`figures.js` の `location.protocol` の判定。
- 試験が主張どおりのことを確かめているか（`figures.test.mjs` の撮り比べの閾値、偽の枠の確かめ、`FrameServeTest`）。
