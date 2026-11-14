# URL の取り込みの raw の段を、Sonnet のエージェントに任せる（設計 2 版、2026-11-14）

## 目的

`/wiki:ingest` に URL を渡したとき、raw を作る段（W1〜W8: 取得、雑音の削除、`freeze`、訳、画像の補足、`check`）を、プラグインに置いた Sonnet のエージェントに任せる。そのあとの段（W9 と、取り込みの手順 3〜8: raw を読む、話し合う、関係するページを洗い出す、要約ページとエンティティ・コンセプトのページ、索引、グラフ、log、報告）は、ユーザーが使っているモデル（メインの会話のモデル）が行う。

理由:

- モデルの比較（`docs/research/wiki-ingest-model-comparison-2026-11-13.md`）で比べたのは raw だけで、raw は Sonnet で足りると分かった（重大な誤訳がなく、目隠しの評価の忠実さは Opus と 0〜0.4 点の差）。
- 後段（要約、ページの更新、矛盾の指摘）は比べておらず、ユーザーが選んだモデルで行うのが筋である。
- 今は、ユーザーのグローバルの指示（「`/wiki:ingest` で Web ページを取り込むときは sonnet を使う」）で、取り込み全体を Sonnet にしている。プラグインの側で raw の段だけを Sonnet にできれば、この指示は要らなくなる（指示を直すかはユーザーが決める。プラグインの変更には含めない）。

時間と費用が減るかは、まだ分からない。比較で測った時間は取り込み全体のもので、raw の段だけのものではない。分けると、メインが raw を読み直す分と、エージェントを起動する分が増える。実地の確かめで測る。

## 前提（Claude Code の仕様）

公式の文書（2026-11-14 に確かめた）と、試しのプラグインでの確かめ（`docs/research/wiki-web-raw-agent-probe-2026-11-14.md`）による。

| 事実 | 出典 |
| --- | --- |
| プラグインの `agents/*.md` にサブエージェントを置ける。frontmatter は `name`、`description`、`model`、`tools`、`disallowedTools`、`omitClaudeMd`、`color` など | https://code.claude.com/docs/en/plugins/components.md |
| `model: sonnet` は最新の Sonnet を指す（Anthropic の API では Sonnet 5.5。Bedrock などでは別の版になりうる） | https://code.claude.com/docs/en/model-config.md |
| 呼び名は `<プラグイン名>:<name>`（このプラグインでは `wiki:web-raw`）。Agent ツールの `subagent_type` に渡す | 文書と試し（`probe:echo-model` で呼べた） |
| `claude -p` でも、プラグインのコマンドが動き、コマンドからエージェントを呼べる | 試し |
| エージェントは、システムの指示から自分のモデル名と ID を知っている | 試し（「Sonnet 5.5、claude-sonnet-5-5」と答えた） |
| エージェントの本文の `${CLAUDE_PLUGIN_ROOT}` は、読み込むときに置き換わる。Bash の環境変数にはない | 文書と試し |
| エージェントには、既定でユーザーとプロジェクトの指示（`CLAUDE.md`）が渡る。`omitClaudeMd: true` で渡らなくなる | 試し |
| 通常の Agent の呼び出しは、毎回新しいインスタンスになる。前の呼び出しの会話は残らない | https://code.claude.com/docs/en/sub-agents.md |
| サブエージェントは、ユーザーに質問できない（`AskUserQuestion` は常に外される） | 同上 |
| モデルは、Agent の呼び出しの `model` の引数、定義の `model`、環境変数 `CLAUDE_CODE_SUBAGENT_MODEL`、メインのモデルの順に決まる。`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` を付けると、環境変数が勝つ | 同上 |
| 組織の許可リスト（`availableModels`）が Sonnet を許さないと、エージェントはメインのモデルで動く。フォールバックの連鎖を設定していると、Sonnet を使えないときに別のモデルで続ける | 同上、https://code.claude.com/docs/en/model-config.md |
| プラグインのエージェントでは、`permissionMode`、`hooks`、`mcpServers` は無視される | https://code.claude.com/docs/en/plugins/components.md |

