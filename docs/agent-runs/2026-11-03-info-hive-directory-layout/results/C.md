画像の配置には決定の食い違いがあります。作者の最新指示は `RAW_ROOT/assets/`、ADR-0005 は生成した SVG を `wiki/assets/` に置く方針です。本案では最新指示を優先し、元画像と生成 SVG を `RAW_ROOT/assets/` 内で分け、生成 SVG は版を追加して既存ファイルを上書きしない扱いを提案します。## 結論

**作者の番号付き構成を採用し、①作業領域を明示する設定、②各ディレクトリの書き手、③移動させないファイルの規則を加える案を推奨する。** 番号やフォルダー名をプラグインの識別条件にしないことが、改名やプラグイン追加に耐えるための要点である。

以下は利用者の作業領域の設計案であり、`info-hive-dev` 自体の再構成ではない。設定ファイルと `log` のコマンドは、特記したものを除いて新規の提案である。

### 1. グローバルの構成

```text
~/info-hive/                           ← info-hive 作業領域・Foam のルート
├── .info-hive/
│   └── workspace.json               ← 保存場所と作業領域の識別情報
├── .foam/
│   └── templates/
│       ├── daily-note.md            ← Foam と log が共用する正本
│       └── weekly-note.md           ← 週次レビューを実装するときに追加
├── .vscode/
│   └── settings.json
├── .github/
│   └── instructions/                ← 対応するツール向けの指示。任意
├── AGENTS.md
├── CLAUDE.md
├── .gitignore
├── .gitattributes
├── 00_Inbox/
│   └── 20261103-091200-調査したいこと.md
├── 10_Assets/
│   └── 2026/
│       └── 日報用スクリーンショット-01.png
├── 20_Daily/
│   └── 2026/
│       └── 11/
│           └── 2026-11-03.md
├── 30_Weekly/
│   └── 2026/
│       └── 2026-W45.md
├── 40_Projects/
│   └── atlas/
│       └── project.md               ← プロジェクトへの案内。コードを置かない
├── 50_Knowledge/
│   └── notes/
│       └── 20261103-120000-文字コードの扱い.md
├── 60_Output/
│   └── atlas/
│       └── 調査報告-2026-11-03.md
├── 90_Wiki/
│   ├── SCHEMA.md
│   ├── index.md
│   ├── log.md                       ← wiki の操作ログ。日々の記録とは別
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   ├── synthesis/
│   ├── indexes/                     ← 目録を分割したときに追加
│   ├── graph/
│   ├── .wiki-cache/
│   └── .evolution/
├── 91_Raw/
│   ├── 文字コードの扱い-20261103.md   ← 取り込んだ時点の資料
│   └── assets/
│       ├── sources/
│       │   └── 資料のスラッグ/
│       │       └── image-01.png      ← 取り込み元の画像
│       └── figures/
│           └── ページのスラッグ-01-v001.svg
└── A0_Archive/
    └── 2026/
        └── 60_Output/
```

このツリーは配置先の全体像を示す。空のディレクトリを最初からすべて作る必要はない。週次レビューなど、未実装の機能の置き場は予約にとどめる。

### 2. プロジェクトの構成

作者の「プロジェクトルートの下に、プロジェクト名の info-hive ディレクトリを置く」は、**外側のプロジェクト用リポジトリに、知識の作業領域とコードのサブモジュールを並べる**意味と解釈した。

