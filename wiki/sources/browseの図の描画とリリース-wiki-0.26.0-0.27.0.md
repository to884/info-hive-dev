---
type: "source"
title: "browse に svg と Mermaid の図を出した wiki 0.26.0 と 0.27.0 のリリース"
tags: ["リリース", "browse", "図", "csp"]
authors: ["to884"]
raw: "docs/plans/wiki-browse-figures-2026-11-17.md"
ingested: 2026-11-17
created: 2026-11-17
updated: 2026-11-17
---

# browse に svg と Mermaid の図を出した wiki 0.26.0 と 0.27.0 のリリース

`/wiki:browse` に、`wiki/assets/` の svg（0.26.0）と本文の mermaid（0.27.0）を図として出した記録である。ADR-0005 が「将来の作業」にしていた表示で、決定は ADR-0030（2026年11月17日に承認）、設計は `docs/plans/wiki-browse-figures-2026-11-17.md`、PoC の記録は `docs/research/wiki-browse-figures-poc-2026-11-17.md`、レビューの記録は `docs/agent-runs/2026-11-17-wiki-browse-figures/` にある。

## 作者が決めたこと

| 論点 | 決定 |
| --- | --- |
| 描き方 | ページの CSP（`style-src 'self'`）を緩めず、Mermaid は見えない sandbox の枠で描いて `<img>` で見せる |
| 同梱する Mermaid | 全部入りの `mermaid.min.js` 12.3.0 から、`@mermaid-js/tiny` 12.3.0 に替えた。全部入りの束は elkjs（EPL-2.0 OR GPL-3.0-or-later）を含んでいた |
| 見た目 | `fluent2-html-replica` のデザインシステム（同梱の `fluent2.css` の Card、Image、Accordion、MessageBar とトークン）で組む |

## 経緯

1. PoC（`poc/browse-figures/`）を、Chromium、Firefox、WebKit、Edge、Chrome と、サーバーと `file://` の 2 方式で流した。サーバーでは 10 種類の図が描け、画像の中の `<style>` はページの CSP に止められなかった。`file://` では 5 つすべてが、sandbox の枠に隣のファイルのスクリプトを読ませなかった。静的の書き出しでは Mermaid を描かないことにした。
2. WebKit は、sandbox で不透明になった文書の `'self'` を配信元と一致させなかった。枠の CSP はヘッダーだけで付け（`<meta>` を置かない）、`script-src` に配信元を書いた。
3. Sol の設計のレビューの 1 回目は却下だった。WebRTC の ICE サーバーの名前（DNS）は CSP で止まらない。枠の URL のトークンと配信元の全体を許す `script-src` で、`data/search.js` を読める。外への口を数えて塞ぐのをやめ、枠が秘密を知らない形にした。枠はトークンのない `/_frame/<版>/` から配って `script-src` をそのパスに限り、図ごとに作ってその図だけを送る（[[敵対的レビューで設計を直す進め方]]）。2 回目の PoC で確かめた。2 回目のレビューは、枠の寿命（配色を変えると枠が増える、正しい形の知らせの連打）を指摘し、描画を「回」に、やり取りを使い切りにした。
4. svg の実装の 1 回目のレビューは、BOM のない UTF-16 の svg が「UTF-8 として読める」の判定を通り、公開の前の検査が中のパスを見つけないことを示した。XML として UTF-8 で読まれること（XML で許される文字だけ、宣言が別の符号化を名乗らない）を求める判定にした。lint と閲覧が画像の参照先を別々の規則で解いていたので、lint を markdown-it が `src` を作る手順（`unescapeAll` と `normalizeLink`）に通した。
5. 実装で、設計の 3 つを改めた。`assets/` の一覧を作れなくても閲覧を止めない（既存の試験が守る契約）。`<img>` に大きさの属性を付け、`loading="lazy"` を付けない。入れ物を `inline-block` にする。WebKit は、幅を中身で決める入れ物の中の、読み込む前の画像を幅 0 のまま組んだ。Firefox は、根に大きさのない svg を幅 0 にした。
6. Mermaid の実装のレビューは「条件付きで採用可」で、重大は 0 件だった。閉じ込めの試験の行き先の誤り、配色を変えたあとの違反の数え漏れ、壊れた SVG を成功とする扱いを直した。偽の枠（Playwright で `mermaid-frame.js` を差し替える）で、2 回の `result`、応答なし、描き直しの失敗、壊れた SVG を確かめた。
7. 0.26.0: 子の PR（to884/info-hive-wiki#83）の CI 4 つと親の PR（to884/info-hive-dev#163）の CI 17 が通ってから子をマージした（`998c52e`）。注釈付きのタグ `v0.26.0` と GitHub リリースを作った。to884/info-hive-wiki#71 も 0.26.0 を名乗っていたが未マージだったので、先に main に入れたこちらが 0.26.0 を取った。子の main に head から新しいコミットがなかったので、付け替えたあとの親の CI を待たずに親をマージした（`ad11830`）。使い捨ての設定でマーケットプレイスから入れ、0.26.0 が入り、v0.25.2 から変わった 11 のファイルの SHA-256 がタグの中身と一致し、入ったスクリプトで svg が `<img>` で書き出されることを確かめた。
8. 0.27.0: 子の main を取り込んだ PR（to884/info-hive-wiki#84）の CI 4 つと、親の PR（to884/info-hive-dev#165）の CI 17 が通ってから子をマージした（`4dc8d28`）。注釈付きのタグ `v0.27.0` と GitHub リリースを作った。使い捨ての設定でマーケットプレイスから入れ、0.27.0 が入り、v0.26.0 から変わった 17 のファイルの SHA-256 がタグの中身と一致した。入った `wiki_browse.py` でサーバーを起動し、Chromium で mermaid のページを開いて、図が画像として描かれ（`naturalWidth` 370）、枠が残らず、`[style]` が 0 件であることを確かめた。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | `file://` のページの sandbox の枠（不透明なオリジン）は、5 つのブラウザで隣のファイルのスクリプトを読めない。CSP に `file:` を足しても同じ | PoC の記録の「file:// の方式」 | `source_only` | browse の静的の書き出しだけに関わる |
| c2 | WebKit 26.0（Playwright）は、sandbox の文書の `'self'` を配信元と一致させず、`<meta>` の CSP があるとヘッダーに配信元を書いても止まる | PoC の記録の門 1 | [[browseの画面の確かめ方]] | ブラウザごとの違いの記録に足す |
| c3 | 外への口を数えて塞ぐ設計は数え漏らしで崩れ、知りうるものを限る設計に替えると崩れなかった | 経緯の 3 | [[敵対的レビューで設計を直す進め方]] | 設計の直し方の例 |
| c4 | WebKit は幅を中身で決める入れ物の中の読み込む前の画像を幅 0 のまま組み、Firefox は大きさのない svg の画像を幅 0 にする | 経緯の 5 | [[browseの画面の確かめ方]] | 画面の確かめの注意 |