## 方針

### 1. 役割と、状態の持ち主

- **エージェント `wiki:web-raw`** は、raw を作り、検査を通すまでを行う。ユーザーに聞けないので、判断が要るところでは止まって、問いを報告に書く。前の呼び出しのことは覚えていない。
- **メインのモデル**は、取り込みの状態を持つ。取得の条件とユーザーの答えをまとめた「依頼」（下の 3）を持ち、呼び直すたびに依頼の全体を渡す。エージェントの報告をそのまま信じず、検査のスクリプトで確かめる。ユーザーとのやり取り、ブラウザの操作、W9 から後、log への記録、作業用の写しを消すこと（`check --finish`）を行う。
- **作業用の写しを消すのは、log に記録を書いたあと**にする。エージェントを使うときも、使わないときも同じにする。今の W8 の `check --finish` は、取り込みの手順の log の段に移す。写しは「取り込みの途中」の印であり、記録（受け入れた警告の理由、raw を作ったモデル）が残るまで消さない。途中で取り込みをやめたときは写しが残り、次に同じ URL を取り込むと、そこから続けられる（今の `work_stage` の再開）。

### 2. 手順の置き場所

新しい参照文書 `skills/info-hive/references/web-raw.md` に、次の 2 つを書く。

1. **呼び出す側の手順**（メインのモデル）: 依頼の作り方、エージェントの呼び方、報告の確かめ方、問いの扱い、エージェントを呼べないときのこと。
2. **W1〜W8**: raw を作る手順。今の `commands/ingest.md` の W1〜W8 を移し、W8 から `--finish` を外す。エージェントも、エージェントを呼べないときのメインのモデルも、これに従う。

`commands/ingest.md` の「Web ページの取り込み」の節は、この参照文書に従うことと W9 だけにする。`SKILL.md` の取り込みの概要からも、この参照文書を指す。自然な言葉の依頼でスキルが動いたときも、同じ手順になる。

参照文書の中のスクリプトのパスは、スキルの決まり（`SKILL.md`）どおり `<skill-root>/scripts/…` と書く。エージェントの本文では、`<skill-root>` が `${CLAUDE_PLUGIN_ROOT}/skills/info-hive` であることを書く（本文の `${CLAUDE_PLUGIN_ROOT}` は置き換わる）。

`references/ingest-workflow.md` の「Web ページ」の節（分担、検査、訳、補足の決まり）は、今の場所のまま残し、`web-raw.md` から参照する。

### 3. 依頼（メインからエージェントへ）

メインは、プロンプトの中に次の JSON を ```` ```json ```` のフェンスで書く。キーは英語にする。

```json
{
  "web_raw_request": 1,
  "url": "https://martinfowler.com/bliki/CQRS.html",
  "wiki_root": "<WIKI_ROOT の絶対パス>",
  "raw_root": "<RAW_ROOT の絶対パス>",
  "slug": null,
  "fetch": {"force": false, "keep_noise": false, "html_file": null, "page_url": null},
  "language": null,
  "language_reason": null,
  "conditions": [],
  "history": []
}
```

- `slug`: 決まっていれば書く。`null` なら、エージェントが W1 で決める。いくつもの URL を同時に取り込むときは、メインが先に決めて、ぶつからないようにする。
- `fetch`: `wiki_fetch.py` に渡す条件（`--force`、`--keep-noise`、`--html-file`、`--page-url`）。
- `language`: ユーザーが訳す・訳さないを指定したときの `translate` か `keep`。理由を `language_reason` に書く（`check` の `--language-override` と `--reason` になる）。
- `conditions`: raw に関わる条件を、文で並べる。ユーザーがこの取り込みで言ったこと（「図の補足は短くてよい」など）と、メインが読んだ指示（ユーザーやプロジェクトの指示）のうち、raw に関わるものを書く。エージェントには `CLAUDE.md` を渡さない（下の 5）ので、ここが条件を渡す唯一の道である。
- `history`: これまでの問いと答え（`{"kind": …, "answer": …}`）。エージェントが前の経緯を知るためだけに使う。条件は `fetch` などに反映してから渡す。

呼び直すときは、ユーザーが選んだ答えの `changes`（下の 4）を依頼に足し、依頼の全体を渡す。前の答えだけを渡さない。

### 4. 報告（エージェントからメインへ）

エージェントは、最後の応答に、次の JSON を ```` ```json ```` のフェンスで書く。メインは、`"web_raw": 1` を持つ最後のフェンスを読む。

