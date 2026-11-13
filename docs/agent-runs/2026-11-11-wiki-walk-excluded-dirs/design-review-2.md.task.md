# 2 回目のレビューの目的

`docs/plans/wiki-walk-excluded-dirs-2026-11-11.md` の 2 版目を壊してほしい。`info-hive-wiki` のスクリプトが wiki のディレクトリをたどる経路を 1 つにまとめ、最上位の除くディレクトリ（`raw/`、`assets/` など）に降りないようにする設計の案である。実装はまだない。

1 版目は、このセッションでの自分のレビュー（`docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/design-review-1.md`）で却下された。そのあと、browse の構造の直し（`docs/plans/wiki-browse-structure-2026-11-11.md` の 3）から 4 つの要望（R1〜R4）が届き、browse の設計の 3 回目のレビュー（`docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-3.md`）の重大 4 も、この計画に当てはまった。2 版目は、指摘を 1 つずつ塞がずに、崩れた前提（「1 版目で崩れた前提」の表）から書き直したものである。

## 設計が果たすべきこと

- wiki をたどる経路を `wiki_pages.py` の 1 つのたどり方にまとめ、ページと索引のファイルを同じたどり方で集める。
- 最上位の除く名前の項目には、種類を調べる呼び出しもしない。
- 失敗のないとき、ページの集合と並びを今と同じにする。違いは、設計が挙げたもの（循環するジャンクション、NFC で同じになる名前の順、索引の側の 2 つ）だけにする。
- 失敗を「ない」「権限がなくて分からない」「そのほか」の 3 つに分け、1 か所で読み替える。権限の失敗は、どの呼び出しで起きても、必ず知らせ（`unlistable` か `unknown`）になる。そのほかの `OSError` は送出する。
- browse が、この関数に乗れる（R1〜R4）。
- ページのディレクトリに置いたジャンクションの先を今までどおりたどること、ファイルのシンボリックリンクを読むこと、lint などが知らせを見ないことは、設計が意図して残す動作である（冒頭の「閉じないこと」）。それ自体を欠陥として挙げるのではなく、その宣言と矛盾する記述や、宣言の範囲を超えて残る経路を挙げてほしい。

## 確かめてほしい点

1. 「1 版目で崩れた前提」の表の 5 つの前提が、2 版目の本文で本当になくなっているか。同じ前提に頼る箇所が、本文、試作、試験のどこかに残っていないか。表にない、別の崩れる前提がないか。
2. 失敗の読み替え（「決めること」の 2）。呼び出しごとの当てはめの表に、抜けている呼び出し、矛盾する扱いがないか。「権限の失敗は必ず知らせになる」が成り立たない経路がないか。「ない」として知らせを出さないことで、ページが黙って欠ける経路のうち、設計が認めていないものがないか。
3. たどる関数と、その上の関数（3、4）。失敗のないとき、今の `iter_page_files()`（`rglob("*.[mM][dD]")`、`is_page_path()`、`Path.is_file()`）と今の `wiki_lint.index_files()` に対して、設計が挙げた違いのほかに、集合か並びが変わる入力がないか。Windows、macOS、Linux、Python 3.10 以上で考える。
4. 循環するジャンクションの検出（5）。条件と、足りることの説明に誤りがないか。循環でないジャンクションを誤って飛ばす入力、循環を見逃す入力がないか。`stat` は成功して識別子が 0 のときの文字列の比較が、誤る入力がないか。
5. 使う側の変更（6、7）。`wiki_stats.compute_stats()`、`wiki_index.stat_signature()` と `WikiIndex.refresh()`、`wiki_index.list_index()`、`wiki_search.collect_pages()` のパースキャッシュと、今の実装で食い違わないか。印を、走査が返す大きさと更新時刻から作ることで、古い結果を返す経路がないか。
6. browse との関係（8）。R1〜R4 への答えが、browse の設計の 3 が求めることを満たすか。browse の設計と矛盾する記述がないか。
7. 試験（「試験」の節）と探索。探索の 3 つの決まりで見つけられない誤りの形がないか。試作の探索（`walk_v2.py` の `Injector` と `explore()`）が、数えていない呼び出し、失敗を入れられない呼び出しがないか。対照が、探索の働きを確かめるのに足りるか。
8. 「検証環境の値」と背景の実測の表に、保存された出力（`results.md`）と食い違う記述がないか。試作（`walk_v2.py`）と本文が食い違う点のうち、設計が「試作と本文の違い」に挙げていないものがないか。

## 読むべきもの

- `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`（対象）
- `docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/walk_v2.py`、`walk_probe.py`、`index_probe.py`、`results.md`
- `docs/plans/wiki-browse-structure-2026-11-11.md`（2 と 3）、`docs/plans/wiki-raw-size-in-stats-2026-11-11.md`、`docs/plans/wiki-page-set-and-links-2026-11-09.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`、`wiki_lint.py`、`wiki_stats.py`、`wiki_index.py`、`wiki_search.py`、`wiki_graph_extract.py`、`wiki_mcp_server.py`
- `tests/wiki/test_page_set.py`、`tests/wiki/test_mcp_server.py`

これまでと同じ形式で答える。応答は日本語で書く。
