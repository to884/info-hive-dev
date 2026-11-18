---
type: "source"
title: "Claude Haiku 5.5 migration guide（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide"
raw: "raw/claude-haiku-5-5-migration.md"
fetched_at: "2026-11-18T23:11:16+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
graph:
  relationships:
    - predicate: cites
      object: "source:claude-api-model-migration"
      source: "claude-haiku-5-5-migration"
      evidence: "Sonnet や Opus に切り替える場合はモデル移行ガイド一覧"
      raw_ref: "raw/claude-haiku-5-5-migration.md#L25"
      confidence: high
      status: current
---

# Claude Haiku 5.5 への移行ガイド

Anthropic の公式ガイド。Claude Haiku 4.5、Haiku 3.5、Haiku 3 から Haiku 5.5 へ移行するときの Messages API の変更を扱う。プラットフォーム別のモデル ID、移行元別のチェックリスト、手動予算から適応型推論に変えるコード例を、[公式 Markdown 版](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide.md)から[日本語訳](../../raw/claude-haiku-5-5-migration.md)に収録した。仕様は 2026年11月18日の取得時点の記載。

## 推論の設定と応答

- 手動の `thinking: {"type": "enabled", "budget_tokens": N}` は 400 エラーになる。推論設定を省略するか `"adaptive"` を指定し、`output_config.effort` で調整する。推論トークンも `max_tokens` に含まれるため、上限が小さいとテキストの前に `stop_reason: "max_tokens"` で停止する場合がある。
- 応答の先頭に推論ブロックが現れる場合があるため、内容ブロックは `type` で判別する。既定では `thinking` フィールドは空で `signature` が付く。要約が必要なら適応型推論で `display: "summarized"` を指定する。ツール結果を返すときは空のブロックもそのまま送り返す。
- 強制の `tool_choice` を指定すると、ツール呼び出しから応答が始まり、推論ブロックは返らない。呼び出し前の推論が必要な場合は `tool_choice: {"type": "auto"}` と、ツールを使う条件を示すプロンプトを使う。
- 過去の推論ブロックが入力のトークン数に加わるので、複数ターンではトークナイザーの変更に加えてその分も見積もる。会話履歴は追記で管理する。生成元とリンクしていないアカウントで再送した場合や、切り替え先のモデルが読めない場合、API は対象ブロックを取り除き、リクエストは成功する。対応するモデルの組み合わせは日本語訳の表を参照。

## 推論以外の移行項目

Claude API のモデル ID は `claude-haiku-5-5`。トークナイザーが変わり、Haiku 4.5 と同じ入力テキストでもトークン数は約 30% 増える。増加幅は内容に依存する。サンプリングパラメーターを取り除き、アシスタント応答の事前入力を置き換える。コンピューター操作は `computer_toolset_20260801` に移行する。Amazon Bedrock では対応ベータヘッダーを付けた `computer_20251124` も受理される。Haiku 3.5 以前では、使っているツールの版と停止理由の処理も見直す。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | Haiku 5.5 への変更項目は移行元とプラットフォームで異なる | 「移行元モデル別のチェックリスト」「Claude Haiku 5.5 のモデル ID を使う」 | `update` | [[claude-api-model-migration]] の Haiku 5.5 の項目から手順へつないだ |
| c2 | 手動予算は 400 エラーになる。適応型推論に切り替え、effort と出力上限を見直す | 「推論を設定する」 | `update` | [[claude-thinking-troubleshooting]] の設定エラーと出力上限の診断から移行例へつないだ |
| c3 | 過去の推論ブロックの保持はモデルやアカウントの組み合わせに依存する | 「推論を設定する」「生成元アカウントで推論ブロックを再送する」「過去のターンを保持する」 | `source_only` | Haiku 5.5 固有の条件とモデル切り替え表をソースと日本語訳で参照できるようにした |

## 関係するページ

- [[claude-api-model-migration|モデル移行ガイド一覧]] から Sonnet や Opus への移行手順も確認できる。
- [[claude-thinking-troubleshooting|推論のトラブルシューティング]] に、推論設定の 400 エラー、空の推論ブロック、出力上限での停止を切り分ける手順がある。
- [[claude-api-extended-thinking|拡張推論]] に、手動予算から適応型推論に切り替えるときの共通手順がある。
