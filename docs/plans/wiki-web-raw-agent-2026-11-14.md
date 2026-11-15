# URL の取り込みの raw の段を、Sonnet のエージェントに任せる（設計 3 版、2026-11-14）

## 目的と、言えること

`/wiki:ingest` に URL を渡したとき、raw を作る段（W1〜W8: 取得、雑音の削除、`freeze`、訳、画像の補足、`check`）を、既定では、プラグインに置いたエージェント `wiki:web-raw`（定義の `model: sonnet`）に任せる。そのあとの段（W9 と、取り込みの手順 3〜8）は、呼び出す側のモデル（ユーザーが使っているモデル）が行う。

この変更で言えるのは、次のことだけである。

- 手順は、raw の段を `model: sonnet` のエージェントに任せるように書いてある。呼び出す側は、`model` の引数を渡さずにエージェントを呼ぶ。
- 実地の確かめ（下の「試験」）で、メインとエージェントのそれぞれについて、セッションの記録の応答のモデルと、道具の使い方（どのファイルに書いたか、どのスクリプトを実行したか）が、分担のとおりであることを確かめる。

言えないこと:

- どのモデルが文を考えたかは、証明できない。プロンプトや報告を通じて文を受け渡すことは、試験で一部（長い文の並びの一致）を見つけるだけである。
- raw を作ったモデルの記録（`translated_by`、補足の表示名、報告の `model`）は、モデルが自分で書く名前であり、目安である。
- 呼び出す側のモデルが手順に従わず、エージェントを呼ばずに自分で raw を作ることや、`model` の引数を渡すことは、仕組みでは止められない。
- 組織の許可リストやフォールバックの連鎖で、エージェントが Sonnet 以外で動くことがある。

理由:

- モデルの比較（`docs/research/wiki-ingest-model-comparison-2026-11-13.md`）で比べたのは raw だけで、raw は Sonnet で足りると分かった（重大な誤訳がなく、目隠しの評価の忠実さは Opus と 0〜0.4 点の差）。後段は比べておらず、ユーザーが選んだモデルで行うのが筋である。
- 今は、ユーザーのグローバルの指示（「`/wiki:ingest` で Web ページを取り込むときは sonnet を使う」）で、取り込み全体を Sonnet にしている。プラグインの側で raw の段だけを Sonnet にできれば、この指示は要らなくなる（指示を直すかはユーザーが決める）。
- 時間と費用が減るかは、まだ分からない。比較で測った時間は取り込み全体のものである。実地の確かめで測る。

## 前提（Claude Code の仕様）

公式の文書（2026-11-14）と、試しのプラグインでの確かめ（`docs/research/wiki-web-raw-agent-probe-2026-11-14.md`）による。

| 事実 | 出典 |
| --- | --- |
| プラグインの `agents/*.md` にエージェントを置ける。frontmatter は `name`、`description`、`model`、`tools`、`omitClaudeMd`、`color` など | https://code.claude.com/docs/en/plugins/components.md |
| `model: sonnet` は最新の Sonnet を指す（Anthropic の API では Sonnet 5.5。Bedrock などでは別の版になりうる） | https://code.claude.com/docs/en/model-config.md |
| 呼び名は `<プラグイン名>:<name>`（`wiki:web-raw`）。`claude -p` でもプラグインのコマンドが動き、コマンドからエージェントを呼べる | 試し |
| エージェントは、システムの指示から自分のモデル名と ID を知っている。本文の `${CLAUDE_PLUGIN_ROOT}` は置き換わる | 試し |
| `omitClaudeMd: true` で、ユーザーとプロジェクトの指示（`CLAUDE.md`）がエージェントに渡らなくなる | 試し |
| 通常の Agent の呼び出しは、毎回新しいインスタンスになる。エージェントはユーザーに質問できない | https://code.claude.com/docs/en/sub-agents.md |
| モデルは、Agent の呼び出しの `model` の引数、定義の `model`、環境変数、メインのモデルの順に決まる。許可リストやフォールバックの連鎖で変わることがある | 同上 |

