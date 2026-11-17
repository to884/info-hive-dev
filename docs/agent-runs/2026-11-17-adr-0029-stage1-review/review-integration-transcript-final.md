## 判定

**条件付きで採用可**（確信度: 中）

最新の HEAD（親 `0cf2d94`、plugin `ad63233`）を対象にした判定です。Wiki walk（run 44109239296）は 6 ジョブすべてで `test_wiki_links.py` の 66 件が通りました。ubuntu と macOS では skip が 0 件で、Windows で飛ばされたのは POSIX 専用の 3 件だけです。条件は 2 つあります。

- **CI の残り:** Wiki browse の Windows 2 ジョブと Wiki MCP server が、提出の時点でまだ pending です。browse の ubuntu 2 ジョブは pass しました。
- **軽微な問題:** 閲覧の診断の表示などに軽微な問題が残っています。

依頼時点の `fbf775a` と `9d51a2c` には重大な欠陥が 3 件あり、CI の walk は 6 ジョブすべてが赤でした。3 件ともレビュー中に依頼元のコミットで直っています。

## 致命的・重大な欠陥

**HEAD の `0cf2d94` では、なし。**

依頼時点のコミット（`fbf775a`）にあった重大な欠陥を、記録のために残します。3 件ともレビュー中に直りました。

1. **重大（`d24dba9` で修正済み）: 目録の試験が統合で壊れていた**
   - 内容: `ReadSiteInventoryTests.test_every_read_site_is_classified` が、main から入った `wiki_codex.py` の `workflow`（`commands/*.md` の読み取り）を「分類していない」として落ちていました。
   - 根拠: run 44107412105 の 6 ジョブすべてに `AssertionError: Lists differ: [('wiki_codex.py', 'workflow')] != []` が出ていました。手元でも再現しました。
2. **重大（`a6d9d71` で修正済み）: 一時ディレクトリに別名があると試験が壊れていた**
   - 内容: `test_both_corpus_entries_stop_before_contract_on_listing_error` が macOS と Windows で `AttributeError: 'types.SimpleNamespace' object has no attribute 'runner'` を出していました。
   - 原因: `wiki_evolve.py:378` と `wiki_evolve_loop.py:508` は `user_file_path(...).resolve()` で suite のパスを解決します。試験の `denied` は未解決の `corpus` とだけ比べていました。そのため、一時ディレクトリが別名の環境では障害が入らず、`evaluate` が `args.runner` まで進みました。macOS では `/var` が `/private/var` の別名で、Windows の runner では短い名前が使われると推測します（Windows 側は推測）。
   - 再現: `_winapi.CreateJunction` で作った別名を TMP にすると、手元でも同じ例外が出ました。`a6d9d71` のあとは、同じ条件で 66 件が OK（skipped=3）になります。
   - 切り分け: 製品の側の欠陥ではありません。解決後のパスでも `source_wiki_root` が根の realpath に一致し、守りは効きます。
3. **重大（`d24dba9` と `0cf2d94` で修正済み）: CI が肝心の試験を飛ばし、閲覧の古い試験が残っていた**
   - 依存の欠落: 当初の手順には `--with numpy/usearch/tantivy` がありませんでした。そのため、索引の依存が要る 3 件（`test_get_page_under_a_link_directory` ほか）が、全 OS で飛ばされていました。
   - 閲覧の古い試験: `tests/wiki/test_browse.py` の `test_linked_indexes_dir_is_watched` は、リンクの先を読むことを期待する旧挙動の試験のまま残っていました。

## 崩れる前提

- **前提: 一時ディレクトリのパスが実体と同じである**
  - 崩れる条件: macOS の `/var`、Windows の 8.3 形式の短い名前、ジャンクションの TMP。上の 2 件目で実際に崩れていました。
  - 今の試験は `resolve()` で比べます。ただし `len(failures) == 2` は、入口ごとに corpus を 1 回だけ一覧することを前提にしています。降りる前の再確認などで一覧が増えると、守りが正しくても落ちます。
