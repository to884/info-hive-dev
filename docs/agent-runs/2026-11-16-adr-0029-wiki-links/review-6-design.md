## 判定

**却下。確信度：高。** 新しく設けた依存の完全性判定が、本文を読めなかった記事を取りこぼす。また、raw の検査には、リンクを検査対象から外す経路と、対象外の項目まで検査する経路がある。

以下は仕様の静的な反例であり、未実装の書く段による原本破壊を実測したものではない。

## 致命的・重大な欠陥

### 1. 重大：本文を読めなかった記事があっても、依存収集を完全と判定できる

**主張：** `Walk.files` に載ることと、本文を読めることを同一視している。追加した `complete` の条件には、列挙後の読み取り失敗が入っていない。

**反例：**

1. `sources/s.md` は通常ファイルで、一覧と `lstat()` は成功する。本文には `raw: concepts/original.md` がある。
2. ファイルの読み取り権限だけがなく、本文を開くと `PermissionError` になる。
3. 走査には両ファイルが載り、`links`、`unlistable`、`unknown` はすべて空になる。
4. 現行の `wiki_search.collect_pages()` は本文の読み取り失敗を飛ばす。収集結果から `s.md` とその原本参照が消える。
5. 発見できた `raw:` がないため、本設計の条件では `complete=True` にでき、`original.md` の保護が成立しない。

指定版の `collect_pages()` を抽出し、読み取りをメモリ上で差し替えたところ、上記の走査結果から原本ページだけが収集され、raw 依存は空になった。

**根拠：**

- [設計書149行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:149)は `files` を「読めた記事」と呼び、完全性を走査の知らせと raw の解決結果で定義している。
- 指定版 `wiki_pages.py:288–296` は、属性だけで `MdFile` を作る。本文は読まない。
- 指定版 `wiki_search.py:273–289` は、本文の `OSError` と文字コードの誤りを飛ばす。
- [設計書153行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:153)の試験対象には、この失敗がない。

過去の「リンクで拒んだ source の依存が落ちる」という指摘とは異なる。今回は**リンクがなく、走査も完全な通常ファイル**で、新しく定義した完全性条件が崩れる。

### 2. 重大：登録後にリンクになった PDF を、外の原本へ分類し直して検査から外す

**主張：** `raw:` が守る木の中かを、最終要素まで解決して判定すると、木の中に作られたリンクの名前を見失う。

**反例：**

1. raw の根を `C:/data/raw` とする。
2. 通常ファイル `C:/data/raw/book.pdf` を rag で登録する。source ページには `rag_job_id:` と `raw: C:/data/raw/book.pdf` が記録される。
3. 登録後、その PDF を、`D:/Books/book.pdf` を指すシンボリックリンクへ置き換える。
4. lint は記録された raw パスを解決する。解決先は守る木の外になる。
5. `rag_job_id:` のある外の原本と分類され、リンク検査から外れる。

登録時のチェックには違反していない。登録後に作られたリンクを lint が見逃す反例である。

**根拠：**

- [設計書31行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:31)は、外の原本を検査対象外にし、守る木の中にある場合だけ検査する。
- [設計書88行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:88)は、`raw:` の所属を解決済みパスどうしで比べる。
- [設計書97行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:97)の「raw はシンボリックリンクを指さない」は、登録時点についてしか成り立たない。指定 rag 版の `rag_config.py:199–213` も、登録時の解決である。

文書が認めた「規則の前にリンクを登録していた場合」の制限では説明できない。

### 3. 重大：ディレクトリを指す raw の検査が、記事でない隠し項目まで違反として返す

**主張：** raw の記事の範囲と、検査に使う `find_links()` の範囲が一致していない。

**反例：**

```text
raw: C:/data/raw/bundle

bundle/document.txt       通常ファイル
bundle/.cache/copy.bin    外部ファイルとのハードリンク
```

隠しディレクトリとその下は記事ではない。しかし、lint は解決先の `bundle` に `find_links()` を当てる。この関数は全項目を調べるため、`.cache/copy.bin` を `links` に返す。

同じ検査を使う2 wiki 問い合わせも、記事でないリンクだけで停止し得る。

**根拠：**

- [設計書25行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:25)と27行は、raw の記事と隠し項目の除外を定義している。
- [設計書107行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:107)は、raw の解決先に `find_links()` を当てる。
- [設計書118行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:118)の同関数は「その下のすべての項目」を対象にし、問い合わせ補助もこれを使う。
- この経路で記事の規則による絞り込みを行う契約はない。

取り込み直後の確認が全項目を調べることとは別問題である。lint と問い合わせにも、その範囲が持ち込まれている。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 走査に載った記事は本文も読める | 属性の取得は成功し、本文の読み取りだけが失敗する |
| 登録時に解決した `result.raw` は、その後もリンクを指さない | 登録後にファイルや途中のディレクトリがリンクへ変わる |
| raw ディレクトリ全体のリンク検査は、記事の検査と同じになる | 対象外の隠し項目にリンクがある |

## 見落としと軽微な問題

- **軽微：`missing` と完全性の契約が衝突する。** [149行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:149)は「すべての raw が1つに解けたとき」を完全とする一方、150行は存在しない raw を飛ばす既存仕様を残す。削除済みの原本を参照するページが1件ある場合、書く段を止めるかどうかが一致しない。
- **軽微：`missing_raw()` との一致を要求する試験は、新しい基準選択と両立しない。** [163行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:163)は旧結果と新しい `missing` の一致を要求する。しかし、セッションの raw が wiki の親にはなく、wiki の根の基準にだけ存在する場合、旧関数は「ある」、新仕様は `missing` になる。旧関数を抽出したメモリ上の確認でも、この差を確認した。

## 検証した事実

- wiki `2452f59475f0c5b04e7c7aeef075c47b315cf813`、rag `c59d05e26add60a9b706141f83f662b81c265533` を `git show` で照合した。
- 設計書が挙げる `_stat_entry()`、`list_index()`、`raw_ref_of()`、旧 `missing_raw()` の行番号と説明は、確認した範囲で一致した。
- ローカルの `origin/main` は wiki v0.21.1。指定版からのスクリプト差分が `wiki_pdf.py` と `wiki_pdf_layer.py` の追加だけという記述も一致した。
- 本文読み取り失敗時の収集結果と、セッション raw の旧存在判定は、指定版から抽出した関数で確認した。
- 新しい `resolve_raw()`、`complete`、書き込み部品の実行結果は未検証。ファイル変更、リンク作成、属性変更は行っていない。

## 崩せなかった点

- リンクで拒んだ記事を `Walk.links` に残し、その依存収集を不完全として書く段を止める契約は、過去のリンク記事の反例を塞いでいる。
- `list_index()` の直接読み取りを専用の読む口へ移す方針は、過去の指摘を具体的に対象としている。
- 通常の書き込みで、既存ハードリンクを置き換えず拒む契約は、今回の本文と試験一覧で一致している。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
