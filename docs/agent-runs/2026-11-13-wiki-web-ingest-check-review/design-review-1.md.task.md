対象は、`/wiki:ingest` で URL を取り込むとき、モデルが raw を書き換えた結果を、取得した直後の内容とスクリプトで照らして止める設計（中の案）である。

背景: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で、モデルが raw を書き換える工程（雑音の削除、訳、画像の補足）で、コードの変更、リンクの欠落、図の説明文の alt への移動、原文にない内容の追加、雑音の残りが見つかった。大きな作り直しの案（docs/plans/wiki-web-ingest-deterministic-2026-11-13.md）と比べ、作者はこの中の案を選んだ。

この案の要点は、モデルの編集を「雑音の削除（消すことだけ）」と「訳と補足」の 2 段に分け、段ごとに検査することである。

見てほしい点:
- freeze と check の検査が、正しい雑音の削除と正しい訳を止めてしまう経路。今の wiki_fetch.py の出力の形（info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py）で、ブロックへの分け方が崩れる入力。
- 検査をすり抜けて、規則に反した raw が通る経路（とくに、比較で実際に起きた失敗）。
- 雑音の規則が本文を消す経路。
- 作業用の写し（.wiki-cache/ingest/<スラッグ>/）と、--html-file、スラッグの検査の欠陥。
- 指摘は、実装の前に設計として決めておくべきものに絞ってほしい。実装の試験で見つければ足りる細部は、軽微として分けてほしい。大の案が扱った同時の取り込みの排他は、意図して対象外にしている。

読むもの: docs/plans/wiki-web-ingest-check-2026-11-13.md、docs/research/wiki-ingest-model-comparison-2026-11-13.md、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py。
