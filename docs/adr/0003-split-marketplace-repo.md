# ADR-0003：マーケットプレイスをプラグインと別のリポジトリに置く

| 項目 | 内容 |
| --- | --- |
| 状態 | 承認 |
| 決定日 | 2026年11月3日 |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | `docs/porting-plan.html`（方針 A の名前、P6）、`info-hive-wiki/CONTRIBUTING.md`（バージョンを書く場所） |

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
- Claude Code は、marketplace.json の `name` をマーケットプレイス名に使い、リポジトリ名は見ない。`info-hive` は予約名ではない。名前を残せば、導入の指定を変えずに済む。
- バージョンを両方に書くと、2 つのリポジトリで同じ値を管理することになる。別のリポジトリを指す項目では、`claude plugin validate` も食い違いを見つけられない。項目に `version` がなければ、Claude Code は `plugin.json` の `version` を使う。
- Claude Code は、`version` が変わったかどうかで更新を判定する。`ref` を書かずに main を配っても、`plugin.json` の `version` を上げるまでは、利用者に更新は届かない。リリースのたびにマーケットプレイスを直さなくてよい。
- 旧リポジトリは改名せず、新しいリポジトリに移してアーカイブする。これは決定者の判断である。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| 今のリポジトリにマーケットプレイスを残し、ほかのプラグインを github の source で載せる | `wiki` のリポジトリがマーケットプレイスを兼ね続け、`wiki` だけが特別な扱いになる |
| 1 つのリポジトリに、すべてのプラグインを置く | プラグインごとにリリースと CI を分けられない |
| マーケットプレイスの項目の `ref` を、リリースのタグに固定する | リリースのたびにマーケットプレイスを直す必要がある。`version` で更新を判定するので、固定しなくても未リリースの変更は届かない |
| マーケットプレイスの項目にも `version` を書く | 二重の管理になり、食い違いを validate で見つけられない |

## 影響

- 旧 `to884/info-hive` をマーケットプレイスとして追加していた利用者は、`/plugin marketplace remove info-hive` のあとに `/plugin marketplace add to884/info-hive-marketplace` と `/plugin install wiki@info-hive` を実行し直す必要がある。同じ名前のマーケットプレイスは、1 人の利用者に 1 つしか登録できない。
- `info-hive-wiki` にはマーケットプレイスがないので、ローカルの変更は `claude --plugin-dir <info-hive-wiki の絶対パス>` で試す。ローカルのマーケットプレイスから隣のフォルダーを相対パスで指す方法は使えない（source は `./` で始まる必要があり、`..` を含むと validate で失敗する）。
- どのリポジトリも非公開なので、利用者は GitHub の認証情報を用意する必要がある（`gh auth setup-git` か、パスフレーズを聞かれない SSH 鍵）。
- 移植計画の P6 で確かめる導入の手順は、`to884/info-hive-marketplace` を追加する形になる。

## 見直す条件

- プラグインのリリースの前の変更を、main に入れたまま配りたくない事情ができたとき（たとえば、`version` を上げずに main の中身を大きく変えることが増えたとき）。そのときは、`ref` をタグに固定する案を見直す。
- リポジトリを公開するとき。認証についての案内を見直す。

## 参照

- Claude Code の文書: https://code.claude.com/docs/en/plugins/marketplace-reference.md 、https://code.claude.com/docs/en/plugins/manifest-reference.md 、https://code.claude.com/docs/en/plugins/host-marketplace.md 、https://code.claude.com/docs/en/plugins/cli-reference.md
- `info-hive-marketplace/README.md`：導入の手順と、プラグインを足すときの手順
- `info-hive-wiki/CONTRIBUTING.md`：バージョンを書く場所とリリースの手順
