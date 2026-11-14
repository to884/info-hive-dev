対象は、Claude Code プラグイン wiki（info-hive-wiki）の Web ページの取得器 `wiki_fetch.py` の、途中の取り込みを再開する判定を、取得の前に置く設計である。設計書は `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`。

目的:
- `--html-file` と `--page-url` で取得したページ（`source_sha256_of: "dom"`）の取り込みを途中でやめ、URL だけで取り直したとき、作業用の写し（`<WIKI_ROOT>/.wiki-cache/ingest/<スラッグ>/`）がそろっていれば、取得せずに前の取得の値を返して途中から続けられること。ネットにつながらないときも続けられること。
- 写しがないとき、raw と別の取得の写しのとき、`--force`、`--html-file`、別の URL のときは、今の動き（取得して比べる）を変えないこと。
- 写しの整合（fetch.json を raw のあとに置く順、raw の frontmatter と写しの照合）で守ってきた不変条件を壊さないこと。

読むべきファイル（パスは info-hive-dev のルートから）:
- 設計書: `docs/plans/wiki-fetch-resume-before-fetch-2026-11-14.md`
- 前提の設計: `docs/plans/wiki-web-ingest-check-2026-11-13.md`（作業用の写し、写しの印の順）
- 今のコード: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（`build` は 1201 行目から。今の再開の枝は 1234〜1261 行目）、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`（`work_dir_complete`、`work_dir_matches_raw`、`remove_work_dir`、`load_fetch`、`remaining_images`、`freeze`、`check`）
- 手順書: `info-hive-wiki/commands/ingest.md` の W2〜W9、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md` の「Web ページ」と「書き換えの検査」
- 今の試験: `tests/wiki/test_wiki_web_check.py`（`FetchCase`、`ResumeTest`、`FetchCounterexample9Test` など）

特に崩してほしい点:
- 取得の前の再開の条件（設計書の 1〜7）で、続けてはならない状態を続けてしまう反例（別の取り込みの写し、終えた取り込み、手で戻した raw、別のスラッグや URL、`--keep-noise` や `--no-images` の違い、取得の途中で止まった `--force` など）。
- `--html-file` を判定から外す理由が成り立つか。外したことで残る詰まり（DOM を保存し直して渡すと終了コード 3 になる、など）が、手順書の流れで問題になるか。
- 「ページの更新を、取り込みを終えるまで知らせない」という意図した変更が、手順書（W2 の終了コード 3 の分岐、取り込みの完了の判断）と矛盾しないか。
- 出力の形（`unchanged: true` と `fetch_skipped: true` の組み合わせ）が、手順書の分岐や呼び出し側を誤らせないか。
- 試験の計画に抜けがないか。

設計書の「限界」（写しがないときに、DOM の raw を URL で取り直すと終了コード 3 になる）は範囲の外として承知している。それでも、この設計がその限界を悪化させるなら指摘してほしい。
