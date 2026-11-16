走査が `index.md` を拒んだ結果を返す状態をメモリ上で与えても、現行の MCP の索引処理は本文を直接返しました。修復処理と書き込み検査の矛盾、`Writer` の作業用領域に渡せる根の欠落も含め、根拠が確認できた指摘をまとめます。
## 判定

**却下。確信度：高。** リンクの修復が書き込み検査によって拒まれる矛盾と、共通走査を変更してもリンクの記事を読み続ける経路が残る。また、下層に渡せる根の制限が、ADR-0023 の作業用領域を扱えない。

コードの行番号は、wiki は `2452f59`、rag は `c59d05e` のもの。以下は作者の決定そのものではなく、その具体化の欠陥である。

## 致命的・重大な欠陥

### 1. 重大：修復対象のリンクを、修復に使う書き込み部品が拒む

**主張：** `wiki_links.py fix` に要求した修復と、その書き込みに適用する検査を同時に満たせない。

**反例：**

```text
wiki の根: C:/data/wiki
C:/data/wiki/sources/a.md → C:/original/a.md
```

利用者がこのシンボリックリンクの修復を承認したとする。

- ADR の直し方では、中身を一時ファイルに写し、リンクの名前を `os.replace()` で置き換える。
- `fix` の書き込みは、下層の書き込み部品を通す。
- 下層は `Writer` の検査 a と同じ条件で、行き先そのものも検査する。既存の `sources/a.md` はリンクなので拒まれる。
- 先にリンクを削除する方法も、削除を同じ検査に通す限り拒まれる。

ジャンクションを消して実ディレクトリに置き換える場合も同じである。承認の有無では解消しない。修復対象の末尾のリンクを扱う契約がなく、記載どおりでは通常の修復が成立しない。

**根拠：** [ADR-0029 の修復処理](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:174)、同 198 行の「行き先まで」の検査、同 234〜235 行の置き換え方法。[書く段の設計](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:381)は削除も `Writer` に通し、385 行の検査 a は既存の行き先自体のリンクも拒む。**結果：設計内の矛盾。**

### 2. 重大：共通走査を変えても、MCP の `list_index` はリンクの索引を直接読む

**主張：** 「読むときはリンクを拒む走査で読む」という説明は、現行の読み取り経路を覆っていない。

**反例・手順：**

1. `W/index.md` を、別の wiki のページとのハードリンクにする。
2. 提案後の `walk_index_files(W)` が、このファイルを拒み、`files` から除外したとする。
3. MCP の `list_index(wiki=W)` を呼ぶ。

`wiki_index.list_index()` は、一覧の収集には `walk_index_files()` を使うが、最上位の本文は別に処理する。979 行で `index_md.is_file()` を調べ、直接 `read_text()` するため、拒んだファイルの本文を返す。

`name` を指定する分岐にも同じ問題がある。`W/indexes/x.md` が別のページとのハードリンクなら、957〜964 行の直接読み取りを通る。この分岐は共通走査を呼ばない。

指定版から関数を抽出し、**走査結果を `files=[]`、`links=[("index.md", "hardlink")]` としたメモリ上の実行でも、`index` に本文が返る**ことを確認した。実ファイルは作成していない。

**根拠：** [ADR-0029 の読み取り方針](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:68)、同 152 行の共通走査の変更。[wiki_index.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:954)の `list_index()`。MCP は [wiki_mcp_server.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:356)で、この関数を直接呼ぶ。**結果：現行コードとの照合で読み取り経路の漏れ。**

### 3. 重大：下層に渡せる根を wiki と raw だけにすると、`Writer` の作業用領域を扱えない

**主張：** 下層の根の制限と、「ADR-0023 の `Writer` の領域は変えない」という約束が両立しない。

**反例となる通常の配置：**

```text
W = C:/data/wiki
R = C:/data/raw
K = C:/Users/u/AppData/Local/info-hive/apply/work
```

ADR-0023 の `begin` は、`K/<名前>-<乱数>/` に作業用ディレクトリを作る。`Writer` はこの書き込みにも道の検査を適用する。

ところが ADR-0029 は、その検査を下層へ切り出したうえで、下層に渡せる根を **wiki の根か raw の根のどちらかだけ**に限定する。`K` はどちらの下でもなく、ADR-0023 の作業用の検査が必要とする起点を渡せない。

これは前回の `.wiki-cache` の反例とは別である。今回は、根を制限した結果、既存設計の正規の書き込み先が契約から脱落する。`Writer` だけに `K` を許す例外も書かれていない。

**根拠：** [ADR-0029 の下層と上層の分担](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:198)、同 201 行の ADR-0023 を変えないという説明。[書く段の設計](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:320)の `K` の配置と定義、385〜389 行の作業用領域の検査。**結果：設計間の契約の矛盾。**

