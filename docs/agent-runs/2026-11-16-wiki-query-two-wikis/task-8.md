# 依頼：2 つの wiki を引く問い合わせの設計（13 版目）の敵対的レビュー

対象は `docs/plans/wiki-query-two-wikis-2026-11-16.md` の 13 版目である。応答は日本語で書く。ファイルは変えない。

## 位置づけ

12 版目までの設計は、7 回のレビュー（どれも却下）を受け、作者が 12 版目でレビューを止めた。そのあと、raw と wiki の記事にリンクを置かない規則が ADR-0029（`docs/adr/0029-wiki-and-raw-hold-no-links.md`）として承認された。実装の詳細は `docs/plans/wiki-links-2026-11-16.md` にある。13 版目は、レビューの指摘ではなく、ADR-0029 と作者の新しい決定に合わせた直しである。差分は `git diff origin/main -- docs/plans/` で見られる。

作者の新しい決定（第 6 節の 12）: 2 つを引く問い合わせは、記事のリンク（ADR-0029 の違反）では止めず、警告を付けて続ける。補助は共有だけを判定する。

## 13 版目の新しい前提（ここを重く見る）

1. **補助の `links` を外した。** ADR-0029 の変えたあとの走査は、リンクの記事を読まず、拒んだ項目を `Walk.links` で返す。だから、リンクを通して他方の wiki の中身が混ざることはない、とした。
2. **`shared` が比べるものを「開くものの集まり」に絞った。** 根の下のすべてではなく、問い合わせが開くもの（記事、走査が降りたディレクトリ、`graph/`、`.wiki-cache/` の決まったファイル、MCP の索引のディレクトリ）だけの識別子を比べる。記事でない開くものは、リンクをたどった先の識別子を取る。拒んだ記事は入れない。`.git/` などの、開かない場所のリンクやハードリンクでは止めない。
3. **ADR-0029 の実装が先にあることを、コードで確かめる。** `Walk` に `links` の欄がない `wiki_pages` では、補助が `null` を返す。

## このレビューで見ること

- 上の 3 つの前提を崩す配置、操作の順、コードの事実がないか。とくに、2 つを引く問い合わせの手順（第 3.2〜3.6 節）が開くのに「開くものの集まり」に入っていないもの、警告を付けて続けたときに他方の中身が回答に入る経路、拒んだことが「ない」に変わる経路。
- 13 版目の記述が、ADR-0029 とその実装の設計（記事の定義、走査、記事を読む口、`resolve_raw()`、書き込みの部品、I1〜I7）と食い違っていないか。
- 試験の一覧で、新しい前提が確かめられるか。

ADR-0029 の作者の決定（1〜10）と、本設計の第 6 節の作者の決定（1〜12）は崩す対象ではない。本設計の 1〜7 回目のレビュー（`docs/agent-runs/2026-11-16-wiki-query-two-wikis/review-1.md`〜`review-7.md`）と、ADR-0029 のレビューの記録（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/`）と同じ指摘の繰り返しは除く。

重大の指摘には、発生の度合いを添える。A（仕様の矛盾か欠落で、実装すれば必ず踏む）、B（日常の使い方で起きうる）、C（まれな時機や名前）、D（作為的な配置が要る）。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コードは主のチェックアウト（`C:/Works/info-hive-dev/info-hive-wiki/`、v0.23.1 の `955c15a`）で読む。ADR-0029 の走査はまだ実装されていない。

- 設計書: `docs/plans/wiki-query-two-wikis-2026-11-16.md`
- ADR: `docs/adr/0029-wiki-and-raw-hold-no-links.md`
- ADR-0029 の実装の設計: `docs/plans/wiki-links-2026-11-16.md`
- コード: `C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/`（`wiki_pages.py`、`wiki_index.py`、`wiki_search.py`、`wiki_graph_query.py`、`wiki_mcp_server.py`、`wiki_mcp_common.py`）、`C:/Works/info-hive-dev/info-hive-wiki/commands/query.md`、`C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md`
