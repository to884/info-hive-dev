# walk_probe.py の出力（2026-11-11）

作業用のディレクトリは、Windows では C ドライブの一時ディレクトリ、Linux では WSL（Ubuntu 24.04、利用者 ubuntu）の /dev/shm。

## Windows 11、tree

```text
python 3.10.11 win32  tree
  作れた: True  raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）
  作れた: True  junc -> ext（ジャンクション）
  作れた: True  dlink -> ext（ディレクトリのシンボリックリンク）
  作れた: True  flink.md -> ext/c.md（ファイルのシンボリックリンク）
  作れた: True  broken.md -> ない先
  作れた: True  dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）
wiki: 今 13 ページ（24.9 ms、rglob が返す .md は 24 個）、案 13 ページ（1.8 ms、scandir 10 回）、並びも一致: True
  ページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
  keep=indexes のとき indexes/i.md を返す: True
  終了コード 0
python 3.12.13 win32  tree
  作れた: True  raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）
  作れた: True  junc -> ext（ジャンクション）
  作れた: True  dlink -> ext（ディレクトリのシンボリックリンク）
  作れた: True  flink.md -> ext/c.md（ファイルのシンボリックリンク）
  作れた: True  broken.md -> ない先
  作れた: True  dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）
wiki: 今 13 ページ（6.5 ms、rglob が返す .md は 24 個）、案 13 ページ（2.2 ms、scandir 10 回）、並びも一致: True
  ページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
  keep=indexes のとき indexes/i.md を返す: True
  終了コード 0
python 3.13.7 win32  tree
  作れた: True  raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）
  作れた: True  junc -> ext（ジャンクション）
  作れた: True  dlink -> ext（ディレクトリのシンボリックリンク）
  作れた: True  flink.md -> ext/c.md（ファイルのシンボリックリンク）
  作れた: True  broken.md -> ない先
  作れた: True  dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）
wiki: 今 13 ページ（18.6 ms、rglob が返す .md は 24 個）、案 13 ページ（2.4 ms、scandir 10 回）、並びも一致: True
  ページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
  keep=indexes のとき indexes/i.md を返す: True
  終了コード 0
python 3.14.6 win32  tree
  作れた: True  raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）
  作れた: True  junc -> ext（ジャンクション）
  作れた: True  dlink -> ext（ディレクトリのシンボリックリンク）
  作れた: True  flink.md -> ext/c.md（ファイルのシンボリックリンク）
  作れた: True  broken.md -> ない先
  作れた: True  dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）
wiki: 今 13 ページ（4.8 ms、rglob が返す .md は 24 個）、案 13 ページ（3.0 ms、scandir 10 回）、並びも一致: True
  ページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
  keep=indexes のとき indexes/i.md を返す: True
  終了コード 0
```

## Windows 11、loop と wikis

wikis は順に、このリポジトリの wiki/、~/info-hive/W0_Wiki、info-hive-wiki/eval/evolution/pilot/wiki、eval/evolution/workflows/wiki、eval/retrieval/corpus/wiki。

```text
python 3.10.11 win32  loop
  作れた: True  sub/loop -> wiki（junction）
  今（rglob）: OSError で止まった（0.53 秒）
  案（scandir）: 128 ページ、もっとも深いパスは 127 階層、0.25 秒
  終了コード 0
python 3.14.6 win32  loop
  作れた: True  sub/loop -> wiki（junction）
  今（rglob）: 128 ページ、もっとも深いパスは 127 階層、0.39 秒
  案（scandir）: 128 ページ、もっとも深いパスは 127 階層、0.21 秒
  終了コード 0
python 3.14.6 win32  wikis
wiki: 今 4 ページ（2.1 ms、rglob が返す .md は 11 個）、案 4 ページ（0.5 ms、scandir 5 回）、並びも一致: True
W0_Wiki: 今 46 ページ（6.0 ms、rglob が返す .md は 53 個）、案 46 ページ（3.2 ms、scandir 5 回）、並びも一致: True
wiki: 今 7 ページ（1.2 ms、rglob が返す .md は 9 個）、案 7 ページ（0.5 ms、scandir 2 回）、並びも一致: True
wiki: 今 7 ページ（1.3 ms、rglob が返す .md は 10 個）、案 7 ページ（0.6 ms、scandir 3 回）、並びも一致: True
wiki: 今 20 ページ（2.7 ms、rglob が返す .md は 21 個）、案 20 ページ（1.7 ms、scandir 5 回）、並びも一致: True
  終了コード 0
```

## Linux（WSL）、tree、loop、denied

```text
ubuntu
python 3.12.3 linux  tree
  作れた: True  raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）
  作れた: False  junc -> ext（ジャンクション）
  作れた: True  dlink -> ext（ディレクトリのシンボリックリンク）
  作れた: True  flink.md -> ext/c.md（ファイルのシンボリックリンク）
  作れた: True  broken.md -> ない先
  作れた: True  dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）
wiki: 今 11 ページ（2.6 ms、rglob が返す .md は 20 個）、案 11 ページ（0.7 ms、scandir 8 回）、並びも一致: True
  ページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
  keep=indexes のとき indexes/i.md を返す: True
  終了コード 0
python 3.12.3 linux  loop
  作れた: True  sub/loop -> wiki（dir）
  今（rglob）: 2 ページ、もっとも深いパスは 1 階層、0.00 秒
  案（scandir）: 2 ページ、もっとも深いパスは 1 階層、0.00 秒
  終了コード 0
python 3.12.3 linux  denied
  今（rglob）: ['a.md']
  案（scandir）: ['a.md'] 一覧を作れなかった: ['locked']
  終了コード 0
```

## Windows 11、cycles（循環の検出を入れた案）

tree の行は、循環の検出を足したあとの walk_probe.py で、検出なしの比較が変わらないことを見たもの。

```text
python 3.10.11 win32  cycles
  sub/loop -> wiki: ['a.md', 'sub/b.md']（0.001 秒）期待どおり: True
  a/b/j -> a: ['a/b/c.md', 'a/top.md']（0.001 秒）期待どおり: True
  x/j1 -> 外、外/j2 -> x: ['x/j1/q.md', 'x/p.md']（0.004 秒）期待どおり: True
  a/j -> a/b（循環でない）: ['a/b/c.md', 'a/j/c.md']（0.002 秒）期待どおり: True
  junc -> 外（循環でない）: ['a.md', 'junc/deep/d.md']（0.003 秒）期待どおり: True
  a/me -> a（自分のいるディレクトリ）: ['a/p.md']（0.001 秒）期待どおり: True
  終了コード 0
wiki: 今 13 ページ（5.5 ms、rglob が返す .md は 24 個）、案 13 ページ（2.3 ms、scandir 10 回）、並びも一致: True
python 3.14.6 win32  cycles
  sub/loop -> wiki: ['a.md', 'sub/b.md']（0.001 秒）期待どおり: True
  a/b/j -> a: ['a/b/c.md', 'a/top.md']（0.001 秒）期待どおり: True
  x/j1 -> 外、外/j2 -> x: ['x/j1/q.md', 'x/p.md']（0.003 秒）期待どおり: True
  a/j -> a/b（循環でない）: ['a/b/c.md', 'a/j/c.md']（0.002 秒）期待どおり: True
  junc -> 外（循環でない）: ['a.md', 'junc/deep/d.md']（0.002 秒）期待どおり: True
  a/me -> a（自分のいるディレクトリ）: ['a/p.md']（0.001 秒）期待どおり: True
  終了コード 0
wiki: 今 13 ページ（4.5 ms、rglob が返す .md は 24 個）、案 13 ページ（2.6 ms、scandir 10 回）、並びも一致: True
```

