## 判定

**却下。確信度：高。** 正当な JSONL の文字列内にある Unicode の行区切り文字によって、検査結果の記録が読み捨てられる。警告を受け入れた違反を見逃して **19/19** にする反例と、正常完了を不合格にする反例を再現した。

## 致命的・重大な欠陥

### 1. 【重大】`read_jsonl()` が JSON の文字列内で記録を切断し、違反の証拠を黙って捨てる

`read_jsonl()` はファイル全体を `str.splitlines()` で分割する。これは LF・CRLF だけでなく、JSON の文字列内にそのまま格納できる U+2028、U+2029、U+0085 でも分割する。切断された断片は JSON として読めず、例外処理で捨てられる。

**反例：警告受け入れの見逃し**

1. 単一 URL の英文に、`The town of Greenwich<U+2028>is old.` という段落がある。
2. Sonnet が「グリニッジの町は古い。」と訳す。実際の `check()` は、`source` に U+2028 を保持した `missing_names` 警告を生成する。
3. Sonnet が誤って `check --finish --accept-warnings --json` を実行する。
4. その後、取り直して `Greenwich` を残した訳に直し、警告なしの `check --finish --json` で終える。

検査結果を既存試験と同じ `json.dumps(..., ensure_ascii=False)` で JSONL に記録すると、手順3の結果のレコードだけが読み捨てられる。`finish_runs()` は対応する結果がない呼び出しを数えないため、警告受け入れの違反が消える。

| 原文の区切り文字 | JSONL の記録数→読めた数 | 判定 |
|---|---:|---|
| 通常の空白 | 12→12 | 18/19、警告受け入れを検出 |
| U+2028 | 12→11 | **19/19、違反を見逃す** |

実際の `check()` で警告を生成し、ファイルと記録をメモリ上で差し替えて `analyze_paths()` まで通した結果である。結果の本文を直接 `check_runs()` に渡すと、どちらも `accepted=True` になる。欠落は JSONL の読み込みで起きている。

**反例：正常完了の誤拒否**

正常完了した実記録の W8 に、`--language-override translate` と、U+2028 を含む正当な `--reason` を与えた結果を記録すると、W8 の呼び出しと結果が読み捨てられ、W8 の項目が落ちた。通常の空白では通り、U+2028・U+2029・U+0085 では落ちる。

**根拠：**

- [check_web_raw_agent.py:90](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:90)：`splitlines()` で分割し、95行目の `JSONDecodeError` を無視する。
- [check_web_raw_agent.py:469](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:469)：対応する結果がなければ、その回を数えない。
- [check_web_raw_agent.py:481](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:481)：残った回だけで警告受け入れを判定する。
- [wiki_rawcheck.py:945](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:945)：警告の詳細に原文を保持する。
- [wiki_rawcheck.py:1148](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1148)：`ensure_ascii=False` で JSON を出力する。
- [test_web_raw_agent.py:313](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_web_raw_agent.py:313)：既存試験も同じ形式で JSONL を作る。

**照合結果：食い違い。** 「どの回の警告受け入れも検出する」という主張が成立しない。実行の隠蔽や出力の見せかけは使っていない。

再現条件は、外側の JSONL が当該文字を ASCII エスケープせず記録することである。新たな Claude Code セッションで、その保存方法まで含めた実地再現は行っていない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| `splitlines()` の各要素が JSONL の1レコードである | JSON の文字列内に U+2028、U+2029、U+0085 がある |
| JSON の解析失敗を無視しても、判定に必要な証拠は残る | 捨てたレコードが警告受け入れや最後の W8 の結果である |
| JSON 化すれば本文由来の文字が回の判定に影響しない | 回の解析より前に、JSONL の読み込みで記録が欠落する |

雑音として消され、最終 raw に残らない文字も、単一 URL の通常の取り込みで出力される限り範囲内である。最終 raw だけを見る `output_shapes()` は、その履歴を調べない。ただし、0.18.1 の freeze の字下げから偽の回が生まれる反例は再現できなかった。

## 見落としと軽微な問題

- **【軽微】`output_shapes()` は実際の認識条件より広く拒否する。** 例えば通常の記事中の `{"final_url": "https://example.com/", "status": 200}` は、`FETCH_OUT` に一致しないが、`output_shapes()` は `"final_url": ` だけで不合格にする。明示された保守的な判定ではあるが、本物の取得結果と取り違えない入力まで拒否する。根拠は [check_web_raw_agent.py:346](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/check_web_raw_agent.py:346)。
- **重大1を通す試験の穴がある。** [test_wiki_web_check.py:482](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:482) は U+2028 を `_item()` に直接渡すだけで、JSON 出力を外側の JSONL に格納して読み直していない。回の解析試験も、読み込み後の文字列から始まっている。
- **【軽微】正常系の試験入力が新手順と一致していない。** [test_web_raw_agent.py:336](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_web_raw_agent.py:336) の `good()` は、`--json` のないコマンドに JSON の結果を対応させている。

## 検証した事実

- 保存結果4件を現行コードで再解析し、`checks` がすべて一致した。順に **19/19、19/19、17/18、19/19**。
- ファイルを生成しない既存試験17件と、入出力をメモリに置き換えた関連試験9件は成功した。
- HTML からの変換でも、英文の途中の U+2028 が保持されることを確認した。
- 重大1の JSONL は、LF ごとに読めば各レコードが正当な JSON として読める。
- W8 と呼び出す側の警告受け入れ手順は照合した。呼び出す側は `--json` を含む「同じ引数」に `--finish --accept-warnings` を足す記述であり、そこに引数の脱落は確認できなかった。
- ファイル変更、新たなモデル呼び出しは行っていない。

## 崩せなかった点

- `render()` の check と freeze のページ由来の値を、11種類の改行・行区切り文字で攻撃したが、字下げを抜けて偽の回になる例は作れなかった。
- CRLF の JSON、行途中の JSON の除外、後続 freeze の警告との分離は崩せなかった。
- 呼び出し全体が誤りになっても、先に出た完了結果や警告受け入れを保持する既存の反例は通った。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
