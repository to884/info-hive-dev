先ほどのタスクに、あなたを含む 4 体のエージェントが独立して取り組みました。
あなた以外の 3 体の成果を渡します。エージェントは「エージェント A」のように記号で呼び、モデル名は明かしません。
あなたの最終メッセージだけがレビューとして保存されます。

## タスク（再掲）

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


## 他のエージェントの成果

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


## 規則

- 各成果について、長所と短所の両方を書く。自分の案を守るためではなく、相手が優れている点を認めるレビューが役に立つ。
- 短所は、誤った前提、見落とし、リスク、隠れた費用、未検証の主張として具体的に書く。
- リポジトリを読めば確かめられる主張は確かめ、結果（一致、食い違い、確かめられず）を書く。
- `docs\agent-runs\2026-11-03-info-hive-directory-layout` の配下は読まない。
- 日本語で書き、結論を先に書く。

## 最終メッセージの形式

1. `## エージェント X のレビュー`（3 体ぶん）。各節に `### 長所`、`### 短所`、`### 検証した事実` を置く
2. `## 自分の結論の見直し`：他の成果を読んで結論を改めるか。改めるなら何をどう、改めないならなぜ
3. `## 順位と確信度`：自分を含む 4 案の順位、1 位の理由、確信度（高・中・低）
