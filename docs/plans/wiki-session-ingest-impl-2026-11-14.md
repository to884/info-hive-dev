# セッションの取り込みの実装の計画（2026年11月14日）

承認済みの[セッションの取り込みの設計](wiki-session-ingest-2026-11-14.md)（5 版目）と [ADR-0020](../adr/0020-session-raw-is-rendered-once-from-decisions.md) を実装する手順である。設計の決定は変えない。設計が書いていない細部を、ここで決める。

| 項目 | 内容 |
| --- | --- |
| 基準 | 親は d3a987c（#103 をマージ済み）、`info-hive-wiki` は 5adb069（#58 をマージ済み、0.15.0、タグなし） |
| ブランチ | 子は `feature/session-ingest`、親は `feature/wiki-session-ingest`。どちらも origin/main から切った |
| 前段の確かめ | `${CLAUDE_SESSION_ID}` の置き換えと、依頼の記録の書かれる時点は、どちらも成り立った（[確かめの記録](../research/wiki-session-id-probe-2026-11-14.md)）。S1 は設計どおり |
| 版 | 0.16.0 の見込み。マージの前に `git fetch` で空いていることを確かめ直す |

## 触るファイル

| リポジトリ | ファイル | 変更 |
| --- | --- | --- |
| 子 | `skills/info-hive/scripts/wiki_session.py`（新規） | `locate`、`list`、`inspect`、`show`、`decide`（`init`、`mark`、`drop`、`list`）、`write`、`verify`、`scan` |
| 子 | `commands/ingest.md` | 手順 2 の分岐と S1〜S10。`${CLAUDE_SESSION_ID}` はこのファイルの本文に書く（参照の文書は Read で読むので置き換わらない） |
| 子 | `skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`SKILL.md` | セッションの raw の frontmatter、記事の構成、根拠の位置（ターンの番号）、言われたことと確かめたことの区別 |
| 子 | `README.md`、`docs/commands.md` | `/wiki:ingest` の引数に `session` を足す |
| 子 | `.claude-plugin/plugin.json`、`CHANGELOG.md` | 0.16.0 |
| 親 | `tests/wiki/test_wiki_session.py`（新規）、`tests/wiki/fixtures/session/`（手で作った JSONL と生成器） | 設計の「試験」の節 |
| 親 | `tests/wiki/test_uninitialized_wiki.py` | 入口の分類 `TAKES_WIKI` と `ReaderEntryTests` の場合に `wiki_session.py` を足す（入口を機械的に数える試験が、ファイルを足した時点で落ちるため） |
| 親 | `tests/wiki/check_commands_mcp.py` | `CLI_NAMES` に `wiki_session.py` を足す |
| 親 | `tests/wiki/check_session_readonly.py`（新規） | Windows で、ジャンクションを経由した Claude Code の Write と Edit が読み取り専用の raw を書き換えられないことを、`claude -p` で確かめる |
| 親 | `tests/wiki/README.md`、`.github/workflows/wiki-mcp.yml` | 試験の一覧と CI の段 |
| 親 | `info-hive-wiki`（サブモジュールの参照） | 子の PR のマージのあと、そのコミットに合わせる |

## 設計が書いていない細部の決め方

### 定数にする一覧

手元の全プロジェクトの記録の構造（[確かめの記録](../research/wiki-session-id-probe-2026-11-14.md)の最後の節）から、次を定数にする。設計書は 1 つのプロジェクトの 17 種類を挙げていたが、全プロジェクトでは 23 種類あった。

- `uuid` のない記録の既知の種類（`KNOWN_UUIDLESS_TYPES`）: 観測した 23 種類。ほかの種類が `uuid` なしで現れたら、読み飛ばしたうえで `unknown_uuidless_type` を出す。
- 文脈の差し込みの `attachment` の種類（`CONTEXT_ATTACHMENT_TYPES`）: 観測した 43 種類から `queued_command` を除いた 42 種類。
- 透過にする `system` の `subtype`: 設計どおり `stop_hook_summary`、`informational`、`api_error` の 3 つ。`model_refusal_fallback` と `turn_duration` は境界になる。

### 印の文

宛先の区分ごとに、次の文を使う。区分は上から順に決める。

| 宛先 | 印の文 |
| --- | --- |
| `origin.kind`（`queued_command` は `attachment.origin.kind`）が `task-notification` | （バックグラウンドの作業の通知。内容は除いた） |
| 同じく `peer` | （ほかのセッションからの伝言。内容は除いた） |
| `isCompactSummary` | （会話の圧縮の要約。内容は除いた） |
| `isMeta` | （スキルの本文などの差し込み。内容は除いた） |
| 上のどれでもない `queued_command` | （キューに入った入力。人の発言と確かめられないので、内容は除いた） |
| `system` の `compact_boundary` | （会話の圧縮の境目） |
| 上のどれでもない `user` | （人の発言でない記録。内容は除いた） |
| それ以外の境界 | （会話でない記録。内容は除いた） |
| 不明 | （返答の対象の記録が範囲にないか、読めない） |
| 中断 I | （ユーザーが中断した） |
| 空になった人の発言 | （人の発言。内容は除いた） |
| 確認で消したターン | （確認で消した） |

返答の宛先がファイルの中で返答より後ろにあるとき（実物の記録では見つかっていない）は、宛先を「不明」として印を置き、`reply_unresolved` を出す（実装の 7 回目のレビューの軽微 1。閉じる側の扱いとして決めた）。種類の値（`type`、`attachment.type`、`subtype`）が文字列でなければ、知らないものとして境界にするか、`uuid` がなければ読み飛ばして `unknown_uuidless_type` を出す。

中断 I は、見出しを `印` にして、上の文を本文にする。宛先が不明の返答の印は、宛先の位置がないので、その返答の最初の記録の位置に置く。不明の宛先は、たどり着いた最後の親の `uuid`（なければその返答の記録の `uuid`）ごとに 1 つの印にする。

### 本文とツールの要約

- 人の発言の本文が `text` のブロックの並びなら、`\n\n` でつないでから、設計の 5 節の 1〜6 を当てる。改行は `\r\n` と `\r` を `\n` にそろえる（raw は LF だけで改行するため）。本文の末尾の改行は除く。
- アシスタントのターンの本文は、`text` のブロックとツールの要約の並びで、`text` の前後は空の行で、続くツールの要約どうしは 1 つの改行で区切る。
- ツールの要約の値は、先に伏せ字をかけてから 120 文字で切る（切ってからかけると、切れた秘密の値が規則に当たらない）。
- 見出しの時刻は `YYYY-MM-DD HH:MM:SS`（`--utc-offset` で直した時刻）にする。読めない時刻は `時刻不明` にする。frontmatter の `started_at` と `ended_at` は、時差つきの ISO 8601 にする。
- 複数の記録をまとめたアシスタントのターンのモデルと時刻は、最初の記録のものにする。

### 自動の伏せ字の規則の細部

- 名前に続く値の規則（`token`、`secret`、`password`、`passwd`、`api_key`、`api-key`、`apikey`、`access_key`、`client_secret`）は、値が 6 文字以上のときだけ当てる。`token: string` のような型の注釈や、短い語の誤検出を減らすためである。ほかの規則には長さの下限を設けない。
- 当てる順は、秘密の鍵の塊、接頭辞の値、JWT、名前に続く値、メールアドレス、ホームのディレクトリである。置き換えた `［伏せ字］` などは、あとの規則に当たらない。

### `decide` の引数

- `decide init --transcript <P> [共通の引数] --wiki <W> --slug <S>` が、`<W>/.wiki-cache/session/<16 進 16 桁>.json` を重ねて書かない形で作り、そのパスを出す（設計の 8 節の置き場所。名前にスラッグを入れないのは、実装の 4 回目のレビューのあとの変更で、作者が承認した）。スラッグは、書く前に `check_slug_value()` で確かめる。wiki が初期化されていなければ、何も書かずに止まる。
- `decide mark` と `decide drop` も `--transcript` と共通の引数を取り、土台を作り直して、決定のファイルの `source_sha256` と `base_sha256` に一致しなければ拒む。
- 決定のファイルを渡すコマンド（`decide mark`、`decide drop`、`show`、`write`、`scan`）では、共通の引数のうち省いたもの（`--tools`、`--keep-reminders`、`--utc-offset`、`--before`、`--session-id`）を決定のファイルから取る。渡した値が決定のファイルと違えば拒む。
- `decide mark --all-turns` は、`--target` を省いてよく、すべてのターンと `cwd` と `git_branch` のすべての一致を足す。
- 決定のファイルは、一時ファイルに書いてから `os.replace` で置く（決定のファイルは一つのセッションだけが書くので、置き換えでよい）。

### raw の行き先の検査の範囲

設計の 9 節の手順 4 の「raw のルートとその途中の階層」は、raw のルートそのものと、wiki の親のディレクトリより下にある raw のルートの祖先とする。wiki の親より上の階層（macOS の `/var` のようなシステムのリンク）は見ない。raw のルートが wiki の親の下になければ、raw のルートそのものだけを見る。

### 判定の置き場所

wiki のパスを取るサブコマンド（`inspect --wiki`、`decide init`、`write`）は、サブコマンドの振り分けより前の 1 か所で `wiki_initialized.require_or_exit()` を呼ぶ。記録を読む前、何かを書く前である。

## 試験の順

制御の差し替えの口を先に作り、それを使う試験を先に書いて、本物の実装と差し替えた実装で、期待どおりに通ることと落ちることを確かめる。

1. 生成器（`fixtures/session/gen_session.py`）と手で作った JSONL を書く。
2. 差し替えの口を持つ骨組みを書く。分類（`classify_record`）、アシスタントのブロックの選び方（`keep_assistant_block`）、raw の公開（`publish_exclusive`）は、モジュールの関数として差し替えられるようにする。サブプロセスでも差し替えられるよう、試験は `-c` で差し替えてから `main()` を呼ぶ小さな駆動を使う。
3. **抜き出しの性質**の試験を書き、骨組みで落ちることを確かめてから、抜き出しを実装して通す。続けて**対照**（3 版目の規則、除くものを並べる方式）で (2) と (1) が落ちることを確かめる。
4. **自己検査**と **`show` の分け方**の試験を書き、`render()` と `show` を実装する。`show` は `sys.stdout.buffer` に書き、試験はバイト列で受ける。
5. **縛り**の試験を書き、`decide` と `show --meta` を実装する。
6. **raw の排他**の試験（スレッドで 200 回、プロセスで数回、公開の前後の例外、リンク、ルートの包含）を書き、対照の `os.replace` で上書きが起きることを確かめてから、`write` を実装する。
7. **読み取り専用と `verify`** の試験を書き、実装する。
8. **`scan`** の試験を書き、実装する。標準入力は UTF-8 として厳密に読み、読めなければ終了コード 1 にする。
9. **ディスクの走査**の試験と、その対照（写しを書く実装）を書く。
10. `test_uninitialized_wiki.py` と `test_python_version.py` を通す。
11. `check_session_readonly.py` と `check_commands_mcp.py` を手元で 1 回ずつ流し、結果を記録する（`claude -p` は Haiku で、回数を少なくする）。
12. 手元の実物の記録で `inspect` と `show --meta` を流し、`reply_unresolved` が 0 件のままであること、印の数、`write` にかかる時間を記録する（コミットしない）。

試験は Python 3.12（`uv run --python 3.12`）と手元の 3.14 の両方で流す。
