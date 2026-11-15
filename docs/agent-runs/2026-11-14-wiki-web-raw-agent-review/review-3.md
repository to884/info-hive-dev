## 判定

**却下。確信度：高。** `warnings` からの再呼び出しで検査条件を失う経路があり、実地試験には、設計が確認するとした操作の分担違反を **14/14 のまま通す反例**がある。以下は、明示された範囲外の問題を除いた指摘である。

## 致命的・重大な欠陥

1. **重大：警告の修正を依頼すると、子が自主的に覆した翻訳判定を次の子へ渡せない。**

   **反例・再現手順：**

   1. 取得器が `needs_translation: false` としたページについて、子が誤判定と判断し、`--language-override translate --reason …` で訳を検査する。
   2. `missing_names` などが残り、`status: "warnings"` と `language_override` を返す。
   3. 親が理由の案を拒み、手順どおり `conditions` に「McNemar を英語表記に戻す」などを追加して呼び直す。
   4. 再送する依頼の `language` は元の `null` のままである。新しい子には前の報告も検査条件も渡らず、取得器は保存済みの `needs_translation: false` を返す。
   5. 翻訳済み raw を既定の引数で検査すると、「訳さないページなのに translated_by がある」と本文変更の誤りになる。

   ファイル入出力をメモリ上で差し替え、同一の raw に対し、`translate` 付きでは終了コード **0・警告あり**、指定なしでは終了コード **1・誤りあり**になることを確認した。

   **根拠：** [呼び出す側の手順](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/references/web-raw.md:36)は、親自身の再検査と警告受け入れには `language_override` を引き継ぐが、修正依頼には引き継がない。[エージェント](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/agents/web-raw.md:16)は前の呼び出しを覚えていない。[取得器](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1250)が再開時に返すのは元の判定で、[検査器](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:843)も引数がなければそれを使う。

   これは、範囲外とされた「別の会話で条件を失う問題」ではない。同じ会話内の、今回追加した再委譲で起きる。

2. **重大：操作の分担に違反した記録でも、実地試験が全項目を通す。**

   **反例：** 正常な記録に、次の道具入力をそれぞれ追加する。

   ```text
   メイン:
   python -c "from pathlib import Path; Path('raw/x.md').write_text('changed', encoding='utf-8')"

   子:
   python -c "from pathlib import Path; Path('wiki/index.md').write_text('changed', encoding='utf-8')"
   ```

   メモリ上にセッション記録と成果物を用意して `analyze()` を実行すると、どちらも **14/14、`ok: true`** になった。

   **根拠：** [RAW_WRITE_RE](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:140)は、リダイレクトと列挙したコマンドだけを検出する。子の wiki 書き込みについても、[判定処理](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:177)が見るのは編集ツールのパスとリダイレクト先だけである。Python 内の書き込みは双方とも対象外になる。

   実際の CQRS・ブルームフィルタの子も、Bash 内の Python で raw を書いていた。したがって、これは特殊な操作方法だけの穴ではない。**実際の二試行で分担違反があったという指摘ではなく、それを否定する判定器に偽陽性があるという指摘**である。

3. **重大：メインの文章出力と、二回目以降の依頼を調べずに「raw の文がない」と判定する。**

   **反例：**

   - 最初の Agent 呼び出し前に、メインの通常の `text` 出力として raw 本文を丸ごと置く。
   - 二回目の `wiki:web-raw` 呼び出しの `prompt` に raw 本文を丸ごと入れる。

   この二つも、メモリ上の記録で **14/14、`ok: true`** になった。

   **根拠：** [文章の受け渡しの判定](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:196)は、メインの道具入力だけを集め、最初の `wiki:web-raw` 呼び出しで打ち切る。通常の文章出力は調べていない。

   これは文章の作者を証明できないという限界とは別である。**同じ本文をそのまま出した記録さえ、明示された照合対象から漏れる。**

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 依頼全体を再送すれば、有効な検査条件も保たれる | 子が自主的に `language_override` を決め、その後に警告修正を再委譲する |
| 道具入力から、書き込み担当を判別できる | Bash 内の Python、変数経由のパス、列挙されていない書き込みコマンドを使う |
| メインの道具入力を最初の Agent まで調べれば、対象の出力を確認できる | 通常の文章出力や、二回目以降の Agent プロンプトに本文がある |
| 分担ログの手順は、エージェント不在時にも適用できる | 呼び出す側が自分で W1〜W8 を行い、子の報告が存在しない |
| 表示名に `Sonnet` がない場合は、別モデルの raw である | 訳さない日本語ページでは `translated_by: ""` が正常で、画像がなければ補足名もない |

