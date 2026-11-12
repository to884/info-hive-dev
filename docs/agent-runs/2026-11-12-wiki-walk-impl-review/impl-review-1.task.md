# レビューの目的

info-hive-wiki の 0.10.2（wiki をたどる経路を 1 つにし、最上位の除くディレクトリに降りない）の実装を壊してほしい。設計は `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`（7 版目。2026年11月12日に作者が承認した）にある。

## 対象

- `docs/agent-runs/2026-11-12-wiki-walk-impl-review/impl-1.wiki.diff`: info-hive-wiki の 0.10.1（`2756a4e`）からの差分（`wiki_pages.py`、`wiki_lint.py`、`wiki_stats.py`、`wiki_index.py`、`plugin.json`、`CHANGELOG.md`）
- `info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（変更のあとの全体）
- `tests/wiki/test_walk.py`（新しい試験）と `.github/workflows/wiki-walk.yml`

## 経緯

設計は 5 回の敵対的レビューを受けた（`docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs/design-review-1.md`〜`design-review-5.md`）。指摘を崩れた前提で分けた記録が、同じフォルダーの `root-causes.md` にある（A: 標準ライブラリの関数の内側の失敗の読み替え、B: パスの文字列での比較、C: 自分で書いた写しとの照合、D: 別の文書の動きへの依存、E: 失敗は障害のときにだけ起きる）。作者の止める条件により、7 版目はレビューにかけずに承認された。設計の「11. 限界」に、直さずに残した限界がある。実装は、試作（同じフォルダーの `walk_v7.py`）の走査を、製品のコードに移したものである。

## 確かめてほしい点

1. 実装が、設計の「決めること」の 1〜10 と食い違う箇所。とくに、口の一覧（1）、失敗の分け方（2）、たどる関数（3、4）、同じ場所を回る道筋（5）、並び（6）、使う側の変更（7）、MCP の索引の印（8）。
2. 失敗のないとき、0.10.1 の `iter_page_files()`、`wiki_lint.index_files()`、`wiki_stats.compute_stats()`、`wiki_index.stat_signature()`、`wiki_index.list_index()` と、設計の 7 の表にない違いが出る入力。Windows、macOS、Linux、Python 3.10 以上で考える。
3. 呼び出し元（lint、search と MCP の索引、グラフの抽出、`wiki_decide.py`、`setup_wiki.py`、browse の中核の `list_inputs()`）が、戻り値の変化で壊れる箇所。
4. 試験（`test_walk.py`）が、試作の探索と比べて弱くなっている箇所。木から計算する答えと呼び出しの集合が、走査と同じ読み違いをしている箇所。CI で、黙って飛ばされて確かめられなくなる試験。
5. `win_file_id()` の ctypes の使い方の誤り（引数と戻り値の型、ハンドルの扱い、エラーの番号の取り方）。
6. 変更履歴（`CHANGELOG.md`）の記述が、実装と食い違う箇所。

## 分かっていること

- 次の 2 つは、0.10.1 でも同じように失敗する（この変更の前から）。`eval/scripts/test_lint_stats.py` の `test_escaped_destination_and_invalid_path`（Python 3.14 だけ）、`eval/retrieval/test_setup.py`（fastembed を入れていない環境）。
- 確かめた試験: `test_walk.py`（Windows 11 の Python 3.10.11、3.12.13、3.13.7、3.14.6、Linux の 3.12.3）、`test_page_set.py`、`test_wiki_lint.py`、`test_browse.py`、`test_browse_server.py`、`test_browse_fs.py`、`test_wiki_index.py`、`test_mcp_server.py`、`test_graph_*`、`test_link_resolution.py`、info-hive-wiki の `eval/scripts` と `eval/retrieval`。

指摘のそれぞれに、反例（入力と、結果）と根拠を書く。推測の指摘は、推測と書く。応答は日本語で書く。
