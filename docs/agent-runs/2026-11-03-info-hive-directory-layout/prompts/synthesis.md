あなたは総括の書き手です。
同じタスクに 4 体のエージェントが独立して取り組み、その後、各エージェントが自分以外の成果をレビューしました。
成果とレビューを読み、作者（このリポジトリの所有者）が判断できる総括を 1 本書いてください。
あなたの最終メッセージだけが `summary.md` として保存されます。
エージェントは記号で呼びます（エージェント A、エージェント B、エージェント C、エージェント D）。記号とモデルの対応は末尾に表として付けるので、本文ではモデル名で優劣を語らないでください。

## タスク

# タスク：破綻しないディレクトリ構成案を考える

## 作者の指示

> 破綻しないディレクトリ構成案を考えて

対象は、info-hive の Claude Code プラグイン（既存の `wiki` と、これから作る日々の記録のプラグイン `log`）が読み書きする、利用者の作業領域のディレクトリ構成である。このリポジトリ（`info-hive-dev`）自体の構成ではない。

## これまでに作者が決めたこと（作者の言葉のまま）

### 日々の記録の機能について

> 1. 保存先の既定をどれにするか。プロジェクト直下の daily/、グローバルの ~/daily/、両方を選べるようにする、の 3 つから選びます。私は両方を選べるようにし、既定をグローバルにする案にする
> 2. 時刻をどう書くか。09:12-10:40 を 1 行に持つ
> 3. 直接 Wiki に昇格せずに、 notes/ ディレクトリにノートを記述してノウハウなどをユーザーが編集できるようにする
> 4. フックによる自動記録を、保留にする
>
> * 作業メモとタスク（前日からの繰り越し、本日のタスク、次回への繰り返し）は別に記述できるようにする。これは作業メモは簡潔に記述し、詳細については、タスクで記述するため
> * daily のテンプレートは Foam のテンプレート置き場に配置する
> * その日に発生した問題や突発的なイベントについて記述する欄を追加する

「次回への繰り返し」は、のちに作者が「繰り越しで合っている」と確認した。

> info-hive-log にします

（リポジトリ名を `info-hive-log`、プラグイン名を `log` とする解釈で ADR-0006 に記録済み）

### ディレクトリ構成について

> 以下のようなディレクトリ構成にしたい。ディレクトリ名は仮だが、先頭に二桁の英数字とアンダースコアを付ける

```
~/info-hive/（またはプロジェクトルート）
├─.foam
│  └─templates
├─.github
│  └─instructions
├─00_Inbox
│  └─ADR
├─10_Assets
├─20_Daily
│  └─2026
│      └─04
├─30_Weekly
├─40_Projects
├─50_Knowledge
├─60_Output
├─90_Wiki
├─91_Raw
└─A0_Archive
```

> 1. `00_Inbox/ADR` は不要。プロジェクトごとの info-hive なら XX_ADR（XX は任意の数字）でルートのすぐ下に置く
> 2. `RAW_ROOT` の下の assets に Wiki 用の画像を置く。`XX_Assets` は Wiki 以外の用途で使用する
> 3. プロジェクトルートの下にプロジェクト名で作成した info-hive のディレクトリを置き、プロジェクトで開発するコード（info-hive 関連のコードではない）は、サブモジュールとして配置する

## 読むべき文書とコード

- `AGENTS.md`（リポジトリの役割、日本語と機械が読む文字列の方針、プラグインを足す手順）
- `docs/adr/0003-split-marketplace-repo.md`、`docs/adr/0005-wiki-figures-use-mermaid-and-svg.md`、`docs/adr/0006-daily-journal-is-separate-plugin.md`（0004 と 0005 はまだコミットされていないが、作業ツリーにある）
- `docs/research/daily-journal-methodology-options.md`、`docs/research/daily-journal-decision-matrix.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`（wiki の探し方）、`info-hive-wiki/commands/init.md`、`info-hive-wiki/skills/info-hive/scripts/init_wiki.py`（`--wiki-dir`、`--raw-dir`）、`info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（走査の除外と孤立の判定）
- Foam の文書：https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/templates.md 、https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/daily-notes.md

## 成果に含めるもの

1. グローバル（`~/info-hive/`）とプロジェクトの両方の場合の、ディレクトリ構成案（ツリー）
2. 各ディレクトリの役割、誰が（人、どのプラグインのどのコマンド）書くか、ファイルの命名
3. 「破綻」として何を想定したか、それぞれの場面で構成がどう持ちこたえるか（例：名前の変更、年をまたぐ、ファイル数の増加、プラグインの追加、wiki との境界、VS Code・Foam・Git との関係、Windows と macOS・Linux の違い）
4. プラグインが作業領域とディレクトリの場所をどう見つけるか
5. 作者の決定や既存の ADR、wiki の現在のコードと食い違う点と、その扱いの提案
6. 作者が決める必要のある未決事項

リポジトリのファイルは書き換えないこと。成果は日本語で書く。


## 成果

### エージェント A

## 結論

作者が示したツリーはほぼそのまま使えます。そのうえで、次の 5 つの規則を足せば破綻を防げます。

1. **画面に出す名前と、プラグインが使う識別子を分けます。** 番号付きの名前（`20_Daily` など）はプラグインのコードに書きません。プラグインはワークスペースのルートにある対応表 `.info-hive/workspace.json` を読み、`daily` → `20_Daily` のように役割の名前（英語）から実際のディレクトリを引きます。キーを英語にするのは AGENTS.md の方針 B に合わせるためです。
2. **wiki のファイルが中身で参照するディレクトリは名前を固定します。** `90_Wiki` と `91_Raw` は、作った後は改名しません。wiki のソースページは `raw: 91_Raw/foo.md` のようにパスを本文に持つので、改名するとこの参照がすべて切れます。ほかのディレクトリは改名しても、対応表を直すだけで済みます。
3. **4 つの場所を同じディレクトリにします。** VS Code で開くフォルダー、Foam のワークスペースのルート、`.info-hive/` のある場所、対応表のパスの基準です。`.foam/templates/` はこのルートに置きます。
4. **ファイル名に、完全な日付か ISO 週を入れます。** `2026-11-03.md`、`2026-W45.md` のようにし、置き場所を変えても名前だけで特定できるようにします。年・月・週のフォルダー分けは見やすくするためのもので、リンクはフォルダーに依存しません。
5. **wiki との境界を、ディレクトリの外側に引きます。** wiki の lint と検索は `90_Wiki/` しか走査しません。日付ノートとノートをその外に置くので、wiki のコードを変えなくても孤立の指摘は増えません。

### 1. ディレクトリ構成案

**グローバル（既定。`~/info-hive/`）**

```text
~/info-hive/                      ← ワークスペースのルート（VS Code で開く／Foam のルート／Git リポジトリ）
├─ .info-hive/
│   └─ workspace.json             ← 役割とディレクトリの対応表。プラグインが読むのはここだけ
├─ .foam/
│   └─ templates/
│       ├─ daily-note.md          ← Foam と /log の両方が使う日付ノートのテンプレート
│       └─ weekly-note.md         ← 週次のテンプレート（/log が使う）
├─ .github/
│   └─ instructions/              ← GitHub Copilot 用の *.instructions.md（Claude Code は読まない）
├─ .vscode/settings.json          ← Foam の索引から外すディレクトリの設定
├─ CLAUDE.md                      ← Claude Code への指示（wiki の場所、ワークスペースの説明）
├─ .gitignore / .gitattributes
├─ 00_Inbox/                      ← 未分類の受け皿
├─ 10_Assets/
│   └─ 2026/                      ← wiki 以外の画像・添付
├─ 20_Daily/
│   └─ 2026/
│       └─ 11/
│           └─ 2026-11-03.md
├─ 30_Weekly/
│   └─ 2026/
│       └─ 2026-W45.md
├─ 40_Projects/
│   └─ <project-id>/
├─ 50_Knowledge/                  ← ADR-0006 の notes/ に当たる（仮定）
├─ 60_Output/
├─ 90_Wiki/                       ← WIKI_ROOT（名前は固定）
│   ├─ SCHEMA.md / index.md / log.md
│   ├─ sources/ entities/ concepts/ synthesis/ graph/
│   ├─ assets/                    ← モデルが書いた svg（ADR-0005。未決 U-2）
│   └─ .wiki-cache/
├─ 91_Raw/                        ← RAW_ROOT（名前は固定）
│   ├─ assets/<source-slug>/NNN.<ext>   ← 取り込んだ画像（ADR-0004）
│   └─ experiences/
└─ A0_Archive/
```

**プロジェクト**

```text
<project-root>/                   ← プロジェクトのハブとなるリポジトリ（VS Code で開く／Foam のルート）
├─ .info-hive/workspace.json      ← パスは <project-id>/... の形で書く
├─ .foam/templates/daily-note.md  ← プロジェクトに日付ノートを置く場合だけ
├─ .github/instructions/
├─ .vscode/settings.json
├─ .gitmodules
├─ CLAUDE.md
├─ <project-id>/                  ← info-hive のディレクトリ（作者の決定 3）
│   ├─ 00_Inbox/
│   ├─ 10_Assets/
│   ├─ 20_Daily/                  ← 任意（既定はグローバルに書く）
│   ├─ 30_Weekly/                 ← 任意
│   ├─ 50_Knowledge/
│   ├─ 60_Output/
│   ├─ 70_ADR/                    ← 作者の決定 1 の XX_ADR。番号は 70 を提案
│   │   ├─ README.md
│   │   └─ 0001-<slug>.md
│   ├─ 90_Wiki/
│   ├─ 91_Raw/
│   └─ A0_Archive/
└─ repos/                         ← 開発するコードのサブモジュール（提案。未決 U-4）
    ├─ <code-repo-a>/
    └─ <code-repo-b>/
