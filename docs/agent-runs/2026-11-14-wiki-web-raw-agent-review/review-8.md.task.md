# 依頼: 7 回目のレビューの指摘を直した版の敵対的レビュー

## 背景

wiki プラグインは、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のエージェント `wiki:web-raw`（`info-hive-wiki/agents/web-raw.md`）に任せる。手順は `info-hive-wiki/skills/info-hive/references/web-raw.md` にある。エージェントはユーザーに聞けず、前の呼び出しを覚えていない。判断が要るときは `needs_user` で返し、呼び出す側がユーザーに聞き、依頼の JSON を変えて呼び直す。

7 回目のレビュー（`review-7.md`、却下）の指摘を、`root-causes-7.md` の考えで直した。

- **プラグイン（0.16.1）:** W1〜W8 の頭に、「`wiki_fetch.py` を実行したら、どの段の取り直しでも、その出力を W2 の扱いで読み、W3 を通ってから W4 に進む」という決まりを置いた。呼び直すときに承認を消す手順は除いた。承認は本文の `fetched_sha256` に結んである。
- **実地の確かめのスクリプト（`tests/wiki/check_web_raw_agent.py`）:** 合否で主張する範囲を狭めた。主張の範囲は次のとおりである。

## 確かめのスクリプトが主張する範囲

- **前提:** 記録は、手順に従って動いたセッションのものとする。わざと隠した書き込みや実行は、見つけることを主張しない。`analyze` に渡すプロジェクトは、空のフォルダーから始めた取り込みとする（`run` はそうする）。
- **合否を決めるもの（あったことを示す証拠）:**
  - メタデータと応答のモデル。
  - `model` の引数を渡していないこと。
  - Edit と Write の書き込み先（禁止は、試みたものも数える。書いたことは、成功したものだけで数える）。
  - `wiki:web-raw` が取得と `freeze` の出力を受け取ったこと。
  - W8 は、`wiki:web-raw` が自分で `check --finish` を動かして通ったこと（警告を受け入れる流れでは、メインの `--accept-warnings`）。
  - 文の受け渡しの一部。
  - 結果のファイル。
- **合否を決めないもの:** ほかの担当がスクリプトを動かさなかったこと、Bash で書かなかったこと。結果の形から見えたほかの担当の実行は `other_script_runs` に出す。メインとほかのサブエージェントのコマンドは、すべて `bash_to_review` に出す。

直したスクリプトで、実際の取り込みの記録 2 件を確かめ直し、どちらも 15/15 で通った。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-8.submodule.diff`: プラグインの修正
- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-8.tests.diff`: 確かめのスクリプトと試験の修正
- 前回の記録: `review-7.md`、`root-causes-7.md`（同じフォルダー）
- 現在の全文: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`、`tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 挙動の根拠: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`

## 探してほしいこと

1. **「取り直したら W3 に戻る」の決まりの穴。**
   - 取り直しなのに、この決まりの文に当たらない経路はないか（呼び出す側が呼び直す場合、W8 の `check` のあとに取り直す場合、W2 の終了コード 3 で別のスラッグで取る場合など）。
   - W3 に戻ることで、抜け出せない繰り返しにならないか。
   - 前の取得について確かめたことを使わない、という決まりと、途中から続ける（`work_stage`）との食い違いはないか。
2. **承認の手順を除いたことで、古い承認が残って害になる場面はないか。**
3. **確かめのスクリプトの、上の範囲の中での欠陥。** 範囲の外（記録からは示せないこと、わざと隠したもの、前提の外のプロジェクト）は、欠陥として挙げない。挙げるときは、範囲の外であることを書く。
   - 手順に従った正しい取り込みを、不合格にする場面。
   - 範囲の中の違反を、合格にする場面。
   - `bash_to_review` から、メインかほかのサブエージェントのコマンドが漏れる場面。
4. **試験が見ていないために、上の欠陥が通ってしまうところ。**

推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
