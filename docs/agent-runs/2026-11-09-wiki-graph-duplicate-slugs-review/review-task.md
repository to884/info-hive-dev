info-hive-wiki（Claude Code のプラグイン wiki）のグラフの抽出の不具合の修正をレビューしてほしい。応答は日本語で書く。

不具合: `skills/info-hive/scripts/wiki_graph_extract.py` で、別のディレクトリに同じスラッグのページ（`a/Foo.md` と `b/Foo.md`）があると、`build_nodes()` が `slug_to_id[slug]` を後のページで上書きし、`build_edges()` が主語をスラッグから引くので、前者の `graph.relationships` の主語が後者のノードになった。パスを付けた `[[a/Foo]]` も後者を指し、同じスラッグの 2 つのノードで `graph.sqlite` の `nodes.slug UNIQUE` に反して抽出が止まった。

修正の意図:
1. 主語は、そのページ自身のノード（`page_key(p)` = disk_rel_path で引く）にする。
2. パスを付けたリンクはそのページを指す。パスのないリンクと `sources:` は、同じスラッグのページが複数あればどれにも寄せない（エッジを作らない）。lint の duplicate_slugs がその重なりを挙げる。
3. `nodes.slug` の UNIQUE を外す。問い合わせ（wiki_graph_query.py、MCP のツール graph）はノードを ID で引く。
4. グラフの lint（wiki_graph_lint.py）の orphan_typed_nodes も、ページで引く対応を渡す。
5. リンクの規則（パスかスラッグか）は wiki_pages.py の 1 か所に置く（ADR-0010 の決定の 1）。

特に確かめてほしいこと: 同じスラッグがない wiki でエッジが変わらないか、NFC と NFD の名前の違いだけのファイル、node_id が重なってノードにならなかったページ、graph lint と extract の対応のずれ（lint は derive_node_id で str(explicit) を使う）、ほかの呼び出し元（wiki_mcp_server.py、test_link_resolution.py、開発リポジトリの tests/graph/test_graph.py）、CHANGELOG の記述の正確さ。

試験: 開発リポジトリの tests/wiki/test_graph_duplicate_slugs.py（下の絶対パス）。tests/graph/test_graph.py（28 件）、test_link_resolution.py（113 件）は通っている。
