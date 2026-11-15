# 記録の読み取りと置き換えの競合の実測（2026年11月15日）

`/wiki:browse` の `stop` が、Windows で、ときどき次の知らせで止まった。info-hive-dev の CI の `browse (windows-latest, 3.12)` の `tests/wiki/test_browse_server.py` の `ProcessTest.test_stop_while_starting_waits_for_record` で見つかった（run 43684426129、job 132721786337）。

```
確かめられないので、何も変えずに止める: open_read: PermissionError（...\data\browse\<id>.server\server.json）
```

`open_read` は `os.open(path, os.O_RDONLY | O_BINARY)` だった。その開き方と、サーバーの記録の書き方（`server.json.new` を作り、`os.replace` で `server.json` にする。終わるときは `os.unlink`）を、2 つのプロセスで同時に繰り返して、失敗を数えた。

## 方法

[share_probe.py](share_probe.py) を、開発用の PC（Windows 11 Enterprise 10.0.26300、NTFS）で、Python 3.12 で流した（3.14.6 でも同じ傾向だった）。

```
python -X utf8 share_probe.py <作業用のディレクトリ> <osopen|share7> <replace|unlink> 4
```

- 書く側（子プロセス）: `replace` は、`server.json.new` を `CreateFileW`（共有 7、`CREATE_NEW`）で作って書き、`os.replace` で `server.json` にする。`unlink` は、`server.json` を `os.unlink` で消し、作り直す。
- 読む側（親）: `server.json` を開いて読み、閉じる。`osopen` は `os.open`、`share7` は `CreateFileW`（`GENERIC_READ`、共有は読み、書き、消すのすべて、`OPEN_EXISTING`）。
- 4 秒ずつ流し、失敗を例外の型と `winerror` で数えた。書く側の失敗は、失敗した呼び出しの名前を付けた。

## 結果（Python 3.12）

| 読む側 | 書く側 | 読む側 | 書く側 |
| --- | --- | --- | --- |
| `os.open` | 置き換え | 成功 4,680、`PermissionError` 470 | 成功 361、`os.replace` の `PermissionError`（エラー 5）3,432 |
| `os.open` | 消す | 成功 1,714、`PermissionError` 2,801、`FileNotFoundError` 5,307 | 成功 930、`os.unlink` の `PermissionError`（エラー 32）46,733 |
| 共有 7 | 置き換え | 成功 4,463、失敗 0 | 成功 397、`os.replace` の `PermissionError`（エラー 5）3,266 |
| 共有 7 | 消す | 成功 2,268、`FileNotFoundError` 5,694、`PermissionError`（エラー 5）57 | 成功 6,103、失敗 0 |

## 分かったこと

1. `os.open` は、共有に `FILE_SHARE_DELETE` を付けない。`os.replace` と `os.unlink` は、途中でファイルを DELETE の権利で開くので、そのあいだに読む側が開くと共有違反になる（`os.open` の例外は CRT の errno から作るので、`winerror` を持たない）。共有 7 で開けば、置き換えの途中の読む側の失敗は 0 になった。
2. `os.open` で開いているあいだは、書く側の `os.unlink` が共有違反（エラー 32）で失敗する。共有 7 なら失敗しない。サーバーの終了が記録を消せず、`stop` が後で消す（`remove_record`）形の、もとの原因の 1 つである。
3. 共有 7 でも、名前が削除待ちのあいだ（`DeleteFileW` が削除の印を付けてから、そのハンドルを閉じるまで）は、読む側がエラー 5 で失敗する。共有の指定では避けられない。そこで、記録を読めない答えは、設計の 7.1 の決まり（ロックがあれば「動いているが、届かない」として待つ）で扱う。
4. `os.replace` は、置き換える先がほかのプロセスに開かれていると、読む側の共有の指定によらずエラー 5 で失敗する（`MoveFileExW` は、POSIX の名前の付け替えの意味を使わない）。前の起動が残した記録をサーバーが置き換えるとき、ほかの browse がちょうど読んでいると、起動が失敗する。CI の経路（状態のディレクトリが新しく、置き換える先がない）では起きない。この直しには含めず、設計の 11 に限界として書いた。

## 試験で作った状態

`tests/wiki/test_browse_server.py` の `UnreadableRecordTest` は、この競合の途中の状態を、決まった順に作る。

- 置き換えと削除の途中のハンドル: `CreateFileW` を DELETE の権利と共有 7 で開いたまま、記録を読む。`os.open` の形（対照 `read_without_share_delete`）は共有違反で読めない。
- 削除待ち: 同じハンドルに `SetFileInformationByHandle(FileDispositionInfo)` で削除の印を付けたまま、`stop` を動かす。直す前の形（対照 `unreadable_record_fails`）は、CI と同じ知らせで止まる。
- どの OS でも流すもの: 記録を開く口だけを、決まった回数か、止める要求のあとのあいだだけ `PermissionError` にする。

直す前のコード（info-hive-wiki の `2e48a73`）で 10 件を流すと、対照でない 7 件がすべて落ちた。5 件は `open_read: PermissionError` の「分からない」、1 件は読んでいるあいだの `os.unlink` の共有違反、`serve` の 1 件は知らせの文が違った。対照の 3 件は、直す前のコードが対照と同じ形なので通った。