## レビューのあとに直した試作での流し直し

ここより上の出力は、最初の試作（名前の判定より先に is_dir を呼び、並びの鍵が NFC だけ、OSError をすべて飛ばすもの）のものである。レビューの指摘を受けて試作を設計の本文に合わせ、同じ木で流し直した。cycles の行の数字は、6 つの形のうち期待どおりだった数である。

```text
python 3.10.11 win32  tree
wiki: 今 13 ページ（5.6 ms、rglob が返す .md は 24 個）、案 13 ページ（1.9 ms、scandir 10 回）、並びも一致: True
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
6
python 3.12.13 win32  tree
wiki: 今 13 ページ（6.9 ms、rglob が返す .md は 24 個）、案 13 ページ（3.2 ms、scandir 10 回）、並びも一致: True
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
6
python 3.13.7 win32  tree
wiki: 今 13 ページ（5.5 ms、rglob が返す .md は 24 個）、案 13 ページ（3.6 ms、scandir 10 回）、並びも一致: True
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
6
python 3.14.6 win32  tree
wiki: 今 13 ページ（5.5 ms、rglob が返す .md は 24 個）、案 13 ページ（4.1 ms、scandir 10 回）、並びも一致: True
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md', 'raw/c.md', 'raw/deep/d.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'junc', 'junc/deep', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
6
python 3.14.6 win32  wikis
wiki: 今 4 ページ（2.8 ms、rglob が返す .md は 11 個）、案 4 ページ（0.9 ms、scandir 5 回）、並びも一致: True
W0_Wiki: 今 46 ページ（8.3 ms、rglob が返す .md は 53 個）、案 46 ページ（4.3 ms、scandir 5 回）、並びも一致: True
wiki: 今 7 ページ（1.6 ms、rglob が返す .md は 9 個）、案 7 ページ（0.7 ms、scandir 2 回）、並びも一致: True
wiki: 今 7 ページ（1.4 ms、rglob が返す .md は 10 個）、案 7 ページ（0.6 ms、scandir 3 回）、並びも一致: True
wiki: 今 20 ページ（3.1 ms、rglob が返す .md は 21 個）、案 20 ページ（1.3 ms、scandir 5 回）、並びも一致: True
  終了コード 0
python 3.12.3 linux  tree
wiki: 今 11 ページ（2.7 ms、rglob が返す .md は 20 個）、案 11 ページ（0.6 ms、scandir 8 回）、並びも一致: True
  今の rglob が返し、案が見ない .md: ['assets/x/as.md', 'graph/README.md', 'indexes/i.md']
  案が scandir を呼んだディレクトリ: ['.', '.obsidian', 'concepts', 'concepts/.NET', 'concepts/raw', 'dir.md', 'real', 'ガイド']
  案が除く名前のディレクトリに降りない: True
python 3.12.3 linux  denied
  今（rglob）: ['a.md']
  案（scandir）: ['a.md'] 一覧を作れなかった: ['locked']
```

## 一覧を作れないときの rglob（os.scandir を差し替えた）

```text
3.10.11 PermissionError -> ['a.md']
3.10.11 EIO -> 送出 OSError
3.10.11 FileNotFoundError -> 送出 FileNotFoundError
3.14.6 では、同じ差し替えが rglob に効かず（3 つとも ['a.md', 'b.md'] を返した）、確かめられなかった。
```

# 2 版目のための実測（2026-11-11）

## index_probe.py（今の索引の集め方、Path.is_file()、realpath）

Windows 11:

```text
python 3.10.11 win32  index
  ふつうの indexes: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/b.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がシンボリックリンク（作れた: True）: ['indexes/sources.md']
  indexes が concepts を指す（junction、作れた: True）: ['indexes/c.md'] rglob が返すページ: ['concepts/c.md', 'indexes/c.md']
  indexes がファイル: []
python 3.10.11 win32  isfile
  os.stat が PermissionError のとき、Path.is_file(): True
  os.stat が EIO のとき、Path.is_file(): True
  os.stat が FileNotFoundError のとき、Path.is_file(): True
  Path.is_file の実装: self.stat() を呼ぶ
  DirEntry.stat() の st_ino: 0  os.stat() の st_ino が 0 でない: True
python 3.10.11 win32  realpath
  os.path.realpath に strict がある: True
  strict=True で、ない先: 送出 FileNotFoundError
  strict なしで、ない先: 返した True
python 3.12.13 win32  index
  ふつうの indexes: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/b.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がシンボリックリンク（作れた: True）: ['indexes/sources.md']
  indexes が concepts を指す（junction、作れた: True）: ['indexes/c.md'] rglob が返すページ: ['concepts/c.md', 'indexes/c.md']
  indexes がファイル: []
python 3.12.13 win32  isfile
  os.stat が PermissionError のとき、Path.is_file(): 送出 PermissionError
  os.stat が EIO のとき、Path.is_file(): 送出 OSError
  os.stat が FileNotFoundError のとき、Path.is_file(): False
  Path.is_file の実装: self.stat() を呼ぶ
  DirEntry.stat() の st_ino: 0  os.stat() の st_ino が 0 でない: True
python 3.12.13 win32  realpath
  os.path.realpath に strict がある: True
  strict=True で、ない先: 送出 FileNotFoundError
  strict なしで、ない先: 返した True
python 3.13.7 win32  index
  ふつうの indexes: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/b.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がシンボリックリンク（作れた: True）: ['indexes/sources.md']
  indexes が concepts を指す（junction、作れた: True）: ['indexes/c.md'] rglob が返すページ: ['concepts/c.md', 'indexes/c.md']
  indexes がファイル: []
python 3.13.7 win32  isfile
  os.stat が PermissionError のとき、Path.is_file(): 送出 PermissionError
  os.stat が EIO のとき、Path.is_file(): 送出 OSError
  os.stat が FileNotFoundError のとき、Path.is_file(): False
  Path.is_file の実装: self.stat() を呼ぶ
  DirEntry.stat() の st_ino: 0  os.stat() の st_ino が 0 でない: True
python 3.13.7 win32  realpath
  os.path.realpath に strict がある: True
  strict=True で、ない先: 送出 FileNotFoundError
  strict なしで、ない先: 返した True
python 3.14.6 win32  index
  ふつうの indexes: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/b.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がシンボリックリンク（作れた: True）: ['indexes/sources.md']
  indexes が concepts を指す（junction、作れた: True）: ['indexes/c.md'] rglob が返すページ: ['concepts/c.md', 'indexes/c.md']
  indexes がファイル: []
python 3.14.6 win32  isfile
  os.stat が PermissionError のとき、Path.is_file(): True
  os.stat が EIO のとき、Path.is_file(): True
  os.stat が FileNotFoundError のとき、Path.is_file(): True
  Path.is_file の実装: os.path.isfile を呼ぶ
  DirEntry.stat() の st_ino: 0  os.stat() の st_ino が 0 でない: True
python 3.14.6 win32  realpath
  os.path.realpath に strict がある: True
  strict=True で、ない先: 送出 FileNotFoundError
  strict なしで、ない先: 返した True
```