## 方針

### 1. 置き場所

- **`skills/info-hive/references/web-raw.md`**（新しい参照文書）: 呼び出す側の手順、報告の形、W1〜W8。W1〜W8 は `commands/ingest.md` から移す。エージェントも、エージェントがないときの呼び出す側も、これに従う。スクリプトのパスは、スキルの決まりどおり `<skill-root>/scripts/…` と書く。
- **`agents/web-raw.md`**（新しいエージェント）: `model: sonnet`、`tools: Bash, Read, Edit, Write, Glob, Grep`（Agent を入れない）、`omitClaudeMd: true`。本文には、役割、依頼の読み方、`<skill-root>` の置き場所（`${CLAUDE_PLUGIN_ROOT}/skills/info-hive`）、`SCHEMA.md` を読むこと、参照文書に従うこと、守ること（ユーザーに聞かない、wiki のページを書かない、`--accept-warnings` を付けない、報告の形）を書く。
- **`commands/ingest.md`**: 「Web ページの取り込み」の節を、参照文書に従うこと、`model` の引数を渡さないこと、W9 だけにする。`SKILL.md` の取り込みの概要からも、参照文書を指す。

### 2. 依頼と報告

依頼（呼び出す側からエージェントへ）は、プロンプトの中の JSON（`web_raw_request: 1`）で、`url`、`wiki_root`、`raw_root`、`slug`、`fetch`（`force`、`keep_noise`、`html_file`、`page_url`）、`language`、`language_reason`、`conditions` を持つ。呼び出す側は、呼ぶたびに依頼の全体を渡す。

- `conditions` には、`SCHEMA.md` とユーザーの指示のうち、raw に関わる条件を文で書く。エージェントには `omitClaudeMd` で `CLAUDE.md` を渡さないので、条件はここからだけ届く。エージェントも、最初に `SCHEMA.md` を読む。

報告（エージェントから呼び出す側へ）は、最後の応答の `web_raw: 1` を持つ最後の JSON のフェンスで、`status` は 4 つのどれかである。

| status | 意味 |
| --- | --- |
| `done` | raw ができ、W8 の `check --finish` で作業用の写しを消した |
| `warnings` | raw はできたが、直さなかった警告が残っている。エージェントは `--accept-warnings` を付けないので、写しは残っている。警告と理由の案、使った `--language-override` を報告する |
| `needs_user` | ユーザーの判断が要る（`existing_differs`、`already_ingested`、`needs_browser`） |
| `failed` | 続けられない（取得の失敗、初期化されていない wiki、raw のルートがない、自分のモデル名が分からない） |

### 3. 呼び出す側の確かめ

- 報告の形が決まりと違う、渡した依頼と `url`・`wiki_root`・`raw_root` が違う、のどれかなら、止まって応答をユーザーに見せる。
- `done`: raw のファイルがあり、frontmatter の `url` が依頼と同じで、作業用のフォルダーがないことを確かめる。作業用のフォルダーを消すのは、`check --finish` が誤りも警告もなく通ったとき（と、`wiki_fetch.py` が新しく取り直すときの作り直し）だけである。
- `warnings`: 呼び出す側が、報告の `language_override` を付けて `check --json` を実行し、誤りがなく、警告の `kind`・`line`・`message` の並びが報告と同じであることを確かめる。理由の案を受け入れられなければ、`conditions` に直し方を足してエージェントを呼び直す。受け入れるなら W9 に進み、log の段で理由を書いてから、`check --finish --accept-warnings`（と、同じ `--language-override`）を実行する。
- `needs_user`: 問いの種類ごとに、呼び出す側が変える依頼の欄を表で決める（汎用の差分の合成はしない）。`existing_differs` は `slug` か `fetch.force`、`already_ingested` は `fetch.force`、`needs_browser` は `fetch.html_file`、`fetch.page_url`、`fetch.force`。
- raw の `translated_by` か補足の表示名に `Sonnet` が入っていなければ（前の途中の取り込みで別のモデルが訳した raw を続けた、など）、ユーザーに伝え、作り直すかを聞く。
- log の段で、取り込みの行のサブ行に、raw の段の分担を書く（「raw: `wiki:web-raw` に任せた（報告したモデル: …）。訳: …、補足: …」）。訳と補足の名前は raw から取る。これは分担の記録であり、作者の証明ではない。