```

**番号の割り当て（グローバルとプロジェクトで共通）**

| 番号 | 用途 |
| --- | --- |
| 00 | Inbox |
| 10 | Assets |
| 20 | Daily |
| 30 | Weekly |
| 40 | Projects（グローバルだけで使う） |
| 50 | Knowledge |
| 60 | Output |
| 70 | ADR（プロジェクトだけで使う） |
| 80 | 空き（今後のプラグイン用に予約） |
| 90 | Wiki |
| 91 | Raw |
| 92〜99 | wiki に関係する拡張用 |
| A0 | Archive |

同じ番号は、どちらのワークスペースでも同じ役割にします。この表は開発用リポジトリ（`info-hive-dev`）の設計書で管理します。

**`workspace.json` の例（提案）**

```json
{
  "schema": 1,
  "scope": "global",
  "roles": {
    "inbox": "00_Inbox", "assets": "10_Assets", "daily": "20_Daily",
    "weekly": "30_Weekly", "projects": "40_Projects", "knowledge": "50_Knowledge",
    "output": "60_Output", "wiki": "90_Wiki", "raw": "91_Raw", "archive": "A0_Archive"
  }
}
```

プロジェクトでは `"scope": "project"` と `"project_id": "myapp"` を書き、パスを `"wiki": "myapp/90_Wiki"` のようにします。**`daily` の項目を書かなければ、`log` はグローバルに書きます。** これで、作者の決定（両方を選べて、既定はグローバル）を、項目の有無だけで表せます。

### 2. 各ディレクトリの役割、書き手、命名

| ディレクトリ | 役割 | 書き手 | 命名 |
| --- | --- | --- | --- |
| `00_Inbox` | 分類や取り込みを待つ資料（PDF、Web のクリップ、断片） | 人、Web Clipper。`/log:review` が残りの件数を伝え、振り分けを提案する。`/wiki:ingest` は、取り込んだファイルを `91_Raw` に**移す** | 自由。`YYYY-MM-DD-<題>.<ext>` を推奨 |
| `10_Assets` | wiki 以外の画像・添付（日付ノート、ノート、成果物から参照） | 人（VS Code での貼り付けなど） | `YYYY/<参照元ノートの名前>-NN.<ext>` |
| `20_Daily` | 1 日 1 ファイルの記録（ADR-0006） | `log`（日付ノートを作るコマンド、`/log:memo` など）と人 | `YYYY/MM/YYYY-MM-DD.md`。月は 2 桁 |
| `30_Weekly` | 週次の見直し | `/log:review --week` が下書きを作り、人がふりかえりを書く | `GGGG/GGGG-Www.md`（ISO の週と週の年） |
| `40_Projects` | グローバルだけ。プロジェクトごとのメモ | 人 | `<project-id>/`。プロジェクトに専用のワークスペースがあれば、その場所を書いた `README.md` だけを置く |
| `50_Knowledge` | 人が手を入れるノウハウのノート（ADR-0006 の `notes/`） | `log` のノート書き出しコマンド（名前は未決）が作り、人が編集する | 日本語の題でよい。frontmatter の 5 項目と、元の日付ノートを書く |
| `60_Output` | 外に出す成果物（報告、スライドなど） | 人とエージェント | `YYYY-MM-DD-<題>`（ファイルまたはフォルダー） |
| `70_ADR` | プロジェクトだけ。設計の決定 | 人（エージェントが補助） | `NNNN-<slug>.md` と `README.md` |
| `90_Wiki` | LLM が書く知識ページ | wiki プラグインだけ（SKILL.md L35「この層はすべて LLM が受け持つ」） | wiki の規約に従う。プロジェクトでは D-06 の `<project-id>--<topic-slug>.md` |
| `91_Raw` | 取り込んだ原資料と訳文。取り込んだ後は変えない | `/wiki:ingest`、`wiki_fetch.py`（ADR-0004）、`/wiki:learn` | ソースページのスラッグとそろえる。画像は `assets/<source-slug>/` |
| `A0_Archive` | 終わったものを退避する | 人（将来はコマンド） | 元のパスを保って移す（例：`A0_Archive/40_Projects/<id>/`）。`20`、`90`、`91` は移さない |

### 3. 想定した「破綻」と、構成がどう持ちこたえるか

| 場面 | 起こること | 対策 |
| --- | --- | --- |
| **番号や名前の変更** | プラグインが名前を決め打ちしていると、見失う。wiki の `raw:` の参照が切れる | 名前は対応表で引く。`90` と `91` は改名しない。日付ノートや週次ノートへのリンクはファイル名だけで解決するので、フォルダーを変えても切れない |
| **年をまたぐ** | 週次ノートを `%Y` で名付けると、年末年始の週が 2 つの年に分かれる | 週の年（ISO）でフォルダーを分ける。計算すると、2026-12-28（月）〜2027-01-03（日）は 2026-W53 になり、2027-01-04 から 2027-W01 が始まる（Python の `date.isocalendar()` で確かめた）。日付ノートは暦の年でよい |
| **ファイル数が増える** | 1 つのフォルダーにファイルがたまる | 日付ノートは 1 か月に 31 件まで、1 年に 365 件で、月のフォルダーで十分に分かれる。Inbox の滞留は週次の見直しで知らせる |
| **プラグインを足す** | 番号やディレクトリ名がぶつかる | 番号の表で空きを割り当てる（80 は予約済み）。新しいプラグインは対応表に役割のキーを 1 つ足し、自分のディレクトリだけを作る。既存のディレクトリを改名したり作り直したりしない |
| **wiki との境界** | 日付ノートが孤立として報告される | 日付ノートとノートは `90_Wiki` の外に置く（`wiki_lint.py` L157 は `wiki_root` の下だけを走査する） |
| | wiki のページから日付ノートにリンクすると、リンク切れになる | wiki からは wikilink を張らず、`/wiki:ingest` で `91_Raw` に取り込んでから引用する |
| | 取り込んだ後にノートを編集すると、raw の内容が変わる | `50_Knowledge` のノートは、取り込みのときに `91_Raw` に**写して**固定する |
| | 同じ名前のノートとソースページが Foam でぶつかる | 写したファイルの名前に日付を付け（例：`<名前>-YYYYMMDD.md`）、ソースページと区別する（提案） |
| **raw を wiki の中に入れる** | lint の除外は `raw` という名前だけを見る（`wiki_lint.py` L108）ので、`90_Wiki/91_Raw` にすると原資料をページとして走査する | `91_Raw` は `90_Wiki` と同じ階層に置き、中に入れない |
| **VS Code と Foam** | テンプレートは各ワークスペースの `.foam/templates` に置く決まりなので、ルートがずれると見つからない | ルートを 1 か所にそろえる（規則 3） |
| | テンプレートのない場所で Foam の「日付ノートを開く」を使うと、`journal/yyyy-mm-dd.md` ができる（Foam の既定） | プロジェクトに日付ノートを置かない場合は、プロジェクトでは `/log` を使い、Foam で開くときは `~/info-hive` を開くと案内する（未決 U-11） |
| | `91_Raw`、`.wiki-cache`、`graph`、`repos/` が Foam の索引に入る | `.vscode/settings.json` で索引から外す。要件定義書 §3.3 が求める除外である |
| **Git** | 派生データ、大きな PDF、個人の日付ノートがリポジトリに入る | `.wiki-cache/` は除外する（wiki に専用の `.gitignore` がある）。PDF は LFS にするか除外する（未決 U-7）。個人の日付ノートを共有のリポジトリに入れないことも、既定をグローバルにする理由になる |
| **Windows と macOS・Linux の違い** | 大文字・小文字の区別、macOS の NFD、予約名、パスの長さ、改行、文字コード | ディレクトリ名は ASCII に限る（NFD、cp932、Windows の予約名を避けられる）。大文字・小文字は対応表のとおりに書き、変えたものを作らない。日本語のファイル名は wiki が NFC にそろえて扱う。`.gitattributes` で改行を LF にする。読み書きは UTF-8 を明示する |
| | `~` の解決先 | `Path.home()` で解決する。Windows では `%USERPROFILE%` になる。`Documents` の下に置くと OneDrive の同期の対象になることがあるので、既定はホームの直下にする |
| | シンボリックリンク | 使わない。Windows では作るのに権限が要り、要件定義書 §4.3 でも使わない方針になっている |
| **グローバルとプロジェクトの取り違え** | 2 つの wiki が混ざる。日付ノートが 2 か所に分かれる | 探す順を決め（下の 4）、`daily` は項目があるときだけプロジェクトに書く |
| **プロジェクトの名前がぶつかる** | `<project-id>/` とコードのサブモジュールが同じ名前になる | サブモジュールは `repos/` の下に置く |

### 4. プラグインが作業領域を見つける方法

1. **コマンドの引数**で場所を指定されたら、それを使う（`--workspace <path>`、`--global`、`--project`）。
2. **環境変数 `INFO_HIVE_HOME`** があれば、それをグローバルのルートにする。なければ `~/info-hive` にする。開発用 PC のパスは仕様に書かない。
3. **現在のディレクトリから親へたどり**、`.info-hive/workspace.json` を探す。サブモジュールの `.git` があっても止まらず、ホームの直下まで進む。見つかればプロジェクトのワークスペースとする。ただし、その場所がグローバルのルートなら、グローバルとして扱う。
4. **役割ごとに場所を決める。** プロジェクトの対応表に役割があれば、それを使う。`daily` と `weekly` がなければグローバルを使う。wiki は SKILL.md L21 の今の順（指定したパス、プロジェクトの指示、グローバルの指示、`wiki/`）をそのまま使う。初期化のときに `CLAUDE.md` に `90_Wiki` と `91_Raw` を書けば、wiki のコードは変えなくてよい。
5. 日付ノートの**作る場所の正本**は、テンプレート `.foam/templates/daily-note.md` の `foam_template.filepath` にする（例：`20_Daily/$FOAM_DATE_YEAR/$FOAM_DATE_MONTH/$FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE.md`）。`log` はこの値の変数を置き換えて場所を決める。対応表の `daily` は、繰り越しや見直しのときに探す範囲として使う。`filepath` が `roles.daily` で始まっているかは、点検のコマンドで確かめる。
6. 何も見つからなければ、黙って作らず、初期化を提案する。初期化では、自分のプラグインが使うディレクトリと、対応表の自分のキーだけを足す。

### 5. 既存の決定やコードとの食い違いと、その扱い

| # | 食い違い | 提案 |
| --- | --- | --- |
| 1 | ADR-0006 の保存先は `~/daily/` と `<プロジェクト>/daily/` | 新しい ADR で置き換える。ADR-0006 は「パスは既定値と設定で扱い、仕様に固定しない」としているので、方針とは合っている |
| 2 | ADR-0006 のテンプレートの置き場は `~/daily/.foam/templates/` | `~/info-hive/.foam/templates/` に変える。プロジェクトでは `<project-root>/.foam/templates/` |
| 3 | ADR-0006 の `<保存先>/notes/` | `50_Knowledge/` に読み替える（仮定。U-3） |
| 4 | 方法論レポート L287 の `<保存先>/YYYY-MM-DD.md`（フォルダーを分けない） | 作者の `20_Daily/2026/04` に合わせて `YYYY/MM/` に分ける |
| 5 | ADR-0005 と要件定義書 §3.3・D-03 では、モデルが書く svg は `wiki/assets/`。作者は「RAW_ROOT の下の assets に Wiki 用の画像を置く」とした | 取り込んだ画像を `91_Raw/assets/` に置く点は、ADR-0004 と一致する。モデルが書く svg まで raw に置くと、raw に原資料でないものが入り、ページから wiki の外を参照することになる。そこで、svg は `90_Wiki/assets/` に残すことを提案する（U-2） |
| 6 | wiki のグローバルの既定は `~/wiki/` と `~/wiki/raw/`（SKILL.md L61、L116〜117、`commands/init.md` の手順 1 と 3、`retrieval-setup.md` の質問 1） | 今の `--wiki-dir 90_Wiki --raw-dir 91_Raw` で初期化できる（`init_wiki.py` L263〜264）。既定と文書は、wiki の別の版で直す |
| 7 | `wiki_evolve_loop.py` L419 は、raw の場所を `args.wiki.parent / 'raw'` と決め打ちしている | `91_Raw` の構成では、`~/info-hive/raw/` というディレクトリが勝手にできる。直すまでは `--raw` を指定する。修正の候補として記録する |
| 8 | `SCHEMA.md.template` の場所の欄は `raw/` のまま（L10〜11）。`init_wiki.py` はこのテンプレートの値を置き換えない | `init.md` の手順 4 で人が直す。初期化で自動で書き換える案は、wiki の改修として扱う |
| 9 | 要件定義書 §3.3 の例は `project-root/raw`、`wiki`。`raw:` は「プロジェクトルート基準」 | 基準は `init_wiki.py` に渡したディレクトリ（ワークスペースのルート、またはプロジェクトの `<project-id>/`）と改める |
| 10 | 要件定義書 D-06 の `project-id` は ASCII の小文字 | `<project-id>/` のディレクトリ名と `40_Projects/<project-id>/` に同じ ID を使う |
| 11 | 決定行列の P5（wiki の側で、指定したディレクトリを孤立の判定から外す） | この構成では、日付ノートは wiki の外にあるので要らない。日付ノートを wiki の検索で探したい場合は、除外ではなく、走査する範囲を広げる話になる |

### 6. 作者が決める必要のある事項

| # | 決めること |
| --- | --- |
| U-1 | `90_Wiki` と `91_Raw` を改名しない固定名にする（推奨）か、入れ子の `90_Wiki/{wiki,raw}` にするか |
| U-2 | モデルが書く svg を `90_Wiki/assets/` に置く（ADR-0005）か、`91_Raw/assets/` の下に置くか |
| U-3 | `50_Knowledge` を ADR-0006 の `notes/` とみなすか |
| U-4 | プロジェクトの info-hive ディレクトリの名前を `project-id`（ASCII）にするか。サブモジュールを `repos/` にまとめるか |
| U-5 | ADR の番号を 70 にするか。グローバルにも ADR を置くか |
| U-6 | 対応表の名前と形式（`.info-hive/workspace.json`） |
| U-7 | グローバルのワークスペースを Git で管理するか。`91_Raw` の PDF を Git に入れるか（LFS か除外か） |
| U-8 | 週次ノートの名前を ISO 週（`GGGG-Www`）にするか |
| U-9 | `40_Projects` と、プロジェクトごとのワークスペースの関係（場所を書いた案内だけを置くか） |
| U-10 | Inbox から `91_Raw` に**移す**か、**写す**か。`50_Knowledge` は写すことを提案する |
| U-11 | プロジェクトにも `20_Daily` と `30_Weekly` を許すか。プロジェクトで Foam の日付ノートを使ったときの扱い |
| U-12 | アーカイブの規則（何を、いつ、誰が移すか） |
| U-13 | ワークスペースの初期化をどこが受け持つか。各プラグインの init が自分の分だけを足す（提案）か、共通の init を作るか |

## 根拠

- **wiki の走査の範囲**
  - `wiki_lint.py` L155〜161 は、`wiki_root.rglob("*.md")` で wiki のルートの下だけを走査します。L107〜108 で、一番上の階層の `indexes`、`graph`、`raw`、`.evolution` と管理用のファイルを除きます。
  - L278〜281 は、被リンクのないページを孤立として報告します。
  - `wiki_search.py` L304、`wiki_stats.py` L55、`wiki_graph_extract.py` L91 も、`"raw"` という名前で除外しています。
  - したがって、raw が wiki の外にあれば除外の設定は要らず、中にあるなら名前を `raw` にしておく必要があります。
- **wiki の場所を変えられるか**
  - `init_wiki.py` は `--wiki-dir` と `--raw-dir` を受け取ります（L263〜264）。`raw/assets` を作ります（L199〜205）。
  - `copy_template` の置き換えは、SCHEMA には使っていません（L215〜217 の呼び出し）。
  - SKILL.md L21 には wiki を探す順が、L84 には「この構成は既定値であり、必須ではない」とあります。L61 と L117 にはグローバルの既定 `~/wiki`、`~/wiki/raw` があります。
- **raw の場所の決め打ち**：`wiki_evolve_loop.py` L419 が `args.wiki.parent / 'raw'`、L699 のヘルプも「既定: wiki と同じ階層の raw」です。
- **raw の参照は文字列のパス**：`SCHEMA.md.template` L10〜11、L64（source ページの `raw`）、L132（`raw_ref: "raw/..."`）。`wiki_graph_extract.py` L402〜407 は、`raw:` の値を `raw:<パス>` という文字列のまま使います。このため、`91_Raw` を改名すると参照が切れます。
- **ADR**
  - ADR-0004：取り込んだ画像は `raw/assets/<ソースのスラッグ>/` に置く。raw は取り込んだ後に変えない。
  - ADR-0005：モデルが書く svg は `wiki/assets/<スラッグ>-NN.svg`。browse は生の HTML を出さず、ページ一覧にあるパスしか返さない。
  - ADR-0006：保存先は `~/daily/` と `<プロジェクト>/daily/` で、既定はグローバル。パスは仕様に固定しない。テンプレートは `.foam/templates/daily-note.md`。ノートは `<保存先>/notes/`。テンプレートの置き場は保存先によって変わる。
- **Foam の文書**（作業中に subagent で取得した報告による）
  - テンプレートは「special `.foam/templates` directory of your workspace」に置きます。日付ノートは `.foam/templates/daily-note.js`、`daily-note.md` の順に探します。
  - `filepath` は「relative to the current workspace」で、`FOAM_DATE_*` の変数を使って日付ごとのフォルダーを作れます（文書の例は `/journal/$FOAM_DATE_YEAR/...`）。
  - 既定では「daily notes are created as `yyyy-mm-dd.md` in the workspace's `journal` folder」です。
  - マルチルートでは「Foam checks each folder in the order they're listed and uses the first one it finds」です。
  - 変数には `FOAM_DATE_WEEK` と `FOAM_DATE_WEEK_YEAR` もあります。
- **要件定義書**：§3.3 は RAW_ROOT とテンプレートを Foam の索引から外すことと、`raw:` の基準を明記することを求めています。§4.1 の D-06 は `project-id` を `[a-z0-9]+(?:-[a-z0-9]+)*` とし、Windows の予約名、パスの長さ、大文字・小文字だけの重複の確認を求めています。§4.3 では、シンボリックリンクを使わない方針です。
- **ISO 週の計算**：Python の `isocalendar()` で、2026-12-28、2026-12-31、2027-01-01、2027-01-03 は (2026, 53)、2027-01-04 は (2027, 1) でした。2026-01-01 が木曜なので、2026 年は 53 週あります。
- **対応表を JSON にした理由**：wiki は Python 3.10 以上を前提にしています（`retrieval-setup.md`）。`tomllib` は 3.11 から入り、YAML は標準ライブラリにないので、標準ライブラリで読める JSON を選びました。CONTRIBUTING.md の「新しい補助の処理には標準ライブラリを優先する」にも合います（ADR-0004 の引用による）。
- **既定をグローバルにする構造上の理由**：Claude Code のデスクトップ版では、作業ディレクトリがプロジェクトとは限りません（ADR-0006 の要件）。グローバルが既定なら、どこから起動しても書く場所が決まります。

## 検討した代替案

| 案 | 採らなかった理由 |
| --- | --- |
| `90_Wiki/wiki/` と `90_Wiki/raw/` の入れ子にする | wiki のコードを変えずに済み、`90_Wiki` を改名しても `raw: raw/...` は切れない。最も丈夫だが、作者のツリー（`91_Raw` が一番上の階層）と違い、`wiki/wiki` という重なりが生じる。U-1 の代わりの案として残す |
| プラグインが使うディレクトリだけ番号を付けない（`wiki/`、`raw/`、`daily/`） | 作者の決定（すべてに番号を付ける）に反する |
| 対応表を持たず、名前をプラグインに書き込む | 改名に耐えない。ADR-0006 の「仕様に固定しない」と、PC に固有の値を仕様にしない方針に反する |
| 対応表を `CLAUDE.md` か `SCHEMA.md` に書く | `CLAUDE.md` は自然文なので、スクリプトから確実には読めない。`SCHEMA.md` は wiki のものなので、`log` が読み書きする場所として適さない |
| 対応表を TOML か YAML にする | TOML は Python 3.11 から、YAML は標準ライブラリ以外が要る |
| 日付ノートを `20_Daily/` の直下か年のフォルダーにだけ置く | 数としては 1 年 365 件でも十分扱えるが、作者が `YYYY/MM` を決めた |
| 月のフォルダーを Foam の例のように `11-Nov` にする | 英語の月名が入り、並び順と文字列の比較が複雑になる |
| 週次ノートを `20_Daily/2026/W45.md` に混ぜる | 型の違うファイルが同じ範囲に入り、`log` が日付ノートを探すときに除外が要る |
| サブモジュールを `<project-root>` の直下に置く | `<project-id>/` と名前がぶつかりやすい。Foam から外すときにサブモジュールごとの指定が要る |
| `.foam` を `<project-id>/` の中に置き、そこを VS Code で開く | コードが VS Code の表示に入らない。Claude Code を起動する場所ともずれる |
| モデルが書く svg も `91_Raw/assets/` に置く | raw に原資料でないものが入る（ADR-0004 の raw の意味が崩れる）。ページから wiki の外のパスを参照することになり、browse の配信の設計（ADR-0005）とも合わない。作者の意図がこちらなら U-2 で決める |
| `.github/instructions` だけで指示を書く | Claude Code はここを読まないので、`CLAUDE.md` を別に置く |

## 前提と不確実性

- **作者の決定 3 の読み方は仮定です。** 「プロジェクトルートの下に `<project-id>/` を置き、コードはサブモジュールにする」と読みました。このリポジトリ（`info-hive-dev`）が、文書をルートに、コードをサブモジュールに置いているのと同じ形だと解釈しています。
- **作者の決定 2 の「Wiki 用の画像」の範囲は仮定です。** 取り込んだ画像を指すと読みました。モデルが書く svg も含むなら、ADR-0005 を改める必要があります。
- **`50_Knowledge` = `notes/` も仮定です。**
- **Foam で確かめられなかったこと**
  - `foam_template` のブロックが、作ったノートから消えるか。
  - Foam の索引から外す設定の正確な名前（`foam.files.ignore` だと理解しているが、今回読んだ文書には出てこない）。
  - `FOAM_DATE_WEEK` と `FOAM_DATE_WEEK_YEAR` が ISO の週か。
  - マルチルートで `filepath` をどう解釈するか。
  - 設定（`foam.openDailyNote.*`）とテンプレートの `filepath` のどちらが優先されるか。
  - これらは実機での確認が要ります。
- **VS Code で貼り付けた画像の保存先**（`markdown.copyFiles.destination` などの設定）は記憶にもとづくもので、確かめていません。
- **パスの長さ**：Windows の 260 文字の上限には、上の構成なら十分な余裕があると推測します。例として `C:\Users\<名前>\Works\myapp\myapp\90_Wiki\concepts\myapp--long-topic-slug.md` は約 85 文字です。ただし、日本語のスラッグが長い場合は確かめていません。
- **他の作業ツリーの未コミットの変更**（要件定義書の差分）は、§3.3 と D-03 の該当箇所だけを読みました。
- **読まなかった文書**：`docs/porting-plan.html` と `info-hive-wiki/UPSTREAM.md` は読んでいません。

## 参照

- `AGENTS.md`（リポジトリの役割、方針 B、プラグインを足す手順）
- `docs/adr/0003-split-marketplace-repo.md`、`docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0005-wiki-figures-use-mermaid-and-svg.md`、`docs/adr/0006-daily-journal-is-separate-plugin.md`
- `docs/research/daily-journal-decision-matrix.md`（L21、L67、L298〜301）、`docs/research/daily-journal-methodology-options.md`（L287、L345、L384）
- `llm-wiki-product-concept-and-requirements-ja.md`（§3.3 L92〜121、§4.1〜4.3、D-03、D-06）
- `info-hive-wiki/skills/info-hive/SKILL.md`（L21、L23、L35、L57〜84、L110〜124）
- `info-hive-wiki/commands/init.md`
- `info-hive-wiki/skills/info-hive/references/retrieval-setup.md`
- `info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template`（L10〜11、L50、L64、L132）
- `info-hive-wiki/skills/info-hive/scripts/init_wiki.py`（L46、L180〜264）
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（L107〜108、L155〜161、L278〜281）
- `info-hive-wiki/skills/info-hive/scripts/wiki_search.py`（L304）、`wiki_stats.py`（L55）、`wiki_graph_extract.py`（L91、L119、L402）、`wiki_evolve_loop.py`（L419、L699）、`wiki_evolve.py`（L9、L534）
- Foam の文書（subagent が取得）：https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/templates.md 、https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/daily-notes.md 、https://raw.githubusercontent.com/foambubble/foam/master/docs/user/recipes/multi-root-workspaces.md

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```

### エージェント B

## 結論

**作業領域の根を 1 つ（グローバルは `~/info-hive/`、プロジェクトは `<プロジェクトルート>/<プロジェクト名>/`）に固定し、その直下に作者の 2 桁接頭辞のディレクトリを並べる。プラグインが書くのは `20_Daily`、`30_Weekly`、`50_Knowledge`、`90_Wiki`、`91_Raw`、`.foam/templates` だけに限り、`90_Wiki` を wiki の走査の根（WIKI_ROOT）、`91_Raw` を RAW_ROOT とする。**場所の対応は、作業領域の直下の 1 つの設定ファイル（提案名 `info-hive.yaml`）に役割→ディレクトリ名として書き、各プラグインはそれを読む。これで、wiki の lint・検索の範囲は `90_Wiki` の中に閉じ、日付ノートは孤立として報告されず、ディレクトリ名を変えても直す場所が限られる。

### 提案するツリー（グローバル）

```
~/info-hive/                       ← 作業領域の根（Foam のワークスペース、Git リポジトリ）
├─ info-hive.yaml                  ← 役割→ディレクトリ名の対応と、作業領域の印（提案）
├─ .foam/
│  └─ templates/
│     ├─ daily-note.md             ← /log:init が置く。filepath で 20_Daily/年/月 を指す
│     └─ weekly-note.md            ← /log:review --week が使う（提案）
├─ .github/
│  └─ instructions/                ← Copilot 向けの指示。人が書く
├─ .vscode/
│  └─ settings.json                ← Foam の除外設定など。人が書く（作者の例にはない。提案）
├─ 00_Inbox/                       ← 未分類の一時置き場。人だけが書く
├─ 10_Assets/                      ← wiki 以外の画像・添付。人だけが書く
├─ 20_Daily/
│  └─ 2026/
│     └─ 11/
│        └─ 2026-11-03.md          ← /log:* と Foam の Open Daily Note が書く
├─ 30_Weekly/
│  └─ 2026/
│     └─ 2026-W45.md               ← /log:review --week が書く
├─ 40_Projects/                    ← プロジェクトごとの入り口ページ。人が書く
├─ 50_Knowledge/                   ← ADR-0006 の notes/ に当たる。/log:note（仮）が書き出し、人が編集
├─ 60_Output/                      ← 成果物（レポート、資料）。人が書く
├─ 90_Wiki/                        ← WIKI_ROOT。/wiki:* だけが書く
│  ├─ SCHEMA.md  index.md  log.md
│  ├─ assets/                      ← ADR-0005 の svg
│  ├─ sources/  entities/  concepts/  synthesis/  graph/  indexes/
│  └─ .wiki-cache/                 ← 派生データ。Git で無視
├─ 91_Raw/                         ← RAW_ROOT。人が置き、/wiki:ingest が書く
│  ├─ <ソースのスラッグ>.<拡張子>
│  └─ assets/<ソースのスラッグ>/   ← ADR-0004 の取り込んだ画像
└─ A0_Archive/                     ← 使わなくなったもの。人だけが動かす。プラグインは走査しない
```

### 提案するツリー（プロジェクト）

```
<プロジェクトルート>/              ← Git リポジトリの根。Claude Code のプロジェクト
├─ CLAUDE.md                       ← 「作業領域は <プロジェクト名>/ にある」と書く
├─ <プロジェクト名>/               ← info-hive の作業領域。中身はグローバルと同じ並び
│  ├─ info-hive.yaml
│  ├─ .foam/templates/
│  ├─ 00_Inbox/  10_Assets/  20_Daily/  30_Weekly/  50_Knowledge/  60_Output/
│  ├─ 70_ADR/                      ← プロジェクトだけ。番号は仮（作者は「任意の数字」）
│  ├─ 90_Wiki/  91_Raw/  A0_Archive/
│  └─ （40_Projects は置かない。提案）
├─ <コードのリポジトリ 1>/         ← Git サブモジュール。info-hive は触らない
└─ <コードのリポジトリ 2>/
```

プロジェクトの作業領域で `20_Daily` と `30_Weekly` を実際に使うかは選べる（ADR-0006 の「両方を選べる」）。使わないときは `info-hive.yaml` に `daily` の役割を書かず、ディレクトリも作らない。

### 各ディレクトリの役割、書き手、命名

| ディレクトリ | 役割 | 書くもの | ファイルの命名 |
| --- | --- | --- | --- |
| `info-hive.yaml` | 役割→ディレクトリ名の対応。作業領域の印 | 各プラグインの init（なければ作る。あれば足りないキーだけ提案） | 固定名 |
| `.foam/templates/daily-note.md` | 日付ノートの雛形。Foam と `log` が共用 | `/log:init`（既存なら上書きせず知らせる。ADR-0006） | Foam の固定名 |
| `.foam/templates/weekly-note.md` | 週次の雛形 | `/log:init` | 提案。Foam の特別名ではない |
| `00_Inbox` | 行き先を決めていないものの一時置き場 | 人 | 自由 |
| `10_Assets` | wiki 以外（`60_Output`、`40_Projects` など）から参照する画像・添付 | 人 | 自由。`90_Wiki` からは参照しない |
| `20_Daily/YYYY/MM/` | 1 日 1 ファイルの日付ノート | `/log:start` `stop` `plan` `close` `tidy` と Foam | `YYYY-MM-DD.md`。年月のディレクトリの下でも日付を省かない |
| `30_Weekly/YYYY/` | 週次レビュー | `/log:review --week` | `YYYY-Www.md`（ISO 週。ディレクトリは ISO 週年） |
| `40_Projects` | グローバルだけ。プロジェクトごとの入り口（作業領域の場所、状態） | 人 | `<プロジェクト名>.md` |
| `50_Knowledge` | 日付ノートから書き出したノート。wiki に入れる前の素材 | `/log:note`（仮）が書き出し、人が編集 | wiki のスラッグ規則（`page-conventions.md` L83〜89）に合わせる。frontmatter は wiki の必須 5 項目に `source_daily:` を足す |
| `60_Output` | 外に出す成果物 | 人 | 自由 |
| `70_ADR` | プロジェクトの設計決定（プロジェクトだけ） | 人 | `NNNN-<slug>.md` |
| `90_Wiki` | WIKI_ROOT | `/wiki:*` だけ | 現行のまま（`SCHEMA.md`、`sources/` ほか）。プロジェクトでは D-06 の `<project-id>--<topic>.md` |
| `91_Raw` | RAW_ROOT。原本または訳文（ADR-0004） | 人が置く。`/wiki:ingest` が訳文と `assets/<slug>/` を書く | `ingest-workflow.md` L11〜23 のスラッグ規則。取り込み後は不変 |
| `A0_Archive` | 現役でないもの。元の相対パスを保ったまま移す（例：`A0_Archive/60_Output/…`） | 人 | 元の名前のまま |

