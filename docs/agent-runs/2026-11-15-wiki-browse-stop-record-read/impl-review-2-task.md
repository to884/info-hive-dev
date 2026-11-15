# 依頼: `/wiki:browse --stop` の記録の読み取りの直しの敵対的レビュー（2 回目）

1 回目のレビュー（`docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/impl-review-1.md`。条件付きで採用可）の指摘を直した。目的、確かめた原因、直したことの全体は、1 回目の依頼 `impl-review-1-task.md` にある。対応は `impl-responses.md` に書いた。

## 1 回目のあとで変えたこと

1. 試験（`tests/wiki/test_browse_server.py` の `RecordReads` と `UnreadableRecordTest`）。補助のスレッドが時間（0.6 秒）で順を作っていたのをやめた。`RecordReads` は、記録を開けなかったとき（入れた失敗でも、OS の失敗でも）に合図 `unreadable` を立てる。補助のスレッドは、その合図を待ってから、記録を消し、ロックを離す。対象は、終わるサーバーの試験、その対照、削除待ちの試験の 3 件。削除待ちの試験は、手を入れずに見張り、`stop` 自身が OS の削除待ちで開けなかったことを確かめる。
2. 設計（`docs/plans/wiki-browse-structure-2026-11-11.md` の 9.2 の「どの場所でも」の行）に、7.1 の場合（ロックのあるあいだに記録を読めなかったあと、読み直して読めた記録で続けたとき）を例外として足した。
3. 本体（`info-hive-wiki`）は、1 回目から変えていない。コミットを 3 つに分けた（共有の指定、待つ決まり、0.18.2）。

要求の戻りを 1.5 秒遅らせる順（1 回目の反例の順）で 3 件を流すスクリプトを `delayed_http_check.py` に置いた。手元の Windows 11、Python 3.12 で、`UnreadableRecordTest` の 10 件と、この 3 件が通った。browse の 3 つの試験のファイル（`test_browse_fs.py`、`test_browse.py`、`test_browse_server.py`）も通り、`ProcessTest` の stop の 3 件を 30 回繰り返して、失敗は 0 回だった。

## 読むもの

- 差分: `docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/impl-review-2.plugin.diff`（本体。1 回目と同じ）と `impl-review-2.tests.diff`（試験と設計）
- 試験: `tests/wiki/test_browse_server.py`（`RecordReads`、`win_hold_for_delete`、`UnreadableRecordTest`）、`docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/delayed_http_check.py`
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`（7.1 と 9.2）
- 本体: `info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`

## とくに崩してほしい点

1. 合図で順を決めた 3 件の試験に、まだ、正常な実装でも落ちる順、または、直す前の実装（対照）でも通る順が残っていないか。合図が立たないまま補助のスレッドが 20 秒の待ちを抜けた場合に、試験が誤って通らないか。
2. 9.2 に足した例外が、広すぎて、ほかの「分からない」の吸収を通してしまわないか。P1 と 7.1、9.2 のほかの行と食い違わないか。
3. 1 回目に崩せなかった点のうち、2 回目の変更で崩れたものがないか。
