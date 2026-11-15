# レビューの目的

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。調査レポート `docs/research/wiki-youtube-transcript-2026-11-15.md` の選択肢 A2（yt-dlp で字幕を取る）と B2（取り込みに動画の分岐とスクリプトを足す）の組み合わせを決める。

この ADR を実装の根拠にしてよいかを判定する。実装すると必ず踏む仕様の矛盾や欠落、日常の使い方で起きる誤り、既存の ADR と要件との食い違いを探す。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前例と制約: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0018-wiki-requires-python-312.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の F-I02、F-I03、F-I08、F-I10〜F-I15、S-01、O-14
- 今の取り込みの手順: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/CONTRIBUTING.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）
- 調査レポート: `docs/research/wiki-youtube-transcript-2026-11-15.md`

ADR-0026（uv で動くスクリプトの Python の範囲を `>=3.12,<3.15` にする）は、別のブランチで提案中である。`C:/Works/info-hive-dev/.claude/worktrees/wiki-py315/docs/adr/0026-wiki-uv-scripts-cap-python-at-tested-range.md` にある。

## 特に確かめてほしいこと

- トラックの選び方、止まる条件、URL の判定に、日常の動画で起きる穴がないか（たとえば、yt-dlp の `language` が欠ける、`-orig` のない自動字幕、地域の変種の言語コード、Shorts、限定公開）。
- raw のバイト列を同一性にする決め方と、取得の時刻を raw に書かないことが、F-I03 と F-I08、O-14 と矛盾しないか。
- json3 から本文への変換の規則で、決定的でない点や、Markdown として誤って解釈される点がないか。
- yt-dlp の版を固定する方針と、`CONTRIBUTING.md` の決まり、ADR-0018 と ADR-0026 との食い違い。
- 自動字幕の聞き違いへの対処（留保と、型付きのエッジを書かないこと）が、wiki の既存の決まり（グラフの証拠、引用）と整合するか。

yt-dlp の振る舞いについての主張は、手元の yt-dlp のソースか文書で確かめられるなら確かめ、確かめられなければ「推測」と書く。