### 4. エージェントがないとき

使えるエージェントの種類に `wiki:web-raw` がないとき（プラグインの外でスキルを使っている、Claude Code ではないエージェントで使っている）だけ、呼び出す側が W1〜W8 を自分で行い、ユーザーにそう伝える。W8 の警告の扱いは 0.14.0 と同じ（理由を log に書いてから `--finish --accept-warnings`）。

プラグインはあるが、呼び出す側に Agent ツールがない（呼び出す側がサブエージェントとして動いている、など）ときも、`wiki:web-raw` は使えるエージェントの種類に出ないので、呼び出す側が自分で行う。これは限界として扱う。

## 変更するもの

| ファイル | 変更 |
| --- | --- |
| `info-hive-wiki/agents/web-raw.md` | 新しいエージェント |
| `info-hive-wiki/skills/info-hive/references/web-raw.md` | 新しい参照文書 |
| `info-hive-wiki/commands/ingest.md` | Web の節を短くし、手順 2 の参照を直す |
| `info-hive-wiki/skills/info-hive/SKILL.md`、`references/ingest-workflow.md` | 分担の説明と、log の段のサブ行 |
| `info-hive-wiki/docs/commands.md`、`README.md` | エージェントがあることを書く |
| `info-hive-wiki/.claude-plugin/plugin.json`、`CHANGELOG.md` | 0.15.0 |
| `tests/wiki/test_web_raw_agent.py`、`tests/wiki/check_web_raw_agent.py` | 下の試験 |

`wiki_fetch.py` と `wiki_rawcheck.py` は変えない。

## 試験

- **静的な試験**（`tests/wiki/test_web_raw_agent.py`、標準ライブラリだけ）: エージェントの frontmatter（`name`、`model: sonnet`、`omitClaudeMd: true`、`tools` に Agent がない）、エージェントの本文の `${CLAUDE_PLUGIN_ROOT}/…` と参照文書の `<skill-root>/…` のパスがあること、参照文書に `${CLAUDE_PLUGIN_ROOT}` がないこと、`commands/ingest.md` に W1〜W8 の本文が残っていないこと、コマンドとスキルが参照文書を指すこと、参照文書の JSON の例が読め、`status` の決まりに合うこと。
- **`claude plugin validate`**。
- **実地の確かめ**（`tests/wiki/check_web_raw_agent.py`。`claude -p` を動かすので費用がかかる）: 一時の wiki で、メインを Opus にして `/wiki:ingest <URL>` を動かし（英語のページと日本語のページ）、セッションの記録から次を確かめる。
  - メインが `wiki:web-raw` を呼び、`model` を渡していない。エージェントの応答のモデルが Sonnet、メインの応答のモデルが Opus。
  - `wiki_fetch.py` と `freeze` の実行と、Edit と Write での raw への書き込みは、`wiki:web-raw` の記録にだけある（メインとすべてのサブエージェントを調べる）。W8 の `check --finish` が通り、写しを消したことが道具の結果に出ている。エージェントは Claude Code のメタデータ（`meta.json` の `agentType`、`launchedWithDefaults`、`prefix.json` のモデル）で選び、確かめる。
  - Bash のコマンドの中の書き込みは、合否を決めない（シェルの文から書き込みを推し量ることは、完全にはできない）。担当ごとに、raw か wiki のページに触れうるコマンドを一覧に出し、人が読んで確かめる。エージェントは wiki のページ、`index.md`、`log.md` に書いていない。メインは要約ページ、`index.md`、`log.md` を書き、raw に書いていない。
  - エージェントの出力に要約ページの文の並び（40 文字）がなく、エージェントを呼ぶまでのメインの出力に raw の文の並びがない（受け渡しの一部を見つけるだけ）。
  - raw、log の分担のサブ行、作業用の写しが消えたこと、時間とモデルごとの費用。
  結果は `docs/research/` に残す。

