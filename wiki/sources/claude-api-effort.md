---
type: "source"
title: "Effort（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/build-with-claude/effort"
raw: "raw/claude-api-effort.md"
fetched_at: "2026-11-18T21:08:51+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-effort"]
---

# Effort（Claude Platform Docs）

Anthropic の公式ガイド。Claude API の `effort` が出力に作用する範囲、段階ごとの対応モデル、推論モードとの組み合わせ、会話中に段階を変える方法を説明する。[公式ページ](https://platform.claude.com/docs/en/build-with-claude/effort)の[公式 Markdown 版](https://platform.claude.com/docs/en/build-with-claude/effort.md)をもとに、モデル別の推奨と各言語のコード例も含めた[日本語訳](../../raw/claude-api-effort.md)を保存した。

## 主な内容

- Messages API では `output_config.effort`、Managed Agents ではエージェントまたはセッションのモデル設定の `effort` を使う。未指定時はモデルの既定値が適用される。
- `effort` は、テキスト、ツール呼び出しと引数、有効な場合の推論に費やすトークン量に影響する。低い段階ではツール呼び出しをまとめたり省いたりする傾向がある。`max_tokens` は推論を含む総出力の上限を指定する。
- `low`、`medium`、`high` が基本で、`xhigh`、`max` の対応はモデルによる。Claude Opus 5.5 と Claude Haiku 5.5 の既定値は `medium`。Claude Fable 5.2、Claude Mythos 5.2、Claude Sonnet 5.5 の既定値は `high`。
- 推論を切り替えられる条件もモデルで異なる。Claude Opus 5.5 は適応型推論が常時有効。Claude Sonnet 5.5 の `between_tools` と Claude Haiku 5.5 の `disabled` は、ともに `high` 以下で使え、`xhigh`、`max` では 400 エラーになる。モデル別の推論モードと出力の扱いは [[claude-api-thinking]] を参照。
- 対応する組み合わせでは、`messages` 内の `system` メッセージに指定するメッセージ単位の変更でプロンプトキャッシュを維持できる。トップレベルの変更ではキャッシュの一部または全部が無効になる場合がある。指定方法と対応条件は [[claude-api-effort-per-message]] を参照。

## 適用範囲

2026年11月18日の取得時点の記載。推奨設定は Anthropic による運用の目安で、同じ段階名でもモデルが変わると推論量が変わる。実際の品質、応答時間、費用は、用途に合う評価で比較するよう案内している。クラウドごとの提供範囲やデータ保持の対象条件は、[日本語訳の「提供状況」](../../raw/claude-api-effort.md#提供状況)に記録した。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | `effort` は推論やツール呼び出しを含む出力に作用し、総出力の上限は `max_tokens` で指定する | 「effort の仕組み」「モデル別の推奨設定」「effort と推論」 | `create` | [[claude-effort]] に各設定の役割をまとめた |
| c2 | Claude API の既定値と推論モードの許容条件はモデルによって異なる | 「effort の段階」「モデル別の推奨設定」 | `create` | [[claude-effort]] に主要モデルの比較を載せた |
| c3 | 対応モデル・モード・プラットフォームでは、メッセージ単位の変更でプロンプトキャッシュを維持できる | 「会話の途中で effort を変更する」「モデル別の推奨設定」 | `create` | [[claude-effort]] に変更方法と適用条件を載せた |
| c4 | 推奨段階の効果はタスクやモデルによって異なり、自分の評価で複数段階を試すよう案内している | 「モデル別の推奨設定」「ベストプラクティス」 | `update` | [[ingestに使うモデル]] から公式の評価指針を参照できるようにした |
| c5 | API ごとの提供範囲とデータ保持の適用条件が掲載されている | 「提供状況」「データの取り扱い」 | `source_only` | 取得時点の提供条件として、要約から原資料内の該当箇所を参照できるようにした |

## 関係するページ

- [[claude-effort]]
- [[claude-api-effort-per-message]]
- [[claude-api-thinking]]
- [[claude-thinking-steering-and-cost]] では、effort と出力上限を調整する手順やキャッシュの例を扱う。
- [[ingestに使うモデル]]
