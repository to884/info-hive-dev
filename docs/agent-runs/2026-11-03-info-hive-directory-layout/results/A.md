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
