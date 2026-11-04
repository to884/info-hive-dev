# タスク：グラフとオントロジーの機能を別プラグインに分けるべきか検討する

## 作者の指示

> グラフ、オントロジーの機能を別プラグインとして分割するべきか検討してください

対象は、info-hive の wiki プラグイン（`info-hive-wiki`、プラグイン名 `wiki`、導入名 `wiki@info-hive`）が今持っている型付きグラフ層である。オントロジー（`graph/ontology.yaml`）、ページの frontmatter の `graph:` メタデータ、抽出・lint・問い合わせのスクリプト、`/wiki:graph` コマンド、取り込み・問い合わせ・lint・アップグレードの各手順に組み込まれたグラフの段を含む。図表（ADR-0005 の mermaid と svg）は対象外である。

## 現状として分かっていること

- グラフ層は移植元 llm-wiki-plugin v0.3.0 で加わった任意の層で、`graph/ontology.yaml` がなければ何もしない。正本は Markdown で、`graph/` の生成物（`nodes.jsonl`、`edges.jsonl`、`graph.sqlite`、`graph.graphml`）はいつでも作り直せる。
- 2026-11-04 に、日本語のノード（`person:山田太郎` など）で extract、lint、`neighbors`・`edges`・`facts`・`path` が動くことを手作業で確かめた。グラフ層の専用のテストは `eval/` にない（判定レイヤーのテスト `eval/decisions/` がグラフの lint の一部を使う）。
- 別のプラグインに依存するプラグインの前例として、`rag`（`info-hive-rag`）が `plugin.json` の `dependencies` に `wiki@info-hive` を宣言している。
- プラグインを足すときの手順は `AGENTS.md` の「リポジトリの役割」にある。

## 読むべき文書とコード

- `AGENTS.md`（リポジトリの役割、プラグインを足す手順、リリースとバージョン、日本語と機械が読む文字列の方針）
- `docs/porting-plan.html`（wiki の移植方針。方針 A・G など）
- `docs/adr/` の 0003（マーケットプレイスの分割）、0006（日々の記録を別プラグインにした判断）、0007（rag の構成）、0008（作業領域の構成）
- `info-hive-wiki/skills/info-hive/references/graph-workflow.md`、`info-hive-wiki/docs/graph.md`、`info-hive-wiki/commands/graph.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py`、`wiki_graph_lint.py`、`wiki_graph_query.py`
- グラフに触れている wiki 側のファイル：`skills/info-hive/SKILL.md`、`references/ingest-workflow.md`、`references/query-workflow.md`、`references/lint-workflow.md`、`references/architecture.md`、`references/decision-models.md`、`scripts/init_wiki.py`（graph のテンプレートと `SCHEMA_SECTION_MARKERS`）、`scripts/wiki_text.py`、`scripts/wiki_lint.py`・`wiki_search.py`・`wiki_stats.py`（`graph/` の除外）、`scripts/wiki_decide.py` と `eval/decisions/`、`assets/SCHEMA.md.template`、`assets/ontology.yaml.template`、`commands/ingest.md`・`query.md`・`lint.md`・`upgrade.md`
- `info-hive-rag/.claude-plugin/plugin.json`（依存の宣言の例）、`info-hive-marketplace/.claude-plugin/marketplace.json`
- Claude Code のプラグインの依存と、プラグインどうしでスクリプトや `${CLAUDE_PLUGIN_ROOT}` を参照できるかについての公式の文書

## 成果に含めるもの

1. 結論：分けるべきか、分けないべきか、条件付きか。一文で書く。
2. 判断の根拠。少なくとも次の観点を扱う：wiki の手順（取り込み・問い合わせ・lint・アップグレード）との結び付きの強さ、利用者が導入する手間と得られる軽さ、依存の向き（グラフが wiki に依存するのか、wiki がグラフの有無で分岐するのか）、PyYAML などの依存パッケージ、`${CLAUDE_PLUGIN_ROOT}` とスクリプトの置き場所、テストとリリース（SemVer とマーケットプレイス）、移植元の修正の取り込みやすさ、log と rag など今後のプラグインとの関係。
3. 分ける場合の構成案：プラグイン名、リポジトリ、wiki 側に残すもの・移すもの、wiki とのつなぎ方（依存の宣言、フック、コマンドの名前）、既存の wiki と利用者の移行。
4. 分けない場合に、境界をはっきりさせるため wiki の中で整理すべきこと。
5. 判断を変える条件（どうなったら分ける、または戻すべきか）。
6. 作者が決める必要のある未決事項。

リポジトリのファイルは書き換えないこと。成果は日本語で書く。
