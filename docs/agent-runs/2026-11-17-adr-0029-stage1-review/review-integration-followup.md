## 判定

**条件付きで採用可**（確信度: 中）

今回の差分に、致命的・重大な欠陥は見つかりませんでした。重点の「`_article_rel` の samefile が根より下のリンクを追うか」も崩せていません。根と一致したところで止まり、残りは `article_path` が検査します。

ただし、軽微な問題が 5 件残っています。

- 大小文字を区別しないファイルシステムの対応は根そのものにしか効かず、根の下のディレクトリを指す別名では素通りします（推測、macOS では未実行）。
- `refused_link` が `posix_rel` を使わないので、旧来の lint より照合が弱くなりました。
- frontmatter の `sources:` は、今も拒否を「ない」と報告します。
- 拒否したページとスラッグが同じ読めるページがあると、警告なしにそちらへ解決します。
- 拒否したディレクトリそのものを指す wikilink は、リンク切れのままです。

保留条件として、Mac CI の `test_case_variant_root_still_checks_articles` の結果はまだ確かめていません。

## 致命的・重大な欠陥

なし

## 崩れる前提

- **前提: 大小文字の違う別名は、根そのものの綴りにしか現れない**（`wiki_pages.py` の `_article_rel` に追加した samefile の部分。推測、macOS では未実行）
  - 崩れる条件: 大小文字か Unicode の正規化（NFC と NFD）だけが違う綴りで、根の下のディレクトリを指すシンボリックリンクを wiki の外に置き、それを通るパスを渡したときです。
  - 再現手順（macOS、APFS の既定）:
    1. wiki を `/tmp/x/wiki` に置き、`concepts/a.md` をハードリンクにする。
    2. `/tmp/x/v` を、`/tmp/x/WIKI/concepts` を指すシンボリックリンクとして作る。
    3. `read_user_bytes("/tmp/x/v/a.md", wiki)` を呼ぶ。
  - 起きること:
    - 接頭辞 `/tmp/x/v` の realpath は `/private/tmp/x/WIKI/concepts` になります。POSIX の realpath は、リンク先の文字列の大小文字を正規化しません。
    - そのため、どちらの根とも `relative` が失敗します。samefile は根そのものとしか比べないので、`concepts` は一致しません。
    - 最後の要素は調べないので、関数は `None` を返します。`user_file_path` は wiki の外のファイルとして、検査せずにハードリンクの記事を返します。
  - 範囲: 根そのものの別名（今回の試験の `WIKI/concepts/a.md`）は防げます。防げないのは、根の下のディレクトリを指す別名だけです。
- **前提: 拒否した項目の `path` と wikilink の行き先は同じ形で正規化されている**
  - 崩れる条件: POSIX の名前にバックスラッシュを含むページです（下の 2 件目）。
- **前提: 拒否はリンク切れの判定と曖昧さの判定にだけ関わる**
  - 崩れる条件: 読めるページと、スラッグが同じページを拒否したときです（下の 4 件目）。

## 見落としと軽微な問題

