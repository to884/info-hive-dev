---
title: "LLM Wiki の記事からナレッジグラフを作る方法"
date: 2026-11-17
language: ja
research_mode: standard
status: research
---

# LLM Wiki の記事からナレッジグラフを作る方法

日本語・英語の一次資料を基に、抽出方法と保存方法を比較する。調査日: 2026年11月17日。

## 要旨

**LLM Wiki では、既存のリンクと構造化メタデータを規則で抽出し、本文にしかない関係を必要に応じて LLM で補う方法を提案する。保存先は別に選べる。** LLM の使用とグラフDBの使用は独立した判断であり、四つの組み合わせが成立する。SQLite は通常の表からグラフを照会でき、Microsoft GraphRAG 自身も既定の出力を Parquet ファイルに保存する。[29](https://www.sqlite.org/lang_with.html)[41](https://microsoft.github.io/graphrag/index/outputs/)[25](https://github.com/HKUDS/LightRAG)

LLM Wiki の元の提案は、LLM が相互参照された Markdown を継続的に整備する方式である。したがって、記事を作る段階で LLM を使っていても、その記事からリンクや frontmatter を読む段階は LLM なしで実行できる。本レポートの「LLM 使用」は、主に後者のグラフ構築工程についての区分である。info-hive でも、Markdown を正本とし、明示された関係を JSONL・SQLite・GraphML に変換する仕組みを確認した。[1](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

抽出対象は、記事へのリンク、人物・組織・概念などの実体、実体間の意味を持つ主張に分ける。リンクがあるという事実と、その相手に依存するという主張を区別する。LLM が本文から提案した関係には、元の記事・版・根拠の位置・抽出方式・採否を残す。スキーマや構造化出力の制約は形式の整合に役立つが、根拠が関係を支持するかは別に判定する必要がある。[4](https://obsidian.md/help/links)[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[23](https://arxiv.org/abs/2308.02357)

保存先は、個人・ローカルの wiki なら JSONL と SQLite、経路照会を中心に使う共有サービスなら Neo4j、RDF の語彙や SPARQL を共有したいなら Jena TDB2 と Fuseki を候補とする。この選択は運用要件から導いた提案であり、速度の実測結果ではない。専用DBを導入する前に、未解決の名前、根拠のない関係、記事の変更・削除に追随しない索引を検出する仕組みを整える方針を推奨する。[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[29](https://www.sqlite.org/lang_with.html)[36](https://jena.apache.org/documentation/tdb2/)[35](https://jena.apache.org/documentation/fuseki2/index.html)

## 調査の範囲と前提

対象は、Markdown の記事群、YAML frontmatter、記事間の wikilink、参照元の資料を持つ LLM Wiki である。PDF の OCR や、画像からの図表認識を中心とする処理は対象外とした。記事作成・検索での LLM 利用と、記事からグラフを作る際の利用を分けて扱う。Karpathy の原案を出発点に、構造化されたリンクの解析、自然言語からの実体・関係抽出、グラフのモデル、永続保存、更新と評価までを調査した。[1](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

「LLM を使用しない」は、モデルを一切使わない処理に限らない。辞書・規則だけを使う処理、学習済みの形態素・係り受け・固有表現解析を使う処理、汎用の生成 LLM を呼ばずに専用の関係抽出器を使う処理を区別する。とくに BERT 系のエンコーダと BART 系の生成器を一括して「LLMなし」とすると、ユーザーが避けたい費用や依存関係が曖昧になる。[8](https://megagonlabs.github.io/ginza/)[12](https://aclanthology.org/2021.naacl-main.5/)[13](https://aclanthology.org/2021.findings-emnlp.204/)

以下では、原典の仕様・実験を述べる段落には直近に出典を付ける。「提案」「推奨」「判断」と明記した箇所は、原典を踏まえた本調査の考察である。info-hive の現状は、2026年11月17日の作業ツリーのスキーマとコードを読んだ結果であり、公開済みの特定バージョンを確認したという意味ではない。未コミットの変更があるため、対象ファイルの SHA-256 を証拠台帳に記録した。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

## 主要な調査結果

### 1. 記事のリンクと、実体間の主張を分ける

最初に、何をノードにし、エッジにどの意味を与えるかを決める。Obsidian の内部リンクは記事や見出しへの参照を記述する。RDF は主語・述語・目的語の形で知識を表現する。Neo4j のプロパティグラフではノードと型付きの関係に属性を持たせられる。これらを踏まえ、本調査では記事、実体、主張という三つの対象を区別する。[4](https://obsidian.md/help/links)[31](https://www.w3.org/TR/rdf11-concepts/)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)

記事をノードにし、`[[SQLite]]` を `links_to` として取り出すと、どの記事が何を参照しているかを調べられる。この例の述語は本レポートでの説明用であり、info-hive は本文の wikilink を `mentions` として出力する。コードのブロックやリンクの表示名、同名記事、見出し指定の解釈は、実装先のパーサーの契約に合わせる。外部ツールのリンク仕様をそのまま info-hive の仕様として扱わない。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)[4](https://obsidian.md/help/links)

実体をノードにすると、記事をまたいで同じ会社や製品を扱える。表示名と識別子は分離する。たとえば日英の別名を辞書で一つの ID に結び付ける運用は可能である。ただし、名前が一致することだけで同一の実体と決めると、同姓同名や略語の衝突を区別できない。Obsidian は異言語表記や略語の aliases を扱い、Neo4j の既定の実体統合は label と name の一致を使う。この機能と文脈に基づく曖昧性解消は区別する。[5](https://obsidian.md/help/aliases)[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)

主張は、誰が、いつ、どの資料を根拠に、何と何の間の関係を記述したかを表す。たとえば「記事Aは製品Bに言及する」と「製品Bは機能Cを提供する」は異なる。原文が将来計画を述べているなら、現在の提供機能として保存しない。info-hive の型付き関係には `source`、`evidence`、`confidence`、`status` があり、任意で有効期間や元の資料への参照も記録できる。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)

この区別から、本文の共起は `co_occurs_with`、単なる参照は `mentions` のように、根拠から直接確認できる関係として残す設計を提案する。共起数やリンク数を、そのまま `causes` や `depends_on` の根拠に使わない。隣接している実体の関係を意味付けるには、関係抽出や原文の確認を追加する。T2KG がトリプル抽出、実体の対応付け、述語の対応付けを分離していることも、この工程の分担を支持する。[15](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf)

LLM Wiki の記事は既に加工された情報である。記事から関係を取り出しても、元資料との対応を失うと、要約段階の誤りを再利用する可能性がある。ここからは、`raw → wiki記事 → 抽出された主張` の由来を保持する設計を提案する。PROV-O は生成や派生の関係を表す語彙を提供し、GraphRAG は抽出された要素と TextUnit を対応付ける。どの方式でも、グラフから根拠の本文へ戻る道を維持する。[32](https://www.w3.org/TR/prov-o/)[16](https://microsoft.github.io/graphrag/index/default_dataflow/)

### 2. LLM を使わずに構築する方法は、構造の解析から関係抽出まである

**最も導入しやすい方法は、記事内に既に明記された構造を読むことである。** frontmatter のノードID、別名、出典、型付き関係と、本文のリンクを解析する。新しい意味を推定しないため、抽出結果と入力の対応を検査しやすい。info-hive の既存抽出器は、この種類の処理を行い、型付き関係と、wikilink・出典から作る関係を同じ出力形式にまとめる。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

| 方法 | 記事から得るもの | 学習モデル | 適する条件と残る作業 |
|---|---|---|---|
| wikilink・frontmatter の解析 | 記事間の参照、明示された関係 | 不要 | 記事に構造がある。未知の意味関係は別途記述する |
| 辞書・文字列の規則 | 既知の名前、定型文の関係候補 | 不要にできる | 用語と文型を絞れる。辞書外の表記や省略を扱う必要がある |
| NER・係り受け解析＋規則 | 本文の実体、文法的な接続に基づく候補 | 多くの場合は使用 | 日本語の解析器を指定し、文法を業務の述語へ対応付ける |
| OpenIE＋実体・述語の統合 | 自由な関係句のトリプル | パイプラインによる | 自由な述語を採用するか、固定語彙に対応付ける |
| 教師あり関係抽出 | 決めた型の関係 | 使用 | 対象分野のデータ、学習・評価・保守を用意する |

表は各公式資料から整理した分類であり、方式の精度順位ではない。spaCy は辞書と規則を使う `EntityRuler` や各種の Matcher を提供する。複数の表記に同じ `id` を与えることもできる。形態素の属性などを条件に使う場合は、それを設定する解析器も必要になる。[6](https://spacy.io/usage/rule-based-matching/)

係り受けを使うなら、たとえば「X が Y を開発した」という文型から `developed` の候補を作る。ただし、spaCy の `DependencyMatcher` は依存構造を設定する処理を必要とする。規則による照合でも、入力を作る段では学習済みモデルを使いうる。日本語では GiNZA が固有表現と依存構造の解析を提供する。`ja_ginza` と、事前学習 Transformer を使う `ja_ginza_electra` などを区別して選ぶ。[7](https://spacy.io/api/dependencymatcher)[8](https://megagonlabs.github.io/ginza/)

日本語の表記ゆれには SudachiPy の `normalized_form()` も利用候補になる。文字の正規化、語の正規形、実体の同一性は別の処理である。「株式会社」を取り除いて同じ文字列になったことだけで組織を統合する、といった規則は本調査では推奨しない。既知の別名を明示的な ID に結び付け、曖昧な候補を残す運用を提案する。[9](https://worksapplications.github.io/sudachi.rs/python/api/sudachipy.html)[5](https://obsidian.md/help/aliases)

自然言語の本文からトリプルを取り出す方法として、Stanford CoreNLP の OpenIE は主語・関係・目的語の抽出を提供する。T2KG は、実体の対応付け、照応解析、トリプル抽出、トリプル統合、述語の対応付けを組み合わせた全体構成を示す。ただし、CoreNLP の公式対応言語一覧に日本語は含まれない。英語向けの構成例を、日本語記事でもそのまま使える方式として勧めることはできない。[10](https://stanfordnlp.github.io/CoreNLP/openie.html)[15](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf)[11](https://stanfordnlp.github.io/CoreNLP/)

教師あり手法では、PURE のように実体抽出と関係抽出のエンコーダを分ける構成がある。汎用のチャット LLM を都度呼ばずに関係を分類できる一方、事前学習言語モデルを使うため、モデル不使用には当たらない。REBEL は BART を用いてトリプルを生成する方式である。こちらも「生成言語モデルを使わない」という制約なら候補から外れる。これらの境界はモデル名より、許容する処理と依存関係で決めるべきである。[12](https://aclanthology.org/2021.naacl-main.5/)[13](https://aclanthology.org/2021.findings-emnlp.204/)

日本語の省略も残る。主語や目的語が前の文にしか現れない場合、近い名詞を接続する規則だけでは対応できない。日本語述語項構造解析の研究では、局所的な手がかりの連鎖を全体で解釈する必要がある事例を分析している。LLM を使わない構成では、抽出対象の述語や文型を絞り、判定できない文を未解決として残す案が現実的と判断する。[14](https://www.jstage.jst.go.jp/article/jnlp/22/5/22_433/_article/-char/ja/)

### 3. LLM では、許可した関係と根拠を持つ候補を抽出する

LLM を使う場合は、本文を見出しや段落単位で区切り、実体候補、実体ID、関係型、根拠を出力させる。固定スキーマの抽出なら、許可するノード型、述語、主語と目的語の型を先に与える。Neo4j GraphRAG Python は、手動のスキーマ、LLM が導出する `EXTRACTED`、制約しない `FREE` を提供する。LangChain の `LLMGraphTransformer` でも許可型やプロパティを指定できる。[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[19](https://reference.langchain.com/python/langchain-neo4j/graph_transformers/llm/LLMGraphTransformer)

| 候補 | 主な役割 | LLM Wiki で使う際の判断 |
|---|---|---|
| `LLMGraphTransformer` | 本文を GraphDocument に変換 | 独自の検証・保存工程に組み込む抽出器の候補 |
| Neo4j GraphRAG Python | 分割、抽出、実体統合、保存を組む | スキーマ誘導を試せる。現行の該当機能は experimental |
| Neo4j LLM Graph Builder | 文書の投入とグラフの確認をする UI | 記事・チャンクのグラフと実体のグラフを見比べる試作向け |
| Microsoft GraphRAG | 実体グラフとコミュニティ要約を構築 | 文書群全体の傾向を問う用途で必要性を評価 |
| LightRAG | グラフとベクトルを用いる検索構成 | グラフDBなしでも試せる。複数ストアの運用も考慮 |

表の機能は公式資料に基づく。各製品が同じグラフを作るという意味ではない。Neo4j の UI は Document・Chunk の lexical graph と entity graph を区別する。Microsoft GraphRAG は TextUnit から実体や関係を抽出した後、統合、説明の要約、コミュニティの形成・要約へ進む。記事リンクを閲覧したいだけの場合に、この全工程が必要かは別に判断する。[20](https://neo4j.com/developer/genai-ecosystem/llm-graph-builder-features/)[16](https://microsoft.github.io/graphrag/index/default_dataflow/)[17](https://arxiv.org/abs/2404.16130)[25](https://github.com/HKUDS/LightRAG)

日本語で書かれた NTT DATA の一次実験は、自作レシピの Markdown で三つのスキーマ方式を比較している。目的に合う関係を得るには手動スキーマが役立った一方、同一のスキーマと入力形式でもノード名などの揺れがあったという。小規模な事例のため、すべての日本語記事での精度や、製品間の順位は結論できない。[21](https://zenn.dev/nttdata_tech/articles/266a6692f85fee)

LLM への指示として、次のような制約を提案する。これは本レポートの抽出方針の例であり、実測して有効性を確認したプロンプトではない。

```text
入力の段落と渡した実体候補だけを根拠に、関係の候補を返す。
predicate は指定した語彙から選び、根拠の文と位置を付ける。
否定・推測・予定・引用者の意見・有効期間を区別する。
別名候補を同一実体へ統合する根拠がなければ unresolved にする。
支持できる関係がなければ空の配列を返す。
出力は候補であり、採用済みの知識として書き込まない。
```

JSON の形式や型を満たしたかの検証と、主張の意味が本文に支持されるかの検証を分ける。`strict_mode` は許可されていない型を除外できるが、誤った関係が許可型で出力された場合の事実性を証明しない。Text2KGBench が抽出性能、オントロジーへの適合、幻覚を別の指標として測ることも、この区別を支持する。[19](https://reference.langchain.com/python/langchain-neo4j/graph_transformers/llm/LLMGraphTransformer)[23](https://arxiv.org/abs/2308.02357)

名寄せには別の判定を置く。東京大学の日本語事例では、埋め込みとクラスタリングだけで意味の異なる表現を同じ群へまとめる問題を報告し、LLM を併用して表現を整理している。ここからは、埋め込みを候補の絞り込みに使い、同一性の採否を別に判断する設計を提案する。類似度の高さだけで、正反対の事象や別の組織を統合しない。[24](https://dss.i.u-tokyo.ac.jp/blog/practical-graph-rag-1/)

### 4. 同じ関係を支持する、複数の主張と証拠を残す

保存方法を選ぶ前に、関係のどの情報を残すかを決める。RDF はトリプルを集合として扱う。Neo4j では関係に属性を付けられる。PROV-O は生成や派生の由来を表す語彙を提供する。これらのどれを使っても、「同じ関係を別の記事がそれぞれ支持している」という情報を保存する方法は明示的に設計する必要がある。[31](https://www.w3.org/TR/rdf11-concepts/)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[32](https://www.w3.org/TR/prov-o/)

ここでは、検索のために集約した関係と、記事ごとの根拠を分ける案を提案する。`relations` に主語・述語・目的語と、肯定・否定や成立条件の区別を置き、`assertions` にその主張を記述する記事、版、根拠、抽出方法、採否を置く。記事Aを削除しても記事Bの支持が残るなら、関係自体を削除しない。逆に、支持が一つもなくなった関係は、通常の採用済みグラフから除く。否定する主張や異なる条件の主張を、肯定する関係の支持件数へ足さない。これは本レポートのモデル案であり、既存 info-hive の必須スキーマへの変更提案を確定したものではない。

次は架空の資料を用いた候補レコードの例である。`decision_status` と、主張が指す時点の状態である `temporal_status` を分けた。ID・型・期間の妥当性を検証する処理も別途必要である。

```json
{
  "assertion_id": "assertion:demo-001",
  "subject_id": "product:demo-a",
  "predicate": "depends_on",
  "object_id": "product:demo-b",
  "polarity": "positive",
  "qualifiers": [],
  "article_id": "page:demo-article",
  "article_revision": "git:demo-revision",
  "source_id": "source:demo-specification",
  "source_revision": "sha256:demo-content-hash",
  "locator": {"section_id": "requirements", "span_id": "sentence-3"},
  "evidence": "製品Aの実行には製品Bが必要である。",
  "extraction_method": "llm_schema_guided",
  "extractor_version": "demo-prompt-v1",
  "decision_status": "proposed",
  "temporal_status": "current",
  "valid_from": null,
  "valid_to": null
}
```

行番号だけでは編集によって根拠がずれるため、版や内容のハッシュと組み合わせる案を推奨する。書類で説明されている出来事の有効期間と、索引へ取り込んだ時刻も分ける。過去の関係や、争われている関係を、現在有効な関係だけの照会に混ぜない。info-hive の現行スキーマにも `status` と `valid_from`・`valid_to` があるため、この情報を失わないエクスポートを優先する。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)

エッジの集約キーにも注意する。「同じ主語・述語・目的語」を集約する場合でも、期間、否定、条件、記事ごとの証拠を消さない。info-hive の抽出器は、記述したページや関係の属性などをエッジ識別子に含める。既存出力を専用DBへ送る際、三つ組の一致だけで上書きすると、元の出力が区別していた根拠を失う。移行用の変換では、元のエッジIDと記事IDを保持する案を推奨する。[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

RDF なら名前付きグラフを記事の版ごとに対応付ける方法が考えられる。ただし、RDF の仕様は、グラフ名が何を指すかを一意に固定しない。名前付きグラフを使うだけで出所が明確になるわけではなく、記事・版・抽出処理との対応規約を定める必要がある。関係ごとに異なる採否や期間を記録するなら、主張を別のリソースとして表現する案もある。[31](https://www.w3.org/TR/rdf11-concepts/)[32](https://www.w3.org/TR/prov-o/)

SHACL は RDF グラフを条件に照らして検証できる。必須の出典、ノードの型、値の種類などを検査する用途に合う。たとえば出典プロパティが存在しても、その文書が主張を支持するとは限らない。構造の検査と、証拠の意味の確認を分担する構成を提案する。[33](https://www.w3.org/TR/shacl/)[23](https://arxiv.org/abs/2308.02357)

### 5. グラフDBを使わなくても、保存・探索・交換はできる

グラフはデータの構造であり、グラフDBはそれを扱う保存・照会の選択肢である。RDF はファイルにも保存できる。SQLite は通常の edge テーブルと再帰 CTE によるグラフ照会を公式資料で示している。Microsoft GraphRAG の既定の索引出力も、Parquet ファイルの表である。これらから、グラフDBの導入を、ナレッジグラフ構築の前提条件にする必要はないと判断する。[31](https://www.w3.org/TR/rdf11-concepts/)[29](https://www.sqlite.org/lang_with.html)[41](https://microsoft.github.io/graphrag/index/outputs/)

| 保存手段 | 主な用途 | 必要になる追加設計 |
|---|---|---|
| Markdown の frontmatter | 人が読める正本と関係の編集 | 対象ページの特定、型とリンクの検証、索引の再生成 |
| JSONL・CSV | ノード・関係・証拠の配布と差分確認 | スキーマ、参照整合性、複数ファイルの世代管理 |
| SQLite の通常表 | ローカルでの絞り込み、隣接探索、根拠の参照 | 索引、深さ上限、書き手の調整、公開時の置き換え |
| Parquet | 表としての一括処理・分析用スナップショット | 隣接索引や更新の仕組みは別途用意 |
| RDF の Turtle・N-Quads | RDF の保存と他ツールへの受け渡し | グラフ単位・データセット単位の形式選択と読込処理 |
| GraphML | グラフ可視化・分析ツールへの受け渡し | 保存できる属性型と、多重辺・証拠の表現の確認 |

表は仕様と既存コードを整理した選択肢である。JSON Lines は UTF-8 で一行ごとに JSON 値を置く形式であり、ノード・エッジ・証拠を別ファイルに保存しやすい。Parquet は列指向のファイル形式である。N-Quads は RDF データセットを行単位で表現する。NetworkX は GraphML の書き出しを提供するが、その実装には未対応のグラフ構造がある。ファイル形式が保存できる情報と、アプリケーションが必要とする情報を照合して選ぶ。[37](https://jsonlines.org/)[38](https://parquet.apache.org/docs/overview/)[34](https://www.w3.org/TR/n-quads/)[39](https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.graphml.write_graphml.html)

SQLite を使う場合は、`nodes`、`relations`、`assertions`、`aliases` のような表と索引を用意する構成が考えられる。始点・終点からの探索は、SQL の再帰 CTE でも、アプリケーション側の BFS でも実装できる。info-hive の既存実装は `nodes`、`aliases`、`edges` の通常表を作る。SQLite がグラフ専用の拡張を使っている、という意味ではない。[29](https://www.sqlite.org/lang_with.html)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

通常の関係DBで経路を照会する場合でも、循環、探索の深さ、ハブに接続した大量の辺を扱う必要がある。到達可能性を求める照会と、すべての経路を列挙する照会を分け、上限を設ける設計を推奨する。SQLite の公式例はグラフ照会が可能であることを示すが、すべての経路処理で専用DBと同じ速度になることを示すベンチマークではない。[29](https://www.sqlite.org/lang_with.html)

同時利用では SQLite WAL の制約を確認する。WAL では読み取りと書き込みを並行できるが、同時の書き手は一つであり、同じマシン上の共有メモリを前提とする。共有フォルダに置いた DB を複数ホストから直接更新する案は、今回の推奨には含めない。単一の構築処理が新しいスナップショットを公開し、複数の読み手が使う構成を提案する。[30](https://www.sqlite.org/wal.html)

ファイルだけで保存する場合は、一行ずつの追記ができることと、複数ファイルを整合した状態で公開できることを分ける。たとえば新しい `nodes.jsonl` と古い `edges.jsonl` が同時に見えないよう、世代のディレクトリと manifest を用意する案がある。JSONL 自体は形式の規約であり、この切り替えの機能を持つわけではない。Git で正本を管理する場合も、生成物の世代と入力の版を対応付ける設計を推奨する。[37](https://jsonlines.org/)

GraphRAG や LightRAG も、専用DBなしの具体例になる。GraphRAG は実体、関係、文書、TextUnit、コミュニティなどの表を既定では Parquet として出力する。LightRAG は KV・vector・graph・document status のストアを使い、標準のローカル構成に NetworkX を含む。後者の標準ストアは RAM に制約され、小規模試験向けと説明されている。どちらも「グラフDBが不要」と「運用上の保存設計が不要」を同じ意味にはしない。[41](https://microsoft.github.io/graphrag/index/outputs/)[25](https://github.com/HKUDS/LightRAG)

### 6. グラフDBを使う場合は、プロパティグラフと RDF ストアを比較する

Neo4j のプロパティグラフは、有向・型付きの関係と、ノード・関係のプロパティを扱う。製品、組織、人物の間をたどり、関係ごとの属性を返す構成の候補になる。記事やチャンクを残した lexical graph と、実体のグラフを対応付ける UI の実例もある。ただし、DBへ保存できることと、抽出した関係が正しいことは別である。[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[20](https://neo4j.com/developer/genai-ecosystem/llm-graph-builder-features/)

RDF を選ぶ場合は、IRI で実体や述語を識別し、共通の語彙を使う設計を検討する。RDF のデータモデルを採用することと、専用ストアを導入することは独立している。ローカルの N-Quads で保存してから、必要に応じて SPARQL のサーバーへ読み込む運用も可能である。日本語のナレッジグラフ推論チャレンジには、RDF を GitHub で配布し、SPARQL エンドポイントも提供する実例がある。[31](https://www.w3.org/TR/rdf11-concepts/)[34](https://www.w3.org/TR/n-quads/)[40](https://challenge.knowledge-graph.jp/2024/rdf.html)

| 比較軸 | Neo4j などのプロパティグラフDB | RDF ストアの例: Jena TDB2＋Fuseki |
|---|---|---|
| データの表現 | ノードと型付きの関係、プロパティ | IRI・リテラル・トリプル・名前付きグラフ |
| 主な照会方法 | グラフのパターン・経路を記述 | SPARQL によるパターン照合など |
| 証拠の表現案 | 関係の属性、または独立した主張ノード | 主張リソース、記事版ごとの名前付きグラフと出所語彙 |
| 適する要件の判断 | アプリケーションの関係照会を中心にする | 外部の RDF 語彙や SPARQL を共有する |
| 確認すること | 採用する機能・版、バックアップ、更新の契約 | TDB2 の永続化構成、Fuseki の公開・更新権限 |

表の「適する要件」は本調査の判断であり、製品の優劣を実測した結果ではない。Fuseki は SPARQL の問い合わせ・更新を受け付けるサーバーで、TDB と組み合わせた永続ストアを提供する。TDB2 は単一マシン向けの RDF 保存・照会のコンポーネントであり、TDB1 と互換ではない。Fuseki を起動したという事実だけで、適切な永続保存が構成されたと判断しない。[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[35](https://jena.apache.org/documentation/fuseki2/index.html)[36](https://jena.apache.org/documentation/tdb2/)

本調査では、複雑な経路を日常的に照会する共有アプリケーションなら専用DBを検討し、ローカルの関連記事検索や根拠の参照が中心なら SQLite を先に評価する方針を提案する。移行の境目を「何万ノード以上」と固定する根拠は得られなかった。代表的な問い、探索の深さ、辺の密度、同時利用数、応答時間の要件を固定して比較する必要がある。[29](https://www.sqlite.org/lang_with.html)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[36](https://jena.apache.org/documentation/tdb2/)

どちらのグラフDBも、wiki と独立したもう一つの正本にするか、wiki から再構築できる索引にするかを先に決める。info-hive では Markdown が正本であるため、まずは専用DBも再構築可能な索引として扱う案を推奨する。DBの画面から直した関係を Markdown に戻す仕組みを作らずに両方を編集すると、どちらを採用すべきか決まらなくなる。後者の問題は本調査の設計上の考察である。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)

### 7. 増分更新と評価を、最初の構築と同じ範囲で扱う

記事を追加するだけでなく、修正・削除したときの扱いを確認する。LightRAG は文書IDによる削除APIを説明し、他文書にも現れる実体や関係を再構築する処理を含める。一方、GraphRAG の公式リポジトリの Issue #2590 には、3.2.0 の増分更新で削除した入力文書が索引に残るという報告があり、調査日の時点で Open だった。これは未再現の一次不具合報告として扱い、全バージョンに共通する仕様とは断定しない。[26](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)[27](https://github.com/microsoft/graphrag/issues/2590)

この事例から、`incremental update` という機能名だけで削除の反映を保証せず、採用する版で確認することを推奨する。記事Aだけが支持する関係、AとBが支持する関係、改訂で否定された関係を用意して試す。Aを削除した場合、Aだけに由来する主張を検索から外し、Bの支持は残す。LLM の説明を複数文書から統合している場合は、辺の削除だけでなく、説明や要約の再計算も対象になる。[26](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)[16](https://microsoft.github.io/graphrag/index/default_dataflow/)

差分の判定には、記事の内容のハッシュだけでなく、パーサー・スキーマ・辞書・抽出モデル・プロンプトの版を記録する案を提案する。同じ本文でも、抽出条件の変更で候補が変わりうるためである。明示リンクの再構築は、同じ入力に同じ出力が得られるかを確認する。LLM による候補抽出は、再実行したときの変動を別に測る。NTT DATA の事例でも、同じ形式の入力とスキーマで表記の変動が報告されている。[21](https://zenn.dev/nttdata_tech/articles/266a6692f85fee)

評価は、抽出した辺の件数や、可視化の見た目で終えない。Text2KGBench は適合率・再現率・F1、オントロジー適合、幻覚を分ける。日本語で執筆された学術要旨の比較研究も、本文に用語があるか、本文に意味が支持されるか、記載のない情報かを分けて専門家が判定している。これらから、構造、根拠、抽出漏れを別々に評価する方針を推奨する。[23](https://arxiv.org/abs/2308.02357)[22](https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/)

日本語記事では、略語・日英別名・主語の省略・否定・条件付きの記述を評価対象に含める。文字列が原文にないだけで誤りとすると、適切な別名展開まで誤検出する可能性がある。Text2KGBench 自身も略語展開による評価上の問題を扱っている。文字列照合を一次チェックに使い、人が原文と関係の意味を確認する層を併用することを提案する。[23](https://arxiv.org/abs/2308.02357)[5](https://obsidian.md/help/aliases)[14](https://www.jstage.jst.go.jp/article/jnlp/22/5/22_433/_article/-char/ja/)

最低限の評価集合として、正しい関係がある記事、関係がない記事、矛盾する記事、複数資料が支持する記事を含める案を提案する。日本語と英語を別に採点し、記事単位で学習・調整用と評価用を分ける。適合率だけでなく、名寄せの誤統合・分割、出典へ戻れる割合、削除後に残る主張、代表的な問い合わせの根拠の妥当性も記録する。この評価計画は未実施であり、採用閾値を示す実測値は今回得ていない。

## 方式を組み合わせるときの判断

| 構成 | グラフDBを使わない | グラフDBを使う |
|---|---|---|
| 抽出で LLM を使わない | wikilink・frontmatter・辞書規則 → JSONL＋SQLite。info-hive の既存方式を土台にできる | 同じ抽出結果を Neo4j または RDF ストアへ読み込む。元の証拠とIDを保持する |
| 抽出で LLM を使う | スキーマに従う抽出 → 検証 → JSONL＋SQLite。GraphRAG の Parquet や LightRAG のローカル保存も例になる | スキーマに従う抽出 → 検証 → Neo4j／RDF ストア。共有照会の要件と運用費用を評価する |

四つの構成は、抽出と保存を分けた本調査の整理である。SQLite のグラフ照会、GraphRAG のファイル出力、Neo4j の抽出機能とデータモデルは、それぞれ異なる部分を提供する。LLM を使うことから専用DBが必要とは結論できず、専用DBを使うことから LLM が必要とも結論できない。[29](https://www.sqlite.org/lang_with.html)[41](https://microsoft.github.io/graphrag/index/outputs/)[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)

本調査が重視するのは、関係を多く生成することより、どの記述をどの関係として採用したかを追えることである。LLM による候補の発見を追加しても、明示されたリンクや、既に検証済みの型付き関係を毎回生成し直す必要はない。この方針は、構造化された既存記事を使う LLM Wiki に対する設計上の提案である。原文との対応、既存のID、採用済みの関係を維持した上で、不足する述語や記事に抽出を限定する。

## 反証・注意点

「LLM を使えば、自由な文章から安定したグラフが作れる」という強い主張は採らない。日本語 Markdown の一次実験には同じ入力形式でも表記が揺れる例があり、学術要旨の比較研究にも誤ったトリプルが残る。Text2KGBench は型への適合と幻覚の評価を分離する。この三者は対象が違うため、ひとつの精度値へ統合できないが、スキーマ適合だけで品質を判断することへの反証になる。[21](https://zenn.dev/nttdata_tech/articles/266a6692f85fee)[22](https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/)[23](https://arxiv.org/abs/2308.02357)

「グラフDBなしなら、更新が簡単である」という主張も採らない。SQLite WAL には書き手の制約がある。LightRAG は複数ストアを使い、文書の削除では共有される要素を再構築する。GraphRAG のファイル索引にも削除に関する不具合報告がある。専用DBを省いても、証拠と索引の整合を維持する仕事は残る。[30](https://www.sqlite.org/wal.html)[26](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)[27](https://github.com/microsoft/graphrag/issues/2590)

「LLM を使わない方法は、本文の関係を扱えない」という主張も採らない。OpenIE、T2KG、教師ありの実体・関係抽出は本文を対象にしている。ただし、日本語対応、対象述語の範囲、学習モデルの依存、評価データを個別に確認する。[10](https://stanfordnlp.github.io/CoreNLP/openie.html)[15](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf)[12](https://aclanthology.org/2021.naacl-main.5/)

## 限界と未確認事項

今回、同じ日本語・英語の wiki を用いて方式間の精度、処理時間、費用、メモリ、照会速度を測定していない。そのため、製品の性能順位、実用上のノード数の境界、抽出の適合率の見込みを示さない。事実として扱ったのは、確認できた仕様、実装の構造、当事者の報告と、その報告が対象とする範囲である。

日本語で検索して見つかる資料が、日本語データでの性能を検証しているとは限らない。学術要旨の比較研究は、日本語で執筆されているが、実験で用いた本文は英語だった。また、抄録の要旨数と本文の要旨数に食い違いがある。したがって、その数値を日本語 wiki の精度予測として流用せず、評価方法と限界の資料として使用した。[22](https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/)

古い研究は手法の構成や言語現象を理解するために使い、現在のモデルの性能を代表する証拠にはしない。T2KG とその後続研究は同じ研究系譜であり、独立した支持として水増ししない。日本語の省略分析も、現在の解析器の性能評価として扱わない。[15](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf)[14](https://www.jstage.jst.go.jp/article/jnlp/22/5/22_433/_article/-char/ja/)

公式ドキュメントでも、開発中の機能や default branch の記述は変わりうる。Neo4j の該当する KG Builder 機能は experimental と明記されている。GraphRAG の不具合報告と LightRAG の削除APIも、本調査では全バックエンドの障害時動作を再現確認していない。実装へ進む際は、採用版を固定して読み直し、追加・変更・削除の契約を試す必要がある。[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[27](https://github.com/microsoft/graphrag/issues/2590)[26](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)

info-hive の調査は現行作業ツリーの読み取りに限った。既存の wiki 記事、プラグイン、索引は変更していない。本レポートの候補スキーマや評価計画は、既存仕様の採用済み変更を表すものではない。調査成果は `docs/research/` と Documents の出力先に保存し、wiki への取り込みは今回の作業に含めなかった。

## info-hive への提案

**初期の候補は、Markdown を正本として保ち、既存の抽出器と SQLite を使う構成である。** 現在、明示関係・wikilink・出典からグラフを作り、JSONL・SQLite・GraphML を生成できる。まず、この出力を使って「何の関係が不足していて、どの問い合わせで困るか」を記録する。グラフDBへの移行と、本文からの意味関係の抽出を同時に始める必要性は、現時点の資料からは示されなかった。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)[3](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py)

次に、リンク解決、別名、重複ID、出典・根拠の欠落、記事更新後の索引の版を確認する。プロジェクト wiki の [[グラフの抽出の契約]]、[[エッジの識別子]] が整理する既存の性質を、別バックエンドへ移すときにも維持する。[[既存リンクからのグラフ検索]] と [[オントロジー候補の生成と採用の分離]] は、既存リンクの利用と候補の採用を分ける参考になる。これらはローカルの既存知識であり、本レポートの性能検証ではない。

本文からの抽出を追加するなら、使う述語と対象記事を絞った比較を提案する。既存方式、GiNZA＋規則、スキーマを使う LLM 抽出を同じ評価集合に当てる。明示されている関係を正しく維持できるか、本文だけの関係を追加できるか、無関係な文で候補を出しすぎないかを分けて採点する。日本語と英語を一つの平均にまとめず、別名や省略のある例の誤りも確認する。[8](https://megagonlabs.github.io/ginza/)[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[23](https://arxiv.org/abs/2308.02357)

抽出で採用する関係を増やす場合は、候補の保存と採用済みの出力を分ける案を推奨する。候補には入力の版、根拠、抽出方法、判定結果を残す。採用時に、既存の型付き関係へ写すのか、別の主張台帳を正本に加えるのかを決める。後者は info-hive の現在の正本の範囲を変えるため、別の設計判断として扱う。候補台帳を作っただけで、既存の Markdown と競合する正本を増やさない。[2](C:/Works/info-hive-dev/wiki/SCHEMA.md)

保存先の比較は、必要な問い合わせが定まってから行う。既存の SQLite で代表的な経路照会が要件を満たすなら継続し、共有サービスや複雑な経路の運用で課題が出れば Neo4j を試す。RDF 語彙を外部と共有する要件があれば N-Quads と Jena TDB2・Fuseki を試す。いずれも、元の主張と根拠へ戻れること、記事の削除を正しく反映することを、速度と並ぶ採用条件にする。[29](https://www.sqlite.org/lang_with.html)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[34](https://www.w3.org/TR/n-quads/)[36](https://jena.apache.org/documentation/tdb2/)[35](https://jena.apache.org/documentation/fuseki2/index.html)

## 主要主張と根拠の対応

| 主要な主張・判断 | 独立性を考慮した根拠 | 支持の範囲 |
|---|---|---|
| 抽出と保存を独立に選べる | SQLite、Microsoft、HKUDS [29](https://www.sqlite.org/lang_with.html)[41](https://microsoft.github.io/graphrag/index/outputs/)[25](https://github.com/HKUDS/LightRAG) | 具体的な構成が成立する。速度の同等性までは示さない |
| 非LLMでも本文から関係を扱える | Stanford、T2KG、PURE [10](https://stanfordnlp.github.io/CoreNLP/openie.html)[15](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf)[12](https://aclanthology.org/2021.naacl-main.5/) | 英語・従来手法を含む。日本語の精度保証ではない |
| 型への適合と意味の支持を分ける | Neo4j、Text2KGBench、学術要旨比較 [18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[23](https://arxiv.org/abs/2308.02357)[22](https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/) | スキーマ、抽出性能、幻覚を別に扱う根拠 |
| 実体の同一性には別の判定が要る | Obsidian、Neo4j、東京大学の事例 [5](https://obsidian.md/help/aliases)[18](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)[24](https://dss.i.u-tokyo.ac.jp/blog/practical-graph-rag-1/) | 別名・同名統合・表現統合の違い。統合アルゴリズムの最良性は未確定 |
| 保存方式には複数のデータモデルと形式がある | W3C、Neo4j、SQLite [31](https://www.w3.org/TR/rdf11-concepts/)[28](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)[29](https://www.sqlite.org/lang_with.html) | データモデルとDB製品・ファイル形式を区別できる |
| 構築後も削除・再構築を確認する必要がある | HKUDS、Microsoftの報告、info-hiveの正本規約 [26](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)[27](https://github.com/microsoft/graphrag/issues/2590)[2](C:/Works/info-hive-dev/wiki/SCHEMA.md) | 設計判断の根拠。全製品の不具合を主張するものではない |

## 出典一覧

[1] Andrej Karpathy (2026). "LLM Wiki". 一次資料・original_proposal。 [原典](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) （参照日: 2026-11-17、言語: en）。

[2] to884 / info-hive (2026年11月17日の作業ツリー). "info-hive wiki スキーマ". 一次資料・local_schema。 [原典](C:/Works/info-hive-dev/wiki/SCHEMA.md) （参照日: 2026-11-17、言語: ja）。

[3] to884 / info-hive (2026年11月17日の作業ツリー). "info-hive グラフ抽出器". 一次資料・local_code。 [原典](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py) （参照日: 2026-11-17、言語: ja）。

[4] Obsidian (更新型資料). "Internal links - Obsidian Help". 一次資料・official_documentation。 [原典](https://obsidian.md/help/links) （参照日: 2026-11-17、言語: en）。

[5] Obsidian (更新型資料). "Aliases - Obsidian Help". 一次資料・official_documentation。 [原典](https://obsidian.md/help/aliases) （参照日: 2026-11-17、言語: en）。

[6] Explosion / spaCy (更新型資料). "Rule-based matching - spaCy Usage Documentation". 一次資料・official_documentation。 [原典](https://spacy.io/usage/rule-based-matching/) （参照日: 2026-11-17、言語: en）。

[7] Explosion / spaCy (更新型資料). "DependencyMatcher - spaCy API Documentation". 一次資料・official_documentation。 [原典](https://spacy.io/api/dependencymatcher) （参照日: 2026-11-17、言語: en）。

[8] Megagon Labs (更新型資料). "GiNZA - Japanese NLP Library". 一次資料・official_documentation。 [原典](https://megagonlabs.github.io/ginza/) （参照日: 2026-11-17、言語: ja）。

[9] Works Applications (更新型資料). "sudachipy package - SudachiPy documentation". 一次資料・official_documentation。 [原典](https://worksapplications.github.io/sudachi.rs/python/api/sudachipy.html) （参照日: 2026-11-17、言語: en）。

[10] Stanford NLP Group (更新型資料). "OpenIE - CoreNLP". 一次資料・official_documentation。 [原典](https://stanfordnlp.github.io/CoreNLP/openie.html) （参照日: 2026-11-17、言語: en）。

[11] Stanford NLP Group (更新型資料). "Overview - CoreNLP". 一次資料・official_documentation。 [原典](https://stanfordnlp.github.io/CoreNLP/) （参照日: 2026-11-17、言語: en）。

[12] Zexuan Zhong・Danqi Chen (2021). "A Frustratingly Easy Approach for Entity and Relation Extraction". 一次資料・research_paper。 [原典](https://aclanthology.org/2021.naacl-main.5/) （参照日: 2026-11-17、言語: en）。

[13] Pere-Lluís Huguet Cabot・Roberto Navigli (2021). "REBEL: Relation Extraction By End-to-end Language generation". 一次資料・research_paper。 [原典](https://aclanthology.org/2021.findings-emnlp.204/) （参照日: 2026-11-17、言語: en）。

[14] 松林優一郎・中山周・乾健太郎 (2015). "日本語述語項構造解析タスクにおける項の省略を伴う事例の分析". 一次資料・research_paper。 [原典](https://www.jstage.jst.go.jp/article/jnlp/22/5/22_433/_article/-char/ja/) （参照日: 2026-11-17、言語: ja）。

[15] Nattawut Kertkeidkachorn・Ryutaro Ichise (2017). "T2KG: An End-to-End System for Creating Knowledge Graph from Unstructured Text". 一次資料・research_paper。 [原典](https://cis.csuohio.edu/~sschung/cis612/KnowledgeGraphTextProcessing_IAAA2017.pdf) （参照日: 2026-11-17、言語: en）。

[16] Microsoft (更新型資料). "Microsoft GraphRAG — Dataflow". 一次資料・official_documentation。 [原典](https://microsoft.github.io/graphrag/index/default_dataflow/) （参照日: 2026-11-17、言語: en）。

[17] Darren Edge ほか (2024、v2: 2025). "From Local to Global: A Graph RAG Approach to Query-Focused Summarization". 一次資料・research_paper。 [原典](https://arxiv.org/abs/2404.16130) （参照日: 2026-11-17、言語: en）。

[18] Neo4j (更新型資料). "Neo4j GraphRAG Python — User Guide: Knowledge Graph Builder". 一次資料・official_documentation。 [原典](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html) （参照日: 2026-11-17、言語: en）。

[19] LangChain (更新型資料). "LangChain Reference — LLMGraphTransformer". 一次資料・official_documentation。 [原典](https://reference.langchain.com/python/langchain-neo4j/graph_transformers/llm/LLMGraphTransformer) （参照日: 2026-11-17、言語: en）。

[20] Neo4j (更新型資料). "Neo4j — LLM Knowledge Graph Builder Features documentation". 一次資料・official_documentation。 [原典](https://neo4j.com/developer/genai-ecosystem/llm-graph-builder-features/) （参照日: 2026-11-17、言語: en）。

[21] NTT DATA 技術広報 (2026). "Neo4jでLLMベースのナレッジグラフ構築を試してみた". 一次資料・firsthand_experiment。 [原典](https://zenn.dev/nttdata_tech/articles/266a6692f85fee) （参照日: 2026-11-17、言語: ja）。

[22] Victor Eiti Yamamoto ほか (2025). "大規模言語モデルに基づく学術要旨からの知識グラフ構築手法の比較評価". 一次資料・academic。 [原典](https://www.jstage.jst.go.jp/article/jsaisigtwo/2025/SWO-067/2025_02/_article/-char/ja/) （参照日: 2026-11-17、言語: ja）。

[23] Nandana Mihindukulasooriya・Sanju Tiwari・Carlos F. Enguix・Kusum Lata (2023). "Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text". 一次資料・research_paper。 [原典](https://arxiv.org/abs/2308.02357) （参照日: 2026-11-17、言語: en）。

[24] 東京大学DSS (公開年未確認). "意味をつなぐ、知識を紡ぐ：LLMsによる知識グラフ精緻化の試み". 一次資料・first_party_experiment。 [原典](https://dss.i.u-tokyo.ac.jp/blog/practical-graph-rag-1/) （参照日: 2026-11-17、言語: ja）。

[25] HKUDS (更新型資料). "HKUDS/LightRAG README". 一次資料・official_repository。 [原典](https://github.com/HKUDS/LightRAG) （参照日: 2026-11-17、言語: en）。

[26] HKUDS (更新型資料). "LightRAG — Programming with Core". 一次資料・official_documentation。 [原典](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md) （参照日: 2026-11-17、言語: en）。

[27] Pikachu707 / microsoft/graphrag Issue #2590 (2026). "Incremental update (graphrag update) silently ignores removed documents; they stay indexed and retrievable — Issue #2590". 一次資料・primary_issue_report。 [原典](https://github.com/microsoft/graphrag/issues/2590) （参照日: 2026-11-17、言語: en）。

[28] Neo4j (更新型資料). "Neo4j: Graph database concepts". 一次資料・official_documentation。 [原典](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/) （参照日: 2026-11-17、言語: en）。

[29] SQLite (更新型資料). "SQLite: The WITH Clause". 一次資料・official_documentation。 [原典](https://www.sqlite.org/lang_with.html) （参照日: 2026-11-17、言語: en）。

[30] SQLite (更新型資料). "SQLite: Write-Ahead Logging". 一次資料・official_documentation。 [原典](https://www.sqlite.org/wal.html) （参照日: 2026-11-17、言語: en）。

[31] W3C (2014). "RDF 1.1 Concepts and Abstract Syntax". 一次資料・standard。 [原典](https://www.w3.org/TR/rdf11-concepts/) （参照日: 2026-11-17、言語: en）。

[32] W3C (2013). "PROV-O: The PROV Ontology". 一次資料・standard。 [原典](https://www.w3.org/TR/prov-o/) （参照日: 2026-11-17、言語: en）。

[33] W3C (2017). "Shapes Constraint Language (SHACL)". 一次資料・standard。 [原典](https://www.w3.org/TR/shacl/) （参照日: 2026-11-17、言語: en）。

[34] W3C (2014). "W3C: RDF 1.1 N-Quads". 一次資料・standard。 [原典](https://www.w3.org/TR/n-quads/) （参照日: 2026-11-17、言語: en）。

[35] Apache Jena (更新型資料). "Apache Jena: Apache Jena Fuseki". 一次資料・official_documentation。 [原典](https://jena.apache.org/documentation/fuseki2/index.html) （参照日: 2026-11-17、言語: en）。

[36] Apache Jena (更新型資料). "Apache Jena — TDB2". 一次資料・official_documentation。 [原典](https://jena.apache.org/documentation/tdb2/) （参照日: 2026-11-17、言語: en）。

[37] JSON Lines (更新型資料). "JSON Lines documentation". 一次資料・format_documentation。 [原典](https://jsonlines.org/) （参照日: 2026-11-17、言語: en）。

[38] Apache Parquet (更新型資料). "Apache Parquet: Overview". 一次資料・official_documentation。 [原典](https://parquet.apache.org/docs/overview/) （参照日: 2026-11-17、言語: en）。

[39] NetworkX (更新型資料). "NetworkX: write_graphml". 一次資料・official_documentation。 [原典](https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.graphml.write_graphml.html) （参照日: 2026-11-17、言語: en）。

[40] ナレッジグラフ推論チャレンジ実行委員会 (2024). "ナレッジグラフ推論チャレンジ: ナレッジグラフ公開". 一次資料・primary_project_documentation。 [原典](https://challenge.knowledge-graph.jp/2024/rdf.html) （参照日: 2026-11-17、言語: ja）。

[41] Microsoft (更新型資料). "Microsoft GraphRAG — Outputs". 一次資料・official_documentation。 [原典](https://microsoft.github.io/graphrag/index/outputs/) （参照日: 2026-11-17、言語: en）。

## 調査方法と証拠の管理

`deep-research` の標準モードを用いた。スコープを、既存構造からの抽出、本文からの非LLM抽出、LLM抽出、モデルと出所、グラフDBを使わない保存、専用DB、更新・評価に分解した。スキルの指示に従い、LLM抽出、非LLM抽出、保存の三つを並行するエージェントへ分担し、主張・短い引用・出所URL・位置・制約を同じ形式で収集した。

検索 CLI は PATH に見つからなかったため、検索 MCP の Web 検索・ページ取得を使用した。日本語・英語で検索し、公式ドキュメント、研究論文、元の提案、当事者による実験・不具合報告を採用した。日本語の探索では「ナレッジグラフ 構築 LLM 使わない GiNZA 固有表現 関係抽出」などを用い、英語では LLM Wiki、OpenIE、ontology-driven knowledge graph、RDF provenance などの観点を調べた。実行したクエリと分担の記録は manifest に保存する。

同じ組織の公式資料と論文は、主要な判断を三角測量するときに独立した証拠として水増ししない。T2KG と後続論文、GraphRAG の論文と実装資料なども同様に扱う。具体的な API やフォーマットの機能は、その一次資料が直接の根拠となる単独出典の事実として扱う。広い判断は、上の対応表のように異なる実装・研究・仕様を照合した。

収集した証拠から、当初の「抽出方法と保存方法」の比較に、記事・実体・主張の区別と、削除の反映を追加した。抽出方法の優劣より、出所と同一性を維持する条件が各方式の比較に必要と分かったためである。日本語で執筆された資料と日本語を対象にした実験も区別し、単独の数値を一般化しなかった。

証拠は本文作成前にJSONへ保存し、安定した source ID を持つ `sources.jsonl`、短い引用と位置を持つ追記専用の `evidence.jsonl`、主張と支持を結ぶ `claims.jsonl` に整理した。`run_manifest.json` には範囲、前提、手法、未確認事項を記録する。短い引用は根拠の目印であり、その引用の語彙一致だけで意味の支持を判定したものではない。資料の該当箇所と制約を合わせて読み、レポートに記載した範囲を手動で照合した。

日本語の文章は、英語の空白区切りの単語数をそのまま当てはめず、章ごとの文字数と論点の充足で長さを確認した。付属の構造・引用バリデーターには、内容を変えず見出しだけを英語名にした検証用コピーを渡す。配布する正本は日本語の Markdown であり、HTML と PDF はそこから生成する。

設計上の提案について `ask-claude` で Opus 5.5 に敵対的レビューを依頼したが、利用上限により生成前に停止し、レビューは実施できなかった。再試行はしていない。独立した Opus レビュー済みとは扱わず、この制約を結果の記録に残した。自己点検では、関係を集約するときに肯定・否定や成立条件を失わないよう、モデル案の説明を補った。