## 限界

上の「言えないこと」のほかに、次がある。

- フォールバックの連鎖で、エージェントの途中からモデルが替わっても分からない。
- 取り込みを途中でやめたあと、別の会話で取り込み直すときに、依頼の `conditions` や判断の理由は引き継がれない（会話の中にしかない）。
- 次の 2 つは、この変更の前（0.14.0）からある問題で、この変更では扱わない（別の作業にする）。
  - `--html-file` で取得した取り込みを途中でやめ、URL だけで取り直すと、`wiki_fetch.py` が作業用の写しを見る前に取得し、原文のハッシュが違うので終了コード 3 で止まる（つながらなければ取得の失敗で止まる）。0.14.0 の `main` で再現した。
  - ほかのセッションが同じ wiki の同じスラッグを同時に取り込むと、作業用の写しと raw がぶつかる（取得のスクリプトは排他をしない）。

## 入れないもの

- 後段（要約ページなど）のモデルの指定。
- PDF とテキストのソース（raw はモデルが書き換えない）。
- 取得のスクリプトと検査のスクリプトの変更（取り込みの状態をスクリプトが作業用のフォルダーに書く形は、別の変更として考える）。
- エージェントの続きの呼び出し（同じインスタンスを再開する仕組み）。

## バージョン

0.15.0。URL の取り込みで、raw を作るモデルが変わる（ユーザーに見える動きの変更）。0.14.0 のタグはまだ付けていないが、`main` の 0.14.0 はすでに配られているので、別の版にする。

## 改訂の記録

- 1 版（2026-11-14）: Sol の敵対的レビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/design-review-1.md`）で却下（`design-root-causes-1.md`）。
- 2 版（2026-11-14）: 状態（依頼）をメインが持ち、完了をメインが check で確かめ、`--finish` を log のあとのメインの段に移した。2 回目のレビュー（`design-review-2.md`）で却下（`design-root-causes-2.md`）。
- 3 版（2026-11-14）: 2 版で足したもの（メインの check のやり直し、`--finish` の移動、汎用の差分の合成、報告のモデルによる作者の記録）を削り、0.14.0 の W8 に戻した。主張を狭め、言えないことを書いた。最小の試作を実際に動かしてから、レビューにかける。
- 3 版の実装（2026-11-14）: 英語と日本語のページで実際に動かし、セッションの記録の 14 項目が通った（`docs/research/wiki-web-raw-agent-trial-2026-11-14.md`）。3 回目のレビュー（`review-3.md`）で却下（`root-causes-3.md`）。呼び直すときに、エージェントが決めた `language_override` も依頼に写すようにした。実地の確かめのスクリプトの穴（Bash の中の Python の書き込み、メインの文の出力と 2 回目以降の依頼）を塞ぎ、書き込みの判定を「道具の入力に現れる書き込み」に狭めた。
- 3 版の実装の 2 回目（2026-11-14）: 4 回目のレビュー（`review-4.md`）で却下（`root-causes-4.md`）。重大 3 件はどれも実地の確かめのスクリプトへの指摘だった。Bash のコマンドの中の書き込みで合否を決めるのをやめ、一覧に出して人が読む形にした。合否は、メタデータ、すべての応答のモデル、Edit と Write の書き込み先（すべてのサブエージェント）、スクリプトの実行と W8 の結果、文の受け渡し、結果で決める。
