# 依頼: 段階 2 の確認表を wiki 0.19.3 に合わせた直しの敵対的レビュー

## 対象の目的

`docs/research/usage-docs-stage2-checklist-2026-11-15.md` は、利用者向け文書の計画（`docs/plans/usage-docs-2026-11-15.md`）の段階 2 で、作者が新しい Windows 11 の VM で実行する確認表である。この表は wiki 0.16.0 で書かれていた。今回、wiki 0.19.3 に合わせて直した。

- W2（醤油の取り込み、`/wiki:browse`、`/wiki:lint`）は、browse 0.17.0 と Fluent 2 の画面（0.18.0）が出るまで待たせていた。条件がそろったので、確認 5 で W1 に続けて通す形にした。
- 0.16.0 から 0.19.3 までの変更を読み直し、表のパスと名前が同じことを確かめた、と書いた。
- W4（URL の取り込み）の行に、0.18.1 の `wiki_rawcheck.py check --finish --json` の出力を写すことを足した。
- 計画を 6 版にし、「段階 2 の前の読み直し」の節を足した。

差分は `git diff origin/main` で見られる。

## 確かめてほしいこと

- 確認表の主張（とくに「版について」の節、確認 5 の W2 の手順と判定、確認 10 の W4 の行）が、`info-hive-wiki` の v0.19.3 のコードとコマンドの定義と合うか。サブモジュール `info-hive-wiki` で `git show v0.19.3:<path>` と `git diff v0.16.0 v0.19.3` を使って読める。主な材料は `commands/browse.md`、`commands/lint.md`、`commands/ingest.md`、`skills/info-hive/scripts/wiki_browse.py`、`wiki_lint.py`、`wiki_mcp_server.py`、`wiki_rawcheck.py`、`skills/info-hive/references/web-raw.md`。
- W2 の判定が、計画の 2-5 の規則（目印に使ってよいのは、スクリプトかコマンドの定義が決めるものと、ツールの呼び出しの欄の出力だけ。モデルの判断で作られるページやリンク、返答の文章は使わない）に従っているか。
- W1 と W2 を同じセッションで続けて通すことで、W1 の判定や、確認 6（ruri の計測）と確認 10 の前提が崩れないか。
- 0.19.3 より新しい版が入ったときの扱い（「版について」）に穴がないか。
- 計画の新しい節と、計画のほかの箇所（段階 2 の手順、「段階 1 で作者が決めたこと」）が食い違っていないか。
