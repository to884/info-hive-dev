---
type: "source"
title: "Steering thinking（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost"
raw: "raw/claude-thinking-steering-and-cost.md"
fetched_at: "2026-11-18T21:45:10+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking", "claude-effort"]
---

# Steering thinking（Claude Platform Docs）

Anthropic の公式ガイド。適応型推論を effort とプロンプトで調整する手順、キャッシュの再利用条件、出力上限と課金の測り方を説明する。推論モードは [[claude-api-thinking]]、effort の対応段階は [[claude-api-effort]] を参照。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost.md)をもとに、コードと出力例 12 ブロックを含む[日本語訳](../../raw/claude-thinking-steering-and-cost.md)を保存した。

## 推論の調整と評価

- 適応型推論では、モデルがリクエストごとに推論の要否を判断する。`xhigh` や `max` でも、ツール結果だけを処理する後続リクエストで推論が省かれる場合がある。
- まず用途に合う `effort` を選び、その段階で推論する頻度が用途に合わなければ、システムプロンプトやユーザーメッセージで補う。Anthropic のテストでは、直接答えるよう指示しても Claude Haiku 5.5 は推論を続け、Claude Fable 5.2 も `medium` 以上で推論を続けた。Claude Sonnet 5.5 でも、プロンプトで推論を減らす効果は安定しないと記載されている。
- 代表的なリクエストで指示ありと指示なしを比較し、推論ブロックが返る頻度、出力トークン数、応答時間、回答の品質を測る。

## 上限、課金、キャッシュ

- `max_tokens` は推論を含む **1 リクエストの総出力上限**。ツールを複数回呼ぶアシスタントターンでは、リクエストごとに上限が適用される。`stop_reason: "max_tokens"` で応答が切れる場合、推論が品質に必要なら上限を上げ、推論を減らせる処理なら effort を下げて回答に出力枠を残す。
- 課金対象の出力の合計は `usage.output_tokens`。そのうちモデルが推論に使った分は `usage.output_tokens_details.thinking_tokens` で確認できる。ストリーミングでは内訳は最後の `message_delta` に入る。表示設定を変えても、生成した推論に対する課金は変わらない。
- Claude Opus 5.5 の例では、メッセージ内にキャッシュの区切りを置き、推論設定と effort を揃えた 2 回目はキャッシュを読み出せた。3 回目にトップレベルの effort を `medium` から `low` に変えると、その区切りは再作成された。対応環境の [[claude-api-effort-per-message|メッセージ単位の effort]] や、新しいユーザーメッセージへの指示で調整すると、変更前の区切りを再利用できる。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 適応型推論ではどの effort でもリクエストごとに推論の要否を判断し、省略する場合がある | 「Claude が推論の要否を決める仕組み」「effort の段階」 | `update` | [[claude-thinking]] に推論ブロックが返らない条件を載せた |
| c2 | まず effort を選び、指示で補う場合は実データに近い例で品質と応答時間を測る | 「Claude が推論する頻度を調整する」「実際の用途で調整の効果を確かめる」 | `update` | [[claude-effort]] に調整の順序と評価項目を載せた |
| c3 | `max_tokens` はリクエスト単位で、ツール利用ターン全体には適用されない | 「費用を調整する」 | `update` | [[claude-effort]] に上限の適用範囲と打ち切り時の調整方法を載せた |
| c4 | 生成した推論トークンの課金上の内訳は `usage.output_tokens_details.thinking_tokens` に現れる | 「料金の仕組み」 | `update` | [[claude-thinking]] に出力の合計と内訳の確認方法を載せた |
| c5 | Claude Opus 5.5 の公式例ではトップレベルの effort を変更するとメッセージのキャッシュが再作成された | 「プロンプトキャッシュ」 | `source_only` | モデル、キャッシュ位置、手順に依存する実行例なので、このページから原資料を参照できるようにした |

## 関係するページ

- [[claude-thinking]]
- [[claude-effort]]
- [[claude-api-thinking]]
- [[claude-api-effort]]
- [[claude-api-effort-per-message]]
- [[claude-thinking-tool-workflows]] では、推論設定を維持するツール利用の往復と、ツール呼び出しの間に推論が入る場合の出力順を扱う。
