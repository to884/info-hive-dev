---
type: "source"
title: "データプラットフォームからエージェントが機能するアーキテクチャへ: Knowledge Catalog、Ossie、GenAI"
authors: ["Ahmet Kalafat"]
url: "https://medium.com/@ahmet.kalafat/veri-platformlar%C4%B1ndan-ajanlar%C4%B1n-%C3%A7al%C4%B1%C5%9Fabildi%C4%9Fi-mimarilere-knowledge-catalog-ossie-ve-genai-bc212259184f"
raw: "raw/knowledge-catalog-ossie-genai.md"
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
tags: ["グラフ"]
---

# データプラットフォームからエージェントが機能するアーキテクチャへ: Knowledge Catalog、Ossie、GenAI

Medium の記事（Ahmet Kalafat、2026-11-01、原文はトルコ語）。2026年10月に発表された Google Knowledge Catalog、Apache Ossie、Dataflow、GPT‑6.1 Terra、BigQuery のクロスプラットフォームのクエリを、「AI エージェントがデータを正しく使うには何が要るか」という問いで評価する。raw は日本語訳で、図 13 枚は取得できず本文だけである。行番号は raw のものである。

## 主な主張

- Knowledge Catalog は、Looker LookML、dbt MetricFlow、Snowflake Semantic Views などのセマンティック定義を共通のコンテキストグラフにまとめる。指標の計算式、フィルター、join、lineage、品質のシグナルを合わせて評価できる（L34〜L36）。
- エージェントには、正しい SQL を作ることと同じくらい、正しいビジネス定義を選ぶことが重要である。どの定義をどの目的で使うかを決める責任は、組織に残る（L52〜L54）。
- Apache Ossie は、指標、ディメンション、リレーションシップ、ビジネス上の意味をツール間で共有するオープンな標準で、Apache Incubator の段階にある。Ossie は定義の可搬性、Knowledge Catalog は定義を発見して関連づけ、エージェントに文脈として渡すことに焦点がある（L58〜L65）。
- 著者は、2 つは補完し合える可能性があるとみる。ただし Google の発表は Ossie との直接の対応を挙げておらず、用意された統合として評価してはならない（L71）。
- 共通のフォーマットでも、組織内の定義の違いは解消されない。「純売上」の 2 つの計算式を同じ標準で書くことはできるが、どちらをどの文脈で使うかは、データモデリングとガバナンスの仕事である（L73）。
- コンテキストにはライフサイクルがある。Google が Preview で発表した self-learning context enrichment と Knowledge Studio は、エージェントのやり取りから欠けた文脈や古い文脈を見つけ、修正案をソースと信頼度つきで出す。観察、特定、提案、検証、公開、再測定のループになる（L85〜L101）。
- Google が報告した社内ベンチマークは、精度約 4 倍、レイテンシ最大 33% 減、トークン使用量最大 75% 減。独立したテストではなく、1 つの性能スコアにまとめられない。著者は、スキーマだけの構成と検証済みの文脈つきの構成を同じ質問で比べる試行を勧める（L105〜L119）。
- アクセス（Iceberg、フェデレーション、shortcuts）、セマンティックの可搬性（Ossie）、組織の文脈の提供（Knowledge Catalog、Fabric IQ）は、別の責任である。テーブルを読めることと正しいビジネス上の結果を出すことの間には、大きな距離がある（L228〜L242）。
- Dataflow のレイテンシレベル、GPT‑6.1 Terra のコンピューター操作、Microsoft 側の対応機能も扱う。いずれも製品の発表の整理で、この wiki の主題から外れる（L133〜L224）。

## 信頼度と限界

- 著者個人の見方の記事で、Ossie と Knowledge Catalog の関係は著者の推測である。Ossie と Google の公式資料は、この取り込みでは確かめていない。
- ベンチマークの数値は Google の社内の結果を引いたものである。
- 図 13 枚は未取得で、図の中身は取り込めていない。frontmatter の `source_lang: en` は誤記で、原文はトルコ語である。

## この wiki との関係

[[オントロジーの要件とOssieへの引継ぎ]] が Ossie の採用検討で照らす「責任範囲」の論点（定義管理・検証・推論と、抽出・名寄せ・承認の境界）に、外部の見方として重なる。記事の「標準を採用しても、定義の選択と承認は組織に残る」は、info-hive が承認を担う側の前提を支える。Ossie の中身は未確認である。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | Ossie は定義の可搬性、Knowledge Catalog は定義の発見と関連づけで、層が違い補完しうる。Google は直接の対応を挙げていない | L58〜L71 | `update` | [[オントロジーの要件とOssieへの引継ぎ]] に外部の見方として追記した。採用検討で参照されるため |
| c2 | 共通フォーマットでも定義の違いは解消されず、選択と承認はガバナンスに残る | L73、L52〜L54 | `update` | [[オントロジーの要件とOssieへの引継ぎ]] の責任範囲の論点に結びつけた |
| c3 | コンテキストの更新ループと、Google の社内ベンチマーク | L85〜L119 | `source_only` | 著者の紹介と Google の社内の結果で、独立した検証がなく、wiki の概念ページに足す根拠が足りない |
| c4 | Dataflow、GPT‑6.1 Terra、BigQuery のクロスプラットフォームのクエリ、Microsoft 側の対応 | L133〜L224 | `source_only` | この wiki の主題（オントロジーと知識グラフ）から外れる製品の発表の整理 |

## 関係するページ

- [[オントロジーの要件とOssieへの引継ぎ]]
- [[実体を単位にするオントロジー]]
- [[オントロジーと知識グラフの役割]]