- **前提: 目録（`SITES`）が main の新しいスクリプトに追いついている**
  - 崩れる条件: main から読み取りの関数が入るたびに落ちます。意図した仕掛けですが、Codex の取り込みで実際に崩れました。統合のたびに手で足す必要があります。
- **前提: `snapshot.entries` の 4 つ目の要素は更新時刻である**
  - 崩れる条件: `("link", rel, None, 種類)` の 4 つ目は、リンクの種類の文字列です。今の使い手（`signature_of`、`take_snapshot`、`Core.__init__`、`wiki_browse.py:145` の `_machine_needles`）は、どれも数として使わないので成り立ちます。
  - 今後、mtime を比べたり足したりする使い手が増えると、`TypeError` になるか、意味の違う値を比べることになります。
- **前提: 大小文字の違う根も、同じ根として判定できる**
  - 崩れる条件（推測、未実行）: macOS の大小文字を区別しない APFS で、根と大小文字の違うパスを渡したときです。
  - `wiki_pages._article_rel`（`wiki_pages.py:585-612`）は `normcase` と `realpath` で根を比べます。POSIX の `normcase` は何も変えず、`realpath` も大小文字を正規化しません。
  - この場合 `_article_rel` は None を返し、`user_file_path` が wiki の外として検査せずに読みます。例: wiki が `/Users/u/Wiki` のとき、`--candidate /users/u/wiki/concepts/a.md` を渡すと、ハードリンクの記事でも読みます。Windows は `normcase` で、Linux は大小文字を区別するので当たりません。

## 見落としと軽微な問題

1. **軽微: 閲覧の HTML の診断に、リンクの場所と種類が出ない**
   - `Core.__init__` は `{"kind": "link", "path": ..., "link_kind": ...}` を足します。しかし `_diagnostics_html`（`wiki_browse_core.py:1614`）が出すキーは `target`、`reason`、`output` などだけで、`path` と `link_kind` を含みません。
   - 再現: `concepts/secret.md` をハードリンクにして `Core(take_snapshot(wiki))` を描くと、HTML は `<li>link</li>` だけでした。`concepts/secret.md` は HTML にありません。
   - `data/diagnostics.js` を描く JS もありません（mermaid を除いて grep で確かめた）。
   - `build` の報告の JSON（`wiki_browse.py:194-195`）にも `link_warnings` がなく、診断の件数しか出ません。計画の決まり 1（`link_warnings` を必ず付ける）と比べると、場所が分かるのは終了時の標準エラーだけです。
2. **軽微: 閲覧と lint で、拒否したページへの wikilink の扱いが違う**
   - 同じ wiki で `concepts/a.md` に `[[secret]]` を置くと、閲覧は `{'kind': 'unresolved', 'page': 'concepts/a', 'target': 'secret'}` と診断しました。lint はリンク切れにしません。
   - 計画は、閲覧には「診断に出す」ことだけを求めています。そのため、この違いは不整合として軽微に置きます。
3. **軽微: lint が、拒否したディレクトリの下をパスで指す wikilink をリンク切れにする**
   - 段階 1 からの挙動で、統合で生じたものではありません。
   - 再現: `concepts/jump` を外へのジャンクションにし、`a.md` に `[[x]] [[concepts/jump/x]]` を置きました。結果は、`links` が `concepts/jump` の 1 件、`broken_links` が `to: 'x'` と `to: 'concepts/jump/x'` の 2 件でした。
   - スラッグだけの `[[x]]` は、降りない設計では判別できないのでやむを得ません。一方、パスの形の側は前方一致で「リンクなので読まない」と判別できます。MCP の `get_page` は判別しています（`test_get_page_under_a_link_directory`）。lint の `refused_by_path` は `.md` の項目しか持たないので、計画の決まり 2 と食い違います。
