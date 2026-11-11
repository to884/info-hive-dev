2 回目のレビューの指摘を受けて直した。差分は同じく 64acc43 からの全体（未コミット）である。応答は日本語で、同じ形式で書く。

直したこと:
1. 重大（NFC と NFD の名前の違いだけの 2 つのファイルで、関係が 1 本にまとまる）: make_edge に page_id を足し、エッジの ID にはディスク上のパス（page_key）を入れるようにした。出力の page は NFC の rel_path のまま（browse の識別子は NFC）。build_edges のすべての make_edge の呼び出しに page_id=here を渡す。duplicate_node_id、ambiguous_object、ambiguous_source の候補のページの一覧（pages）は、ディスク上のパスにした（lint の duplicate_node_ids と同じ）。診断の page は、エッジの page と同じ NFC の rel_path のまま。
2. ソースページの sources: も、解決と診断（ambiguous_source、unresolved_source）は行い、sourced_from だけを作らない。
3. lint の目的語の照合を str(obj) にした（object: 1 が node_id: 1 のノードに当たる）。
4. GraphML のエッジに d_page（page）を足した。
5. 手順書の例を `sources:` の `a/Foo` に直し、ソースページでも診断を挙げることを書いた。
6. 試験を 19 件にした（NFC/NFD、ソースページの診断、数値の目的語、GraphML の page、neighbors と path）。CI（開発リポジトリの .github/workflows/wiki-mcp.yml）にこの試験を足した。

「重複がない wiki なら、ID 以外のエッジは変わらない」は、CHANGELOG には書いていない（sources: の読み方を直したので、パス、[[...]]、1 つの文字列、前後の空白の値でエッジが増えることは変更として書いてある）。

直した点が正しいか、直したことで新しく崩れたものがないかを確かめてほしい。
