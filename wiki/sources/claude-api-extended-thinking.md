---
type: "source"
title: "Extended thinking（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/extended-thinking"
raw: "raw/claude-api-extended-thinking.md"
fetched_at: "2026-11-18T22:18:09+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
graph:
  relationships:
    - predicate: cites
      object: "source:claude-api-thinking"
      source: "claude-api-extended-thinking"
      evidence: "推論の多くの挙動はモードに共通しており、推論の概要で説明しています。"
      raw_ref: "raw/claude-api-extended-thinking.md#L339"
      confidence: high
      status: current
    - predicate: cites
      object: "source:claude-thinking-troubleshooting"
      source: "claude-api-extended-thinking"
      evidence: "拡張推論だけを使えるモデルを含め、各モデルの対応状況はモデル別の設定表を参照してください。"
      raw_ref: "raw/claude-api-extended-thinking.md#L30"
      confidence: high
      status: current
    - predicate: cites
      object: "source:claude-api-model-migration"
      source: "claude-api-extended-thinking"
      evidence: "詳しい手順は推論の概要、effort、移行ガイドを参照してください。"
      raw_ref: "raw/claude-api-extended-thinking.md#L392"
      confidence: high
      status: current
---

# Extended thinking（Claude Platform Docs）

Anthropic の公式ガイド。対応モデルで `thinking.type: "enabled"` と `budget_tokens` を指定して使う手動の拡張推論を扱う。推論モードに共通する仕様は [[claude-api-thinking|Thinking]]、対応モデルと 400 エラーの診断は [[claude-thinking-troubleshooting|推論のトラブルシューティング]] を参照。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/extended-thinking.md)をもとに、SDK 別のリクエスト例や移行前後の設定例を含む[日本語訳](../../raw/claude-api-extended-thinking.md)を保存した。

## 手動モードの予算と制約

- `budget_tokens` は推論に使うトークン数の目安で、最小値は 1,024。最終回答を含む総出力の上限は `max_tokens`。通常は `budget_tokens < max_tokens` が必要だが、手動モードでツール呼び出し間に推論する場合、予算は同じアシスタントターン内の推論ブロック全体にわたり、`max_tokens` を超えられる。
- Claude Opus 4.5 では `budget_tokens` で推論の深さを指定し、effort で応答全体を調整する。実際に課金された推論トークン数は `usage.output_tokens_details.thinking_tokens` に出る。ストリーミングでは最後の `message_delta` で確認できる。
- ツール呼び出し間の推論は、Claude Sonnet 4.6 ではベータヘッダー付きの手動モードでも動作するが、非推奨。Claude Opus 4.6 では適応型推論で使え、Claude Haiku 4.5 では使えない。ヘッダーをエラーなく受理しても機能が有効になるとは限らない。
- `budget_tokens` をリクエスト間で変更すると、メッセージのキャッシュ区切りでミスが起きる。ツールやシステムプロンプトの区切りへの影響はモデルによる。

## 適応型推論への移行

Claude Opus 4.6 と Claude Sonnet 4.6 では手動設定が非推奨で、モデル番号が 4.7 以降のモデルでは `type: "enabled"` が 400 エラーになる。適応型推論に対応するモデルへ移るときは、`budget_tokens` を取り除き、`thinking.type` を `"adaptive"` に設定し、`output_config.effort` で推論を調整する。適応型推論では入力と effort に応じて推論を省く場合があり、ツール呼び出し間の推論は自動で有効になる。切り替え直後のリクエストではキャッシュの再利用に影響する。

拡張推論だけに対応する Claude Opus 4.5、Claude Sonnet 4.5、Claude Haiku 4.5 などを使い続ける間は、手動設定が必要。Claude Mythos Preview は拡張推論と適応型推論の両方に対応する。対応状況は 2026年11月18日の取得時点の記載。

移行先のモデルに固有の手順は、[[claude-api-model-migration|モデル移行ガイド一覧]] から確認できる。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | 手動の予算は最小 1,024。通常は `max_tokens` 未満で、手動モードのツール呼び出し間の推論では例外がある | 「予算の規則と調整」「手動モードでツール呼び出し間に推論する」 | `update` | [[claude-thinking]] に基本制約を追加し、[[claude-api-thinking]] から詳しい設定へつないだ |
| c2 | 4.6 では手動設定が非推奨。モデル番号が 4.7 以降で `enabled` を拒否された場合は適応型の設定と effort に切り替える | 「適応型推論への移行」 | `update` | [[claude-thinking]] に切り替え手順を追加し、[[claude-thinking-troubleshooting]] の 400 エラーの診断から参照できるようにした |
| c3 | 手動のツール呼び出し間の推論はモデルに依存し、ベータヘッダーの受理だけでは機能の有効性を判断できない | 「手動モードでツール呼び出し間に推論する」 | `source_only` | モデルとプラットフォームごとの条件をこのソースと日本語訳で参照できるようにした |
| c4 | 手動予算を変えるとメッセージのキャッシュ区切りでミスが起きる | 「手動モードのプロンプトキャッシュ」 | `source_only` | 概念ページに既存の説明があるため、数値付きの検証例をこのソースの日本語訳に残した |

## 関係するページ

- [[claude-thinking]]
- [[claude-api-thinking]] では、推論ブロックの表示、保持、ストリーミングなどの共通仕様を扱う。
- [[claude-thinking-troubleshooting]] では、モデルごとに受理される推論モードと 400 エラーの対処を確認できる。
- [[claude-thinking-steering-and-cost]] では、適応型推論の effort と費用、キャッシュの確認方法を扱う。
- [[claude-thinking-tool-workflows]] では、ツール結果を返すリクエストの組み立て方を扱う。