```text
<project-root>/                       ← 例: ~/projects/atlas-workspace/
├── .git/
├── .gitmodules
├── .info-hive/
│   └── project.json                 ← {"workspace": "atlas"} という案内だけ
├── .github/
│   └── instructions/                ← 外側の Git リポジトリ用
├── AGENTS.md                        ← atlas/ の設定へ案内する
├── CLAUDE.md
├── .gitignore
├── .gitattributes
├── atlas/                           ← プロジェクト名。info-hive・Foam のルート
│   ├── .info-hive/
│   │   └── workspace.json
│   ├── .foam/
│   │   └── templates/
│   │       └── daily-note.md
│   ├── .vscode/
│   │   └── settings.json
│   ├── 00_Inbox/
│   ├── 10_Assets/
│   ├── 20_Daily/
│   │   └── 2026/
│   │       └── 11/
│   │           └── 2026-11-03.md
│   ├── 30_Weekly/
│   │   └── 2026/
│   │       └── 2026-W45.md
│   ├── 40_Projects/
│   │   └── 認証機能/
│   │       └── project.md
│   ├── 50_Knowledge/
│   │   └── notes/
│   ├── 60_Output/
│   ├── 70_ADR/                       ← このプロジェクトの設計判断
│   │   └── 0001-認証方式の選定.md
│   ├── 90_Wiki/
│   │   ├── SCHEMA.md
│   │   ├── index.md
│   │   ├── log.md
│   │   ├── sources/
│   │   ├── entities/
│   │   ├── concepts/
│   │   ├── synthesis/
│   │   └── graph/
│   ├── 91_Raw/
│   │   └── assets/
│   │       ├── sources/
│   │       └── figures/
│   └── A0_Archive/
├── app/                             ← 開発対象のコード。Git サブモジュール
└── service/                         ← 別のコードがある場合のサブモジュール
```

`70_ADR` は仮の番号であり、設定で別の番号に変更できる。`00_Inbox/ADR` は作らない。

`.github/instructions` は外側のリポジトリに置いた。内側の `atlas/.github/` に置くだけで、外側やコードのサブモジュールに指示が適用されるとは扱わない。各サブモジュール固有の開発指示は、そのリポジトリの規則を尊重する。

外側のリポジトリは `atlas/` の文書とコードの参照コミットを管理し、コードそのものの履歴は各サブモジュールが管理する。

### 3. 役割、書き手、命名

`/log:*` の名前・機能は、ADR-0006 と方法論レポートを踏まえた提案であり、実装済みのコマンドではない。特に `memo`、`note`、`issue` は仮称である。[R2、R8]

| 場所 | 役割・書き手 | 命名・運用 |
|---|---|---|
| `.info-hive/` | 人と初期化コマンドが保存場所を登録する。通常の記録コマンドは読むだけ | `workspace.json` を正本にする。プラグインが他プラグインの設定を消さない |
| `.foam/templates/` | 人が編集し、初期化コマンドが未存在時だけひな型を作る | `daily-note.md` は固定。既存ファイルを上書きしない |
| `.vscode/` | 人が Foam、検索・表示の範囲を設定する | `settings.json`。複数ルートでは `.code-workspace` 側の設定を使う |
| `.github/instructions/`、`AGENTS.md`、`CLAUDE.md` | 人が各ツール向けに運用規則を書く | 対応ツールが読む位置に置く。保存パスの正本を別々に持たせない |
| `00_Inbox/` | 人が分類前の独立したメモや受領資料を置く | `YYYYMMDD-HHMMSS-件名.md`。同時刻の重複には連番を付ける。`log` の通常入力先にはしない |
| `10_Assets/` | 人が日記、編集用ノート、成果物に使う添付を置く | 年などで分割可能。Wiki 用画像は置かない |
| `20_Daily/` | 人、Foam、`/log:memo`、`start`、`stop`、`todo`、`issue`、`plan`、`close`、`tidy` | `YYYY/MM/YYYY-MM-DD.md`。一つの作業領域で一日一ファイル |
| `30_Weekly/` | 人、将来の `/log:review --week` | `ISO週年/ISO週年-Www.md`。暦年と ISO 週年を混ぜない |
| `40_Projects/` | 人がプロジェクトや活動の目的、進捗、関連文書への案内を書く | 安定した識別名の下に `project.md`。グローバルでは外部プロジェクトへの案内、プロジェクト内では機能・活動単位の整理に使う |
| `50_Knowledge/notes/` | `/log:note` が抽出したノウハウの下書きを作り、人が編集する | `YYYYMMDD-HHMMSS-件名.md`。題名は frontmatter の `title` で変更できる。Wiki のページを複製して管理しない |
| `60_Output/` | 人、または人が依頼した成果物作成の操作 | `<project-id>/件名-YYYY-MM-DD.ext`。`log` や `wiki` が無条件に公開する場所ではない |
| `70_ADR/` | 人が判断し、依頼されたエージェントが記述する | `0001-件名.md`。欠番を許し、採番後に詰め直さない |
| `90_Wiki/` | `/wiki:init`、`/wiki:ingest`、保存を伴う `/wiki:query`。規約は人と改訂する | 内部の `sources/`、`concepts/`、`SCHEMA.md` などは現行名を維持。Wiki 全体でスラッグを一意にする |
| `91_Raw/` | 人が持ち込んだ資料と、`/wiki:ingest` が保存する取り込み時点の資料 | 同じパスの既存資料を上書きしない。更新された編集用ノートは別の版として取り込む |
| `91_Raw/assets/sources/` | 取り込み時に取得・保存した画像 | `<source-slug>/image-NN.ext`。出典と対応させ、保存済み画像を改変しない |
| `91_Raw/assets/figures/` | Wiki を書く操作が生成した SVG | `<page-slug>-NN-v001.svg`。改訂時は新しい版を追加し、参照を更新する |
| `A0_Archive/` | 人が終了済みの補助文書・成果物を退避する | `年/元の分類/...`。日付ノート、Wiki、raw を年末に自動移動しない |

