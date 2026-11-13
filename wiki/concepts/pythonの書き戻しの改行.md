---
type: "concept"
title: "Windows の Python で読んで書き戻すと LF が CRLF に変わる（標準出力も同じ）"
tags: ["windows"]
sources: ["取り込み手順の追従とリリース-wiki-0.11.1", "titleが値なしや配列のときの修正-wiki-0.12.2"]
created: 2026-11-13
updated: 2026-11-13
---

# Windows の Python で読んで書き戻すと LF が CRLF に変わる（標準出力も同じ）

Windows の Python で、LF のファイルを `Path.read_text` で読み、`Path.write_text` で書き戻すと、改行がすべて CRLF に変わる。文字列の置き換えを 1 か所しかしていなくても、git の差分はファイル全体になる。

## 確かめたこと

2026-11-13 に、Windows の Python 3.14.6 で確かめた。

| 操作 | 結果 |
| --- | --- |
| LF のファイルを `read_text` で読み、`write_text(t, encoding="utf-8")` で書く | CRLF になる |
| 同じく `write_text(t, encoding="utf-8", newline="\n")` で書く | LF のまま |
| CRLF のファイルを `read_text` で読む | 文字列の改行は LF になる |

> 確かめたことの表 補足: テキストモードで書くと、Python は `\n` を Windows の既定の改行（CRLF）に直して書く。読むときは CRLF を `\n` に直すので、読んだ文字列からは元の改行が分からない。ほかの版の Python では確かめていない。

## 避け方

- `write_text` に `newline="\n"` を渡す。
- または、`read_bytes` と `write_bytes` でバイト列のまま置き換える。
- エディターのツール（Edit や Write）で直せる編集なら、そちらを使う。

## 標準出力も CRLF になる

Windows の Python の標準出力も、テキストモードなので `\n` を CRLF にして書く。`-X utf8` を付けても変わらない。シェルでファイルにリダイレクトしても、パイプで次のコマンドに渡しても同じである。2026-11-13 に、Windows の Python 3.14.6 で確かめた。

| 書き方 | 出力のバイト |
| --- | --- |
| `sys.stdout.write("a\nb\n")`、`print("a")` | `a\r\nb\r\n` |
| `sys.stdout.buffer.write(b"a\nb\n")` | `a\nb\n` |
| `sys.stdout.reconfigure(newline="\n")` のあとに `sys.stdout.write("a\nb\n")` | `a\nb\n` |

> 標準出力の表 補足: Python の小さなスクリプトで文字を取り出してファイルに書き、ほかのファイルとバイトで比べると、改行だけが違って「一致しない」と出る。比べる前に、両方の改行をそろえるか、`sys.stdout.buffer` に書く。

## 気づき方

- `git diff --stat` の行数が、変えた行数よりずっと多い。
- `file <ファイル>` が `with CRLF line terminators` と出す。
- `git ls-files --eol <パス>` の作業ツリーの欄（`w/`）が `w/crlf` になる。
- Git Bash の `grep -c $'\r$'` は、`-U` を付けないと CR を数えず、CRLF のファイルでも 0 を返す。`grep -c -U $'\r$'` なら数えた。

## 起きた所

wiki の記録（to884/info-hive-dev#82）を作るとき、`SCHEMA.md`、`index.md`、`log.md` とソースのページを Python で書き換えて起きた。コミットの前に `git diff --stat` で気づき、`write_bytes` で LF に戻した（[[取り込み手順の追従とリリース-wiki-0.11.1]]）。

wiki v0.12.2 のリリースの確かめでは、CHANGELOG の節を Python の標準出力でファイルに取り出した。そのファイルが CRLF になり、GitHub リリースの本文（LF）と比べて「違う」と出た。先頭のバイトを比べて気づいた（[[titleが値なしや配列のときの修正-wiki-0.12.2]]）。
