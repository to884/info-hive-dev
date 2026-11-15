# プロジェクト運用ガイドライン

## 応答言語
- このリポジトリでエージェントがユーザーに返す応答は、すべて日本語で記述する。
- コード、コマンド、パス、識別子は原文のまま書く。

## リポジトリの役割
- このリポジトリ（`info-hive-dev`）は、info-hive の Claude Code プラグインを開発するためのリポジトリである。プラグインは複数作る。
- 次のリポジトリを、それぞれ独立した Git リポジトリとして、このリポジトリのサブモジュールに置く。
  - `info-hive-wiki`（`to884/info-hive-wiki`）: プラグイン `wiki` の本体
  - `info-hive-rag`（`to884/info-hive-rag`）: プラグイン `rag` の本体
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

## 設計と実装のレビューについて

設計と実装が完了する度に、以下のタスクを実行する。

- Claude Code で実行している場合は、`ask-codex` スキルを用いて Sol による敵対的レビューを行う
- Codex で実行している場合は、`ask-claude` スキルを用いて Opus による敵対的レビューを行う

レビューの指摘に基づいて修正を行う際には、場当たり的な修正をしてはならない。
場合によっては構造的な変更を許可し、根本的に欠陥が修正する方法を考える。

## wiki プラグイン（info-hive-wiki）の開発

`info-hive-wiki` は、Claude Code プラグイン llm-wiki（praneybehl/llm-wiki-plugin v4.0.1）を日本語に特化して移植したものである。`info-hive-wiki` で作業する前に [docs/porting-plan.html](docs/porting-plan.html) の方針と段階を読み、それに従う。移植元との関係は [info-hive-wiki/UPSTREAM.md](info-hive-wiki/UPSTREAM.md) に記録する。

### 名前
- プラグイン名は `wiki`、スキル名は `info-hive` である。コマンドは `/wiki:<名前>` の形で起動する。
- マーケットプレイス名 `info-hive` の定義は、`info-hive-marketplace/.claude-plugin/marketplace.json` にある。`info-hive-wiki` にはマーケットプレイスの定義を置かない。
- スキルの本体は `info-hive-wiki/skills/info-hive/` にある。コマンドからは `${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/...` で参照する。
- 手元で試すときは、`claude --plugin-dir <info-hive-wiki の絶対パス>` で起動する。マーケットプレイスから `wiki@info-hive` を入れていても、`--plugin-dir` の側が優先され、その MCP のサーバーが使われる（Claude Code 2.1.316 で確かめた）。

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

### Browse UI constraints
The /wiki:browse page runs under a strict CSP (ADR-0010). Do not use inline style attributes or inline scripts. Use classes and token-based CSS.

## rag プラグイン（info-hive-rag）の開発

`info-hive-rag` は、プラグイン `wiki@info-hive` に依存し、RAG（検索拡張生成）を扱う Claude Code プラグインである。PDF の登録、抽出、OCR、埋め込み、索引化を永続ジョブとして処理し、MCP の次回接続時に未完了ジョブを再開する。

### 名前と配置
- プラグイン名は `rag`、導入名は `rag@info-hive` である。コマンドを追加するときは `/rag:<名前>` の形にする。
- プラグインの本体はサブモジュール `info-hive-rag/` に置く。コンセプト、設計書、テストは開発用のリポジトリ `info-hive-dev` に置く。
- マーケットプレイスの定義は `info-hive-marketplace/.claude-plugin/marketplace.json` に置く。`info-hive-rag` には置かない。
- 依存先は `info-hive-rag/.claude-plugin/plugin.json` の `dependencies` に `wiki@info-hive` として宣言する。`wiki` を導入し、有効にした状態で使う。
- 手元で試すときは、`claude --plugin-dir <info-hive-wiki の絶対パス> --plugin-dir <info-hive-rag の絶対パス>` で両プラグインを読み込む。マーケットプレイスから入れたものがあっても、`--plugin-dir` の側が優先される。
- wiki の PDF 取り込みから MCP の `register_pdf` を明示的に呼ぶ。`queued` は受付済みであり、索引化完了ではない。原本は移動・複製せず参照する。
- ジョブの台帳は `scripts/rag_jobs.py`、接続中だけ動く子ワーカーは `scripts/rag_worker.py` にある。テストは親リポジトリの `tests/rag/` に置く。

