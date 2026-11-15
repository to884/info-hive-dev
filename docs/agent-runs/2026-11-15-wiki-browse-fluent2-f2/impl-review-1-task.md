# browse の記事のページを Fluent 2 にする実装（段 F2）のレビュー（1 回目）

## 対象

- プラグインの差分: `docs/agent-runs/2026-11-15-wiki-browse-fluent2-f2/impl-review-1.plugin.diff`（`git -C info-hive-wiki diff origin/main..feature/browse-fluent2-article`。`skills/info-hive/scripts/wiki_browse_core.py` と `browse_assets/style.css`）。変更後のファイルは `info-hive-wiki/skills/info-hive/scripts/` にある
- 試験の差分: `docs/agent-runs/2026-11-15-wiki-browse-fluent2-f2/impl-review-1.tests.diff`（`tests/wiki/test_browse.py`、`tests/wiki/browse/findability.test.mjs`、`tests/wiki/browse_read_sweep.py`）
- 設計（承認済み）: `docs/plans/wiki-browse-fluent2-2026-11-14.md` の 5 節（段 F2）。4.2（状態で地を変える要素と文字の色）、4.3（利用者の文字の折り返し）、1 節（守ること）、6 節（試験）も守る
- 下敷きにした試作: `poc/browse-fluent2/proto_fluent.py` と `poc/browse-fluent2/assets/style.css` の記事の規則
- 同梱の `browse_assets/fluent2.css` は書き換えない（読んでよい）。F1 の実装のレビューの記録は `docs/agent-runs/2026-11-14-wiki-browse-fluent2/impl-responses.md`、F1 で崩れた前提は `wiki/concepts/browseのデザインシステム.md` にある

## 目的

実装が設計の 5 節の約束を守り、F1 までの約束を壊さないかを確かめる。特に:

1. `#_body`（Markdown の出力に class を足さない）: 16px と行間 1.8、幅 48em、h1〜h4 の書体のトークン、リンクの色と下線、コード、`pre`、表、引用、`hr`。`ta-*` が `#_body th` に負けないこと。`wl-unresolved`、`wl-ambiguous`、`wl-missing-heading`、`a.ext::after` が残り、色だけで区別しないこと。
2. 中核が描く部分: `#_meta` の `fui-Table`（small）と行、見出しのセル、値のセルの class。`#_relations` の `fui-Table`（small）を `div.table-scroll` で包み、最小幅 48em、表だけを横に送ること。`#_backlinks` の `ul.fui-List`。被リンク、関係、診断の見出しの `h2.fui-Subtitle2`。
3. 4.2: 読むだけの表と一覧の行は、ホバーと押下で地を変えない。brand のリンクの色は、祖先の地が状態で変わらない場所だけで使い、どの状態でも 4.5:1 を保つ（light と dark）。
4. 4.3: 利用者の文字（題名、タグ、要約、出典、関係の相手と証拠、診断）を持つ部品が、幅 320〜1000 で `#_main` とページから横にはみ出さない。関係表は入れ物の中だけで送る。
5. 画面の契約: CSP、`[style]` 0 件、ID の重複なし、2 方式（`file://` とサーバー）で同じ画面、スクリプトなしで本文、メタ欄、被リンク、関係表、診断が読めること。`class="wl` の数が wikilink の数と合うこと（`test_browse.py`）。`style.css` に hex と px を直に書かないこと。
6. 試験が約束を本当に確かめているか（測る要素がないと測らずに通る、状態の切り替わりの途中を測る、などの抜け）。

## 止める条件（作者が決めたこと）

指摘には分類を付ける。

- A: 失敗も競合も入れない正しい使い方で、設計の約束を破る反例（具体的な入力か操作と、破る約束を書く）。
- B: 試験だけの欠陥で、実装は正しいもの。
- C: 表現、試験の網羅、限界の書き漏らし。

A が 0 件なら、残りは直すか限界に書いて、作者の承認に回す。

## 実装の段で分かったこと

- 試作にあった `#_main a:active` の押下の色（`colorBrandForegroundLinkPressed`）は、暗い配色で 3.85:1 になり、試験が落とした。押下でもホバーの色のままにした。
- 試作の関係表は `word-break: keep-all` だったが、日本語の長い証拠が 1 行に伸びるので、`overflow-wrap: normal` と `word-break: normal`（日本語は文字の間で折り返し、英語の語は折らない）にした。見出しのセルは決まった文字なので `nowrap` にした。
- 関係表の入れ物は、キーボードで送れるように `role="region"`、`aria-label`、`tabindex="0"` を付けた。
- 試験の結果: `test_browse.py`、`test_browse_server.py`、`test_browse_fs.py` は通る。`findability.test.mjs`、`browse.test.mjs`、`startup.test.mjs` も Chromium の 2 方式で通る（押下を含むコントラストの最小は、明るい配色で 5.13、暗い配色で 4.74）。
