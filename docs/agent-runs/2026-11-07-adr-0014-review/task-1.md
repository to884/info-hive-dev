対象は ADR-0014（docs/adr/0014-rag-keeps-extraction-independent-of-embedding.md、状態は提案）である。実装はすでにある（info-hive-rag の 6a760b9..28361a4）が、このレビューでは設計の判断を対象にする。

目的: rag プラグインの PDF 抽出と OCR の結果を、埋め込みモデル・分割の設定から切り離して保存し、モデルや分割を変えても OCR をやり直さずに済むようにする。あわせて /rag:setup（configure）で ocr_mode と ocr_dpi を変えられるようにする。前提は ADR-0013（docs/adr/0013-rag-records-pdfs-by-absolute-path-and-hash.md）と、data_dir ごとにワーカーが 1 つであること（info-hive-rag/scripts/rag_worker.py）。

設計の欠陥、崩れる前提、検討した選択肢の比較の誤りを探してほしい。Claude による暫定のレビューの記録（docs/agent-runs/2026-11-07-adr-0014-review/claude-interim-review.md）で直した点は、直し方が十分かも見ること。
