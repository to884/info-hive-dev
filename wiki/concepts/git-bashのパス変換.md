---
type: "concept"
title: "Git Bash のパス変換で git の引数が壊れる"
tags: ["windows"]
sources: ["取り込み手順の追従とリリース-wiki-0.11.1"]
created: 2026-11-13
updated: 2026-11-13
---

# Git Bash のパス変換で git の引数が壊れる

Windows の Git Bash（MSYS2 の bash）は、Windows のプログラムに渡す引数のうち、POSIX のパスの並びに見えるものを、Windows のパスに書き換える。`git show <リビジョン>:<パス>` の引数がこれに当たると、`/` が `\` に、`:` が `;` に変わり、git が引数を読めなくなる。

```text
$ git show origin/main:.claude-plugin/plugin.json
fatal: ambiguous argument 'origin\main;.claude-plugin\plugin.json': unknown revision or path not in the working tree.
```

## 確かめた形

2026-11-13 に、GNU bash 5.2.26（x86_64-pc-msys）で確かめた。

| 引数 | 結果 |
| --- | --- |
| `origin/main:.claude-plugin/plugin.json` | 書き換えられて失敗する |
| `"origin/main:.claude-plugin/plugin.json"`（引用符で囲む） | 書き換えられて失敗する |
| `MSYS_NO_PATHCONV=1 git show origin/main:.claude-plugin/plugin.json` | 動く |
| `origin/main:CHANGELOG.md`（`:` の右に `/` がない） | 動く |
| `origin/main:./.claude-plugin/plugin.json` | 動く |
| `origin/main`（`:` がない。`git log` などに渡す） | 動く |

> 確かめた形の表 補足: 引用符はシェルの単語の分け方を変えるだけで、MSYS の書き換えは止めない。書き換えられたのは、`:` の右が `/` を含み、`./` で始まらない形だけだった。MSYS がどの形を書き換えるかの規則の全体は確かめていない。

## 避け方

- コマンドの前に `MSYS_NO_PATHCONV=1` を付ける。1 つのシェルで何度も使うなら `export MSYS_NO_PATHCONV=1` にする。
- ただし、Windows のパスに直してほしい引数（`/c/Users/...` を Windows のプログラムに渡すときなど）も書き換えられなくなる。必要なコマンドだけに付ける。
- `git show` のパスは、`./` から書いても避けられる。

## 起きた所

wiki 0.11.1 と rag 0.5.1 のリリースで、`origin/main` の `plugin.json` の版を確かめるときに 2 回起きた。2 回とも `MSYS_NO_PATHCONV=1` を付けて確かめ直した（[[取り込み手順の追従とリリース-wiki-0.11.1]]）。`git grep <パターン> origin/main -- <パス>` と `git ls-tree origin/main <パス>` は、念のため同じものを付けて実行した。