1. **軽微: 上の samefile の残り。** 根の下のディレクトリを指す別名は、大小文字が違うと wiki の外として扱われます。内容は「崩れる前提」の 1 件目のとおりです（推測）。
2. **軽微: `refused_link` が `posix_rel` を通さない**（確認済み）
   - `refused_link` は `rel = nfc(item["path"])` で比べています。旧来の lint は `posix_rel(rel)` を使っていました。一方、`clean_link_target` と `build_page_index` は、`\` を `/` に変えます。
   - 結果: 純粋な関数として呼ぶと、警告 `{"path": "concepts/a\\b.md"}` に対して、`refused_link("concepts/a\\b", ...)` も `refused_link("concepts/a/b", ...)` も `None` を返しました。ページの索引の鍵は `concepts/a/b` です。
   - 影響: POSIX でこの名前のページを拒否すると、lint はリンク切れに、閲覧は `unresolved` に戻ります。今回の差分による後退です。
3. **軽微: `sources:` は拒否を「ない」と報告する**（確認済み、段階 1 からの問題）
   - 再現: `sources/s.md` をハードリンクにし、`concepts/a.md` に `sources: ["[[s]]"]` を置いて lint を流しました。lint の `links` には `sources/s.md` が出ますが、同時に `unresolved_sources` に `{'source': '[[s]]', 'reason': 'missing'}` が出ます。
   - 原因: `classify_source_ref`（`wiki_pages.py:1007-1024`）は `refused_link` を見ません。閲覧の出典の欄（`wiki_browse_core.py:1548`）も `wl-unresolved` だけを描き、理由を出しません。今回の (2)(3) の対応は、本文の wikilink にしか及んでいません。
4. **軽微: 同じスラッグの読めるページへ、警告なしに解決する**（コードを読んだ推論、未実行）
   - `concepts/b.md` を拒否し、`entities/b.md` が読めるとき、`[[b]]` は `link_candidates` が 1 件なので `entities/b` に解決します。`refused_link` は候補が空のときしか呼ばれません（`wiki_browse_core.py:949-953`、`wiki_lint.py` のリンク切れの判定）。
   - リンクでなければ曖昧になったはずの行き先が、黙って別のページに結び付きます。`resolve_link` の docstring は「誤った解決は気づかれない」害を避ける方針ですが、それと食い違います。
5. **軽微: 拒否したディレクトリそのものを指す wikilink は、リンク切れのまま**（確認済み）
   - `refused_link("concepts/jump", [{"path": "concepts/jump", ...}])` は `None` を返しました。比べ方が `target.startswith(rel + "/")` だけだからです。
   - ディレクトリそのものはページではないので、実害は小さいです。

## 検証した事実

- **samefile の追加:** 一致したときは `parts[size:]` を返して止まります。それより下の要素は `article_path` が要素ごとに lstat します（`wiki_pages.py:579-620`）。一致。
- **samefile の評価の順:** `relative` による綴りでの一致を先に試し、samefile はその後です。根の中のリンクで根に戻る道（`concepts/self` から根へ）を、綴りの合うパスで渡すと、最初の `relative(given, root)` で `concepts/self/...` として捕まります。一致。
- **新しい試験:** `IntegrationReviewTests` の 3 件が手元（Windows、Python 3.12）で OK でした。ただし Windows では、`normcase` が先に一致するので、samefile の分岐は通りません。Mac CI での実行は確かめていません。
- **`refused_link` の境界:** `concepts/jumpx/a` は拒否せず（要素の境界が効く）、`concepts/jump/a` は拒否しました。`concepts/B.MD` へのスラッグ `B` は拒否し、`indexes/c` は拒否しません（索引はページでないので、通常の解決と一致）。
- **閲覧の `self.link_warnings`:** `_build_pages` と `_build_assets` のあとで作られます。`resolve()` が呼ばれるのは、そのあとの `_prepass`、`_nav` です。初期化の順は一致。
- **索引の行の描画:** `_index_unresolved_html` は `_link_html` を使い、`refused` に「リンクなので読まない」の title を付けます。`_nav_item` は `label` を必ず渡すので、KeyError は起きません。一致。
- **`unresolved()`:** `state == "unresolved"` だけを数えるので、`refused` は入りません。lint の broken_links と同じく拒否を除き、docstring と一致しました。
- **報告の JSON:** `build` の報告に `link_warnings` があります（差分の `wiki_browse.py`）。一致。
- **診断の HTML:** `_diagnostics_html` が `path` と `link_kind` を出します（差分）。一致。

## 崩せなかった点

- samefile の追加が、根より下のリンクを解決して検査を飛ばす経路は見つかりませんでした。一致した時点の残りの要素は、根を起点に `article_path` が検査します。読むのも、`article_path` が返した根の下の実際のパスです。
- 要素の境界での照合（`concepts/jumper/x` を `concepts/jump` で拒否しない）。
- スラッグだけの wikilink を、降りなかったディレクトリの下で推測しないこと（`x` は `None`）。
- 拒否した wikilink が、閲覧の `unresolved()` と lint の broken_links のどちらにも数えられないこと。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし
次の作業（軽微な指摘の修正）に向くモデルとエフォート: Opus、medium