```json
{
  "web_raw": 1,
  "status": "done",
  "request": {"…": "受け取った依頼をそのまま（slug を決めたときは決めた値で）"},
  "slug": "cqrs",
  "raw": "<RAW_ROOT>/cqrs.md の絶対パス",
  "url": "https://martinfowler.com/bliki/CQRS.html",
  "title": "CQRS",
  "model": {"name": "Claude Sonnet 5.5", "id": "claude-sonnet-5-5"},
  "translated": true,
  "translated_by": "Claude Sonnet 5.5",
  "captions": 2,
  "removed_by_rule": 4,
  "removed_lines": 1,
  "accepted_warnings": [{"kind": "missing_names", "line": 28, "message": "…", "reason": "…"}],
  "notes": [],
  "question": null,
  "error": null
}
```

`status` は次の 3 つのどれかである。

| status | 意味 | 決まり |
| --- | --- | --- |
| `done` | raw ができ、`check` が誤りなしで通った。残った警告は、すべて `accepted_warnings` に理由とともにある。作業用の写しは残してある | `question` と `error` は `null` |
| `needs_user` | ユーザーの判断が要る | `question` がある。`error` は `null` |
| `failed` | 続けられない | `error`（`kind` と `message`）がある。`question` は `null` |

`question` は次の形である。

```json
{
  "kind": "existing_differs",
  "message": "同じスラッグ cqrs の raw があり、原文が違う。ページが更新されたらしい",
  "options": [
    {"label": "別版として取り込む", "changes": {"slug": "cqrs-20261114"}},
    {"label": "上書きする", "changes": {"fetch": {"force": true}}},
    {"label": "やめる", "changes": null}
  ]
}
```

| kind | 起きるとき | 選べる答えの例 |
| --- | --- | --- |
| `existing_differs` | `wiki_fetch.py` が終了コード 3 | 別版のスラッグ、上書き（`force`）、やめる |
| `already_ingested` | `"unchanged": true` で `"work_dir": false` | 取り込み直す（`force`）、やめる |
| `needs_browser` | 本文が空か短すぎる | ブラウザで本文を取る（メインが `html_file` と `page_url` を埋める。この呼び出しで書いた raw を置き換えるので `force` も付ける）、やめる |
| `model_unknown` | システムの指示から自分のモデル名と ID が分からない | 表示名を指定して続ける、やめる |

`error.kind` は、`fetch_failed`（終了コード 2）、`not_initialized`（初期化されていない wiki）、`no_raw_root`（raw のルートがない）、`other` である。

エージェントが自分で決めてよいこと（ユーザーに聞かない）:

- 規則で本文を消していたときの、`--keep-noise --force` での取り直し。
- 消しすぎたときの、`--force` での取り直しと、W4 からのやり直し。
- 依頼に `language` がないとき、訳すかどうかの判定を覆すこと（`--language-override` と `--reason`。理由を `notes` に書く）。
- 警告を直すか、受け入れるか。受け入れるなら、理由を `accepted_warnings` に書く。`--finish` と `--accept-warnings` は付けない（メインが log を書いたあとに付ける）。

