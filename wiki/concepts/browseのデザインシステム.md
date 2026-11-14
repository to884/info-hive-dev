---
type: "concept"
title: "browse のデザインシステム（Fluent 2）"
tags: ["browse"]
sources: []
created: 2026-11-14
updated: 2026-11-14
---

# browse のデザインシステム（Fluent 2）

`/wiki:browse` の画面は、Fluent 2 の Web 版のデザインを React を使わずに再現した CSS（スキル `fluent2-html-replica` の `fluent2.css`）で描く。2026年11月14日に作者が決めた（ADR-0021、設計は `docs/plans/wiki-browse-fluent2-2026-11-14.md`）。実装は、構造の直しのあと、探しやすさの実装と一緒に行う（F1）。記事のページの部品は、そのあとに当てる（F2）。

## 決まりの要点

- **同梱する。** `fluent2.css` は書き換えずに、全体をプラグインの `browse_assets/` に写す。出どころ、基準の版、SHA-256 は `browse_assets/README.md` にある。プラグインはスキルの場所を読まない。
- **`fluent2.js` は使わない。** 要素の `style` に書き込み、閲覧の画面の約束（`[style]` が 0 件）に反する。要るふるまいは `app.js` が受け持つ。
- **配色を選べる。** `<html data-theme="auto">` を既定にし、ライトとダークを選べる。選んだ値は、http ではポートを区別しない cookie に、`file://` では localStorage に置く。サーバーは起動ごとにポートが変わり、localStorage はポートごとに分かれるためである。
- **ライセンスの表示を出力に付ける。** `fluent2.css` の先頭のコメントは Fluent UI の表示だけを持つ。`fluent2-html-replica` 自身の MIT の表示は、出力に必ず入る `style.css` の先頭のコメントに写す。

## レビューで分かったこと

設計は Sol の敵対的レビューを 3 回受け、1 回目と 2 回目は分類 A の反例で却下された。崩れた前提は次のとおりで、どれも Fluent の部品を当てるときに繰り返し起きうる。

- **止まっている状態の配色が通っても、操作中は通るとは限らない。** 暗い配色で、brand のリンクの色（`colorBrandForegroundLink`）と、ホバーの地（`colorSubtleBackgroundHover`）の組は 4.18:1 で、4.5:1 を割る。
- **地が変わらない場所を、場所の名前で数え上げてはならない。** Fluent の `fui-TableRow` は、操作できない表でもホバーで地を変える。規則は「地を状態で変えてよいのは操作できる要素だけ」「自分か祖先の地が変わる要素は brand のリンクの色を使わない」の 2 つにした。
- **親の折り返しは、部品の中の `white-space: nowrap` を解かない。** Tag、Badge、Button、Nav の項目に利用者の文字を入れるときは、`nowrap` を外す。
- **試験は場所を数え上げず、地が変わりうるすべての入れ物にポインターを置き、押したままの状態でも測る。** 押下の色は、ホバーの色と別に 4.5:1 を割ることがある（木の「一覧」のリンクで 4.36:1）。

## 関係するページ

- [[browseの画面の確かめ方]]
