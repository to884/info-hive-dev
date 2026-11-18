---
type: "source"
title: "Thinking（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/thinking"
raw: "raw/claude-api-thinking.md"
fetched_at: "2026-11-18T21:27:00+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking", "claude-effort"]
graph:
  relationships:
    - predicate: cites
      object: "source:claude-api-extended-thinking"
      source: "claude-api-thinking"
      evidence: "設定方法は拡張推論を参照してください。"
      raw_ref: "raw/claude-api-thinking.md#L478"
      confidence: high
      status: current
---

# Thinking（Claude Platform Docs）

Anthropic の公式ガイド。Claude の推論モード、推論ブロックの表示と返送、ツール利用、ストリーミング、プロンプトキャッシュとの関係を説明する。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/thinking.md)をもとに、図 4 枚とコード・イベント例 40 ブロックを含む[日本語訳](../../raw/claude-api-thinking.md)を保存した。

## 主な内容

- Messages API の `thinking` は推論モードを指定する。既定値と指定可能な値はモデルによって異なる。適応型ではモデルが推論の有無と深さを決める。拡張推論では `budget_tokens` を指定する。Managed Agents ではサービスが推論設定を決める。
- `effort` は適応型推論の頻度と深さを含めて、応答全体に費やすトークン量を調整する。推論を含む総出力の上限は `max_tokens` で指定する。Claude Sonnet 5.5 の `between_tools` は回答前の推論を省き、Claude Haiku 5.5 の `disabled` は推論を無効にする。どちらも effort が `high` 以下で使える。
- `display` は応答に含める推論テキストを調整する。`"summarized"` は要約、`"omitted"` は空のテキスト、ベータの `"updates"` は対応モデルの進捗報告の要約を返す。現在のターンで生成した推論は、表示の有無によらず出力トークンとして課金される。
- ツール呼び出しと結果の受け渡しは同じアシスタントターンに属する。ツール結果を返す際は `thinking` と `redacted_thinking` を含むブロックを順序どおり、そのまま送り返す。過去ターンの推論が入力に残るかはモデルによって異なる。
- 推論モード、推論予算、トップレベルの effort はプロンプトに反映されるため、変更するとキャッシュに影響する。対応環境でメッセージ単位の effort を使うと、変更前のキャッシュ済みの先頭部分を再利用できる。推論の保持に対応するモデルでは、送り返したブロックより前の履歴を編集すると先頭部分の照合に失敗する場合がある。

## 適用範囲

2026年11月18日の取得時点の記載。対応モデルやクラウド、API の版によって、既定の推論モード、強制ツール利用、サンプリングパラメーター、出力上限などの制約が異なる。各モデルの設定表、ストリーミングのイベント順、サービス別の制約は日本語訳に収録した。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | `thinking` が推論モードを指定し、適応型推論では `effort` で推論の深さや頻度を調整できる | 「推論を設定する」「推論と effort」 | `update` | [[claude-effort]] にモードの詳細への参照を追加した |
| c2 | 推論の表示設定で見えるテキストを調整できる。生成した推論は表示設定によらず出力トークンに数える | 「推論の出力を読む」「推論とコンテキストウィンドウ」 | `create` | [[claude-thinking]] に表示と課金の関係をまとめた |
| c3 | ツール結果を返すときは推論ブロックをそのまま送り返す。古い推論を入力として保持する範囲はモデルによる | 「ツール利用時の推論」「モデル別の推論ブロックの保持」 | `create` | [[claude-thinking]] にターン内の返送とターン間の保持を整理した |
| c4 | 対応環境では、メッセージ単位の effort でキャッシュ済みの先頭部分を再利用できる。推論モードを変えるとキャッシュに影響する | 「推論とプロンプトキャッシュ」 | `update` | [[claude-api-effort-per-message]] にキャッシュの適用条件への参照を追加した |
| c5 | ストリーミングのイベント順、API の版によるサンプリング制約、モデル別の出力上限が掲載されている | 「推論のストリーミング」「制限と機能の互換性」 | `source_only` | 取得時点の仕様表とコード例を日本語訳から参照できるようにした |

## 関係するページ

- [[claude-thinking]]
- [[claude-effort]]
- [[claude-api-effort]]
- [[claude-api-effort-per-message]]
- [[claude-thinking-steering-and-cost]] では、適応型推論の調整手順と課金される推論トークンの確認方法を扱う。
- [[claude-thinking-tool-workflows]] では、元の推論ブロックを保持してツール結果を返すコード例を扱う。
- [[claude-api-extended-thinking|拡張推論]] では、手動予算の制約、ツール呼び出し間の推論、適応型推論への移行手順を扱う。
- [[claude-thinking-troubleshooting]] では、モデル別の設定エラー、署名の不一致、空または欠落した推論ブロックの診断を扱う。