4. **軽微: 図の走査の変更が、版を上げたあとに入った**
   - `ad63233`（`walk_assets` を共通のリンク判定につなぐ変更）は、`17c150a`（v0.30.0 の版の更新）のあとのコミットです。
   - CHANGELOG の 0.30.0 には、この挙動の変化が書かれていません。変化は、`assets` が名前の代理の再解析点なら降りなくなったことです。
   - タグは未作成なので、今なら直せます。
5. **軽微: 依頼文のクラス名が実装と違う**
   - 依頼文は `wiki_browse_core.WikiSite.__init__` としていますが、実在するのは `class Core`（`wiki_browse_core.py:789`）です。中身は依頼文の説明どおりでした（`_build_assets()` とリンクの診断の両方が残っている）。

## 検証した事実

- **対象のコミット:** 依頼文の plugin `9d51a2c` から、レビュー中に `17c150a`、`ad63233` へ、親は `fbf775a` から `d24dba9`、`a6d9d71`、`0cf2d94` へ進みました。判定は最新の状態に対するものです。
- **統合の形:** `10afe5d` は `9d51a2c` の祖先で、マージのコミットはありません（rebase による統合）。
- **CHANGELOG:** `[Unreleased]` は空で、`[0.30.0]` に段階 1 の項目、その下に `[0.29.0]`（Codex の対応）が残っています。比較のリンクも 0.30.0 と 0.29.0 の両方があり、一致しました。
- **`Core.__init__`:** `self._build_assets()` とリンクの診断の追加が両方残っています（`wiki_browse_core.py:811-815`）。一致。
- **`take_snapshot`:** link の項目は読まず、世代に入れます（`wiki_browse_core.py:315-318`）。一致。
- **`_machine_needles`:** link の項目は realpath を取るだけで、中身は読みません。I2 違反にはならず、一致しました。
- **CI の POSIX の反例:** run 44109239296 で、`test_posix_parent_after_symlink_never_reads_a_decoy`、`test_posix_colon_hardlink_is_not_read`、`test_posix_candidate_bytes_are_from_the_named_file` が ubuntu と macOS で実行されました（`OK`、skip なし）。Windows では、この 3 件だけが飛ばされました（`OK (skipped=3)`）。一致。
- **CI の索引の依存:** 最新の手順は `--with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0` を付けて実行します。一致。
- **手元の試験（Windows、Python 3.12）:**
  - HEAD で `test_wiki_links.py` は 66 件が OK（skipped=3）。別名の TMP でも同じ結果でした。
  - `test_walk`、`test_page_set`、`test_wiki_lint` は OK。
  - `test_browse.SignatureTest` は OK。
  - `test_browse_fs` は、提出までに終わりませんでした（確かめられず）。
- **Codex の MCP の起動:** `.codex-plugin` も `wiki_mcp_launch.py` を使うので、`ServerFilesTests` の閉包に入ります。一致。
- **CI の browse と MCP:** browse の Windows 2 ジョブと MCP は pending でした（確かめられず）。

## 崩せなかった点

- **`walk_markdown`:** `.md` のリンクとディレクトリのリンクの判定、降りる前の再確認、最上位の `README.md` の例外を崩せませんでした。拒否した項目は links に入り、中身は読まれません。
- **`..` を含むパス:** `absolute_user_path` が正規化の前に拒みます。POSIX のシンボリックリンクと `..` の組み合わせで別のファイル（decoy）を読ませる反例も、CI の POSIX 環境で実際に止まりました。
- **suite のパスの `resolve()`:** corpus が解決後のパスになっても、`source_wiki_root` が根の realpath に一致するので、wiki の規則を引き継ぎます。製品の側で守りが抜ける経路は見つかりませんでした。
- **閲覧の印（signature）:** リンクの先の中身が変わっても、印は変わりません（読まないので正しい）。リンクがふつうのファイルに戻ると、項目の種類が変わるので印も変わります。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし
次の作業（指摘の修正）に向くモデルとエフォート: Opus、high
