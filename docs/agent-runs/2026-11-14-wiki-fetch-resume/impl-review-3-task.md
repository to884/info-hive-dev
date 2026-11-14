対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` で、途中の取り込みを取得の前に再開するようにした実装の 4 版である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`（4 版）。これまでのレビュー（同じフォルダーの `design-review-1.md`、`impl-review-1.md`、`impl-review-2.md`）と、設計書の「改訂の履歴」に、指摘と直し方がある。

差分は `docs/agent-runs/2026-11-14-wiki-fetch-resume/impl-3.diff` にある（worktree の中）。info-hive-wiki はサブモジュールで、変更はコミット済み（`git -C info-hive-wiki diff origin/main..HEAD`）。試験は親の `tests/wiki/test_wiki_web_check.py` の `ResumeBeforeFetchTest`。

保証（設計書の「前提」。4 版で定め直した）:
- 保証するのは整合である。写しのファイルの組（`fetched.md`、`fetch.json`、あれば `cleaned.md`）と raw が、1 つの取得と、その取得のあとの `freeze` が残しうる組のときだけ続ける。どこで止まっても、写しのファイルの一部を丸ごと別の取得のものに置き換えても（一部だけを戻したバックアップなど）、この組でなければ続けない。
- どの取得がその組を残したか（取得の出自）は保証しない。ファイルからは決められないからである。別の設定でも `fetched.md` が同じバイト列になる 2 つの取得は、どちらの `fetch.json` で続けても正しい組とする。別の取得の `cleaned.md` でも、今の `fetched.md` のあとの `freeze` が通す内容なら、正しい組とする。
- 作業用の写しは `wiki_fetch.py` と `wiki_rawcheck.py freeze` だけが書く。ファイルの中を手で書き換えたものは前提の外である（形の違う `fetch.json` で例外にならないことは守る）。

目的:
- `--html-file` で取ったページの取り込みを URL だけで再開でき、ネットにつながらなくても続けられること。
- 写しがないとき、raw と別の取得の写しのとき、`--force`、`--html-file`、別の URL のときは、今の動き（取得して比べる）を変えないこと。0.14.0 が書いた写し（`fetched_sha256` がない）は、0.14.0 と同じに、取得して原文が同じときだけ続けること。
- 続けるときに、最後に終えた段の出力（`fetched` なら前の取得の警告と規則で消したもの、`frozen` なら `freeze` の報告）と `source_sha256_of` を返し、手順書（`info-hive-wiki/commands/ingest.md` の W2・W3・W5、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`）がその確かめの段から続け、ループしないこと。
- `freeze` から切り出した `deletion_errors` と `deletion_report` で、`freeze` の出力（誤りの順と文、報告）が変わっていないこと。

判定の基準: 上の保証に反する反例（続けてはならない組で続ける、続けてよい組を続けない）を重大とする。保証の外のもの（出自、手で書き換えたファイルの中）は、設計書の「限界」に書いたものと同じに扱い、軽微か範囲の外とする。

特に崩してほしい点:
- `wiki_rawcheck.resumable_fetch` の条件（設計書の 5〜10）で、保証に反する反例。
- `cleaned.md` の照合（`deletion_errors`）が、`freeze` の判定と食い違う場合。`freeze` が通した `cleaned.md` を通さない、または `freeze` が通さない `cleaned.md` を通す場合。
- 取得の前の再開と、取得して比べる枝の、出力と文字の出力の食い違い。
- 手順書の流れの矛盾、ループ、詰まり。特に W3 の `source_sha256_of` の扱い。
- 試験の抜けと、試験が実装の誤りを見逃す書き方。
- CHANGELOG の記述と実装の食い違い。

設計書の「限界」に書いたものは範囲の外として承知している。並行する PR（to884/info-hive-wiki#54 が `write_outputs` と `build` の最後の `os.replace` を直している）との衝突は、ここでは問わない。
