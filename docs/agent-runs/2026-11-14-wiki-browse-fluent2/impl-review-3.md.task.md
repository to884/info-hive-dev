# browse の探しやすさと Fluent 2 の実装のレビュー（3 回目）

## 対象

- プラグインの差分: `git -C info-hive-wiki diff origin/main..feature/browse-fluent2`（`skills/info-hive/scripts/wiki_browse_core.py`、`browse_assets/app.js`、`browse_assets/style.css`、`browse_assets/theme.js`、同梱の `browse_assets/fluent2.css` と `licenses/`、文書）
- 試験: `tests/wiki/test_browse.py`、`tests/wiki/test_browse_server.py`、`tests/wiki/browse/findability.test.mjs`、`tests/wiki/browse/startup.test.mjs`、`tests/wiki/browse_nav/`
- 設計（承認済み）: `docs/plans/wiki-browse-findability-2026-11-13.md`（8 版目。2.2 は実装の段で直した）、`docs/plans/wiki-browse-fluent2-2026-11-14.md`（4 版目）、`docs/plans/wiki-browse-structure-2026-11-11.md`（実装済み）、ADR-0010、0017、0021

## 目的

実装が設計の約束を守るかを確かめる。特に:

1. 木の規則（N1〜N8）と 2.1 の末尾の 5 つの性質。参照の実装 `tests/wiki/browse_nav/nav_model.py`（書き換える前の中核 `core_before.py` の上の 2 つ目の段）と同じ木になること。
2. 構造の直しの約束（読めない入力は、その入力がない Wiki と同じに描き、読み取りの印を足す。描く側は機械の情報を持たない）を、木、索引のページ、`data/search.js` が破らないこと。
3. 要約（4.2）、検索（5.1〜5.5）、索引のページの絞り込み（4.3）、変換中のキー、後からの読み込み、状態の表示。
4. 画面の契約: CSP、`[style]` 0 件、classic なスクリプトだけ、2 方式で同じ、スクリプトなしで読める、`data-theme` の例外だけ。
5. Fluent 2: 配色の切り替えと保存、4.2 の状態と文字の色の規則、4.3 の折り返し、ライセンスの表示、同梱の資産の一致。

## 止める条件（作者が決めたこと）

指摘には分類を付ける。

- A: 失敗も競合も入れない正しい使い方で、設計の約束を破る反例（具体的な入力か操作と、破る約束を書く）。
- B: 試験だけの欠陥で、実装は正しいもの。
- C: 表現、試験の網羅、限界の書き漏らし。

A が 0 件なら、残りは直すか限界に書いて、作者の承認に回す。

## これまでの変化

1 回目（A 2 件）と 2 回目（A 1 件）の対応は `docs/agent-runs/2026-11-14-wiki-browse-fluent2/impl-responses.md` にある。直した所が反例を塞ぐか、別の反例が残っていないかを確かめる。プラグインの差分は `docs/agent-runs/2026-11-14-wiki-browse-fluent2/impl-review-3.plugin.diff`。