### 日本語とバージョン
- 人とエージェントが読む文章は日本語で書き、ファイルの読み書きと子プロセスとの入出力は UTF-8 を明示する。機械が読むキーや識別子は英語のままにする。
- バージョンは `info-hive-rag/.claude-plugin/plugin.json` で管理し、変更を `info-hive-rag/CHANGELOG.md` に記録する。マーケットプレイスの項目には `version` を書かない。

## 変更時のルール
- スキルを変更するときは対応する定義を確認し、`.agents/skills/` と `.claude/skills/` の内容を同期する。
- スキルの取得元、パス、または内容を変更した場合は、`skills-lock.json` のメタデータも実態に合わせて更新する。
- 変更範囲は依頼されたスキルに限定し、既存の構成とフロントマターを維持する。

## Git の PR をマージしたら

- GitHub で PR をマージしたら、リモートブランチを削除する。

## Release & merge workflow (wiki / rag plugins)
1. Before bumping a version, run `git fetch` and check the latest tag and version on origin/main. Other sessions often release in parallel. If the version is taken, renumber it.
2. Check whether the target PR is already merged (`gh pr view`) before pushing more commits to its branch. If it is merged, open a new PR.
3. Merge order: the plugin repo PR first, then the parent repo PR that updates the submodule ref.
4. After tagging and creating the GitHub release, verify that the marketplace installs the new version.
5. Update the CHANGELOG date and record the release in the project wiki.
6. Clean up: remove the worktree (cd out of it first) and delete local and remote branches.

## セッションの後始末

- セッションに行うべきタスクが無くなった場合は、worktree を削除し、git のブランチも削除する。


## 使用した MCP サーバーと Agent Skills の報告

応答の最後に、その応答を作るために使った MCP サーバーと Agent Skills を書く。作者が、どの道具が結果に関わったかを確かめられるようにするためである。

- 使ったものだけを、名前で並べる
- どちらも使わなかったときは「なし」と書く
- 読み込んだだけで使わなかったものは含めない

```text
使用した MCP サーバー: なし
使用した Agent Skills: git-conventions、claude-api
```

## LLM Wiki

このプロジェクトでは、Andrej Karpathy の「LLM Wiki」のパターン（https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f）に従い、LLM が管理する wiki を `wiki/` に置いている。

このプロジェクトで蓄積した知識をもとに答える質問では、先に `wiki/index.md`（インデックスを分割した wiki では、`wiki/indexes/` の該当するファイル）を読み、1行の要約から必要なページを探す。引用には `[[wikilinks]]` を使う。インデックスからよい候補が見つからなければ、`info-hive` スキルの `wiki_search.py` でローカルのハイブリッド検索をする。依存パッケージを使わない BM25 にするには `--no-embed` を付ける。

新しいソースを加えるときは、`info-hive` スキルの取り込みのワークフローに従う。`wiki/sources/`、`wiki/entities/`、`wiki/concepts/`、`wiki/synthesis/` のどこに置くかを決め、影響するページを洗い出し、ページを書き直さずに `str_replace` で必要な箇所だけを更新する。インデックスを更新し、`wiki/log.md` に1行の記録を追記する。

規模を保つための規律: ページは1つの話題に絞る（目安は空白を除いて 10,000 文字または 100 行、上限は 25,000 文字または 200 行）。約 150 ページか、インデックスが 300 行を超えたら、インデックスを分割する。どのページにも YAML の frontmatter を付け、相互参照にはすべて `[[wikilinks]]` を使う。

規約の全体は `wiki/SCHEMA.md` にある。この要約と食い違うときは、`wiki/SCHEMA.md` に従う。