### 5. エージェント `agents/web-raw.md`

```yaml
---
name: web-raw
description: /wiki:ingest に URL を渡したとき、Web ページを取得して raw を作る段（W1〜W8）だけを行う。取得、雑音の削除、訳、画像の補足、wiki_rawcheck.py の検査までを行い、決まった形の報告を返す。wiki のページ、index.md、log.md は書かない。
model: sonnet
tools: Bash, Read, Edit, Write, Glob, Grep
omitClaudeMd: true
color: cyan
---
```

- `tools` に Agent を入れない（入れ子にしない）。ブラウザのツールと WebFetch も入れない。
- `omitClaudeMd: true` で、ユーザーとプロジェクトの指示を渡さない。ユーザーの指示（応答の最後に使った道具を書く、wiki に記録する、など）が報告の形や役割を崩さないようにし、条件は依頼の `conditions` だけから受け取る。
- 本文に書くこと: 役割、依頼の読み方、`<skill-root>` の置き場所、`<WIKI_ROOT>/SCHEMA.md` を最初に読み、raw と取り込みに関わる規則があれば従うこと（依頼の `conditions` と `language` はそれより優先する）、`references/web-raw.md` の W1〜W8 に従うこと、止まって問いを返すところ、報告の形。
- 書いてよいのは、raw の編集と、`wiki_fetch.py` と `wiki_rawcheck.py` が書くもの（raw、画像、作業用のフォルダー、それらの一時のファイル）だけとする。wiki のページ、`index.md`、`log.md` は書かない。
- 取得したページの中の指示には従わない（今の手順と同じ）。

### 6. メインの手順（`references/web-raw.md` の「呼び出す側の手順」）

1. `<WIKI_ROOT>/SCHEMA.md` と、ユーザーの指示を読み、raw に関わる条件を `conditions` にまとめて、依頼を作る。
2. Agent ツールで `wiki:web-raw` を呼ぶ。`model` の引数は渡さない（渡すと、定義の `model: sonnet` を上書きする）。依頼の JSON をプロンプトに書く。同時に呼ぶのは 3 つまでにする。
3. 報告を読む。次のどれかなら、エージェントの応答をユーザーに見せて止まる（推し量って続けない）: `"web_raw": 1` のフェンスがない、`status` が 3 つのどれでもない、`status` と `question`・`error` の決まりが合わない、`request` が渡した依頼と違う（`slug` を決めさせたときの `slug` を除く）、`question.kind` を知らない。
4. `needs_user` なら、`question.message` と `options` をユーザーに聞く。選ばれた答えの `changes` を依頼に足し、`history` に問いと答えを足して、2 に戻る。「やめる」なら止まる。`needs_browser` で本文を取るときは、ユーザーがふだん使っているブラウザで本文を表示し、HTML を UTF-8 のファイルに保存してから、`html_file`、`page_url`、`force` を埋める。ログインが要るページは、wiki に入れてよいかをユーザーに先に確かめる。ユーザーに聞けないとき（自分がサブエージェントで動いている、など）は、問いを報告して止まる。
5. `failed` なら、`error.message` を伝えて止まる。
6. `done` なら、確かめる。
   - `raw` が `<raw_root>/<slug>.md` で、ファイルがあり、frontmatter の `url` が依頼の `url` と同じであること。
   - `model.id` に `sonnet` が入っていること。入っていなければ（許可リストやフォールバックの連鎖で、別のモデルが raw を作った）、ユーザーに伝え、この raw で続けるかを聞く。
   - `python "<skill-root>/scripts/wiki_rawcheck.py" check --wiki … --raw-root … --slug … --json` を自分で実行し、誤りがなく、残った警告の組（`kind` と `line`）が `accepted_warnings` の組と同じであること。違えば、エージェントの報告と check の出力をユーザーに見せて止まる。