isfile の 3.10 と 3.14 の True は、os.stat の差し替えが Path.is_file() に届かなかったことを示す（3.10 の pathlib は os.stat を読み込み時に控え、3.14 は nt._path_isfile を呼ぶ）。

Linux（WSL）:

```text
python 3.12.3 linux  index
  ふつうの indexes: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/b.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md', 'indexes/sub/dir.md/in.md']
  indexes がシンボリックリンク（作れた: True）: ['indexes/sources.md']
  indexes が concepts を指す（dir、作れた: True）: ['indexes/c.md'] rglob が返すページ: ['concepts/c.md']
  indexes がファイル: []
python 3.12.3 linux  isfile
  os.stat が PermissionError のとき、Path.is_file(): 送出 PermissionError
  os.stat が EIO のとき、Path.is_file(): 送出 OSError
  os.stat が FileNotFoundError のとき、Path.is_file(): False
  Path.is_file の実装: self.stat() を呼ぶ
  DirEntry.stat() の st_ino: 32  os.stat() の st_ino が 0 でない: True
python 3.12.3 linux  realpath
  os.path.realpath に strict がある: True
  strict=True で、ない先: 送出 FileNotFoundError
  strict なしで、ない先: 返した True
```

## walk_v2.py（2 版目の試作。今の実装との比較と、失敗の注入の探索）

Windows 11:

```text
python 3.10.11 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 41 回、失敗を入れた実行 123 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 20 回、失敗を入れた実行 60 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 28 回、失敗を入れた実行 84 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 198 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     scandir(.) に eio: 送出しなかった
  対照「権限を知らせずに飛ばす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 78 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     is_symlink(.obsidian) に denied: 知らせのないまま減った ['.obsidian/o.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 0 回、失敗を入れた実行 0 回、破られた決まり 0 件
  終了: よい
python 3.12.13 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 41 回、失敗を入れた実行 123 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 20 回、失敗を入れた実行 60 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 28 回、失敗を入れた実行 84 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 198 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     scandir(.) に eio: 送出しなかった
  対照「権限を知らせずに飛ばす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 78 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     is_symlink(.obsidian) に denied: 知らせのないまま減った ['.obsidian/o.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: 探索の途中で TypeError（差し替えた項目を pathlib が扱えない）
  終了: よい
python 3.13.7 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 41 回、失敗を入れた実行 123 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 20 回、失敗を入れた実行 60 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 28 回、失敗を入れた実行 84 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 198 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     scandir(.) に eio: 送出しなかった
  対照「権限を知らせずに飛ばす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 78 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     is_symlink(.obsidian) に denied: 知らせのないまま減った ['.obsidian/o.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 29 回、失敗を入れた実行 87 回、破られた決まり 42 件
     stat(a.md) に denied: 送出した（PermissionError）
     stat(broken.md) に denied: 送出した（PermissionError）
     stat(dir.md) に denied: 送出した（PermissionError）
  終了: よい
python 3.14.6 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 41 回、失敗を入れた実行 123 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 20 回、失敗を入れた実行 60 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 28 回、失敗を入れた実行 84 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 198 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     scandir(.) に eio: 送出しなかった
  対照「権限を知らせずに飛ばす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 78 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     is_symlink(.obsidian) に denied: 知らせのないまま減った ['.obsidian/o.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 97 回、失敗を入れた実行 291 回、破られた決まり 141 件
     scandir(.) に denied: 知らせのないまま減った ['Upper.MD', 'a.md', 'flink.md', 'か.md', 'が.md']
     scandir(.) に eio: 送出しなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'ガイド/ガイド.md']
  終了: よい
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  W0_Wiki: ページ 48 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 7 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 7 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 20 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  終了: よい
```

Linux（WSL）:

```text
python 3.12.3 linux  compare
  リンクを置いた木: ページ 11 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True（Linux で足される大文字の拡張子: ['indexes/Upper.MD']）
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/Upper.MD', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 29 回、失敗を入れた実行 87 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 7 回、失敗を入れた実行 21 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 10 回、失敗を入れた実行 30 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 128 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     scandir(.) に eio: 送出しなかった
  対照「権限を知らせずに飛ばす」: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 55 件
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
     is_symlink(flink.md) に denied: 知らせのないまま減った ['flink.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: 探索の途中で TypeError（差し替えた項目を pathlib が扱えない）
  終了: よい
```

## walk_v2.py の流し直し（browse の設計の 3 回目のレビューの重大 4 を受けて直したあと）

循環の検出で、比べるための os.stat() の失敗を文字列の比較に落とすのをやめた。探索に「権限の失敗を入れたら、必ず知らせが出る」という決まりを足し、前の試作と同じ誤りを対照に足した。ここより上の walk_v2.py の出力は、直す前のものである。

Windows 11:

```text
python 3.10.11 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 30 回、失敗を入れた実行 90 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 19 回、失敗を入れた実行 57 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 27 回、失敗を入れた実行 81 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 309 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「権限を知らせずに飛ばす」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 200 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「比べるための stat の失敗を、文字列の比較に落とす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 24 件
     stat(None) に denied: 知らせを出さなかった
     stat(.) に denied: 知らせを出さなかった
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 0 回、失敗を入れた実行 0 回、破られた決まり 0 件
  終了: よい
python 3.12.13 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 30 回、失敗を入れた実行 90 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 19 回、失敗を入れた実行 57 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 27 回、失敗を入れた実行 81 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 309 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「権限を知らせずに飛ばす」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 200 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「比べるための stat の失敗を、文字列の比較に落とす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 24 件
     stat(None) に denied: 知らせを出さなかった
     stat(.) に denied: 知らせを出さなかった
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: 探索の途中で TypeError（差し替えた項目を pathlib が扱えない）
  終了: よい
python 3.13.7 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 30 回、失敗を入れた実行 90 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 19 回、失敗を入れた実行 57 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 27 回、失敗を入れた実行 81 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 309 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「権限を知らせずに飛ばす」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 200 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「比べるための stat の失敗を、文字列の比較に落とす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 24 件
     stat(None) に denied: 知らせを出さなかった
     stat(.) に denied: 知らせを出さなかった
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 29 回、失敗を入れた実行 87 回、破られた決まり 42 件
     stat(a.md) に denied: 送出した（PermissionError）
     stat(broken.md) に denied: 送出した（PermissionError）
     stat(dir.md) に denied: 送出した（PermissionError）
  終了: よい
python 3.14.6 win32  compare
  リンクを置いた木: ページ 13 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  輪でないジャンクションの別名（a と alias）: ページ 2 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md', 'indexes/Upper.MD']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  輪でないジャンクションの別名（a と alias）: ページ ['a/x.md', 'alias/x.md']、索引 []
  循環するジャンクション（sub/loop と indexes が wiki を指す）: ページ ['a.md', 'sub/b.md']、索引 ['indexes/a.md', 'indexes/sub/b.md']
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 31 回、失敗を入れた実行 93 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 8 回、失敗を入れた実行 24 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 11 回、失敗を入れた実行 33 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、ページ: OS の呼び出し 30 回、失敗を入れた実行 90 回、破られた決まり 0 件
  輪でないジャンクションの別名（a と alias）、索引: OS の呼び出し 2 回、失敗を入れた実行 6 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、ページ: OS の呼び出し 19 回、失敗を入れた実行 57 回、破られた決まり 0 件
  循環するジャンクション（sub/loop と indexes が wiki を指す）、索引: OS の呼び出し 27 回、失敗を入れた実行 81 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 309 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「権限を知らせずに飛ばす」: OS の呼び出し 109 回、失敗を入れた実行 327 回、破られた決まり 200 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'junc/c.md', 'junc/deep/d.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「比べるための stat の失敗を、文字列の比較に落とす」: OS の呼び出し 120 回、失敗を入れた実行 360 回、破られた決まり 24 件
     stat(None) に denied: 知らせを出さなかった
     stat(.) に denied: 知らせを出さなかった
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: OS の呼び出し 97 回、失敗を入れた実行 291 回、破られた決まり 222 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['Upper.MD', 'a.md', 'flink.md', 'か.md', 'が.md']
     scandir(.) に eio: 送出しなかった
  終了: よい
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  W0_Wiki: ページ 48 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 7 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 7 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  wiki: ページ 20 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  終了: よい
```

