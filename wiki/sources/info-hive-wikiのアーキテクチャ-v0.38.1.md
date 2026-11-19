---
type: "source"
title: "info-hive-wiki v0.38.1 のアーキテクチャ"
authors: ["to884"]
url: "https://github.com/to884/info-hive-wiki/tree/b8596d1888035769528cb74e35bda51c9d9c40a0"
raw: "raw/info-hive-wikiのアーキテクチャ-v0.38.1.md"
raw_sha256: "f2d69d52eb4cbd310b1d89c9d69699d192b775df0f045b1ca62d0f3c2a05bb2b"
repository_commit: "b8596d1888035769528cb74e35bda51c9d9c40a0"
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
tags: ["wiki設計", "取り込み", "検索", "グラフ", "browse", "rag"]
entities: ["info-hive-wiki"]
concepts: ["グラフの抽出の契約"]
---

# info-hive-wiki v0.38.1 のアーキテクチャ

2026-11-19 の Git タグ v0.38.1（`b8596d1888035769528cb74e35bda51c9d9c40a0`）のコードと同梱文書を照合した。raw に、そのコミットの抜粋と行番号付きの参照を保存した。

## ホストと書き込み

- Claude Code は `commands/*.md` を `/wiki:*` として使う。Codex は `$wiki:info-hive <操作> <引数>` を入口とし、`wiki_codex.py` が同じファイルを読み、ホスト向けに表記を変えて表示する。両ホストの MCP 登録は共通の `wiki_mcp_launch.py` を指す。
- 取り込みでは、資料の保存・取得・照合を入力形式ごとのスクリプトが担当する。エージェントは原本を読んで要約と関連ページを編集し、索引とログを更新する。wiki 固有の規約はルートの `SCHEMA.md` に置く。[[初期化されたwikiの判定]] に入口での判定を記録している。
- Claude Code の `UserPromptSubmit` フックには、操作コマンドと別に候補ページを知らせる入口がある。`hooks/hooks.json` が `wiki_prompt_hook.py` を起動する。

## MCP と検索索引

ホストのセッションごとに起動した `wiki_mcp_launch.py` が、stdio の `wiki_mcp_relay.py` を動かす。中継は `127.0.0.1` の `wiki_mcp_server.py` を共有する。モデルの読み込みと MCP の索引更新をサーバーに集約するため、ホストのセッションが増えても同じモデルと索引を使える。

| 経路 | 語彙検索とベクトル検索 | 索引の保存先 |
| --- | --- | --- |
| MCP の wiki 検索 | Tantivy の BM25 と ruri-v3-130m の ONNX 埋め込みを使う usearch の検索を RRF で統合 | wiki の外のデータディレクトリにルート別に作る。SQLite を索引の台帳とし、usearch と Tantivy は台帳から再構築できる |
| CLI の wiki 検索 | 日本語対応 BM25 と、FastEmbed の multilingual-e5-small・sqlite-vec によるベクトル検索。依存なしの語彙検索は `--no-embed` | wiki 内の `.wiki-cache/` |
| MCP の外部チャンク検索 | `index_chunks` の呼び出し元がトークンを用意し、必要に応じて MCP が埋め込む | wiki の外に collection 単位で作る |

> Codex 補足: MCP と CLI はそれぞれ索引を持つ。MCP 内でも wiki ページと外部チャンクは保存単位とトークンの供給元が異なる。

`query` は候補となるセクションを返す。`get_page` と `list_index` は記事と索引を読み、`lint`、`stats`、`graph` は CLI と共通の処理を呼ぶ。PDF の取り込みで rag が使える場合、エージェントは rag の `register_pdf` に原本のパスを渡し、ジョブの完了後に抽出結果を要約する。wiki の MCP には、外部の呼び出し元からチャンクを受け取る `index_chunks` もある。

## グラフと browse

`wiki_pages.py` はページの列挙と wikilink の抽出・解決を共有する。グラフ層を有効にすると、`wiki_graph_extract.py` が Markdown の frontmatter と本文を `graph/ontology.yaml` に沿って処理し、JSONL、SQLite、GraphML を作る。`graph.relationships` の型付き関係には明示した出典と引用を付ける。通常の wikilink からできる `mentions` は、記事を探すときに使う。MCP の `graph` は生成済みの `graph.sqlite` を読む。

browse は `wiki_browse_fs.py` を通じて入力を読み、`wiki_browse_core.py` の `Snapshot` からページ、被リンク、関係表を組み立てる。関係表は写しに `build_nodes()` と `build_edges()` を適用して作る。静的な `build` とローカル HTTP の `serve` は同じ描画中核を使う。

静的版は Pele で Mermaid を明暗の SVG にできる。サーバー版の Mermaid は専用の描画枠を使い、v0.38.1 では同じオリジンのタブ間で一度に一つの枠だけを動かす。記事の概要は `assets/overview/` のサイドカーとして保存する。[図の描画の変更履歴](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/CHANGELOG.md#L9-L25)、[概要の保存処理](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_overview.py#L754)

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | Claude Code と Codex は操作手順と MCP の起動処理を共用する | raw「ホストの入口」のプラグイン定義と `wiki_codex.py` | `create` | [[info-hive-wiki]] にホストとの接続を記録 |
| c2 | エージェントが raw と `SCHEMA.md` をもとに Markdown を更新する | raw「3 つの層と書き込み」 | `create` | [[info-hive-wiki]] に正本への書き込み経路を記録 |
| c3 | MCP はモデルと索引を共有サーバーに集約する。CLI 検索は別のモデルと索引を使う | raw「MCP のプロセスと検索」の `wiki_mcp_relay.py`、`wiki_index.py`、MCP 文書の末尾 | `create` | [[info-hive-wiki]] に検索の境界を記録 |
| c4 | グラフは Markdown とオントロジーから再生成できる | raw「ページの解釈とグラフ」の `wiki_graph_extract.py` とグラフ手順 | `create` | [[info-hive-wiki]] にグラフの生成経路を記録 |
| c5 | browse の関係表は記事の写しから抽出関数を呼んで組み立てる | raw「browse の閲覧経路」の `wiki_browse_core.py` 1328–1341 行 | `update` | [[グラフの抽出の契約]] に v0.38.1 での確認を追記 |
| c6 | browse の静的版とサーバー版は描画中核を共有し、Mermaid の描画経路が異なる | raw「browse の閲覧経路」の `wiki_browse_core.py` 冒頭と変更履歴 | `create` | [[info-hive-wiki]] に表示方法の分担を記録 |
| c7 | rag は PDF の処理を担当し、外部チャンク用の MCP 索引は wiki ページ用と分かれる | raw「3 つの層と書き込み」の `commands/ingest.md` 78–84 行、「MCP のプロセスと検索」の `index_chunks` | `create` | [[info-hive-wiki]] に連携の境界を記録 |
| c8 | Claude Code の指示のフックが候補ページを知らせる | raw「ホストの入口」の `hooks/hooks.json` | `source_only` | ホスト固有の補助経路として記録 |
| c9 | ページの概要はサイドカーとして保存する | 上記「概要の保存処理」の `wiki_overview.py` 754 行 | `source_only` | 記事本文と別に保存する補助機能として記録 |

> Codex 補足: 構成をたどる入口は製品ページに置いた。browse とグラフの接点は既存ページに追記した。

## 関係するページ

- [[info-hive-wiki]]
- [[グラフの抽出の契約]]
- [[初期化されたwikiの判定]]
