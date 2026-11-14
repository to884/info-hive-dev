対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` で、途中の取り込みを取得の前に再開するようにした実装の 6 版である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`（6 版）。これまでのレビュー（同じフォルダーの `design-review-1.md`、`impl-review-1.md`〜`impl-review-4.md`）と、設計書の「改訂の履歴」に、指摘と直し方がある。

差分は `docs/agent-runs/2026-11-14-wiki-fetch-resume/impl-5.diff` にある（worktree の中）。info-hive-wiki はサブモジュールで、変更はコミット済み（`git -C info-hive-wiki diff origin/main...HEAD`。origin/main はリリース済みの 0.14.1）。試験は親の `tests/wiki/test_wiki_web_check.py` の `ResumeBeforeFetchTest`。

6 版で変えたこと（5 版から）:
- 5 版の実装レビュー（`impl-review-4.md`）の重大 1 件（0.14.1 までの版で DOM から始めた取り込みを URL だけで呼ぶと、終了コード 3 になり、旧版の写しを続けられないことが伝わらない）を直した。
- `wiki_rawcheck.old_version_work_dir` で、写しがそろい、raw の frontmatter が写しと同じで、`fetch.json` が辞書だが `fetched_sha256` がない写しを、旧版の取り込みの途中と見分ける。`wiki_fetch.has_old_work_dir` がこれを使い（`--force` のときは問わない）、`build` は終了コード 0 と 3 の出力に、`main` は取得の失敗（終了コード 2）の出力に、`"old_work_dir": true` を付ける。文字の出力も、続けられないこと、`--force` で取り直すと途中の作業が消えること、終了コード 3 ならページの更新とは限らないことを書く。
- 手順書の W2 に、どの終了コードでも `old_work_dir` があれば `--force` で取り直すかをユーザーに聞く、を足した。CHANGELOG、`ingest-workflow.md` も合わせた。

保証（設計書の「前提」。4 版から変えていない）:
- 保証するのは整合である。写しのファイルの組（`fetched.md`、`fetch.json`、あれば `cleaned.md`）と raw が、1 つの取得と、その取得のあとの `freeze` が残しうる組のときだけ続ける。どこで止まっても、写しのファイルの一部を丸ごと別の取得のものに置き換えても、この組でなければ続けない。
- 取得の出自は保証しない。別の設定でも `fetched.md` が同じバイト列になる 2 つの取得は、どちらの `fetch.json` で続けても正しい組とする。別の取得の `cleaned.md` でも、今の `fetched.md` のあとの `freeze` が通す内容なら、正しい組とする。
- 0.14.1 までの版が書いた写しは、どちらの枝でも続けない（5 版で捨てた互換。意図した変更）。そのことは、取得の結果によらず利用者に知らせる（6 版）。
- 作業用の写しは `wiki_fetch.py` と `wiki_rawcheck.py freeze` だけが書く。ファイルの中を手で書き換えたものは前提の外である（形の違う `fetch.json` で例外にならないことは守る）。

判定の基準: 上の保証に反する反例（続けてはならない組で続ける、続けてよい組を続けない、続けられない旧版の写しがあるのに知らせない、旧版の写しでないのに知らせる）を重大とする。保証の外のもの（出自、手で書き換えたファイルの中）と、設計書の「限界」に書いたものは、軽微か範囲の外とする。

特に崩してほしい点:
- `old_version_work_dir` と `has_old_work_dir` の判定が、旧版の写しを取りこぼす場合、新版の写しや旧版でないものを旧版と誤る場合。`main` の取得の失敗の枝で、判定そのものが例外を上げる場合。
- `old_work_dir` を付ける出口の抜け（終了コード 0、3、2 のほか、`build` が上げる例外や、`--html-file` のとき）。
- 6 版の変更で、5 版までに崩せなかった点（新版の写しの整合、`cleaned.md` の照合、`freeze` の出力、取得の前の再開と取得して比べる枝の一致）が崩れていないか。
- 手順書の流れの矛盾、ループ、詰まり。CHANGELOG の記述と実装の食い違い。
- 試験の抜けと、試験が実装の誤りを見逃す書き方。