Linux（WSL）:

```text
python 3.12.3 linux  compare
  リンクを置いた木: ページ 11 個、並びも一致: True。索引 8 個、決めた違いを除いて一致: True（Linux で足される大文字の拡張子: ['indexes/Upper.MD']）
  indexes がシンボリックリンク: ページ 1 個、並びも一致: True。索引 1 個、決めた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、並びも一致: True。索引 2 個、決めた違いを除いて一致: True
  indexes がファイル: ページ 1 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  空の wiki: ページ 0 個、並びも一致: True。索引 0 個、決めた違いを除いて一致: True
  リンクを置いた木のページ: ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  リンクを置いた木の索引: ['index.md', 'indexes/.hidden.md', 'indexes/A.md', 'indexes/Upper.MD', 'indexes/i.md', 'indexes/sources.md', 'indexes/sub/deep.md', 'indexes/sub/dir.md/in.md']
  indexes がページのディレクトリを指す: ページ ['concepts/c.md']、索引 ['index.md', 'indexes/c.md']
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 0 件
  リンクを置いた木、索引: OS の呼び出し 29 回、失敗を入れた実行 87 回、破られた決まり 0 件
  indexes がシンボリックリンク、ページ: OS の呼び出し 7 回、失敗を入れた実行 21 回、破られた決まり 0 件
  indexes がシンボリックリンク、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、ページ: OS の呼び出し 10 回、失敗を入れた実行 30 回、破られた決まり 0 件
  indexes がページのディレクトリを指す、索引: OS の呼び出し 5 回、失敗を入れた実行 15 回、破られた決まり 0 件
  対照（破られた決まりが 1 件以上あれば、探索が働いている）:
  対照「どの失敗もないことにする」: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 201 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  対照「権限を知らせずに飛ばす」: OS の呼び出し 73 回、失敗を入れた実行 219 回、破られた決まり 128 件
     scandir(.) に denied: 知らせを出さなかった
     scandir(.) に denied: 知らせのないまま減った ['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.md/in.md', 'flink.md', 'real/b.md', 'か.md', 'が.md', 'ガイド/ガイド.md']
  参考（今の実装に同じ探索をかける。合否に入れない）:
  今の実装（rglob と Path.is_file()）: 探索の途中で TypeError（差し替えた項目を pathlib が扱えない）
  終了: よい
```

# 3 版目のための実測（2026-11-11）

## walk_v3.py（識別子だけで決める方式の試作。木から計算した答えとの比較、実物の今の実装との照合、失敗の注入の探索）

照らした今の実装は、info-hive-wiki のコミット f0a758f（0.10.0）の wiki_pages.py と wiki_lint.py である。

Windows 11、Python 3.10.11 と 3.14.6:

```text
python 3.10.11 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 155 回、失敗を入れた実行 465 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 57 回、失敗を入れた実行 171 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 15 回、失敗を入れた実行 45 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 35 回、失敗を入れた実行 105 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 26 回、失敗を入れた実行 78 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 40 回、失敗を入れた実行 120 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1536 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 788 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 394 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 322 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.m）
  終了: よい
python 3.14.6 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 155 回、失敗を入れた実行 465 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 57 回、失敗を入れた実行 171 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 15 回、失敗を入れた実行 45 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 35 回、失敗を入れた実行 105 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 26 回、失敗を入れた実行 78 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 40 回、失敗を入れた実行 120 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1536 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 788 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 394 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 322 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.m）
  終了: よい
```

Windows 11、Python 3.12.13 と 3.13.7、実物の wiki:

```text
python 3.12.13 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 155 回、失敗を入れた実行 465 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 57 回、失敗を入れた実行 171 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 15 回、失敗を入れた実行 45 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 35 回、失敗を入れた実行 105 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 26 回、失敗を入れた実行 78 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 40 回、失敗を入れた実行 120 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1536 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 788 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 394 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 322 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.m）
  終了: よい
python 3.13.7 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 155 回、失敗を入れた実行 465 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 57 回、失敗を入れた実行 171 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 15 回、失敗を入れた実行 45 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 35 回、失敗を入れた実行 105 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 26 回、失敗を入れた実行 78 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 40 回、失敗を入れた実行 120 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1536 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 788 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 394 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 322 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.m）
  終了: よい
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  W0_Wiki: ページ 48 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 20 個、並びまで一致: True。索引 0 個、挙げた違いを除いて一致: True
  終了: よい
```

上の Windows の出力は、対照の一覧を OS で分ける前のもので、試作の走査の部分は同じである。分けたあとの 3.14.6 の探索:

```text
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 155 回、失敗を入れた実行 465 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 57 回、失敗を入れた実行 171 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 15 回、失敗を入れた実行 45 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 35 回、失敗を入れた実行 105 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 26 回、失敗を入れた実行 78 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 40 回、失敗を入れた実行 120 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 33 回、失敗を入れた実行 99 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1536 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 788 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 394 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 322 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.m）
  終了: よい
```

Linux（WSL）、Python 3.12.3:

```text
python 3.12.3 linux  check
  リンクを置いた木: ページ 11 個、索引 9 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  名前に \ を含む: ページ 3 個、索引 0 個、答えと一致: True。今の実装とページの並びまで一致: True、索引は挙げた違いを除いて一致: True
  鍵が同じになる名前: ページ 3 個、索引 0 個、答えと一致: True。今の実装とページの集合が一致: True（並びは、鍵が同じ名前の順だけ違ってよい。今 ['a\\b.md', 'a/b.md', 'a0.md']、案 ['a/b.md', 'a\\b.md', 'a0.md']）、索引は挙げた違いを除いて一致: True
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: 口の呼び出し 121 回、失敗を入れた実行 363 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 54 回、失敗を入れた実行 162 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 14 回、失敗を入れた実行 42 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 18 回、失敗を入れた実行 54 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 8 回、失敗を入れた実行 24 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 3 回、失敗を入れた実行 9 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  名前に \ を含む、ページ: 口の呼び出し 21 回、失敗を入れた実行 63 回、答えと違った実行 0 件
  名前に \ を含む、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  鍵が同じになる名前、ページ: 口の呼び出し 21 回、失敗を入れた実行 63 回、答えと違った実行 0 件
  鍵が同じになる名前、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 852 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 412 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 206 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 151 件（例: リンクを置いた木、is_symlink(dirlink.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'conce）
  対照「並びの鍵を NFC だけにする」: 答えと違った実行 38 件（例: 名前に \ を含む、失敗なし: 答えと違う ['a0.md', 'a\\b.md', 'c/d.md']）
  終了: よい
```

