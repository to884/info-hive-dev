あなたは、同じタスクに独立して取り組む 4 体のエージェントの 1 体です。
他のエージェントが誰で、何を書くかは知らされません。
あなたの最終メッセージだけが成果物として保存され、後で他のエージェントに読まれます。途中のメッセージは保存されないので、根拠と結論は最終メッセージにすべて書いてください。

## タスク

# タスク：LLM Wiki で蓄積した情報の活用方法を、発散と収束で考える

## 作者の指示

> LLM Wiki で蓄積した情報の活用方法。
> LLM Wiki は Web や文章などから情報を取り込み、その上で概念を整理した記事を作成したり、概念同士の関連付けをおこなったり（グラフ）、定義を作ったり（オントロジー）をしている。
> これらの情報をどのように活用するか？について考察し、効果的な活用方法を考えてほしい

作者はこの検討の結果を、次の 2 つを決めるために使う（2026年11月6日に確認）。

- **スコープ A**: info-hive に次に足す機能（プラグインのロードマップへの入力）
- **スコープ B**: 今の wiki を日々どう使うか（新しい実装を前提にしない運用の手順）

発散は 2 つのスコープに共通で行い、収束は A と B に分けて行う。手法は brainstorm-diverge-converge（発散 → クラスタ → 収束）である。

## 現状として分かっていること

### wiki プラグイン（`info-hive-wiki`、プラグイン名 `wiki`、導入名 `wiki@info-hive`）

コマンドは `/wiki:<名前>` で呼ぶ。

| コマンド | 入力 → 出力 |
| --- | --- |
| init | セットアップの質問に答えると、wiki の骨組み（SCHEMA.md、index.md、log.md、graph/ontology.yaml）と実行環境を作る |
| ingest | ソース（論文、記事、文字起こし、PDF、メモ、URL）を受け取り、原本を raw に置き、`sources/<slug>.md` の要約と entity / concept ページの新規作成または部分更新、`index.md` と `log.md` の追記を行う。オントロジーがあれば根拠付きの型付きエッジを足し、graph の lint と extract も行う。PDF は rag の `register_pdf` に登録する |
| query | 質問を受け取り、`index.md` → 候補ページ →（見つからなければ `wiki_search.py` のハイブリッド検索、関係を問う質問なら `wiki_graph_query.py`）の順に調べ、`[[wikilink]]` を出典に付けた回答を返す。回答を `synthesis/` に保存することを提案する |
| graph | `extract` / `lint` / `neighbors` / `edges` / `path` / `facts` を受け取る。extract は `graph/` に nodes.jsonl、edges.jsonl、graph.sqlite、graph.graphml を作る |
| learn | タスクの成果物や経験を受け取り、変更不可の raw JSON（`raw/experiences/`）を作り、source として取り込み、concept（`kind: experience-pattern`、`status: hypothesis|supported|superseded`）のパターンページにまとめる |
| evolve | 対象スキルと改善の目的を受け取り、`.evolution/` に実験記録を残して改善案を作り、学習・検証・最終テストで評価し、承認があれば apply、依頼があれば rollback する |
| lint | 孤立ページ、リンク切れ、大きすぎるページ、frontmatter の誤り、古い日付、graph の矛盾、内容の矛盾と不足を修正案として返す |
| stats | ページ数、種類別の数、リンク密度、スケーリングの閾値（150、300、500 ページ）の判定を返す |
| upgrade | 実行環境とベクトルを作り直し、SCHEMA.md に欠けている節を追記する |

### wiki が蓄積するデータ

- ページの `type` は `source`（`sources/`）、`entity`（`entities/`）、`concept`（`concepts/`）、`synthesis`（`synthesis/`）の 4 つ。entity の `kind` は person、company、product、paper、place、organization。
- frontmatter の必須項目は `type`、`title`、`tags`、`created`、`updated`。source には `raw`、`ingested`、`authors`、`url`。source 以外には `sources`。任意で `aliases`、`question`、`sources_consulted`。
- 本文の `[[wikilink]]` から `mentions` のエッジが自動で作られる。`sources:` から `sourced_from`、`raw:` から `summarizes_raw` も自動で作られる。
- 型付きの述語（`graph/ontology.yaml` で宣言、根拠必須）: founded、owns、contains_product、works_on、chose、proposed、competes_with、depends_on、authored、cites、contradicts、supersedes。ノード型 decision、claim、raw は `explicit_only`（明示したときだけ使う）。
- 型付きエッジの必須項目: `predicate`、`object`、`source`（ソースページのスラッグ）、`evidence`（原文の引用）、`confidence`（high / medium / low）、`status`（current / historical / proposed / disputed / superseded）。任意で `valid_from`、`valid_to`、`raw_ref`、`contradicts`、`supersedes`。
- 検索はセクション単位のハイブリッド検索（語彙 + 埋め込み。現行は `intfloat/multilingual-e5-small` と sqlite-vec。統一レポートは Ruri v3 130m + usearch + Tantivy に変える案）。`--type`、`--tag`、`--since` で絞れる。
- 派生データ（`.wiki-cache/`、`graph/` の生成物、`.evolution/`）は作り直せる。正本は Markdown である。

