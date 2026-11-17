# 依頼：2 つの wiki を引く問い合わせの設計（15 版目）の敵対的レビュー

対象は `docs/plans/wiki-query-two-wikis-2026-11-16.md` の 15 版目である。応答は日本語で書く。ファイルは変えない。

## 位置づけ

15 版目は、作り直しの版である。8 回目のレビュー（`review-8.md`）のあと、作者は 14 版目をレビューにかける前に、設計を前提から見直すと決めた。4 体のエージェントの見直しと相互レビューの総括（`docs/agent-runs/2026-11-16-wiki-query-two-wikis-rethink/summary.md`）にもとづき、分離の確かめを、エージェントが呼ぶ補助（`wiki_roots.py`）から、2 つの根を受け取る読み手（MCP の新しいツール `pair_read` と CLI の `wiki_pair.py`）の中に移した。作者は、作り直しの前に第 6 節の 13〜15（CLI の戻り道を残す、raw は読み手の入口が根の下だけ読む、確かめを読み手の中に置く）を決めた。差分は `git diff origin/main -- docs/plans/` で見られる。

## このレビューで見ること

作り直しの直後は、仕様の矛盾や欠落（実装すれば必ず踏むもの）が出やすい。とくに次を見る。

- 第 3.9 節の読み手の仕様が、閉じているか。8 つの操作、確かめの順序（`State.wiki()` と `WikiIndex` より前）、根ごとの綴り・そろえた根・識別子、開くものの集まり（対称、記事でない開く場所の下をすべて、リンクには降りず先の識別子）、`relation` の順。
- 「確かめる者と読む者を同じにする」が実際に成り立つか。読み手が確かめたあと、確かめていないものを開く経路（MCP のサーバーの中の既存の索引、裏の埋め込みのスレッド、`State.wiki()` が持ち続ける索引、CLI の検索のキャッシュなど）がないか。
- 手順（第 3.2〜3.6 節）が、読み手の操作だけで回るか。読み手にない読み取りが残っていないか。CLI に戻る条件と、戻らない条件が閉じているか。
- raw の読み方（第 3.4 節）が、ADR-0029 の `resolve_raw()` と raw の根の記録と食い違っていないか。
- 15 版目の記述が、ADR-0029（`docs/adr/0029-wiki-and-raw-hold-no-links.md`）とその実装の設計（`docs/plans/wiki-links-2026-11-16.md`）と食い違っていないか。
- 試験の一覧で、読み手の要の振る舞いが確かめられるか。

本設計の 1〜8 回目のレビュー、4 体の見直しの成果と相互レビュー（`docs/agent-runs/2026-11-16-wiki-query-two-wikis-rethink/` の `results/`、`reviews/`）、ADR-0029 のレビューの記録と同じ指摘の繰り返しは除く。ただし、15 版目がそれらの指摘を直せていないなら、直せていないこととして挙げる。作者の決定（本設計の第 6 節の 1〜15、ADR-0029 の 1〜10）は崩す対象ではない。

重大の指摘には、発生の度合いを添える。A（仕様の矛盾か欠落で、実装すれば必ず踏む）、B（日常の使い方で起きうる）、C（まれな時機や名前）、D（作為的な配置が要る）。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コードは主のチェックアウト（`C:/Works/info-hive-dev/info-hive-wiki/`、v0.23.1 の `955c15a`）で読む。ADR-0029 の実装と読み手は、まだない。

- 設計書: `docs/plans/wiki-query-two-wikis-2026-11-16.md`
- ADR: `docs/adr/0029-wiki-and-raw-hold-no-links.md`、実装の設計: `docs/plans/wiki-links-2026-11-16.md`
- 4 体の見直し: `docs/agent-runs/2026-11-16-wiki-query-two-wikis-rethink/`
- コード: `C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/`（`wiki_mcp_server.py`、`wiki_mcp_relay.py`、`wiki_mcp_common.py`、`wiki_index.py`、`wiki_pages.py`、`wiki_search.py`、`wiki_graph_query.py`）、`C:/Works/info-hive-dev/info-hive-wiki/commands/query.md`、`C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md`