## アクセスを拒まれる場所への os.stat（Windows）

```text
3.10.11  C:/System Volume Information: os.stat は成功し、st_ino 0、st_dev 0。os.scandir は PermissionError
3.14.6   C:/System Volume Information: os.stat は成功し、st_ino は 0 でない。os.scandir は PermissionError
3.10.11、3.14.6  C:/pagefile.sys: os.stat は成功し、st_ino 0、st_dev 0
```

## zero_ino_probe.py（os.stat が成功し、識別子が 0 で返る場合）

```text
python 3.10.11 win32  zero_ino
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの先の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点（wiki）の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  ジャンクションなし、sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  終了: よい
python 3.14.6 win32  zero_ino
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの先の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点（wiki）の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  ジャンクションなし、sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  終了: よい
```

# 4 版目のための実測（2026-11-11）

## walk_v4.py（3 回目のレビューの指摘を受けた試作。呼び出しの集合も木から計算して照らす）

照らした今の実装は、info-hive-wiki のコミット f0a758f（0.10.0）の wiki_pages.py と wiki_lint.py である。

### Windows 11、Python 3.10.11

```text
python 3.10.11 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True（今の実装は、Python 3.10 の rglob が Path の比較で重複を除くので、片方を落とした。挙げた違い）
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1593 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 814 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 407 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 336 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.m）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 10 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', 'real'), ('stat', 'ガイド')]）
  終了: よい
```

### Windows 11、Python 3.12.13

```text
python 3.12.13 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 並びまで一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1593 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 814 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 407 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 336 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.m）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 10 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', 'real'), ('stat', 'ガイド')]）
  終了: よい
```

### Windows 11、Python 3.13.7

```text
python 3.13.7 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 並びまで一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1593 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 814 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 407 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 336 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.m）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 10 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', 'real'), ('stat', 'ガイド')]）
  終了: よい
```

### Windows 11、Python 3.14.6

```text
python 3.14.6 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1593 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 814 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 407 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 336 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 80 件（例: リンクを置いた木、stat(junc) に absent: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr.md', 'dir.m）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 10 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', 'real'), ('stat', 'ガイド')]）
  終了: よい
```

### 実物の wiki（Windows 11、Python 3.14.6）

```text
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  W0_Wiki: ページ 48 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 20 個、並びまで一致: True。索引 0 個、挙げた違いを除いて一致: True
  終了: よい
```

### Linux（WSL）、Python 3.12.3

```text
python 3.12.3 linux  check
  リンクを置いた木: ページ 11 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  名前に \ を含む: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  鍵が同じになる名前: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True（組の順が違った: ページ 今 ['a\\b.md', 'a/b.md', 'a0.md'] 案 ['a/b.md', 'a\\b.md', 'a0.md']、索引 今 [] 案 []）
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: 口の呼び出し 113 回、失敗を入れた実行 339 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 50 回、失敗を入れた実行 150 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 12 回、失敗を入れた実行 36 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 16 回、失敗を入れた実行 48 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  名前に \ を含む、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  名前に \ を含む、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  鍵が同じになる名前、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  鍵が同じになる名前、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 846 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 398 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 199 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 146 件（例: リンクを置いた木、is_symlink(dirlink.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「並びの鍵を NFC だけにする」: 答えと違った実行 34 件（例: 名前に \ を含む、失敗なし: 答えと違う ['a0.md', 'a\\b.md', 'c/d.md']）
  終了: よい
```

### CPython のソースで確かめたこと

```text
ScandirIterator_closedir（3.10.11、3.14.0 の Modules/posixmodule.c）: FindClose(handle) と closedir(dirp) の戻り値を見ない。
ScandirIterator_iternext（同）: FindNextFileW が ERROR_NO_MORE_FILES のほかで失敗すると、また readdir が errno を立てると、path_error() で送出する。
pathlib._RecursiveWildcardSelector._select_from（3.10.11）: 返したパスを yielded（Path の集合）で重複除去する。PermissionError は捕まえて止める。
```

## zero_ino_probe.py を 4 版目の試作で流し直したもの（2026-11-11）

兄弟の木と、.md の項目の識別子が 0 の場合を足した。v3 の行は、同じ確かめを 3 版目の試作にかけたもので、兄弟の木で plain/x.md が消えることを示す（3 回目のレビューの重大 1 の再現）。

```text
python 3.10.11 win32  zero_ino（walk_v4）
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの先の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点（wiki）の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  ジャンクションなし、sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  兄弟、plain の識別子が 0、j を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟、plain の識別子が 0、plain を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.10.11 win32  zero_ino（walk_v3）
  兄弟、plain の識別子が 0、j を先に列挙: ページ ['j/c.md']、unknown ['plain']、期待どおり: False
  兄弟、plain の識別子が 0、plain を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  終了: だめ
python 3.14.6 win32  zero_ino（walk_v4）
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの先の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点（wiki）の識別子が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  ジャンクションなし、sub の識別子が 0: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  兄弟、plain の識別子が 0、j を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟、plain の識別子が 0、plain を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.14.6 win32  zero_ino（walk_v3）
  兄弟、plain の識別子が 0、j を先に列挙: ページ ['j/c.md']、unknown ['plain']、期待どおり: False
  兄弟、plain の識別子が 0、plain を先に列挙: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  終了: だめ
```

## CPython のソースで確かめた、口の各行の内側（3.10.11 と 3.14.0 の Modules/posixmodule.c）

```text
DirEntry.is_symlink: Windows は一覧の情報（win32_lstat）から答え、OS を呼ばない。POSIX は d_type から、DT_UNKNOWN なら DirEntry_test_mode で lstat する。
DirEntry.is_dir: DirEntry_test_mode。Windows はシンボリックリンクのときだけ stat する。stat が FileNotFoundError なら偽を返し、ほかの失敗は送出する。
DirEntry.stat(follow_symlinks=False): Windows は一覧の情報（win32_lstat）を返し、OS を呼ばない。POSIX は lstat し、失敗は送出する。
os.stat（Windows、win32_xstat_impl）: CreateFileW が ERROR_ACCESS_DENIED、ERROR_SHARING_VIOLATION などで失敗すると、attributes_from_dir（FindFirstFileW）でディレクトリの一覧の情報を取り、成功として返す。そのとき st_ino は 0 になる。
```

# 4 回目のレビューのあとの実測（2026-11-11）

## file_id_probe.py（識別子を Win32 の呼び出しから直接取る方式）

```text
python 3.10.11 win32  file_id
  wiki と sub/loop（wiki を指すジャンクション）が同じ: True、期待どおり: True
  ext と j（ext を指すジャンクション）が同じ: True、期待どおり: True
  wiki と sub が違う: True、期待どおり: True
  ないパス: FileNotFoundError、期待どおり: True
  アクセスを拒まれるパス: PermissionError、期待どおり: True
  参考: os.stat の st_dev 0xb6dbc26f、FileIdInfo の VolumeSerialNumber 0xeeb6dbfbb6dbc26f、低い 32 ビットが同じ: True
  終了: よい
python 3.14.6 win32  file_id
  wiki と sub/loop（wiki を指すジャンクション）が同じ: True、期待どおり: True
  ext と j（ext を指すジャンクション）が同じ: True、期待どおり: True
  wiki と sub が違う: True、期待どおり: True
  ないパス: FileNotFoundError、期待どおり: True
  アクセスを拒まれるパス: PermissionError、期待どおり: True
  参考: os.stat の st_dev 0xeeb6dbfbb6dbc26f、FileIdInfo の VolumeSerialNumber 0xeeb6dbfbb6dbc26f、低い 32 ビットが同じ: True
  終了: よい
```

