# レビューの目的（8 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

7 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-7.md`、却下、重大 1）の指摘を、次のように直した。対象は「決定」の「字幕の訂正と confidence」の節である。

- 照合を、訂正と留保で分けた。留保の定義には訂正した語も根拠もないので、(2) は訂正の定義にだけ当てる。(4) は、印の種類が定義と同じで、印の直前の本文の末尾が、訂正なら訂正した語、留保なら字幕の語と同じであることを求める。関係するページの印も同じにした（7 回目の重大 1）。
- 印の直前の語には書式を付けない（コードスパン、強調、wikilink で囲んだ語の直後には印を置けない）とした（7 回目の軽微 1）。
- コードスパンの語の先頭か末尾がバッククォートか空白なら、内側の前後に空白を 1 つずつ足し、CommonMark のとおり外して読むとした（7 回目の軽微 2）。
- 同じ行の同じ位置を 2 つの識別子が指すことを、(3) で誤りにした（7 回目の軽微 3）。

7 回目までに崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。前の回と同じ指摘は、直っていなければそう書く。新しい指摘には、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを丁寧に分けて書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`〜`review-7.md`
- 関係する ADR: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- ADR-0028（別のブランチ、読むだけ）: `C:/Works/info-hive-dev/.claude/worktrees/query-confidence/docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の 8 章、F-I02、F-I03、F-I08、S-01、O-14
- 今の取り込みの手順と規約: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/references/graph-workflow.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）

確かめられない主張は「推測」と書く。
