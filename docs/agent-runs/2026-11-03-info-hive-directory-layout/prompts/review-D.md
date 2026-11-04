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
