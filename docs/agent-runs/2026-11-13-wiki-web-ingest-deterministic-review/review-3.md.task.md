対象は、`/wiki:ingest` で URL を取り込むとき、規則で決まる工程をモデルからスクリプトに移す設計案の 3 版である。

1 版と 2 版は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/review-1.md、review-2.md）。指摘は原因の構造で分け、前提を変えた（root-causes.md、root-causes-2.md）。3 版の主な変更は次のとおり。
- 推測で取り出した特徴（名前、記号）を誤りの判定に使わない。守る語は訳の前に原文の側で候補を挙げ、モデルが決め、決めた語はタグにしてモデルが書き換えられないようにする。記号の追加は誤りにせず記録する。
- 合格の条件を、今の出力との一致ではなく HTML の内容に置く。文字は常にエスケープして描く。
- 中間表現を body 全体で作り、本文の選択と雑音の判定を、捨てずに木の上の印にする。選ばれなかった article と main はモデルに確かめさせる。
- 同じスラッグの操作（--stage、--restage、apply、clean）を 1 つの錠で排他し、確定の順を決めた。stage_id はファイル名に使える 16 進の値にした。

目的: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で見つかった raw の誤りを、モデルの能力に頼らず構造で防ぐこと。raw は取り込み後に書き換えない原本である（docs/adr/0004-raw-holds-translated-web-pages.md）。

見てほしい点:
- review-1.md と review-2.md の指摘が、3 版の構造で本当に起きなくなったか。root-causes-2.md の対応表の主張を崩せるか。
- 3 版で新しく入った仕組み（守る語のタグ、decisions.json と fill の分離、本文の選択の印と確認、錠と確定の順序）が持ち込んだ欠陥。
- 正しい訳や正しい判断を誤りとして止めてしまう経路が、まだ残っていないか。
- 段階 1（中間表現への置き換えで、今の出力との差をエスケープだけにする）が、今の Converter（info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py）で成り立つか。

読むもの: 設計案 docs/plans/wiki-web-ingest-deterministic-2026-11-13.md、root-causes.md、root-causes-2.md、review-1.md、review-2.md、ADR-0004、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、wiki_fetch.py。
