---
type: "source"
title: "検索の結果の tags と sources を文字の配列にそろえた修正と、wiki 0.12.1 のリリースの記録"
tags: ["検索", "リリース"]
authors: ["to884"]
raw: "docs/agent-runs/2026-11-13-wiki-search-json-list-fields"
ingested: 2026-11-13
created: 2026-11-13
updated: 2026-11-13
---

# 検索の結果の tags と sources を文字の配列にそろえた修正と、wiki 0.12.1 のリリースの記録

2026-11-13 の、`wiki_search.py --json` と MCP の `query` の結果の `tags` と `sources` を直した変更と、そのリリースの記録である。原本は、Sol の敵対的レビューと対応を残した `docs/agent-runs/2026-11-13-wiki-search-json-list-fields/` である。リリースと導入の確かめは、作業の記録から書いた。

## 経緯

1. 閲覧（browse）の画面の改修（`docs/plans/wiki-browse-ui-2026-11-13.md`、wiki 0.13.0 に向けた作業）で、埋め込みの検索の結果を `--json` の結果と同じ型にそろえる契約（`tests/wiki/browse/search_result_contract.json`）を作った。そこで、`wiki_search.py` 自身が契約から外れていると分かった。frontmatter に `tags: 検索` と値を 1 つだけ書くと、`json_result()` が `tags` を文字のまま返していた（`sources` も同じ）。browse の作業の範囲の外とし、別のセッションで直した。
2. 結果を作る `json_result()` の 1 か所で、`tags` と `sources` を `wiki_pages.ref_values()` で作るようにした（[[frontmatterのリストの値]]）。CLI の section と page の粒度、`--decide`、パースキャッシュから読んだ値、MCP の `query`（`WikiIndex.search`）は、どれもこの関数を通る。
3. 試験を先に書き、修正前の実装で失敗することを確かめてから直した。CLI の経路はプラグインの `eval/retrieval/test_search_contracts.py` に、MCP の `query` の経路は親の `tests/wiki/test_wiki_index.py` に置いた。
4. 評価ゲート（`run_eval.py --gate --baseline` と `--set ja`）の出力と、評価のコーパスの英語と日本語の全クエリの `--json` の出力（section と page で 170 通り）を、修正の前後で比べた。どちらもバイト単位で同じだった。
5. GPT-6.1 Sol の敵対的レビューは、採用可（確信度は高）だった。軽微な指摘 2 件（CHANGELOG の「変わらない」の範囲が広すぎる、`--decide` と MCP の経路の試験がない）を直した。直しはレビューにかけ直していない。
6. 子の PR（to884/info-hive-wiki#50）と親の PR（to884/info-hive-dev#87）を出した。親の PR は、はじめ子の PR の head（`a32a373`）を指した。子の CI（Linux と Windows の Python 3.12 と 3.14）が通ったところで、作者の指示で子をマージした（`5326bf9`）。親の CI は、まだ 2 つのジョブが走っていた。
7. 親の参照を子のマージコミットに付け替えた（`102e51f`、木の差はない）。親のリポジトリでは GitHub の自動マージが許されていなかった。CI の 9 つが通ったのを確かめてから、親をマージした（`d100dfd`）。
8. `5326bf9` に注釈付きのタグ `v0.12.1` を付け、GitHub リリースを作った（2026-11-13 08:41、日本時間。GitHub の記録では 2026-11-12T23:41Z）。題名は `v0.12.1`、本文は CHANGELOG の 0.12.1 の節である。
9. 使い捨ての設定でマーケットプレイスから入れ、0.12.1 が入ることを確かめた（[[リリースの確かめ方]]）。変更した 5 つのファイルの SHA-256 がタグの中身と一致し、入った `wiki_search.py` は `tags: 検索` を `["検索"]` にした。

## 決めたこと

- 直すのは結果を作る `json_result()` だけにした。パーサーとパースキャッシュには手を入れず、出すときにそろえる。どの経路もこの関数を通るので、1 か所で足りる。
- そろえる規則は新しく作らず、lint が `sources` を読むのに使っている `ref_values()` を使った。`normalize_tags()` は NFKC をかけて値そのものを変え、`""` を `[""]` にする。グラフの `_tag_list()` は要素を文字にしない。どちらも結果の欄には合わない（[[frontmatterのリストの値]]）。
- `ref_values()` は要素の前後の空白と空の要素を除くので、`tags: ["", " x "]` は `["x"]` に変わる。これを CHANGELOG に書いた。「規約どおりのページは変わらない」と書いたところ、Sol に、引用符の中に空白のある配列は変わると指摘された。そこで「配列で書いていて、要素が空でなく、引用符の中に前後の空白もないページ」と範囲を狭めた。
- 版はパッチ（0.12.1）にした。契約から外れていたのを直す修正で、新しい機能はない。
- 同じ種類の別の欠陥（`title` を配列で書くと検索が止まる、など）は、直す規則を決める必要があるので、範囲の外として残した（[[frontmatterのリストの値]]）。

## 途中で起きたこと

- 子のサブモジュールの手元の `main` は、PR #46 のころの古いコミット（`b383121`）を指していた。`origin/main`（`a3d05e6`、0.12.0）からブランチを切った。
- `git show origin/main:.claude-plugin/plugin.json` を Git Bash で実行して、また引数が書き換えられて失敗した（[[git-bashのパス変換]]）。
- `skills/info-hive/scripts/test_link_resolution.py` を依存なしの `python` で動かすと、`wiki_graph_extract.py` が PyYAML を求める案内を出し、終了コード 2 で止まった。`uv run --with pyyaml==6.0.3` で動かすと 113 件が通った。
- browse の改修のブランチも、`plugin.json` と `CHANGELOG.md` を 0.13.0 に向けて変えている。0.12.1 が先に main に入ったので、browse の側で 0.12.1 の上に重ねる必要がある。セッションの共有メモで伝えた。
- 2 つの PR に、Codex の自動レビューが付いた。どちらも指摘は 0 件だった。

## 主張と行き先

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| 1 | パーサーが返す値の形と、リストの値をそろえる関数ごとの違い | `wiki_text.py`、`wiki_pages.py`、`wiki_graph_extract.py`、作業の記録 | create | [[frontmatterのリストの値]] |
| 2 | `title`、`type`、`updated` を配列で書いたときの欠陥と、MCP の `get_page` の `meta` | `review-sol.md`、作業の記録 | update | [[frontmatterのリストの値]] の「残っている欠陥」 |
| 3 | 作者の指示で、親の CI を待たずに子をマージした。親のリポジトリでは自動マージが使えない | 作業の記録 | update | [[リリースの確かめ方]] の「リポジトリをまたぐマージの順番」 |
| 4 | v0.12.1 も注釈付きのタグにした | 作業の記録 | update | [[リリースの確かめ方]] の「タグとリリースの形」 |
| 5 | Git Bash のパス変換を、0.12.1 のリリースでもまた踏んだ | 作業の記録 | update | [[git-bashのパス変換]] の「起きた所」 |
| 6 | 検索の出力を変えないはずの修正では、評価ゲートに加え、全クエリの `--json` を前後でバイト単位で比べる | 作業の記録 | source_only | 今回の確かめ方で、ほかの修正でも同じ形で使うかは決めていない |
| 7 | `test_link_resolution.py` は PyYAML がないと止まる | 作業の記録 | source_only | 試験の動かし方の事情で、ほかのページから引く話ではない |

## 関係するページ

- [[frontmatterのリストの値]]
- [[リリースの確かめ方]]
- [[git-bashのパス変換]]
- [[browseのスコープ表示とリリース-wiki-0.12.0]]
