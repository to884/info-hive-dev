---
type: "source"
title: "Per-message effort（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/effort-per-message"
raw: "raw/claude-api-effort-per-message.md"
fetched_at: "2026-11-18T21:21:28+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-effort"]
---

# Per-message effort（Claude Platform Docs）

Anthropic の公式ガイド。Messages API で、キャッシュ済みの先頭部分を再利用しながら会話途中で `effort` を変更するベータ機能を扱う。設定全体は [[claude-api-effort]] を参照。[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/effort-per-message.md)をもとに、コード例 9 件とクラウド別の対応表を含む[日本語訳](../../raw/claude-api-effort-per-message.md)を保存した。

## 設定方法と適用時点

1. `messages` に、空の `content` と新しい `output_config.effort` を持つ `role: "system"` のメッセージを追加する。
2. ベータ値 `mid-conversation-output-config-2026-07-01` を送る。Messages API では `anthropic-beta` ヘッダー、Amazon Bedrock の `InvokeModel` API ではリクエスト本体の `anthropic_beta` 配列を使う。
3. トップレベルの `output_config.effort` は同じ値を使い続ける。

新しい入力のある `user` ターンの直後に置くと、その入力に対する応答に適用される。それ以外の位置では、新しい入力のある次の `user` ターンから適用される。`tool_result` だけのターンは新しい入力に数えない。変更した段階は、後続のメッセージが段階を変えるまで続く。

メッセージは送信済みの履歴の後ろに追加し、以後も同じ位置に置く。保持された推論（preserved thinking）に対応するモデルでは、送信済みの履歴への挿入や、追加したメッセージの移動・削除によって、それ以降の `assistant` ターンにある推論ブロックが無効になる。

## 対応条件とエラー

- 利用できるモデルはクラウドによって異なる。メッセージ単位の設定は Messages API のベータ機能で、Managed Agents ではセッションのモデル設定で effort を指定する。
- ベータヘッダーの省略、未対応のモデルや環境、Claude Sonnet 5.5 の `between_tools` または Claude Haiku 5.5 の `disabled` で段階を変える指定は、400 エラーの原因になる。詳しいモデル一覧とエラー本文は日本語訳の「提供状況」「エラーの条件」を参照。
- トップレベルの値を変えると、プロンプトキャッシュの一部または全部が無効になる場合がある。Claude Fable 5.1 では、トップレベルの変更が挙動に反映されにくいこともあるとガイドは説明している。
- 対応するモデルで推論モードを保ったまま段階だけを変えると、変更前のキャッシュ済みの部分を再利用できる。推論設定の変更や、推論ブロックより前の履歴編集がキャッシュや照合に及ぼす影響は [[claude-api-thinking]] を参照。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 対応環境では、空の `system` メッセージとベータ指定で会話途中の effort を変更できる | 「effort の段階を変える」「必須のベータヘッダー」 | `update` | [[claude-effort]] に指定方法と適用範囲を追記した |
| c2 | 新しい段階が適用される応答は、`system` メッセージと新規入力の位置で決まる | 「effort の段階を変える」 | `update` | [[claude-effort]] に適用時点と `tool_result` の例外を追記した |
| c3 | キャッシュ済みの履歴を再利用するには、トップレベルの値と送信したメッセージの位置を維持する | 「effort の段階を変える」「メッセージ単位とトップレベルの設定の違い」 | `update` | [[claude-effort]] に追加後の履歴の扱いを追記した |
| c4 | ベータ機能の対応モデルとエラーの詳細は、プラットフォームや推論モードによって異なる | 「提供状況」「エラーの条件」 | `source_only` | 取得時点の対応表と個別のエラー本文はこのガイドの日本語訳から確認できる |

## 関係するページ

- [[claude-effort]]
- [[claude-api-effort]]
- [[claude-api-thinking]]
