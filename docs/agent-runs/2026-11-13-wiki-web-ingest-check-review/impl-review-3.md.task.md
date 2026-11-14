対象は、`/wiki:ingest` で URL を取り込むときの、raw の書き換えの検査（`wiki_rawcheck.py`）の 3 回目の実装と、`wiki_fetch.py` の雑音の規則・`--html-file`・作業用の写しである。設計は docs/plans/wiki-web-ingest-check-2026-11-13.md。

1 回目と 2 回目の実装は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/impl-review-1.md、impl-review-2.md）。2 回目の指摘は impl-root-causes-2.md で分類して直し、反例を ReviewCounterexample2Test に入れた。指摘は原因の構造で分け（同じフォルダーの impl-root-causes-1.md）、行ごとの正規表現で構造を推し量るのをやめ、同梱の markdown-it-py（wiki_pages.new_parser()。lint と閲覧と同じ設定）のトークンの木で照らす形に作り直した。freeze は木の上で「消すことだけで作れるか」を再帰的に照らし、check は補足の引用を木から取り除いてから節点ごとに照らす。1 回目の反例は tests/wiki/test_wiki_web_check.py の ReviewCounterexampleTest に回帰試験として入れた。

見てほしい点:
- impl-review-1.md と impl-review-2.md の指摘が本当に起きなくなったか。impl-root-causes-1.md と impl-root-causes-2.md の主張を崩せるか。
- トークンの木で照らす形が新しく持ち込んだ欠陥。とくに、freeze の derivable（子の並びの部分列と、インラインの単位の部分列）、インラインの単位の作り方（開きから閉じまでを 1 つのかたまりにすること）、check の strip_captions と compare、Node.signature が比べるもの・比べないもの。
- 正しい雑音の削除と正しい訳を止めてしまう入力、規則に反した raw が通る入力。今の wiki_fetch.py が実際に出す Markdown の形で確かめてほしい。
- 雑音の規則と作業用の写し（fetch.json を最後に書き、そろったかを両方のファイルで判定する）。
- 試験が確かめていると言いながら、実は確かめていないこと。

読むもの: info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py（差分は docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/impl-3.submodule.diff）、tests/wiki/test_wiki_web_check.py、info-hive-wiki/skills/info-hive/scripts/wiki_pages.py の new_parser、設計案、impl-review-1.md、impl-root-causes-1.md。

試験は `python -X utf8 -m unittest tests/wiki/test_wiki_web_check.py tests/wiki/test_wiki_fetch.py` で流せる（標準ライブラリと同梱のパーサーだけ）。