## 索引の側の、ふつうのファイルでない項目（実物の今の index_files() と、4 版目の試作）

```text
python 3.14.6 win32
  今の index_files(): ['index.md', 'indexes/broken.md', 'indexes/dirlink.md', 'indexes/ok.md']
  4 版目の index_files(): ['index.md', 'indexes/ok.md']
  ページ: 今 [] 4 版目 []
python 3.12.3 linux
  今の index_files(): ['index.md', 'indexes/broken.md', 'indexes/dirlink.md', 'indexes/ok.md', 'indexes/pipe.md']
  4 版目の index_files(): ['index.md', 'indexes/ok.md']
  ページ: 今 [] 4 版目 []
```

## CPython のソースで確かめたこと（4 回目のレビューの重大 1）

```text
3.12.13、3.14.6 の win32_xstat_slow_impl: GetFileInformationByHandleEx(hFile, FileIdInfo, ...) が失敗しても、エラーを見ずに pIdInfo を NULL のまま続ける。
同じ版の Python/fileutils.c の _Py_attribute_data_to_stat: st_dev = id_info ? id_info->VolumeSerialNumber : info->dwVolumeSerialNumber。FileIdInfo を取れないと、64 ビットではなく 32 ビットの値になる。
3.10.11: FileIdInfo を使わない。st_dev はいつも dwVolumeSerialNumber（32 ビット）、st_ino は nFileIndexHigh と nFileIndexLow から作る。
```

# 5 版目のための実測（2026-11-11）

## walk_v5.py（識別子を Win32 の呼び出しから直接取る。索引の今の集合を、今の規則で木から計算する）

照らした今の実装は、info-hive-wiki のコミット f0a758f（0.10.0）の wiki_pages.py と wiki_lint.py である。

### Windows 11、Python 3.10.11

```text
python 3.10.11 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True（今の実装は、Python 3.10 の rglob が Path の比較で重複を除くので、片方を落とした。挙げた違い）
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1716 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 848 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 424 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 348 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 100 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 80 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 72 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.12.13

```text
python 3.12.13 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1716 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 848 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 424 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 348 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 100 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 80 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 72 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.13.7

```text
python 3.13.7 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1716 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 848 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 424 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 348 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 100 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 80 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 72 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.14.6

```text
python 3.14.6 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 429 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 159 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 39 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 114 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 93 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 111 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 90 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1716 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 848 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 424 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 348 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 100 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 80 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 72 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  終了: よい
```

### 実物の wiki（Windows 11、Python 3.14.6）

```text
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  W0_Wiki: ページ 48 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 20 個、並びまで一致: True。索引 0 個、挙げた違いを除いて一致: True
  終了: よい
