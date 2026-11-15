# 依頼: 9 回目のレビューの指摘を直した版の、確かめのスクリプトの敵対的レビュー

## 背景

wiki プラグインは、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のエージェント `wiki:web-raw` に任せる。`tests/wiki/check_web_raw_agent.py` は、実際の取り込みのセッションの記録から、その分担を確かめる開発用のスクリプトである。

9 回目のレビュー（`review-9.md`、却下）の重大な指摘 4 件は、どれもこのスクリプトにあった。原因は、シェルのコマンドと Markdown を正規表現で読み直していたことである。そこで、`root-causes-9.md` のとおり、判定をプラグインの出力とファイルの中身に移した。

- **W8:** コマンドに `wiki_rawcheck`、`check`、`--finish` があり、結果が通って写しを消した形であることで決める（`names_finish`。シェルの区切りや引用符は読まない）。
- **索引とログ:** ファイルの中身で決める。`index.md` に、メインが成功した Edit か Write で書いた要約ページへのリンクがあること。`log.md` に取り込みの行と「raw:」のサブ行があること。
- **表示名:** W8 の `check --json` の結果の `translated_by` と `caption_names` から取る（`check_json`）。文字の出力のときは判定せず、`display_names_verified` を false にする。
- **`--accept-warnings`:** オプションを付けて check を動かし、check の出力を受け取った呼び出しだけを違反とする。

実際の取り込みの記録 3 件は、18/18、18/18、17/17 で通った（3 件目は表示名を判定していない）。プラグインの手順（PR to884/info-hive-wiki#61、0.16.1）は 9 回目で崩されなかったので、今回の対象にしない。

## 確かめのスクリプトが主張する範囲（8 回目、9 回目と同じ）

- **前提:**
  - 記録は、手順に従って動いたセッションのものとする。わざと隠した書き込みや実行は、見つけることを主張しない。
  - `analyze` に渡すプロジェクトは、空のフォルダーから始めた取り込みとする。
- **合否を決めるもの:** あったことを示す証拠（スクリプトの説明の「合否を決めるもの」）。
- **合否を決めないもの:** ほかの担当がスクリプトを動かさなかったこと、Bash で書かなかったこと。これらは `other_script_runs` と `bash_to_review` に出す。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-10.tests.diff`: 9 回目のあとの修正
- 前回の記録: `review-9.md`、`root-causes-9.md`（同じフォルダー）
- 現在の全文: `tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 判定の根拠にしたプラグインの出力: `info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`（`check` の結果の JSON と文字の出力）、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/init_wiki.py`（初期化で書く `index.md` と `log.md`）
- 手順: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`、`info-hive-wiki/commands/ingest.md`
- 確かめ直した結果: `trial-cqrs.json`、`trial-bloom.json`、`trial-0161-cqrs.json`（同じフォルダー）

## 探してほしいこと

1. **プラグインの出力に移した判定の穴。**
   - `check_json` が、別の出力（前の `check` の JSON、`fetch.json`、エージェントが表示した文）を取り違える場面。
   - 1 つの結果に `check` の JSON が 2 つあるとき、どちらを使うか。
   - W8 を 2 回動かしたとき、どの結果の表示名を使うか。
2. **ファイルの中身による判定の穴。**
   - 初期化した `index.md` と `log.md`（`init_wiki.py` が書くもの）だけで、通ってしまう場面。
   - 要約ページのスラッグと、索引のリンクの書き方（`[[スラッグ]]`、`[[スラッグ|別名]]`、パス付き、日本語のスラッグ）の食い違いで、正しい取り込みを落とす場面。
   - 1 回の取り込みで要約ページが 2 つ以上あるとき。
3. **`names_finish` と `--accept-warnings` の判定で、手順に従った正しい取り込みを落とす場面と、範囲の中の違反を通す場面。**
4. **試験が見ていないために、上の欠陥が通ってしまうところ。**

範囲の外（記録からは示せないこと、わざと隠したもの、前提の外のプロジェクト）は、欠陥として挙げない。挙げるときは、範囲の外であることを書く。推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