### 4. 重大：「記事」の定義が `.git/` と隠しファイルについて実際の走査と食い違う

**主張：** 現行の走査関数で記事を定義する部分と、対象外を列挙する部分が、同じ入力を別々に分類する。

**反例 A：**

```text
W/.git/info/notes.md
```

現行の `SKIP_TOP_LEVEL_DIRS` に `.git` は入っていない。通常のディレクトリなら走査が降り、`is_page_path(".git/info/notes.md")` も真を返す。したがって 55 行の定義では記事だが、57 行では `.git/` は対象外である。

指定版の `is_page_path()` を抽出して実行し、この入力が真になることを確認した。リンク拒否だけを足す変更では、この食い違いは消えない。

**反例 B：**

```text
W/indexes/.private.md
```

`walk_index_files()` は `walk_markdown()` の結果をそのまま加える。こちらには、ページ側の `is_page_path()` にある隠しファイルの除外がない。そのため隠し Markdown も索引として返す。55 行では記事、57 行では隠しファイルとして対象外になる。

リンクにした場合、どちらの定義に従うかで lint の結果と修復対象が変わる。作者が明示的に対象外とした `.git/` 内のファイルが、修復の候補になる契約になっている。

**根拠：** [ADR-0029 の記事と対象外の定義](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:55)。[wiki_pages.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:36)の除外定数と `is_page_path()`、同 301〜321 行のページ・索引の走査。**結果：事実の記述と対象範囲の不一致。**

## 崩れる前提

- **通常の書き込みとリンクの修復に、同じ拒否条件をそのまま使える。** 修復は、通常の書き込みが拒むリンクの名前を変更・削除する必要がある。
- **記事を読む経路は共通走査を必ず通る。** MCP の `list_index` に直接読み取りがある。
- **`Writer` が必要とする検査の起点は、wiki と raw の根だけで足りる。** wiki と raw の外に置く作業用領域 `K` がある。
- **現行のページ・索引の集合は、列挙した対象外と一致する。** `.git/` 内の Markdown と索引の隠し Markdown で崩れる。

## 見落としと軽微な問題

- **軽微：`Walk.links` を追加するだけでは、欠落の通知は利用者まで届かない。** 現行の `iter_page_files()` は走査の知らせを捨て、検索と lint はこれを使う。閲覧の `walk_inputs()` も `unlistable` と `unknown` は見るが、新しい `links` を伝える経路はない。ADR の「黙って消えないように」という説明に対し、呼び出し側の変更範囲が不足している。根拠：[wiki_pages.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:324)、[wiki_search.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:264)、[wiki_browse_fs.py](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1413)。
- **軽微：旧版の指示が残る。** ADR の 68 行は索引・ログを「記事でないファイル」と呼び、77 行は `links` の直しを利用者が行うとする。282 行には「守る木の中のリンクのソースを取り込まないこと」が残る。いずれも今回の決定・手順と一致しない。根拠：[ADR-0029](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:68)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 走査は `.md` に既存の `os.stat()` を呼ぶ | **一致。** `_stat_entry()` は `os.stat()` を呼び、その結果を使う |
| 既存の結果からハードリンクを判定できる | **一致。** `st_nlink` を利用できる。Windows の `DirEntry.stat()` が各識別値を 0 にする制約とは別である。[Python 3.14 の公式文書](https://docs.python.org/3.14/library/os.html#os.DirEntry.stat) |
| 現行の走査はジャンクションに降り、途中のディレクトリのシンボリックリンクには降りない | **一致。** `wiki_pages.py` の 257〜286 行 |
| `.git/` と隠し索引は現行の走査で除外される | **食い違い。** 重大な欠陥の 4 のとおり |
| rag は指定パスを検証し、解決したパスを `result.raw` に返す | **一致。** `rag_config.py` の 181〜209 行、`rag_index.py` の 661 行 |
| 名前の代理のビットは別の名前の実体を表す | **一致。** [Microsoft の定義](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-tags)と合う |
| Windows の読み取り専用ハードリンクの属性共有、置き換え失敗、OneDrive の観察結果 | **確かめられず。** 今回はリンク作成・属性変更を実施していない |

ファイルは変更していない。実行した反例確認は、指定版から抽出した関数とメモリ上の代替入力によるものに限る。

## 崩せなかった点

- 検索キャッシュの書き手に wiki の根を渡せば、前回の `.wiki-cache` 自身を検査から外す反例は成立しない。
- `rag_job_id:` のない過去のセッション raw を、現在の raw の根の外にあるという理由だけで除外する記述はなくなっている。
- 一意の一時ファイルを排他的に作り、名前を置き換える方式そのものから、既存ハードリンクの他方の中身を書き換える反例は見つからなかった。
- ADR-0017 の入力読み取り方針を一部置き換えることと、ADR-0019 の初期化判定を維持することは明記されている。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
