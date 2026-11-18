---
type: "source"
title: "Troubleshooting thinking（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting"
raw: "raw/claude-thinking-troubleshooting.md"
fetched_at: "2026-11-18T22:03:42+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
graph:
  relationships:
    - predicate: cites
      object: "source:claude-api-extended-thinking"
      source: "claude-thinking-troubleshooting"
      evidence: "budget_tokens からの移行手順は適応型推論への移行を参照してください。"
      raw_ref: "raw/claude-thinking-troubleshooting.md#L69"
      confidence: high
      status: current
---

# Troubleshooting thinking（Claude Platform Docs）

Anthropic の公式ガイド。推論設定に起因する 400 エラー、推論ブロックを送り返す際の署名検証、応答の欠落や打ち切り、キャッシュミスを症状ごとに扱う。推論の仕様は [[claude-api-thinking]]、ツール結果を返すリクエストの組み立て方は [[claude-thinking-tool-workflows]] を参照。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting.md)をもとに、モデル別の対応表とエラーメッセージ例 10 ブロックを含む[日本語訳](../../raw/claude-thinking-troubleshooting.md)を保存した。

## 症状と確認箇所

| 症状 | 確認すること | 対処 |
| --- | --- | --- |
| `thinking.type` または effort の指定で 400 | モデルが受理する推論モードと段階。例として Claude Sonnet 5.5 の `between_tools` は `high` 以下で使える | モデル別の表から対応する組み合わせを選ぶ。Sonnet 5.5 の `between_tools` でターンごとに段階を変える必要がある場合は適応型推論を使う |
| ツール結果の返送で「推論ブロックを変更できない」という 400 | 以前のアシスタントターンを含め、返送したブロックの順序と内容が受信時と一致するか | `thinking`、`redacted_thinking` を含む元の `assistant.content` をそのまま返す |
| 署名エラーに、別の会話にひも付いていると続く | ブロックより前の `system`、`tools`、メッセージの編集や並べ替え | 対応環境ではベータヘッダーと `prefix_mismatch_behavior: "drop_block"` を指定する。もう一つの方法は、指摘されたブロック以降の推論ブロックを取り除き、同じターンのほかのブロックを残す |
| 署名が無効という文言だけで終わる | `signature` 自体の欠落、切り詰め、変更 | 返された署名をそのまま戻す。会話の先頭部分が不一致の場合の設定は適用されない |
| `thinking` フィールドが空、またはブロック自体が欠落 | 空のフィールドは `display: "omitted"` で生じる。ブロックの欠落は適応型推論で省略されたときや、受理された強制ツール利用で生じる | 空のフィールドを含むブロックも署名ごと保持する。推論の要約が必要なら対応する設定で `display: "summarized"` を使う |
| `stop_reason: "max_tokens"` で停止、または設定変更後にキャッシュミス | 出力上限に達したか、推論モード・予算・トップレベルの effort を変えたか | 出力枠は `max_tokens` と effort で調整する。同じキャッシュを使うリクエストでは設定を維持する。調整例は [[claude-thinking-steering-and-cost]] |

> 表1 補足: 取得時点の診断例。署名エラーのうち、履歴の不一致と署名自体の不正では対処が異なる。モデル別の詳細、ベータヘッダー、エラーの原文は日本語訳にある。

モデルが `thinking.type: "enabled"` を拒否した場合は、[[claude-api-extended-thinking|拡張推論]] で `budget_tokens` から `output_config.effort` への切り替え手順を確認できる。拡張推論だけに対応するモデルで `"adaptive"` を指定すると 400 エラーになるため、日本語訳のモデル別対応表を確認する。

Claude Fable 5.2・Mythos 5.2 へ切り替える前に、リクエストが会話の先頭部分の照合で失敗するかを確認できる。移行元ごとの確認手順は [[claude-fable-5-2-migration|Fable 5.2・Mythos 5.2 への移行ガイド]] を参照。

Claude Opus 5.5 に切り替える場合は、`thinking.type` の `"disabled"` と手動の `"enabled"` を取り除き、effort と `max_tokens` を見直す。空の推論ブロックの扱いを含む変更例と移行元別の確認項目は [[claude-opus-5-5-migration|Opus 5.5 への移行ガイド]] を参照。

Claude Sonnet 5.5 の `between_tools` は、`display`、`budget_tokens`、`block_binding` を併用すると 400 エラーになる。回答前の推論を省く設定への切り替え例と、応答ブロックの処理は [[claude-sonnet-5-5-migration|Sonnet 5.5 への移行ガイド]] を参照。

Claude Haiku 5.5 に切り替えるときは、手動の `budget_tokens` を取り除いて適応型推論に移行する。小さな `max_tokens` を使っていた処理では、推論だけで出力上限に達する場合がある。設定例と出力上限の見直し方は [[claude-haiku-5-5-migration|Haiku 5.5 への移行ガイド]] を参照。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 400 エラーの内容は、モデルと推論モード、effort の組み合わせによって異なる | 「モデル別の推論の対応状況、既定値、拒否される設定」以下の設定エラー各節 | `source_only` | 取得時点の対応表とエラーの原文をこのページから参照できるようにした |
| c2 | 返送したブロックの変更、署名自体の不正、過去の履歴の不一致では確認箇所が異なる | 「推論ブロックを変更できないという 400 エラー」「推論ブロックの署名が無効だという 400 エラー」 | `update` | [[claude-thinking]] と [[claude-thinking-tool-workflows]] から症状別の対処を参照できるようにした |
| c3 | 空の `thinking` フィールドでも、署名を含むブロックはツール結果の返送時に保持する | 「応答の thinking フィールドが空になる」 | `update` | [[claude-thinking-tool-workflows]] に空のテキストを含むブロックの返送条件を追記した |
| c4 | トークン上限による停止、キャッシュミス、テキストに出るツール呼び出しにも診断手順がある | 「ツール呼び出しや XML タグがテキストに現れる」「応答が停止する」「キャッシュヒットが減る」 | `source_only` | 症状ごとの切り分けと対処をこのソースにまとめた |

## 関係するページ

- [[claude-thinking]]
- [[claude-api-thinking]]
- [[claude-api-extended-thinking|拡張推論]]
- 推論設定の 400 エラーをきっかけにモデルを切り替える場合は、[[claude-api-model-migration|モデル移行ガイド一覧]] から移行先の手順を確認できる。
- [[claude-thinking-tool-workflows]]
- [[claude-thinking-steering-and-cost]]
