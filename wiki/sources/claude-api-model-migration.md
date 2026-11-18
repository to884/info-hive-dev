---
type: "source"
title: "Migration guides（Claude Platform Docs）"
authors: ["Anthropic"]
url: "https://platform.claude.com/docs/en/about-claude/models/migration-guide"
raw: "raw/claude-api-model-migration.md"
fetched_at: "2026-11-18T22:26:44+09:00"
ingested: 2026-11-18
created: 2026-11-18
updated: 2026-11-18
tags: ["モデル設定"]
concepts: ["claude-thinking"]
graph:
  relationships:
    - predicate: cites
      object: "source:claude-fable-5-2-migration"
      source: "claude-api-model-migration"
      evidence: "Claude Fable 5.2 と Claude Mythos 5.2 への移行ガイド"
      raw_ref: "raw/claude-api-model-migration.md#L17"
      confidence: high
      status: current
    - predicate: cites
      object: "source:claude-opus-5-5-migration"
      source: "claude-api-model-migration"
      evidence: "Claude Opus 5.5 への移行ガイド"
      raw_ref: "raw/claude-api-model-migration.md#L18"
      confidence: high
      status: current
    - predicate: cites
      object: "source:claude-sonnet-5-5-migration"
      source: "claude-api-model-migration"
      evidence: "Claude Sonnet 5.5 への移行ガイド"
      raw_ref: "raw/claude-api-model-migration.md#L19"
      confidence: high
      status: current
    - predicate: cites
      object: "source:claude-haiku-5-5-migration"
      source: "claude-api-model-migration"
      evidence: "Claude Haiku 5.5 への移行ガイド"
      raw_ref: "raw/claude-api-model-migration.md#L20"
      confidence: high
      status: current
---

# Migration guides（Claude Platform Docs）

Anthropic が公開する、Claude の移行先モデル別ガイドへの索引。掲載先は 2026年11月18日の取得時点のもの。[公式 Markdown 版](https://platform.claude.com/docs/en/about-claude/models/migration-guide.md)から、案内文とリンクを[日本語訳](../../raw/claude-api-model-migration.md)に保存した。

## 移行先モデルごとのガイド

- [[claude-fable-5-2-migration|Claude Fable 5.2・Claude Mythos 5.2]]
- [[claude-opus-5-5-migration|Claude Opus 5.5]]
- [[claude-sonnet-5-5-migration|Claude Sonnet 5.5]]
- [[claude-haiku-5-5-migration|Claude Haiku 5.5]]

移行時に参照する資料として、API の概要、モデルの機能比較、Claude Platform のリリースノートも案内している。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 移行先モデルに応じて個別ガイドを選べる。Fable 5.2 と Mythos 5.2 は共通のガイドを使う | 冒頭の移行ガイド一覧 | `update` | [[claude-api-extended-thinking]] の移行手順と [[claude-thinking-troubleshooting]] の設定エラーの診断から、モデル別のガイド一覧へつないだ |
| c2 | API 仕様、モデルの機能比較、API の更新情報の参照先がある | 「サポート情報」 | `source_only` | 索引が案内する参照先を日本語訳にまとめた |

## 関係するページ

- [[claude-api-extended-thinking|拡張推論]] に、手動の `budget_tokens` を指定する方式から適応型推論へ切り替える手順と設定例がある。
- [[claude-thinking-troubleshooting|推論のトラブルシューティング]] に、モデルが受理する推論モードと、設定に起因する 400 エラーの診断がある。
