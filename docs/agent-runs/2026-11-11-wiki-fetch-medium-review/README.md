# info-hive-wiki#42 の修正の敵対的レビュー（2026-11-11）

`wiki_fetch.py` が Medium の記事の図（`<picture>` の `<source srcset>` にだけ URL がある）とコードブロックの改行（`<pre>` の中の `<br>`）を落とす不具合の修正を、GPT-6.1 Sol（effort high）にレビューしてもらった。

- 依頼: `task.md`。対象の差分は `submodule.diff`（info-hive-wiki）と `parent.diff`（このリポジトリ）
- 結果: `review-1.md`（判定は「条件付きで採用可、確信度 高」）

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| `srcset` を `,` で区切るので、URL の中のカンマ（`resize,w_1400/a.png`）で URL が切れ、別の URL を取りに行く | 重大 | `parse_srcset()` を足し、HTML の規則に沿って空白までを URL として読む。`<img>` の `srcset` から最初の候補を取るときも同じ読み方にした |
| `<source>` の `media` を見ないので、使われない候補を選びうる | 重大 | `media` のない `<source>` を先に見る |
| 記述子のない候補を 0 として比べる。`2x 1000w` のような不正な候補を選ぶ | 軽微 | 記述子のない候補は 1x とし、記述子が読めない候補は捨てる。幅の候補があれば幅で、なければ密度で比べる |
| `srcset` が `data:` の画像だと `data-srcset` を見ない | 軽微 | `srcset` から取れなければ `data-srcset` を見る |
| テストが名前の解決（DNS）を止めていない | 軽微 | テストで `is_private_host` も差し替えた |
| CHANGELOG の「Medium の図はすべてこの形」は確かめられない | 軽微 | 「確かめた Medium の記事では」に改めた |

対応のあと、`tests/wiki/test_wiki_fetch.py` は 18 件、標準ライブラリだけのほかの wiki の試験と合わせて 57 件が通った。実際の Medium の記事（連載の第 1 回と第 2 回）でも、図がすべて保存され、コードブロックの行と字下げが保たれることを確かめた。
