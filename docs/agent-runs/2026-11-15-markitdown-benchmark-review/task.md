# レビューの目的

`docs/research/markitdown-benchmark-2026-11-15.md` は、info-hive の wiki と rag の取り込みで MarkItDown を使うかを決めるためのベンチマークのレポートである。計測のスクリプトは `docs/research/markitdown-benchmark-2026-11-15/scripts/`、計測の結果は `results.json` と `summary.md`、品質の判定は `judge/` にある。

このレポートの結論（PDF は rag の PDFium の抽出にし、MarkItDown は使わない。Office の形式、EPUB、ZIP には MarkItDown を使う。HTML は今の `wiki_fetch.py` を使う。CSV、JSON、XML はどちらでもよい）を、作者が採ってよいかを判断できるようにしたい。

次の点を中心に崩してほしい。

- 計測のスクリプトが、比べると言っている方式を正しく再現しているか（rag 0.5.3 の `info-hive-rag/scripts/rag_pdf.py`、wiki 0.18.0 の `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py` と `wiki_encoding.py`、wiki の取り込みの手順 `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`）
- 機械的な指標（網羅率、読み順、表の行、位置の目印）の定義に、結論を左右する偏りや誤りがないか
- 速度の測り方が、結論の書き方（起動に約 3.5 秒かかる、など）を支えているか
- 試料と判定の作り方（試料の作り方、方式の名前を伏せる方法、判定の依頼の文）が、特定の方式に有利または不利になっていないか
- レポートの文が、計測の結果と Sol の判定の全文（`judge/sol-result.md` と `judge/mapping.json`）に合っているか。言い過ぎや、結果にない主張がないか