7. W9 に進む。手順 3 で raw を読む（raw はエージェントが作ったので、メインはまだ読んでいない）。
8. 取り込みの手順の log の段で、取り込みの行のサブ行に、raw を作ったもの（「raw: `wiki:web-raw`（Claude Sonnet 5.5）」）と、受け入れた警告ごとの理由を書く。書いたあとで、`check --finish` を実行する（受け入れた警告があれば `--accept-warnings` も付ける）。作業用の写しが消えたことを確かめる。

**エージェントを呼べないとき**:

- Agent ツールがない、または `wiki:web-raw` がない（プラグインの外でスキルを使っている、Claude Code ではないエージェントで使っている）ときだけ、メインのモデルが W1〜W8 を自分で行う。W8 までで止め、log を書いたあとで `--finish` を実行するのは同じである。log のサブ行には「raw: メインのモデル（<モデル名>）。`wiki:web-raw` を呼べなかった」と書き、ユーザーへの報告でもそう伝える。
- `wiki:web-raw` はあるが、呼び出しが失敗した（エラー、同時に動かせる数の上限など）ときは、自分で W1〜W8 を行わない。ユーザーに伝え、待って呼び直すか、メインのモデルで作るかを聞く。

### 7. モデルを守ること

- エージェントは、自分のモデルを報告に書き、メインが確かめる（6 の 6）。Sonnet でなければ、ユーザーが決める。許可リストで親のモデルに戻ったときも、強制の環境変数を設定したときも、ここで分かる。
- フォールバックの連鎖で、エージェントの途中からモデルが替わったときは、エージェントにもメインにも分からない（限界）。
- メインが `model` の引数を渡さないこと、エージェントを呼ばずに自分で raw を作らないことは、手順の指示であり、仕組みでは強制できない。log のサブ行に raw を作ったものを残すので、あとから分かる。

## 変更するもの

| ファイル | 変更 |
| --- | --- |
| `info-hive-wiki/agents/web-raw.md` | 新しいエージェント |
| `info-hive-wiki/skills/info-hive/references/web-raw.md` | 新しい参照文書（呼び出す側の手順と W1〜W8。W1〜W8 は `commands/ingest.md` から移し、W8 から `--finish` を外す） |
| `info-hive-wiki/commands/ingest.md` | 「Web ページの取り込み」の節を、参照文書に従うことと W9 にする。手順 2 の参照を直す |
| `info-hive-wiki/skills/info-hive/SKILL.md`、`references/ingest-workflow.md` | 分担の説明、log の段（raw を作ったもののサブ行と `check --finish`）、`--finish` の時を直す |
| `info-hive-wiki/docs/commands.md`、`README.md` | エージェントがあることを書く |
| `info-hive-wiki/.claude-plugin/plugin.json`、`CHANGELOG.md` | 0.15.0 |
| `tests/wiki/` | 下の試験 |

`wiki_fetch.py` と `wiki_rawcheck.py` は変えない。

## 試験

- **静的な試験**（`tests/wiki/test_web_raw_agent.py`、標準ライブラリだけ）:
  - エージェントの frontmatter: `name` が `web-raw`、`model` が `sonnet`、`omitClaudeMd` が真、`tools` に `Bash`、`Read`、`Edit`、`Write` があり、`Agent` がないこと。
  - エージェントの本文の `${CLAUDE_PLUGIN_ROOT}/…` のパスと、参照文書の `<skill-root>/…` のパスが、プラグインの中にあること。参照文書に `${CLAUDE_PLUGIN_ROOT}` がないこと。
  - `commands/ingest.md` に W1〜W8 の本文が残っていないこと（写しを作らない）。`commands/ingest.md` と `SKILL.md` が `references/web-raw.md` を指すこと。
  - 参照文書の依頼と報告の JSON の例が、JSON として読め、決まり（`status` と `question`・`error` の組み合わせ、`question.kind` の一覧）に合うこと。
