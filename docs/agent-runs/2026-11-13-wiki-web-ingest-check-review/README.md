# URL の取り込みの検査（中の案）の設計と実装のレビュー（2026-11-13）

[docs/plans/wiki-web-ingest-check-2026-11-13.md](../../plans/wiki-web-ingest-check-2026-11-13.md) の設計と、`info-hive-wiki` の `wiki_rawcheck.py` と `wiki_fetch.py` の変更を、GPT-6.1 Sol（effort high）の敵対的レビューにかけた記録である。

| 回 | 対象 | 判定 | 重大以上 | 原因の分類 |
| --- | --- | --- | --- | --- |
| 設計 1 | 設計 1 版 | 条件付きで採用可 | 8 | 設計案の改訂の記録 |
| 実装 1 | 行ごとの正規表現で照らす実装 | 却下 | 9 | [impl-root-causes-1.md](impl-root-causes-1.md) |
| 実装 2 | パーサーのトークンの木で照らす形に作り直したもの | 却下 | 6 | [impl-root-causes-2.md](impl-root-causes-2.md) |
| 実装 3 | | 却下 | 3 | [impl-root-causes-3.md](impl-root-causes-3.md) |
| 実装 4 | | 却下 | 3 | [impl-root-causes-4.md](impl-root-causes-4.md) |
| 実装 5 | | 却下 | 2 | [impl-root-causes-5.md](impl-root-causes-5.md) |
| 実装 6 | | 却下 | 2 | [impl-root-causes-6.md](impl-root-causes-6.md) |
| 実装 7 | | 却下 | 3 | [impl-root-causes-7.md](impl-root-causes-7.md) |
| 実装 8 | Sonnet 5.5 で試した結果の改善を含む版 | 却下 | 4 | [impl-root-causes-8.md](impl-root-causes-8.md) |

実装の各回とも、前の回の指摘の反例はすべて「崩せなかった」とされた。反例は、`tests/wiki/test_wiki_web_check.py` の `ReviewCounterexampleTest`〜`ReviewCounterexample8Test`、`FetchCounterexample8Test` などに回帰試験として入れた。7 回目と 8 回目の間に、Sonnet 5.5 で手順を実地に試した（[sonnet-trial.md](sonnet-trial.md)）。

8 回目の指摘を直したあとの版は、まだレビューしていない。8 回目で、表の見えないセルについての 6 回目と 7 回目の保証（列の数とパイプの数による言い換え）を取り下げ、パーサーの中で不変条件を確かめる形にした。

各回の依頼文は、結果の隣の `*.task.md` にある。`impl-N.submodule.diff` は、その回にレビューした `info-hive-wiki` の差分（`origin/main` から）である。
