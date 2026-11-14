# `/wiki:ingest` のモデルの比較の記録（2026-11-13）

Haiku 5.5、Sonnet 5.5、Opus 5.5 の各モデルで、4 つの Web ページを `/wiki:ingest` で取り込み、raw の違いを比べた。結論と進め方は [docs/research/wiki-ingest-model-comparison-2026-11-13.md](../../research/wiki-ingest-model-comparison-2026-11-13.md) にある。

## ファイル

| ファイル | 中身 |
| --- | --- |
| `mapping.json` | 実行の番号（r01〜r12）と、モデル、ページ、URL の対応 |
| `metrics.json` | 各実行の raw を基準の取得と突き合わせた結果（`compare_raw.py` の出力から本文の行を除いたもの）と、目隠しの評価の A、B、C の割り当て |
| `scripts/compare_raw.py` | raw を基準の取得と突き合わせるスクリプト |
| `scripts/anonymize.py` | 目隠しの評価のために、raw からモデル名を消すスクリプト |
| `scripts/fetch_from_dom.py` | ブラウザで取った HTML を、`wiki_fetch.py` の変換にそのまま通すスクリプト（Medium の有料記事に使った） |
| `judge/task-en.md`、`judge/verdict-en.md` | CQRS と SQLite の訳の目隠しの評価の依頼と結果（GPT-6.1 Sol、effort high） |
| `judge/task-medium.md`、`judge/verdict-medium.md` | Medium の記事の 5 つの節の、同じ評価の依頼と結果 |

`metrics.json` を読むときの注意:

- `images.removed` は、画像の行が基準と文字どおり一致しないものを並べる。スラッグを変えた実行（r02、r05、r07〜r09）と、alt を書き換えた実行（r11）では、残っている画像も「削除」と出る。
- `urls.missing` は URL の集合の差なので、同じ URL が何度も出るページでは欠落を拾えない。リンクの欠落は `links_lost_by_occurrence`（出現の回数で数えたもの。`content` はタグや著者のリンクなどの雑音を除いたもの）を見る。

目隠しの評価の割り当ては、CQRS が A=Opus、B=Haiku、C=Sonnet、SQLite が A=Sonnet、B=Haiku、C=Opus、Medium が A=Sonnet、B=Opus、C=Haiku である。

raw と wiki のページそのものはリポジトリに入れていない。ページの著作権のためと、Medium の記事が有料のためである。評価の結果の中の短い引用だけが残っている。
