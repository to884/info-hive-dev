3 回目のあと、browse が頼る性質が 2 つ加わった（feature/wiki-browse-stage1 の docs/plans/wiki-browse-stage1-2026-11-09.md の 3、コミット cb30278）。それに合わせて直した。差分は同じく 64acc43 からの全体（未コミット）。応答は日本語で、同じ形式で書く。

加わった性質:
(a) graph.relationships の 1 つの項目から必ず 1 本のエッジができ、別の項目とまとめない。同じページの中で status や valid_from/valid_to だけが違う 2 件も両方残す。
(b) sources: の値は、lint の unresolved_sources と同じ字句の処理（外側の [[ ]] を外す）をしてから解く。lint とグラフの抽出が wiki_pages の同じ関数を使い、その関数が「未解決」「source でない」とする値の集合が lint の unresolved_sources と一致すること。

実装:
- (a) edge_id に variant を足した。型付きの関係では、項目の中身全体（キーを文字列にした JSON、sort_keys）と、同じページで中身がまったく同じ項目の何番目か（"<json>#<n>"）を入れる。項目の並べ替えでは ID が変わらない。mentions、sourced_from、summarizes_raw は今までどおり（同じページの同じ値は 1 本）。
- (b) wiki_pages.build_page_index と classify_source_ref を足した。classify_source_ref は ("missing" | "not_source" | "ok", 当たるページ, 最初の source でない type) を返す。lint の unresolved_sources はこれで missing と not_source を挙げる。抽出は当たるページの数で、0 なら unresolved_source、2 以上なら ambiguous_source、1 なら sourced_from（not_source でも作る。契約の 6）。
- lint の変化: パスを付けた値（concepts/paper）は、そのパスのページの type で判断する（今までは同じスラッグのページすべての type）。パスのない値は今までと同じ。

確かめてほしいこと: (a) と (b) を満たすか、まだまとまるエッジや、lint と抽出で食い違う値がないか、wiki_lint の unresolved_sources の既存の振る舞いの変化が CHANGELOG のとおりか、ID の作り方が sqlite、graphml、判定レイヤー（wiki_decide.py と wiki_graph_lint.py の decide_evidence）、MCP の graph に与える影響、試験（21 件）の妥当性。
