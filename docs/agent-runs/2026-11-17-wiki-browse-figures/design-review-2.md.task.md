# 図の描画の設計の 2 回目のレビュー

対象は、Claude Code プラグイン `wiki`（サブモジュール `info-hive-wiki`）のコマンド `/wiki:browse` に、Mermaid の図と svg の表示を足す設計の 2 版目である。

- 設計書: `docs/plans/wiki-browse-figures-2026-11-17.md`（2 節に、1 回目のレビューで崩れた前提と 2 版目の形の対応がある）
- 決定: `docs/adr/0030-wiki-browse-shows-figures-as-images.md`（提案）
- PoC の記録: `docs/research/wiki-browse-figures-poc-2026-11-17.md`（「2 回目の PoC」の節）。試作は `poc/browse-figures/`（今の `src/figures.js` が 2 版目の方式）
- 1 回目のレビュー: `docs/agent-runs/2026-11-17-wiki-browse-figures/design-review-1.md`

設計が守るべき目的は次のとおりである。

1. ページの CSP（`style-src 'self'`、`script-src 'self'`）を緩めず、`[style]` と CSP の違反が 0 件のまま、図を見せる。
2. wiki の本文（Web から取り込んだ信頼しない入力を含む）に Mermaid の欠陥を突く図があり、枠の中で任意のスクリプトが動いても、その図を書いた人がすでに知っている以上のもの（ほかの図、ページの本文、wiki のデータ、表示と操作のトークン、cookie）を知りえず、親の文書を操作できない。
3. 既存の閲覧の契約を壊さない: 中核と届け方の分離（ADR-0010）、2 方式（サーバーと `file://`）、入力の走査と写し（`wiki_browse_fs.py`、`wiki_browse_core.py` の `take_snapshot`）、出力の名前（`assign_names`、`_clashes`、`RESERVED_TOP`）、自分が作ったものだけを置き換える（ADR-0017）、ローカルだけのサーバーの条件（ADR-0001）、世代と静的の書き出しの門、公開の前の検査。
4. 見た目は同梱の `fluent2.css` の部品とトークンだけで組む。

実装の現状は `info-hive-wiki/skills/info-hive/scripts/` の `wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_pages.py`、`wiki_lint.py`、`browse_assets/` にある。コードで確かめてほしい。

とくに次を崩せるか見てほしい。

- 7.1 節の「枠が知ってよいもの」の表。2 版目の形で、枠の中の任意のスクリプトが、目的 2 の外のものを知る、または親を操作する道が残っていないか（`/_frame/<版>/` のパスの限り方と CSP のパスの照合の規則、リダイレクト、同じオリジンへの自分の移動、`postMessage` の受け取り、画像と `alt`、キャッシュ、ほかのタブやページの枠との関係など）。
- `/_frame/` をトークンなしで配ることが、ADR-0001 の条件（127.0.0.1 への固定、起動ごとのトークン、Host の確かめ、書き込みの API なし）の目的を崩さないか。
- 6.1 節の守る範囲の書き直しと 6.2 節の読む口の上限、UTF-8 の限りが、1 回目の重大 3 と 4 を閉じているか。
- 図ごとの枠にしたことで生まれる新しい欠陥（同時に 2 つ、描き直しの途中の配色の変化、時間切れ、消した枠の知らせ）。
- 1 回目の指摘のうち、2 版目で閉じていないもの。
