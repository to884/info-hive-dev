## 判定

**条件付きで採用可**（確信度: 中）

今回の差分そのものに、致命的・重大な欠陥や既存の仕様の後退は見つかりませんでした。方針と実装が食い違う箇所は 3 件あり、どれも軽微です。

- **`_article_rel` の別名:** 根の規則は、外の別名が wiki の中の「リンクのディレクトリ」を指すと引き継がれません。拒否すべき記事を読みます。今回の差分で生じたものではなく、以前からある経路です。
- **`classify_source_ref` の共用:** 「lint とグラフが共有する」と書かれていますが、グラフの抽出は拒否の情報を渡していません。
- **同じスラッグの別ページへの解決:** 閲覧は解決しなくなりましたが、lint は今も解決します。

下位ディレクトリの別名の試験（Mac の CI）は、まだ確かめていません。

## 致命的・重大な欠陥

なし

## 崩れる前提

- **前提: 祖先を上から調べれば、根に届いたところで止まり、根より下のリンクは解決しない**（差分の `_article_rel` のコメントと docstring）
  - 崩れる条件: wiki の外の別名が、wiki の中のリンクのディレクトリ（またはその下）を指すときです。
  - 原因: `os.path.realpath(prefix)` は、別名から先のリンクの連鎖を一度にすべて解決します。そのため、解決済みのパスは根の下にとどまらず、wiki の外の実体に飛びます。新しい `resolved_parts` の祖先を samefile で探す処理も、根に当たりません。結果は `None` になり、`user_file_path` は wiki の外のファイルとして、検査せずに返します。
  - 再現（Windows、ジャンクション、手元で実行。プローブは `alias_through_link.py`）:
    1. `wiki/concepts/jump` を `ext` へのジャンクションにし、`ext/a.md` に `OUTSIDE` と書く。
    2. wiki の外の `view` を、`wiki/concepts/jump` へのジャンクションにする。
    3. `read_user_bytes(wiki/concepts/jump/a.md, wiki)` は、`拒否: リンクなので読まない: concepts/jump（junction）` になる。
    4. `read_user_bytes(view/a.md, wiki)` は、`b'OUTSIDE'` を返す（`_article_rel` は `None`）。
  - 評価: `view/a.md` は、論理的には wiki の `concepts/jump/a.md`、つまりリンクの道の下の記事です。直接のパスでは拒否し、別名では読むので、方針 1 の「根の下のディレクトリを外から指す別名にも、根の規則を引き継ぐ」と食い違います。
  - 範囲: 外の別名が根や、リンクを含まない根の下を指す場合は、正しく引き継ぎます。手元では確かめませんでしたが、依頼元の試験（`view` から `WIKI/concepts`）がこの場合に当たります。差分の前から同じ経路で読めるので、後退ではありません。利用者が意図して外に別名を置く必要があるので、軽微とします。
- **前提: `classify_source_ref` を共有する呼び出し元は、どれも拒否を同じに扱う**
  - 崩れる条件: グラフの抽出です。`wiki_graph_extract.py:796` は `classify_source_ref(ref, pages_by_path, pages_by_slug, type_by_key.get)` と呼び、`link_warnings` を渡しません。
  - 結果1: 拒否した source を指す `sources: ["[[s]]"]` を、グラフは `unresolved_source`（ない）と診断します。
  - 結果2: 同じスラッグの読める source ページがあると、グラフはそのページへ `sourced_from` の辺を作ります。lint と閲覧は `refused` とするので、扱いが分かれます。
  - docstring の「lint の unresolved_sources と、グラフの抽出の sourced_from が、この関数を共有する」は、共有の範囲を誤って示しています。
- **前提: 拒否を先に判定する規則（方針 4）は、閲覧と lint で同じである**
  - 崩れる条件: `concepts/b.md` を拒否し、`entities/b.md` が読めるときに `[[b]]` と書いた場合です。
  - 閲覧の `Core.resolve` は、拒否を先に判定して `refused` にします（差分の `wiki_browse_core.py:948`）。
  - lint は今も `resolve_link(...) is None and refused_link(...) is None` の順です（`wiki_lint.py:585`）。そのため `[[b]]` を `entities/b` に解決し、指摘しません。被リンクの集計（`wiki_lint.py:543`）でも、`entities/b` に被リンクを数えます。同じリンクを、閲覧は拒否、lint は解決と扱います。
  - 依頼文の方針 4 は `Core.resolve` についての記述なので、仕様の上では閲覧に限っています。ただ、`unresolved()` の docstring は「lint の broken_links と同じ集合」としているので、この違いを軽微として挙げます。

