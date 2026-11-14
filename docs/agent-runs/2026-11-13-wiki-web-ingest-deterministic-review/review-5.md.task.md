対象は、`/wiki:ingest` で URL を取り込むとき、規則で決まる工程をモデルからスクリプトに移す設計案の 5 版である。

1〜4 版は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/review-1.md〜review-4.md）。指摘は原因の構造で分け、前提を変えた（root-causes.md〜root-causes-4.md）。5 版の主な変更は次のとおり。
- 管理用のパスを、スラッグをそのまま 1 つのフォルダーの名前にし、その下の決まった名前の子にした（.wiki-cache/ingest/<スラッグ>/lock、.../work/、raw/.ingest-tmp/<スラッグ>/）。接尾辞やワイルドカードを使わない。
- 木に入れないのを、文字を描かない要素の種類（script、style、template、head）だけにした。aria-hidden、hidden、noscript は雑音の候補にする。
- ブロックを入れられる HTML の要素は、すべて子のブロックを持てる形にした。子のブロックを持つセルのある表は、HTML の表として描く。
- 訳さないページに drop_text（1 つの text にちょうど 1 回現れる文字列を消す）を足した。
- 記録に release_terms と drop_text を足した。

目的: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で見つかった raw の誤りを、モデルの能力に頼らず構造で防ぐこと。raw は取り込み後に書き換えない原本である（docs/adr/0004-raw-holds-translated-web-pages.md）。

見てほしい点:
- review-1〜4 の指摘が、5 版の構造で本当に起きなくなったか。root-causes-4.md の対応表の主張を崩せるか。
- 5 版で新しく入った仕組み（スラッグごとのフォルダー、一時フォルダー、HTML の表としての描画、drop_text）が持ち込んだ欠陥。
- 正しい訳や正しい判断を誤りとして止めてしまう経路が、まだ残っていないか。
- 指摘は、実装の前に設計として決めておくべきものに絞ってほしい。実装の試験で見つければ足りる細部は、軽微として分けてほしい。

読むもの: 設計案 docs/plans/wiki-web-ingest-deterministic-2026-11-13.md、root-causes*.md、review-*.md、ADR-0004、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py。
