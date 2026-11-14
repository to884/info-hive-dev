対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` で、途中の取り込みを取得の前に再開するようにした実装である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`（2 版）。1 版は設計レビュー（`docs/agent-runs/2026-11-14-wiki-fetch-resume/design-review-1.md`）で却下され、2 版で直した。差分は `impl-1.diff`（`--target` で渡した絶対パスのファイル）にある。info-hive-wiki はサブモジュールで、変更はコミット済み（`git -C info-hive-wiki diff origin/main..HEAD`）。試験は親の `tests/wiki/test_wiki_web_check.py` の `ResumeBeforeFetchTest` に足した（未コミット）。

目的:
- `--html-file` で取ったページの取り込みを URL だけで再開でき、ネットにつながらなくても続けられること。
- 写しがないとき、raw と別の取得の写しのとき、`--force`、`--html-file`、別の URL のときは、今の動き（取得して比べる）を変えないこと。
- 写しの整合（fetch.json を raw のあとに置く順、raw と写しの照合）で守ってきた不変条件を壊さないこと。
- 1 版のレビューの重大 2 件（再開で警告が消える、fetch.json だけが別の取得のものなら誤った値を返す）と軽微 2 件が、反例を塞ぐだけでなく、原因の構造で直っていること。

特に崩してほしい点:
- `wiki_rawcheck.resumable_fetch` の照合（fetch.json と fetched.md の frontmatter の url、final_url、source_sha256、キーの型）で、続けてはならない状態を続ける反例、または続けてよい状態（0.14.0 が書いた写しを含む）を続けない反例。frontmatter の値の読み戻し（`parse_frontmatter_text`）と `format_fm_value` の往復が崩れる URL があるか。
- 取得の前の再開と、今の「原文が同じ」の枝の出力の食い違い。
- 手順書（`info-hive-wiki/commands/ingest.md` の W2・W3、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`）の流れが、出力と矛盾しないか。`fetched` なら W3 から続けることで、ループや詰まりが起きないか。
- 試験の抜けと、試験が実装の誤りを見逃す書き方になっていないか。
- CHANGELOG の記述が実装と食い違っていないか。

既知の限界（設計書の「限界」）は範囲の外として承知している。並行する PR（to884/info-hive-wiki#54 が `write_outputs` と `build` の最後の `os.replace` を直している）との衝突は、ここでは問わない。
