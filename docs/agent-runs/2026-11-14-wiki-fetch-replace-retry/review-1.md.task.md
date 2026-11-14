# 依頼: wiki_fetch.py の名前の変更の試し直しの敵対的レビュー

## 目的

`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py` の `write_outputs` は、raw の本文と画像を一時の名前で書き、`os.replace` で正式な名前にする（古い画像の退避、新しい画像の配置、本文の置き換え、失敗したときの古い画像の戻し）。Windows では、ほかのプロセス（ウイルス対策の検査、検索の索引、エディター）が移動元か移動先を開いていると、`PermissionError`（WinError 5 か 32）で失敗する。raw を何百回も置き換える試験では、10 回に 1 回ほど起きた。

この変更で次のことを満たしたい。

1. `os.replace` が Windows で `PermissionError` を出したときだけ、短い間隔で数回（合わせて 1 秒ほど）試し直す小さな関数（`replace_with_retry`）を作り、`write_outputs` の名前の変更に使う。
2. ほかの例外と、試し直しても失敗したときは、今までどおり例外を上げる。失敗したときに前の raw と画像を戻す今の処理は変えない。
3. Windows のほかでは試し直さない。
4. 試験（親のリポジトリの `tests/wiki/test_wiki_fetch.py`）で、`os.replace` が 1〜2 回だけ `PermissionError` を出して成功する場合（raw が書かれる）と、ずっと失敗する場合（例外が上がり、前の raw が残る）を確かめる。CI は Linux（ubuntu）だけでこの試験を流すので、Windows かどうかの判定をモジュールの変数にして、試験で差し替える。

## 対象

- 差分: `docs/agent-runs/2026-11-14-wiki-fetch-replace-retry/submodule.diff`（info-hive-wiki）と `parent.diff`（このリポジトリ）
- 変更後のファイル: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（`replace_with_retry` と `write_outputs`）、`tests/wiki/test_wiki_fetch.py`（`FlakyReplace` と `ReplaceRetryTest`）、`info-hive-wiki/CHANGELOG.md` の `[Unreleased]`

## 作者が確かめたこと

- `python -X utf8 -B -m unittest tests/wiki/test_wiki_fetch.py`（Python 3.14 と `uv run --python 3.12`）で 25 件が通る。
- 修正の要所を 1 つずつ壊した写し（試し直しをなくす、4 か所の呼び出しのどれかを `os.replace` に戻す、`OSError` を全部試し直す、Windows の判定を見ない）では、それぞれ対応する試験が落ちる。
- Windows の実機で、別スレッドが `open(path, "rb")` で raw か古い画像を開いたまま `write_outputs` を呼んだ。0.3 秒で閉じれば書け、1.5 秒開いたままなら約 1.01 秒で `PermissionError`（raw は winerror 5、古い画像は winerror 32）を上げ、前の raw と画像が残り、一時のファイルも残らない。main の版では、どちらもすぐに失敗する。

## 範囲の外（指摘は不要）

- `finally` の `unlink` と `rmdir` も、Windows で同じ理由で `PermissionError` になりうる。今回は名前の変更だけを直す。
- `wiki_fetch.py` から使わないスクリプト（`wiki_browse_fs.py`、`wiki_evolve.py`、`wiki_index.py`、`wiki_mcp_common.py`、`wiki_search.py`）の `os.replace`。

## 見てほしいこと

- 試し直しが、復元（戻し）を含む `write_outputs` の失敗の扱いを壊す筋がないか（例外の差し替わり、途中で止まったときの状態、`KeyboardInterrupt` など）。
- 試し直してはいけない `PermissionError` を試し直していないか、試し直すべき失敗を取りこぼしていないか。
- 試験が、目的の 1〜4 を本当に確かめているか（偽の `os.replace` が本物の挙動とずれて、通るべきでないものが通っていないか）。
