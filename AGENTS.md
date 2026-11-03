# プロジェクト運用ガイドライン

## 応答言語
- このリポジトリでエージェントがユーザーに返す応答は、すべて日本語で記述する。
- コード、コマンド、パス、識別子は原文のまま書く。

## リポジトリの役割
- このリポジトリ（`info-hive-dev`）は、info-hive の Claude Code プラグインを開発するためのリポジトリである。プラグインは複数作る。
- 次のリポジトリを、それぞれ独立した Git リポジトリとして、このリポジトリのサブモジュールに置く。
  - `info-hive-wiki`（`to884/info-hive-wiki`）: プラグイン `wiki` の本体
  - `info-hive-marketplace`（`to884/info-hive-marketplace`）: マーケットプレイス `info-hive` の定義。各プラグインは `<プラグイン名>@info-hive` の形で入れる。
- プラグインごとのコンセプト、設計書、テストは、このリポジトリ（`info-hive-dev`）に置く。
- サブモジュールのリポジトリには、開発に関わるファイルを置かない。
- プラグインを足すときは、次の順に進める。
  1. プラグイン用のリポジトリ `to884/info-hive-<名前>` を作り、このリポジトリのサブモジュールにする。
  2. `info-hive-marketplace/.claude-plugin/marketplace.json` の `plugins` に項目を足す。`source` は `{"source": "github", "repo": "to884/info-hive-<名前>"}` とし、`version` は書かない。
  3. この AGENTS.md に、そのプラグインの開発の節を足す。

## リポジトリ構成
- エージェントスキルは `.agents/skills/` と `.claude/skills/` で管理する。
- `skills-lock.json` には、各スキルの取得元、パス、算出済みハッシュを記録する。
- `docs/porting-plan.html` は、wiki プラグイン（`info-hive-wiki`）の移植計画（方針と段階）である。
- `docs/adr/` には設計の決定を、`docs/research/` には調査レポートを、`docs/plans/` には実装の計画を、`docs/agent-runs/` には複数のエージェントに依頼した作業の記録を置く。
- `docs/upstream/translation-hashes.txt` には、移植元から取り込んだときの日本語訳のファイルの SHA-256 を記録している。

## wiki プラグイン（info-hive-wiki）の開発

`info-hive-wiki` は、Claude Code プラグイン llm-wiki（praneybehl/llm-wiki-plugin v4.0.1）を日本語に特化して移植したものである。`info-hive-wiki` で作業する前に [docs/porting-plan.html](docs/porting-plan.html) の方針と段階を読み、それに従う。移植元との関係は [info-hive-wiki/UPSTREAM.md](info-hive-wiki/UPSTREAM.md) に記録する。

### 名前
- プラグイン名は `wiki`、スキル名は `info-hive` である。コマンドは `/wiki:<名前>` の形で起動する。
- マーケットプレイス名 `info-hive` の定義は、`info-hive-marketplace/.claude-plugin/marketplace.json` にある。`info-hive-wiki` にはマーケットプレイスの定義を置かない。
- スキルの本体は `info-hive-wiki/skills/info-hive/` にある。コマンドからは `${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/...` で参照する。
- 手元で試すときは、`claude --plugin-dir <info-hive-wiki の絶対パス>` で起動する。

### 日本語と機械が読む文字列
- 人とエージェントが読む文章（文書、コメント、出力メッセージ）は日本語で書く。
- frontmatter のキー、`type`・`kind` の値、グラフの述語名、`--json` の出力のキー、コマンドラインの引数名、`SCHEMA.md` のアップグレード検出用の見出しは英語のまま残す。frontmatter のキーと `type`・`kind` の値は日本語の別名でも読めるようにするが、スクリプトとテンプレートが書くときは英語を使う（計画の方針 B）。
- ファイルの読み書きと子プロセスとの入出力は UTF-8 を明示する。Windows の既定は cp932 である。

### 移植元の修正
- 移植元の修正を取り込んだら、[info-hive-wiki/UPSTREAM.md](info-hive-wiki/UPSTREAM.md) の表に 1 行追加する。
- info-hive の修正を移植元に送ることはしない。

### リリース
- この指示でいう「公開」は、Claude Code プラグイン、skills.sh ディレクトリのスキル、GitHub リリースの公開だけを指す。npm への公開は、ユーザーが明示的に求めない限り含めない。
- ユーザーに見えるプラグインやスキルの変更は、マージ前に SemVer のバージョンを決める。バージョンは `info-hive-wiki/.claude-plugin/plugin.json` と `info-hive-wiki/CHANGELOG.md` をまとめて更新する。マーケットプレイスの項目にはバージョンを書かないので、`info-hive-marketplace` は直さない。スキルには独自のバージョンがなく、プラグインのバージョンを引き継ぐ。
- マーケットプレイスは `info-hive-wiki` の main を配る。`plugin.json` の `version` を上げたコミットが main に入ると、利用者に更新が届く。
- リリースのコミットが `info-hive-wiki` の `main` に入り、`vX.Y.Z` のタグが push され、GitHub リリースが作成され、マーケットプレイスからの導入を確かめるまでは、リリースの完了を報告しない。

## 変更時のルール
- スキルを変更するときは対応する定義を確認し、`.agents/skills/` と `.claude/skills/` の内容を同期する。
- スキルの取得元、パス、または内容を変更した場合は、`skills-lock.json` のメタデータも実態に合わせて更新する。
- 変更範囲は依頼されたスキルに限定し、既存の構成とフロントマターを維持する。

## 調査レポートの配置
- `deep-research` などの調査系スキルを使ってレポートを作成したときは、`docs/research/` ディレクトリの配下に保存する。

## 使用した MCP サーバーと Agent Skills の報告

応答の最後に、その応答を作るために使った MCP サーバーと Agent Skills を書く。作者が、どの道具が結果に関わったかを確かめられるようにするためである。

- 使ったものだけを、名前で並べる
- どちらも使わなかったときは「なし」と書く
- 読み込んだだけで使わなかったものは含めない

```text
使用した MCP サーバー: なし
使用した Agent Skills: git-conventions、claude-api
```
