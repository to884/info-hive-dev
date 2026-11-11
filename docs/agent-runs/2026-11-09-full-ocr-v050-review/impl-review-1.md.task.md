目的: info-hive の rag プラグインの検証用の全量データ（905 文書、OCR は約 22,335 ページ）の OCR を、rag 0.5.0 の製品の関数（info-hive-rag/scripts/rag_pdf.py の extract_pages）で数日かけて裏で進める。結果は ADR-0014（docs/adr/0014-rag-keeps-extraction-independent-of-embedding.md）の鍵と形（<data_dir>/extracted/<SHA-256>/<抽出の鍵>/page-*.json と document.md）で残し、のちの rag の移行（ADR-0012）で、同じ data_dir で取り込めば製品が OCR をやり直さずに使い回せることが要件である。

確かめてほしいこと:
- 製品が取り込むとき、このスクリプトが残したファイルを、製品自身が作ったものと区別なく使い回せるか（形、鍵、document.md の有無と中身、ロック、一時ファイルの後始末）。製品のコードは info-hive-rag/scripts/rag_index.py の Engine.ingest_pdf と rag_pdf.py を読むこと。サブモジュールがこの worktree で空なら、C:/Works/info-hive-dev/info-hive-rag/scripts を読む。
- 止めても（STOP、親の強制終了、PC の再起動）再開でき、保存済みのページが壊れたり、半端なファイルが製品に読まれたりしないか。
- 進み具合の数（progress.json）が、再開をまたいで正しいか。
- 原本の PDF を書き換えたり複製したりしないか。CPU を使いすぎないか（3 並列、2 スレッド、優先度は通常以下）。
- 記録の文書の主張が、スクリプトの動きと事実に合っているか。
制約: info-hive-rag のコードは変えない。
