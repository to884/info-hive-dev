## 判定

**却下。確信度：高。** 実地試験は、道具の入力に明示されたファイル操作による分担違反を、依然として **14/14・`ok: true`** と判定する。「記録上のファイル操作が分担どおりであることを確かめる」という設計の主張を満たしていない。

## 致命的・重大な欠陥

1. **重大：`mv` が移動元を変更することを見落とし、禁止されたファイル操作を通す。**

   `SyntheticTranscriptTest.good()` 相当の正常な記録に、次の道具入力を追加して `analyze_paths()` を実行した。ファイル入出力はメモリ上で差し替えた。

   ```text
   メイン:
   mv raw/assets/cqrs/cqrs-01.png /tmp/stolen.png

   wiki:web-raw:
   mv wiki/index.md /tmp/stolen-index.md
   ```

   **それぞれ単独で14/14、`ok: true`。** 前者は raw の画像を失わせ、後者は子が変更禁止の wiki の索引を移動する操作である。

   原因分類では、読み取りだけの `cp` を誤検出しないために「`cp` と `mv` は行き先だけを見る」とした。しかし、`mv` は移動元も変更する。この二つを同じ規則にしたことで、別の穴を作っている。

   根拠：[`command_write_targets()` の164〜165行](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:164)、[原因分類の対応方針](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/root-causes-3.md:10)。これは、コード中で組み立てたパスを見つけられないという明記済みの限界には当たらない。

2. **重大：作業ディレクトリを変更すると、入力に明示された raw への書き込みを見落とす。**

   正常なメインの記録に、次の Bash 呼び出しを追加した。

   ```bash
   cd raw && echo changed > cqrs.md
   ```

   **14/14、`ok: true`。** `bash_write_targets()` は `cqrs.md` を抽出するが、`is_raw_target()` は絶対 raw パスか `raw/` から始まるパスだけを認識する。直前の `cd raw` を扱わないため、raw 本文の上書きを検出できない。

   この反例にも、変数によるパスの組み立てや外部スクリプトはない。対象ディレクトリと書き込み先は、同じ道具入力にそのまま現れている。

   根拠：[`bash_write_targets()`](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:139)、[`is_raw_target()`](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:184)、[メインの書き込み判定](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:258)。

3. **重大：別のサブエージェントを判定から丸ごと外すため、別モデルによる raw の書き込みを通す。**

   正常な記録に、次の二つを追加した。

   - メインが `general-purpose` を呼ぶ Agent 入力。
   - その子が、Opus の応答で `<project>/raw/cqrs.md` を直接 `Write` する記録。

   **14/14、`ok: true`。** 元の `wiki:web-raw` の正常な記録があれば、別の子が raw を上書きしても合格する。

   無関係な子に Sonnet を要求しないことと、その子のファイル操作を調べないことは別である。現在の実装は、`agentType != "wiki:web-raw"` の子を一覧に出すだけにし、書き込みの判定からも除外している。そのため、「raw への書き込みはエージェントの記録にだけある」という設計の分担確認になっていない。

   根拠：[子の選別と除外](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:226)、[`agent_tools` の収集](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:249)、[設計の試験項目](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/docs/plans/wiki-web-raw-agent-2026-11-14.md:97)。

以上は**判定器の反例**であり、保存された二試行で実際に分担違反が起きたという指摘ではない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| `cp` と `mv` は行き先だけ調べれば変更対象が分かる | `mv` で raw や wiki のファイルを外へ移す |
| 書き込み先の文字列だけで raw 配下か判断できる | `cd raw` のあと、ファイル名だけで書く |
| `wiki:web-raw` 以外の子は取り込みの分担に影響しない | 別の子が raw や wiki を直接編集する |
| Python の書き込み呼び出しと raw パスが同じコマンドにあれば、raw に書いている | raw を読み、別の場所へ結果を書く |
| `prefix.json` が Sonnet なら、応答のモデルも確認できたと言える | 応答の `model` が欠けている |
| 作業用フォルダーがなければ、W8 の実施を確認できる | 検査の呼び出し自体が記録になく、フォルダーも存在しない |

## 見落としと軽微な問題

- **軽微：正常な Python の読み取り・コピーを分担違反にする。**

  次のメインの入力は、raw を変更しない。

  ```python
  Path('/tmp/copy.md').write_text(Path('raw/cqrs.md').read_text())
  ```

  それでも合成記録は **13/14・`ok: false`** となった。[`python_writes()`](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:173)は、書き込み先と読み取り元を区別せず、同じコマンドに raw パスがあれば違反とする。

- **軽微：応答モデルの確認に欠測を許す。**

  子の全応答から `model` を空にしても、`prefix.json` に Sonnet があれば **14/14** になる。[244〜247行](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:244)は両者の集合を検査するため、応答側の証拠がなくても「応答のモデルが Sonnet（記録と prefix.json）」を通す。`launchedWithDefaults` の欠落も通った。なお、保存された二試行には両方の証拠があった。

- **軽微：W8 の実行と成功を判定していない。**

  合成記録から `wiki_rawcheck.py check … --finish` の呼び出しを削除しても **14/14** だった。[252行以降](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:252)で必須にするのは取得と `freeze` だけであり、最後はフォルダーの不在を確認する。したがって、「14項目通過」から W8 成功は導けない。

- **軽微：`warnings` の分岐に、後続の確認を飛ばす読み方が残る。**

  [手順5](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/references/web-raw.md:36)は警告を受け入れたら「W9 に進み」と指示する。一方、[手順6](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/references/web-raw.md:46)は、その前に Sonnet 以外の表示名を確認するよう要求する。分岐のジャンプ先を字義どおりに読むと手順6を飛ばせる。**実モデルがその読み方で処理するかは未確認であり、挙動については推測**である。

## 検証した事実

- **一致：** 指定された設計、過去レビューと原因分類、差分、実装文書、試験、取得・検査スクリプトの関連処理を照合した。
- **一致：** `model: sonnet`、`omitClaudeMd: true`、指定の6ツールが定義され、`Agent` は含まれていない。
- **一致：** 報告の `language_override` を次の依頼の `language`・`language_reason` に写す指示が追加されている。
- **一致：** 保存された元 JSONL を読めた。二試行とも、メインの応答モデルは Opus、対象の子は Sonnet。子の検査結果には `errors: []`、`warnings: []`、`work_dir_removed: true` があった。
- **食い違い：** 上述の分担違反を含む合成記録も14項目通過となるため、判定器の合格は設計に書かれた操作分担を保証しない。
- **一致：** `plugin.json` は `0.15.0`、CHANGELOG に同版・同日の記載がある。版の選択自体を欠陥とする根拠は見つからなかった。
- **実行制約：** unittest は16件中12件通過、4件は一時ディレクトリを作れずエラーになった。読み取り専用環境によるもので、対象の欠陥には数えていない。
- **確かめられず：** 二試行の一時プロジェクトは現在存在せず、保存済み raw・wiki・log の実体を再確認できなかった。新規の Claude 実行と `plugin validate` は行っていない。
- 反例検証はメモリ上で行い、リポジトリと既存のセッション記録は変更していない。

## 崩せなかった点

- `needs_user` ごとに依頼の欄を個別に変更し、依頼全体を再送する手順。過去版の汎用差分合成による取得条件の消失は再発させられなかった。
- `language_override` を警告の再検査と呼び直しへ引き継ぐ現在の手順。
- 子が警告を受け入れず、親が log に理由を書いてから受け入れる順序。
- エージェント不在時に自分で処理し、その分担を記録する文面。
- 保存された正常系二試行の、記録上のモデル選択と検査成功。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