接頭辞の割り当ての規則（提案）：`0x`〜`6x` は人が主に書く領域、`7x`〜`8x` はプロジェクト固有の領域（ADR など）、`9x` はプラグインが正本として管理する領域、`A0` 以降は冷やしておく領域。プラグインを足すときは `9x` から取る。番号は飛ばして付けてあるので、間に足せる。

### プラグインが作業領域を見つける手順

1. ユーザーが引数や依頼でパスを指定していれば、それを使う。
2. 現在のディレクトリから Git の根まで上にたどり、各階層で `./info-hive.yaml` と、1 段下の `./*/info-hive.yaml` を探す。1 つ見つかれば、それが「プロジェクトの作業領域」。2 つ以上なら、混ぜずにユーザーに聞く（`SKILL.md` L21 の「2 つの wiki を黙って混ぜてはならない」を踏襲）。1 段下も見るのは、作業領域が `<プロジェクトルート>/<プロジェクト名>/` にあり、cwd がプロジェクトルートやコードのサブモジュールの中であることが多いため。
3. 見つからなければ `~/info-hive/info-hive.yaml`（グローバル）。
4. 役割がその作業領域にあるかは、`info-hive.yaml` のキーの有無で決める。`wiki` キーがあれば wiki はそこ、`daily` キーがなければ `log` はグローバルに落ちる。これで「wiki はプロジェクト既定、log はグローバル既定」（ADR-0006）を、プラグインごとの分岐なしに表せる。
5. 人向けの案内は、現行どおり `CLAUDE.md`／`~/.claude/CLAUDE.md` の定型文（`agent-memory-integration.md`）に書く。定型文は案内、`info-hive.yaml` はスクリプトが読む正本、`90_Wiki/SCHEMA.md` の「置き場所」ブロックは wiki の内部で引き続き有効で、`info-hive.yaml` と一致させる（lint で一致を確かめる項目を将来足す）。

`info-hive.yaml` の中身の案（キーは英語、AGENTS.md の方針）：

```yaml
version: 1
wiki: 90_Wiki
raw: 91_Raw
daily: 20_Daily
weekly: 30_Weekly
notes: 50_Knowledge
archive: A0_Archive
```

パスは作業領域の根からの相対パスで、区切りは `/` で書く。

## 根拠

**wiki の範囲が `90_Wiki` に閉じるので、日付ノートの孤立問題が構造で消える。** `wiki_lint.py` の `collect_pages` は `wiki_root.rglob("*.md")` で wiki の根の下だけを歩き（L157）、被リンクのないページを全て孤立として報告する（L279〜281）。`wiki_search.py` も同じく `wiki_root.rglob` で、`indexes`、`graph`、`raw`、`.wiki-cache`、`.evolution` を除く（L300〜304）。`20_Daily` と `50_Knowledge` を `90_Wiki` の外の兄弟に置けば、lint も検索も触れない。ADR-0006 が避けたかった「lint と検索の両方に例外を足し続ける」事態にならない。

**既存の wiki コードは、この配置をそのまま受け付ける。** `init_wiki.py` は `<base-dir> --wiki-dir --raw-dir` を取り、`wiki = project_root / wiki_dir`、`raw = project_root / raw_dir` を作る（L166〜167、`SUBDIRS` と `raw/assets` を作る L182〜195）。つまり `python init_wiki.py ~/info-hive --wiki-dir 90_Wiki --raw-dir 91_Raw` で動く。`SKILL.md` L84 も「`kb/`、`notes/`、`vault/` のような別の名前を使ってよい。`SCHEMA.md` に従う」と明言している。`SCHEMA.md.template` の「置き場所」ブロック（L7〜11）に `90_Wiki/`、`91_Raw/`、`91_Raw/assets/` と書けばよい。要件定義書 §3.3 も「`raw: raw/...` はプロジェクトルート基準」とし、基準は作業領域の根である（L121）。

**raw と wiki を兄弟に置く理由。** グローバルの既定 `~/wiki/raw/`（`SKILL.md` L61、`init.md` 手順 3）は raw を wiki の中に入れるが、ADR-0004 の「見直す条件」が、Foam が frontmatter つきの訳文を知識ページと取り違える懸念を挙げている。raw を `91_Raw` として wiki の外に出せば、Foam の除外設定を `91_Raw/**` の 1 行で書け、要件 §3.3 L117「`RAW_ROOT` …を索引・名前衝突検査の対象から除外する」にも合う。作者の決定 2「`RAW_ROOT` の下の assets に Wiki 用の画像を置く」は、`91_Raw/assets/<slug>/`（ADR-0004、`init_wiki.py` L191）にそのまま対応する。

**作業領域をプロジェクト名のディレクトリにする作者の決定 3 は、Foam のマルチルートの仕様と合う。** Foam の文書（multi-root-workspaces.md、2026年11月3日に取得）は、テンプレートの `filepath` を `/<フォルダー名>/...` で始めると、そのフォルダーを狙えるとし、「If no folder has that name, the path starts from the first folder」とする。グローバル（フォルダー名 `info-hive`）とプロジェクト（`<プロジェクト名>`）を同じワークスペースに開いても、名前が衝突しない。もし両方を `info-hive/` という固定名にすると、Foam も人も区別できない。

**日付ノートのファイル名に日付を全部書く理由。** Foam の wikilink はファイル名で解決し、`/today` などの日付スニペットは「日付テンプレートが作る名前」に向けてリンクを張る（daily-notes.md）。`2026/11/03.md` のように短くすると、月をまたいで同名が並び、Foam でリンク先が曖昧になる。`$FOAM_PREVIOUS_DAILY_NOTE` も「path must use numeric year, month and day」で、月名（`11-Nov`）や週番号のパスからは読み戻せない（daily-notes.md）。したがって `filepath` は次の形にする。

```yaml
---
foam_template:
  filepath: '/20_Daily/$FOAM_DATE_YEAR/$FOAM_DATE_MONTH/$FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE.md'
  name: 日付ノート
---
```

**週次を ISO 週年で切る理由。** 2026年1月1日は木曜なので 2026 年は ISO 週が 53 週あり、2027年1月1日（金）は 2026-W53 に属する。暦年のディレクトリに置くと、年末年始の週が 2 つの年に割れる。`FOAM_DATE_WEEK` と `FOAM_DATE_WEEK_YEAR` が Foam の変数にある（templates.md）ので、テンプレートと `log` のスクリプトで同じ値を作れる。今日 2026年11月3日は、ISO 週 1 の開始 2025年12月29日から 310 日目で、310 ÷ 7 = 44.3 なので W45 である。

**`A0_Archive` が最後に並ぶ理由。** ASCII では数字（0x30〜0x39）が英大文字（0x41〜）より前なので、`91_Raw` の後に `A0_Archive` が来る。Windows の Explorer の大文字小文字を無視した並びでも同じ。

**「破綻」として想定した場面と、持ちこたえ方。**

| 場面 | 何が壊れうるか | この構成での扱い |
| --- | --- | --- |
| ディレクトリ名（接頭辞）を変える | パスを持つ箇所が散ると直し漏れる | 持つ箇所を `info-hive.yaml`、`SCHEMA.md` の置き場所、指示ファイルの定型文、`.foam/templates/*.md` の `filepath`、`.vscode/settings.json` の 5 つに限る。wiki 内のリンクはスラッグで解決するので（`page-conventions.md` L49）`90_Wiki` の改名で壊れない。残る弱点は `sources/*.md` の `raw:`（`91_Raw/<slug>.pdf` を各ページが持つ）で、`91_Raw` の改名は一括置換が要る。`9x` を「改名しない番号」と決め、改名は手順書つきの作業にする |
| 年をまたぐ | 年のディレクトリがない。週が割れる | `log` は `mkdir(parents=True)` で作る。Foam が `filepath` の中間ディレクトリを作るかは未確認（下の不確実性）。週は ISO 週年で切る |
| ファイル数が増える | 一覧が重い | `20_Daily` は月ごとに最大 31 件。`30_Weekly` は年 53 件。wiki は 150 ページで index 分割の規律がある（`SKILL.md` L94）。`91_Raw` だけが平らに増えるので、必要になったら `91_Raw/<年>/` を許す（`raw:` は自由なパスなので受け付ける） |
| プラグインを足す | 既存のディレクトリに勝手に書く | 役割は `info-hive.yaml` に登録し、プラグインは自分の役割のディレクトリだけに書く。新しい正本は `9x` に取る |
| wiki との境界 | 日付ノートやノートが孤立・リンク切れとして報告される。wiki からの外向きリンク | `90_Wiki` の外は走査しない。wiki のページから `90_Wiki` の外へ `[[...]]` を書かない（lint でリンク切れになる）。外から wiki へ入る経路は `/wiki:ingest` だけ |
| VS Code・Foam | `.vscode/settings.json` が効かない。テンプレートの `filepath` が別のフォルダーに落ちる | マルチルートでは VS Code がフォルダー内の `settings.json` を無視し、`.code-workspace` かユーザー設定に書く必要がある（multi-root-workspaces.md）。`filepath` が `/20_Daily/...` なら単一ルートで正しく、マルチルートでは「最初のフォルダー」に落ちる。逆に `/info-hive/20_Daily/...` は単一ルートで `~/info-hive/info-hive/20_Daily/` を作る。対策：`log` のスクリプトは `filepath` の先頭が `/<作業領域のディレクトリ名>/` なら、その段を剥がして作業領域の根に解決する。人には「1 作業領域 1 ウィンドウ」を既定として勧める |
| Git | 派生データや大きい原本をコミットする | `90_Wiki/.wiki-cache/` と `graph.sqlite` は既存の `.gitignore` テンプレートで無視される。`91_Raw` を Git に入れるかは未決（下） |
| Windows と macOS・Linux | 大文字小文字、NFC/NFD、区切り、cp932 | 作業領域直下のディレクトリ名を ASCII に限る（日本語のファイル名は中で使う）。設定は `/` 区切りで書き、`Path` で結合する。大文字小文字は Linux で区別されるので、設定に書いた綴りのとおりに比べる。`~` は `Path.home()` で展開する。長いパスは Windows の 260 文字制限に当たりうるので、長い日本語スラッグを使う人には長いパスの設定を案内する |
| 2 つの作業領域を同時に開く | グローバルとプロジェクトを混ぜる | Foam ではフォルダー名で区別する。プラグインは手順 2〜4 で 1 つに決め、曖昧なら聞く |
| アーカイブ | 動かした先へのリンクが切れる | wiki のページと raw は `A0_Archive` に動かさない（`raw:` が切れる）。動かすのは `60_Output`、`40_Projects`、古い年の `20_Daily` など。Foam はワークスペース全体のファイル名でリンクを解決するので、`A0_Archive` を Foam の除外には入れず、プラグインの走査からだけ外す |

## 検討した代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 作者の最初のツリーのとおり、プロジェクトルート直下に番号つきディレクトリを並べる | 作者のあとの決定 3（プロジェクト名のディレクトリを置き、コードはサブモジュール）と食い違う。プロジェクトルート直下に並べると、コードのサブモジュールと `20_Daily` などが同じ階層に混ざり、Foam と Copilot の対象範囲も切り分けにくい |
| 作業領域のディレクトリ名を固定の `info-hive/` にする | Foam のマルチルートでフォルダー名が衝突し、`filepath` で狙えない。作者の決定 3 にも反する |
| `91_Raw` を `90_Wiki/raw/` に入れる（現行のグローバル既定） | Foam の除外とリポジトリの分離が `91_Raw` 単位でできなくなる。`wiki_lint.py` の `SKIP_TOP_LEVEL_DIRS` は `raw` という名前に依存しており（L108）、`91_Raw` に改名すると中に入れたときに走査される |
| 日付ノートを `90_Wiki/daily/` に入れる | 決定行列の P3 と同じで、孤立として全件報告される。ADR-0006 で却下済み |
| `info-hive.yaml` を作らず、`CLAUDE.md` の定型文だけで場所を伝える | 人向けの散文をスクリプトが解釈することになる。`log` と wiki が別々に場所の規則を持つと二重になる。ただし、作者が新しい設定ファイルを望まなければ、wiki は `SCHEMA.md`、`log` はテンプレートの `filepath` から場所を得る形でも成り立つ（下の未決 6） |
| 日付ノートを `20_Daily/2026/11/03.md` にする | Foam のリンクがファイル名で解決されるため曖昧になる。`$FOAM_PREVIOUS_DAILY_NOTE` も数値の年月日のパスを前提にしている |
| 週を暦年のディレクトリに置く | 年末年始の週が割れる。ISO 週年を使えば Foam の変数でも同じ値が取れる |
| `50_Knowledge` を wiki の一部（`90_Wiki/notes/`）にする | ユーザーが自由に編集する途中のノートが lint の対象になる。ADR-0006 は「ユーザーが `notes/` で手を入れてから wiki に入れるかを決める」としている |
| 接頭辞を 1 桁や 3 桁にする | 作者が 2 桁の英数字と決めている。2 桁で `00`〜`99` と `A0`〜 を使えば十分に間が空く |

## 前提と不確実性

**仮定**

- 作者の決定 3 を「プロジェクトルートは Git の根で、その直下に `<プロジェクト名>/` の作業領域と、コードのサブモジュールが並ぶ」と読んだ。「作業領域自体をサブモジュールにする」とは読んでいない。
- `70_ADR` の番号、`weekly-note.md` の名前、`info-hive.yaml` の名前と形式、`source_daily:` のキー名は、この文書の提案で、決まっていない。
- `40_Projects` はグローバルだけに置くと仮定した。作者のツリーはグローバルとプロジェクトを区別していない。
- 今日の日付（2026年11月3日）は環境から取った。ISO 週の計算は上に式で示した。

**確かめられなかったこと**

- Foam が `filepath` の中間ディレクトリ（`2026/11/`）を自動で作るか。templates.md の例は `journal/2022/11-Nov/...` を作るとしているので作ると推測するが、原文に明記はない。
- Foam の除外設定のキー名。`foam.files.ignore` という名前と、既定に `**/.foam/**` が入っていることは記憶で、今回取得した文書には載っていない。`foam.openDailyNote.directory` などの設定も daily-notes.md には書かれておらず、文書は「場所の変更はテンプレートの `filepath` で行う」としている。
- Foam が作ったノートから `foam_template` ブロックを除くか（ADR-0006 も未確認としている）。
- `.github/instructions/` が効く場所。Copilot はリポジトリの根の `.github/` を読むと記憶しているので、プロジェクトの作業領域 `<プロジェクト名>/.github/` は読まれない可能性がある。VS Code の設定で場所を足せるという記憶もあるが未確認。グローバル（`~/info-hive/` 自体がリポジトリ）では効く。
- wiki のスクリプトが `raw:` の相対パスをどこを基準に解決するか（`wiki_graph_lint.py` などは読んでいない）。要件 §3.3 の「プロジェクトルート基準」を前提にした。

**作者の決定・既存の ADR・現行コードと食い違う点と、扱いの提案**

1. ADR-0006 は保存先を `~/daily/`、`<プロジェクト>/daily/`、ノートを `<保存先>/notes/`、テンプレートを `~/daily/.foam/templates/` としている。この案では `~/info-hive/20_Daily/`、`<作業領域>/50_Knowledge/`、`<作業領域>/.foam/templates/` になる。構成を決める ADR（0007）を書き、ADR-0006 の「決定」と「影響」の該当行をそこから上書きするのがよい。
2. wiki の `SKILL.md` L61 と `init.md` 手順 3 は、グローバルの既定を `~/wiki/` と `~/wiki/raw/` にしている。コードは任意のパスを受け付けるので変更は文書だけだが、既定値を `~/info-hive`、`--wiki-dir 90_Wiki --raw-dir 91_Raw` に変えるなら、`SKILL.md`、`init.md`、`retrieval-setup.md`、`agent-memory-integration.md` の定型文を直す。ユーザーに見える変更なので SemVer の版が上がる（AGENTS.md のリリースの節）。
3. `SKILL.md` L21 の探索順（指定パス → プロジェクトの指示 → グローバルの指示 → cwd の `wiki/`）に、`info-hive.yaml` の段を足す提案になる。wiki のコードを変えない方針（ADR-0006）との兼ね合いは、作者が決める。
4. 作者の決定 2「`RAW_ROOT` の下の assets に Wiki 用の画像を置く」は、取り込んだ画像（ADR-0004、`91_Raw/assets/<slug>/`）と読んだ。モデルが描く svg は ADR-0005 のとおり `90_Wiki/assets/` に残す。「Wiki 用の画像を全て RAW 側に置く」という意味なら ADR-0005 と衝突するので、確認が要る。
5. 要件定義書 §3.3 の配置例は `raw/` と `wiki/` をプロジェクトルート直下に置いている。「提案」「未決」と明記された節なので、構成の ADR のあとに書き換える。D-06 の `<project-id>--<topic-slug>.md` は `90_Wiki` の中でそのまま使う。
6. `/log:note`（仮）が書いた `50_Knowledge` のノートを `/wiki:ingest` に渡すと、`ingest-workflow.md` L11 により `91_Raw` に写しが置かれ、ノートは人が編集し続けるので 2 つに分かれる。raw の不変性（ADR-0004）と合わせるなら、取り込み時点の写しを `91_Raw` に置き、元のパスとハッシュを frontmatter に記録して再取り込みは ADR-0004 と同じく別版にするのが整合する。
7. ADR-0005 の「影響」は `init_wiki.py` で `wiki/assets/` を作るとしているが、現行の `init_wiki.py` は `raw/assets` だけを作る（L191）。構成の変更とは別の未実装項目として残る。

**作者が決める必要のある未決事項**

1. プロジェクトの作業領域の形。上の仮定（`<プロジェクトルート>/<プロジェクト名>/`）でよいか。作業領域の中身をプロジェクトルートのリポジトリに直接コミットするか。
2. `XX_ADR` の番号と、ADR を wiki のソースとして取り込むか（取り込むなら `raw:` に `70_ADR/...` を書くことを許すか）。
3. `91_Raw` を Git に入れるか、Git LFS にするか、外に置くか。PDF が増えるとリポジトリが重くなる。
4. 場所の正本を `info-hive.yaml` にするか、wiki は `SCHEMA.md`、`log` はテンプレートの `filepath` という各自の方式にするか。
5. Foam を 1 作業領域 1 ウィンドウで使うか、グローバルとプロジェクトを 1 つのマルチルートにするか。後者なら `filepath` をフォルダー名つきで書き、設定を `.code-workspace` に置く。
6. `40_Projects` をグローバルだけにするか。`10_Assets` と `60_Output` の境目。`00_Inbox` にプラグインが書く場面（`/log:tidy` の振り分け先）を認めるか。
7. 週次のファイル名を ISO 週（`2026-W45.md`）にするか、週の月曜の日付にするか。
8. `.github/instructions/` を何に使うか。プロジェクトの作業領域に置いて効かない場合の置き場。
9. 古い年の `20_Daily` を `A0_Archive` に動かす運用を認めるか（`$FOAM_PREVIOUS_DAILY_NOTE` の連鎖はそこで切れる）。