入力のたびに分類させないため、日々の短い入力は日付ノートの `## メモ` に集める。`00_Inbox` は、日付ノートとは独立したファイルを置きたいときの受け皿とする。

日付ノートの中身は ADR-0006 を維持する。作業メモとタスクを分け、タスクに三つの繰り越し用小節を設け、`問題・突発事項` を残す。ディレクトリの整理を理由に、この形式まで変更しない。[R2、L31–79]

### 4. 作業領域と保存場所の見つけ方

**ディレクトリを探して役割を推測する方式をやめ、明示された作業領域から設定を読む。**

設定の例は次のとおりである。これは新規仕様の提案であり、現在の wiki スクリプトがこの JSON を読むわけではない。

```json
{
  "schema_version": 1,
  "workspace_id": "atlas",
  "scope": "project",
  "paths": {
    "inbox": "00_Inbox",
    "assets": "10_Assets",
    "daily": "20_Daily",
    "weekly": "30_Weekly",
    "projects": "40_Projects",
    "notes": "50_Knowledge/notes",
    "output": "60_Output",
    "adr": "70_ADR",
    "wiki": "90_Wiki",
    "raw": "91_Raw",
    "archive": "A0_Archive"
  },
  "plugins": {
    "log": {
      "timezone": "Asia/Tokyo"
    }
  }
}
```

配置には次の規則を付ける。

- パスは `.info-hive/` の親、すなわち作業領域ルートを基準とする相対パスに統一する。
- Wiki 用画像のルートは `raw/assets/` として導出する。独立した画像パス設定を重ねない。
- 番号付きの主要ディレクトリは、二文字の半角英数字と `_` で始める。内部の `notes/`、`sources/` など、ツールが扱う固定名には番号を付けない。
- 新規構成では `wiki`、`daily`、`notes`、`raw` の相互包含を禁止する。誤って日付ノートを Wiki の走査範囲に含めないためである。
- 未知の設定項目は保存時に維持する。プラグイン追加で既存設定を失わせない。
- パスの存在や包含関係は、解決後の実パスで検査する。設定が壊れていたら書き込みを止める。

**`log` の選択規則は、作者の「既定はグローバル」を守る。**

1. 明示的な `--workspace <path>` があれば、その作業領域を使う。
2. `--project` があれば、現在位置から祖先をたどり、作業領域設定または外側の `.info-hive/project.json` を読む。
3. どちらもなければ、登録されたグローバル作業領域、未登録なら `~/info-hive/` を使う。

したがって、コードのサブモジュール内で起動しても、無指定の `log` はグローバルへ記録する。プロジェクト用の記録は明示的に選ぶ。`--project` で指定先が見つからない場合は、グローバルへ切り替えて書き込まない。

