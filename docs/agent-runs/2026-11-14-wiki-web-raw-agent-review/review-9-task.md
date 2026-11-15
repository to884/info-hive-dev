# 依頼: 8 回目のレビューの指摘を直した版の敵対的レビュー

## 背景

wiki プラグインは、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のエージェント `wiki:web-raw`（`info-hive-wiki/agents/web-raw.md`）に任せる。手順は `info-hive-wiki/skills/info-hive/references/web-raw.md` にある。

8 回目のレビュー（`review-8.md`、却下）の指摘を、`root-causes-8.md` のとおりに直した。

- **プラグイン（0.16.1、PR to884/info-hive-wiki#61）:** 「取り直したら W2 の出力の扱いと W3 に戻る」の決まりを、写しを作り直したとき（出力が `"unchanged": false`）に限った。途中の写しから続けるとき（`"work_dir": true`）は、段ごとの続け方に従う。
- **実地の確かめのスクリプト（`tests/wiki/check_web_raw_agent.py`、PR to884/info-hive-dev#115）:**
  - 文の部品は、応答の id とモデルと中身がすべて同じときだけ重ねる。
  - 会話の記録（`type` が `assistant` と `user`）だけを読む。
  - 見直しの一覧を切り詰めない。
  - 索引とログの書き込みを、パスそのもので比べる。
  - 行の継続で分けた W8 を読む。
  - エージェントの `--accept-warnings` は不合格にする。
  - 表示名が Sonnet であることを合否にする。

直したスクリプトで、実際の取り込みの記録 3 件（0.15.0 より前の版の CQRS とブルームフィルタ、0.16.1 の版の CQRS）を確かめ直し、どれも 17/17 で通った。

## 確かめのスクリプトが主張する範囲（8 回目と同じ）

- **前提:** 記録は、手順に従って動いたセッションのものとする。わざと隠した書き込みや実行は、見つけることを主張しない。`analyze` に渡すプロジェクトは、空のフォルダーから始めた取り込みとする。
- **合否を決めるもの:** あったことを示す証拠。
- **合否を決めないもの:** ほかの担当がスクリプトを動かさなかったこと、Bash で書かなかったこと。この 2 つは、`other_script_runs` と `bash_to_review` に出す。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-9.submodule.diff`: プラグインの修正
- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-9.tests.diff`: 確かめのスクリプトと試験の修正
- 前回の記録: `review-8.md`、`root-causes-8.md`（同じフォルダー）
- 現在の全文: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`、`tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 挙動の根拠: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`
- 実際の記録の確かめの結果: `trial-cqrs.json`、`trial-bloom.json`、`trial-0161-cqrs.json`（同じフォルダー）

## 探してほしいこと

1. **決まりの切り分けの穴。**
   - `"unchanged": false` でも `"work_dir": true` でもない出力（終了コード 3、`"unchanged": true` で `"work_dir": false`、失敗）のとき、どこへ進むかが決まっているか。
   - `--html-file` で同じ内容を渡したとき（`"unchanged": true` かつ `"work_dir": true`）に、取り直しと続けることを取り違えないか。
2. **確かめのスクリプトの直しが、新しく生んだ欠陥。** 上の範囲の中のものに限る。
   - 会話の記録だけを読むことで、落ちる応答や結果がないか（`type` のない記録、別の種類の記録に入った道具の結果など）。
   - 重ねる鍵を変えたことで、同じ応答の重複を二重に数え、正しい取り込みを落とすことはないか。
   - 索引とログの比べ方、行の継続の読み方、表示名の判定で、手順に従った正しい取り込みを落とす場面、範囲の中の違反を通す場面。
3. **試験が見ていないために、上の欠陥が通ってしまうところ。**

範囲の外（記録からは示せないこと、わざと隠したもの、前提の外のプロジェクト）は、欠陥として挙げない。挙げるときは、範囲の外であることを書く。推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
