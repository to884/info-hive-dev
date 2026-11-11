1 回目のレビュー（`docs/agent-runs/2026-11-11-wiki-graph-frontmatter-values/review-1.md`、却下）の指摘に対応した。直したあとの実装を、もう一度レビューしてほしい。応答は日本語で書く。

変更: サブモジュール `info-hive-wiki` のコミット 2 つ（a38c537 と、その次の HEAD）。`git -C info-hive-wiki diff c50854a HEAD` で 0.9.3 からの差分、`git -C info-hive-wiki diff a38c537 HEAD` で 1 回目のレビューからの差分を読める。試験 `tests/wiki/test_graph_frontmatter_values.py`、期待値 `tests/wiki/graph_frontmatter_values_golden.json`、設計 `docs/plans/wiki-graph-frontmatter-values-2026-11-11.md` は開発リポジトリの未コミットのファイルである。

対応:
1. 重大 1（NUL などで `SafeLoader` の生成が失敗して止まる）: `_read_graph()` の中でローダーの生成の例外も捕まえる。`graph` の欄がありそうなら `unreadable_graph`（`yaml_error`）。
2. 重大 2（マージで来た `maps_from` が文字にならない）と重大 3（自分を含むアンカーで参照の欄がすべて元の型のまま）: `BaseLoader`・`BaseConstructor` をやめ、PyYAML が値に組み立てたあとのノードから、参照の欄のノードの値（書かれた文字）を直接取る（`_child()`、`_written()`）。オントロジーも `SafeLoader` のノードを手元に残して同じ方法で読む。
3. 重大 4（出力不変の主張と試験）: 主張に「`raw:` を配列で書いていない」を足した。配列で書いたタグは 0.9.3 と同じ値のまま出す（`_tag_list()`）。試験は、0.9.3（c50854a）のスクリプトそのものが作った出力（`graph_frontmatter_values_golden.json`）と比べる。
4. 軽微（`unread_field` の誤検出と見逃し）: 欄を自分で書いた回数（マージの展開前）と、lint のパーサーがキーの行として読んだ回数（`wiki_text.top_level_keys()`）を比べる。マージだけで来た欄は、展開後のノードと lint の形を比べて挙げる。
5. 軽微（`<<: 3` で独立した `graph` を失う）: 最上位のマージキーを展開できなくても、`graph` を読む。

特に確かめてほしいこと:
- 1 回目の重大 1〜4 と軽微 3 件が、直っているか。直し方が新しい欠陥を作っていないか。
- `_child()` と `_written()` でノードから値を引くことの誤り（PyYAML が辞書を作るときのキーの選び方、マージキーの優先順、タグ付きのキーや値、`!!binary` などとの食い違い）。
- `_unread_fields()` の誤検出と見逃し。
- `read_ontology()` を `yaml.safe_load()` から `SafeLoader` の `get_single_node()` と `construct_document()` に変えたことで、読める・読めないオントロジーが 0.9.3 と変わる入力。
- CHANGELOG と `references/graph-workflow.md` の記述が実装と食い違うところ。

通っている試験（Windows、Python 3.12、PyYAML 6.0.3）: `tests/wiki/test_graph_frontmatter_values.py`（48 件）と、1 回目に挙げたほかの試験すべて。