外側の `project.json` は `{"workspace": "atlas"}` という案内だけにする。各保存場所は内側の `workspace.json` だけに記録する。祖先の探索を最初の `.git` で打ち切ると、コードのサブモジュールから案内を見つけられないため、Git リポジトリの境界と作業領域の境界を分ける。

**wiki は当面、現行の探索順を維持する。** 現在の順序は「明示パス → 近いプロジェクトの指示 → グローバル指示 → プロジェクトの `wiki/`」である。[R4、L21–23]

初期段階では、プロジェクト指示に設定ファイルへの案内と解決済みの `WIKI_ROOT`・`RAW_ROOT` を記し、付属スクリプトには絶対パスを渡す。例えば以下の引数で既存の初期化処理を利用できる。

```text
python <plugin-root>/skills/info-hive/scripts/init_wiki.py <workspace-root> --wiki-dir 90_Wiki --raw-dir 91_Raw
```

これは引数指定の例であり、今回実行したものではない。既存コードは基準ディレクトリに `--wiki-dir` と `--raw-dir` を結合するので、外側の名前を変えるために内部構造を書き換える必要はない。[R6、L170–200、L260–268]

### 5. Foam との接続

日付ノートの配置パターンは `.foam/templates/daily-note.md` に持たせる。

```yaml
---
type: daily
title: "$FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE"
date: $FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE
tags: []
created: $FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE
updated: $FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE
foam_template:
  name: 日付ノート
  filepath: "/20_Daily/$FOAM_DATE_YEAR/$FOAM_DATE_MONTH/$FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE.md"
---
```

本文には ADR-0006 の日本語見出しを置く。`log` はこのテンプレートを読み、対象日の変数を置換し、`foam_template` を除いて生成する。単純な静的 Markdown と三つの日付変数から始めれば、Foam の全テンプレート機能を再実装せずに済む。対応外の変数を見つけた場合は、未展開のまま保存しない。

