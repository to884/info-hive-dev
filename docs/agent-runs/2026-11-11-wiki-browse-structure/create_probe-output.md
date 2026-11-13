# 名前がリンクのときの、作る口の振る舞い（2026年11月13日）

設計の 3.1 の標準ライブラリの表（`os.open()` の `O_CREAT`）と、3.2 の「口は名前そのものに働く」の根拠である。開発用の PC（Windows 11）で流した。POSIX では流していない（設計の 11）。

## [lock_link_probe.py](lock_link_probe.py)

作業用のロックの名前が、Wiki の中を指す先のないシンボリックリンクのとき、`os.open` で開くと先にファイルができるか。

```text
Python 3.14.6 win32
lstat: S_ISLNK True attrs 0x2420
O_CREAT: 開けた。先ができたか: True
O_CREAT|O_EXCL: 開けた。先ができたか: True
```

`O_EXCL` を付けても、Windows の `os.open` はリンクをたどり、Wiki の中に `created.md` を作った。

## [createfile_probe.py](createfile_probe.py)

`CreateFileW` に `FILE_FLAG_OPEN_REPARSE_POINT` を付けて呼ぶと、最後の名前のリンクをたどらないか。あわせて、`mkdir`、`os.rename`、`os.replace` が、先のないリンクの名前でどう振る舞うか。

```text
Python 3.14.6 win32
OPEN_ALWAYS（先のないリンク）: 開けた。属性 0x2420（再解析点 True）、先ができたか False
CREATE_NEW（先のないリンク）: 失敗 FileExistsError 80
OPEN_ALWAYS（ない名前）: 作れた。ロックも取れた。属性 0x2020
OPEN_ALWAYS（今ある通常のファイル）: 開けた
CREATE_NEW（今ある通常のファイル）: 失敗 FileExistsError 80
mkdir（先のないディレクトリのリンクの名前）: 失敗 FileExistsError 183
rename（先が先のないリンク）: 失敗 FileExistsError 183
replace（先が先のないリンク）: (None, False, False)
```

- `OPEN_ALWAYS` は、リンクそのものを開き（属性に再解析点 0x400 がある）、先を作らなかった。試作は、開いたハンドルが再解析点かディレクトリなら、閉じて「分からない」にする。
- `CREATE_NEW` は、名前があれば（リンクでも通常のファイルでも）winerror 80 で失敗した。
- `mkdir` と `os.rename` は、先のないリンクの名前で失敗した（winerror 183）。`os.replace` は、リンクそのものを置き換えた（最後の `(None, False, False)` は、置き換えたあとの名前がリンクでなく、リンクの先もできていないことを示す）。
