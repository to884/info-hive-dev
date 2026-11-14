対象は、`/wiki:ingest` で URL を取り込むときの、raw の書き換えの検査（`wiki_rawcheck.py`）と、`wiki_fetch.py` の雑音の規則・`--html-file`・作業用の写しの実装である。設計は docs/plans/wiki-web-ingest-check-2026-11-13.md（2 版）。設計のレビューは docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/design-review-1.md。

目的: モデルが raw を書き換える工程（雑音の削除、訳、画像の補足）で、規則に反した raw のまま先に進むことを止める。比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で実際に起きた失敗（コードの変更、リンクの欠落、図の説明文の alt への移動、`<>` の追加、固有の名前の訳、雑音の残り）が対象である。

見てほしい点:
- 実装が設計（2 版）の条件と食い違うところ。
- freeze と check が、正しい雑音の削除と正しい訳を止めてしまう入力。今の wiki_fetch.py が実際に出す Markdown の形（入れ子のリスト、引用の中のコード、表、段落の中の改行、リストや引用の中の画像、長さの違うフェンス、`\|` を含む表）で確かめてほしい。
- 検査をすり抜けて、規則に反した raw が通る入力。とくに、freeze の行の対応づけ（difflib と、かたまりを単位にした部分列の判定）と、check のブロックの分け方と補足の取り除き方。
- 雑音の規則が本文を消す入力。
- 作業用の写しの書き方と消し方（リンクやジャンクション、写しを書けないとき）。
- 試験（tests/wiki/test_wiki_web_check.py）が確かめていると言いながら、実は確かめていないこと。

読むもの: info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py（差分は docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/impl-1.submodule.diff）、tests/wiki/test_wiki_web_check.py、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、設計案。

試験は `python -X utf8 -m unittest tests/wiki/test_wiki_web_check.py tests/wiki/test_wiki_fetch.py` で流せる（標準ライブラリだけ）。
