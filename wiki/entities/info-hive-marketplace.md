---
type: "entity"
kind: "product"
title: "info-hive-marketplace"
aliases: ["info-hive マーケットプレイス"]
tags: ["リリース", "wiki設計"]
sources: ["info-hive-marketplaceの配布構成-c709eb3"]
created: 2026-11-19
updated: 2026-11-19
---

# info-hive-marketplace

`to884/info-hive-marketplace` は、各プラグインの取得先を定義する `info-hive` の公開カタログを置くリポジトリ。以下はコミット `c709eb3` の構成。[[info-hive-marketplaceの配布構成-c709eb3]]

## Claude Code と Codex の公開配布

配布先のプラグインと実行時の PDF 取り込みは [[info-hiveの配布と実行の全体図]] で続けてたどれる。

```mermaid
flowchart TD
    Claude["Claude Code"] --> ClaudeCatalog[".claude-plugin/marketplace.json"]
    Codex["Codex"] --> CodexCatalog[".agents/plugins/marketplace.json"]
    ClaudeCatalog -->|"wiki@info-hive"| Wiki["to884/info-hive-wiki"]
    ClaudeCatalog -->|"rag@info-hive"| Rag["to884/info-hive-rag"]
    CodexCatalog -->|"wiki@info-hive"| Wiki
```

> Codex 補足: 両カタログは `to884/info-hive-marketplace` にあり、カタログ名はどちらも `info-hive`。Claude Code は wiki と rag を掲載し、Codex は wiki のみを掲載する。矢印のラベルは導入時の名前。

- Claude Code のカタログは、各プラグインを `source: "github"` と `repo` で指定する。[[info-hive-rag]] は `wiki@info-hive` に依存する。
- Codex のカタログは、[[info-hive-wiki]] を `source: "url"` と `https://github.com/to884/info-hive-wiki.git` で指定する。
- バージョンは各取得先のプラグイン定義 `plugin.json` で管理する。

## Codex の開発用カタログ

```mermaid
flowchart TD
    Codex["Codex"] --> Local["info-hive-dev の開発用カタログ"]
    Local -->|"wiki@info-hive-dev"| Wiki["ローカルの info-hive-wiki"]
```

> Codex 補足: 親リポジトリの `info-hive-dev/.agents/plugins/marketplace.json` は、`source: "local"` で `./info-hive-wiki` を参照する。作業ツリーの変更を試すときに使う。
