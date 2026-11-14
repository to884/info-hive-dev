対象は、`/wiki:ingest` で URL を取り込むとき、規則で決まる工程をモデルからスクリプトに移す設計案の 2 版である。

1 版は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/review-1.md）。2 版では、指摘を原因の構造で 6 つに分け、前提そのものを変えた（同じフォルダーの root-causes.md）。主な変更は、モデルに Markdown を書かせず平文と対のタグだけを返させること、変換が中間表現の木を返すこと、規則は雑音の候補を挙げるだけにすること、確定の直前に保存先を確かめて排他的な作成で確定すること、stage_id と画像の出現と asset の区別、手順に規則のある違反は宣言がなければ誤りにすること、である。

目的: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で見つかった raw の誤りを、モデルの能力に頼らず構造で防ぐこと。raw は取り込み後に書き換えない原本である（docs/adr/0004-raw-holds-translated-web-pages.md）。

見てほしい点:
- 1 版の指摘が、2 版の構造で本当に起きなくなったか。root-causes.md の対応表の主張を崩せるか。
- 2 版で新しく入った仕組み（タグの木の照合、名前と記号の多重集合の照合と宣言、雑音の候補の振り分け、確定の順序、取り込みの記録、中間表現と描画）が持ち込んだ欠陥。
- 中間表現から今の Markdown を描いて一致させる、という段階 1 の前提が、今の Converter（info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py）で成り立つか。
- 正しい訳を誤りとして止めてしまう経路（とくに名前と記号の照合）。

読むもの: 設計案 docs/plans/wiki-web-ingest-deterministic-2026-11-13.md、root-causes.md、review-1.md、ADR-0004、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、wiki_fetch.py。
