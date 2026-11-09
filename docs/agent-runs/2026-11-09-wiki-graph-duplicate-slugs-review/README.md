# wiki 0.9.2（グラフの同じスラッグのページ）の敵対的レビュー

2026-11-09、`info-hive-wiki` の `wiki_graph_extract.py` で、別のディレクトリに同じスラッグのページがあるとエッジが別のページのノードに付く不具合の修正を、GPT-6.1 Sol（effort high、`ask-codex` の `review`）に敵対的レビューしてもらった。

- `review-task.md`: 依頼の文面
- `review-1.md`: Sol の結果。判定は「採用可」（確信度：中）。致命的・重大な欠陥はなし。

軽微な指摘への対応:

1. パスのないリンクの試験が独立していない → `test_bare_link_alone_points_to_neither` を足した。
2. ノードにならなかったページへのリンクの説明が抜けている → CHANGELOG と `references/graph-workflow.md` に書き、`test_link_to_page_without_its_own_node_makes_no_edge` を足した。
3. 文字列でない node_id で lint と extract が食い違う → 修正前からある。コメントを正確にし、範囲外として PR に書いた。
4. NFC と NFD の名前の違いだけのファイルの出力のパスが重なる → 修正前からある仕様の制約。範囲外として PR に書いた。
