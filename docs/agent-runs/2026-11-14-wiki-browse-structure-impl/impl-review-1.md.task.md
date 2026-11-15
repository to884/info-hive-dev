# browse の構造の直しの実装の敵対的レビュー（1 回目）

## 対象が果たすべき目的

承認済みの設計 `docs/plans/wiki-browse-structure-2026-11-11.md`（8 版目）を、次の 3 つのモジュールと試験に実装した。
設計どおりかどうか、特に「失敗のないときの約束」（設計の 9.1。失敗も競合も入れない実行が守るべきこと）を破る反例を探してほしい。

- `info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py`（入出力の層。口、失敗の読み替え、書き込みの口の Wiki のルートとの重なりの確かめ、領分、門、書き出しの手順、サーバーの記録、読む側の走査）
- `info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`（写しと中核。2 回の走査、内容と読み取りの情報、読めない入力の印、1 ページの描画の失敗、公開の前の検査）
- `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`（入口。build、serve、stop、core、コマンドの出口の境界）
- 試験: `tests/wiki/browse_sandbox.py`、`tests/wiki/browse_sweep.py`、`tests/wiki/browse_blackbox.py`、`tests/wiki/test_browse*.py`

変更前のコードは、`info-hive-wiki` の `origin/main`（`git -C info-hive-wiki diff origin/main -- skills/info-hive/scripts/` で差分を見られる）。

## 守ること（設計の要約。正本は設計の文書）

- 守ること 1 の言い換え（設計の 1、ADR-0017 を書き換える予定）: browse は、領分（`<data_dir>/browse/` と、`--out` の書き出し先の隣の `<名前>.browse-work/`）の外では、自分が作ったものだけを置き換え、消す。Wiki のルートの下には何も作らない。
- 書き込みの口は、どれも名前そのものに働き、最後の名前のリンクをたどらない。ファイルを作る口は Windows で `CreateFileW` + `FILE_FLAG_OPEN_REPARSE_POINT`。
- 領分の根 `<data_dir>/browse` の名前がリンクなら止まる。`<data_dir>` そのものはリンクでもよい。
- `--out` は門（一覧と中身が全体で合う世代、ない、空、のどれか）を通るときだけ置き換える。既定の書き出し先は領分で、前の世代を読まない。
- 終了コードは単位の真実（書き出し先にある世代）だけで決める。確定のあとの失敗は警告にする。
- stop と動いているかの確かめは何も作らない。

## 設計から離れた点（実装で決めたこと。これ自体の妥当性も疑ってよい）

1. 初めての 2 つの書き出し・起動が同時に走るとき、`<data_dir>`、領分の根、状態のディレクトリを作る `mkdir` と、目印を作る排他の作成が `FileExistsError` で失敗したら、名前の種類を見て「もうある」として続ける（`_mkdir_shared`、`use_territory`）。0.10.0 の試験（同時の serve、同時の入れ子の書き出し）が通らなくなったため。
2. `stop` は、止めたサーバーが終わったあと、その instance の記録が残っていれば消す（`remove_record`）。Windows で、読んでいるほかのプロセスがいると、サーバー自身が記録を消せないため。
3. `--out` が browse のデータの場所と重なるとき（中か、含むか）は止める。0.10.0 と同じ。
4. 状態のディレクトリは 0o700、記録は 0o600（POSIX）。0.10.0 と同じ。
5. 対照（設計の 9.5）は、層の中の `MUTANTS` の集合で持つ。空なら働かない。
6. `wiki_initialized`（ADR-0019）は層の外の入出力のまま使う（設計を書いたあとに入ったもの）。

## 出力の言語

日本語で書く。
