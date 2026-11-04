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
