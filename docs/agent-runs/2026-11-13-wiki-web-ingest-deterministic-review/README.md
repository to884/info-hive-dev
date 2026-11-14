# URL の取り込みの決定論的な処理の設計のレビュー（2026-11-13）

[docs/plans/wiki-web-ingest-deterministic-2026-11-13.md](../../plans/wiki-web-ingest-deterministic-2026-11-13.md) を、GPT-6.1 Sol（effort high）の敵対的レビューに 5 回かけた。設計の発端は、`/wiki:ingest` のモデルの比較（[docs/research/wiki-ingest-model-comparison-2026-11-13.md](../../research/wiki-ingest-model-comparison-2026-11-13.md)）で見つかった raw の誤りである。

| 回 | 対象 | 判定 | 重大以上 | 指摘の原因の分類 |
| --- | --- | --- | --- | --- |
| 1 | 1 版 | 却下 | 9 | [root-causes.md](root-causes.md) |
| 2 | 2 版 | 却下 | 6 | [root-causes-2.md](root-causes-2.md) |
| 3 | 3 版 | 却下 | 6 | [root-causes-3.md](root-causes-3.md) |
| 4 | 4 版 | 却下 | 5 | [root-causes-4.md](root-causes-4.md) |
| 5 | 5 版 | 却下 | 2 | 本文の「改訂の記録」に、5 版の追記として直した |

各回とも、前の回の指摘はすべて「崩せなかった」とされた。新しい指摘は、その回で足した仕組みの前提に集まり、範囲は回を追って狭くなった（モデルとの受け渡しの形、変換の構造、錠と確定、パスの名前、部分の削除の指定）。

各回の依頼文は、`ask-codex` の `review` が結果の隣に残した `review-N.md.task.md` にある。

5 版の追記（スラッグの照合と `drop_text` の出現の番号）はレビューしていない。残りの細部は、段階 1 の試作と試験で確かめる方針とした。
