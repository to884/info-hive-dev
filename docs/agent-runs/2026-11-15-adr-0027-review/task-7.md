# レビューの目的（7 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

6 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-6.md`、却下、重大 3）の指摘を、次のように構造から直した。

- raw の字幕の行に、スクリプトが通し番号を振る（`L<番号> [時刻] 本文`）。聞き違いの疑いの 1 件を `L123-1` の識別子で指し、時刻と語の字面に頼らない（6 回目の 1）。
- 文の中の印は識別子だけを持つ（`〔訂正 L123-1〕`、`〔留保 L123-1〕`）。字幕の語、訂正した語、根拠は、そのページの `## 字幕の訂正と留保` の節の箇条書きの定義に、コードスパンで書く。訂正した語の境目は、定義の訂正した語が印の直前の本文の末尾と同じであることで確かめる（6 回目の 2 と軽微な指摘）。
- 関係するページの印も、要約ページと識別子を持つ（`〔訂正 [[要約ページ]] L123-1〕`）（6 回目の 3）。
- 引用の位置も、行の番号と時刻で書く。

6 回目までに崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。特に、識別子と定義の形（一意性、番号の振り方、定義と印の対応、コードスパンの読み方、印の直前の末尾との照らし方）に抜け道や曖昧さがないかを探す。前の回と同じ指摘は、直っていなければそう書く。

なお、この ADR は 4 回目から 3 回続けて却下で、重大の多くは直しで足した仕組み（記録の形）から出ている。新しい指摘が、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを、いつもより丁寧に分けて書いてほしい。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`〜`review-6.md`
- 関係する ADR: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- ADR-0028（別のブランチ、読むだけ）: `C:/Works/info-hive-dev/.claude/worktrees/query-confidence/docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の 8 章、F-I02、F-I03、F-I08、S-01、O-14
- 今の取り込みの手順と規約: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/references/graph-workflow.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）

確かめられない主張は「推測」と書く。
