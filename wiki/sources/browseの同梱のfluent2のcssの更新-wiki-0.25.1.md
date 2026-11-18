---
type: "source"
title: "browse の同梱の fluent2.css をスキルの 0.1.5 に写し直した wiki 0.25.1 のリリース"
tags: ["リリース", "browse", "fluent2"]
authors: ["to884"]
raw: "info-hive-wiki/skills/info-hive/scripts/browse_assets/README.md"
ingested: 2026-11-16
created: 2026-11-16
updated: 2026-11-16
---

# browse の同梱の fluent2.css をスキルの 0.1.5 に写し直した wiki 0.25.1 のリリース

`/wiki:browse` が同梱する Fluent 2 の CSS（`browse_assets/fluent2.css`）を、スキル `fluent2-html-replica` の 0.1.5 のものに写し直し、wiki 0.25.1 として出した記録である。スキルの側の修正は、0.25.0 の作業（[[browseのタグの段とTreeのリリース-wiki-0.25.0]]）で browse が自前で避けた 2 つの不具合を、スキルの原本で直したものである。

## 経緯

1. 0.25.0 の作業で、Tree の 2 つの不具合が見つかった。子の行のホバーで祖先の枝のクイックアクションが出ること（画面で見つけた）と、`enhanceTree` が葉の Enter を取り消すこと（Sol のレビューの指摘）である。browse は `style.css` と `app.js` で避け、スキルの側は別の版で直すことにした。
2. スキルの開発用のリポジトリ（to884/fluent2-web-design）で v9 のソースを確かめて直し、スキルの 0.1.4 として出した。v9 は、子の木からのホバーを除き（`useTreeItemLayout.tsx:219-237`）、葉の Enter で既定の動作を止めない（`useTreeItem.tsx:175-180`）。`a.fui-TreeItem` の下線を消す規則も足した。続けて、修飾キーの付いた文字と、Alt と左右の矢印を扱わない修正を 0.1.5 として出した。
3. browse の写しは、スキルの 0.1.0〜0.1.3 と同じ中身だった。0.1.5 の `fluent2.css` に写し直した。0.1.5 の CSS は 0.1.4 と同じである。下線は同梱の CSS が消すので、`style.css` の `.tree a.fui-TreeItem` の規則を外した。`app.js` は、Ctrl、Meta、Alt の付いたキーをすべて扱わず、葉の Enter も止めないので、変えていない。見た目と操作は変わらない。
4. 開発用のリポジトリの `.agents/skills/fluent2-html-replica` も 0.1.5 にした。`npx skills add` は `.claude/skills` の symlink を本物のフォルダーに置き換え、`.agents` を古いまま残したので、元に戻して `.agents` に写し、`skills-lock.json` の `commit` と `computedHash` を合わせた。
5. 手元で、browse の Python の試験（186 passed、5 skipped）と、Chromium のブラウザーの試験（`browse`、`findability`、`startup`）を流した。外れはなかった。明るい配色と暗い配色の画面を目で見た。Sol の敵対的レビューは「採用可」で、指摘はなかった。
6. 子の PR（to884/info-hive-wiki#79）の CI 4 つと、親の PR（to884/info-hive-dev#158）の CI 17 が通ってから、子をマージした（`4f82917`）。注釈付きのタグ `v0.25.1` と GitHub リリース `v0.25.1` を作った。
7. 使い捨ての設定でマーケットプレイスから入れ、0.25.1 が入ることを確かめた。v0.25.0 から v0.25.1 までに変わった 5 つのファイルの SHA-256 が、すべてタグの中身と一致した。入った `wiki_browse.py` で Wiki を書き出し、出力の `fluent2.css` が 0.1.5 のものであることを確かめた。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | `npx skills add` は、このリポジトリの `.claude/skills` の symlink を本物のフォルダーに置き換え、`.agents/skills` を更新しない。`.agents` に写して symlink を戻す | 経緯の 4 | `source_only` | 1 回の観察で、CLI の版で変わりうる |

## 関係するページ

- [[browseのタグの段とTreeのリリース-wiki-0.25.0]]
- [[リリースの確かめ方]]