## 見落としと軽微な問題

1. **軽微: 別名が wiki の中のリンクのディレクトリを指すと、記事を読む**（上の 1 件目。以前からあり、Windows で再現済み）
2. **軽微: グラフの抽出が `link_warnings` を渡さない**（上の 2 件目。コードを読んで確認）
3. **軽微: 拒否を先に判定するのが閲覧だけで、lint は旧来の順のまま**（上の 3 件目。コードを読んで確認）
4. **軽微: 大小文字の違う残りの要素で、記事かどうかの判定がずれる**（推測、未実行）
   - 新しい分岐が返す rel の残りの要素は、realpath の結果の綴り（リンク先の文字列の大小文字や NFD）のままです。
   - 大小文字を区別しない環境で、`RAW/x.md` や `INDEXES/c.md` のように綴りが違うと、`is_article_path` はそれぞれページとして判定します。
   - どちらも検査の対象を広げる側に寄り、読む側に寄る例は見つかりませんでした。実害はないと見ます。

## 検証した事実

- **方針 2（`refused_link` の照合だけを `posix_rel` にする）:** `refused_link` は `rel = posix_rel(item["path"])` で比べ、OS 上の読み取りのパスは変えません。`build_page_index` の鍵（`posix_rel` から `.md` を除いたもの）と同じ形です。一致。
- **方針 3（出典の拒否を lint と閲覧で共通に扱う）:** `classify_source_ref` は、`link_warnings` があると、候補を探す前に `"refused"` を返します。lint は `findings["links"]` を渡し、`"refused"` を `missing` にも `not_source` にもしません。閲覧は「リンクなので読まない」で描きます。lint と閲覧の間では一致しました。グラフについては食い違いです（上の 2 件目）。
- **方針 4（閲覧は同じスラッグの別ページへ解決しない）:** `Core.resolve` は `refused_link` を先に呼びます。スラッグの形はページの `.md` の項目にしか当たらないので、`[[entities/b]]` のように別のパスを明示すれば解決します。閲覧の中では一致しました。lint とは食い違います（上の 3 件目）。
- **方針 5（ディレクトリそのものへの wikilink は拒否にしない）:** 比べ方は `target.startswith(rel + "/")` で、ディレクトリと同名のパスは拒否になりません。前回のプローブでも `refused_link("concepts/jump", ...)` は `None` を返しました。方針と一致します。
- **方針 1（別名からの所属判定）:**
  - 一致した部分: 解決済みのパスの祖先から samefile で根を探し、見つかれば残りを返す実装は、差分の `wiki_pages.py:611-623` にあります。返したあとは `article_path` が要素ごとに検査します。
  - 食い違う部分: 解決済みのパスがリンクの先の外に出る場合は、根を見つけられません（上の 1 件目）。
- **試験:** 新しい試験 `test_refused_sources_and_duplicate_slugs_do_not_become_missing_or_retargeted` と、`view` から `alias / "concepts"` への入力の試験があることを確かめました（`tests/wiki/test_wiki_links.py:138-164`）。

## 崩せなかった点

- 新しい祖先の探索が、wiki の外のパスを wiki の中と誤る例は見つかりませんでした。samefile が真になるのは根の実体だけで、realpath の結果には `..` が残りません。
- 根の下のリンクを含まない別名（大小文字や NFC/NFD の違いを含む）では、根を見つけたあと、残りの要素を `article_path` が lstat で検査します。拒否を飛ばす例は見つかりませんでした。
- `refused_link` の `posix_rel` 化で、前回の POSIX のバックスラッシュの名前の後退は解消しています（コードで確認）。
- `classify_source_ref` に `link_warnings` を渡さない従来の呼び出し（グラフ）の挙動は、差分の前と変わらず、後退はありません。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし
次の作業（軽微な指摘の修正）に向くモデルとエフォート: Opus、medium