### 作者の wiki の現在の規模と中身

- 22 ページ（source 7、entity 1、concept 15、synthesis 0）。`graph/` は生成済み。タグの体系は「並行処理」「知識表現」「AIエージェント」「情報検索」。
- 中身の多くは Yuan An の連載「Ontology and Knowledge Graphs and AI Agents」の第 1〜4 回を取り込んだ concept ページで、この検討の素材にもなる。要点は次のとおり（作者の wiki はこのリポジトリの外にあるので、ここに書き写す）。
  - **コンテキストグラフ**: 全体のナレッジグラフから、1 つのエージェント・1 つの目標・1 つの時点のために、焦点の実体から k ホップ（2〜3）で切り出した部分グラフ。エージェントの動的な作業記憶にあたる。関連度は構造（距離）・意味（型が目標に合うか）・時間（新しさ）の重み付き和で採点し、予算を超えた分は退去させ、行動の結果は確認後に出所と時刻を付けて全体のグラフへ書き戻す。
  - **グラウンディング**: 推論を取得した事実（グラフ）と規則（オントロジー）に結びつける。行動の前に SPARQL の ASK で前提条件を確かめ、偽なら行動を拒否して再問い合わせする。「取得・推論・検証」の往復。
  - **コンテキストエンジニアリング**: 有限のウィンドウに何をどの形で入れ、いつ入れ替えるかを設計する。制約はトークンの予算、遅延、注意の劣化（context rot）。答えは「もっと多く」ではなく、鮮度のある正しい事実を使える形で入れること。
  - **名前付きグラフ**: トリプルにグラフ名を足し、フィードごとの出所と時点、PROV-O による系譜を持つ。
  - **オントロジー抽出パイプライン**: 資料からオントロジーを 7 段階で作る。再現率優先、来歴、根拠づけで LLM を囲い、上位オントロジーに anchor してから coin する。T-Box（スキーマ）と A-Box（個体）を分ける。

### 関連する決定と計画

- Markdown が正本で、索引やグラフは使い捨ての派生データである（SCHEMA.md）。
- 処理はローカルで完結する。wiki やクエリの文字列をマシンの外に出さない。
- PC 固有の値（パスなど）は既定値と設定で扱い、仕様に書かない。
- ADR-0009: グラフ層とオントロジーは wiki プラグインの中の「任意の索引」であり、wiki、log、rag を横断する基盤にはしない。log、rag、複数の wiki から関係の問い合わせやオントロジーの管理を直接使う要件ができたら、分割を見直す。
- ADR-0006: 日々の記録は別のプラグイン `log`（未実装）。日付ノートから wiki に直接は入れず、`notes/` に書き出したものを人が `/wiki:ingest` で入れるかを決める。
- ADR-0007: `rag` は PDF を永続ジョブで索引化し、MCP の `search` でチャンクを返す。回答は Claude Code が作る。
- 埋め込み統一レポート §13・§15: wiki を 127.0.0.1 の streamable HTTP の MCP サーバーにし、モデルと索引をこのサーバーだけが持ち、rag や他のエージェント（Codex など）からも問い合わせできるようにする案。ツール案は query、get_page、list_index、lint、stats、graph、ingest_source、index_chunks。ADR としては未確定。
- 要件定義書 §2.2 の利用場面: 技術資料を読む、実装前に調べる、不具合を直す、作業を終える、知識を見直す。§4.2 と O-03: 複数の wiki をまたぐ横断検索は未決。§5.3: Project Wiki の知見を Global Wiki に一般化する案。

## 読むべき文書とコード

- `AGENTS.md`（リポジトリの役割、日本語と機械が読む文字列の方針）
- `llm-wiki-product-concept-and-requirements-ja.md` の §2、§4.2、§5.3、§13
- `docs/adr/0006-daily-journal-is-separate-plugin.md`、`0007-rag-uses-mcp-core-and-persistent-jobs.md`、`0009-graph-layer-stays-in-wiki.md`
- `docs/research/embedding-backend-unification-2026-11-05/README.md` の §13 と §15
- `info-hive-wiki/skills/info-hive/SKILL.md`、`info-hive-wiki/commands/*.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`、`graph-workflow.md`、`evolution-workflow.md`、`agent-memory-integration.md`、`scaling-playbook.md`
- `info-hive-wiki/skills/info-hive/assets/ontology.yaml.template`、`SCHEMA.md.template`
- `info-hive-wiki/docs/index.md`（「LLM Wiki は RAG とどう違うのか」）、`info-hive-wiki/docs/graph.md`、`evolution.md`、`search.md`
- 前例の形式: `docs/research/rag-execution-architecture/brainstorm-diverge-converge.md`、`docs/research/daily-journal-methodology-options.md`

## 成果に含めるもの

成果は 1 本の Markdown で、次の順に書く。

