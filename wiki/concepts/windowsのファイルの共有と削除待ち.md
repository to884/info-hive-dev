---
type: "concept"
title: "Windows で、置き換えと削除の途中のファイルを開くと失敗する（共有の指定と削除待ち）"
tags: ["windows", "browse"]
sources: ["stopの記録の読み取りの直し-wiki-0.19.1"]
created: 2026-11-15
updated: 2026-11-15
---

# Windows で、置き換えと削除の途中のファイルを開くと失敗する（共有の指定と削除待ち）

Windows では、ほかのプロセスが `os.replace` か `os.unlink` をしている途中のファイルを開くと、`PermissionError` になることがある。browse の `stop` が、サーバーの記録（`server.json`）を読むときに、これで止まっていた（[[stopの記録の読み取りの直し-wiki-0.19.1]]）。原因は 3 つあり、効く手当てが違う。

## 3 つの原因

| 原因 | 起きる場面 | エラー | 手当て |
| --- | --- | --- | --- |
| 開く側が `FILE_SHARE_DELETE` を付けない | `os.replace`（`MoveFileExW`）と `os.unlink`（`DeleteFileW`）は、途中でファイルを DELETE の権利で開く。そのあいだに `os.open` で開く | 共有違反（エラー 32。`os.open` は CRT の errno から例外を作るので `winerror` がない） | `CreateFileW` に `FILE_SHARE_READ \| FILE_SHARE_WRITE \| FILE_SHARE_DELETE` を付けて開く |
| 開いている側が `FILE_SHARE_DELETE` を付けない | `os.open` で開いているあいだに、ほかのプロセスが `os.unlink` する | 消す側が共有違反（エラー 32） | 同じ |
| 名前が削除待ち | 削除の印を付けてから、そのハンドルを閉じるまで（`DeleteFileW` の途中） | 開く側がエラー 5。共有の指定では避けられない | 読めない（分からない）答えとして扱い、待って読み直す |

加えて、`os.replace` は、置き換える先がほかのプロセスに開かれていると、開いた側の共有の指定によらずエラー 5 で失敗する（`MoveFileExW` は、POSIX の名前の付け替えの意味を使わない）。

## 確かめたこと

2026-11-15 に、Windows 11（NTFS）の Python 3.12 と 3.14.6 で、書く側と読む側を 2 つのプロセスで 4 秒ずつ同時に回して数えた（info-hive-dev の `docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/share_probe-results.md`）。

| 読む側 | 書く側 | 読む側の失敗 | 書く側の失敗 |
| --- | --- | --- | --- |
| `os.open` | 置き換え | 約 9% | `os.replace` の約 90%（先が開かれている） |
| `os.open` | 消して作り直す | 約 29% | `os.unlink` の大半（共有違反） |
| 共有 7 | 置き換え | 0 | `os.replace` の約 89% |
| 共有 7 | 消して作り直す | 削除待ちの 57 回だけ | 0 |

## 試験で決まった順に作る

2 つのスレッドやプロセスの競合は、繰り返しでしか見つからない。途中の状態は、試験で直接作れる。

- 置き換えと削除の途中: `CreateFileW` を DELETE の権利（`0x00010000`）と共有 7 で開いたままにする。`os.open` で開くと共有違反になり、共有 7 なら開ける。
- 削除待ち: 同じハンドルに `SetFileInformationByHandle(FileDispositionInfo)` で削除の印を付けたままにする。閉じるまで、名前はどの共有でも開けない。閉じると名前が消える。

browse の `tests/wiki/test_browse_server.py` の `UnreadableRecordTest` が、この形で作っている。

## 関連

- [[pythonの書き戻しの改行]]: 同じく Windows の Python で気づきにくい振る舞い
- [[browseの構造の直しとリリース-wiki-0.17.0]]: browse の入出力の層（口と失敗の読み替え）