## 参照

- `AGENTS.md`：リポジトリの役割、日本語と機械が読む文字列の方針、リリースの節
- `docs/adr/0003-split-marketplace-repo.md`、`docs/adr/0004-raw-holds-translated-web-pages.md`（raw の内容と `raw/assets/<slug>/`、見直す条件の Foam の取り違え）、`docs/adr/0005-wiki-figures-use-mermaid-and-svg.md`（`wiki/assets/` の svg、lint の除外）、`docs/adr/0006-daily-journal-is-separate-plugin.md`（保存先、テンプレート、`notes/`、影響と未決）
- `docs/research/daily-journal-methodology-options.md` L280〜290、L380〜392（ファイル名 `YYYY-MM-DD.md`、決定事項）、`docs/research/daily-journal-decision-matrix.md` §1、§6.2（P1 と P5）
- `llm-wiki-product-concept-and-requirements-ja.md` §3.2〜3.3（Global/Project、`RAW_ROOT`/`WIKI_ROOT`、除外、パスの基準）、D-06、§4.3（Foam CLI の範囲外書き込み）
- `info-hive-wiki/skills/info-hive/SKILL.md` L21〜23（wiki の探し方）、L55〜84（構成の既定と別名の許可）、L94（index の分割）
- `info-hive-wiki/commands/init.md` 手順 1〜5
- `info-hive-wiki/skills/info-hive/scripts/init_wiki.py` L166〜195（`--wiki-dir`、`--raw-dir`、`raw/assets`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py` L107〜108、L155〜161（走査と除外）、L277〜281（孤立）
- `info-hive-wiki/skills/info-hive/scripts/wiki_search.py` L300〜304、L635、L1165（走査と `.wiki-cache`）
- `info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template` L7〜11（置き場所）、`assets/wiki-cache_gitignore.template`
- `info-hive-wiki/skills/info-hive/references/retrieval-setup.md`（`.wiki-cache`、絶対パスを記録しない）、`references/agent-memory-integration.md`（定型文、パスの直し方）、`references/ingest-workflow.md` L11〜23、L63（raw のスラッグと `raw:`）、`references/page-conventions.md` L49〜53、L79〜97（スラッグの規則、NFC）
- Foam の文書（2026年11月3日に取得）：templates.md（`.foam/templates`、`daily-note.md`、変数、`foam_template.filepath`）、daily-notes.md（既定の `journal/yyyy-mm-dd.md`、`$FOAM_PREVIOUS_DAILY_NOTE` の数値パスの条件、スニペット）、recipes/multi-root-workspaces.md（設定の置き場、テンプレートの探索順、`/<フォルダー名>/` の解決）

使用した MCP サーバー: なし
使用した Agent Skills: なし

### エージェント C

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

### エージェント D

提案は、各作業領域を独立した保存単位にし、日次記録・人が編集するノート・Wiki・原資料を分ける形にまとまりました。番号は並び順にだけ使い、保存先は設定で指定します。現行 wiki で実現できる部分と、log の新規実装や ADR の改訂が必要な部分も分けて示します。
## 結論

**作者が示した番号付きの構成を採り、`90_Wiki`、`91_Raw`、日次記録、人が編集するノートを兄弟ディレクトリに分ける。番号や名前で保存先を推測せず、作業領域ごとの設定で指定する構成を推奨する。**

破綻を防ぐために固定すべきなのはディレクトリ名より、次の四つの境界である。

- **保存範囲**：グローバルとプロジェクトを混ぜない。
- **編集責任**：人のノート、log の記録、wiki の知識を区別する。
- **正本**：Markdown と原資料を正本にし、検索キャッシュは再生成可能にする。
- **探索範囲**：Wiki の検査・検索には `90_Wiki` だけを渡す。

以下は構成と運用の提案であり、未実装の設定やコマンドを含む。リポジトリのファイルは変更していない。

**1．グローバルの構成**

`~/info-hive/` 自体を、一つの info-hive 作業領域、かつ Foam で開くフォルダーとする。

```text
~/info-hive/                       ← info-hive 作業領域 W
├─.info-hive.json                  ← 保存先と作業領域 ID の設定【新設案】
├─.foam/
│  └─templates/
│      ├─daily-note.md
│      ├─weekly-note.md            ← 週次機能を導入したら作成
│      └─knowledge-note.md         ← 必要になったら作成
├─.github/
│  └─instructions/
├─.vscode/
│  └─settings.json                 ← 必要な場合だけ
├─AGENTS.md
├─CLAUDE.md                       ← Claude Code 向けの入口
├─.gitignore
├─.gitattributes
├─00_Inbox/
├─10_Assets/
│  └─2026/
│      └─11/
├─20_Daily/
│  └─2026/
│      └─11/
│          └─2026-11-03.md
├─30_Weekly/
│  └─2026/
│      └─2026-11-02-weekly.md       ← 対象週の月曜日の日付
├─40_Projects/
│  └─project-a/
│      └─project-a-overview.md
├─50_Knowledge/
│  └─notes/
│      └─2026-11-03-<識別子>-<題名>.md
├─60_Output/
├─90_Wiki/
│  ├─SCHEMA.md
│  ├─index.md
│  ├─log.md                        ← wiki の操作履歴。日次記録とは別
│  ├─sources/
│  ├─entities/
│  ├─concepts/
│  ├─synthesis/
│  ├─indexes/                      ← インデックス分割時
│  ├─graph/
│  ├─.evolution/
│  └─.wiki-cache/
├─91_Raw/
│  ├─<資料スラッグ>.md
│  └─assets/
│      ├─imported/
│      │  └─<資料ID>/
│      │      └─<内容ハッシュ>.<拡張子>
│      └─generated/
│          └─<ページスラッグ>-01.svg
└─A0_Archive/
```

全ディレクトリを初日に作る必要はない。`log` だけを導入した利用者には、設定、テンプレート、`20_Daily` と必要な出力先だけを作る。Wiki の初期化と検索環境の導入は、`wiki` を使うときに行う。

**2．プロジェクトの構成**

作者の「プロジェクトルートの下に、プロジェクト名の info-hive ディレクトリを置く」は、次のように解釈する。外側のプロジェクトルートを `P`、内側の info-hive 作業領域を `W` と区別する。

```text
<プロジェクトルート>/              ← P。親 Git リポジトリ
├─.git/
├─.gitmodules
├─.info-hive.json                  ← W を指す設定【新設案】
├─AGENTS.md
├─CLAUDE.md
├─project-a.code-workspace         ← 任意。コードと資料を並べる入口
├─project-a/                      ← W。プロジェクト名の info-hive 領域
│  ├─.info-hive.json
│  ├─.foam/
│  │  └─templates/
│  │      └─daily-note.md
│  ├─.github/
│  │  └─instructions/
│  ├─.vscode/
│  ├─AGENTS.md
│  ├─CLAUDE.md
│  ├─00_Inbox/
│  ├─10_Assets/
│  ├─20_Daily/
│  │  └─2026/
│  │      └─11/
│  │          └─2026-11-03.md
│  ├─30_Weekly/
│  ├─40_Projects/                 ← この案件内の施策・サブプロジェクト
│  ├─50_Knowledge/
│  │  └─notes/
│  ├─60_Output/
│  ├─70_ADR/
│  │  └─0001-<決定の題名>.md
│  ├─90_Wiki/                     ← 内部構成はグローバルと同じ
│  ├─91_Raw/
│  │  └─assets/
│  │      ├─imported/
│  │      └─generated/
│  └─A0_Archive/
└─80_Code/
   ├─application/                 ← 開発対象のコード。Git サブモジュール
   └─library/                     ← 必要なら別のサブモジュール
```

`70_ADR` は例であり、作者の指示どおり任意の二桁の数字を選べる。`00_Inbox/ADR` は作らない。コードは `W` の外に置き、Wiki や日次記録の走査から構造的に切り離す。

この案では `W` 自身に別の `.git` を作らず、資料を親リポジトリで管理する。コードのサブモジュールは独立した履歴を持ち、親はそのコミットを記録する。[Git のサブモジュール仕様](https://git-scm.com/docs/gitsubmodules)

**3．各ディレクトリの責任と命名**

表中の `/log:*` は提案中のコマンドであり、実装済みとは扱わない。`memo`、`issue`、`note`、`init` の最終的な名前も未決である。既存の調査案は `/log:*` に読み替えている。[R3、R4]

| 場所 | 役割・正本 | 主に書く人・コマンド | 命名 |
|---|---|---|---|
| `00_Inbox` | 日付ノートに収まらない未整理の文書・受領物 | 人。初版では自動振り分けしない | 新規メモは `YYYY-MM-DD-<識別子>-<題名>.md`。受領物は元の名前を保持し、衝突時に識別子を付ける |
| `10_Assets` | 日次記録、手書きノート、成果物の添付。Wiki 用画像を入れない | 人、依頼を受けたエージェント | `YYYY/MM/<識別子>-<説明>.<拡張子>` |
| `20_Daily` | 予定、タスク、作業メモ、問題・突発事項、メモ、ふりかえり | 人・Foam。`/log:memo`、`start`、`stop`、`todo`、`issue`、`plan`、`close`、`tidy` | `YYYY/MM/YYYY-MM-DD.md` |
| `30_Weekly` | 期間をまたぐ見直し。日次記録の代替ではない | 人、`/log:review --week` | `YYYY/YYYY-MM-DD-weekly.md`。日付は週の月曜日 |
| `40_Projects` | 案件の目的、進め方、関連資料への入口 | 人、明示的に依頼されたエージェント | `<案件ID>/<案件ID>-overview.md` など。案件名変更でも ID は維持 |
| `50_Knowledge/notes` | 日次記録から取り出し、人が編集するノートの正本 | `/log:note` が下書き、人が編集 | `YYYY-MM-DD-<識別子>-<題名>.md`。見出し・title の変更だけで改名しない |
| `60_Output` | 配布・提出・公開のために編集した成果物 | 人、明示的に依頼されたエージェント | `<案件ID>/YYYY-MM-DD-<成果物名>.<拡張子>` |
| `70_ADR` | プロジェクトの設計判断 | 人、判断の記録を依頼されたエージェント | `0001-<題名>.md`。番号は欠番を許し、再採番しない |
| `90_Wiki` | 出典を持つ、LLM が整理した知識 | `/wiki:init`、`/wiki:ingest`、保存を伴う `/wiki:query` など。人も規約に従って編集可能 | 既存の `SCHEMA.md` に従う。Wiki 全体でスラッグを重複させない |
| `91_Raw` | Wiki が取り込んだ資料の保存コピー | 人、`/wiki:ingest` | 原則 `<資料スラッグ>.<拡張子>`。更新版は旧版を上書きせず区別する |
| `91_Raw/assets/imported` | 取り込んだ画像原本 | `/wiki:ingest` | 資料 ID と内容ハッシュで衝突・上書きを避ける【追加設計案】 |
| `91_Raw/assets/generated` | Wiki の説明用に生成した SVG | Wiki を編集するエージェント | `<ページスラッグ>-NN.svg`。元画像とは別の編集規則にする |
| `A0_Archive` | 完了し、通常の整理対象から外した文書 | 人による明示的な移動 | `YYYY/<元の分類>/<元の相対パス>`。移動時に参照を更新 |
| `.foam/templates` | Foam と log が共有するテンプレート | 人、提案する `/log:init` | `daily-note.md` は固定。既存ファイルを上書きしない |
| `.github/instructions` | 対応ツール向けの指示 | 人 | `<用途>.instructions.md`。保存先設定の正本にはしない |
| `.wiki-cache` 等 | 再生成できる索引 | 対応するプラグイン | 既存実装の名前を維持。生成物を Git 管理から除く |

`40_Projects` に日次タスクの別の正本を作らない。プロジェクトの概要やマイルストーンはここに置いてよいが、日々のタスク状態は ADR-0006 の日付ノートに残す。

**4．知識の受け渡し**

```text
20_Daily
    ↓ /log:note で下書きを作る
50_Knowledge/notes
    ↓ 人が編集する
    ↓ 人が /wiki:ingest を指示する
91_Raw に取り込み時点の資料を保存
    ↓
90_Wiki に出典付きの知識を作る
```

取り込み後も、編集用ノートと取り込み時点の資料は役割が違う。ノートを編集しただけでは Wiki を自動更新しない。再取り込み時に新しい資料版と対応付ける。

ノートの添付を Wiki に使う場合も、`10_Assets` のファイルへ依存し続けず、必要な画像を `91_Raw/assets/imported` に保存して取り込む。これにより、人のノートを整理・移動しても Wiki の出典一式を保てる。

## 根拠

**現行の Wiki は、兄弟ディレクトリに分ければ境界を保てる。**

`wiki_lint.py` は指定されたルート以下の `.md` を再帰走査する。固定の除外は `indexes`、`graph`、`raw`、`.evolution` などであり、任意の番号付きディレクトリを除外する機能ではない。被リンクのないページは `type` にかかわらず孤立として報告する。[R8：107–108、155–162、258–281行]

したがって、次の使い分けが必要である。

- 正しい検査対象：`W/90_Wiki`
- 避ける対象：`W` 全体
- 避ける配置：`W/90_Wiki/20_Daily`、`W/90_Wiki/91_Raw`

特に `raw` を `91_Raw` に改名して Wiki 内部に置くと、既存の除外名に一致しない。兄弟配置なら、除外規則を追加せずに対応できる。

また、`index.md` は走査対象から除かれるため、日付ノートをインデックスに並べるだけで孤立判定を解消できるわけではない。[R8：107、155–162、258–280行]

**番号付きの Wiki ルート自体は、現行コードで指定できる。**

`init_wiki.py` は `--wiki-dir` と `--raw-dir` を受け取り、基準ディレクトリとの結合で場所を決める。したがって、将来の初期化時には次の指定が可能である。今回は実行していない。[R7：170–177、260–268行]

```text
python init_wiki.py <Wの絶対パス> --wiki-dir 90_Wiki --raw-dir 91_Raw
```

ただし、**ディレクトリが作れることと、設定がすべて連動することは別である。** テンプレートのコピーではパスの置換を渡しておらず、生成元の `SCHEMA.md.template` は `wiki/`、`raw/`、`raw/assets/` と記載している。初期化後に `SCHEMA.md` とエージェントの指示を選択したパスへ合わせる必要がある。[R7：207–226行、R9：7–11行、R6：13–14行]

**番号は表示順、設定は機械との契約にする。**

`20_Daily` という名前そのものをコードに埋め込むと、作者が仮名を変更しただけで保存先が変わる。そこで、作業領域 `W` の `.info-hive.json` を次のようにする案を推奨する。

```json
{
  "schema_version": 1,
  "kind": "workspace",
  "workspace_id": "<初期化時に作成し、改名では変えないID>",
  "paths": {
    "inbox": "00_Inbox",
    "assets": "10_Assets",
    "daily": "20_Daily",
    "weekly": "30_Weekly",
    "projects": "40_Projects",
    "notes": "50_Knowledge/notes",
    "output": "60_Output",
    "wiki": "90_Wiki",
    "raw": "91_Raw",
    "archive": "A0_Archive"
  },
  "log": {
    "daily_template": ".foam/templates/daily-note.md",
    "timezone": "Asia/Tokyo"
  }
}
```

これは**新規提案であり、現行 wiki が読む設定ではない。** `Asia/Tokyo` も利用者が選ぶ値の例である。相対パスは常にこのファイルのある `W` を基準に解決する。

プロジェクト外側の `P/.info-hive.json` は、作業領域への案内だけを持つ。

```json
{
  "schema_version": 1,
  "kind": "project",
  "workspace": "project-a",
  "log_scope": "global"
}
```

この相対パスの基準は `P`。プロジェクトへの日次記録を明示的に選んだ場合だけ `log_scope` を `project` にする。**ローカルの Wiki が存在するだけで、log の既定をグローバルから変えない。**

作業領域の探索は次のようにする。

| 対象 | 探索・選択の規則 |
|---|---|
| 新しい log | 明示的な作業領域・範囲指定を最優先。次に明示的なプロジェクト設定。未指定ならグローバルの `~/info-hive` |
| プロジェクト候補 | 現在位置から祖先の `.info-hive.json` を探す。サブモジュール内部からでも親 `P` の案内を発見できるようにする。子孫・兄弟の再帰検索はしない |
| 現行 wiki | 現在の優先順位を維持する。ユーザー指定 → 最も近いプロジェクトの指示 → グローバルな指示 → 現在のプロジェクトの `wiki/`。[R5：21行] |
| 新構成と現行 wiki の橋渡し | `CLAUDE.md`／`AGENTS.md` に `W/90_Wiki` を明記し、`SCHEMA.md` に Wiki と Raw の場所を記す。各スクリプトには解決済みのパスを渡す |
| 設定不整合 | 指定先の不存在、不明な設定版、複数の矛盾する指定はエラーにする。別の場所へ黙って切り替えて新しい記録を作らない |

既存 wiki への互換性を保つため、初版の共通設定は log が読み、wiki は既存の指示ファイルを介して利用する。wiki 自身に設定読み込みを足す場合は、ADR-0006 の「wiki のコードは変えない」から独立した変更として判断する。

**Foam との一致は、テンプレートの保存先を照合して保つ。**

`W` を Foam で開き、テンプレートには次のように書く。

```yaml
---
type: daily
foam_template:
  filepath: '/20_Daily/$FOAM_DATE_YEAR/$FOAM_DATE_MONTH/$FOAM_DATE_YEAR-$FOAM_DATE_MONTH-$FOAM_DATE_DATE.md'
