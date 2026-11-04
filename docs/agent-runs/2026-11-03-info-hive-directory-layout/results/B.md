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