Foam のテンプレート文書は、日付変数を使った年・月別配置を明示的に扱っている。また `daily-note.js` が `daily-note.md` より優先されるため、既存の JavaScript テンプレートがある場合も初期化時に検出する必要がある。[Foam: Note Templates](https://github.com/foambubble/foam/blob/main/docs/user/features/templates.md)

通常運用では、`~/info-hive/` または `<project-root>/atlas/` を単独の Foam ワークスペースとして開くことを推奨する。コードは別ウィンドウで開ける。

複数ルートを使う場合は、対象の知識領域を先頭にし、テンプレートの `filepath` に作業領域のフォルダー名を含めて保存先を固定する。グローバルとプロジェクトの両方に `daily-note.md` を置いても、アクティブファイルに応じて自動選択されるとは扱わない。Foam はフォルダー順で特別なテンプレートを選ぶ。[Foam: Multi-root workspaces](https://github.com/foambubble/foam/blob/main/docs/user/recipes/multi-root-workspaces.md)

## 根拠

### 1. 分けるべき境界は、分類名より編集と検査の規則で決まる

現行 wiki は、raw を変更不可の資料、wiki を LLM が整理するページ群、`SCHEMA.md` を個別の規約として定義している。[R4、L31–37]

一方、日付ノートは何度も追記し、`notes/` は人が編集する場所である。したがって、同じ「知識」に関するファイルでも、次の四段階を分けるのが妥当である。

```text
日付ノート
  → 編集用ノート
  → ユーザーが取り込みを選択
  → raw に取り込み時点の資料を保存し、Wiki を生成
```

これは日付ノートから Wiki へ直接昇格させない ADR-0006 と整合する。[R2、L37–40、L91、L113–114]

編集用ノートを取り込むときは、元のノートを残し、raw に写した時点の内容を出典にする。現在の `/wiki:ingest` にも、raw にないソースを raw に置く手順がある。ただし「移動かコピーか」「同名の資料をどう更新するか」は明文化したほうがよい。[R9、L12–19]

### 2. Wiki の外側を番号付きにするのは、現行コードで実現できる

`init_wiki.py` は `project_root / wiki_dir` と `project_root / raw_dir` を使い、作成する内部ディレクトリは `sources`、`entities`、`concepts`、`synthesis`、`graph` である。[R6、L43、L170–200]

したがって、`90_Wiki` と `91_Raw` を使いつつ、内部の固定名を維持できる。wiki のスキル自体も、掲載した構成は既定値であり、別のディレクトリ名を使用できると記している。[R4、L84]

ただし、**番号を付ければ自動的に見つけてもらえるわけではない。** 現行の探索は指示ファイルとパス指定に依存するため、保存先の登録が必要である。

### 3. 日付ノートを Wiki の下に置くと、現在の検査と衝突する

`wiki_lint.py` は渡されたルート以下の Markdown を再帰的に収集し、除外は固定のファイル名・ディレクトリ名で判定する。[R7、L107–108、L155–162]

さらに、収集したページから被リンクを集計し、被リンクがなければ孤立として報告する。[R7、L258–281]

このため、日付ノートを `90_Wiki/20_Daily/` に置いたり、lint に作業領域全体を渡したりする構成は採らない。Wiki の外の日付ノートからリンクしても、現在の lint では Wiki ページの孤立を解消する根拠にならない。Wiki 内で必要な相互参照を維持する必要がある。

### 4. 想定する「破綻」と対処

以下の対処は設計上の提案であり、実装・実測済みの保証ではない。

| 想定する破綻 | 本案での対処・残る制約 |
|---|---|
| `20_Daily` などを改名するとプラグインが別の場所へ書く | 役割は設定のキーで特定する。改名時は実体、設定、テンプレート、リンクをまとめて更新する。旧名・新名の二か所へ同時に書かない |
| プロジェクト名が変わる | `workspace_id` は維持する。表示名だけの変更でフォルダーを動かす必要はない。`atlas/` 自体を改名する場合は外側の案内も更新する |
| 年末年始・閏日で保存先や繰り越しが壊れる | 日付を解析して年・月を導出する。繰り越し元は年を固定せず探索する。週次は ISO 週年を使う |
| 休日を挟んで「前日」のファイルがない | 直前に存在する日付ノートから繰り越す案を推奨する。暦上の前日との違いは仕様に明記する |
| ファイル数が増える | 日付ノートは月ごとに分かれ、一か月の直下は最大31ファイル。10年間でも日付ノート数の上限は `10 × 366 = 3,660`。ただし検索性能は未測定であり、月分割だけで全文走査が速くなるとは主張しない |
| 新しいプラグインが増える | `70`、`80` などを必要に応じて割り当て、役割を設定に登録する。既存の番号を詰め直さず、プラグイン名をフォルダー名の必須条件にしない |
| `50_Knowledge` と Wiki が二重管理になる | 前者は人が編集するノート、後者は出典に基づく統合結果。内容の双方向同期をしない |
| Wiki と原資料の同名ファイルが Foam で混ざる | Wiki 内リンクは `[[concepts/名前]]` などで区別し、raw の Markdown は必要に応じて Foam の索引から除外する。Wiki 外への参照には通常の相対 Markdown リンクを使う |
| コードのサブモジュール内から起動すると保存先を誤る | 外側の案内を祖先探索で見つける。`git rev-parse --show-toplevel` だけで作業領域を決めない |
| 年末の整理でリンクが壊れる | 日付ノート、Wiki、raw は元の場所に残す。アーカイブは表示・検索の絞り込みを優先し、物理移動はリンクを確認できる補助文書に限る |
| プラグイン更新でテンプレートやノートが消える | 初期化は既存ファイルを上書きしない。設定の版とプラグインの版を分け、移行は別の操作にする |
| 複数セッションから同じ日付ノートへ書く | 作業領域単位の排他、変更検出、再読込を実装する。Git の未解決競合には追記しない。ディレクトリ構成だけで同時編集問題は解消しない |

Foam の現行仕様では、曖昧な同名リンクは警告対象であり、識別子にディレクトリを足して区別できる。Wiki 内の `[[concepts/名前]]` は、現行 lint の Wiki 相対パスとも合わせられる。[Foam: Wikilinks](https://github.com/foambubble/foam/blob/main/docs/user/features/wikilinks.md)

Foam の除外には現行の `foam.files.exclude` を使う。`foam.files.ignore` は非推奨である。例えば raw の Markdown や再生成可能な領域を対象にするが、設定の配列を置き換える際は既定の除外も維持する。`.gitignore`、VS Code の表示除外、Foam の索引除外は別々に扱う。[Foam の設定定義](https://github.com/foambubble/foam/blob/main/packages/foam-vscode/package.json#L742)

### 5. Windows・macOS・Linux で共有するための条件

- ディレクトリやファイルの照合で、大文字・小文字だけの違いを作らない。
- 日本語ファイル名は NFC を基準にし、正規化後の重複を検出する。現行 wiki lint にも NFC の重複検出がある。[R7、L243–256]
- 日付と時間のファイル名には `:` を使わない。タイムスタンプは `YYYYMMDD-HHMMSS` とする。
- 保存する相対パスは `/` 区切りに統一し、コードではパス API で結合する。`~` はホームディレクトリとして明示的に展開する。
- 文字コードは UTF-8 を指定し、Markdown などのテキストは `.gitattributes` で改行方針を揃える。これは既存の運用方針とも一致する。[R1、L36–39]
- シンボリックリンクやジャンクションを必須にしない。移動可能な相対パスを基本とする。
- 深い分類を増やす前に索引・タグを使う。長いパスの限界は環境依存なので、共通の絶対上限値を本案では保証しない。

### 6. 決定・ADR・現行実装との食い違い

| 論点 | 現状との差と扱い |
|---|---|
| `~/daily/` から `~/info-hive/20_Daily/` へ | ADR-0006 は保存先を固定仕様にしないと決めている。最新の作者案を新規作業領域の既定値とし、既存の保存先は移行するまで維持する。[R2、L37] |
| `<保存先>/notes/` から `50_Knowledge/notes/` へ | `notes/` を人が編集する境界は維持するが、物理的な親を変更する提案である。ADR-0006 に論理的な `NOTES_ROOT` として追記する必要がある。[R2、L39] |
| Wiki 用画像の配置 | 最新の作者指示を広く解釈し、生成 SVG も `91_Raw/assets/figures/` に置いた。ADR-0005 の `wiki/assets/` と明確に異なるため、ADR の改訂が必要。[R3、L26–30] |
| raw の意味 | 原資料に加えて生成図も入る。原資料と生成図の区画を分け、生成図も保存後は上書きせず版を追加する。生成図を原資料として自動取り込みしない |
| SVG のリンク | ADR-0005 の `assets/...` 固定では参照できない。例えば `90_Wiki/concepts/ページ.md` からは `../../91_Raw/assets/figures/図.svg` のように、ページからの相対パスを生成する |
| 図の実装状況 | ADR-0005 自体が `wiki/assets/` 作成、画像参照検証、サイズ判定の変更を将来の実装として挙げている。現行 `init_wiki.py` がすでにその構成を作るとは扱わない。[R3、L59、R6、L43、L199–220] |
| 「wiki のコードは変えない」 | 初期段階は明示パスと既存引数で維持できる。共通設定の自動読込や図の検査を wiki に追加するなら、`log` の導入と別の変更として判断する。[R2、L29] |
| `.foam/templates` の位置 | プロジェクト全体のルートではなく、内側の info-hive 領域を Foam のルートにする。ADR-0006 の配置説明を新しい階層に合わせて更新する。[R2、L112] |
| 固定名の変更 | 番号を付ける対象は外側の分類ディレクトリに限る。`SCHEMA.md`、`graph/`、ページ種別のディレクトリなど、機械が扱う既存名は維持する。[R10、L461–498] |

ADR-0003 が定めるプラグイン本体・マーケットプレイスのリポジトリ分離は、この利用者領域の配置では変更しない。[R5、L18–23]

## 検討した代替案

| 案 | 採らなかった理由 |
|---|---|
| 日付ノートや編集用ノートを `90_Wiki/` 内に置く | 現行 lint の孤立判定、検索、ページの規律が日々の記録と合わない。ADR-0006 にも反する |
| `20_Daily/notes/` にする | ADR-0006 の記述には近いが、日付による保管と主題による編集が混在する。作者案の `50_Knowledge` とも役割が重なる |
| `50_Knowledge` を Wiki の別名にする | 人が編集するノートと LLM が統合するページの境界が消え、二つの正本ができる |
| 二桁の番号を機械的な役割 ID にする | 並べ替えや改名のたびにコードへ影響する。番号は表示順、役割は設定キーに分けるほうが変更範囲を限定できる |
| `40_Projects/` にすべてのコードと入れ子の info-hive を置く | 親子の作業領域の選択、Foam の走査範囲、Git の管理境界が複雑になる。作者が決めた外側のプロジェクトルートを使う |
| 直近の Git ルートを保存先にする | サブモジュール内ではコードのリポジトリを返し、兄弟の知識領域を見つけられない |
| グローバル・プロジェクトを常に一つの Foam ウィンドウに混ぜる | 日付ファイル名と特別なテンプレートが重なる。必要時の明示的な複数ルート利用にとどめる |
| 毎年の日付ノートを `A0_Archive` に移す | 既存リンクと保存パターンが変わる。Foam の「直前の日付ノート」も現在のテンプレートパターンに依存するため、単なる年末整理で参照を失うおそれがある。[Foam: Daily Notes](https://github.com/foambubble/foam/blob/main/docs/user/features/daily-notes.md) |
| 生成 SVG だけ `90_Wiki/assets/` に残す | ADR-0005 との整合性は高い。ただし、本案では作者の最新の「Wiki 用画像は RAW_ROOT 下の assets」という指示を優先した。取り込み画像だけを指した発言なら、この代替案のほうが変更は小さい |

## 前提と不確実性

**本案で置いた前提**

- 一つの作業領域の日付ノートは、基本的に一人が記録する。同じ日付に複数人が独立した日誌を持つ構成は対象外とした。
- `50_Knowledge` は人が編集する知識ノート、`90_Wiki` は統合済み知識、と役割を分けられる。
- プロジェクトのコードは、info-hive 領域の兄弟のサブモジュールに置くという解釈を採った。
- 最新の「Wiki 用画像」を生成 SVG も含む指示と解釈した。これは推論である。
- `workspace.json`、外側の案内ファイル、パス検証・移行処理は、新たに実装する契約である。

**作者の判断が必要な事項**

1. **Wiki 用画像の範囲。** 全画像を `RAW_ROOT/assets` に置くのか、取り込み画像だけを指し、生成 SVG は ADR-0005 の場所に残すのか。本案は前者を採った。
2. **編集用ノートの位置。** `50_Knowledge/notes/` を正式に採るか。採る場合は ADR-0006 の保存場所の説明を更新する。
3. **プロジェクト用の記録の選択方法。** 本案は無指定なら常にグローバルを守った。プロジェクトごとに既定を切り替えたい場合は、明示的な設定として追加する。
4. **記録日と繰り越しの規則。** タイムゾーン、日をまたぐ作業の所属日、休日を挟んだ「前日」の意味。本案では開始日のファイルを保持して終了を書き込み、繰り越し元は直前の既存ノートとすることを推奨する。
5. **共有範囲。** プロジェクトの日誌を外側の Git リポジトリに含めるか、個人用として除外するか。複数人用なら、利用者別の作業領域を設ける判断が先に必要になる。
6. **既存領域の移行方針。** 新規作成だけ番号付きにするのか、既存の `~/wiki/`、`~/daily/` も移すのか。本案は既存領域を自動移動せず、個別に移行する案である。

**確認できていないこと**

Foam は公式リポジトリの現行文書を確認したが、利用者に導入される拡張の版は不明である。テンプレートメタデータの除去、二経路から同じ日付を開いた場合の再利用、Windows のパス処理、複数ルートでの保存先は、対象の版で確認する必要がある。`log` のテンプレート処理も未実装である。

採用前の確認は、Foam と `log` から同じ日を作って一ファイルになること、年末年始・閏日・日跨ぎ、サブモジュールからの保存先選択、フォルダー改名後のリンク、同時追記、既存テンプレートの保持を中心に行うのがよい。

今回、リポジトリの変更、ビルド、動作試験は行っていない。指定された他エージェントの成果配置先も参照していない。

## 参照

ローカルの行番号は、今回読んだ作業ツリーのもの。

- **R1:** [AGENTS.md](C:/Works/info-hive-dev/AGENTS.md:7) — L7–17：開発リポジトリとプラグイン追加手順。L30–39：名前、機械が読む文字列、UTF-8。
- **R2:** [docs/adr/0006-daily-journal-is-separate-plugin.md](C:/Works/info-hive-dev/docs/adr/0006-daily-journal-is-separate-plugin.md:25) — L25–42：承認済みの決定。L44–79：日付ノート形式。L89–91：既定と編集用ノートの理由。L109–124：テンプレート、未決事項、見直す条件。
- **R3:** [docs/adr/0005-wiki-figures-use-mermaid-and-svg.md](C:/Works/info-hive-dev/docs/adr/0005-wiki-figures-use-mermaid-and-svg.md:22) — L22–34：図・画像の配置。L56–60：今後の実装。
- **R4:** [info-hive-wiki/skills/info-hive/SKILL.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md:21) — L21–23：探索順。L31–43：層と操作。L55–84：保存範囲と任意の配置。L86–104：規模への対処。
- **R5:** [docs/adr/0003-split-marketplace-repo.md](C:/Works/info-hive-dev/docs/adr/0003-split-marketplace-repo.md:14) — L14–30：リポジトリ分離とバージョンの管理。
- **R6:** [info-hive-wiki/skills/info-hive/scripts/init_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:170) — L43：内部ディレクトリ。L89–99：既存ファイルを上書きしない処理。L170–220：配置の生成。L260–275：引数と UTF-8。
- **R7:** [info-hive-wiki/skills/info-hive/scripts/wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:107) — L81–104：リンク解決。L107–108、L155–183：走査・除外。L243–281：スラッグの重複、被リンクと孤立。
- **R8:** [docs/research/daily-journal-methodology-options.md](C:/Works/info-hive-dev/docs/research/daily-journal-methodology-options.md:278) — L278–350：形式と段階別コマンド。L380–410：作者の決定と未検証事項。[daily-journal-decision-matrix.md](C:/Works/info-hive-dev/docs/research/daily-journal-decision-matrix.md:190) — L190–205：配置案の比較。L289–319：推奨、改訂注記、限界。採点は本案で再計算していない。
- **R9:** [info-hive-wiki/commands/ingest.md](C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:12) — L12–20：ルートの特定、raw 保存、Wiki の更新。[commands/init.md](C:/Works/info-hive-dev/info-hive-wiki/commands/init.md:10) — L10–15：現在の既定値と初期化。[references/ingest-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:9) — 手順1、5〜9。[references/page-conventions.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md:47) — wikilink と命名の規約。
- **R10:** [docs/porting-plan.html](C:/Works/info-hive-dev/docs/porting-plan.html:461) — L461–498：固定名と方針B。L583以降：作業段階。[info-hive-wiki/UPSTREAM.md](C:/Works/info-hive-dev/info-hive-wiki/UPSTREAM.md:3) — L3–14：移植元と起点。
- **Foam 公式文書:** [Note Templates](https://github.com/foambubble/foam/blob/main/docs/user/features/templates.md) の「Special templates」「Metadata」「FOAM_DATE_* variables」、[Daily Notes](https://github.com/foambubble/foam/blob/main/docs/user/features/daily-notes.md) の「Linking to the Previous Daily Note」、[Multi-root workspaces](https://github.com/foambubble/foam/blob/main/docs/user/recipes/multi-root-workspaces.md)、[Wikilinks](https://github.com/foambubble/foam/blob/main/docs/user/features/wikilinks.md)、[設定定義](https://github.com/foambubble/foam/blob/main/packages/foam-vscode/package.json#L742)。2026年11月3日に確認。テンプレート文書の取得時 blob SHA は `1ee03055e1087465d696af08aa47d09cc52411f8`。

使用した MCP サーバー: GitHub（codex_apps）  
使用した Agent Skills: なし
