# 依頼: 10 回目のレビューの指摘を直した版の、確かめのスクリプトの敵対的レビュー

## 背景

`tests/wiki/check_web_raw_agent.py` は、wiki プラグインの URL の取り込みのセッションの記録から、分担を確かめる開発用のスクリプトである。分担は、raw の段（W1〜W8）を Sonnet のエージェント `wiki:web-raw` が行い、後段をメインのモデルが行うというものである。

10 回目のレビュー（`review-10.md`、却下）の重大な指摘は 6 件だった。作者の判断で、1、2、3、5 を `root-causes-10.md` のとおりに直し、4 と 6 は前提の外として説明に書いた。

- **索引:** プラグインの `wiki_pages.extract_wikilinks` と `resolve_link` で読み、メインが書いた要約ページのすべてへのリンクを求める。
- **ログ:** `## [日付] ingest |` の見出しの項目の中に「raw:」のサブ行があることを見る。
- **W8:** 1 つの結果の中の check の出力のうち、写しを消した最後のものを使い（`finish_result`）、表示名も同じ出力から取る。サブエージェントの記録は時刻の順に並べ、表示名は時刻で最後に終えた W8 から取る。
- **警告の受け入れ:** 警告が残ったまま写しを消した check の出力で決める。この出力は `--accept-warnings` を付けたときだけ出る。コマンドの文字は見ない。

実際の取り込みの記録 3 件は、18/18、18/18、17/17 で通った（3 件目は W8 を `--json` なしで動かしたので、表示名を判定していない）。

## 確かめのスクリプトが主張する範囲

スクリプトの説明の「前提」「合否を決めるもの」「合否を決めないもの」に書いてある。前提は次の 3 つである。

- 手順に従って動いたセッションの記録であること。わざと隠したものと見せかけは見つけない。
- 空のフォルダーから始めた取り込みであること。
- 1 回の確かめで取り込む URL は 1 つであること。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-11.tests.diff`: 10 回目のあとの修正
- 前回の記録: `review-10.md`、`root-causes-10.md`（同じフォルダー）
- 現在の全文: `tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 判定の根拠にしたプラグインの部分:
  - `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（`extract_wikilinks`、`resolve_link`）
  - `info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`（`check` の出力と `main` の `--finish`）
  - `info-hive-wiki/skills/info-hive/assets/index.md.template`、`log.md.template`
- 手順: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`
- 確かめ直した結果: `trial-cqrs.json`、`trial-bloom.json`、`trial-0161-cqrs.json`（同じフォルダー）

## 探してほしいこと

1. **10 回目の直しが、新しく生んだ欠陥。** 上の範囲の中のものに限る。
   - `finish_result` の選び方。
   - 時刻の順の並べ方（時刻のない記録、同じ時刻）。
   - `resolve_link` の使い方（日本語のスラッグ、NFC と NFD、大文字と小文字）。
   - ログの項目の分け方（見出しの書き方の揺れ、コードブロックの中の見出し）。
   - 警告の受け入れを出力で決めることの穴（警告がないときに付けた `--accept-warnings`、文字の出力のとき）。
2. **手順に従った正しい取り込みを落とす場面と、範囲の中の違反を通す場面。**
3. **試験が見ていないために、上の欠陥が通ってしまうところ。**

範囲の外（前提の外の記録やプロジェクト、記録からは示せないこと）は、欠陥として挙げない。挙げるときは、範囲の外であることを書く。推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
