# info-hive-marketplace の配布構成の根拠

開発用リポジトリのサブモジュール参照と、各リポジトリの該当する Git コミットを照合した。

- info-hive-dev 23abeb19e1fa42cd4d974c99bb9c0d44f5bec000
- info-hive-marketplace c709eb3fd3dbb2a43d9d523160096fea3979984b
- info-hive-wiki b8596d1888035769528cb74e35bda51c9d9c40a0
- info-hive-rag 4fabe3294d86a367e635bc18635af6e7132a8d93

## 公開カタログと開発用カタログ

- [info-hive-marketplace/.claude-plugin/marketplace.json 1 行目から](https://github.com/to884/info-hive-marketplace/blob/c709eb3fd3dbb2a43d9d523160096fea3979984b/.claude-plugin/marketplace.json#L1-L53)

````
{
  "name": "info-hive",
  "owner": {
    "name": "to884"
  },
  "metadata": {
    "description": "info-hive の Claude Code プラグインを配るマーケットプレイス。"
  },
  "plugins": [
    {
      "name": "wiki",
      "source": {
        "source": "github",
        "repo": "to884/info-hive-wiki"
      },
      "description": "日本語の Markdown の wiki を構築・保守する。日本語に対応したローカルのハイブリッド検索（BM25 と多言語の埋め込み）、出典つきの回答、任意の型付きグラフ、Shift_JIS などのソースの文字コードの変換を備える。タスクの経験を記録し、スキルの改善案を評価して適用・ロールバックできる。info-hive スキルと 11 本の /wiki:* コマンド（一覧は /wiki:help）を含む。",
      "author": {
        "name": "to884"
      },
      "homepage": "https://github.com/to884/info-hive-wiki",
      "repository": "https://github.com/to884/info-hive-wiki",
      "license": "MIT",
      "category": "productivity",
      "keywords": [
        "knowledge-base",
        "wiki",
        "notes",
        "research",
        "japanese"
      ]
    },
    {
      "name": "rag",
      "source": {
        "source": "github",
        "repo": "to884/info-hive-rag"
      },
      "description": "wiki@info-hive に依存し、RAG（検索拡張生成）を扱う info-hive の Claude Code プラグイン。PDF の抽出、必要なページの OCR、埋め込み、索引化を永続ジョブとして進め、Claude Code を終えても次の接続時に再開する。日本語に対応したローカルのハイブリッド検索（BM25 と埋め込み）を MCP で提供する。3 本の /rag:* コマンド（setup、status、search）を含む。",
      "author": {
        "name": "to884"
      },
      "homepage": "https://github.com/to884/info-hive-rag",
      "repository": "https://github.com/to884/info-hive-rag",
      "license": "MIT",
      "category": "productivity",
      "keywords": [
        "rag",
        "retrieval-augmented-generation",
        "japanese"
      ]
    }
  ]
}
````

- [info-hive-marketplace/.agents/plugins/marketplace.json 1 行目から](https://github.com/to884/info-hive-marketplace/blob/c709eb3fd3dbb2a43d9d523160096fea3979984b/.agents/plugins/marketplace.json#L1-L20)

````
{
  "name": "info-hive",
  "interface": {
    "displayName": "info-hive"
  },
  "plugins": [
    {
      "name": "wiki",
      "source": {
        "source": "url",
        "url": "https://github.com/to884/info-hive-wiki.git"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
````

- [info-hive-dev/.agents/plugins/marketplace.json 1 行目から](https://github.com/to884/info-hive-dev/blob/23abeb19e1fa42cd4d974c99bb9c0d44f5bec000/.agents/plugins/marketplace.json#L1-L12)

````
{
  "name": "info-hive-dev",
  "interface": { "displayName": "info-hive（ローカル開発）" },
  "plugins": [
    {
      "name": "wiki",
      "source": { "source": "local", "path": "./info-hive-wiki" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
````

## プラグイン本体の定義

- [info-hive-wiki/.claude-plugin/plugin.json 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/.claude-plugin/plugin.json#L1-L9)

````
{
  "name": "wiki",
  "version": "0.38.1",
  "description": "日本語による Markdown の wiki を構築し、ローカルのハイブリッド検索、出典つきの回答、グラフ、タスクの経験からのスキル改善を提供する。praneybehl/llm-wiki-plugin v4.0.1 の日本語向け移植版。",
  "author": {
    "name": "to884"
  },
  "license": "MIT",
  "homepage": "https://github.com/to884/info-hive-wiki",
````

- [info-hive-wiki/.codex-plugin/plugin.json 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/.codex-plugin/plugin.json#L1-L9)

````
{
  "name": "wiki",
  "version": "0.38.1",
  "description": "日本語の Markdown の wiki を構築・保守し、ローカル検索、出典つきの回答、グラフ、閲覧、経験の記録を提供する。",
  "author": { "name": "to884" },
  "license": "MIT",
  "homepage": "https://github.com/to884/info-hive-wiki",
  "repository": "https://github.com/to884/info-hive-wiki",
  "skills": "./skills/",
````

- [info-hive-rag/.claude-plugin/plugin.json 1 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/.claude-plugin/plugin.json#L1-L9)

````
{
  "name": "rag",
  "version": "0.5.3",
  "description": "wiki@info-hive に依存し、PDF の抽出・OCR・埋め込みを永続ジョブで進め、中断後の再開とローカル検索を提供する Claude Code プラグイン。",
  "dependencies": [
    "wiki@info-hive"
  ],
  "author": {
    "name": "to884"
````

## 導入経路と設計の経緯

- [info-hive-marketplace/README.md 1 行目から](https://github.com/to884/info-hive-marketplace/blob/c709eb3fd3dbb2a43d9d523160096fea3979984b/README.md#L1-L23)

````
# info-hive-marketplace

info-hive の Claude Code プラグインを配るマーケットプレイスである。マーケットプレイス名は `info-hive` で、プラグインは `<プラグイン名>@info-hive` の形で入れる。プラグインの本体は、それぞれ別のリポジトリにある。このリポジトリには、マーケットプレイスの定義（`.claude-plugin/marketplace.json`）だけを置く。

## 入れ方

Claude Code で、マーケットプレイスを追加してからプラグインを入れる。

```
/plugin marketplace add to884/info-hive-marketplace
/plugin install wiki@info-hive
```

新しいバージョンを取り込むときは、`/plugin marketplace update` のあとに `/plugin install wiki@info-hive` を実行する。

## 載っているプラグイン

| プラグイン | 入れるときの名前 | リポジトリ | 内容 |
| --- | --- | --- | --- |
| wiki | `wiki@info-hive` | [to884/info-hive-wiki](https://github.com/to884/info-hive-wiki) | 日本語に特化した LLM Wiki。日本語の Markdown の wiki を構築・保守する。日本語に対応したローカルのハイブリッド検索（BM25 と多言語の埋め込み）、出典つきの回答、任意の型付きグラフ、Shift_JIS などのソースの文字コードの変換を備える。タスクの経験を記録し、スキルの改善案を評価して適用・ロールバックできる。`/wiki:*` のコマンドを 11 本含み、一覧は `/wiki:help` で見られる。 |
| rag | `rag@info-hive` | [to884/info-hive-rag](https://github.com/to884/info-hive-rag) | `wiki@info-hive` に依存する RAG（検索拡張生成）のプラグイン。PDF の抽出、必要なページの OCR、埋め込み、索引化を永続ジョブとして進め、Claude Code を終えても次の接続時に再開する。日本語に対応したローカルのハイブリッド検索（BM25 と埋め込み）を MCP で提供する。`/rag:*` のコマンドを 3 本（setup、status、search）含む。 |

## 旧リポジトリ to884/info-hive から移るとき
````

- [info-hive-marketplace/README.md 35 行目から](https://github.com/to884/info-hive-marketplace/blob/c709eb3fd3dbb2a43d9d523160096fea3979984b/README.md#L35-L45)

````
1. プラグインのリポジトリを作り、`.claude-plugin/plugin.json` に `name` と `version` を書く。
2. このリポジトリの `.claude-plugin/marketplace.json` の `plugins` に項目を足す。
   - `name` は、プラグインの `plugin.json` の `name` とそろえる。そろっていないと、入れるときにプラグインが見つからない。
   - `source` は `{"source": "github", "repo": "to884/<リポジトリ名>"}` とする。`ref` は書かず、既定のブランチを配る。
   - `version` は書かない。バージョンは、プラグインの `plugin.json` だけに書く。
3. `claude plugin validate .` で確かめる。
4. この README の「載っているプラグイン」の表に 1 行足す。

プラグインのバージョンを上げても、このリポジトリは直さなくてよい。Claude Code は、プラグインの `plugin.json` の `version` が変わったときに、更新があると判断する。

開発の決まりと手順は、開発用のリポジトリ [to884/info-hive-dev](https://github.com/to884/info-hive-dev) にある。
````

- [info-hive-wiki/README.md 5 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/README.md#L5-L30)

````
Claude Code と Codex では `wiki@info-hive` プラグインとして、ほかの対応エージェントでは `info-hive` スキルとして使う。スキルは [Agent Skills](https://agentskills.io) 形式である。

## インストール

最初に [`uv`](https://docs.astral.sh/uv/getting-started/installation/) をインストールする。同梱のスクリプト用に、必要な Python と依存パッケージを `uv` が用意する。初回は検索用モデルも取得するため、数分かかることがある。

### Claude Code

Claude Code のチャットで次を実行する。スキル、MCP サーバー、`/wiki:*` コマンドがまとめて入る。

```text
/plugin marketplace add to884/info-hive-marketplace
/plugin install wiki@info-hive
```

### Codex

ターミナルで次を実行する（Codex CLI 0.166.0 で確認）。スキルと MCP サーバーをまとめて導入できる。

```bash
codex plugin marketplace add to884/info-hive-marketplace
codex plugin add wiki@info-hive
```

導入後は新しいチャットを開き、`$wiki:info-hive <操作> <引数>` の形で呼び出す。MCP は自動登録され、Claude CLI は不要である。操作の一覧は `$wiki:info-hive help`、個別の使い方は `$wiki:info-hive help query` で確認できる。

````

- [info-hive-rag/README.md 11 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/README.md#L11-L29)

````

| 対象 | 名前 |
| --- | --- |
| リポジトリ | `to884/info-hive-rag` |
| プラグイン | `rag` |
| マーケットプレイス | `info-hive` |
| 導入するときの名前 | `rag@info-hive` |

## 導入

Claude Code で、マーケットプレイスを追加してから `rag` を入れます。依存先の `wiki` も自動で導入されます。

```text
/plugin marketplace add to884/info-hive-marketplace
/plugin install rag@info-hive
```

## PDF の取り込み

````

- [info-hive-dev/docs/adr/0003-split-marketplace-repo.md 10 行目から](https://github.com/to884/info-hive-dev/blob/23abeb19e1fa42cd4d974c99bb9c0d44f5bec000/docs/adr/0003-split-marketplace-repo.md#L10-L27)

````
## 背景

info-hive では、今後 Claude Code のプラグインを複数作る。これまでは 1 つのリポジトリ `to884/info-hive` に、プラグイン `wiki` の本体（`.claude-plugin/plugin.json`）と、マーケットプレイス `info-hive` の定義（`.claude-plugin/marketplace.json`、プラグインの source は `"./"`）が同居していた。この形では、別のリポジトリで作るプラグインをマーケットプレイスに載せにくい。

## 決定

| 項目 | 決定 |
| --- | --- |
| マーケットプレイス | 専用のリポジトリ `to884/info-hive-marketplace` に置く。中身は `.claude-plugin/marketplace.json`、README、LICENSE だけにする |
| プラグインのリポジトリ | プラグインごとに `to884/info-hive-<名前>` を作る。`wiki` は、旧 `to884/info-hive` を新しいリポジトリ `to884/info-hive-wiki` に履歴ごと移し、旧リポジトリはアーカイブする |
| マーケットプレイス名 | `info-hive` のまま残す。導入の指定は `wiki@info-hive` のままである |
| プラグインの source | `{"source": "github", "repo": "to884/info-hive-<名前>"}` と書き、`ref` は書かない。既定のブランチ（main）を配る |
| バージョン | プラグインの `plugin.json` の `version` だけに書く。マーケットプレイスの項目には書かない |
| 開発での置き場所 | どちらのリポジトリも、`info-hive-dev` のサブモジュールにする（`info-hive-wiki/`、`info-hive-marketplace/`） |

## 理由

- マーケットプレイスを分けると、プラグインを足すときに、マーケットプレイスの定義に項目を 1 つ足すだけで済む。各プラグインのリポジトリは、自分の `plugin.json` だけを持てばよい。
````

- [info-hive-dev/docs/adr/0031-wiki-codex-plugin.md 14 行目から](https://github.com/to884/info-hive-dev/blob/23abeb19e1fa42cd4d974c99bb9c0d44f5bec000/docs/adr/0031-wiki-codex-plugin.md#L14-L20)

````
## 決定

- wiki の配布物に `.codex-plugin/plugin.json` を追加する。既存の `skills/info-hive/` と MCP サーバーを共用し、Claude Code の定義を残す。Codex CLI 0.166.0 の互換形式の MCP 定義は `${CLAUDE_PLUGIN_ROOT}` を展開しないため、Codex の定義では `cwd: "."`（プラグインのルートに解決される）と相対パスの引数を使う。初回の環境の準備に備えて接続の待ちを 600 秒とする。
- Codex 向けのカタログは、マーケットプレイスのリポジトリの `.agents/plugins/marketplace.json` に置く。配布先は `source: "url"` と `url: "https://github.com/to884/info-hive-wiki.git"` で指定する。Codex CLI 0.166.0 は Claude Code 用の `source: "github"` を認識せず、項目を一覧から除く。対象は wiki のみとし、rag の Codex 対応は宣言しない。項目に `version` は書かない。
- Codex では `$wiki:info-hive <操作> <引数>` を入口にする。11 本の操作手順の正本は既存の `commands/*.md` のままとし、読み取り専用の `wiki_codex.py` がパス、呼び出し名、ホスト固有の前提を補って表示する。利用者の引数は受け取らず、シェルも起動しない。
- Web の raw は Codex 自身が既存の W1〜W8 を実行する。Claude の CLI や Sonnet のエージェントを起動しない。ページの編集には Codex の差分編集を使う。
- `session` による実行中の会話の自動取得は Claude Code の機能として残す。Codex の会話履歴を Claude の形式として読ませない。明示した Claude Code の記録は従来の処理で取り込める。
````
