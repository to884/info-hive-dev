## 判定

**条件付きで採用可**（確信度: 中）

構造を変えた `_article_rel` は、前回の反例を手元で拒否しました。反例は、wiki の外のディレクトリの別名が `wiki/concepts/jump`（外へのジャンクション）を指す配置です。グラフと lint の拒否の扱いも、方針どおりでした。

ただし、同じ種類の迂回が、入力の「最後の要素」に残っています。wiki の外のファイルのシンボリックリンクを経由すると、wiki の中のリンクの道の先も、拒否すべきハードリンクの記事も、検査せずに読みます（Windows で再現）。利用者が外にリンクを作って渡す必要があるので、軽微とします。

## 致命的・重大な欠陥

なし

## 崩れる前提

- **前提: 外の別名は、要素ごとにリンクを展開すれば、根の規則を引き継げる**（方針 1）
  - 崩れる条件: 別名が入力の最後の要素、つまりファイルのシンボリックリンクのときです。
  - 原因: ループは、`directory` が偽で残りの要素が 1 つになると `return None` で抜けます（差分の `wiki_pages.py` の `if not pending or (not directory and len(pending) == 1): return None`）。最後の要素は lstat も `readlink` もしません。`user_file_path` は wiki の外のファイルとして、そのままのパスを返します。そのパスを OS が読むと、リンクがたどられます。
  - 再現（Windows、開発者モードでファイルのシンボリックリンクを作成、手元で実行。プローブは `file_alias_probe.py`）:
    1. `wiki/concepts/jump` を `ext` へのジャンクションにし、`ext/a.md` に `OUTSIDE` と書く。
    2. `wiki/concepts/h.md` を作り、`ext/h-copy.md` とハードリンクにする。
    3. wiki の外に `x.md` を `wiki/concepts/jump/a.md` へのシンボリックリンクとして作り、`read_user_bytes(x.md, wiki)` を呼ぶ。結果は `b'OUTSIDE'` だった。
    4. wiki の外に `y.md` を `wiki/concepts/h.md` へのシンボリックリンクとして作り、`read_user_bytes(y.md, wiki)` を呼ぶ。結果は `b'HARDLINKED'` だった。
    5. 比較のため、ディレクトリの別名 `view/a.md` を渡すと、`リンクなので読まない: concepts/jump（junction）` で拒否した。`view2/h.md`（`view2` は `wiki/concepts` を指す）も、`リンクなので読まない: concepts/h.md（hardlink）` で拒否した。
  - 評価:
    - docstring の「ファイル自身は解決しない」は、以前からの設計です。
    - ただ、ファイルのシンボリックリンクはハードリンクと違い、lstat で見分けられます。方針 1 の「外の別名にも根の規則を引き継ぐ」は、ディレクトリの別名にしか成り立っていません。
- **前提: `os.readlink` は、`link_kind` がリンクとみなすすべての再解析点を読める**（推測、未実行）
  - 崩れる条件: Windows で、wiki の外の祖先に、名前の代理のビットが立つ symlink とジャンクション以外の再解析点があるときです。例は、WSL が NTFS に作る `IO_REPARSE_TAG_LX_SYMLINK` です。
  - 起きること:
    - `link_kind` はこれを `"reparse"` として展開しようとします。
    - CPython の Windows の `os.readlink` は、symlink とジャンクション以外に、`OSError` ではなく `ValueError("not a symbolic link")` を送出すると理解しています（未確認）。
    - そうなら、`except OSError` を素通りします。呼び出し元には、英語の `not a symbolic link` の ValueError として伝わります。
  - 影響: 拒否の向きなので、読まない側に寄ります。ただし、以前は wiki の外として読めた利用者のファイルが、意図しない文言で失敗するようになります。
- **前提: wiki の外の祖先は、いつでも lstat できる**
  - 崩れる条件: wiki の外の祖先の属性を取れないときです。以前は `realpath` が `OSError` になり、`continue` で外として扱っていました。今は `ValueError("パスの所属を調べられない: ...")` で止まります。
  - 影響: 安全な向きの変化ですが、wiki の外の利用者のファイルでも止まるようになりました（推測、未実行）。

## 見落としと軽微な問題

