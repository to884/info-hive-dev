---
type: "source"
title: "Thinking in tool and multi-turn workflows（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows"
raw: "raw/claude-thinking-tool-workflows.md"
fetched_at: "2026-11-18T21:57:35+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
---

# Thinking in tool and multi-turn workflows（Claude Platform Docs）

Anthropic の公式ガイド。天気取得ツールを題材に、Claude のツール呼び出しを受け取り、元の推論ブロックを保持して結果を返すまでを説明する。推論モードと保持の規則は [[claude-api-thinking]]、推論する頻度や深さの調整は [[claude-thinking-steering-and-cost]] を参照。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows.md)をもとに、コード、応答例、処理の比較を含む[日本語訳](../../raw/claude-thinking-tool-workflows.md)を保存した。

## ツール利用の往復

~~~mermaid
sequenceDiagram
    participant App as アプリケーション
    participant API as Messages API
    participant Tool as ツール
    App->>API: ユーザー入力とツール定義を送信
    API-->>App: assistant の content（tool_use、推論ブロックなど）
    App->>Tool: tool_use の指定で実行
    Tool-->>App: 実行結果
    App->>API: 元の assistant の content と user の tool_result
    API-->>App: 最終応答（必要に応じて新しい thinking）
~~~

> 図1 補足: 公式ガイドの 2 回の API リクエストを示す。アプリケーションは最初の `assistant` の `content` 配列を受信した順序と内容のまま返し、`tool_result.tool_use_id` には対応する `tool_use.id` を入れる。呼び出しと結果の処理は同じアシスタントターンに属する。

## 推論が入る位置と設定条件

- 呼び出し間の推論を使えるモデルでは、ツールの中間結果を受けて、新しい `thinking` ブロックが次のツール呼び出しや最終回答の前に現れる場合がある。公式ガイドは、電卓とデータベースを続けて使う場合の出力順を、呼び出し間の推論の有無で比較している。
- 1 つのアシスタントターンの途中では推論設定を維持する。最初の応答で推論が省かれる場合や、表示設定により `thinking` のテキストが空でも `signature` を含むブロックが返る場合もある。返送する `content` は受信したものを使う。
- 手動の拡張推論でツールを使う場合、`tool_choice` は `auto` または `none`。適応型推論でツール利用を強制した際の挙動はモデルによる。ガイドに挙がる Claude Opus 5.5、Claude Sonnet 5.5、Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1 では 400 エラーが返る。強制が受理されるモデルでは応答がツール呼び出しから始まる。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | ツール結果を返すリクエストでは、元の `assistant.content` と対応する `tool_result` を送る | 「2 回のリクエストでツール利用を一往復させる」 | `update` | [[claude-thinking]] に `content` 配列と ID の対応を載せた |
| c2 | 同じアシスタントターンでは推論設定を維持し、呼び出し間の推論が有効な場合は途中結果を受けて推論できる | 「この手順で守る規則」「ツール呼び出しの間に推論すると処理はどう変わるか」 | `update` | [[claude-thinking-steering-and-cost]] から具体的な往復と出力順を参照できるようにした |
| c3 | 手動の拡張推論では強制ツール利用はエラーになり、適応型推論ではモデルで挙動が異なる | 「この手順で守る規則」 | `source_only` | モデル別の挙動とコード例をこのソースにまとめた |

## 関係するページ

- [[claude-thinking]]
- [[claude-api-thinking]]
- [[claude-thinking-steering-and-cost]]
- [[claude-thinking-troubleshooting]] では、返送した推論ブロックの変更と署名エラーの切り分けを扱う。テキストが空でも署名を含む推論ブロックは受信したまま返す。