---
```

Foam の文書は、`.foam/templates`、`foam_template.filepath`、日付変数による年月の階層化を説明している。相対日付にも対応するため、現在日時の変数ではなく `FOAM_DATE_*` を使う。[Foam のテンプレート仕様](https://github.com/foambubble/foam/blob/main/docs/user/features/templates.md)

log は同じファイルを読み、対応する日付変数を置換し、テンプレート用の `foam_template` を出力から除く。設定の `daily` とテンプレートの保存先が食い違った場合は書き込みを止める。未対応の変数を残したままファイルを作らない。

日付ノートの場所を変える旧設定は非推奨と案内されているため、新構成ではテンプレートを使う。[Foam の日次ノート仕様](https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/daily-notes.md)

**想定する「破綻」と、その対処**

| 想定する場面 | 構成・運用による対処と限界 |
|---|---|
| `20_Daily` を `20_Journal` に改名 | 設定、Foam テンプレート、文書内リンクを一組で更新する。設定だけでは既存リンクは直らない。変更後に旧パス参照の残存を調べる |
| プロジェクト名が変わる | 表示名と作業領域 ID を分ける。物理フォルダー名は必要な場合だけ変更し、外側の案内と指示ファイルを更新する |
| 年をまたぐ | 日付ノートは完全な年月日を持ち、月・年をまたいでも一意。繰り越しは直前の暦日が存在する前提にせず、過去の対象ノートを日付で探す |
| 週が年をまたぐ | 週次ファイルは「週の月曜日の日付」で識別する。暦年と ISO 週年を混ぜて `YYYY-Www` を組み立てる問題を避ける |
| 日付ノートが増える | 1か月の直下は最大31ファイル。10年間なら `365 × 10 ＋ 閏日数 = 3,650 ＋ 2〜3` ファイル、月ディレクトリは `12 × 10 = 120`。ただし年月分割だけで全文検索が高速になるとは主張しない。log は対象期間を絞って読む |
| Wiki が増える | 既存のページ種別とインデックス分割を維持する。目安は約150ページまたは index 約300行。[R5：90–104行] |
| 別のプラグインが増える | 保存先を設定の役割で追加する。番号の空きへ置けるようにし、既存番号を詰め直さない。ほかのプラグインの領域を自動編集しない |
| `50_Knowledge` と Wiki の違いが曖昧になる | 前者は人が編集するノート、後者は明示的に取り込んだ資料に基づく知識と定義する。同じ文書の同期コピーを双方で編集しない |
| Wiki から外部ノートへのリンクが切れる | Wiki 内部は既存の wikilink 規約。Raw・日次記録への参照は適切な相対 Markdown リンクや出典メタデータを使う。現行 lint は外部ファイルへの Markdown リンクを保証しない |
| 古い日次記録を Archive に移して繰り越し元が見つからなくなる | 日次・週次は年が変わっただけでは移動しない。Wiki のページと参照中の Raw も日付だけで移動しない。Archive は主に終了した案件文書・旧成果物に使う |
| 複数端末・Foam と log が同じファイルを更新する | 読み込み時点から変更されていないかを確認し、競合時は止める。再実行で繰り越しを二重追加しない識別が必要。ディレクトリ構成だけでは競合を解決できない |
| コードが Foam の検索に大量に入る | 標準運用では `W` を単独で開く。コードと資料を同時に開く multi-root workspace は別途検証し、テンプレート選択と索引範囲を設定する |
| グローバルとプロジェクトで同じ日付名ができる | 一意性の単位を「作業領域 ID と日付」にする。両方を単一の名前空間として暗黙に集計・リンク解決しない |
| Windows・macOS・Linux を移動する | UTF-8 を明示し、比較時は NFC を使う。大文字小文字だけ違う名前、Windows の予約名・禁止文字・末尾の空白やピリオドを使わない。設定には移設可能な相対パスを使う |

最後の命名制約は Windows の公式仕様と、既存 wiki の日本語命名・NFC 方針に基づく。長いパスへの対応は環境差があるため、階層とスラッグをむやみに長くしない。[Windows の命名仕様](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)、[R8：10–11行、R9：44–50行]

Git 管理では、テンプレート、設定、ノート、原資料、`graph/ontology.yaml` のような編集対象を残す。検索 DB、再生成できるグラフ出力、一時ファイルは除く。`graph/` 全体を除外してオントロジーまで失わないようにする。[R5：「グラフ層」]

なお、`W/.github/instructions` が、外側の Git リポジトリ `P` の `.github` と同じ扱いになるとは仮定しない。GitHub の自動処理を置くなら `P/.github`、Foam のテンプレートは `W/.foam`、Claude Code の入口は各起動範囲の `CLAUDE.md` と役割を分ける。

**既存の決定・実装との食い違い**

| 食い違い | 扱いの提案 |
|---|---|
| ADR-0006 の既定は `~/daily/`、最新の構成案は `~/info-hive/20_Daily` | 最新の作者指示を優先し、新規作成の既定を変更する。既存保存先は設定で維持し、自動移動しない |
| ADR-0006 は `<保存先>/notes/`、本案は `50_Knowledge/notes/` | **作者の判断が必要な変更。** `notes/` という編集段階を維持し、配置を設定可能にする。承認前は互換案の `20_Daily/notes/` も利用できるようにする |
| ADR-0005 は生成 SVG を `wiki/assets/` に置く | 最新指示の「Wiki 用画像は `RAW_ROOT/assets`」を広く解釈し、生成 SVG も `91_Raw/assets/generated` に置く。ADR-0005 の保存先と将来の配信設計を改訂する |
| Raw に生成図を入れると「原資料」の意味が崩れる | `imported` と `generated` を分け、前者は保存原本、後者は編集可能な生成物と明記する。Raw 全体を一律に不変と扱わない |
| `init_wiki.py` は `wiki/assets` をまだ作らない | ADR-0005 の「実装で直す」項目と現行コードを区別する。今回の新配置へ合わせて実装計画を更新する。[R7：43、199–205行、R2：59行] |
| 現行 wiki は新しい JSON 設定を読まない | 指示ファイルと `SCHEMA.md` による橋渡しで開始する。共通 resolver の導入は別変更とする |
| 二桁接頭辞を内部ディレクトリにも付けたくなる | 適用範囲を **W 直下の利用者向け分類**に限定する。`.foam`、`.github`、`sources`、`graph`、`assets` などの固定名は維持する |
| ADR-0003 のサブモジュールと今回のコード用サブモジュール | 前者はプラグイン開発リポジトリの話、後者は利用者の開発コードの話。利用者の作業領域へプラグイン本体をサブモジュール配置する意味にはしない |

画像リンクはページの場所から相対パスを計算する。例えば `90_Wiki/concepts/構成.md` からなら、次の形になる。

```markdown
![構成の説明](../../91_Raw/assets/generated/構成-01.svg)
```

ADR-0005 の `assets/...` という例を一律に置換するだけでは、ページ階層によってリンクが壊れる。

## 検討した代替案

| 代替案 | 採らなかった理由 |
|---|---|
| すべてを `90_Wiki` に入れる | 日次記録、人の下書き、原資料が lint と検索に混ざる。現在のコードでは番号付きの Raw も自動除外されない |
| グローバルだけ、またはプロジェクトだけに統一する | 作者が両方を選べるようにすると決めている。個人の横断記録と案件固有の記録は、分離したまま選択できる方がよい |
| `20_` や末尾の `_Daily` を探して保存先を決める | 改名、翻訳、重複フォルダーの発生に弱い。複数候補から誤って選ぶと記録が分散する |
| 各プラグインが独自の保存先設定を持つ | Raw・Wiki・ノートの対応を複数箇所で管理し続けることになる。共通の設定契約と、既存 wiki への互換用記述を区別した方が移行しやすい |
| 日次記録を各 `40_Projects/<案件>` に分割する | 一日の作業が案件ごとに分かれ、入力時に分類判断が必要になる。作者が重視する入力の軽さと合わない。[R4：24–28行] |
| `20_Daily/notes` にすべての知識ノートを置く | ADR-0006 への互換性は高いが、日付を持つ記録と編集を続けるノートが混ざる。本案では互換用の選択肢として残す |
| `50_Knowledge` と `90_Wiki` を統合する | 人の編集中のノートまで Wiki の管理対象になる。直接昇格させないという決定を配置でも表すために分ける |
| コードを `40_Projects` の下に置く | 案件文書とコードの探索境界が曖昧になる。Foam の単独フォルダー運用も難しくなる |
| 年度末に Daily・Raw・Wiki を Archive へまとめて移す | 日付リンク、出典、繰り越し探索を毎年修復する必要が生じる。年階層を保ったまま残す方が安定する |
| シンボリックリンクで旧名と新名を併存させる | OS・Git・探索処理によって扱いが異なり、二重走査の原因にもなる。標準構成の前提にはしない |

## 前提と不確実性

**作者が決める必要がある事項は、次の六点である。**

1. **プロジェクトの内外構造**  
   本案は `P/project-a/` を info-hive 領域、`P/80_Code/*` をコード用サブモジュールと解釈した。作者の文言だけでは、コードをその内側に置く意図だった可能性も残る。

2. **`notes/` の正式な場所**  
   推奨は `50_Knowledge/notes/`。ADR-0006 の保存先との関係を改訂する必要がある。`50_Knowledge` は人が編集する知識、`90_Wiki` は取り込み後の知識、という区分を採るかも合わせて決める。

3. **「Wiki 用の画像」の範囲**  
   本案はダウンロード画像と生成 SVG の両方を含むと解釈した。ダウンロード画像だけを指すなら、生成 SVG は ADR-0005 の `90_Wiki/assets` を維持する案になる。

4. **「一日一ファイル」の単位**  
   本案は一作業領域・一日につき一ファイルとする。グローバルとプロジェクトの両方に同日のファイルは存在し得る。一人につき一日一ファイルを厳密に求めるなら、その日は記録先を一つに固定する運用が必要である。

5. **日付・時間と繰り越しの規則**  
   タイムゾーン、日付を切り替える時刻、午前零時をまたぐ作業、休業日を挟んだ繰り越しを決める。本案の初期値は「利用者が選ぶタイムゾーンの午前零時で日付を区切る」。深夜作業は日付境界で行を分けると、既存の `HH:MM-HH:MM` を維持できる。Foam と log が異なるタイムゾーンを使う場合の一致は別途検証が必要である。

6. **共有範囲と設定契約**  
   プロジェクト資料を親 Git リポジトリで共有してよいか、個人の日誌はグローバルに限るかを決める。また、提案した `.info-hive.json` の形式・探索順・設定の更新責任を、log 実装前に確定する。

補足として、タスクと作業メモを結ぶ識別子、および繰り越しを再実行しても重複しない規則は、ADR-0006 に残る未決事項と関係する。ディレクトリ構成だけでは解決しない。

調査は指定文書と現在の作業ツリーのコード読解による。ビルド、初期化、Foam の実機動作、各 OS での移動試験は行っていない。特に multi-root workspace、画像プレビュー、既存テンプレートとの共存は確認対象として残る。

Foam の指定された `master` のテンプレート文書は取得できなかったため、検索で得られた公式リポジトリの `main` の同文書を参照した。日次ノート文書は指定 URL から取得した。文書の取得元が異なるため、実装時には使用する Foam の版に合わせて確認する必要がある。

## 参照

ローカル資料の行番号は、今回読んだ作業ツリーに対応する。以下の SKILL.md は **wiki の仕様資料として読んだもの**であり、今回の調査に Agent Skill として適用したものではない。

- **R1**：[AGENTS.md](C:/Works/info-hive-dev/AGENTS.md:7)  
  7–17行：開発リポジトリの役割。36–39行：日本語・機械可読文字列・UTF-8。
- **R2**：[ADR-0005](C:/Works/info-hive-dev/docs/adr/0005-wiki-figures-use-mermaid-and-svg.md:22)  
  22–34行：図と画像の保存先。56–65行：未実装の変更と browse の見直し条件。
- **R3**：[ADR-0006](C:/Works/info-hive-dev/docs/adr/0006-daily-journal-is-separate-plugin.md:25)  
  25–42行：確定した保存先、テンプレート、記録形式、notes。107–124行：実装上の影響と未決事項。
- **R4**：[方法論レポート](C:/Works/info-hive-dev/docs/research/daily-journal-methodology-options.md:20)  
  20–28行：推奨と入力の軽さ。278–350行：決定後の形式・コマンド案。380–409行：確定事項と限界。
- **R5**：[wiki の SKILL.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md:21)  
  21–23行：探索順。41–53行：グラフと正本。55–104行：保存範囲・構成・拡張。108–128行：初期化と取り込み。
- **R6**：[commands/init.md](C:/Works/info-hive-dev/info-hive-wiki/commands/init.md:10)  
  10–15行：既定パス、初期化、SCHEMA と指示ファイルの設定。
- **R7**：[init_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:170)  
  43行：内部ディレクトリ。170–226行：パス結合、Raw の assets、テンプレートコピー。260–268行：引数。
- **R8**：[wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:107)  
  81–104行：リンク解決。107–108行：除外。155–199行：走査。243–290行：スラッグ重複、孤立、リンク切れ。
- **R9**：[SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template:7)  
  7–20行：保存先とページ種別。44–65行：命名と必須項目。
- [エージェントのメモリとの連携](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/agent-memory-integration.md:24)  
  「正本の定型文」「wiki の構成が変わったとき」「複数のプロジェクト」。
- [ADR-0003](C:/Works/info-hive-dev/docs/adr/0003-split-marketplace-repo.md:14)  
  「決定」：プラグインとマーケットプレイスの独立、開発側のサブモジュール。
- [決定行列レポート](C:/Works/info-hive-dev/docs/research/daily-journal-decision-matrix.md:190)  
  190–205行：別プラグインと Wiki への影響。287–319行：段階導入と採点の限界。点数は実測値として扱っていない。
- [移植計画](C:/Works/info-hive-dev/docs/porting-plan.html:461)  
  「変えてはいけないもの」、方針 B・D、P5：固定名、英語キー、日本語スラッグと NFC。
- [Foam：テンプレート](https://github.com/foambubble/foam/blob/main/docs/user/features/templates.md)  
  「Special templates」「Markdown templates」「Metadata」「filepath attribute」。
- [Foam：日次ノート](https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/daily-notes.md)  
  「Daily Note Templates」「Configuration」。
- [Git：gitsubmodules](https://git-scm.com/docs/gitsubmodules)  
  「DESCRIPTION」：独立した履歴と、親が保持するコミット参照。
- [Microsoft：ファイル・パス・名前空間の命名](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)  
  「Naming Conventions」「Maximum Path Length Limitation」。

使用した MCP サーバー: node_repl  
使用した Agent Skills: なし


## 相互レビュー

### エージェント A

## エージェント B のレビュー

### 長所
- 作者のツリーと決定に最も忠実です。`90_Wiki` と `91_Raw` を同じ階層に並べ、モデルが書く svg を ADR-0005 どおり `90_Wiki/assets/` に残し、取り込んだ画像を `91_Raw/assets/<slug>/` に置いています。そのため、既存の ADR との衝突がいちばん少なくなっています。
- `.foam` をプロジェクトの内側の作業領域 `<プロジェクト名>/` に置いています。こうすると、グローバルとプロジェクトで同じテンプレート（`filepath: '/20_Daily/...'`）を使え、Foam がコードのサブモジュールを索引に入れずに済みます。私の案（`.foam` をプロジェクトルートに置く）より優れています。
- Foam のマルチルートで `filepath` がどのフォルダーに解決されるかを、具体的な失敗例で示しています。「`/info-hive/20_Daily/...` を単一ルートで使うと `~/info-hive/info-hive/20_Daily/` ができる」という例です。マルチルートの仕様を読み込んだうえでの分析です。
- `$FOAM_PREVIOUS_DAILY_NOTE` は数値の年月日のパスを前提にしているので、日付ノートのファイル名を短くできない、と指摘しています。私の案にはない根拠です。
- `91_Raw` を改名すると、ソースページの `raw:` が切れることを弱点として明記しています。そのうえで、`9x` を改名しない番号とする規則を提案しています。
- `.github/instructions` をプロジェクトの内側に置いても、Copilot に読まれない可能性を指摘しています。

### 短所
- **作業領域の探し方に穴があります。** 「現在のディレクトリから Git の根まで上にたどり」とありますが、コードのサブモジュールの中で起動すると、Git の根はサブモジュールのルートになり、プロジェクトルートまで上れません。その結果、`<プロジェクト名>/info-hive.yaml` は見つからず、黙ってグローバルに書きます。B 自身が「cwd がコードのサブモジュールの中であることが多い」と書いているので、この手順はその前提と矛盾します。C と D は、まさにこの点を避ける設計にしています。
- 設定を YAML にしています。YAML は標準ライブラリで読めないので、`log` のスクリプトに PyYAML（`uv` の環境）が要ります。B はこの費用に触れていません。
- 「1 段下の `./*/info-hive.yaml` も探す」規則は、候補が複数見つかる場面を増やします。曖昧なら聞くとしていますが、毎回聞かれると入力の軽さを損ないます。
- Foam の除外設定は記憶で `foam.files.ignore` と書いています。この設定は非推奨で、今は `foam.files.exclude` です。既定に `**/.foam/**` が入るという記憶も、実際の既定値と合いません（下の「検証した事実」）。
- 週番号の計算式「310 ÷ 7 = 44.3 なので W45」は、結果は正しいものの式が雑です。正しくは (310 − 1) // 7 + 1 = 45 です。
- 引用した行番号の一部が、現在の作業ツリーとずれています（下の「検証した事実」）。

### 検証した事実
- `init_wiki.py` の `wiki = project_root / wiki_dir`：B は L166〜167 としていますが、現在は L176〜177 です。`raw/assets` の作成は B の L191 に対して L200 です。中身は一致し、行番号はずれています。
- `wiki_search.py` の走査と除外：B は L300〜304 としていますが、現在は L284 と L288 です。除外の集合 `{"indexes", "graph", "raw", ".wiki-cache", ".evolution"}` は一致します。
- `SKILL.md` L94 の、150 ページでインデックスを分割する規律：一致します。
- `page-conventions.md` L83〜89 のスラッグの規則：一致します。
- Foam のマルチルートの文書の「If no folder has that name, the path starts from the first folder」：一致します。subagent で原文を取得して確かめました。
- `$FOAM_PREVIOUS_DAILY_NOTE` の「That path has to spell out the year, month and day in numbers」：一致します。ただし、原文は `$FOAM_TITLE` をパスに使ってもよいとしています。
- `foam.files.ignore`：食い違います。Foam 0.47.0 の package.json では `"deprecationMessage": "Use 'foam.files.exclude' instead."` となっています。`foam.files.exclude` の既定値は 22 個の glob で、`**/.foam/**` は含まれません。
- ADR-0005 の `wiki/assets/` を `init_wiki.py` がまだ作らないこと：一致します。`SUBDIRS` に `assets` はありません（L43）。

## エージェント C のレビュー

### 長所
- **Foam の除外設定を正しく書いた唯一の案です。** `foam.files.exclude` を使い、`foam.files.ignore` は非推奨だと述べています。設定の配列を置き換えるときは既定の除外を残すように、という注意も正確です。
- プロジェクトの外側に案内のファイル（`.info-hive/project.json`）を、内側に `workspace.json` を置いています。そのうえで、祖先をたどる探索を「最初の `.git` で打ち切らない」と明記しています。サブモジュールの中から起動した場面を正しく扱っています。
- ディレクトリの構成だけでは解決しない問題を挙げています。休日をはさんだ繰り越し（直前に存在するノートから繰り越す）、タイムゾーン、同じ日付ノートへの同時の追記です。実装の前に決めるべき事項として役に立ちます。
- 設定の規則が丁寧です。未知の項目を保存のときに残す、wiki・daily・notes・raw を互いの中に置かない、設定が壊れていたら書き込みを止める、の 3 点です。
- 作者の決定 2 を、モデルが書く svg も含むと読みました。そう読んだことと、ADR-0005 と衝突することを、冒頭と表で明示しています。

### 短所
- **`log` の既定の扱いが、入力の軽さに反します。** `--project` を指定しない限り、プロジェクトの中でも常にグローバルに書く設計です。そのため、プロジェクトに日付ノートを置くと決めた利用者も、毎回フラグを付けることになります。ADR-0006 は入力の軽さを最も重い要件としています（「入力の軽さは要件の中で最も重く見ている」）。C は設定で切り替える案を後から足すとしていますが、最初の設計では負担が残ります。
- 生成した svg を `91_Raw/assets/figures/` に置き、さらに `-v001` のような版の番号を付けます。これにより、raw が「原資料」と「編集する生成物」の 2 つの意味を持ちます。ページの階層によって `../../91_Raw/...` という相対パスが変わり、browse で配信する設計（ADR-0005）にも影響します。版の番号を付けると、svg を描き直すたびに参照を書き換える手間が増えます。C は ADR の改訂が要ることを認めていますが、費用の見積もりはありません。
- `wiki_evolve_loop.py` L419 の、raw の場所の決め打ち（`args.wiki.parent / 'raw'`）を見落としています。`91_Raw` の構成では、ここで `raw/` というディレクトリが勝手にできます。
- `SCHEMA.md.template` の置き場所の欄（`raw/`）を、初期化が置き換えないことにも触れていません。
- `40_Projects` を、グローバルでは外部のプロジェクトへの案内、プロジェクトの中では機能ごとの整理と、範囲によって違う意味で使っています。同じ番号は同じ役割にするほうが、迷いが少なくなります。
- Inbox とノートのファイル名を `YYYYMMDD-HHMMSS-件名` にしています。題名を変えても名前が変わらない利点はありますが、Foam のリンクで `[[20261103-120000-...]]` と書くことになり、人が手で書くには重い名前です。

### 検証した事実
- `foam.files.exclude` が現行で、`foam.files.ignore` が非推奨であること：一致します。Foam 0.47.0 の package.json で確かめました。
- `wiki_lint.py` L243〜256 の、NFC にそろえた名前の重複の検出：一致します（`normalization_collision`）。
- `AGENTS.md` L36〜39 の UTF-8 の方針：一致します（L39）。
- `init_wiki.py` L43 の `SUBDIRS`：一致します。
- 同じ名前のリンクが曖昧なときに Foam が警告を出すこと：確かめられませんでした。wikilinks.md は読んでいません。

## エージェント D のレビュー

### 長所
- **作業領域の見つけ方が、4 案の中で最も丈夫です。** プロジェクト側の設定 `P/.info-hive.json`（`kind: project`、`workspace`、`log_scope`）と、作業領域の設定 `W/.info-hive.json` を分けています。「ローカルに wiki があるだけでは、`log` の既定をグローバルから変えない」とも明記しています。作者の「両方を選べて、既定はグローバル」を、毎回フラグを付けずに表せます。
- 設定とテンプレートの `filepath` が食い違ったら書き込みを止める、としています。2 か所に場所を持つことの危うさに、正しく手当てしています。
- `index.md` は lint の走査から外れるので、インデックスに日付ノートを並べても孤立は消えない、と指摘しています。正しい細部です。
- 初期化で `SCHEMA.md.template` の `wiki/`、`raw/` が置き換えられないことを見つけています。私と同じ発見です。
- 「1 日 1 ファイル」の単位を「作業領域ごとに 1 日 1 ファイル」と明確にしています。グローバルとプロジェクトに同じ日のファイルができうることを、作者が決める事項に挙げています。
- `graph/` をまるごと Git から外すと `ontology.yaml` まで失う、と注意しています。
- コードを `80_Code/` にまとめ、作業領域の外に置いています。名前の衝突と Foam の索引の両方を避けられます。

### 短所
- **週次ノートを「週の月曜日の日付」で名付けると、Foam のテンプレートと合いません。** Foam の Markdown のテンプレートの `FOAM_DATE_*` は、作る日付そのものを表します。水曜に開くと水曜の日付になり、月曜の日付を出すには JavaScript のテンプレートが要ります。Foam の MCP は JavaScript のテンプレートを `untrusted_workspace` として拒みます。ISO 週の名前なら、`FOAM_DATE_WEEK` と `FOAM_DATE_WEEK_YEAR` が使えます。ただし、この 2 つが ISO の週かは確かめていません。
- 取り込んだ画像を `91_Raw/assets/imported/<資料ID>/<内容ハッシュ>.<拡張子>` と名付けると、ADR-0004 の「出現順の連番で保存」と食い違います。D は【追加設計案】と書いていますが、食い違いの表には載せていません。名前をハッシュにすると、本文での出現順も分からなくなります。
- 生成した svg を `91_Raw/assets/generated` に置く点は、C と同じ費用を負います。raw の意味が変わり、相対パスが深さに依存し、browse の設計にも影響します。そのうえで「raw 全体を一律に不変と扱わない」としており、ADR-0004 の「raw の不変性」を部分的に崩します。
- Foam の日付ノートの古い設定が非推奨であることを、daily-notes.md の記述として引いています。実際にはこの文書に記述はなく、非推奨の表示は package.json にあります。事実は正しいのですが、出典が誤っています。
- `wiki_evolve_loop.py` L419 の、raw の決め打ちを見落としています。
- `.github/instructions` をプロジェクト側と作業領域側の両方に置いています。どちらが読まれるのかの整理は、未決のまま残っています。

### 検証した事実
- `foam.openDailyNote.directory`、`filenameFormat`、`fileExtension`、`titleFormat` が非推奨であること：一致します。package.json に「No longer used: daily notes follow the daily note template.」とあります。ただし D が出典とした daily-notes.md には、この記述はありません。
- `index.md` が `SKIP_TOP_LEVEL_FILES` に入っていること：一致します（現在の `wiki_lint.py` L110）。
- `init_wiki.py` L207〜226 の、テンプレートをコピーするときにパスを置き換えないこと：一致します。L226 の `copy_template(src, dst)` は、置き換えの引数なしで呼ばれています。テンプレートの置き場所の欄は `wiki/`、`raw/`、`raw/assets/` のままです。
- `init_wiki.py` L170〜177、L199〜205：一致します（L176〜177、L200）。
- 10 年分の日付ノートの数 3,650 + 2〜3：一致します。2028 年と 2032 年が閏年です。

**4 案に共通する注意**：`info-hive-wiki` の作業ツリーには、`wiki_lint.py`、`wiki_search.py`、`SKILL.md`、`SCHEMA.md.template` などのコミットしていない変更があり、作業の途中で行番号が動いていました。私が最初に引いた `wiki_lint.py` L107〜108、L157 も、今は L110〜111、L142 です。除外の集合と走査の範囲という中身は変わっていないので、4 案の主張は行番号だけがずれています。

## 自分の結論の見直し

結論を一部改めます。

1. **Foam のルートを作業領域の内側に移します。** 元の案では、`.foam`、`.vscode`、`.info-hive/workspace.json` をプロジェクトルートに置いていました。B、C、D はこれらを `<project-id>/` の中に置いています。こうすると次の利点があります。
   - グローバルとプロジェクトで、同じ `filepath: '/20_Daily/...'` のテンプレートを使える。
   - Foam がコードのサブモジュールを索引に入れない。
   - 対応表のパスを `<project-id>/...` と書かずに済む。

   どれも、私の案より破綻しにくい点です。プロジェクトルートには `CLAUDE.md`、`.gitmodules`、`.github/` と、D の案にならって作業領域を指す案内（`.info-hive/` に `kind: project`、`workspace`、`log_scope`）だけを残します。サブモジュールの中から上にたどる探索は、元の案のとおり `.git` で止めず、案内を見つけて作業領域に移ります。
2. **Foam の除外設定を `foam.files.exclude` に直します。** `foam.files.ignore` は非推奨です。既定の 22 個の glob は残し、`91_Raw/**/*`、`90_Wiki/.wiki-cache/**/*`、`90_Wiki/graph/**/*` を足します。
3. **日付ノートのパスを後から変えないことを規則にします。** `$FOAM_PREVIOUS_DAILY_NOTE` は、パスを変える前に書いた日付ノートを見つけられないためです（B の指摘と Foam の文書による）。
4. **未決事項を足します。** C と D が挙げた、タイムゾーン、日をまたぐ作業、休日をはさんだ繰り越し元、同時の追記の 4 つです。

次の点は改めません。

- **`90_Wiki` と `91_Raw` を固定名にすること。** 4 案とも同じ弱点（`raw:` が切れる）を認めています。
- **対応表を JSON にすること。** 標準ライブラリで読めるためです。B の YAML は依存を増やします。
- **週次ノートを ISO 週にすること。** D の月曜日の日付は Foam のテンプレートと合わないためです。
- **svg を `90_Wiki/assets/` に置くこと。** C と D は作者の決定 2 を広く読みましたが、どちらも ADR-0004 と ADR-0005 の改訂という費用を負います。作者の発言は、取り込んだ画像を指すと読むほうが既存の決定と矛盾しません。ただし、作者に確かめる事項（U-2）として残します。
- **`wiki_evolve_loop.py` L419 の、raw の決め打ちを食い違いに挙げること。** 4 案のうち、この点を挙げたのは私だけです。現在の作業ツリーでも同じ行にあることを確かめました。

## 順位と確信度

| 順位 | 案 | 理由 |
| --- | --- | --- |
| 1 | エージェント D | 作業領域を探す仕組みが最も丈夫 |
| 2 | 自分 | wiki のコードとの食い違いを最も多く見つけたが、Foam のルートの置き場所と除外設定の名前に誤り |
| 3 | エージェント B | 作者の決定と既存の ADR に最も忠実だが、探索に穴がある |
| 4 | エージェント C | Foam の設定は唯一正確で、運用上の論点も多いが、既定の扱いと svg の置き場所で費用が大きい |

1. **エージェント D**：プロジェクトと作業領域を分け、案内に `log_scope` を書くので、サブモジュールの中からでも見つかり、既定がグローバルであることも保たれます。設定とテンプレートの食い違いも止めます。短所はあります。週次ノートの名前が Foam のテンプレートと合わず、画像をハッシュで名付けるため ADR-0004 と食い違い、svg を raw に置きます。ただし、どれも構成の骨格を変えずに直せます。
2. **自分**：`evolve_loop` の決め打ちと、`SCHEMA` の置き場所の欄が置き換えられないことを見つけました。誤りは見直しの 1 と 2 のとおりです。
3. **エージェント B**：ADR-0005 と作者のツリーに最も忠実で、Foam の分析も深い案です。ただし、Git の根で止まる探索は、サブモジュールの中で起動したときに黙ってグローバルに書く欠陥になります。YAML の依存もあります。
4. **エージェント C**：毎回 `--project` を付ける既定は入力の軽さを損ないます。svg を raw に版の番号付きで置くと、費用が大きくなります。

1 位の理由：破綻の多くは「どこに書くかを取り違える」ことから起きます。D は、その取り違えを構造（案内と作業領域の 2 段の設定、`log_scope`、食い違ったら止める）で防いでいます。残る短所は、名前の付け方と ADR との整合の問題で、骨格を変えずに直せます。

確信度：**中**です。上位 3 案は骨格（番号付きのディレクトリを並べる、対応表、wiki を外に閉じる）がほぼ同じで、差は細部の正しさにあります。svg の置き場所（U-2）を作者がどちらに決めるかで、C と D の評価は上がりえます。

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```