## 見落としと軽微な問題

- **軽微：エージェント不在時の分担ログが定義されていない。**  
  [呼び出す側の手順1](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/references/web-raw.md:13)は自分で処理し、その事実をユーザーに伝えるよう指示する。一方、[W9](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/commands/ingest.md:28)が参照する手順7は「`wiki:web-raw` に任せた」「報告したモデル」を前提としている。不在経路では報告がなく、同じ文面では事実に合うログを作れない。

- **軽微：Sonnet 名の確認が後段の処理とログ記録より後にある。**  
  [手順6〜8](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/references/web-raw.md:46)を順に実行すると、別モデル名を含む raw からページを書いた後で、作り直す判断になる。また、空の `translated_by` や補足名が存在しない場合の除外条件がない。日本語・画像なしの正常入力にも告知する読み方が成立する。実モデルが必ずそう誤読するかは未確認である。

- **軽微：`style` 警告には `line` がない。**  
  報告契約は警告の `kind`・`line`・`message` を要求するが、[検査器の文体警告](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:895)は `kind` と `message` だけを返す。実行でも確認した。欠けた `line` を省略するのか `null` にするのか、親がどう比較するのかが未定義である。

- **軽微：正常な読み取り操作を raw 書き込みとして扱う偽陰性もある。**  
  `RAW_WRITE_RE.search("cp raw/x.md /tmp/copy.md")` は真になる。raw はコピー元なので変更されないが、試験は分担違反として拒否する。

- **軽微：無関係なサブエージェントまで Sonnet 判定に含める。**  
  [記録の収集](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:61)はセッション配下の全サブエージェントを読み、[モデル判定](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:162)で全部に Sonnet を要求する。後段の調査を別モデルの子へ任せると、raw の分担が正常でも落ちる。

- **軽微：静的試験は制約の意味や全 status の契約を検査していない。**  
  [制約の試験](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_web_raw_agent.py:73)は語句の存在確認であり、禁止の向きは読まない。[JSON の試験](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_web_raw_agent.py:98)が検査する報告例は `done` 一つだけである。`warnings`・`needs_user`・`failed` の具体的な報告を検証したとは言えない。

## 検証した事実

- **一致：** 指定された設計、過去レビュー、原因分類、差分、実装、試験、試行結果を読み、関連する取得・検査処理を照合した。
- **一致：** 指定の unittest は **12件すべて通過**した。
- **一致：** エージェント定義は `model: sonnet`、`omitClaudeMd: true`、指定された6ツールで、`Agent` は含まない。参照先のパスも存在する。
- **一致：** 保存された二試行の元 JSONL を読めた。メインの応答モデルは Opus、子は Sonnetで、子の検査結果には `errors: []`、`warnings: []`、`work_dir_removed: true` があった。
- **一致：** `plugin.json` は **0.15.0**、CHANGELOG に同版・同日の項目がある。この版の選択を欠陥とする根拠は見つからなかった。
- **食い違い：** 「14/14」は、上述した操作・文章出力の分担違反を排除しない。
- **確かめられず：** 一時プロジェクトの実体は現在存在せず、保存済み raw・wiki・ログの現在の内容は再確認できなかった。Claude の新規呼び出しと `plugin validate` の再実行は行っていない。
- メモリ上の反例検証では、ファイルやセッション記録を書き換えていない。

## 崩せなかった点

- `warnings` を受け入れる経路では、親の再検査と最後の受け入れ検査に同じ `language_override` を渡す指示がある。
- 子に `--accept-warnings` を禁止し、親がログに理由を書いてから受け入れる順序は、実装文書と整合する。
- `needs_user` の表は、各欄を個別に変更して依頼全体を再送する形であり、過去版の汎用差分合成による `fetch` の消失は崩せなかった。
- 通常の二試行について、記録上のモデル選択と raw 検査の成功を覆す証拠は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
