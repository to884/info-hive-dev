# 図の描画の設計の 1 回目のレビュー

対象は、Claude Code プラグイン `wiki`（サブモジュール `info-hive-wiki`）のコマンド `/wiki:browse` に、Mermaid の図と svg の表示を足す設計である。

- 設計書: `docs/plans/wiki-browse-figures-2026-11-17.md`
- 決定: `docs/adr/0030-wiki-browse-shows-figures-as-images.md`（提案）
- PoC の記録: `docs/research/wiki-browse-figures-poc-2026-11-17.md`。試作は `poc/browse-figures/`（`src/figures.js`、`src/mermaid-frame.js`、`serve.py`、`setup.py`、`test.mjs`）

設計が守るべき目的は次のとおりである。

1. ページの CSP（`style-src 'self'`、`script-src 'self'`）を緩めず、`[style]` と CSP の違反が 0 件のまま、図を見せる。
2. wiki の本文（Web から取り込んだ信頼しない入力を含む）に Mermaid の欠陥を突く図があっても、親の文書、cookie、表示のトークン、wiki のファイルに届かず、外へ送れない。
3. 既存の閲覧の契約を壊さない: 中核と届け方の分離（ADR-0010）、2 方式（サーバーと `file://`）、入力の走査と写しの決まり（`wiki_browse_fs.py`、`wiki_browse_core.py` の `take_snapshot`）、出力の名前の決まり（`assign_names`、`_clashes`、`RESERVED_TOP`）、自分が作ったものだけを置き換える（ADR-0017）、リンクを読まない（ADR-0029）、世代と静的の書き出しの門。
4. 見た目は同梱の `fluent2.css` の部品とトークンだけで組む。

実装の現状は `info-hive-wiki/skills/info-hive/scripts/` の `wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_pages.py`、`wiki_lint.py`（`missing_assets`）、`browse_assets/`、試験は `tests/wiki/test_browse*.py` と `tests/wiki/browse/` にある。設計書の行番号ではなく、コードで確かめてほしい。

とくに次を崩せるか見てほしい。

- 7.5 節の「枠の中の欠陥が届く範囲」の表。枠の中で任意のスクリプトが動いたとき、外へ送る、表示のトークンを漏らす、親を操作する、利用者を騙す道が残っていないか（sandbox の枠の自分自身の移動、`frame-src` の効く範囲、`postMessage` の受け取り、`data:` の画像、`alt` など）。
- 6 節の svg の入力の走査と写しの変更が、`walk_inputs` の知らせ、`signature_of`、`take_snapshot` の 2 回の走査、`_machine_needles`、`fs.build` と、矛盾しないか。出力の名前 `assets/wiki/<16 桁>.svg` が、既存の出力や予約と衝突しないか。
- 6.4 節の `figure_target` が lint の `missing_assets` とずれる入力と、そのずれで困ること。
- 7.2 節の CSP の値が、目的 1 と 2 を満たし、PoC の結果と矛盾しないか。
- 静的の書き出しで Mermaid を描かない決定と、ADR-0016 との関係の書き方。