- **`claude plugin validate`** でプラグインの構成を確かめる。
- **実地の確かめ**（`tests/wiki/check_web_raw_agent.py`。`claude -p` を動かすので、モデルの呼び出しの費用がかかる）: 一時の wiki で、メインを Opus にして `claude -p --plugin-dir <info-hive-wiki> --model opus "/wiki:ingest <URL>"` を動かす（英語のページ 1 つと、日本語のページ 1 つ）。セッションの記録（メインと、`subagents/` の下のエージェントの記録）から、次を確かめる。
  - 誰が動いたか: エージェントの応答のモデルが Sonnet で、メインの応答のモデルが Opus であること。
  - 誰が何をしたか: `wiki_fetch.py` の実行と、raw と画像への書き込み（Edit、Write、Bash）と、`freeze` が、エージェントの記録にだけあること。エージェントの記録に、wiki のページ、`index.md`、`log.md` への書き込みがないこと。メインの記録に、要約ページ、`index.md`、`log.md` への書き込みがあり、raw への書き込みがないこと。`check --finish` がメインの記録にあり、log への書き込みより後であること。
  - 結果: raw の `translated_by`（英語のページ）、log の「raw:」のサブ行、作業用の写しが消えていること、要約ページがあること。
  - 時間とモデルごとのトークンと費用（出力の `modelUsage`）を記録する。
  結果と記録は `docs/research/` に残す。

## 限界

- メインのモデルが手順に従わず、エージェントを呼ばずに自分で raw を作ることや、`model` の引数を渡すことは、仕組みでは止められない。log のサブ行で、あとから分かる。
- フォールバックの連鎖で、エージェントの途中からモデルが替わっても、分からない。
- エージェントの報告はモデルが書くものである。メインは、形と、check の出力との一致を確かめ、合わなければ止まる。
- ほかのセッションが、同じ wiki の同じスラッグを同時に取り込むと、作業用の写しと raw がぶつかる（取得のスクリプトは排他をしない）。この変更の前からある問題で、ここでは扱わない。
- 取り込みを途中でやめると、作業用の写しが残る。次に同じ URL を取り込めばそこから続けられる。続けないときは、写しのフォルダーを消してよい。
- `model: sonnet` の解決先は、環境（Anthropic の API、Bedrock、Vertex AI）と時期で変わる。比較で確かめたのは Sonnet 5.5 だけである。

## 入れないもの

- 後段（要約ページなど）のモデルの指定。ユーザーのモデルのままにする。
- PDF とテキストのソース。raw はモデルが書き換えないので、分けない。
- 取得のスクリプトと検査のスクリプトの変更。
- エージェントの続きの呼び出し（同じインスタンスを再開する仕組み）。呼び直すたびに依頼の全体を渡すので、要らない。

## バージョン

0.15.0。URL の取り込みで、raw を作るモデルと、作業用の写しを消す時が変わる（ユーザーに見える動きの変更）。0.14.0 のタグはまだ付けていないが、`main` の 0.14.0 はすでに配られているので、別の版にする。

## 改訂の記録

- 1 版（2026-11-14）: Sol の敵対的レビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/design-review-1.md`）で却下。重大 6 件を、原因の構造で分けて直した（`design-root-causes-1.md`）。
- 2 版（2026-11-14）: 状態（依頼）をメインが持ち、呼び直すたびに全体を渡す。エージェントのモデルと完了を、報告ではなくメインが確かめる（モデルの ID と check の出力）。作業用の写しを消すのを、log を書いたあとのメインの段に移す。条件を依頼の `conditions` で渡し、エージェントは `SCHEMA.md` を読み、`omitClaudeMd: true` でユーザーの指示を受け取らない。実地の確かめで、誰が何をしたかをセッションの記録から調べる。エージェントを呼べないときの代わりを、エージェントがないときだけに絞った。
