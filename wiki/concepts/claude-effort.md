---
type: "concept"
title: "Claude API の effort"
sources: ["claude-api-effort", "claude-api-effort-per-message", "claude-api-thinking", "claude-thinking-steering-and-cost"]
tags: ["モデル設定"]
created: 2026-11-18
updated: 2026-11-18
---

# Claude API の effort

`effort` は、Claude が 1 回の応答にどれだけトークンを使うかを調整する設定。回答テキスト、ツール呼び出しと引数、推論が対象になる。Messages API ではリクエストの `output_config.effort`、Managed Agents ではエージェントのモデル設定やセッションのモデル上書きで指定する。省略時にはモデルの既定値が適用される。出典は [[claude-api-effort]]。

## 出力の上限と推論モード

`effort` で段階を選び、`max_tokens` で推論を含む総出力の上限を指定する。適応型推論では `effort` を上げるほど、推論を始めやすくなり、推論量も増える傾向がある。`thinking` で指定できるモードはモデルと `effort` の段階によって異なる。モードの設定、推論の表示と課金は [[claude-thinking]] を参照。

| モデル | API の既定値 | 公式ガイドの目安 | 推論モードの条件 |
| --- | --- | --- | --- |
| Claude Fable 5.2／Claude Mythos 5.2 | `high` | `high` から始め、難しい長時間タスクで改善を測れた場合に `xhigh` を試す | 適応型推論は常時有効 |
| Claude Opus 5.5 | `medium` | 過去の Opus の設定から移行する際は複数の段階を試す | 適応型推論は常時有効。`disabled` は全段階で 400 エラー |
| Claude Sonnet 5.5 | `high` | 要件の明確なコーディングや複数段階のツール利用は `medium`、難しい・長い作業は `high` から試す | `between_tools` は `high` 以下。`xhigh` と `max` では適応型推論を使う |
| Claude Haiku 5.5 | `medium` | 多くの用途は `medium`、単純で件数が多い処理は `low` | `disabled` は `high` 以下。`xhigh` と `max` では適応型推論を使う |

> 表1 補足: 主要モデルの比較。掲載の 5 モデルはいずれも `low`、`medium`、`high`、`xhigh`、`max` に対応する。ほかのモデルの対応段階と推奨値は [[claude-api-effort]] の raw を参照。

## 推論量と費用を調整する

まず用途に合う effort を選ぶ。その段階でも推論を行う頻度が用途に合わなければ、プロンプトで補う。代表的なリクエストで推論ブロックが返る頻度、出力トークン数、応答時間、回答の品質を比較する。モデルごとの指示の効き方は [[claude-thinking-steering-and-cost]] を参照。

`max_tokens` は、ツール利用ターンを構成する個々のリクエストに適用される上限。`stop_reason: "max_tokens"` で応答が切れた場合は、推論が品質に必要なら `max_tokens` を上げ、推論を減らせる処理なら effort を下げて回答に出力枠を残す。

## 会話の途中で変える場合

対応する Messages API 環境では、トップレベルの `output_config.effort` を固定したまま、`messages` に空の `content` と新しい `output_config.effort` を持つ `system` メッセージを追加する。プロンプトキャッシュを再利用できる。ベータ値 `mid-conversation-output-config-2026-07-01` の送り方、対応モデル、コード例は [[claude-api-effort-per-message]] を参照。

新しい入力のある `user` ターンの直後に置くと、そのターンへの応答に適用される。それ以外の位置では次の新規入力から適用される。`tool_result` だけのターンは数えない。送信済みの履歴の後ろに追加し、後続リクエストでも位置を維持する。

Claude Sonnet 5.5 の `between_tools`、Claude Haiku 5.5 の `disabled` では、途中で異なる段階を指定すると 400 エラーになる。トップレベルの `output_config.effort` を次のリクエストで変更すると、すでにキャッシュされた範囲の一部または全部が無効になることがある。推論モードや `budget_tokens` の変更によるキャッシュへの影響は [[claude-api-thinking]] を参照。

## 関連

- [[ingestに使うモデル]] では、wiki の取り込みに使うモデルを比較した結果を扱う。
