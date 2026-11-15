# 依頼: 6 回目のレビューの指摘を直した版の敵対的レビュー

## 背景

wiki プラグイン 0.15.0 は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のエージェント `wiki:web-raw`（`info-hive-wiki/agents/web-raw.md`）に任せる。手順は `info-hive-wiki/skills/info-hive/references/web-raw.md` にある。エージェントはユーザーに聞けず、前の呼び出しを覚えていない。判断が要るときは `needs_user` で返し、呼び出す側がユーザーに聞き、依頼の JSON を変えて呼び直す。

6 回目のレビュー（`review-6.md`、却下）の指摘 4 件を、`root-causes-6.md` の考えで直した。

1. 「本文が短いまま続ける」の承認を、本文のハッシュに結んだ。
   - `needs_browser` の問いに `fetched_sha256` を入れる。
   - 呼び出す側は、承認を「本文が短いまま続ける（fetched_sha256: <値>）」と書く。
   - エージェントは、最後に実行した `wiki_fetch.py` の出力の値と同じときだけ、承認を効かせる。
   - 途中から続けるときの出力にも `fetched_sha256` を入れた（`wiki_rawcheck.RESUME_KEYS`）。
2. 実地の確かめのスクリプト（`tests/wiki/check_web_raw_agent.py`）は、道具の呼び出しと結果を id で対応させ、成功した書き込みだけを「書いた」と数える。
3. スクリプトの実行者は、受け取った結果がスクリプトの出力の形をしているかで決める。W8 の `check --finish` も同じに決める。
4. 書き込み先も、`..` とリンクを解いてから比べる。

直したスクリプトで、実際の取り込みのセッションの記録 2 件（`trial-cqrs.json`、`trial-bloom.json`）を確かめ直し、どちらも 15/15 で通った。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-7.submodule.diff`: プラグインの修正（`references/web-raw.md`、`wiki_rawcheck.py`、`CHANGELOG.md`）
- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-7.tests.diff`: 確かめのスクリプトと試験の修正
- 前回の記録: `review-6.md`、`root-causes-6.md`（同じフォルダー）
- 現在の全文: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`、`tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 挙動の根拠: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`、`tests/wiki/test_wiki_web_check.py`

## 探してほしいこと

1. ハッシュで結んだ承認の穴。
   - `fetched_sha256` は本当に本文を特定するか（`--keep-noise`、画像、同じ本文で別の取得など）。
   - 「最後に実行した `wiki_fetch.py` の出力」があいまいになる場面（終了コード 3、失敗、途中から続けたとき）はないか。
   - 呼び出す側が値を写し間違えたときに、どう振る舞うか。
   - 承認が効かなくなって、抜け出せない往復になる場面はないか。
2. `RESUME_KEYS` に `fetched_sha256` を足したことで、`wiki_fetch.py`、`wiki_rawcheck.py`、ほかの呼び出し元の挙動が変わったところ。
3. 結果の形で実行者を決める判定の穴。
   - 偽の陽性: `fetch.json` を読む、`check` の出力を `cat` する、など。
   - 偽の陰性: 出力を捨てる、ファイルに書く、一部だけを表示する、長い出力が切られる、など。
   - 取り違え: 結果がない呼び出し、同じ id が重なる記録、`PowerShell` の道具、など。
4. 書き込みの成否の判定の穴。
   - `is_error` のない失敗の結果。
   - `Edit` が別のファイルを作るか、同じファイルを書き換えるか。
   - 前の要約ページへの `Edit` の成功。
   - `norm()` の、Windows の UNC パス、ドライブの大文字小文字、`resolve()` の例外。
5. 試験が見ていないために、上の欠陥が通ってしまうところ。

推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