### エージェント B

## エージェント A のレビュー

### 長所
- **現行コードの読み込みが 4 案の中で最も深い。** `wiki_evolve_loop.py` L419 が raw の既定を `args.wiki.parent / 'raw'` と決め打ちしている点、`wiki_graph_extract.py` L402〜407 が `raw:` の値を文字列のまま `raw:<パス>` のノード ID にする点、`91_Raw/experiences/` が必要な点は、他の 3 案（私を含む）が見落とした。`91_Raw` を兄弟に置くと `/wiki:learn` が `~/info-hive/raw/` を勝手に作りうる、という具体的な破綻を示せている。
- **設定ファイルを JSON にした根拠が正しい。** wiki は Python 3.10 以上を前提にし（`retrieval-setup.md` L16）、lint・stats・グラフのクエリは標準ライブラリだけで書く方針（`CONTRIBUTING.md` L34）。`tomllib` は 3.11 から、YAML は PyYAML が要る。私の YAML 案より筋が通る。
- **5 つの規則（表示名と識別子の分離、`90`/`91` は改名しない、4 つのルートを一致させる、ファイル名に完全な日付、境界を wiki の外に引く）が簡潔で、作者が判断しやすい。**
- svg を `90_Wiki/assets/` に残し、作者の決定 2 を「取り込んだ画像」と読んだうえで U-2 として明示している。ADR-0004 の raw 不変性と ADR-0005 の browse の設計に整合する。
- `daily` のキーの有無で「既定はグローバル」を表す案は、プラグインごとの分岐がなく、私の案と同じ結論に独立に至っている。

### 短所
- **プロジェクトでは Foam のルートがプロジェクトルートになり、コードのサブモジュールが Foam の索引に入る。** `.info-hive/`、`.foam/`、`.vscode/` を `<project-root>` に置き、番号付きディレクトリを `<project-id>/` の下に置いているため、Foam は `repos/` 以下の `README.md` なども索引化する。除外設定で防ぐとしているが、サブモジュールを足すたびに設定の保守が要る。C と D と私は `<project-id>/` を Foam のルートにしており、そちらのほうが構造で防げる。
- **テンプレートの `filepath` の例が自分の対応表と食い違う。** 対応表ではプロジェクトの `daily` を `myapp/20_Daily` と書くとしながら、`filepath` の例は `20_Daily/$FOAM_DATE_YEAR/...` のまま。プロジェクトでは `myapp/20_Daily/...` にしないと Foam がプロジェクトルート直下に `20_Daily/` を作る。
- **「日付ノートへのリンクはファイル名だけで解決するので、フォルダーを変えても切れない」は Foam のリンクには当てはまるが、`$FOAM_PREVIOUS_DAILY_NOTE` には当てはまらない。** daily-notes.md は「Notes written before a path change are not found」としている。D はこの点を正しく指摘している。
- `00_Inbox` の資料を `/wiki:ingest` が `91_Raw` に「移す」としているが、`ingest-workflow.md` L11 は「raw にない場合はそこに置く」としか言っておらず、移動の挙動は現行にない。U-10 で未決にはしているが、表の本文では既定の挙動のように読める。
- `repos/` という階層は作者の決定 3 にない追加で、根拠は名前の衝突回避だけ。作者のツリーに `80_Code` のような番号もないので、要確認事項として扱うべきだった。
- 行番号の小さなずれ：`wiki_stats.py` の除外は L56（A は L55）、`SCHEMA.md.template` の `raw_ref` は L134（A は L132）。結論には影響しない。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `wiki_evolve_loop.py` L419 `args.wiki.parent / 'raw'`、L699 のヘルプ「wiki と同じ階層の raw」 | 一致 |
| `wiki_graph_extract.py` L91 の除外に `raw`、L402〜407 で `obj=f"raw:{raw_path}"` | 一致 |
| `init_wiki.py` L263〜264 の `--wiki-dir`／`--raw-dir`、raw/assets の作成 | 一致（assets は L200） |
| `copy_template` に SCHEMA の置換を渡していない | 一致（`template_map` の呼び出しに `substitutions` なし） |
| 要件定義書 D-06 の `project-id` が `[a-z0-9]+(?:-[a-z0-9]+)*` | 一致（L138） |
| Python 3.10 以上、lint・stats は標準ライブラリだけ | 一致（`retrieval-setup.md` L16、`CONTRIBUTING.md` L34。`wiki_lint.py` に yaml の import はない） |
| `91_Raw/experiences/` | 一致（`SCHEMA.md.template` L191「設定した raw ルートの `experiences/`」） |
| 2026 年は ISO 週が 53 週 | 一致（私の計算と同じ） |

## エージェント C のレビュー

### 長所
- **Foam の除外設定を正確に押さえている。** `foam.files.ignore` は非推奨で `foam.files.exclude` が現行、という指摘は package.json（0.47.0）で確認できた。A、D、私はいずれも非推奨のキーを書いていた。
- **`.github/instructions` を外側のリポジトリに置く判断が正しい。** GitHub や Copilot はリポジトリの根の `.github/` を読むので、`<project-id>/.github/` に置いても効かない。私は「効かない可能性」を未確認事項に残しただけで、C は構成で解決している。
- **外側のプロジェクトルートに案内だけの `project.json` を置き、内側の `workspace.json` を正本にする 2 段構えは、サブモジュール内から起動したときの探索を単純にする。** 私の「1 段下を走査する」案より、複数候補の曖昧さがない。
- **ADR-0005 の `![説明](assets/<slug>-NN.svg)` が、`90_Wiki/concepts/` のページからは `concepts/assets/` に解決されてしまう**という指摘は、ADR-0005 自体の不備で、構成とは独立に直す必要がある。D も同じ指摘をしている。
- タイムゾーン、同時編集、`workspace_id`（改名しても変えない ID）、未知の設定項目の保持、といった運用上のリスクを挙げている。私は同時編集とタイムゾーンを落としていた。
- `[[concepts/名前]]` で同名を区別できるという Foam の挙動は、wikilinks.md で確認できた。

### 短所
- **生成 svg を `91_Raw/assets/figures/` に置く判断は、承認済みの 2 つの ADR に反し、根拠が弱い。** ADR-0004 は raw を「取り込み後に変えない」とし、ADR-0005 は svg を `wiki/assets/` に置くと決めている。どちらも作者が 2026年11月3日に承認している。「最新指示を優先」としているが、作者の決定 2 と ADR-0005 は同じ日のもので、どちらが後かは示されていない。さらに C 自身が「raw 全体を一律に不変と扱わない」と raw の意味を変えており、版番号 `-v001` という新しい命名まで足している。作者の一言の解釈のために、承認済みの 2 つの決定と raw の定義を変えるのは費用が大きい。A と私のように「取り込んだ画像」と読み、未決として確認を求めるほうが安全である。
- **`50_Knowledge/notes/` の 2 段構成は作者のツリーにない。** 作者は `50_Knowledge` を直下に置いている。`notes/` を残す意図は ADR-0006 との連続性だろうが、`50_Knowledge` の直下に他に何を置くのかが示されていない。
- `00_Inbox` と `50_Knowledge` の命名を `YYYYMMDD-HHMMSS-件名.md` にしているが、秒まで含む名前は人が書くには重く、ADR-0006 が最も重く見る「入力の軽さ」と合わない。wiki のスラッグ規則（`page-conventions.md` L83〜89）とも別の体系になる。
- `--project` を付けないと常にグローバルに書く設計は、作者の「既定はグローバル」を忠実に守る一方で、プロジェクトの作業領域にいても毎回フラグが要る。設定で切り替えられる A・D・私の案と比べて、入力の負担が増える。
- 「Foam の索引除外は `foam.files.exclude`」の根拠に package.json の行番号 L742 を挙げているが、行番号は版で変わるので、設定名だけを根拠にしたほうがよい。
- 週次を ISO 週にしているが、ISO 週年のディレクトリにする点は A と同じで、暦年と混ぜない注意書きがあるのはよい。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `foam.files.ignore` は非推奨、`foam.files.exclude` が現行 | 一致（package.json 0.47.0 に `deprecationMessage` あり。`exclude` の既定は 22 個の glob） |
| Foam は `[[folder/filename]]` の識別子リンクで同名を区別できる | 一致（wikilinks.md「Identifier links」「Foam picks the shortest unambiguous form」） |
| `wiki_lint.py` L243〜256 に NFC の重複検出 | 一致（`normalization_collision` のフラグ） |
| ADR-0005 の参照 `assets/<slug>-NN.svg` がページ相対では解決しない | 一致（ADR-0005 L27 の書き方。ページは `wiki/concepts/` などに置かれる） |
| `SCHEMA.md.template` L64 に source ページの `raw` | 一致 |
| 作者の決定 2 が ADR-0005 より後 | 確かめられず（両方とも 2026年11月3日） |

## エージェント D のレビュー

### 長所
- **`index.md` からのリンクは被リンクに数えられない、という指摘が正確。** `wiki_lint.py` は `index.md` を `SKIP_TOP_LEVEL_FILES`（L107）で走査から外し、被リンクは走査したページの本文からだけ集める（L247〜）。日付ノートをインデックスに並べても孤立は消えない、という帰結も正しい。
- **`$FOAM_PREVIOUS_DAILY_NOTE` がテンプレートのパスの型に依存するため、古い年を `A0_Archive` に動かすと繰り越し元が見つからなくなる**、という破綻を具体的に挙げている。A と私は「古い年の daily は動かしてよい」寄りで、D のほうが慎重で正しい。
- **「一意性の単位を作業領域 ID と日付にする」**という整理で、グローバルとプロジェクトに同じ `2026-11-03.md` があることを明示的に許している。私は Foam のフォルダー名の違いで済ませていたが、`log` の集計を考えるとこの定義が要る。
- 外側 `P/.info-hive.json` に `log_scope` を持たせる案は、「ローカルの wiki があるだけで log の既定を変えない」という作者の決定を守りつつ、プロジェクトごとに切り替えられる。C の毎回 `--project` より軽い。
- `graph/` 全体を Git から除外して `ontology.yaml` まで失わないよう注意している点は、既存の `graph_gitignore.template`（`graph.sqlite` と `graph.graphml` だけ無視）と合っている。
- 日付の切り替え時刻、深夜をまたぐ作業、休業日を挟む繰り越しなど、`log` の実装で必ず決める事項を未決として列挙している。

