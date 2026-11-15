## 判定

**却下。確信度：高。** 正常な取り込みを落とす反例と、記録に残った禁止行為を見逃す反例を再現した。いずれも単一 URL・空のフォルダーからの取り込みで成立し、出力の隠蔽や見せかけを必要としない。

## 致命的・重大な欠陥

### 1. 【重大】後続の freeze の警告を、完了済みの check の警告として扱う

**反例：** 同じ URL の取り直しを含む一つの Bash 呼び出しで、次を順に実行する。

1. 警告なしの `check --finish`。文字出力で完了する。
2. `--force` で取り直し、雑音を削除して `freeze`。削除量について警告が出る。
3. 訳と補足を処理し、警告なしの `check --finish --json` で完了する。

出力の要部は次の形になる。

```text
check: 通った
作業用の写しを消した
freeze: 通った
警告: 消した文字が本文の 2 割を超える（…）
…
{"stage": "check", "ok": true, "warnings": [], "work_dir_removed": true}
```

`check_runs()` は最初の回を **`removed: true, warnings: true, accepted: true`** と判定する。`--accept-warnings` を使っていないにもかかわらず、実際の `analyze_paths()` は **17/18、不合格**となり、「wiki:web-raw は警告を受け入れて終えていない」が落ちた。

**根拠：**

- [check_web_raw_agent.py:316](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:316) の境界は check の JSON と文字出力だけで、`freeze:` を含まない。318〜324行で、その区間全体の警告を最初の check に帰属させる。
- [wiki_rawcheck.py:390](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:390) は、削除量が2割を超えると freeze の警告を生成する。本文を削っていなくても、雑音が多ければ発生する。
- [wiki_rawcheck.py:1067](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1067) は、その警告を `警告: ` で出力する。

**照合結果：食い違い。** 「回ごとに警告を見る」という説明に対し、別の段の警告が混入する。再現には実装の `deletion_report()` と `render()` を使用した。

### 2. 【重大】呼び出し全体が失敗すると、先に成立した完了と禁止行為まで捨てる

**反例：**

1. エージェントが `check --finish --accept-warnings --json` を実行し、警告付きで写しを消す。
2. 同じ Bash 呼び出しの後続で、もう一度 check する。基準の写しは消えているため失敗し、呼び出し全体が `is_error: true` になる。
3. 次の呼び出しで同じ URL を取り直し、警告なしで正常完了する。

最初の道具の結果には、警告付きの `work_dir_removed: true` がそのまま残る。`check_runs()` 単体も **`accepted: true`** と読める。しかし実際の `analyze_paths()` は、その結果を解析対象に入れず、**18/18、`ok: true`** を返した。

逆方向にも誤判定する。正常な finish の直後に、消えた作業用フォルダーを `ls` で確認して呼び出し全体が失敗すると、正常な完了出力があっても **16/17、W8 不合格**となった。

**根拠：**

- [check_web_raw_agent.py:406](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:406)〜408行は、`succeeded()` が偽なら結果の中の全 check を読まない。
- [check_web_raw_agent.py:162](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:162)〜165行の成功判定は、道具の結果全体の `is_error` による。
- [wiki_rawcheck.py:985](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:985) は、削除済みの `cleaned.md` に対する再検査を失敗させる。1134〜1136行で標準エラーを出し、終了コード1を返す。

**照合結果：食い違い。** 「エージェントのどの回でも違反を見る」という説明は、後続コマンドの失敗によって破れる。実記録にも、非ゼロ終了の Bash 出力を保持した `is_error: true` の結果が存在することを確認した。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| 次の check までの警告は、直前の check が出したもの | 間に文字出力の freeze が入る |
| Bash 全体の失敗は、その中の全 check の失敗を意味する | finish 成功後の確認・再検査が失敗する |
| 同時刻では、エージェント側を最後にすればよい | 担当をまたぐ完了の時刻が欠落・同値になる |

最後の項目は条件付きである。410行の比較キーでは担当の固定順位が記録順より優先されることは確認したが、この条件で実際の Claude Code 記録が誤判定される事例は確認できていない。採否の根拠には含めない。

## 見落としと軽微な問題

- **試験が freeze の混入を見ていない。** [test_web_raw_agent.py:583](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_web_raw_agent.py:583) 以降の追加試験は、check 同士を連結する形で、重大1の境界不足を検出しない。
- **先行完了を含む失敗結果を試していない。** `got()` は `is_error` を指定できるが、今回の追加試験では使っていない。重大2は `check_runs()` 単体の試験だけでは見つからない。
- **時刻の試験名と検証内容がずれる。** 618〜621行は「記録の順」を説明しているが、一つの道具の結果内に二つの JSON を置いている。実際に検証するのは `pos` であり、別の呼び出しの `n` や、担当をまたぐ順位ではない。

## 検証した事実

- 指定された差分、前回レビュー、原因分析、実装、手順、保存結果を照合した。
- 実記録3件を現行コードで再解析し、**18/18、18/18、17/17**。保存された `checks` とすべて一致した。
- ファイルを生成しない既存試験16件は、すべて成功した。
- W8 の担当、正常な文字出力、11回目の反例に関する既存試験3件も、記録の入出力をメモリに置き換えて成功を確認した。
- 上記2件の欠陥は、記録をメモリ上で構成し、実際の `analyze_paths()` に通して再現した。反例のシェルコマンド自体は実行していない。

## 崩せなかった点

- 11回目の重大3件は、追加試験の入力では再発しなかった。
- JSON の後に文字出力で完了すると、最後の文字出力を採用し、表示名を検証済みにしなかった。
- 通常の誤りの check と、`--finish` のない check は、前の文字出力から分離された。
- JSON の文字列内に改行を含む check 風の文章があっても、別の文字出力の回には分割されなかった。
- 呼び出す側が警告付きで完了する既存試験は通り、`w8_finished_by: ["main"]` になった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