1. **軽微: ファイルのシンボリックリンクの経由で、拒否すべき記事を読む**（上の 1 件目、再現済み）
   - 前回直したディレクトリの別名と同じ種類の迂回が、最後の要素に残っています。
2. **軽微: 拒否を知らない解決が、lint と閲覧とグラフの外に残る**（コードを読んで確認、今回の差分の範囲外）
   - `wiki_search.link_key`（`wiki_search.py:263-265`）と `wiki_decide`（`wiki_decide.py:567`）は、`resolve_link` を直接呼びます。
   - そのため、`concepts/b.md` を拒否し、`entities/b.md` が読めるとき、`[[b]]` を `entities/b` に結び付けます。方針 3 で lint に入れた「拒否を先に判定する」規則と食い違います。
3. **軽微（推測）: `GraphPages` の拒否の情報は、リストを作り直すと消える**
   - `build_edges` は、`pages` の `link_warnings` 属性を既定として使います。今の呼び出し元（`wiki_graph_extract.py:1169-1172`、`wiki_graph_lint.py:94` と `217-218`）は、`collect_pages` の戻り値をそのまま渡すので、正しく動きます。
   - 将来、`sorted(pages)` や内包表記で並べ直してから渡すと、属性が消えます。その場合、黙って `()` に戻り、拒否した名前を同じスラッグの別ページへ結び付けます。

## 検証した事実

- **方針 1（ディレクトリの別名）:**
  - 前回の反例（`view` から `wiki/concepts/jump`、さらに `ext`）は、手元の Windows で拒否しました。`view2` から `wiki/concepts` の下のハードリンクの記事も拒否しました。一致。
  - ジャンクションの `os.readlink` は `'\\\\?\\C:\\...'` の形を返します。綴りの比較では根と一致しませんが、ループの先頭の `samefile` で根を認識し、拒否に至りました。一致。
  - 根に届いたあとの残りに `..` があれば、`found()` が拒否します。リンクの展開は 64 回を超えると拒否します。どちらもコードで確認しました。
- **方針 2（グラフ）:**
  - `collect_pages` は、1 回の `walk_pages` の結果から、ページと `link_warnings` を `GraphPages` に載せて返します。
  - `build_edges` の `link_target`（mentions）は、`refused_link` を先に判定します。`sources:` は `refused` なら `unresolved_source` にせず、辺も作りません。
  - 閲覧は `link_warnings=self.link_warnings` を明示して渡します（差分の `wiki_browse_core.py:1092`）。
  - 呼び出し元は CLI（`wiki_graph_extract.py:1169-1172`）、graph lint（`wiki_graph_lint.py:94` と `217-218`）、MCP（`wiki_mcp_server.py:129`）です。どれも `GraphPages` をそのまま渡していました。一致。
- **方針 3（lint）:**
  - `resolve_available` は、拒否を先に判定してから `resolve_link` を呼びます。被リンク（`wiki_lint.py:548`）、索引の type の検査（`wiki_lint.py:566`）、リンク切れ（`wiki_lint.py:590`）で共用しています。
  - 明示したパスで読める別のページを指すリンクは、`refused_link` のパスの形が一致しないので解決します。一致。
- **残りの解決箇所:** `wiki_lint.py` の中に、`resolve_link` を直接呼ぶ箇所は、もう残っていません（grep で確認）。

## 崩せなかった点

- 要素ごとの展開が、根を通り過ぎて、その下のリンクを解決する経路は見つかりませんでした。根は、要素を足した直後に綴りで比べ、ループの先頭で `samefile` でも比べます。どちらかで一致すれば、そこで止まります。
- `..` を綴りの上で親へ戻す処理は、展開を終えた物理的な祖先にだけ当たります。リンクの先で `..` を誤って解決する例は見つかりませんでした。
- `.` の要素は、pathlib が取り除くので、`article_path` の `not_article` に紛れ込みませんでした。
- グラフと lint と閲覧の 3 者で、拒否した wikilink と `sources:` の扱いがそろっています（mentions と sourced_from を作らない。リンク切れと unresolved_source にしない）。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし
次の作業（最後の要素の別名の扱いの修正）に向くモデルとエフォート: Opus、high