### 短所
- **生成 svg を `91_Raw/assets/generated/` に置く判断は C と同じ問題を持つ。** ADR-0004 と ADR-0005 に反し、D 自身が「Raw 全体を一律に不変と扱わない」と raw の定義を変えている。さらに `imported/<資料ID>/<内容ハッシュ>.<拡張子>` という命名は、ADR-0004 が決めた「出現順の連番、元の URL は title 属性」と異なる。承認済みの ADR を、今回の課題（ディレクトリ構成）に必要のない範囲まで変えている。
- **`80_Code/` を外側 `P` に番号付きで置くのは、番号の体系を 2 つの階層に分散させる。** D 自身が「適用範囲を W 直下の利用者向け分類に限定する」と書いており、`80_Code` はその規則に反する。作者の決定 3 は「サブモジュールとして配置する」とだけ言っており、専用の番号ディレクトリは作者の指示にない。
- **週次を「週の月曜日の日付」で名付ける案は、Foam の `FOAM_DATE_WEEK`／`FOAM_DATE_WEEK_YEAR` を使えなくする。** ISO 週の混乱を避ける意図は分かるが、ディレクトリを `YYYY/` の暦年にしているので、2026-12-28 の週は `2026/` に入り、2027-01-04 の週は `2027/` に入る。これは ISO 週年と同じ分け方であり、ISO 週年を避けた利点がない。
- 「日付ノートの場所を変える旧設定は非推奨と案内されている」の根拠に daily-notes.md を挙げているが、daily-notes.md に「deprecated」の語はない。主張自体は package.json の `deprecationMessage` で正しいので、引用元の誤りである。
- 「Foam の指定された master のテンプレート文書は取得できなかった」としているが、私の取得では 200 で読めた。環境の問題と思われるが、結果として `main` の文書を代わりに読んでおり、指定された文書を読んだとは言えない。
- `50_Knowledge/notes/` の 2 段構成、`YYYY-MM-DD-<識別子>-<題名>.md` という命名は C と同じく作者のツリーより重い。
- 文量が多く、`log` の実装仕様（排他、再実行の冪等性、タイムゾーン）にまで踏み込んでいる。作者が今決めるべきディレクトリ構成と、後で設計書で決める事項の区別が薄い。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `index.md` は走査対象外で、被リンクに数えられない | 一致（`SKIP_TOP_LEVEL_FILES` L107、`collect_pages` L159） |
| `$FOAM_PREVIOUS_DAILY_NOTE` はパスの型に依存し、パス変更前のノートは見つからない | 一致（daily-notes.md） |
| `foam.openDailyNote.directory` などは非推奨 | 一致（package.json。ただし daily-notes.md には書かれていない） |
| `init_wiki.py` はテンプレートのコピーでパスの置換を渡さない | 一致 |
| `SCHEMA.md.template` L7〜11 が `wiki/`、`raw/`、`raw/assets/` | 一致 |
| `docs/porting-plan.html` L461「変えてはいけないもの」 | 一致 |
| master の templates.md を取得できない | 食い違い（私の環境では取得できた） |

## 自分の結論の見直し

結論の骨格（根を 1 つに固定、`90_Wiki`/`91_Raw` を兄弟に、プラグインは役割→ディレクトリの対応表を読む、svg は `90_Wiki/assets/` のまま、`.foam` は内側の作業領域に置く）は変えない。A、C、D の 3 案も同じ骨格に独立に至っており、ADR と現行コードに整合する。次の 7 点を改める。

1. **設定ファイルは YAML ではなく JSON にする。** A の根拠のとおり、wiki の lint・stats は標準ライブラリだけで動き、Python 3.10 が下限なので `tomllib` も使えない。名前は `info-hive.json` か A の `.info-hive/workspace.json` のどちらでもよく、作者が決める。
2. **プロジェクトの探索は「1 段下の走査」をやめ、外側のプロジェクトルートに案内ファイルを置く**（C と D の方式）。複数候補の曖昧さがなく、サブモジュール内からも親の案内で見つかる。D の `log_scope` を案内ファイルに持たせる。
3. **`91_Raw/experiences/` を加え、`/wiki:learn`・`/wiki:evolve` が `--raw` を省くと `~/info-hive/raw/` を作る**ことを食い違いの表に加える（A の発見）。`commands/learn.md` と `evolve.md` は「raw ルートを特定する」としか書いておらず、`--raw` を渡す手順が明文化されていない。
4. **Foam の除外設定は `foam.files.exclude`** と書く（C の指摘。私は非推奨の `foam.files.ignore` を記憶で書いていた）。
5. **ADR-0005 の `![説明](assets/<slug>-NN.svg)` はページ相対では解決しない**ので、`../assets/<slug>-NN.svg` のようにページからの相対パスに改める必要がある、という点を食い違いの表に加える（C と D の指摘）。
6. **古い年の `20_Daily` を `A0_Archive` に動かす運用は勧めない**に改める。`$FOAM_PREVIOUS_DAILY_NOTE` の連鎖が切れる（D の指摘）。
7. 未決事項に、**タイムゾーンと日付の切り替え時刻**、**Foam と `log` の同時編集**を加える（C と D）。構成だけでは解決しないが、作業領域の設定に持たせる値として今決めておくほうがよい。

改めない点とその理由：

- **svg は `90_Wiki/assets/` のまま。** C と D は作者の決定 2 を広く読んで raw に入れたが、ADR-0004 の raw 不変性と ADR-0005 の決定（どちらも同日に承認）に反し、raw の定義まで変える必要が出る。作者の一言の解釈としては「取り込んだ画像」のほうが費用が小さい。作者の確認は要る。
- **`.foam/templates` は内側の作業領域に置く。** A はプロジェクトルートに置くが、Foam のルートにコードのサブモジュールが入る。
- **`50_Knowledge` は直下に置く**（作者のツリーのまま）。C と D の `notes/` の 1 段は作者のツリーにない。
- **週次は ISO 週（`YYYY-Www.md`）のまま。** Foam の変数と同じ値を作れる。

## 順位と確信度

| 順位 | 案 | 理由 |
| --- | --- | --- |
| 1 | エージェント A | 現行コードの読み込みが最も深く、`wiki_evolve_loop.py` の raw の決め打ち、`experiences/`、JSON を選ぶ根拠など、実装に直接効く発見がある。承認済みの ADR を変えない。弱点は Foam のルートをプロジェクトルートにしたことと、`filepath` の例の不整合で、どちらも局所的に直せる |
| 2 | 自分（この文書） | 骨格は A と同じで、Foam のマルチルートと単一ルートでの `filepath` の解釈の違い、ISO 週年の計算、ディレクトリ名を ASCII に限る理由など、構成の破綻の場面は具体的に書けた。YAML の選択、1 段下の走査、`foam.files.ignore`、`experiences/` の見落としが A に劣る |
| 3 | エージェント C | Foam と VS Code の設定、`.github` の置き場、外側の案内ファイル、同時編集とタイムゾーンの指摘は 4 案で最も丁寧。ただし生成 svg を raw に入れる判断で承認済みの 2 つの ADR と raw の定義を変えており、作者の一言に対して費用が大きい。命名も重い |
| 4 | エージェント D | C と同じ長所と同じ弱点（svg を raw に、`notes/` の 2 段、重い命名）に加え、`80_Code` で番号の体系を外側に広げ、ADR-0004 の画像の命名まで変えている。`index.md` と `$FOAM_PREVIOUS_DAILY_NOTE` の指摘は正確で価値がある |

確信度は**中**。A と自分の差は小さく、Foam のルートをどこにするかの一点で A を 2 位に置く判断もありうる。C と D の順位は、svg の置き場の解釈を作者がどう確認するかで入れ替わりうるが、どちらも承認済みの ADR の変更を伴う点で A と自分より下に置く判断は変わらない。

使用した MCP サーバー: なし
使用した Agent Skills: なし

### エージェント C

## エージェント A のレビュー

**A は既存コードの互換性調査が最も充実している。採用案に取り込むべき発見が多い一方、改名とリンクについての保証は修正が必要である。**

### 長所

- **初期化以外の処理まで調べている。** `wiki_evolve_loop.py` の raw 既定値の決め打ちと、`SCHEMA.md` のパスが初期化引数に連動しない点は重要である。私の案では、この二点の確認が不足していた。
- **コードと資料を同じウィンドウで開く運用を具体化している。** 外側を Foam のルートにする案には、コードを別ウィンドウで開かずに済む利点がある。内側だけを開く案より常に劣るわけではない。
- **既存の命名要件を拾っている。** Project Wiki の `<project-id>--<topic-slug>.md` を取り入れており、複数 Wiki を同時に開く際の衝突対策が具体的である。
- **原資料と生成 SVG を区別している。** 生成図を raw に置くことで生じる意味の変更を指摘しており、最新指示の解釈を決める材料になる。

### 短所

1. **「ほかのディレクトリは対応表を直すだけで改名できる」は成立しない。**  
   日付テンプレートの `filepath`、画像の相対リンク、パス付き wikilink、Foam の除外設定などにも旧名が残る。対応表はプラグインの保存先を変更できるが、既存文書の参照を自動修復しない。

2. **「ファイル名だけなら移動してもリンクが切れない」は条件付きである。**  
   Foam が移動先を引き続き索引化し、同名ファイルがなく、リンクが名前による識別子である場合には成立する。しかし、パス付きリンクや通常の Markdown リンクには適用できない。グローバルとプロジェクトには同日のファイルも存在する。

3. **raw の写しに日付を付けるだけでは、資料要約との衝突を解消できない。**  
   現行の取り込み手順は raw と資料要約のスラッグを揃える。日付付きに改名しても、その規則を維持すれば両者は同名になる。必要なのは raw の索引除外である。

4. **保存先の選択を `daily` キーの有無に兼用させている。**  
   「プロジェクト保存を利用できること」と「無指定時にプロジェクトへ保存すること」を区別できない。初期化でキーを追加した結果、既定が変わるリスクがある。保存範囲を明示する設定を別に持つほうが分かりやすい。

5. **コピーと移動の方針が統一されていない。**  
   Inbox は「移す」、編集用ノートは「写す」としている。これは採用可能な運用方針だが、既存コマンドの確定動作としては説明できない。Inbox のファイルを参照するリンクへの影響も必要である。

### 検証した事実

行番号は今回の再読時点のもの。成果作成時からの行番号の変化は、誤りとして数えていない。

