対象は、`/wiki:ingest` で URL を取り込むとき、規則で決まる工程（コードとリンクと画像の行の保護、サイトに共通の雑音の削除、言語の判定、補足の挿入、訳した raw の検査）を、モデルからスクリプトに移す設計案である。

目的: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で見つかった raw の誤り（コードブロックの変更、リンクの欠落、図の説明文の alt への移動、原文にない内容の追加、固有の名前の訳、文体の混在、雑音の残り）を、モデルの能力に頼らず構造で防ぐこと。raw は取り込み後に書き換えない原本である（docs/adr/0004-raw-holds-translated-web-pages.md）。

特に見てほしい点:
- 単位への分割と印（⟦U12⟧ など）で、元の Markdown に戻らない入力（入れ子のリスト、引用の中のコード、表の中の画像、強調の中のリンク、段落の中の改行など）。今の変換は info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py の Converter にある。
- apply の検査をすり抜けて raw が壊れる経路と、正しい訳を誤りとして止めてしまう経路。
- 規則による雑音の削除が本文を消す経路。
- 作業場所（.wiki-cache/ingest/）と ADR-0004 の「原文を保存しない」、raw の不変性との食い違い。
- 長いページを fill-NNN.json に分けて書くときの整合。
- 設計がモデルに残した判断のうち、実は決定論にできるもの、逆に決定論にしたせいで悪くなるもの。

読むもの: 設計案 docs/plans/wiki-web-ingest-deterministic-2026-11-13.md、比較のレポート、ADR-0004、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py。
