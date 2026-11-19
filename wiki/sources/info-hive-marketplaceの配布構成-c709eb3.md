---
type: "source"
title: "info-hive-marketplace の配布構成（c709eb3）"
authors: ["to884"]
url: "https://github.com/to884/info-hive-marketplace/tree/c709eb3fd3dbb2a43d9d523160096fea3979984b"
raw: "raw/info-hive-marketplaceの配布構成-c709eb3.md"
raw_sha256: "ad9ce6c638c42b7a631bf74a8c446a2fcfa98b2bc6717cfdeed79721140b5d72"
repository_commit: "c709eb3fd3dbb2a43d9d523160096fea3979984b"
ingested: 2026-11-19
created: 2026-11-19
updated: 2026-11-19
tags: ["リリース", "wiki設計", "rag"]
entities: ["info-hive-marketplace", "info-hive-wiki", "info-hive-rag"]
---

# info-hive-marketplace の配布構成（c709eb3）

親リポジトリ `info-hive-dev` の `23abeb1` が参照する marketplace `c709eb3`、wiki `b8596d1`、rag `4fabe32` の定義を照合した。raw にカタログ3件、プラグインの定義、導入案内と ADR の該当箇所を行番号付きで保存した。

## カタログと取得先

- **Claude Code** は `to884/info-hive-marketplace` の `.claude-plugin/marketplace.json` を読む。名前は `info-hive`。掲載する `wiki` と `rag` はそれぞれ `source: "github"` で `to884/info-hive-wiki` と `to884/info-hive-rag` を指す。導入名は `wiki@info-hive` と `rag@info-hive`。rag の本体は `wiki@info-hive` を依存先に宣言する。
- **Codex** は同じリポジトリの `.agents/plugins/marketplace.json` を読む。名前は `info-hive`。掲載は `wiki` のみで、`source: "url"` と Git URL `https://github.com/to884/info-hive-wiki.git` を使う。導入名は `wiki@info-hive`。Codex CLI 0.166.0 で使う形式を ADR-0031 が記録している。
- **Codex の開発用カタログ**は `info-hive-dev/.agents/plugins/marketplace.json` にある。名前は `info-hive-dev`。掲載は `wiki` のみで、`source: "local"` と `./info-hive-wiki` が作業ツリーのサブモジュールを指す。導入名は `wiki@info-hive-dev`。

## 配布とバージョンの管理

公開カタログには取得元を記載し、調査した項目は版や Git の参照を固定していない。プラグインの `version` は取得元の `plugin.json` にあり、wiki は Claude Code 用の `.claude-plugin/plugin.json` と Codex 用の `.codex-plugin/plugin.json`、rag は Claude Code 用の `.claude-plugin/plugin.json` で管理する。カタログを本体から分ける経緯は ADR-0003 にある。

marketplace の README は Claude Code の導入を説明している。Codex の掲載状況は Codex 用 JSON、導入コマンドは wiki の README で確認できる。今回の照合では3件のカタログを JSON として読み、Claude Code の公開カタログは `claude plugin validate` でも検証した。導入時の検証記録は [[リリースごとの導入の確かめの記録]] にある。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | Claude Code の公開カタログは wiki と rag を GitHub の別リポジトリから配る | raw「公開カタログと開発用カタログ」の marketplace 側 `.claude-plugin/marketplace.json` | `create` | [[info-hive-marketplace]] の配布図に掲載 |
| c2 | Codex の公開カタログに載るのは Git URL を使う wiki のみ | 同節の marketplace 側 `.agents/plugins/marketplace.json` | `create` | [[info-hive-marketplace]] の配布図に掲載 |
| c3 | Codex の開発用カタログは親リポジトリのローカル wiki を指す | 同節の dev 側 `.agents/plugins/marketplace.json` | `create` | [[info-hive-marketplace]] に開発時の経路を掲載 |
| c4 | カタログが取得元を、プラグイン本体の定義がバージョンを持つ | raw「公開カタログと開発用カタログ」「プラグイン本体の定義」と ADR-0003 | `create` | [[info-hive-marketplace]] に配布とリリースの責務を記録 |
| c5 | wiki は両ホストの公開カタログで同じ導入名を使う | 公開カタログ2件と wiki の README「インストール」 | `update` | [[info-hive-wiki]] に配布経路へのリンクを追加 |
| c6 | rag は Claude Code 向けに掲載され、wiki に依存する | Claude Code の公開カタログ、rag のプラグイン定義と README「導入」 | `update` | [[info-hive-rag]] に配布経路へのリンクを追加 |

> Codex 補足: 配布の全体図はマーケットプレイスのページに置き、プラグインのページからも参照できるようにした。

## 関係するページ

- [[info-hive-marketplace]]
- [[info-hive-wiki]]
- [[info-hive-rag]]
- [[リリースごとの導入の確かめの記録]]
