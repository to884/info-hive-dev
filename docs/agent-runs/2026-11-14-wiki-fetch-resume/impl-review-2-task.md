対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` で、途中の取り込みを取得の前に再開するようにした実装の 3 版である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`（3 版）。1 版は設計レビュー（`docs/agent-runs/2026-11-14-wiki-fetch-resume/design-review-1.md`）、2 版は実装レビュー（同じフォルダーの `impl-review-1.md`）で却下された。設計書の「改訂の履歴」に、指摘と直し方を書いた。

差分は `docs/agent-runs/2026-11-14-wiki-fetch-resume/impl-2.diff` にある（前回は差分のファイルを読めなかったので、今回は worktree の中に置いた）。info-hive-wiki はサブモジュールで、変更はコミット済み（`git -C info-hive-wiki diff origin/main..HEAD`）。試験は親の `tests/wiki/test_wiki_web_check.py` の `ResumeBeforeFetchTest` に足した（未コミット）。

守る範囲（設計書の「前提」）:
- 作業用の写しは、`wiki_fetch.py` と `wiki_rawcheck.py freeze` だけが書く。
- 守るのは、どこで止まっても続けてはならない写しで続けないことと、写しのファイルを丸ごと別の取得のものに置き換えたとき（一部だけを戻したバックアップなど）にその写しで続けないことである。
- ファイルの中を手で書き換えたものは前提の外である（ただし、形の違う `fetch.json` で例外にならないこと）。

目的:
- `--html-file` で取ったページの取り込みを URL だけで再開でき、ネットにつながらなくても続けられること。
- 写しがないとき、raw と別の取得の写しのとき、`--force`、`--html-file`、別の URL のときは、今の動き（取得して比べる）を変えないこと。0.14.0 が書いた写し（`fetched_sha256` がない）は、0.14.0 と同じに、取得して原文が同じときだけ続けること。
- 続けるときに、最後に終えた段の出力（`fetched` なら前の取得の警告と規則で消したもの、`frozen` なら `freeze` の報告）を返し、手順書（`info-hive-wiki/commands/ingest.md` の W2・W3・W5、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`）がその確かめの段から続けること。
- 前回までの重大な指摘（警告が消える、`fetch.json` だけ別の取得のもの、同じ原文を別の設定で取った `fetch.json`、`freeze` の報告を読む段を飛ばす）が、反例を塞ぐだけでなく、原因の構造で直っていること。

特に崩してほしい点:
- `fetched_sha256` での結びつけ（`wiki_rawcheck.resumable_fetch`）で、前提の範囲の中で、続けてはならない写しで続ける反例。続けてよい写し（0.14.0 の写しを含む）を続けない反例。
- `deletion_report` を `freeze` から切り出したことで、`freeze` の出力が変わっていないか。`frozen` の再開で作り直した報告が、`freeze` が出した報告と食い違う場合があるか（`cleaned.md` は `freeze` が通したときの raw をそのまま書いたもの）。
- 取得の前の再開と、取得して比べる枝の出力と文字の出力の食い違い。
- 手順書の流れの矛盾、ループ、詰まり。
- 試験の抜けと、試験が実装の誤りを見逃す書き方。
- CHANGELOG の記述と実装の食い違い。

設計書の「限界」に書いたもの（写しがないときの DOM の raw の終了コード 3、frontmatter が同じ別の版の raw、取得して比べる枝で URL や `--page-url` が違うとき、0.14.0 の `--html-file` の取り込み）は範囲の外として承知している。並行する PR（to884/info-hive-wiki#54 が `write_outputs` と `build` の最後の `os.replace` を直している）との衝突は、ここでは問わない。
