---
type: "concept"
title: "Windows の Python で読んで書き戻すと LF が CRLF に変わる"
tags: ["windows"]
sources: ["取り込み手順の追従とリリース-wiki-0.11.1"]
created: 2026-11-13
updated: 2026-11-13
---

# Windows の Python で読んで書き戻すと LF が CRLF に変わる

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

## 気づき方

- `git diff --stat` の行数が、変えた行数よりずっと多い。
- `file <ファイル>` が `with CRLF line terminators` と出す。
- `git ls-files --eol <パス>` の作業ツリーの欄（`w/`）が `w/crlf` になる。
- Git Bash の `grep -c $'\r$'` は、`-U` を付けないと CR を数えず、CRLF のファイルでも 0 を返す。`grep -c -U $'\r$'` なら数えた。

## 起きた所

wiki の記録（to884/info-hive-dev#82）を作るとき、`SCHEMA.md`、`index.md`、`log.md` とソースのページを Python で書き換えて起きた。コミットの前に `git diff --stat` で気づき、`write_bytes` で LF に戻した（[[取り込み手順の追従とリリース-wiki-0.11.1]]）。
