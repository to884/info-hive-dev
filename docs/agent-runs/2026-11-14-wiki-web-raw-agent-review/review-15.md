## 判定

**却下。確信度：高。** 本物の check 出力を読み落として違反なしとする反例と、起動されたエージェントの記録が丸ごと欠けても「読み切れた」とする反例を再現した。正常な W8 を誤って落とす反例もある。

## 致命的・重大な欠陥

### 1. 【重大】直前の出力に改行がないと、本物の check JSON を候補から除外する

**主張：** `wiki_rawcheck.main()` が JSON の前に改行を出さないため、同じ Bash 呼び出しの直前出力によって `{` が行途中に移る。認識器はこれを候補にも解析失敗にも数えず、警告受け入れを見逃す。

**反例：**

```sh
printf 'check result: '
python wiki_rawcheck.py check --wiki wiki --raw-root raw --slug cqrs --finish --accept-warnings --json
```

結果は次の形になる。

```text
check result: {
  "stage": "check",
  …
}
```

同じ URL を取り直し、その後に警告なしの W8 で終える場合、前の警告受け入れが消える。進捗表示を付けるだけであり、出力の偽装や意図的な隠蔽は必要ない。

実際の `check()` と `main()` で `missing_names` 警告と `work_dir_removed: true` を生成し、0.18.1 の実記録を基にメモリ上で検証した。

| 前の回の出力 | 結果 |
|---|---|
| 行頭から始まる JSON | 20/21。警告受け入れを検出 |
| `check result: ` が直前にある同じ JSON | **21/21。違反を見逃す** |

逆に、警告なしで正常終了した**最後の W8** に同じ進捗表示を付けるだけでも、JSON を認識できず **19/20、W8 不合格**になる。このときも「check の JSON をすべて読めた」は合格する。

**根拠：**

- [check_web_raw_agent.py:344](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:344)：`stage` を探した後、349 行で行途中の `{` を無条件に捨てる。`broken` には追加しない。
- [check_web_raw_agent.py:546](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:546)：候補がなく、`broken` も空なら欠落としない。
- [wiki_rawcheck.py:1148](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1148)：JSON の直前に改行を挿入せず `print()` する。

**照合結果：食い違い。** 「スクリプトの出力が `{` で始まる」ことは、「結合された道具の結果でも `{` が行頭にある」ことを保証しない。

### 2. 【重大】起動記録と記録ファイルを対応付けず、丸ごとの欠落を見逃す

**主張：** メタデータの欠落検査は、発見できた `.jsonl` に対してしか働かない。起動されたエージェントの `.jsonl` 自体が欠けると、そのメタデータも検査対象にならない。

**反例・再現手順：**

1. 0.18.1 の CQRS 実記録を基にする。
2. 同じ URL の依頼について、別 ID の `Agent` 呼び出しと、別の `agentId` を返す起動成功結果を加える。実記録と同じ構造を保つ。
3. 保存・収集漏れにより、そのエージェントの記録ファイルがない状態を仮定する。
4. 元からある正常なエージェントの記録だけで解析する。

結果は **21/21、`ok=True`**。呼び出し検査の詳細にも、次の不一致が出るが合否に影響しない。

```json
{
  "calls": ["wiki:web-raw", "wiki:web-raw"],
  "agents": ["wiki:web-raw"]
}
```

さらに、欠けた側を**空の `.jsonl` と、読める正しいメタデータ・prefix**として渡しても **21/21** だった。応答モデルなどの証拠をエージェント間でまとめて判定するため、正常な一方が空の他方を補ってしまう。

単一 URL の再試行で成立する。意図的に記録を隠したケースは仮定していない。実際に収集漏れが発生した事例までは確認していないが、欠けた入力を合格とする挙動は再現済みである。

**根拠：**

- [check_web_raw_agent.py:155](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:155)：存在する `agent-*.jsonl` だけを列挙する。
- [check_web_raw_agent.py:461](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:461)：列挙されたファイルについてのみメタデータを読む。
- [check_web_raw_agent.py:482](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:482)：起動と記録がそれぞれ一つ以上あれば通る。ID による対応を確認しない。
- [check_web_raw_agent.py:497](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/check_web_raw_agent.py:497)：全 raw エージェントの応答をまとめて判定し、各記録に応答があることを要求しない。

**照合結果：食い違い。** 発見したファイルを読めたことと、必要なエージェントの記録をすべて読めたことが混同されている。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| JSON の出力先は必ず行頭である | 同じシェル呼び出しで、改行のない進捗表示が先に出る |
| 候補なしなら、読めない check 出力もない | 行頭条件から外れる、または `stage` の途中で出力が切れる |
| 存在する `.jsonl` の一覧が、起動された全エージェントの一覧である | 一部の記録ファイルが保存・収集から漏れる |
| 全体に応答があれば、各エージェントの証拠もそろっている | 一方が正常で、別のエージェントの記録が空である |

## 見落としと軽微な問題

- **【軽微・候補判定の限界】ヘッダー途中の切断は欠落にならない。** `{\n  "stage": "ch` を渡すと、`spans=[]`、`broken=[]` になる。後に正常な W8 があれば **21/21** になることも確認した。根拠は `check_json_spans()` の 344〜346 行。Claude Code が実際にこの位置で切断した事例は未確認であり、その発生経路は推測である。
- **試験は切断位置を一つしか見ていない。** [test_web_raw_agent.py:774](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/test_web_raw_agent.py:774) は出力の中央で切るため、完全な `"stage": "check"` が必ず残る。候補認識より前の欠落を検出できない。
- **記録生成の補助処理が、丸ごとの欠落を作らない。** [test_web_raw_agent.py:315](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/test_web_raw_agent.py:315) は、渡された全エージェントについて `.jsonl`・メタデータ・prefix を必ず生成する。追加された欠落試験も、既存 `.jsonl` のメタデータを壊すケースに限られる。
- **実出力の往復試験にも直前出力がない。** [test_web_raw_agent.py:821](C:/Works/info-hive-dev/.claude/worktrees/web-raw-evidence/tests/wiki/test_web_raw_agent.py:821) は空の `StringIO` で捕捉するため、重大1の行頭条件を常に満たす。

## 検証した事実

- 指定の差分、総括、修正案、前回レビュー、原因整理、現行コード、保存結果4件を読んだ。
- 保存結果4件を実際の記録から再解析し、`checks` がすべて一致した。順に **21/21、21/21、19/20、21/21**。0.16.1 は W8 だけが不合格だった。
- 実際の `check()`・`main()` が、`missing_names` 警告を残したまま `--accept-warnings` で写しを消す JSON を出すことを確認した。ファイル操作はメモリ上で置き換えた。
- 不正 UTF-8、非オブジェクト行、破損メタデータ、結果のない finish 呼び出しは、不合格になることを確認した。
- ファイルを生成しない既存試験 **17 件は成功**。書き込みを伴う合成試験全体は実行していない。
- リポジトリのファイル変更、新たなモデル呼び出しは行っていない。

## 崩せなかった点

- LF 分割では、U+2028・U+2029・U+0085 を含む JSONL レコードが失われなかった。
- `render()` の値に11種類の改行・行区切り文字を入れても、字下げを抜けて偽の完了回にはならなかった。
- CRLF の解析と、後続 freeze の警告を前の check に混ぜない既存試験は通った。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
