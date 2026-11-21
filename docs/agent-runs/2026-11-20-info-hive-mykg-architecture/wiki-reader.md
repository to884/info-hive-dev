## 結論

Agent ツールで `wiki:wiki-reader` を1回だけ呼びました（model=sonnet、effort=medium）。候補の2ページ（`entities/info-hive-wiki.md`、`sources/info-hive-wikiのアーキテクチャ-v0.38.1.md`）だけを読み、リンク先は開いていません。私自身はページを開いていないため、本文と突き合わせた確認もしていません。以下は reader の報告の要約です。

## 要約（候補2ページの範囲）

- **書き込み**: エージェントが raw の原本と `SCHEMA.md` の規約を読み、`wiki/` の Markdown を編集します。資料の保存、取得、照合は、入力の形式ごとのスクリプトが受け持ちます。入口は Claude Code では `/wiki:*`、Codex では `$wiki:info-hive` で、両方が `commands/*.md` を使います。両ホストの MCP の登録は、どちらも `wiki_mcp_launch.py` を指します。
  - 根拠: entities の「アーキテクチャ」節（入口と正本）、sources の「ホストと書き込み」節
- **MCP と検索**: 中継はホストのセッションごとに起動し、`127.0.0.1` の共有 MCP サーバーにつなぎます。MCP の検索は Tantivy BM25 と、ruri-v3-130m の ONNX 埋め込みを使う usearch の結果を、RRF で統合します。索引は wiki の外に置きます。
  - CLI の検索は別の系統で、索引を `.wiki-cache/` に持ちます。
  - `index_chunks` の外部チャンクは、collection ごとに別に保持します。
  - `query` は候補のセクションを返します。`lint`、`stats`、`graph` は CLI と同じ処理を呼びます。
  - 根拠: sources の「MCP と検索索引」節（索引の対応表）、entities の「検索」項
- **graph**: `wiki_graph_extract.py` が frontmatter と本文を `graph/ontology.yaml` に沿って処理し、JSONL、SQLite、GraphML を作ります。どれも作り直せる生成物です。型付きの関係には出典と引用を付けます。通常の wikilink から作る `mentions` は、記事をたどるために使います。MCP の `graph` は、生成済みの `graph.sqlite` を読みます。
  - 根拠: sources の「グラフと browse」節、entities の「グラフ」項
- **browse**: `Snapshot` からページ、被リンク、関係表を組み立てます。関係表は、記事の写しに `build_nodes()` と `build_edges()` をかけて作ります。静的な `build` とローカル HTTP の `serve` は、同じ描画の中核を使います。Mermaid は、静的版では SVG に書き出し、サーバー版では専用の枠で描きます。「同じオリジンのタブ間で一度に一つの枠」という制約は、v0.38.1 の挙動として書かれています。
  - 根拠: sources の「グラフと browse」節、entities の「閲覧」項
- **公開版の責務**: 2ページに記述がありません。`release_id` や公開版の扱いも出てこないため、wiki から答えは出せません。
- **既存の設計案と実装の区別**: entities の冒頭に「以下の構成はタグ v0.38.1 の実装をもとにしている」とあり、2ページとも実装の記述として扱えます。設計案の節はありません。
  - Box Drive について確かめたのは、1台の PC での初期化から再編集までです。複数の端末は、確定版のアーカイブか静的 HTML の配布で扱うとしています（entities の「Box Drive 上の wiki」項）。

## 未確認の点

- **v0.38.1 と v0.39.0 の差は、推測で補っていません。** entities は v0.39.0 の MCP に触れていて、検索、記事の取得、点検、統計、グラフの照会、外部チャンクの索引化を挙げています。ただし詳細は `sources/wikiのmcpサーバーの仕様-v0.39.0.md` に任せています。このページは読んでいないので、v0.38.1 の記事との差は確かめていません。
- **myKG との比較**: 2ページに myKG の記述はありません。
- **読んでいない関連ページ**: `wikiのmcpサーバーの仕様-v0.39.0`、`グラフの抽出の契約`、`box-drive上のwikiの運用`、`info-hive-rag`、raw の `info-hive-wikiのアーキテクチャ-v0.38.1.md`
- **仮定**: v0.39.0 の差と公開版の責務を埋めるには、まず `sources/wikiのmcpサーバーの仕様-v0.39.0.md` を読む必要があります。このページはフックの候補の3番目で、要約に「0.39.0 での公開版の指定」と書かれていたため、こう判断しました。

## 実際に呼んだモデルとエフォート

- 指定: `subagent_type=wiki:wiki-reader`、`model=sonnet`、`effort=medium`、1回だけ
- reader の自己申告: Sonnet 5.5（`claude-sonnet-5-5`）。ツールの呼び出しは3回です。

`✶ Insight ─────────────────────────────────────`
- フックの読み方には段があります。普段は R1（effort=low）ですが、複数ページの比較や設計判断の根拠を求めるときだけ、理由を1行書いて R3（effort=medium）に上げます。今回は依頼元がその理由を書いていました。
- reader はリンク先を2ページまで読めましたが、読みませんでした。そのため v0.39.0 の差は空白のまま残っています。読む範囲を候補に絞ると、本文が呼び出し元の文脈に入らない代わりに、こうした取りこぼしが出ます。
`─────────────────────────────────────────────────`

**このタスクに合うモデル**: Sonnet（effort は medium）
**次のタスク**: `sources/wikiのmcpサーバーの仕様-v0.39.0.md` を読み、v0.39.0 の差と公開版の責務を補う作業も、`wiki:wiki-reader` に Sonnet、effort は medium で任せるのが合っています。

使用した MCP サーバー: plugin:wiki:wiki（`get_page`、wiki-reader の中で使用）
使用した Agent Skills: なし
