---
type: "source"
title: "rag のコマンド一覧（4fabe32）"
authors: ["to884"]
url: "https://github.com/to884/info-hive-rag/tree/4fabe3294d86a367e635bc18635af6e7132a8d93/commands"
raw: "raw/ragのコマンド一覧-4fabe32.md"
raw_sha256: "b9351fe5b1f5e9ba0dc5b044a4df9b2b542ab83184ad42e19d8a3393dddad304"
repository_commit: "4fabe3294d86a367e635bc18635af6e7132a8d93"
tags: ["コマンド", "rag", "検索", "取り込み"]
entities: ["info-hive-rag", "info-hive-wiki"]
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
---

# rag のコマンド一覧（4fabe32）

[[info-hive-rag]] の Claude Code 用コマンドは3つ。親リポジトリが参照するコミット `4fabe32` の3定義はタグ v0.5.3 と同じ。利用時は `rag@info-hive` と依存先の `wiki@info-hive` を有効にする。[コマンド定義](https://github.com/to884/info-hive-rag/tree/4fabe3294d86a367e635bc18635af6e7132a8d93/commands)

## コマンドと主な引数

| コマンド | 主な引数 | 用途と結果 |
| --- | --- | --- |
| `/rag:setup` | 保存先、埋め込みモデル、OCR、検索設定の指定 | MCP の `configure` で指定した項目を更新する。`reingest_required` は取り込み直しの要否、`extraction_changed` はその際に抽出もやり直すかを示す。 |
| `/rag:status` | 既定の対象 wiki、必要なら対象の指定 | MCP の `status` で、その wiki の文書・チャンク数、ジョブ ID、進捗、失敗理由、取り込み直す PDF の一覧を確認する。 |
| `/rag:search` | `<質問>` | 公開済みの PDF 索引を MCP の `search` で検索する。取得した本文、ページ番号、原本のパス、wiki の出典ページを根拠に Claude Code が回答する。例は `/rag:search 契約の更新条件はどのページにある？`。 |

> Codex 補足: 設定を変えるのが `setup`、索引と進捗を確認するのが `status`、索引済み PDF の中を探すのが `search`。

## setup の設定項目

- `data_dir` は抽出結果・索引など派生データの保存先。変更すると以前の保存先の結果を引き継がないため、PDF の取り込み直しが必要になる。
- `embedding_model` は埋め込みモデル。既定は `cl-nagoya/ruri-v3-130m`。モデルだけを変えたときは、抽出済みの本文を使って埋め込みと索引を作り直す。
- `ocr_mode` は `auto`（必要と判定したページ）、`always`（全ページ）、`off`（OCR を無効）のいずれか。既定は `auto`。`ocr_dpi` は72〜300の整数で既定は150。これらを変更すると、新しい設定で抽出・索引化し直す。
- `retrieval` はリランクなどの検索設定。変更後も既存の索引を使える。

## 登録とジョブ操作

PDF を加える入口は [[wikiのコマンド一覧-v0.38.1|wiki の ingest]]。原本の絶対パスを渡すと、エージェントが rag MCP の `register_pdf` で受付し、`job_status` で `completed` を待つ。索引化済みの本文は `/rag:search`、wiki に保存された知識ページは `/wiki:query` で探す。

`queued`・`running`・`paused` は処理中の状態。次回の rag MCP 接続時に未完了ジョブが再開される。失敗の原因を解消したら MCP の `retry_job` で再試行し、途中で止めるときは `cancel_job` の `cancellation_accepted` を確認する。索引の公開開始までキャンセルを受理する。

## 取り込んだ内容と載せたページ

| 番号 | 内容 | 出典の該当箇所 | 掲載方法 | 掲載先または理由 |
| --- | --- | --- | --- | --- |
| c1 | 3コマンドの用途、引数、結果 | `commands/setup.md`、`commands/status.md`、`commands/search.md` | `source_only` | 本ページをコマンドリファレンスとして使う |
| c2 | PDF 登録の入口とジョブの進捗・再試行 | wiki の `commands/ingest.md` の PDF 登録節、`scripts/rag_server.py` | `source_only` | 取り込みと索引検索の入口を併記した |
| c3 | 製品ページからコマンド一覧を参照できる | rag の `commands/` | `update` | [[info-hive-rag]] に一覧へのリンクを追加 |

> Codex 補足: コマンドから呼ぶ MCP のツール名は、設定結果やジョブの状態を追うときの手がかりになる。

## 関係するページ

- [[info-hive-rag]]
- [[info-hive-ragのアーキテクチャ-4fabe32]]
- [[wikiのコマンド一覧-v0.38.1]]
