# レビューの目的（3 回目）

`docs/plans/wiki-query-two-wikis-2026-11-16.md`（4 版目）は、info-hive の wiki プラグイン（`info-hive-wiki`）の `/wiki:query` で、利用者が求めたときだけ、ユーザースコープの wiki とプロジェクトの wiki の 2 つを引く設計である。1 回目（`review-1.md`）と 2 回目（`review-2.md`）のレビューはどちらも却下で、崩れた前提と直し方の対照は第 8 節にある。第 6 節の事項は作者が決めたので、決定そのものではなく、決定のもとで設計が崩れる点を探してほしい。

2 回目の指摘（根のパスを比べても 2 つの wiki が分かれているとは言えない）を受けて、4 版目は次のように変えた。

- 補助 `wiki_roots.py check <根 A> <根 B>` は、根のパスではなく、検索が走査するページのファイル（`wiki_pages.walk_pages()`）を、ファイルシステムの識別子（Windows は `wiki_pages.win_file_id()`、ほかは `(st_dev, st_ino)`）で比べる。
- 結果は `same`、`overlap`、`key_collision`（`wiki_key()` が同じになる別のディレクトリ）、`disjoint`、`null`（確かめられない）。2 つを引くのは `disjoint` のときだけである。

次を崩すことを狙ってほしい。

- 補助の仕様（第 4 節）で、`disjoint` を返すのに、2 つの検索が同じ中身を返すか、出典の wiki の区別が誤る反例。たとえば、走査がページ以外のもの（索引のファイル、`get_page`、raw、グラフ）を読む経路、ハードリンク、識別子の取り方の誤り、`walk_pages()` と MCP の索引や CLI の検索の走査の食い違い。`info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`、`wiki_index.py`、`wiki_search.py`、`wiki_mcp_server.py`、`wiki_mcp_common.py` と照らして。
- 補助が `same` や `overlap` を返すべきでないのに返して、正しい配置で 2 つを引けなくなる反例。
- 2 回目までの直し（第 8 節）が、4 版目の変更で崩れていないか。
- 第 2 節の前提が、今の実装と文書に照らして誤っていないか。
- 第 5 節に入れるべきなのに入っていない欠陥。

設計の段階なので、細かな文言より、設計を覆す欠陥を優先する。
