# 日本語PDF向け大規模ローカルRAG設計方針

## 目的

約100GBの日本語PDFを対象とするローカルRAGシステムを構築する。

重視する要件:

- 高速検索
- 小容量インデックス
- 日本語検索品質
- ローカルPC運用
- 将来的な拡張性

以下を実現すること。

- 検索応答時間 1秒以内
- メモリ消費量 16GB以下
- インデックスサイズ 10〜30GB程度
- 高い検索精度

---

# 基本方針

採用:

- Hybrid RAG
- Hierarchical RAG
- BM25検索
- ベクトル検索
- Rerank検索

非採用:

- GraphRAG
- Agent主体の再帰検索
- PDF全件への直接ベクトル検索
- 全文書フラットインデックス

Agentは検索には使用せず、回答生成や要約に限定すること。

---

# 埋め込みモデル

採用:

bge-m3

要件:

- 日本語対応
- 多言語対応
- 長文対応
- Hybrid Search対応

埋め込み次元:

1024

---

# Vector Database

採用:

Qdrant

要件:

- HNSW
- Disk Storage
- Payload Index
- Quantization対応

---

# データ前処理

PDFからテキスト抽出する。

抽出後:

PDF
↓
Markdown変換
↓
構造化
↓
Index作成

文書構造は以下を保持する。

- ファイル名
- タイトル
- 章
- 節
- ページ番号
- 更新日時
- カテゴリ

---

# 階層インデックス

2層構造ではなく3層構造を採用する。

## Layer 1: Summary Index

目的:

対象文書の絞り込み

データ単位:

- PDF単位
- 章単位

保存内容:

- タイトル
- 要約
- メタデータ

検索対象:

- BM25
- bge-m3

---

## Layer 2: Detail Index

目的:

詳細検索

チャンクサイズ:

500〜1000文字

オーバーラップ:

100〜200文字

保存内容:

- 本文
- セクション情報
- ページ番号

検索対象:

- BM25
- bge-m3

---

## Layer 3: Candidate Pool

目的:

最終候補生成

保存不要

検索時に生成する。

候補数:

30〜200件

---

# Hierarchical Search Flow

以下の順序を厳守すること。

Query
↓
Summary Index
↓
上位50文書取得
↓
Detail Index
↓
上位200チャンク取得
↓
Hybrid Search統合
↓
上位30チャンク抽出
↓
Cross Encoder Rerank
↓
上位10チャンク抽出
↓
LLM回答生成

全文書検索は禁止。

必ず段階的に絞り込む。

---

# Hybrid Search

スコア配分:

初期設定

BM25 = 70%

Vector = 30%

技術文書ではキーワード一致を優先する。

問い合わせ内容に応じて以下を許可する。

技術用語検索:

BM25 80%
Vector 20%

概念検索:

BM25 50%
Vector 50%

---

# Reranking

Cross Encoderによる再ランキングを行う。

推奨モデル:

- bge-reranker-v2-m3
- bge-reranker-large

処理対象:

Top 30チャンク

出力:

Top 10チャンク

目的:

- 関連性向上
- ノイズ除去
- 誤ヒット削減

---

# Qdrant Quantization

以下の条件を満たしたら有効化する。

## Condition A

総ベクトル数

5,000,000件以上

---

## Condition B

推定ベクトルサイズ

20GB以上

---

## Condition C

Qdrantコレクションサイズが

利用可能RAMの50%以上

---

## Condition D

検索レイテンシ

500ms以上

---

条件を一つでも満たした場合は量子化を有効化する。

---

# Quantization Strategy

優先順位

1. Scalar Quantization (Int8)
2. Product Quantization

最初は必ず:

Scalar Quantization

を適用する。

想定効果:

- ストレージ 75%以上削減
- メモリ使用量削減
- 検索高速化

検索精度が基準値を下回った場合のみ解除を検討する。

---

# Retrieval Parameters

Summary Index

Top-K:

50

---

Detail Index

Top-K:

200

---

Hybrid Merge

Top-K:

30

---

Rerank

Top-K:

10

---

Context Window

最終投入:

5〜10チャンク

---

# キャッシュ

有効化する。

キャッシュ対象:

- Embedding結果
- Summary検索結果
- Rerank結果

よく利用される問い合わせの再計算を防ぐこと。

---

# スケール方針

データ増加時は以下の順に対応する。

1. Scalar Quantization
2. Product Quantization
3. Detail Index分割
4. Collection Sharding

GraphRAGへの移行は禁止。

---

# 完成アーキテクチャ

User Query
↓
Summary Index
(BM25 + Vector)
↓
Top 50 Documents
↓
Detail Index
(BM25 + Vector)
↓
Top 200 Chunks
↓
Hybrid Merge
↓
Top 30 Chunks
↓
Cross Encoder Rerank
↓
Top 10 Chunks
↓
Qwen3 / Gemma / Local LLM
↓
Answer

この構成を標準構成とする。


100GBの日本語技術PDFなら、この構成は「GraphRAGよりはるかに軽量」でありながら、検索精度はかなり高くなります。特に Summary → Detail → Rerank の3段階検索 が効いて、ベクトルDBサイズと検索時間を大きく抑えられます。GraphRAGを導入するのは、数十万〜数百万エンティティの関連分析が必要になった時だけで十分です。