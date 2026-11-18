---
type: "source"
title: "Build an Agentic Knowledge Graph From Scratch: No Graph DB, No Extraction Model"
authors: ["Saurabh"]
url: "https://medium.com/@saurabhraj042/build-an-agentic-knowledge-graph-from-scratch-no-graph-db-no-extraction-model-074d944a68b3"
raw: "raw/build-an-agentic-knowledge-graph-from-scratch-ja.md"
ingested: 2026-11-17
created: 2026-11-17
updated: 2026-11-17
tags: ["グラフ", "検索", "wiki設計"]
concepts: ["既存リンクからのグラフ検索", "エージェントに守らせる決まりの書き方"]
---

# 既存リンクから作るグラフと、根拠を確かめるエージェント

Saurabh が 2026-10-31 に公開した設計の記事。日本語訳を `raw/build-an-agentic-knowledge-graph-from-scratch-ja.md` に保存した。本文の訳と図 6 点の補足は GPT-6 による。コードブロック、インラインのコード、リンク先、画像の記法は原文のまま残した。翻訳元の英語版 `raw/build-an-agentic-knowledge-graph-from-scratch.md` は変更していない。

## 要点

資料にリンクがあれば、その構造を解析してグラフを作れる。Parquet と DuckDB に保存し、CSR の配列と双方向の幅優先探索で経路を探す。BM25 は探索の入口を見つける役である（[[既存リンクからのグラフ検索]]）。

経路の存在だけでは、関係の意味は決まらない。本文も読み、引用と経路の根拠をコードで照合する構成を提案する。評価では正答と引用の精度に加え、適切な見送りと誤った見送りを分ける。

## 検証の範囲

著者が確かめたのは合成データや小さなグラフの部品で、実際の Wikipedia を使う全工程は未検証である。最終回答の検査器のコードも掲載されていない。他記事から引いた性能・費用の数値を、この方式の測定結果として扱わない。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | 明示的なリンクがある資料では解析からグラフを作れる | raw「中心となる発想」 | `create` | [[既存リンクからのグラフ検索]] に適用条件を残した |
| c2 | 型のない経路は意味の裏づけを別に要する | 同節の「引き換えに失うもの」 | `create` | [[既存リンクからのグラフ検索]] に限界を残した |
| c3 | 回答の採否を、経路と引用の照合で判定する設計である | raw「手順 5」 | `update` | [[エージェントに守らせる決まりの書き方]] に提案と検証の範囲を追記した |
| c4 | 見送りの正しさも評価する | raw「手順 6」 | `source_only` | 本記事の評価案として残した |
| c5 | 実データの全工程は未検証である | raw「率直な限界」 | `source_only` | 部品の検証と全体の実証を分けた |

> 取り込んだ内容と載せたページ 補足: 根拠の位置は保存した日本語の raw を指す。この記事は info-hive の実装を評価していない。

## 関係するページ

- [[既存リンクからのグラフ検索]]
- [[エージェントに守らせる決まりの書き方]]
- [[グラフの抽出の契約]]: info-hive 固有の抽出の契約