| 主張 | 結果 |
|---|---|
| `wiki_evolve_loop.py` が兄弟の `raw` を既定にする | **一致。** [wiki_evolve_loop.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:417) L419–420。正確には、`--raw` を省略し、学習成果を公開する処理に到達した場合である。L699 で `--raw` を指定できる |
| 初期化引数が `SCHEMA.md` の保存場所へ反映されない | **一致。** [init_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:207) L207–226 は置換引数なしでコピーする。[SCHEMA.md.template](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template:7) L9–11 は `wiki/`、`raw/` のまま |
| `/wiki:ingest` が Inbox のファイルを移動する | **確かめられず。** [ingest.md](C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:14) は「そこに置く」とし、移動・コピーを確定していない |
| Project Wiki の命名規則が既存要件にある | **一致。** [要件定義書](C:/Works/info-hive-dev/llm-wiki-product-concept-and-requirements-ja.md:32) D-06 と L125–143 に記載されている |
| 2027年1月3日までが `2026-W53`、1月4日から `2027-W01` | **一致。** `date.isocalendar()` で再計算した |
| 移動しても名前だけでリンクを維持できる | **条件付き。** [Foam のリンク仕様](https://github.com/foambubble/foam/blob/main/docs/user/features/wikilinks.md) は名前による識別子とパス参照を区別し、同名ファイルの曖昧性も説明している |

## エージェント B のレビュー

**B は配置と既存要件の対応が読み取りやすい。ただし、保存先探索と Foam のパス解釈に、誤保存につながる具体的な問題がある。**

### 長所

- **役割、書き手、命名、既存仕様との差を一通り整理している。** 設計の出発点として必要な情報が揃っている。
- **編集用ノートと取り込み時点の写しを区別している。** 元の場所やハッシュを記録し、再取り込みを別版にする提案は、出典を再現するうえで有用である。
- **Project Wiki の命名要件を継承している。** 私の案より、既存の製品要件への接続が明確である。
- **Foam の設定と Git の除外を分けて考えている。** 複数ルートでの設定場所にも触れており、運用上の論点を多く拾っている。

### 短所

1. **探索を「Git の根まで」で止めると、コードのサブモジュールから作業領域を発見できない。**  
   B のツリーでは、知識領域はコードの兄弟にある。サブモジュール内から、その Git ルートまでを探しても外側の親には到達しない。この状態でグローバルへ切り替えると、プロジェクト用の入力が別の場所へ保存される。

2. **Foam の単独フォルダー時のパス解釈が公式文書と食い違う。**  
   `/<フォルダー名>/…` は単独で開いても同じフォルダー内を指す、と公式文書に明記されている。「`info-hive/info-hive/` ができる」という説明を根拠に独自の除去処理を設計する必要はない。

3. **古い日付ノートを Archive に移す案が、探索範囲の設計と衝突する。**  
   B は Archive をプラグインの走査から外しつつ、古い日付ノートを移動対象に含める。すると過去の未完了タスク、期間レビュー、Foam の直前ノート探索から外れ得る。末尾で問題を認めているが、推奨する運用を一つに絞れていない。

4. **初期化できることから、wiki 全体の互換性を広く見積もっている。**  
   `--wiki-dir` と `--raw-dir` が使えるのは事実だが、A が発見した `wiki_evolve_loop.py` の既定値までは変わらない。「この配置をそのまま受け付ける」は、処理ごとに範囲を限定すべきである。

5. **追加プラグインの正本を `9x` に置く規則が、提案自身と合わない。**  
   `log` は `20_Daily`、`30_Weekly`、`50_Knowledge` に正本を書く。番号を編集主体に結び付けると、プラグイン追加のたびに例外が必要になる。番号は表示順、編集権限は役割ごとの契約とするほうが拡張しやすい。

### 検証した事実

| 主張 | 結果 |
|---|---|
| `init_wiki.py` が番号付きの Wiki・Raw を作成できる | **一致。** [init_wiki.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:170) L176–177 は指定名を基準ディレクトリへ結合する。ただし全処理の互換性を保証するものではない |
| 外側の知識領域を Git ルートまでの探索で発見できる | **提案ツリーと食い違い。** サブモジュールの Git ルートは外側の親ではない。B の探索手順のままでは親の知識領域に到達しない |
| フォルダー名付き `filepath` は単独で開くと二重になる | **食い違い。** [Foam の複数ルート仕様](https://github.com/foambubble/foam/blob/main/docs/user/recipes/multi-root-workspaces.md) は、同じテンプレートが単独でも使えると明記している |
| 日付ノートを移動しても、ファイル名が同じなら直前ノートを探せる | **一般には成立しない。** [Foam の日付ノート仕様](https://github.com/foambubble/foam/blob/main/docs/user/features/daily-notes.md) は、現在のテンプレートが生成するパスに照合して探すとしている |
| raw の不変性と、再取り込み時の別版保存が必要 | **一致。** [ADR-0004](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:26) L27–28 が規定している |
| 除外設定は `foam.files.ignore` を使う | **現行仕様では修正が必要。** [設定定義](https://github.com/foambubble/foam/blob/main/packages/foam-vscode/package.json#L750) では非推奨で、`foam.files.exclude` が後継。A の未確認事項も同様に解消できる |

## エージェント D のレビュー

**D は保存範囲、編集責任、正本、探索範囲を一貫して分けており、採用の土台として最もまとまっている。互換性の追加調査と画像規約の修正を加えたい。**

### 長所

- **プロジェクト用 Wiki の存在と、日誌の保存先を切り離している。** `log_scope` による明示的な選択は、作者の「log の既定はグローバル」を保ちやすい。
- **外側の案内と内側の保存場所設定を分けている。** 子や兄弟を検索して推測せず、サブモジュール内からも祖先の案内をたどる構造が明確である。
- **改名を一連の移行として扱っている。** 設定だけでなく、テンプレートと既存リンクも更新対象にしており、A より保証の範囲が適切である。
- **ノートの添付も取り込み時に保存する。** 本文だけ raw に写して画像は編集用領域へ依存し続ける、という取り込み漏れを防げる。
- **既存 wiki への段階的な接続を明示している。** 新設定を現行 wiki が読むとは主張せず、指示ファイルと `SCHEMA.md` から始める案は実装費用を把握しやすい。
- **週の月曜日をファイル名にする案は有効な代替である。** ISO 週番号を採る必然性はなく、期間の開始日を正本にする方式にも単純さがある。

### 短所

1. **生成図を同じパスで編集可能にすることで、必要以上に raw の規則を変えている。**  
   最新指示は画像の保存場所を指定しているが、既存画像の上書きを求めてはいない。生成図も別版を追加する方式なら、保存後の不変性を維持できる。可変領域を導入する場合は、バックアップ、古いページとの対応、削除規則も追加で必要になる。

2. **取り込み画像のハッシュ命名は、既存規約からの追加変更である。**  
   ADR-0004 はソースのスラッグ単位・出現順連番を採る。D の `imported/<資料ID>/<ハッシュ>` は合理的な別案だが、本文リンク、取得処理、受け入れ基準への影響を改訂事項として列挙すべきである。

3. **A が発見した raw の既定値の決め打ちを見落としている。**  
   指示ファイルに場所を書くだけでは、スクリプト引数を省略した場合の既定値は変わらない。各入口から `--raw` が渡ることまで確認する必要がある。

4. **Project Wiki の既存命名要件を明示的に継承していない。**  
   作業領域 ID があっても、Foam のリンクがそれを自動で名前空間として扱うわけではない。D-06 のファイル名プレフィックスを保つか、変更する理由を示す必要がある。この見落としは私の案にもある。

### 検証した事実

| 主張 | 結果 |
|---|---|
| Wiki と日付ノートを兄弟配置にすれば、日付ノートは Wiki lint に入らない | **一致。** [wiki_lint.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:140) L140–147 は渡された Wiki ルート内だけを収集する |
| `index.md` に並べるだけでは孤立判定を解消しない | **一致。** 同ファイル L110 で `index.md` を除外し、L245–268 で収集済みページから被リンクを計算する |
| 初期化後に `SCHEMA.md` の場所を合わせる必要がある | **一致。** テンプレートの記載とコピー処理は、A の検証結果のとおり |
| 原資料は保存後に変更しない | **一致。** [ADR-0004](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:28) に明記されている。生成図を可変にする部分は現行規則ではなく追加提案 |
| 取り込み画像の保存規則がハッシュ名である | **現行規約とは食い違い。** [ADR-0004](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:26) と [要件定義書 F-I13](C:/Works/info-hive-dev/llm-wiki-product-concept-and-requirements-ja.md:193) はソース単位の連番を指定する |
| `.github/instructions` が内側にあっても外側と同じように効く | **確かめられず。** D はこの点を保証しておらず、その留保は適切。採用するツールと開き方での確認が残る |

## 自分の結論の見直し

**基本構成は維持するが、「既存コードとの互換性」と「既存要件の継承」を補強する。私の初回案は、初期化処理を確認した範囲から、利用全体への説明を広げすぎていた。**

具体的には次のように改める。

1. **A の互換性調査を採用する。**  
   `wiki_evolve_loop.py` を含む各処理へ、解決済みの `RAW_ROOT` を渡すことを要件に加える。参照ワークフローの実行例には既に `--raw` があるため、「必ず誤作成される」ではなく、**省略時の既定値に依存してはいけない**と記述する。[evolution-workflow.md](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/evolution-workflow.md:44)

2. **初期化の完了条件に設定の整合を加える。**  
   ディレクトリ作成だけでなく、`SCHEMA.md`、指示ファイル、Foam テンプレートが同じルートを指すことを確認する。対応表を追加しても、既存 wiki が自動で参照するとは扱わない。

3. **A・B が拾った D-06 を明記する。**  
   Project Wiki の知識ページは `<project-id>--<topic-slug>.md` を継承する。表示タイトルや編集用ノートの日本語名とは分ける。新しい作業領域 ID は、この既存規則を代替しない。

4. **取り込み画像の配置を、既存規約へ寄せる。**  
   初回案の `assets/sources/<source-slug>/` は追加変更だった。原則として既存の `assets/<source-slug>/` を維持する。生成図の区画を追加する場合は、ソース名との衝突も含めて別途定義する。

5. **D の添付保存と保存範囲設定を取り入れる。**  
   ノートを取り込む際は、必要な添付と参照先も保存する。また、保存先を毎回指定する方式に加え、明示的な `log_scope` を保存できる案は有用である。ただし、ローカル Wiki の作成や `daily` キーの追加だけで既定を変えない。

維持する点は、日付ノート・編集用ノート・Wiki・raw の兄弟配置、改名時の一括移行、日付ノートの年次アーカイブを避けること、生成 SVG を raw 側に置く場合の別版保存である。

画像の配置については、A・B の「取り込み画像だけを指す」という解釈にも根拠がある。**生成図も raw に置く案は最新指示を広く読んだ提案であり、確定済みの意味としては扱わない。** ここは構成の優劣より、作者の指示の範囲を決める論点である。

今回のレビューではファイル変更、ビルド、初期化、Foam の実機試験は行っていない。指定された他エージェントの成果配置先も読んでいない。Foam の検証結果は公式 `main` の文書・設定定義との照合であり、導入済みの拡張の動作保証とは区別する。

## 順位と確信度

順位は、**初回に提出された案**を対象とする。上記のレビュー後の修正は順位に織り込んでいない。

| 順位 | 案 | 主な理由 |
|---|---|---|
| **1位** | **エージェント D** | 保存範囲、探索、改名、正本の扱いが一貫している。サブモジュールからの発見とグローバル既定を両立し、移行の費用も隠していない |
| **2位** | **エージェント A** | 既存実装の落とし穴の発見で最も優れる。ただし、改名・リンク維持の保証と保存範囲の選択規則に修正が必要 |
| **3位** | **自分** | 保存先選択、Foam の現行仕様、改名時の扱いは具体的。ただし、raw の既定値と D-06 の見落としがあり、取り込み画像の規約変更も十分に列挙できていなかった |
| **4位** | **エージェント B** | 整理は有用だが、サブモジュールからの探索失敗と Foam のパス解釈の誤りが保存先に直接影響する |

**確信度は中。** D を土台に A のコード調査を取り込む判断は有力だが、1〜3位は補修可能な差である。最終的な採用判断には、同じ試験用領域で「サブモジュールからの入力」「Foam と log による同日の作成」「改名後の参照」「再取り込み」を確認する必要がある。

使用した MCP サーバー: GitHub（codex_apps）  
使用した Agent Skills: なし

### エージェント D

Foam の公式文書では、フォルダー名を先頭に付けた保存先は、そのフォルダーを単独で開いた場合にも使えると説明されています。この点でエージェント B の説明には食い違いがありました。エージェント C の除外設定名 `foam.files.exclude` と、特別なテンプレートをフォルダー順に選ぶという説明は確認できました。
## エージェント A のレビュー

**現行コードとの互換性調査が強い案である。特に `wiki_evolve_loop.py` の固定パスの発見は、全案へ取り込むべきである。一方、「対応表を直せば改名できる」という説明は保証が強すぎる。**

### 長所

- **初期化以外の処理まで調べている。** `--wiki-dir`、`--raw-dir` だけでは済まない `evolve` の保存先を発見した点は、自分の案より優れている。
- **コードと資料を一つの VS Code ウィンドウで扱いやすい。** 外側を Foam のルートにする構成には、コードの閲覧と記録を行き来しやすい利点がある。
- **日次記録・Wiki・Raw をアーカイブへ移さない。** 保存先を安定させ、出典や繰り越しの参照を維持する方針は妥当。
- **既存の要件定義書を確認している。** Project Wiki の命名に `<project-id>--<topic-slug>.md` を反映した点は、自分の見落としを補っている。

### 短所

1. **「ほかのディレクトリは対応表を直すだけで済む」は誤り。**  
   Daily の改名でも、Foam テンプレートの `filepath`、パス付きリンク、通常の Markdown リンク、添付画像への参照などが残る。名前だけの wikilink が解決できる場合と、すべての参照が保たれることを分ける必要がある。

2. **生成 SVG を Wiki 側に残す解釈は、最新指示を狭く読んでいる。**  
   作者は「Wiki 用の画像」と述べており、取り込み画像だけとは限定していない。ADR-0005 を維持する代替案として提示することはよいが、推奨ツリーは最新指示を優先するか、二案を同じ重みで明示した方がよい。  
   また、ADR-0004 はすでにモデルが作る訳文を Raw に認めている。「生成物だから Raw に置けない」より、**出典・用途の区別と保存後の不変性**を論点にすべきである。

3. **探索の終点と保存範囲の切り替えが不十分。**  
   「ホームの直下まで」では、`C:\Works\...` のようにホーム配下でないプロジェクトの停止条件が決まらない。また、`daily` と `weekly` の項目を別々に省略できると、日次記録はプロジェクト、週次レビューはグローバルという分断が起き得る。log の対象作業領域を先に一つ選ぶ方が明確である。

4. **Inbox から Raw への「移動」は追加仕様である。**  
   現行の取り込み手順は Raw に「置く」としか定めていない。移動を既定にすると、Inbox の原位置を参照するリンクを更新する必要がある。提案として明示し、通常はコピーを推奨したい。

5. **テンプレートの保存先検証が後回しになっている。**  
   `filepath` と `roles.daily` の一致を点検コマンドだけで確かめると、点検前に別の場所へ書けてしまう。書き込み前の必須検証にすべきである。また、単純な文字列の前方一致ではなく、解決後のパスの包含関係を検査する必要がある。

### 検証した事実

| 主張 | 結果 |
|---|---|
| `wiki_evolve_loop.py` は `--raw` 未指定時に Wiki の兄弟の `raw` を使う | **一致。** `publish_learning()` に `getattr(args, 'raw', None) or args.wiki.parent / 'raw'` があり、その場所を作る。`--raw` 引数も存在する。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:417) |
| `init_wiki.py` は SCHEMA 内の保存先を自動置換しない | **一致。** テンプレートを `copy_template(src, dst)` でコピーしており、置換を渡していない。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:207) |
| Project Wiki のページ名にはプロジェクト ID を付ける | **一致。** 要件定義書の D-06 に確定事項として記載。ただし、ASCII 文字種などの詳細は同文書で提案として区別されている。[要件定義書](C:/Works/info-hive-dev/llm-wiki-product-concept-and-requirements-ja.md:24) |
| Raw の参照はパス文字列として保持される | **一致。** グラフ抽出は `raw` の値から `raw:<値>` を生成する。改名時には設定以外の参照更新も必要。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:400) |
| 完全な日付名ならフォルダー変更でリンクは切れない | **条件付き。** Foam の名前によるリンクは一意なら解決できるが、パスによるリンクも存在する。同名ファイルが複数あれば曖昧になる。[Foam のリンク仕様](https://raw.githubusercontent.com/foambubble/foam/main/docs/user/features/wikilinks.md) |
| `/wiki:ingest` は Inbox のファイルを移動する | **確かめられず。** 現行手順は「Raw に置く」と記載し、移動かコピーかを規定していない。[取り込み手順](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:9) |

## エージェント B のレビュー

**分類の境界と役割表は分かりやすい。しかし、サブモジュールからの探索と Foam のパス解釈に、保存先を誤る原因となる問題がある。採用前の修正が最も多い案である。**

### 長所

- **人が編集する素材と Wiki の管理対象を分離している。** `50_Knowledge` と `90_Wiki` の役割が明確で、日次記録を Wiki の検査へ混ぜない。
- **取り込み時点のコピーと、その後も編集するノートを区別している。** 元パス・ハッシュ・別版を記録する案は、再取り込みの設計に役立つ。
- **週次ファイルの ISO 週年を明示している。** 暦年との混同を避ける説明がある。
- **未検証事項を具体的に列挙している。** Foam の中間ディレクトリ作成、指示ファイルの適用範囲、Raw の解決基準など、動作確認が必要な箇所を隠していない。

### 短所

1. **Git の根で探索を止めると、コードのサブモジュールから作業領域を発見できない。**  
   B のツリーでは、info-hive 領域はコードのサブモジュールの兄弟である。サブモジュールの Git ルートまで祖先を調べ、各階層の直下を一段検索しても、外側の親へ到達しない。結果としてグローバルへ切り替わり、意図しない場所へ記録するおそれがある。

2. **Foam の単一ルートでのパス解釈が公式文書と食い違う。**  
   B は `/info-hive/20_Daily/...` が単一ルートでは `info-hive/info-hive/...` を作ると説明している。しかし、公式文書はフォルダー名付きの同じテンプレートを、そのフォルダー単独でも使えるとしている。この誤認を根拠に独自の補正を加えるべきではない。

3. **「既存コードがそのまま受け付ける」「変更は文書だけ」は範囲が広すぎる。**  
   初期化処理が別名を受け付けることは確認できるが、A が発見した `evolve` の既定値は残る。各操作で明示的な Raw の引数が必要かを確認しなければ、別の `raw/` が生まれる。

4. **古い Daily のアーカイブを許す一方、参照と探索の維持方法が不足している。**  
   Foam でリンクが開くことと、log が過去のノートを繰り越し・レビュー対象として発見することは別である。B 自身も直前ノートの連鎖が切れる可能性を認めている。追加の探索仕様を作るより、日次記録は年が変わっても移さない方が単純である。

5. **役割キーの有無によるフォールバックが、誤設定と意図的な選択を区別しない。**  
   `daily` の書き忘れがグローバルへの書き込みになる。明示的にプロジェクトを指定した場合は、設定不足をエラーにすべきである。Daily と Weekly を同じ保存範囲にまとめる規則も必要。

### 検証した事実

| 主張 | 結果 |
|---|---|
| 初期化時に `90_Wiki` と `91_Raw` を指定できる | **一致。** `project_root / wiki_dir` と `project_root / raw_dir` で場所を決める。ただし、初期化以外の全操作の互換性を保証しない。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:170) |
| Wiki の外の Daily と Knowledge は lint に入らない | **一致。** `collect_pages()` は渡された Wiki ルート配下だけを走査する。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:140) |
| Project Wiki の命名は D-06 に従う | **一致。** A と同様、既存の確定事項を拾えている。[要件定義書](C:/Works/info-hive-dev/llm-wiki-product-concept-and-requirements-ja.md:32) |
| フォルダー名付きの `filepath` は単一ルートで二重のフォルダーを作る | **食い違い。** 公式文書の「Create notes in a specific folder」は、単独で開いた場合も同じテンプレートが機能すると明記している。[Foam の複数ルート仕様](https://github.com/foambubble/foam/blob/main/docs/user/recipes/multi-root-workspaces.md) |
| 複数ルートでは `.code-workspace` またはユーザー設定へ Foam の設定を書く | **一致。** 上記公式文書の「Settings」に記載。これは Foam の設定についての説明であり、VS Code のフォルダー設定すべてが無効という意味には広げない |
| `foam.files.ignore` が現在の推奨設定である | **食い違い。** B は記憶として留保しているが、現在の設定定義では非推奨で、`foam.files.exclude` が案内されている。[Foam の設定定義](https://raw.githubusercontent.com/foambubble/foam/main/packages/foam-vscode/package.json) |

## エージェント C のレビュー

**3案の中では最も採用に近い。保存範囲の選択、設定の検証、既存実装と新規提案の区別が明確である。ただし、既存の命名決定と画像配置の移行費用を補う必要がある。**

### 長所

- **明示的なプロジェクト指定の失敗時に、グローバルへ書かない。** 保存先の誤選択を防ぐ規則が最も明確である。
- **作業領域と Git の境界を区別している。** 外側の案内ファイルを使い、サブモジュールの `.git` で探索を止めない。
- **設定ファイルを追加するだけでは動かないことを明記している。** 現行 wiki には指示ファイルと明示パスで接続し、共通設定の自動読込を別変更として扱っている。
- **改名・同時更新・未知の設定項目に配慮している。** 実パスでの包含検証、既存項目の保持、競合時の停止など、ディレクトリ構成を支える実装条件まで示している。
- **Foam の実際の設定とテンプレート優先順位を確認している。** `daily-note.js` の優先と `foam.files.exclude` の指摘は、自分の案に追加したい。
- **最新の画像配置指示を優先し、生成図の旧版も残す。** 過去の Wiki の説明図が、同じパスへの上書きで変わることを避けられる。

### 短所

1. **Project Wiki の確定した命名形式が抜けている。**  
   「Wiki 全体でスラッグを一意にする」だけでは、要件定義書の D-06 を満たさない。`<project-id>--<topic-slug>.md` を追記する必要がある。これは自分の前案にも同じ見落としがあった。

2. **取り込み画像の階層変更と ADR-0004 の差が明記されていない。**  
   C は `assets/sources/<slug>/` を提案しているが、ADR-0004 は `assets/<slug>/` と定めている。最新の作者指示はどちらも許容するため、追加階層は必須ではない。変更するなら、取得処理・リンク・既存画像の移行範囲を示す必要がある。

3. **`evolve` の Raw 既定値を見落としている。**  
   明示パスを渡すという方針自体は正しいが、どの操作で必要かが具体化されていない。A の発見を加えるべきである。

4. **日をまたぐ作業の表現が未完成。**  
   開始日のファイルへ終了を記録する案では、例えば `23:30-01:00` が翌日終了を意味する規則と、集計方法が必要になる。保存ファイルを決めただけでは時刻の曖昧さは解消しない。

5. **版を追加する SVG には管理費用がある。**  
   不変性は長所だが、旧版の参照追跡、未参照ファイルの扱い、採番の競合を設計する必要がある。ディレクトリ構成だけで解決済みとは扱えない。

### 検証した事実

| 主張 | 結果 |
|---|---|
| `foam.files.exclude` が現在の除外設定で、`ignore` は非推奨 | **一致。** 公式の `package.json` に両方と非推奨メッセージが定義されている。[設定定義](https://raw.githubusercontent.com/foambubble/foam/main/packages/foam-vscode/package.json) |
| 複数ルートの特別なテンプレートはフォルダー順で選ばれる | **一致。** `new-note` と `daily-note` は最初に見つかったものを使う。アクティブなファイルに応じて選ばれるとは書かれていない。[公式文書](https://github.com/foambubble/foam/blob/main/docs/user/recipes/multi-root-workspaces.md) |
| Wiki 外からのリンクでは現行 lint の被リンクを増やせない | **一致。** 被リンクは収集済みの Wiki ページから集計される。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:245) |
| `[[concepts/名前]]` は現行 lint のパス解決と合わせられる | **一致。ただし制約あり。** Wiki 相対パスが存在すれば解決するが、別ディレクトリの同一スラッグを許可する機能ではない。重複スラッグの検査は別に残る。[コード](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:84) |
| 生成 SVG を Raw 側へ置くには ADR-0005 の改訂が必要 | **一致。** ADR-0005 は `wiki/assets/<ページのスラッグ>-NN.svg` を指定している。[ADR-0005](C:/Works/info-hive-dev/docs/adr/0005-wiki-figures-use-mermaid-and-svg.md:22) |
| 取り込み画像を `assets/sources/<slug>/` にするのは現行決定のまま | **食い違い。** ADR-0004 は `raw/assets/<ソースのスラッグ>/` と出現順の連番を指定している。新しい提案として改訂範囲に加える必要がある。[ADR-0004](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:18) |
| 対象版の Foam と log が同じ日付ノートを確実に再利用する | **確かめられず。** C 自身も実機確認事項として残しており、その扱いは適切 |

## 自分の結論の見直し

**基本構成は維持し、C の探索・検証規則と、A の互換性調査を取り込む。自分の前案にも、既存決定の見落としと不要な変更があった。**

維持するのは、内側の info-hive 領域を基本の Foam ルートとし、Daily・編集用ノート・Wiki・Raw を兄弟に分ける構成である。単独フォルダー運用を既定にし、複数ルートは必要な場合に明示的に設定する方針も維持する。

具体的には次を改める。

1. **Project Wiki の命名を D-06 に合わせる。**  
   自分の「既存の SCHEMA に従い、一意にする」という記述だけでは不足していた。確定している `<project-id>--<topic-slug>.md` を明記する。ASCII 制限などの詳細案とは区別する。

2. **互換性の説明を、操作ごとの条件に分解する。**  
   `init` の引数だけを根拠に全操作の対応を判断しない。少なくとも `wiki_evolve_loop.py` には解決済みの `--raw` を渡す。通常の運用から別の `raw/` が生成されないことを確認条件に加える。

3. **画像原本のハッシュ命名案を引っ込める。**  
   自分は `assets/imported/<資料ID>/<内容ハッシュ>` を提案したが、ADR-0004 の既存構成を変える費用を十分に示していなかった。取り込み画像は原則 `assets/<source-slug>/連番` を維持する。生成図用の区画を追加する場合は、資料スラッグとの衝突を防ぐ予約名と改訂範囲を定める。

4. **生成 SVG も保存後は別版として更新する。**  
   自分は生成図を編集可能としたが、Raw 配下に置くなら C の版追加方式の方が、取り込み時点の資料を維持する方針と揃う。旧版の削除は別の整理操作にする。

5. **log の保存範囲を、役割キーの有無から推測しない。**  
   グローバルかプロジェクトかを先に一つ選ぶ。明示したプロジェクトの設定が不足・破損していれば停止する。Daily、Weekly、抽出ノートを、それぞれ黙って別の作業領域へ振り分けない。

6. **Foam の具体的な条件を追加する。**  
   `daily-note.js` の存在も確認し、除外には採用版の `foam.files.exclude` を使う。フォルダー名付きの `filepath` は単独でも使用可能という公式仕様を踏まえ、独自のパス補正を増やさない。実機試験では Foam と log の両経路で同じファイルを開くことを確認する。

7. **改名を設定変更だけで済む操作にしない。**  
   設定、テンプレート、本文リンク、frontmatter の `raw`・`sources`、外側の案内をまとめて検査する。通常運用では名前を安定させるが、改名を永久禁止するより、移行手順を用意する。

今回の確認では、前回と `wiki_lint.py` の行番号が変わっていたため、現在の関数本体を読んで検証した。行番号のずれを各案の誤りとは扱っていない。リポジトリの変更、ビルド、動作試験は禁止どおり行っておらず、指定された成果配置先も読んでいない。

## 順位と確信度

順位は、**提出された元の4案**について、保存先を誤る危険、既存決定との整合、検証の具体性、実装費用の明示を基準に判断した。

| 順位 | 案 | 主な理由 |
|---|---|---|
| **1位** | **エージェント C** | 保存範囲の明示、失敗時の停止、Git と作業領域の境界、設定検証が最も明確。Foam の仕様確認も具体的 |
| **2位** | **自分の案** | 改名時の参照更新、作業領域 ID、年月をまたぐ保存、既存 wiki との段階的接続が明確。ただし D-06 と `evolve` の見落とし、画像構成の追加変更がある |
| **3位** | **エージェント A** | 現行コードの互換性調査は最も有用。ただし改名・リンク維持の過大な保証と、保存範囲選択の曖昧さが残る |
| **4位** | **エージェント B** | 分類は分かりやすいが、サブモジュールからの探索と Foam のパス解釈に実害につながる問題がある |

**確信度は中。** C を統合案の土台にする判断は比較的強いが、自分と A の順位は重視点で入れ替わる。現行コードへの即時適用を最優先するなら、A の調査価値はさらに高い。どの案も、実際の保存先選択と Foam・log の同一ファイル利用をまだ動作検証していないため、構成案だけで「破綻しない」とは保証できない。

使用した MCP サーバー: node_repl、GitHub（codex_apps）  
使用した Agent Skills: なし


## 規則

- 票数ではなく根拠の質で優劣を付ける。複数が同じ結論でも、同じ資料を写しただけなら独立に同じ結論へ至ったとは言えない。
- レビューで確かめられた事実（一致、食い違い）を、レビュー前の主張より優先する。
- 正面から割れた論点は根拠で決める。決められないなら、決めるために何が要るかを書く。
- 作者の判断が要ることは、選択肢とそれぞれの帰結を並べる。
- 日本語で書き、結論を先に書く。

## 最終メッセージの形式

```markdown
# <タスクの主題> の総括

## 推奨
（決定を 1〜2 文で）

## 批評で動いたこと
- （他の成果を読んで結論を改めたエージェントと、その内容）
- （最も鋭い反論と、それが決定的だったか）

## 推奨案が残る理由
- （レビューで確かめられた根拠）

## エージェントごとの要約
（エージェント A、エージェント B、エージェント C、エージェント D の結論を 1 段落ずつ。レビューで受けた指摘のうち当たっていたものを添える）

## 残るリスクと未確定事項
- （作者の判断が要ること。選択肢と帰結）

## 記号とモデルの対応
| 記号 | モデル |
| --- | --- |
| A | Claude Opus 5.5（`claude-opus-5-5`） |
| B | Claude Fable 5.1（`claude-fable-5-1`） |
| C | GPT-6.1 Sol（`gpt-6.1-sol`） |
| D | GPT-6 Astra（`gpt-6-astra`） |
```
