---
type: "source"
title: "Claude Opus 5.5 migration guide（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/models/opus-5-5/migration-guide"
raw: "raw/claude-opus-5-5-migration.md"
fetched_at: "2026-11-18T22:48:49+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-19
tags: ["モデル設定"]
concepts: ["claude-thinking"]
---

# Claude Opus 5.5 への移行ガイド

Anthropic の公式ガイド。Claude Opus 5、Opus 4.8、Opus 4.7、Opus 4.6 以前、および Claude Sonnet 5 から移行する際の Messages API の変更を扱う。[公式 Markdown 版](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide.md)をもとに、各 SDK の設定例と移行元別のチェックリストを[日本語訳](../../raw/claude-opus-5-5-migration.md)に収録した。仕様は 2026年11月18日の取得時点の記載。

## 推論の設定と応答の処理

- モデル ID は `claude-opus-5-5`。クラウドでは提供先ごとの ID を使う。適応型推論は常に有効で、`thinking` の省略と `thinking: {"type": "adaptive"}` は同じ挙動になる。無効化の `"disabled"` と手動予算の `"enabled"` は 400 エラーになる。
- 推論の深さは effort で調整する。既定値は `medium` で、Opus 5 の `high` から変わる。推論と応答テキストが `max_tokens` を共有し、非表示の推論も出力として課金される。推論を無効にしていた処理では出力上限、費用、応答時間を測り直す。
- `thinking` が `text` より先に現れる場合があるため、内容ブロックやストリームイベントは `type` で判別する。`thinking.display` の既定値は `"omitted"`。テキストが空でも、ツール結果を返すときは推論ブロックを署名ごと受信時のまま送り返す。
- ツール呼び出し間の進捗は `thinking` ブロックで返る。進捗だけを表示するには対応するベータヘッダーと `display: "updates"` を使い、推論の要約も受け取るには `"summarized"` を使う。
- 会話履歴は追記で管理する。推論ブロックより前の履歴を編集すると先頭部分の照合に失敗することがある。読めないモデルに切り替えた場合は API が対象ブロックを取り除き、リクエストは成功する。切り分けは [[claude-thinking-troubleshooting|推論のトラブルシューティング]] を参照。

## 移行元に応じた変更

チェックリストは移行元に該当するグループまで順に適用する。Opus 5 は共通項目、Sonnet 5 は共通項目と Sonnet 5 専用項目を使う。Opus 4.6 以前から移る場合は、手動予算の廃止、サンプリングパラメーターの削除、トークナイザーの変更を確認する。共通項目では、強制ツール選択、事前入力、コンピューター操作ツールの版も確認する。旧ツール `computer_20251124` は Amazon Bedrock で引き続き利用できる。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | Opus 5.5 への変更項目は移行元モデルによって異なる | 「移行元モデル別のチェックリスト」 | `update` | [[claude-api-model-migration]] の Opus 5.5 の項目から移行元ごとの手順を参照できるようにした |
| c2 | `disabled` と手動の `enabled` は 400 エラー。既定表示では推論テキストが空になり、ツール結果の返送時は空のブロックも保持する | 「すべてのリクエストに共通する要件」「各応答の推論を処理する」 | `update` | [[claude-thinking-troubleshooting]] からエラーと空のブロックの移行時の対処へつないだ |
| c3 | 強制ツール選択、旧ツールの版、トークン数の変化は機能と移行元に応じて確認が必要 | 各移行元のチェックリストと互換性の説明 | `source_only` | モデルと提供先に固有の条件として、このページと日本語訳に収録した |

## 関係するページ

- [[stashから保存した原文と候補メモ-2026-11-19]]: 翻訳前の英語原文の保存先と元の版の記録

- [[claude-api-model-migration|モデル移行ガイド一覧]] から他の移行先モデルの手順を確認できる。
- [[claude-thinking-troubleshooting|推論のトラブルシューティング]] に、推論設定の 400 エラー、署名エラー、空の推論ブロックを切り分ける手順がある。
- [[claude-api-extended-thinking|拡張推論]] に、手動予算から適応型推論への切り替え手順がある。
