---
type: "source"
title: "Claude Fable 5.2 and Claude Mythos 5.2 migration guide（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/models/fable-5-2/migration-guide"
raw: "raw/claude-fable-5-2-migration.md"
fetched_at: "2026-11-18T22:32:30+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-19
tags: ["モデル設定"]
concepts: ["claude-thinking"]
---

# Claude Fable 5.2 と Claude Mythos 5.2 への移行ガイド

Anthropic の公式ガイド。Claude Fable 5.1・5、Claude Mythos 5.1・5、Claude Opus 5.5・5・4.8 以前からの移行を扱う。Messages API の移行元別チェックリスト、モデル ID、互換性を損なう変更を、[公式 Markdown 版](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide.md)から[日本語訳](../../raw/claude-fable-5-2-migration.md)に取り込んだ。モデルの機能や提供条件は 2026年11月18日の取得時点の記載。

## 推論設定と会話の引き継ぎ

- 両モデルでは適応型推論が常に有効で、`thinking.type` に `"disabled"` または手動の `"enabled"` を指定すると 400 エラーになる。effort は 5 段階で既定値は `high`。Claude Opus 5.5 から移ると、effort を省略したリクエストは既定値が `medium` から `high` に変わる。推論とテキストが同じ `max_tokens` の枠を使うため、出力上限と費用を測り直す。
- 再送した推論ブロックより前の `system`、`tools`、メッセージを変えると、先頭部分の照合に失敗して既定では 400 エラーになる。本番移行前のテストでは、対応するベータヘッダーと `prefix_mismatch_behavior: "drop_block"` を使い、`input_transformations` の `prefix_binding_mismatch` を記録して原因を直す。
- Claude API と Claude Models on Google Cloud (Google managed) では、Fable 5.2 が Fable 5.1 や Opus 5.5 の推論ブロックを読み取れる。逆方向に切り替える場合や、生成元とリンクしていない別のアカウントから再送する場合、API が対象ブロックを取り除き、リクエストは成功する。対応環境ではそれぞれ `model_binding_mismatch` と `organization_binding_mismatch` で確認できる。

## 移行時に確認するその他の設定

- 強制ツール選択は 400 エラーになる。旧コンピューター操作ツール `computer_20251124` は Amazon Bedrock 以外で 400 エラーになるため、`computer_toolset_20260801` への移行が必要。アドバイザーを使う場合は実行側とアドバイザーのモデルの組み合わせも見直す。
- Claude API では原則として 30 日間のデータ保持が必要。Mythos 5.2 は Anthropic の認証プログラムで確認された組織向け。高速モードの提供条件やモデル ID はプラットフォームによって異なる。CMEK を使う組織では両モデルで厳密なツール利用と JSON 出力を利用できない。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 移行元の Fable・Mythos・Opus の世代によって変更箇所が異なる | 移行元ごとの節とチェックリスト | `update` | [[claude-api-model-migration]] の Fable 5.2・Mythos 5.2 の項目から個別の手順を参照できるようにした |
| c2 | 返送した推論ブロックの前の履歴が変わると、先頭部分の照合に失敗して 400 エラーになり得る | Fable 5.1 からの移行「互換性を損なう変更」、Mythos 5.1 からの移行 | `update` | [[claude-thinking-troubleshooting]] に移行前の照合テストへの参照を加えた |
| c3 | 対応環境では旧モデルから 5.2 に推論を引き継げる場合がある。逆方向で読めないブロックは API が取り除く | 共通の基本設定、Opus 5.5 からの移行「変更点」 | `update` | [[claude-thinking]] にモデル切り替え時の方向による違いを追記した |
| c4 | ツール、データ保持、構造化出力、高速モードにはモデルやプラットフォームによる制約がある | 共通の基本設定、各移行元のチェックリスト | `source_only` | 取得時点のモデル固有の条件として、このページと日本語訳に収録した |

## 関係するページ

- [[stashから保存した原文と候補メモ-2026-11-19]]: 翻訳前の英語原文の保存先と元の版の記録

- [[claude-api-model-migration|モデル移行ガイド一覧]] から他の移行先モデルのガイドを確認できる。
- [[claude-thinking-troubleshooting|推論のトラブルシューティング]] に、推論設定の 400 エラーと署名エラーを切り分ける手順がある。
- [[claude-thinking]] に、推論ブロックの表示、ツール利用、会話履歴との関係がある。
