---
type: "concept"
title: "Claude API の推論（thinking）"
sources: ["claude-api-thinking", "claude-api-effort", "claude-api-effort-per-message", "claude-thinking-steering-and-cost", "claude-thinking-tool-workflows", "claude-thinking-troubleshooting", "claude-api-extended-thinking", "claude-fable-5-2-migration"]
tags: ["モデル設定"]
created: 2026-11-18
updated: 2026-11-18
---

# Claude API の推論（thinking）

Messages API の `thinking` は、Claude の推論モードを指定する設定。モデルによって既定値と選択肢が異なる。適応型（`adaptive`）ではモデルが推論の要否と深さを決め、[[claude-effort|effort]] で調整できる。手動の拡張推論（`enabled`）は対応する旧モデルなどで `budget_tokens` とともに使う。モデル別の設定表は [[claude-api-thinking]] にある。

## 手動の拡張推論と適応型への移行

対応モデルでは `thinking.type: "enabled"` と `budget_tokens` を指定する。予算は推論トークン数の目安で、最低 1,024 トークン。通常は `max_tokens` 未満にする。手動モードでツール呼び出し間に推論する場合は、予算が同じアシスタントターンの推論ブロック全体にわたるため、`max_tokens` を超えられる。

Claude Opus 4.6 と Claude Sonnet 4.6 では手動設定が非推奨で、モデル番号が 4.7 以降では `enabled` を指定すると 400 エラーになる。適応型推論へ切り替えるときは `budget_tokens` を取り除き、`thinking.type: "adaptive"` とし、`output_config.effort` で調整する。対応モデル、例外、移行前後のリクエスト例は [[claude-api-extended-thinking|拡張推論]] を参照。

## 表示とトークンの計上

適応型と拡張推論では、`display` で推論の見せ方を指定できる。設定を省略したときの表示はモデルによって異なる。

| `display` | 推論ブロックのテキスト | ツール呼び出し間の進捗報告 |
| --- | --- | --- |
| `"summarized"` | 推論の要約 | 要約付き。推論ブロックの要約と区別できない |
| `"omitted"` | 空のテキスト | 空のテキスト |
| `"updates"`（ベータ） | 空のテキスト | 対応モデルは報告の要約を返す |

> 表1 補足: 推論ブロックが返る場合、表示設定にかかわらず `signature` が含まれる。`"updates"` のベータヘッダーは `thinking-display-updates-2026-08-18`。出典は [[claude-api-thinking]]。

現在のターンで生成した推論は、表示方法にかかわらず `max_tokens` に含まれ、出力トークンとして課金される。モデルが過去の推論ブロックをコンテキストに保持する場合、そのブロックは後続リクエストの入力に含まれる。

課金対象の出力の合計は `usage.output_tokens`、そのうち推論に使われた分は `usage.output_tokens_details.thinking_tokens` で確認できる。ストリーミングでは、内訳は最後の `message_delta` に含まれる。出典は [[claude-thinking-steering-and-cost]]。

## ツール利用と会話履歴

適応型推論では、モデルがリクエストごとに推論するか判断する。`xhigh` や `max` でも、ツール結果だけを処理するリクエストでは推論ブロックが返らない場合がある。

ツール結果を送るときは、同じアシスタントターンの `thinking`、`redacted_thinking` とツール呼び出しを、受け取った順序と内容のまま送り返す。対応モデルでは、ブロックより前の `system`、`tools` やメッセージを変更すると、ブロックの先頭部分の照合に失敗して 400 エラーになることがある。

ツールを実行したら、受け取った `assistant.content` 配列と、`tool_result` を含む `user` メッセージを追加して次のリクエストを送る。`tool_result.tool_use_id` には、対応する `tool_use.id` を指定する。この往復は同じアシスタントターンなので、推論設定は次のターンまで維持する。処理の順序とコード例は [[claude-thinking-tool-workflows]] を参照。

返送時の署名エラーに「別の会話にひも付いている」と続く場合は、推論ブロックより前の履歴を確認する。署名が無効という文言だけで終わる場合は、`signature` 自体の欠落や変更を確認する。症状別の対処は [[claude-thinking-troubleshooting]] を参照。

推論を引き継げるかは、切り替えの方向にもよる。Claude API と Claude Models on Google Cloud (Google managed) では、Fable 5.2 は Opus 5.5 の推論ブロックを読み取れる。Fable 5.2 から Opus 5.5 に切り替えると、API は読み取れない推論ブロックを取り除き、リクエストは成功する。具体的な組み合わせは [[claude-fable-5-2-migration]] を参照。

推論モードや `budget_tokens`、トップレベルの effort を途中で変えると、キャッシュの再利用に影響する。推論モードを保って段階だけを変えたい場合は、対応環境で [[claude-api-effort-per-message|メッセージ単位の effort]] を使うと変更前の先頭部分を再利用できる。Claude Sonnet 5.5 の `between_tools` と Claude Haiku 5.5 の `disabled` では、メッセージ単位で異なる段階を指定すると 400 エラーになる。
