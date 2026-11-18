---
type: "source"
title: "Claude Sonnet 5.5 migration guide（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide"
raw: "raw/claude-sonnet-5-5-migration.md"
fetched_at: "2026-11-18T23:00:46+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
---

# Claude Sonnet 5.5 への移行ガイド

Anthropic の公式ガイド。Claude Sonnet 5、Sonnet 4.6、Sonnet 4.5、Sonnet 4、Claude 3.7 Sonnet、Claude Haiku 4.5 から Sonnet 5.5 へ移行する際の Messages API の変更を扱う。移行元別のチェックリスト、設定例、エラーメッセージを、[公式 Markdown 版](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide.md)から[日本語訳](../../raw/claude-sonnet-5-5-migration.md)に収録した。仕様は 2026年11月18日の取得時点の記載。

## 推論設定と応答処理

- モデル ID は `claude-sonnet-5-5`。推論設定を省略すると適応型推論が有効になる。`thinking.type: "disabled"` と手動の推論予算を指定すると 400 エラーになる。Sonnet 4.6 以前や Haiku 4.5 で推論設定を省略していた処理では、推論も含めて `max_tokens` と費用を見直す。
- 最初の応答前の推論を省くには、`thinking: {"type": "between_tools"}` を使う。effort は `low`、`medium`、`high` に限る。`xhigh` や `max`、`display`・`budget_tokens`・`block_binding` の併用、適用中と異なるメッセージ単位の effort は 400 エラーになる。ターンごとに effort を変える場合は適応型推論を使う。
- 応答の内容ブロックは `type` で判別する。適応型推論では `display` の既定値が `"omitted"` のため、推論フィールドが空でも署名付きのブロックをツール結果とともにそのまま返す。ツール呼び出し間の長い進捗報告は推論ブロックで返る。適応型では `"updates"`（ベータ）や `"summarized"` で表示し、`between_tools` では `display` の指定なしで要約テキストが返る。
- 過去の会話は追記だけで管理する。会話の先頭部分が変わると推論ブロックの照合に失敗する場合がある。切り替え先のモデルが読めないブロックは API が取り除き、リクエストは成功する。診断は [[claude-thinking-troubleshooting|推論のトラブルシューティング]] を参照。

## 移行元別の注意点

全モデル共通の変更には、強制ツール選択、コンピューター操作ツール、アドバイザーの互換性がある。Sonnet 4.6 以前から移る場合は、手動予算、サンプリング、推論表示、トークンの数え方も見直す。Haiku 4.5 からは Sonnet 4 以前のグループを飛ばして Haiku 4.5 専用の項目を適用する。詳しい条件は日本語訳のチェックリストにある。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | Sonnet 5.5 への変更項目は移行元によって異なる | 「移行元モデル別のチェックリスト」 | `update` | [[claude-api-model-migration]] の Sonnet 5.5 の項目から移行元別の手順へつないだ |
| c2 | `between_tools` は `high` 以下で使える。追加の推論フィールドや適用中と異なるメッセージ単位の effort を拒否する | 「最初の応答前の推論を省く」 | `update` | [[claude-thinking-troubleshooting]] に Sonnet 5.5 の設定エラーと移行例への参照を追加した |
| c3 | `type` で内容ブロックを判別し、空の推論ブロックも保持する。進捗報告の表示方法は推論モードに依存する | 「応答の推論を処理する」「ツール呼び出し間のテキストは推論ブロックで返る」 | `source_only` | 共通の扱いは既存ページにあるため、移行時の Sonnet 固有の表示条件とコード例をこのソースに収録した |
| c4 | ツールやアドバイザーの互換性、トークン消費、キャッシュの条件は移行元や環境で異なる | 共通項目と移行元別の説明 | `source_only` | モデル固有の条件をこのページと日本語訳で確認できるようにした |

## 関係するページ

- [[claude-api-model-migration|モデル移行ガイド一覧]] から他の移行先モデルの手順を確認できる。
- [[claude-thinking-troubleshooting|推論のトラブルシューティング]] に、推論モードや effort の指定で起きる 400 エラー、署名エラー、空の推論ブロックの診断がある。
- [[claude-api-effort-per-message|メッセージ単位の effort]] に、会話途中で段階を変える手順と推論モードごとの制約がある。
