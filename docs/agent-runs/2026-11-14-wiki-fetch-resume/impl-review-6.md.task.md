対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` で、途中の取り込みを取得の前に再開するようにした実装の 7 版である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`（7 版）。これまでのレビュー（同じフォルダーの `design-review-1.md`、`impl-review-1.md`〜`impl-review-5.md`）と、設計書の「改訂の履歴」に、指摘と直し方がある。

差分は `docs/agent-runs/2026-11-14-wiki-fetch-resume/impl-6.diff` にある（worktree の中）。info-hive-wiki はサブモジュールで、変更はコミット済み（`git -C info-hive-wiki diff origin/main...HEAD`。origin/main はリリース済みの 0.14.1）。試験は親の `tests/wiki/test_wiki_web_check.py` の `ResumeBeforeFetchTest`。

7 版で変えたこと（6 版から）:
- 6 版の実装レビュー（`impl-review-5.md`）の重大 1 件（`--html-file` のファイルがない `OSError`、UTF-8 でない `ValueError` で止まると、旧版の写しを知らせない）を直した。`main` の例外の出口を `report_failure` の 1 か所にまとめ、`build` が上げるどの例外（`ValueError`、`FetchError`、`OSError`、`RecursionError`）でも、旧版の写しがあれば標準エラーに案内を足し、JSON を出す誤り（取得の失敗、入れ子の深すぎる HTML）では `old_work_dir` を付ける。終了コードと出力の対応は 6 版と同じ。
- 軽微 1 件（桁の多すぎる整数の `fetch.json` で、`JSONDecodeError` でない `ValueError` が漏れる）を直した。写しの判定（`work_dir_complete`、`old_version_work_dir`）は `OSError`、`ValueError`、`RecursionError` で偽を返す。`has_old_work_dir` は、規則に反するスラッグでも例外を上げない。

保証（設計書の「前提」。4 版から変えていない）:
- 保証するのは整合である。写しのファイルの組（`fetched.md`、`fetch.json`、あれば `cleaned.md`）と raw が、1 つの取得と、その取得のあとの `freeze` が残しうる組のときだけ続ける。どこで止まっても、写しのファイルの一部を丸ごと別の取得のものに置き換えても、この組でなければ続けない。
- 取得の出自は保証しない。別の設定でも `fetched.md` が同じバイト列になる 2 つの取得は、どちらの `fetch.json` で続けても正しい組とする。別の取得の `cleaned.md` でも、今の `fetched.md` のあとの `freeze` が通す内容なら、正しい組とする。
- 0.14.1 までの版が書いた写しは、どちらの枝でも続けない（意図した変更）。そのことは、取得の結果と止まった例外によらず利用者に知らせる。
- 作業用の写しは `wiki_fetch.py` と `wiki_rawcheck.py freeze` だけが書く。ファイルの中を手で書き換えたものは前提の外である（形の違う `fetch.json` で例外にならないことは守る）。

判定の基準: 上の保証に反する反例（続けてはならない組で続ける、続けてよい組を続けない、続けられない旧版の写しがあるのに知らせない、旧版の写しでないのに知らせる、形の違う `fetch.json` で例外になる）を重大とする。保証の外のもの（出自、手で書き換えたファイルの中）と、設計書の「限界」に書いたものは、軽微か範囲の外とする。

特に崩してほしい点:
- `report_failure` に移したことで、6 版までの例外の出力（終了コード、標準出力の JSON、標準エラーの文、`OSError` の注記）が変わっていないか。`main` の `try` が捕まえない例外の経路が残っていないか。
- 旧版の写しを知らせる判定の、取りこぼしと誤り。判定そのものが例外を上げる経路。
- 6 版までに崩せなかった点（新版の写しの整合、`cleaned.md` の照合、`freeze` の出力、取得の前の再開と取得して比べる枝の一致）が、7 版で崩れていないか。
- 手順書の流れの矛盾、ループ、詰まり。CHANGELOG の記述と実装の食い違い。
- 試験の抜けと、試験が実装の誤りを見逃す書き方。