```

### Linux（WSL）、Python 3.12.3

```text
python 3.12.3 linux  check
  リンクを置いた木: ページ 11 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  名前に \ を含む: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  鍵が同じになる名前: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True（組の順が違った: ページ 今 ['a\\b.md', 'a/b.md', 'a0.md'] 案 ['a/b.md', 'a\\b.md', 'a0.md']、索引 今 [] 案 []）
  飛ばした（ジャンクションは Windows だけ）
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: 口の呼び出し 113 回、失敗を入れた実行 339 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 50 回、失敗を入れた実行 150 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 12 回、失敗を入れた実行 36 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 16 回、失敗を入れた実行 48 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 21 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 33 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 20 回、失敗を入れた実行 60 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 27 回、失敗を入れた実行 81 回、答えと違った実行 0 件
  名前に \ を含む、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  名前に \ を含む、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  鍵が同じになる名前、ページ: 口の呼び出し 19 回、失敗を入れた実行 57 回、答えと違った実行 0 件
  鍵が同じになる名前、索引: 口の呼び出し 2 回、失敗を入れた実行 6 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 987 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 438 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 219 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 160 件（例: リンクを置いた木、is_symlink(dirlink.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「並びの鍵を NFC だけにする」: 答えと違った実行 34 件（例: 名前に \ を含む、失敗なし: 答えと違う ['a0.md', 'a\\b.md', 'c/d.md']）
  終了: よい
```

# 5 版目のあとに自分で見つけたこと（2026-11-11）

## 自分を指すシンボリックリンクを 1 つ置いた wiki（verify_loop.py の出力）

`wiki/loop.md` → `loop.md`（自分を指すファイルのリンク）と、`wiki/sub/dloop` → `dloop`（自分を指すディレクトリのリンク）を置いた。失敗は入れていない。

```text
python 3.10.11 win32
  pathlib の _IGNORED_WINERRORS: (21, 123, 1921)
  Path.is_file の実装: self.stat() と _ignore_error
  リンク: ['作れた']
  今の iter_page_files(): ['a.md', 'sub/b.md']
  5 版目の walk_pages(): 送出 OSError 22 1921
  DirEntry.is_dir(): 送出 OSError 22 1921
  os.stat(): 送出 OSError 22 1921
python 3.12.13 win32
  pathlib の _IGNORED_ERRNOS: (2, 20, 9, 10062)
  pathlib の _IGNORED_WINERRORS: (21, 123, 1921)
  Path.is_file の実装: self.stat() と _ignore_error
  リンク: ['作れた']
  今の iter_page_files(): ['a.md', 'sub/b.md']
  5 版目の walk_pages(): 送出 OSError 22 1921
  DirEntry.is_dir(): 送出 OSError 22 1921
  os.stat(): 送出 OSError 22 1921
python 3.14.6 win32
  Path.is_file の実装: os.path.isfile
  リンク: ['作れた']
  今の iter_page_files(): ['a.md', 'sub/b.md']
  5 版目の walk_pages(): 送出 OSError 22 1921
  DirEntry.is_dir(): 送出 OSError 22 1921
  os.stat(): 送出 OSError 22 1921
python 3.12.3 linux
  pathlib の _IGNORED_ERRNOS: (2, 20, 9, 40)
  pathlib の _IGNORED_WINERRORS: (21, 123, 1921)
  Path.is_file の実装: self.stat() と _ignore_error
  リンク: ['作れた']
  今の iter_page_files(): ['a.md', 'sub/b.md']
  5 版目の walk_pages(): 送出 OSError 40 None
  DirEntry.is_dir(): 送出 OSError 40 None
  os.stat(): 送出 OSError 40 None
```

3.10 の `pathlib` の無視する errno の一覧の名前は `_IGNORED_ERROS`（綴りの誤りのまま）で、値は `(2, 20, 9, 10062)`（Windows の `errno.ELOOP` は 10062）。3.14 の `glob` は、`except OSError` ですべての失敗を無視する。


# 6 版目のための実測（2026-11-11）

## walk_v6.py（失敗の分け方を、今の実装の扱いの表から決め直した試作）

照らした今の実装は、info-hive-wiki のコミット f0a758f（0.10.0）の wiki_pages.py と wiki_lint.py である。

### Windows 11、Python 3.10.11

```text
python 3.10.11 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True（今の実装は、Python 3.10 の rglob が Path の比較で重複を除くので、片方を落とした。挙げた違い）
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1001 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 371 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 91 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 203 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 70 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 266 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 217 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 259 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4277 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1359 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1107 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 212 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1397 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1373 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1197 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.12.13

```text
python 3.12.13 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1001 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 371 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 91 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 203 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 70 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 266 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 217 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 259 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4277 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1359 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1107 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 212 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1397 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1373 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1197 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.13.7

```text
python 3.13.7 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1001 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 371 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 91 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 203 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 70 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 266 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 217 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 259 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4277 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1359 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1107 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 212 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1397 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1373 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1197 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.14.6

```text
python 3.14.6 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1001 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 371 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 91 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 49 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 77 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 203 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 70 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 119 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 266 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 217 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 168 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 259 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 210 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4277 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1359 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1107 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 212 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1397 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1373 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1197 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### 実物の wiki（Windows 11、Python 3.14.6）

```text
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  W0_Wiki: ページ 52 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 20 個、並びまで一致: True。索引 0 個、挙げた違いを除いて一致: True
  終了: よい
```

### Linux（WSL）、Python 3.12.3

```text
python 3.12.3 linux  check
  リンクを置いた木: ページ 11 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  名前に \ を含む: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  鍵が同じになる名前: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True（組の順が違った: ページ 今 ['a\\b.md', 'a/b.md', 'a0.md'] 案 ['a/b.md', 'a\\b.md', 'a0.md']、索引 今 [] 案 []）
  飛ばした（ジャンクションは Windows だけ）
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: 口の呼び出し 113 回、失敗を入れた実行 565 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 50 回、失敗を入れた実行 250 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 12 回、失敗を入れた実行 60 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 16 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 55 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 55 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 28 回、失敗を入れた実行 140 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 20 回、失敗を入れた実行 100 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 27 回、失敗を入れた実行 135 回、答えと違った実行 0 件
  名前に \ を含む、ページ: 口の呼び出し 19 回、失敗を入れた実行 95 回、答えと違った実行 0 件
  名前に \ を含む、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  鍵が同じになる名前、ページ: 口の呼び出し 19 回、失敗を入れた実行 95 回、答えと違った実行 0 件
  鍵が同じになる名前、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1835 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 741 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 494 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 360 件（例: リンクを置いた木、is_symlink(dirlink.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 439 件（例: リンクを置いた木、scandir(.) に loop: 送出した（OSError））
  対照「並びの鍵を NFC だけにする」: 答えと違った実行 66 件（例: 名前に \ を含む、失敗なし: 答えと違う ['a0.md', 'a\\b.md', 'c/d.md']）
  終了: よい
```

## longpath_probe.py（MAX_PATH を超えるページ）

```text
python 3.10.11 win32  longpath
  LongPathsEnabled: 1
  深いページのパスの長さ: 440
  今の iter_page_files(): ['a.md', 'deep.md']
  6 版目の walk_pages(): ['a.md', 'deep.md'] unlistable 0 unknown 0
python 3.14.6 win32  longpath
  LongPathsEnabled: 1
  深いページのパスの長さ: 440
  今の iter_page_files(): ['a.md', 'deep.md']
  6 版目の walk_pages(): ['a.md', 'deep.md'] unlistable 0 unknown 0
```

# 7 版目のための実測（2026-11-12）

## walk_v7.py（Windows の os.stat() が返すブロックデバイスの成功を「分からない」にした試作）

照らした今の実装は、info-hive-wiki のコミット f0a758f（0.10.0）である。3.12.13 は、同じ版の Python が 2 か所にあり、最初は 2 つが同じ作業フォルダーで同時に走って対照の件数が乱れたので、1 つだけで流し直した。下はその出力である。

### Windows 11、Python 3.10.11

```text
python 3.10.11 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True（今の実装は、Python 3.10 の rglob が Path の比較で重複を除くので、片方を落とした。挙げた違い）
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  .md の項目に os.stat() が S_IFBLK の成功を返す: ページ ['a.md']、unknown ['locked.md']、期待どおり: True
  終了: よい
python 3.10.11 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1018 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 380 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 92 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 79 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 205 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 172 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 270 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 219 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 213 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 261 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4353 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1402 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1150 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 240 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1470 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1442 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1238 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  対照「6 版目の試作（ブロックデバイスの成功で、ページを知らせなしに落とす）」: 答えと違った実行 51 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.12.13

```text
python 3.12.13 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  .md の項目に os.stat() が S_IFBLK の成功を返す: ページ ['a.md']、unknown ['locked.md']、期待どおり: True
  終了: よい
python 3.12.13 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1018 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 380 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 92 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 79 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 205 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 172 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 270 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 219 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 213 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 261 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4353 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1402 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1150 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 240 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1470 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1442 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1238 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  対照「6 版目の試作（ブロックデバイスの成功で、ページを知らせなしに落とす）」: 答えと違った実行 51 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.13.7

```text
python 3.13.7 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  .md の項目に os.stat() が S_IFBLK の成功を返す: ページ ['a.md']、unknown ['locked.md']、期待どおり: True
  終了: よい
python 3.13.7 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1018 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 380 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 92 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 79 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 205 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 172 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 270 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 219 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 213 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 261 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4353 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1402 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1150 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 240 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1470 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1442 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1238 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  対照「6 版目の試作（ブロックデバイスの成功で、ページを知らせなしに落とす）」: 答えと違った実行 51 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### Windows 11、Python 3.14.6

```text
python 3.14.6 win32  check
  リンクを置いた木: ページ 13 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  ジャンクションと通常のディレクトリが兄弟: ページ 4 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['j/c.md', 'plain/deep/y.md', 'plain/x.md', 'z.md'] 索引: []
  輪でないジャンクションの別名: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/x.md', 'alias/x.md'] 索引: []
  下を指すジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['a/b/c.md', 'a/j/c.md'] 索引: []
  循環: sub/loop と indexes が wiki を指す: ページ 2 個、索引 2 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'sub/b.md'] 索引: ['indexes/a.md', 'indexes/sub/b.md']
  循環: a/b/j が a を、a/me が a を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a/b/c.md', 'a/top.md'] 索引: []
  循環: 2 つのジャンクション: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['x/j1/q.md', 'x/p.md'] 索引: []
  循環: wiki の親を指す: ページ 2 個、索引 0 個、答えと一致: True。今の実装との照合はしない（循環）
    ページ: ['a.md', 'up/side/s.md'] 索引: []
  大文字と小文字を区別するフォルダー: ページ 今 ['p/A.md', 'p/a.md'] 案 ['p/A.md', 'p/a.md'] 一致 True。索引 今 ['indexes/A.md', 'indexes/a.md'] 案 ['indexes/A.md', 'indexes/a.md']、今の鍵で同じになる組の順を除いて一致 True
  失敗なし: ページ ['a.md', 'junc/c.md']、unknown []、期待どおり: True
  ジャンクションの FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  ジャンクションの先が識別子を持たない: ページ ['a.md']、unknown ['junc']、期待どおり: True
  起点の FileId が 0: ページ ['a.md']、unknown ['junc']、期待どおり: True
  循環、失敗なし: ページ ['a.md', 'sub/b.md']、unknown []、期待どおり: True
  循環、道筋の sub が識別子を持たない: ページ ['a.md', 'sub/b.md']、unknown ['sub/loop']、期待どおり: True
  兄弟: ページ ['j/c.md', 'plain/x.md']、unknown []、期待どおり: True
  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: True（呼んだ先 2 個）
  .md の項目の識別子が 0（開けないファイル）: ページ ['a.md', 'locked.md']、unknown []、期待どおり: True
  .md の項目に os.stat() が S_IFBLK の成功を返す: ページ ['a.md']、unknown ['locked.md']、期待どおり: True
  終了: よい
python 3.14.6 win32  explore
  リンクを置いた木、ページ: 口の呼び出し 143 回、失敗を入れた実行 1018 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 53 回、失敗を入れた実行 380 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 13 回、失敗を入れた実行 92 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 51 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 14 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 79 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 29 回、失敗を入れた実行 205 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 72 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 17 回、失敗を入れた実行 121 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 24 回、失敗を入れた実行 172 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、ページ: 口の呼び出し 38 回、失敗を入れた実行 270 回、答えと違った実行 0 件
  ジャンクションと通常のディレクトリが兄弟、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  輪でないジャンクションの別名、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  輪でないジャンクションの別名、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  下を指すジャンクション、ページ: 口の呼び出し 31 回、失敗を入れた実行 219 回、答えと違った実行 0 件
  下を指すジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、ページ: 口の呼び出し 24 回、失敗を入れた実行 170 回、答えと違った実行 0 件
  循環: sub/loop と indexes が wiki を指す、索引: 口の呼び出し 30 回、失敗を入れた実行 213 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、ページ: 口の呼び出し 37 回、失敗を入れた実行 261 回、答えと違った実行 0 件
  循環: a/b/j が a を、a/me が a を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: 2 つのジャンクション、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  循環: wiki の親を指す、ページ: 口の呼び出し 30 回、失敗を入れた実行 212 回、答えと違った実行 0 件
  循環: wiki の親を指す、索引: 口の呼び出し 2 回、失敗を入れた実行 15 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 4353 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 1812 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 1402 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 1150 件（例: リンクを置いた木、is_symlink(.hidden.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「識別子を取れないとき、パスの文字列で比べる」: 答えと違った実行 240 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「3 版目の試作（道筋の識別子が兄弟に漏れる）」: 答えと違った実行 1470 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep'), ('stat', 'real')]）
  対照「4 版目の試作（識別子を os.stat() から取る）」: 答えと違った実行 1442 件（例: リンクを置いた木、失敗なし: 木から決まらない呼び出しをした [('stat', '.'), ('stat', 'junc'), ('stat', 'junc/deep')]）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 1238 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  対照「6 版目の試作（ブロックデバイスの成功で、ページを知らせなしに落とす）」: 答えと違った実行 51 件（例: リンクを置いた木、失敗なし: 木から決まる呼び出しをしなかった [('file_id', '.'), ('file_id', 'junc'), ('file_id', 'junc/deep')]）
  終了: よい
```

### 実物の wiki（Windows 11、Python 3.14.6）

```text
python 3.14.6 win32  wikis
  wiki: ページ 4 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  W0_Wiki: ページ 56 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 7 個、並びまで一致: True。索引 1 個、挙げた違いを除いて一致: True
  wiki: ページ 20 個、並びまで一致: True。索引 0 個、挙げた違いを除いて一致: True
  終了: よい
```

### Linux（WSL）、Python 3.12.3

```text
python 3.12.3 linux  check
  リンクを置いた木: ページ 11 個、索引 9 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がシンボリックリンク: ページ 1 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  indexes がページのディレクトリを指す: ページ 1 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
    ページ: ['concepts/c.md'] 索引: ['index.md', 'indexes/c.md']
  indexes がファイル: ページ 1 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  空の wiki: ページ 0 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  NFC と NFD の名前: ページ 2 個、索引 2 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  解けないリンク: ページ 2 個、索引 1 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  索引の下の、ふつうのファイルでない項目: ページ 1 個、索引 3 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  名前に \ を含む: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True
  鍵が同じになる名前: ページ 3 個、索引 0 個、答えと一致: True。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ True、索引 True（組の順が違った: ページ 今 ['a\\b.md', 'a/b.md', 'a0.md'] 案 ['a/b.md', 'a\\b.md', 'a0.md']、索引 今 [] 案 []）
  飛ばした（ジャンクションは Windows だけ）
  終了: よい
python 3.12.3 linux  explore
  リンクを置いた木、ページ: 口の呼び出し 113 回、失敗を入れた実行 565 回、答えと違った実行 0 件
  リンクを置いた木、索引: 口の呼び出し 50 回、失敗を入れた実行 250 回、答えと違った実行 0 件
  indexes がシンボリックリンク、ページ: 口の呼び出し 12 回、失敗を入れた実行 60 回、答えと違った実行 0 件
  indexes がシンボリックリンク、索引: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、ページ: 口の呼び出し 16 回、失敗を入れた実行 80 回、答えと違った実行 0 件
  indexes がページのディレクトリを指す、索引: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がファイル、ページ: 口の呼び出し 7 回、失敗を入れた実行 35 回、答えと違った実行 0 件
  indexes がファイル、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  空の wiki、ページ: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  空の wiki、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  NFC と NFD の名前、ページ: 口の呼び出し 11 回、失敗を入れた実行 55 回、答えと違った実行 0 件
  NFC と NFD の名前、索引: 口の呼び出し 11 回、失敗を入れた実行 55 回、答えと違った実行 0 件
  解けないリンク、ページ: 口の呼び出し 28 回、失敗を入れた実行 140 回、答えと違った実行 0 件
  解けないリンク、索引: 口の呼び出し 10 回、失敗を入れた実行 50 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、ページ: 口の呼び出し 20 回、失敗を入れた実行 100 回、答えと違った実行 0 件
  索引の下の、ふつうのファイルでない項目、索引: 口の呼び出し 27 回、失敗を入れた実行 135 回、答えと違った実行 0 件
  名前に \ を含む、ページ: 口の呼び出し 19 回、失敗を入れた実行 95 回、答えと違った実行 0 件
  名前に \ を含む、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  鍵が同じになる名前、ページ: 口の呼び出し 19 回、失敗を入れた実行 95 回、答えと違った実行 0 件
  鍵が同じになる名前、索引: 口の呼び出し 2 回、失敗を入れた実行 10 回、答えと違った実行 0 件
  失敗を入れた実行の合計: 1835 回
  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:
  対照「どの失敗も「ない」にする」: 答えと違った実行 741 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「権限を知らせずに飛ばす」: 答えと違った実行 494 件（例: リンクを置いた木、scandir(.) に denied: 答えと違う。答え ([], ['.'], [])、走査 ([], [], [])）
  対照「知らせがあったら全ページを捨てる」: 答えと違った実行 360 件（例: リンクを置いた木、is_symlink(dirlink.md) に denied: 答えと違う。答え (['.obsidian/o.md', 'Upper.MD', 'a.md', 'concepts/.NET/c.md', 'concepts/raw/cr）
  対照「5 版目の試作（解けないリンクで送出する）」: 答えと違った実行 439 件（例: リンクを置いた木、scandir(.) に loop: 送出した（OSError））
  対照「並びの鍵を NFC だけにする」: 答えと違った実行 66 件（例: 名前に \ を含む、失敗なし: 答えと違う ['a0.md', 'a\\b.md', 'c/d.md']）
  終了: よい
```
