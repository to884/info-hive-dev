# プロジェクト運用ガイドライン

## 応答言語
- このリポジトリでエージェントがユーザーに返す応答は、すべて日本語で記述する。
- コード、コマンド、パス、識別子は原文のまま書く。

## リポジトリの役割
- このリポジトリ（`info-hive-dev`）は、`info-hive` を開発するためのリポジトリである。
- `info-hive` は独立した Git リポジトリとして、このリポジトリのサブモジュールとして配置する。
- `info-hive` のコンセプト、設計書、テストは、このリポジトリ（'info-hive-dev`）に置く。
- `info-hive` には、開発に関わるファイルを置かない。

## リポジトリ構成
- エージェントスキルは `.agents/skills/` と `.claude/skills/` で管理する。
- `skills-lock.json` には、各スキルの取得元、パス、算出済みハッシュを記録する。
- `docs/porting-plan.html` は、`info-hive` の移植計画（方針と段階）である。
- `docs/adr/` には設計の決定を、`docs/research/` には調査レポートを、`docs/agent-runs/` には複数のエージェントに依頼した作業の記録を置く。
- `docs/upstream/translation-hashes.txt` には、移植元から取り込んだときの日本語訳のファイルの SHA-256 を記録している。

## info-hive の開発

`info-hive` は、Claude Code プラグイン llm-wiki（praneybehl/llm-wiki-plugin v4.0.1）を日本語に特化して移植したものである。`info-hive` で作業する前に [docs/porting-plan.html](docs/porting-plan.html) の方針と段階を読み、それに従う。移植元との関係は [info-hive/UPSTREAM.md](info-hive/UPSTREAM.md) に記録する。

### 名前
- プラグイン名は `wiki`、マーケットプレイス名とスキル名は `info-hive` である。コマンドは `/wiki:<名前>` の形で起動する。
- スキルの本体は `info-hive/skills/info-hive/` にある。コマンドからは `${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/...` で参照する。

### 日本語と機械が読む文字列
- 人とエージェントが読む文章（文書、コメント、出力メッセージ）は日本語で書く。
- frontmatter のキー、`type`・`kind` の値、グラフの述語名、`--json` の出力のキー、コマンドラインの引数名、`SCHEMA.md` のアップグレード検出用の見出しは英語のまま残す。frontmatter のキーと `type`・`kind` の値は日本語の別名でも読めるようにするが、スクリプトとテンプレートが書くときは英語を使う（計画の方針 B）。
- ファイルの読み書きと子プロセスとの入出力は UTF-8 を明示する。Windows の既定は cp932 である。

### 移植元の修正
- 移植元の修正を取り込んだら、[info-hive/UPSTREAM.md](info-hive/UPSTREAM.md) の表に 1 行追加する。
- info-hive の修正を移植元に送ることはしない。

### リリース
- この指示でいう「公開」は、Claude Code プラグイン、skills.sh ディレクトリのスキル、GitHub リリースの公開だけを指す。npm への公開は、ユーザーが明示的に求めない限り含めない。
- ユーザーに見えるプラグインやスキルの変更は、マージ前に SemVer のバージョンを決める。バージョンは `info-hive/.claude-plugin/plugin.json`、`info-hive/.claude-plugin/marketplace.json` の 2 か所、`info-hive/CHANGELOG.md` をまとめて更新する。スキルには独自のバージョンがなく、プラグインのバージョンを引き継ぐ。
- リリースのコミットが `info-hive` の `main` に入り、`vX.Y.Z` のタグが push され、GitHub リリースが作成され、マーケットプレイスからの導入を確かめるまでは、リリースの完了を報告しない。

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