1. **結論の要約**: スコープ A とスコープ B それぞれの上位 3〜5 案を、先に一覧で書く。
2. **発散**: 30 案以上を番号付きで並べる。この段階では評価しない。次の 4 軸を掛け合わせ、各軸のどの値にも最低 1 案を置く。「検索して答える」に偏らないこと。
   - 使う主体: 人が読む / Claude Code が答える / 他のプラグイン（rag、log）/ 外部のツールやエージェント（Foam、Obsidian、Codex など）
   - 使う資産: 記事の本文 / wikilink のグラフ / 型付きエッジ（evidence、confidence、status、valid_from、valid_to）/ ontology.yaml / synthesis / raw / `.evolution` と `experience-pattern` の経験
   - 使う時点: 取り込み時 / 質問時 / 定期の lint 時 / プロジェクトの出来事（設計、不具合、作業の終了、セッションの開始）時
   - 仕組み: 取得 / グラフ上の推論（k ホップ、経路、集約）/ 検証（矛盾、前提条件、鮮度、出典）/ 下書きの生成（ADR、調査の骨子、用語集、レビューの観点）/ 学習（learn、evolve）/ 書き出し（MCP、エクスポート、他ツール連携）
3. **クラスタ**: 4〜8 系統の表。各系統に含む案の番号と、そう分けた理由を書く。
4. **収束 A（info-hive に次に足す機能）**: 全案を次の基準で 1〜10 点で採点し、合計（各点数 × 重みの和 ÷ 100）で並べる。点数の根拠を短く添える。重みを 2 通り変えて、上位が入れ替わるかも確認する。

   | 基準 | 重み | 高く評価する条件 |
   | --- | --- | --- |
   | 利用者が得る価値 | 25 | 今のコマンドでは得られない結果を出す。既存機能との差分が明確 |
   | 既存の設計との整合 | 20 | Markdown が正本、生成物は使い捨て、ローカル完結、ADR-0009 に反しない |
   | 規模への耐性 | 20 | 22 ページの今も効果が出て、150 ページを超えても壊れない |
   | 実装と検証の軽さ | 20 | 既存のスクリプト（`wiki_search.py`、`wiki_graph_query.py`、`wiki_lint.py`）の延長で作れ、テストで確かめられる |
   | 他プラグインへの波及 | 15 | rag、log、MCP サーバー化の計画と矛盾せず、むしろ前提を作る |

5. **収束 B（今の wiki を日々どう使うか）**: 新しい実装を前提にしない案だけを対象に、次の基準で同じように採点する。既存のコマンドと SCHEMA.md の規約（「ワークフローのカスタマイズ」「ユーザーの好み」の節への追記を含む）だけで回ることを前提にする。

   | 基準 | 重み | 高く評価する条件 |
   | --- | --- | --- |
   | 今日からできる | 30 | 新しい実装なしに、既存コマンドと規約だけで回る |
   | 手間に対する見返り | 25 | 1 回の操作で、次のセッションや別のプロジェクトで再利用できる成果が残る |
   | 知識の質を上げる | 25 | 矛盾、鮮度、出典のたどりやすさが改善する |
   | 習慣にしやすい | 20 | 作業の自然な切れ目（取り込み後、質問後、作業の終了時）に置ける |

6. **選んだ案と条件**: A と B それぞれについて、上位 3〜5 案、採る条件と弱点、次点、保留を表にする。ADR-0009 の「見直す条件」に触れる案（グラフを横断基盤にする案など）は除外せず採点し、その旨を注記する。既に実装済みの機能（query の synthesis 保存、learn、evolve、graph の問い合わせなど）と重なる案は、何が差分かを明記する。
7. **次のステップ**: A は PoC や ADR の候補、B は SCHEMA.md への追記案やコマンドの使い方の手順として書く。
8. **確認できなかったこと**と、基準や重みへの異議があればそれも書く。

基準と重みは 4 体の成果を比べやすくするために共通にしてある。基準の妥当性への異議は成果に書いてよい。

リポジトリのファイルは書き換えないこと。成果は日本語で書き、コマンド名、frontmatter のキー、述語名、ファイル名は英語の原文のまま書く。


## 制約

- 調査と判断のタスクである。リポジトリのファイルを書き換えない。読むための道具は使える。ビルドはしない。
- `docs\agent-runs\2026-11-06-wiki-knowledge-utilization` の配下は読まない。他のエージェントの成果が置かれる場所である。
- 質問はできない。足りない情報は妥当な仮定を置いて最後まで進め、仮定であることを明記する。
- 主張には根拠を添える。読んだファイルはパスと該当箇所、計算は式と値、推測は推測と書く。
- 作業ログではなく、判断に要る情報を書く。
- 日本語で書き、結論を先に書く。

## 最終メッセージの形式

Markdown で、次の見出しをこの順に置く。

1. `## 結論`：タスクへの答え
2. `## 根拠`：結論を支える事実と推論
3. `## 検討した代替案`：採らなかった案と、採らなかった理由
4. `## 前提と不確実性`：依存している仮定、確かめられなかったこと、作者の判断が要ること
5. `## 参照`：読んだファイルと文書
