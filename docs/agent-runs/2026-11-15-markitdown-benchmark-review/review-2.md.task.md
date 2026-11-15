# レビューの目的（2 回目）

`docs/research/markitdown-benchmark-2026-11-15.md` は、info-hive の wiki と rag の取り込みで MarkItDown を使うかを決めるためのベンチマークのレポートである。1 回目の敵対的レビュー（`docs/agent-runs/2026-11-15-markitdown-benchmark-review/review-1.md`）の指摘を受けて、計測のスクリプト（`docs/research/markitdown-benchmark-2026-11-15/scripts/`）、結果（`results.json`、`summary.md`、`footprint.json`）、レポートを直した。直したことは、レポートの末尾の「レビュー」の節にまとめてある。

次の点を中心に崩してほしい。

- 1 回目の指摘が、実際に直っているか。言い換えただけで、元の欠陥が残っていないか
- 新しい指標（順に読めた割合、1 行に残った表の行、列のそろった表の行）と自己試験に、別の偽陽性や偽陰性がないか。保存した出力（`outputs/`）に当てて確かめてよい
- 判定と出力の照合（`prepare_judge.py` と `aggregate.py`）に、古い判定を新しい出力に結び付ける抜け道が残っていないか
- レポートの結論の範囲が、試料と計測の結果に合っているか。言い過ぎ、または結果にない主張がないか

1 回目の指摘のうち直っていないものは、そのことを書く。1 回目に挙がっていない欠陥も挙げる。
