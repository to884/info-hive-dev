# type と updated を配列や値なしで書いたページの扱いの修正の敵対的レビュー（2026-11-14）

wiki 0.12.2 の記録（`2026-11-13-wiki-title-list-values/README.md` の「直していないこと」）に、`type` と `updated` を配列で書くと `--json` に配列のまま出ると残していた。frontmatter のパーサーは値を書かれた形のまま返すので、`type: [concept]` は配列、値なしの `type:` は空の配列になる。調べると、配列のまま出るだけでなく、次の取り違えもあった。

- `--type` と `--since` の絞り込みが、そのページを外す。
- 統計が、種類なしと数える。
- lint とグラフが、`type: [source]` のページを source と読まない。
- グラフの抽出が、配列の `type` と `kind` を sqlite に渡して止まる。

この修正は 2026-11-13 に作りかけたまま、コミットされずに worktree（`full-ocr-continue-94ee76` の `info-hive-wiki`）に残っていた。2026-11-14 に、作者の依頼で、いまの main（0.14.0 のあと）に載せ直して仕上げた。

`wiki_pages.scalar_value()`、`type_value()`、`kind_value()` を足し、`type`、`kind`、`updated`、`created` を読む箇所をそろえた。

- 文字と `None` は、そのまま返す。
- 配列は、0.12.2 の `title` と同じく、空でない要素を「, 」でつなぐ。`type` と `kind` の要素は、日本語の別名を英語に直す。
- 空なら `None` にする。

GPT-6.1 Sol（effort high、`ask-codex` の `review`）に 1 回レビューしてもらった。

- 依頼: `review-sol.md.task.md`。対象は次のとおり。
  - 差分 `reviewed.diff`（`origin/main..d86985a`。`info-hive-wiki` の 8 つのスクリプト、CHANGELOG、`docs/search.md`、`references/graph-workflow.md`）。
  - `--target` で渡した試験 `info-hive-wiki/eval/scripts/test_scalar_values.py`。
  - 親の `tests/wiki/test_wiki_index.py` に足した試験は、レビューのあとに足したので、レビューの対象に入っていない。
- 結果: `review-sol.md`（条件付きで採用可、確信度 中。致命的・重大な欠陥はなし）
- レビュアーの環境は読み取り専用で、PyYAML もなかったので、CLI と試験は流していない。グラフの空値と判定の候補の数は、対象のソースから関数を取り出して確かめている。

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| lint の `index_type_mismatch` と `unresolved_sources` の `type` が、そろえた値（`"concept"`）になり、配列で書いたことが分からなくなる。CHANGELOG の「lint の指摘は書かれた形のまま出す」に反する | 軽微 | 指摘ごとに塞がず、lint の指摘の値の規則を 1 つにした。書き方を指摘するもの（`non_iso_dates` の `value`）だけを書かれた形のまま出す。判定に使った値を示す欄（`index_type_mismatch` と `unresolved_sources` の `type`、`stale_pages` の `updated`）は、比べた値と同じく、そろえた値を出す。`stale_pages` の `updated` は配列のまま残っていた（人が読む出力に `['2026-03-01']` と出る）ので、この規則に合わせて直した。CHANGELOG に規則を書いた |
| グラフのノードの値なしの `type` などは、CHANGELOG の言う `null` でなく `""` になる | 軽微 | グラフのノードは前から値なしを `""` にしていた（sqlite には `NULL` で入る）。振る舞いは変えず、CHANGELOG を「値がないか空の配列なら、今までどおり `""` にする」に直した |
| `type: [concept, entity]` は「どの `--type` にも当たらない」とあるが、`--type "concept, entity"` には当たる | 軽微 | CHANGELOG を「`--type concept` にも `--type entity` にも当たらず、`--type "concept, entity"` にだけ当たる」に直した |
| `--decide` を付けた試験は、証拠がソースの本文にあるので判定の候補が 0 件になり、`decide_evidence()` の source の判定を元に戻しても気づかない | 軽微 | 証拠が本文にない 2 つ目の関係を足し、`--decide` の出力の `evidence_check.candidates` が 1 になることを確かめるようにした |

上の直しはレビューのあとに入れた（`78dfc31`）。レビューにはかけ直していない。

## 確かめたこと

- 足した試験は、該当する実装を元に戻すとどれも失敗し、修正後はどれも通った。
  - 親の `test_list_type_and_updated_are_strings` は、修正前の wiki（`318a357`）で `(['concept'], ['2026-03-01'])` を返して失敗した。
  - `decide_evidence()` の source の判定を生の値の比較に戻すと、`candidates` が 0 になって失敗した。
  - `stale_pages` の `updated` を生の値に戻すと失敗した。
- Windows 11 の Python 3.12 で、次の試験が通った。
  - プラグイン: `eval/scripts` のすべて（`test_scalar_values.py` の 10 件を含む）、`test_link_resolution.py`（113 件）、`eval/retrieval/test_search_contracts.py`（24 件）、`test_embedding_mode.py`、`eval/decisions`（43 件）、`eval/check_encoding.py`
  - 親の `tests/wiki`（browse を除く）: 索引（20 件）、MCP サーバー（32 件）、グラフ（53 件、29 件、5 件）、lint、page_set、未初期化の wiki（41 件）、走査、Python の版、frontmatter、fetch、Web の検査、テンプレートのパス
- `eval/retrieval/test_setup.py` は、埋め込みの依存（`fastembed`、`sqlite-vec`）が入っているかを確かめる試験で、この環境では入っていないので失敗する。修正前の main でも同じく失敗する。
- 評価ゲート（`run_eval.py --gate --baseline`）の出力が、修正の前後でバイト単位で同じだった。

## 直していないこと

- 閲覧（`wiki_browse_core.py`）は、索引にないページを種類で分ける欄で、配列の `type` を `['concept']` と出す。止まりはしない。`sources:` の参照の解決（`classify_source_ref`）は、閲覧では当たるページだけを使い、種類の判定の結果は使わないので、表示は変わらない。browse の構造を直す設計が別に進んでいるので、触らなかった。
- MCP の `get_page` の `meta` は、frontmatter をそのまま返すツールなので変えていない。
- バージョンは上げていない。CHANGELOG の `[Unreleased]` に書いた。main の `plugin.json` は 0.14.0 だが、v0.14.0 のタグとリリースはまだない。`[Unreleased]` には、ほかのセッションの `wiki_fetch.py` の修正（to884/info-hive-wiki#54）も入っている。
