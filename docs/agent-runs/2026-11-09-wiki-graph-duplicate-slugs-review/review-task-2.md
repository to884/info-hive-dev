info-hive-wiki（Claude Code のプラグイン wiki）のグラフの抽出の修正（wiki 0.9.2）の 2 回目のレビュー。応答は日本語で書く。

1 回目（主語をスラッグからページに替えた修正、判定は採用可）のあとに、閲覧（browse）の関係表がグラフの抽出に求める契約が決まり、それに合わせて直した。差分は 1 回目の前（64acc43）からの全体である。

契約（開発リポジトリの docs/plans/wiki-browse-stage1-2026-11-09.md の 3「グラフの抽出に求める契約」、ブランチ feature/wiki-browse-stage1 のコミット d4391da。要約）:
1. エッジの主語は、そのエッジを書いたページのノード。スラッグから引き直さない。
2. エッジは page を持ち、ページの違う同じ内容の関係を 1 本にまとめない（edge_id に page を入れる）。
3. 型付きの関係の目的語はノード ID として引く。1 つのページのノードに当たればそれを目的語に、当たらなければ今と同じ文字列の目的語。目的語をページへの参照として解かない。
4. sources: の値は resolve_link() と同じ規則でページ（相対パス）に解決する。当たるページの集合が 1 つならそのページ、2 つ以上なら曖昧、0 なら未解決。曖昧と未解決はエッジを作らず診断に挙げる。
5. 別のページが同じ graph.node_id を持つときは黙って捨てず診断に挙げる。そのノード ID を目的語にした関係はエッジを作らず曖昧として診断に挙げる。
6. sources: の値のうち 1 つのページに解決するものからは、必ず sourced_from ができる。

実装の判断（崩してほしい）:
- 同じノード ID のページが複数あるとき、ノードは最初のページから 1 つだけ作り、どのページも page_node_ids ではそのノードを指す。どのページの関係もそのノードを主語にして残る。ページへの参照（wikilink、sources:）は、そのページのノード（共有のノード）へのエッジにする。ノード ID の参照（型付きの関係の目的語）だけを曖昧とする。
- 契約の 6 の「必ず」は、今の仕様（手順書）のとおり、type: source のページの sources: には当てはめない。
- エッジの ID に page を入れたので、すべてのエッジの ID が変わる。生成物（JSONL、SQLite の edges の主キー、GraphML の平行なエッジ）と MCP のツール graph（wiki_graph_query.py の neighbors、edges、path、facts）への影響を確かめてほしい。
- 診断は build_nodes/build_edges の引数 diagnostics に足し、グラフの lint が ambiguous_object_refs、ambiguous_sources、unresolved_sources として挙げる。抽出は件数を標準エラーに書く。
- frontmatter の参照の読み方（ref_values、ref_link）を wiki_lint.py から wiki_pages.py に移し、lint と抽出で共有した。
- lint の derive_node_id は抽出の page_node_id に寄せた（node_id を str() にする）。

特に確かめてほしいこと: 契約の 6 項目を満たすか、同じスラッグも同じ node_id もない wiki でエッジ（ID を除く）が変わらないか、wiki_lint.py の unresolved_sources と raw: の検査が変わらないか、CHANGELOG と references/graph-workflow.md の記述の正確さ、試験が主張を本当に確かめているか。

試験: 開発リポジトリの tests/wiki/test_graph_duplicate_slugs.py（下の絶対パス、16 件）。
