前回の指摘を受けて、poc/rag/full_pipeline/product_ocr.py と checkpoint_product_ocr.py を直した。直し方が指摘を解消しているか、直したことで新しい欠陥が入っていないかを、同じ観点で敵対的に確かめてほしい。
1. 失敗した文書の保存済みページ: 失敗時に partial をファイルから数え直す。起動時は completed 以外のすべての文書（--limit の対象外も含む）をファイルから数える。
2. 保存前の OCR を数える: recognize のラッパーは結果を覚えるだけにし、製品が page-*.json を保存した直後に呼ぶ progress コールバックで、そのページのファイルがあるときだけ親に知らせる。終わった文書への遅れた知らせは partial に足さない。
3. 二重起動: run の最初に作業領域の runner.lock を FileLock(timeout=0) で取る。start は古い runner.pid を、処理が生きていなければ消してから起動を待つ。
4. checkpoint の verify: 新しい runner.pid が元の owner と違って生きていること、新しいランナーの起動時刻より後に保存したページがあること、それらが製品のキーの並びで読めることを確かめる。
fsync を入れないことは、製品の write_json と同じなので変えない（記録に制約として書く）。
