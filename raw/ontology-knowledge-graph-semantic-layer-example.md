---
url: "https://medium.com/@kalingwu/ontology-knowledge-graph-semantic-layer-example-e2df3d47416e"
title: "Ontology vs Knowledge Graph vs Semantic Layer, Shown on One Subscription Business"
fetched_at: "2026-11-19T19:04:17+09:00"
source_sha256: "d49b7c543af1bdc17ad0d120b3a7eb18190e63936eef0fe6c459ba82e25fd202"
source_sha256_of: "dom"
fetch_method: "playwright"
source_lang: "en"
translated_by: "Claude Sonnet 5.5"
fetched_by: "wiki_fetch.py 0.1"
browser_session: "existing"
---

# オントロジー、ナレッジグラフ、セマンティックレイヤーを 1 つのサブスクリプション事業で示す

## *同じ Customer、Subscription、Invoice を、タクソノミー、オントロジー、ナレッジグラフ、セマンティックレイヤーとして作り、それぞれが何に答えられるかを示す。*

[Ka Ling Wu](https://medium.com/@kalingwu?source=post_page---byline--e2df3d47416e------------------------------------------)

読了時間 6 分、2026年11月10日

![Ontology vs knowledge graph vs semantic layer: four stacked cards showing one Customer concept modeled four ways](https://miro.medium.com/v2/resize:fit:1225/1*Psbi95xl1VM6wI1IPOiIMg.png)（未取得）

*1 つの概念を、4 つの表現で示す。*

タクソノミー、オントロジー、ナレッジグラフ、セマンティックレイヤーは、競合する製品であるかのように語られる。しかし、そうではない。これらは 4 つの異なる問いに対する 4 つの答えであり、それを最も手早く確かめるには、小さな事業をこの 4 つの形で作り、同じ質問をそれぞれに投げてみればよい。

その事業は、**Customer**、**Subscription**、**Invoice** の 3 つの概念に、Plan を加えたサブスクリプション企業である。すべての Subscription はいずれかの Plan に属するからだ。質問は次のとおりである。

1. 年額の Subscription は、Subscription の一種か。
2. 1 枚の Invoice を 2 人の Customer に請求できるか。
3. Pro プランで、今まさに支払期限を過ぎた Invoice を持つ Enterprise の Customer はどれか。
4. 先四半期のセグメント別 ARR を、どのツールでも同じ方法で計算するとどうなるか。

![Diagram of one subscription business modeled as a taxonomy, an ontology, a knowledge graph and a semantic layer, side by side](https://miro.medium.com/v2/resize:fit:1225/1*eKZ_wXK3OqjZkodtsEqs8g.png)（未取得）

*それぞれの形は、前の形に 1 つずつ要素を加える。まずカテゴリ、次に関係とルール、次に実データ、最後に計算である。*

## 同じ事業を 4 通りに作る

## タクソノミーが知っているのは「これは何の種類か」だけである

タクソノミーは、is-a（〜の一種）の関係による階層である。これに対する W3C の標準が [SKOS（Simple Knowledge Organization System）](https://www.w3.org/2004/02/skos/)である。この事業では次のようになる。

- Customer → Enterprise Customer、SMB Customer
- Subscription → Monthly Subscription、Annual Subscription
- Invoice → Open Invoice、Paid Invoice、Overdue Invoice

タクソノミーが答えられるのは質問 1 だけで、ほかには答えられない。Subscription から Customer への辺はない。辺の種類が「is-a」しかないからである。「Overdue Invoice」はラベルとしては存在するが、何をもって請求書が期限超過になるのかは、タクソノミーでは表せない。誰かがタグを付けなければならない。

これは欠陥ではない。タクソノミーは、カタログ、サポート用のタグ、コンテンツ管理システムにわたって分類の一貫性を保つ。ただ、物事がどうつながるかについては意見を持たないだけである。

## オントロジーは関係とルールを加えるが、データはまだない

Tom Gruber の広く引用される定義では、オントロジーは[概念化の明示的な仕様](https://tomgruber.org/writing/ontolingua-kaj-1993.htm)である。実際には、カテゴリの上に、型付きの関係、プロパティ、ルールを加えたものになる。[Web Ontology Language（OWL）](https://www.w3.org/OWL/)に対して Turtle で書くと、骨格は短い。

```
:Customer     a owl:Class .
:Subscription a owl:Class .
:Invoice      a owl:Class .
```

```
:holds    a owl:ObjectProperty ;
          rdfs:domain :Customer ;
          rdfs:range  :Subscription .
```

この構造の上に、オントロジーは業務の言葉でルールを述べる。Active Customer とは、状態が active または past due である Subscription を少なくとも 1 つ持つ Customer である。Overdue Invoice とは、支払期限を過ぎた未払いの Invoice である。Invoice は、ちょうど 1 人の Customer に請求される。

これで質問 2 に答えが出る。できない。Invoice に 2 人目の Customer を記録するシステムは誤りである。質問 3 は、オントロジーの用語で厳密に*述べる*ことはできるが、答えることはできない。オントロジーは設計図であり、顧客は 1 人も入っていない。

## ナレッジグラフは、記入済みの設計図である

実際のインスタンスを加えると、ナレッジグラフになる。[Enterprise Knowledge の略式の言い方](https://enterprise-knowledge.com/whats-the-difference-between-an-ontology-and-a-knowledge-graph/)では、オントロジーにデータを足したものがナレッジグラフである。架空のデータで示す。

```
:AcmeCorp a :Customer ;     :holds    :SUB1042 .
:SUB1042  a :Subscription ; :billedBy :INV8873 .
:INV8873  a :Invoice ;      :amount 48000 ; :status "open" .
```

ルールがグラフと一緒に移動するので、推論器は、支払期限が過ぎれば INV-8873 が Overdue Invoice であること、そして Acme Corp が Active Customer であることを、誰もタグを付けなくても推論できる。質問 3 は走査になる。Customer から Subscription、Plan へ、そして Subscription から Invoice へとたどり、推論されたクラスで絞り込む。[Neo4j がうまく述べている](https://neo4j.com/blog/knowledge-graph/taxonomy-vs-ontology-vs-knowledge-graph/)とおり、ナレッジグラフは作るものであり、タクソノミーとオントロジーはその設計図である。

グラフが得意としないのは質問 4 である。グラフ上で Invoice の金額を合計することはできるが、ARR が active と past-due の Subscription に対する月次経常収益の 12 倍であることや、その数字がダッシュボード、スプレッドシート、Slack のボットで一致しなければならないことは、グラフのどこにも書かれていない。

## セマンティックレイヤーは、数字を決定論的にする

[セマンティックレイヤー](https://upsolve.ai/blog/semantic-layer-ai)は、同じ概念をウェアハウスのテーブル（`dim_customers`、`fct_subscriptions`、`fct_invoices`）に対応づけ、それらの間の結合を宣言し、SQL にコンパイルされる指標を定義する。

- **ARR** = `SUM(fct_subscriptions.mrr) * 12`（ただし `status IN ('active', 'past_due')`）
- **Overdue AR** = `SUM(fct_invoices.amount)`（ただし `status = 'open' AND due_date < CURRENT_DATE`）
- **ディメンション:** segment、region、plan

質問 4 は、セマンティックレイヤーが答えるために作られたものである。ARR は、それを問い合わせるどのツールでも、毎回同じようにコンパイルされる。表現力はオントロジーより低い。クラスについて推論できず、Invoice に 2 人の Customer が付くことも止められない。ただし、誰も二重に数えないことは保証する。

ここで「active」がどこに置かれたかを見てほしい。タクソノミーではラベルである。オントロジーではルールである。ナレッジグラフでは、Acme Corp についての推論された事実である。セマンティックレイヤーでは、指標の内部に埋め込まれた `WHERE` 句である。**同じ業務上の概念に 4 つの置き場所があり、その 4 つが食い違えば、システムも食い違う。**

## スコアカード: それぞれ反対の場所で失敗する

![Scorecard of which questions a taxonomy, ontology, knowledge graph and semantic layer can answer for a subscription business](https://miro.medium.com/v2/resize:fit:1225/1*cllwwpW7EmO-GizfloClYw.png)（未取得）

*4 つの質問と 4 つの形。「Partial（部分的）」は、その形が質問を表現できるが、答えることはできないことを意味する。*

採点すると、2 つの点が目に付く。

1 つめは、セマンティックレイヤーとナレッジグラフが、反対の場所で強いことである。dbt Labs の[2026 年のベンチマーク](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026)は、その境目をはっきり示している。dbt Semantic Layer は、引き受けた質問の 100% に答えた。範囲外の質問は、「MetricFlow には、たどるエンティティの数が多すぎる」ものだった。多段のたどり（Many-hop traversal）こそ、グラフが得意とすることである。逆に、取締役会の資料に載る指標の定義を置く場所として、グラフは向いていない。

2 つめは、ほかのどの形も、静かにオントロジーに依存していることである。data.world が、企業の保険に関する質問で GPT-4 を評価したとき、SQL では[正答率が 16.7%、オントロジーに基づくナレッジグラフでは 54.2%](https://arxiv.org/abs/2311.07509) だった。業務データは同じである。変わったのは、その意味がどれだけ明示的に書かれていたかである。

## 2026 年には、4 つの箱が製品の中で融合しつつある

4 つのパネルをきれいに分けた図は、ぼやけてきており、その理由は Microsoft の Fabric IQ が示している。まだプレビュー段階の[オントロジー項目](https://learn.microsoft.com/en-us/fabric/iq/ontology/overview)は、エンティティ型、関係、自然言語のルールを保持する。Power BI のセマンティックモデルから生成でき、その DAX のメジャーを指標として引き継ぐが、「元のセマンティックモデルが DAX 式の所有者であり続ける」。グラフ（Graph）は、多段の質問のための「任意の実行レイヤー」と説明されている。これは、オントロジー、ナレッジグラフ、セマンティックレイヤーが 1 つの製品に入ったものであり、計算の所有者は依然としてセマンティックモデルである。

用語は、職種をまたぐと安定しない。ナレッジマネジメントの界隈では、[Enterprise Knowledge は、タクソノミー、オントロジー、ナレッジグラフの*上に*築かれるセマンティックレイヤー](https://enterprise-knowledge.com/what-is-the-difference-between-a-semantic-layer-and-a-context-layer/)を説明している。これは、アナリティクスエンジニアがこの語を使う方法とほぼ逆である。どちらがどちらを含むかで 2 人が言い争っているときは、一方が司書から、もう一方が dbt のプロジェクトから、その言葉を学んだのではないかと確かめる価値がある。

## アナリティクスチームが実際に作るべきもの

私の考えはこうである。多くのアナリティクスチームにとって正しい答えは、軽いオントロジーとセマンティックレイヤーであり、完全なナレッジグラフは、多段の質問が主な作業負荷であるときに限る。

軽いオントロジーに、OWL もトリプルストアも要らない。それは運用上の最小限である。業務の言葉で記述されたエンティティ、関係として宣言されたキー、「active customer」のようなルールを 1 度だけ書いたもの、そして status のような列の取りうる値を、人間やエージェントが読める場所に記録したものである。そのうえで、セマンティックレイヤーが、人々が実際に議論している少数の指標を、コンパイルされた SQL にする。

**「どの Customer が X の影響を受けるか」に答えるために 5 つの結合を持つクエリを書き続けているなら、それがグラフの出番が来たという合図である。** そうなるまでは、4 つの中で維持に最も費用がかかり、最も使われないことが多い。

Palantir の Ontology や 2026 年のベンダーのオントロジーがこの図にどう収まるかを含む、より長い解説は、私たちの[データオントロジーの解説](https://upsolve.ai/blog/data-ontology?utm_source=medium&utm_medium=referral&utm_campaign=agent-stack&utm_content=ontology-vs-knowledge-graph)にある。
