---
type: "source"
title: "info-hive と myKG のアーキテクチャ比較を更新した記録"
raw: "raw/experiences/info-hive-architecture-refresh-20261120.json"
raw_ref: "C:/Works/info-hive-dev/raw/experiences/info-hive-architecture-refresh-20261120.json"
raw_sha256: "65da6e77216ea105c3e7980e31df77717585f115c0e32a44c0521476a8234323"
created: 2026-11-20
updated: 2026-11-20
ingested: 2026-11-20
tags: ["wiki設計", "グラフ", "試験"]
---

# info-hive と myKG の比較の更新

2026-11-20 に、公開済み wiki v0.39.0 と rag v0.5.4 のコードを固定して、以前の構成図と導入案を見直した。[[info-hive-wikiのアーキテクチャ-v0.38.1]] は前の版の記録として残す。myKG は [[mykgのアーキテクチャ]] と同じコミットだった。

## 固定した対象

| 対象 | 確認したコミット |
| --- | --- |
| wiki v0.39.0 | `84d149ffc642f5820adf3dd2d583d4350e19a17f` |
| rag v0.5.4 | `9af30c3d46fd1699638ea87c908c8d1bb313bae8` |
| myKG v0.4.10 | `afb0a9c9bafdc49751563b9aa7f59bcf4bb787fb` |

wiki と rag は origin/main と一致する HEAD のファイルを `git show` で確認した。作業中の書き込み・復元処理の変更は、公開済み機能には数えていない。

## 実装を踏まえた訂正

wiki v0.39.0 には、記事・目次・ログを保存する共通の承認計画、ハッシュ、ロック、日誌、保留と再試行がある。以前の「書き込みの日誌を導入する」という案は実装済みとして取り下げた。これは LLM の意味抽出の全工程が自動再開するという意味ではない。

公開版は任意の検証向け拡張である。ontology.yaml、definition.json、互換グラフと6つの Ossie 成果物、wiki の外の raw の根が必要で、初回の候補・計画は開発用 PoC で準備して承認する。有効化すると通常保存と版未指定の読み取りが公開版を使う。記事変更時の公開候補ではグラフを検査・再生成し、同じ `release_id` の記事とグラフを読む。ライブの MCP 検索はハイブリッドだが、公開版の `query` は `mode: lexical` の語彙検索である。版固定は外部の raw や PDF の同梱を意味しない。

公開版では Ossie の WikiArticle / sem_articles の定義も検査し、記事の版を追記するが、通常保存で意味上の主張や履歴を自動確定するものではない。RAG は引き続き独自のモデルと LanceDB を持つ。v0.5.4 には OCR キャッシュの再利用と回収の修正がある。

## 残る導入案

1. 既存語彙を確認し、不足した語彙と具体的な事実を別々に候補化する。既存の引用・状態の欄と保存経路を使う。
2. 意味抽出・表記の正規化・候補評価の中間結果を、原本・語彙・プロンプト・モデルの版に結び付けて再開する。
3. `orphan_typed_nodes` から原文へ戻り、関係の候補と見送りを作る。被リンクのないページとは分ける。

以上は設計上の提案で、精度・速度・費用の改善は測定していない。

## 検証と成果物

- [最新の図解](../../docs/research/info-hive-mykg-architecture-visual-2026-11-20.html) と [参照ファイルの記録](../../docs/research/info-hive-mykg-architecture-sources-2026-11-20.json)。
- 360・375・1024・1440px と明暗の計5条件で表示、操作、横幅、JavaScript 例外、外部依存を検査した。
- [検証の結果](../../docs/agent-runs/2026-11-20-info-hive-mykg-architecture/verification.json)、[Opus のレビュー](../../docs/agent-runs/2026-11-20-info-hive-mykg-architecture/review.md)、[指摘の反証と対応](../../docs/agent-runs/2026-11-20-info-hive-mykg-architecture/review-disposition.md)。抽出の品質や本番の保存先の適性は、この画面の検査では確かめていない。

## 取り込んだ内容と載せたページ

| 内容 | 掲載方法 | 掲載ページ |
| --- | --- | --- |
| 固定した版、前の図の訂正、検証の範囲 | 要約 | このページ |
| v0.39.0 の保存と公開版の読み取り | 追記 | [[info-hive-wiki]] |
