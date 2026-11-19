---
type: "source"
title: "wiki のコマンド一覧（v0.38.1）"
authors: ["to884"]
url: "https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/docs/commands.md"
raw: "raw/wikiのコマンド一覧-v0.38.1.md"
raw_sha256: "5f5b4ba67bfc3aa989aeb267ebaad2cea795505fd0b10d65eb7d7ff7eeba432c"
repository_commit: "b8596d1888035769528cb74e35bda51c9d9c40a0"
tags: ["コマンド", "取り込み", "wiki設計"]
entities: ["info-hive-wiki"]
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
---

# wiki のコマンド一覧（v0.38.1）

対象は [[info-hive-wiki]] のタグ v0.38.1。Claude Code では `/wiki:<コマンド>`、Codex では `$wiki:info-hive <コマンド>` を使う。例えば `/wiki:help graph` は Codex では `$wiki:info-hive help graph` と書く。両方で同じ12操作が使える。[コマンドの正本](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/docs/commands.md)

## コマンドと主な引数

| Claude Code | 主な引数 | 用途と結果 |
| --- | --- | --- |
| `/wiki:init` | `--user`、`--wiki-dir <名前>`、`--raw-dir <名前>` | wiki を作り、`SCHEMA.md`、索引、ログ、ローカル検索環境を用意する。既定はこのプロジェクトの `wiki/` と `raw/`。ユーザー共通の保存先には `--user` を使う。 |
| `/wiki:ingest` | ファイルパス、URL、`session`、`session:<ID>`、資料の指定 | 資料を取り込み、出典の要約と関連ページ、索引、ログを更新する。YouTube の URL では字幕、`session` では実行中の会話を取り込む。 |
| `/wiki:query` | `<質問>` | wiki のページや raw の根拠をたどり、出典付きで回答する。根拠のある結論には確信度を示し、保存に適した回答はシンセシスとして残せる。 |
| `/wiki:lint` | `--suggest-pages` | リンク切れ、孤立、frontmatter、古い記事、記述の矛盾などを点検し、修正案を示す。`--suggest-pages` で独立ページの候補も調べる。 |
| `/wiki:stats` | 引数なし | ページ数、種類別の内訳、リンク密度、よく参照されるページを確認する。索引を分割する規模に達したかの判断にも使う。 |
| `/wiki:graph` | `extract`、`lint`、`neighbors`、`edges`、`path`、`facts` | 型付きの関係を生成・検査し、周辺のノードや経路を調べる。`graph/ontology.yaml` がある wiki で使う。 |
| `/wiki:browse` | `[スラッグ]` または `--stop` | ローカル閲覧サーバーで wiki を開く。スラッグで記事を直接開き、引数を省くと索引を開く。`--stop` でサーバーを止める。 |
| `/wiki:overview` | `<ページ> [--refresh]`、`--status`、`--remove <ページ>` | 指定ページの図を中心とした概要を `wiki/assets/overview/` に保存し、browse で表示する。`--refresh` は再生成、`--status` は状態一覧、`--remove` は概要だけの削除。 |
| `/wiki:learn` | `<検証済みのタスクや成果物>` | 実際の成果・検証記録を経験の raw JSON として残し、適用範囲や反例を添えて再利用できる教訓にまとめる。 |
| `/wiki:evolve` | `<スキルと改善の目的>`、`history`、`show <ID>`、`apply <ID>`、`rollback <ID>` | 証拠をもとに改善案を作って評価する。`history` と `show` は実験の閲覧、`apply` は評価・レビュー済みで承認された案の適用、`rollback` は適用を戻す操作。 |
| `/wiki:upgrade` | `--user`、`--wiki-dir <パス>`、`--raw-dir <パス>`、`--previous-raw-root <パス>` | 既存 wiki の保存形式と実行環境を導入済みプラグインの版に合わせる。`--previous-raw-root` は過去の原本の場所を記録するために繰り返し指定できる。 |
| `/wiki:help` | `[コマンド名]` | 引数なしで一覧、`help query` のように名前を渡すと書式・引数・例を表示する。 |

> Codex 補足: 初回は `init`、資料を加えるときは `ingest`、蓄積した資料に質問するときは `query`。書式を確認するには `help` にコマンド名を渡す。

## グラフのサブコマンド

- `extract` は Markdown を読み、JSONL、SQLite、GraphML のグラフを生成する。
- `lint` は型付きエッジの述語や根拠を検査し、結果を示す。
- `neighbors --node <id>` は指定ノードの隣接ノードを調べる。
- `edges --subject <id> [--predicate <述語>]` は指定ノードから出るエッジを調べる。
- `path --from <id> --to <id> [--max-depth <数>]` は有向グラフで二つのノードを結ぶ最短経路を調べる。
- `facts --about <id>` は指定ノードへ入る関係と出る関係を調べる。例えば `/wiki:graph facts --about product:info-hive-rag`。

## 操作の境界

- `init` と `help` 以外は、ルートに `SCHEMA.md` がある wiki が対象。既存 wiki の整備には `upgrade` を使い、`SCHEMA.md` の変更案が示されたときは差分を確認する。
- Claude Code で rag が使えるとき、`/wiki:ingest <PDF の絶対パス>` が rag に登録する。索引化の完了後、抽出本文から wiki の要約を作る。PDF 内をページ番号付きで探すには [[ragのコマンド一覧-4fabe32|rag の search]] を使う。
- `learn` は検証済みの経験を残す操作。`evolve` で有料の評価を実行する場合は、承認された実行方法と予算が必要。

## 取り込んだ内容と載せたページ

| 番号 | 内容 | 出典の該当箇所 | 掲載方法 | 掲載先または理由 |
| --- | --- | --- | --- | --- |
| c1 | 12操作の用途・書式と Codex での呼び方 | `commands/*.md`、`docs/commands.md`、`references/codex.md` | `source_only` | 本ページをコマンドリファレンスとして使う |
| c2 | グラフと PDF 取り込みのサブ操作 | `commands/graph.md`、`commands/ingest.md` | `source_only` | 一覧から続けて参照できるようにした |
| c3 | 製品ページからコマンド一覧を参照できる | `commands/` とヘルプの一覧 | `update` | [[info-hive-wiki]] に一覧へのリンクを追加 |

> Codex 補足: コマンド定義と使用説明を版ごとに照合できるよう、原本を保存した。

## 関係するページ

- [[info-hive-wiki]]
- [[info-hive-wikiのアーキテクチャ-v0.38.1]]
- [[ragのコマンド一覧-4fabe32]]
- [[helpの個別のヘルプとリリース-wiki-0.14.0]]
