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
