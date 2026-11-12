# レビューの目的

`docs/plans/wiki-walk-excluded-dirs-2026-11-11.md` は、`info-hive-wiki` のスクリプトが wiki のディレクトリをたどる経路を 1 つにまとめ、最上位の除くディレクトリ（`raw/`、`assets/` など）に降りないようにする設計の案である。実装はまだない。Raw の大きさの設計（`docs/plans/wiki-raw-size-in-stats-2026-11-11.md`）の 2 回目のレビューの重大 2（このセッションでの自分の指摘）を受けて、作者が「Raw の機能の前に、別の変更として直す」と決めたものである。この設計のまま実装すると壊れる点、既存の実装や設計書と食い違う点、決め残しを探してほしい。

## 設計が果たすべきこと

- wiki をたどる経路を `wiki_pages.py` の 1 つの関数にまとめる。
- 最上位の除くディレクトリの下を列挙しない（その名前のディレクトリがジャンクションやシンボリックリンクでも、大きな Raw でも）。
- ページの集合を変えない。lint、search、グラフ、stats、browse が数えるページは、循環するジャンクションがある場合を除いて、今と同じにする。
- ページのディレクトリに置いたジャンクションの先を今までどおりたどることは、この設計が意図して残す動作である（冒頭の「閉じないこと」）。それ自体を欠陥として挙げるのではなく、その宣言と矛盾する記述や、宣言の範囲を超えて残る経路を挙げてほしい。

## 確かめてほしい点

1. 「ページの集合は変わらない」が崩れる入力がないか。今の `wiki_pages.iter_page_files()`（`rglob("*.[mM][dD]")` と `is_page_path()` と `is_file()`）と、設計の `walk_markdown()` から作る `iter_page_files()` を照らす。Windows、macOS、Linux、Python 3.10 以上で考える。並びも含める。
2. 循環するジャンクションの検出（「決めること」の 2）。条件と、足りることの説明に誤りがないか。検出が、循環でないジャンクションを誤って飛ばす入力、循環を見逃す入力がないか。
3. 使う側の変更（「決めること」の 3〜5）。`wiki_stats.compute_stats()`、`wiki_index.stat_signature()` と `WikiIndex.refresh()`、`wiki_search.collect_pages()` のパースキャッシュ、`wiki_browse_core.py`（`check_enumerable()`、`signature()`、`list_inputs()`）と、今の実装で食い違わないか。MCP の索引の印から除くディレクトリが外れることで、古い結果を返す経路がないか。
4. 背景の表（今のたどり方）と実測の表に、事実の誤りがないか。実測のスクリプトと出力は `docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/walk_probe.py` と `results.md` にある。試作と設計の本文が食い違う点も挙げる。
5. この変更のあと、Raw の大きさの設計の 2 回目のレビューの重大 2 が解消するか。解消しない経路が残るなら挙げる。Raw の大きさの設計書は、この変更を前提にするように書き直してある。2 つの設計書のあいだの矛盾も挙げる。
6. 「試験」の節で、上の点を確かめきれるか。

## 読むべきもの

- `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`（対象）
- `docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/walk_probe.py`、`results.md`
- `docs/plans/wiki-raw-size-in-stats-2026-11-11.md`、`docs/plans/wiki-page-set-and-links-2026-11-09.md`、`docs/plans/wiki-browse-stage1-2026-11-09.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`、`wiki_stats.py`、`wiki_index.py`、`wiki_search.py`、`wiki_lint.py`、`wiki_graph_extract.py`、`wiki_browse_core.py`、`wiki_mcp_server.py`
- `tests/wiki/test_page_set.py`、`tests/wiki/test_mcp_server.py`

これまでと同じ形式で答える。応答は日本語で書く。
