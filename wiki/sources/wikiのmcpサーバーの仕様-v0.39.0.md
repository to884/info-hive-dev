---
type: "source"
title: "info-hive-wiki v0.39.0 の MCP サーバー仕様"
authors: ["to884"]
url: "https://github.com/to884/info-hive-wiki/blob/84d149ffc642f5820adf3dd2d583d4350e19a17f/skills/info-hive/references/mcp-server.md"
raw: "raw/wikiのmcpサーバーの仕様-v0.39.0.md"
raw_sha256: "ae87f29725028ce0cbb97f2712510f2b3871b9fd7b77c61510d42bf871cd36be"
repository_commit: "84d149ffc642f5820adf3dd2d583d4350e19a17f"
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
tags: ["wiki設計", "検索", "グラフ", "取り込み"]
entities: ["info-hive-wiki"]
---

# info-hive-wiki v0.39.0 の MCP サーバー仕様

タグ v0.39.0 の同梱文書「wiki の MCP サーバー」を取り込んだ。Claude Code と Codex のホストはセッションごとに入口と stdio 中継を起動し、同じデータディレクトリのローカルサーバーを共有する。サーバーは `127.0.0.1` に限定して待ち受け、起動ごとの Bearer トークンと Host ヘッダーを検査する。既定では要求のない状態が15分続くと終了する。

## ツールと取り込みの分担

| 用途 | ツールと結果 |
| --- | --- |
| 記事の検索 | `query` は Tantivy の BM25 と ruri-v3-130m の埋め込みによる usearch 検索を RRF で統合する。埋め込み中も語彙検索は wiki 全体を対象にする。 |
| 本文と索引 | `get_page` は記事本文と frontmatter、`list_index` は索引と分割索引の一覧を返す。 |
| 点検と統計 | `lint` は構造とグラフを検査し、`stats` は規模、索引の状態、サーバーの版を返す。 |
| 関係の照会 | `graph` は生成済みの SQLite を読み、近傍、主語からの関係、最短経路、入出力の関係を返す。 |
| 外部チャンクの登録 | `index_chunks` は呼び出し側が作ったトークンなどを受け取り、collection 別に索引を更新する。同じ ID と世代で再送できる。 |

> ツールと取り込みの分担 補足: `index_chunks` の書き込み先は wiki の外の索引である。通常の `ingest` はエージェントがページ・索引・ログの差分を提案し、承認済みの計画を `wiki_apply.py` で反映する。取り込み時の検査には MCP の `lint` を使える。

wiki を読む入口では、`SCHEMA.md` がある wiki の絶対パスを渡す。記事や記事までの経路に禁止されたリンクがある場合、`link_warnings` で知らせる。wiki 記事の検索索引はデータディレクトリで wiki のルートごとに分かれ、外部チャンクの索引は collection に置く。MCP が使えない場合、CLI の検索は別のモデルと索引を使う。

## v0.39.0 の版指定

同梱文書の記述に加えて同じタグの実装を確認した。公開版の wiki では `query` が語彙検索を実行して `release_id` を返す。`get_page`、`list_index`、`lint`、`graph` は同じ ID を受け付け、記事・索引・グラフを同じ公開版から読める。`stats` は現在の公開版を集計し、呼び出し側から版を指定する引数は持たない。[v0.39.0 のツール実装](https://github.com/to884/info-hive-wiki/blob/84d149ffc642f5820adf3dd2d583d4350e19a17f/skills/info-hive/scripts/wiki_mcp_server.py#L343-L530)

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 入口・中継・ローカルサーバーの分担と共有 | 仕組み | source_only | 既存の製品ページは構成の概要を持つため、このページに運用詳細を残す。 |
| c2 | 7ツールの責務と記事の取り込みとの境界 | ツール、index_chunks | update | [[info-hive-wiki]] からツールの契約を、[[リリースごとの導入の確かめの記録]] から配布版の仕様をたどれるようにする。 |
| c3 | wiki ごと・collection ごとの索引の置き場所と CLI への切り替え | 置き場所、MCP が使えないとき | source_only | このページに経路別の違いを記録する。 |

## 関係するページ

- [[info-hive-wiki]]
- [[info-hive-wikiのアーキテクチャ-v0.38.1]]
- [[リリースごとの導入の確かめの記録]]
- [[wiki切り戻し後の再公開と本番判定-2026-11-19]]
