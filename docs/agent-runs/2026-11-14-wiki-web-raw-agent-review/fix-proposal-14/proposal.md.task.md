# 依頼: 14 回目のレビューの指摘への修正案

## 背景

`tests/wiki/check_web_raw_agent.py` は、wiki プラグインの URL の取り込みのセッションの記録（Claude Code の JSONL）から、分担を確かめる開発用のスクリプトである。確かめる分担は、raw の段（W1〜W8）を Sonnet のエージェント `wiki:web-raw` が行い、後段をメインのモデルが行うことである。

あなた（GPT-6.1 Sol）の 14 回目の敵対的レビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-14.md`）は却下だった。今回は、その指摘を直す**修正案**を考えてほしい。修正は別の担当がすでに 1 つ作ってある。あとで突き合わせるので、独立に考えてほしい。

## 読むもの

- 指摘: `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-14.md`
- 直す前の版（指摘を受けた版）:
  - `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/fix-proposal-14/check_web_raw_agent.before.py`
  - `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/fix-proposal-14/test_web_raw_agent.before.py`
- これまでの原因の整理: 同じフォルダーの `root-causes-11.md`、`root-causes-12.md`、`root-causes-13.md`（13 回目までの考え方。「判定できないことを、通したことにしない」など）
- プラグインの出力の元: `info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`（`render`、`_item`、`check`、`main`）、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`

**読まないでほしいもの**（独立に考えるため）: 作業ツリーの今の `tests/wiki/check_web_raw_agent.py` と `tests/wiki/test_web_raw_agent.py`、`root-causes-14.md`、`git log` と `git diff` の 2f8c9ef より後のもの。

## 考えてほしいこと

1. **根の原因。** 指摘の 1 つずつを直すのではなく、指摘を生んだ前提を書き出す。11〜13 回目の原因（結果の文の形から実行を組み立て直していた、など）とのつながりがあれば書く。
2. **修正案。** 重大 1、軽微 2 件、試験の穴の 1 件のそれぞれに、どう直すか。直す場所（関数、行）、直したあとの決まり、コードの骨組み（短い擬似コードか Python）を書く。場当たり的な直し（反例を 1 つずつ塞ぐ）を避け、構造で直す。
3. **同じ種類の穴。** 同じ前提に頼っているほかの場所（記録の読み込み、道具の結果の文の扱い、メタデータの JSON の読み込み、文字列の分け方など）があれば、直す前の版の行を根拠に挙げ、案に含める。
4. **案の代わりと、その損得。** 取りうる別の直し方があれば、1〜2 個挙げ、採らない理由を書く。
5. **試験の案。** 直したことを確かめる試験（直す前の版で落ち、直したあとで通るもの）を挙げる。

確かめのスクリプトが主張する範囲（前提: 手順に従ったセッションの記録、空のフォルダーからの取り込み、1 回に 1 つの URL）は変えない。範囲の外のことは、外と書いて分ける。推測は推測と書く。挙動についての主張は、コードの行を根拠にする。

## 出力の形

日本語で、次の見出しの順に書く。

- `## 根の原因`
- `## 修正案`（指摘ごとの小見出し）
- `## 同じ種類の穴`
- `## 採らない案`
- `## 試験の案`
- `## 確かめたこと`（実際に読んだり動かしたりして確かめた事実と、確かめていない推測を分ける）
