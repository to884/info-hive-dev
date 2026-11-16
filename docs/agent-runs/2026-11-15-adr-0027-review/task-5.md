# レビューの目的（5 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

4 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-4.md`、却下、重大 4）の指摘を、次のように構造から直した。「決定」の「字幕の訂正と confidence」の節を中心に、「理由」「検討した選択肢」「影響」も書き直した。

- 疑いの表を、要約ページごとでなく raw ごとに 1 つにし、親の要約ページ（スラッグが raw のファイル名と同じページ）にだけ置く。confidence も親の要約ページにだけ書く（4 回目の 2）。
- 訂正できない語と、利用者が退けた訂正を、`none`（重み 3）として同じ表に残す。退けても疑いは消えない。行を消すのは、利用者が字幕の語のほうが正しいと判断したときだけ（4 回目の 3）。
- confidence の出発点を raw の `caption_kind` から決める。ADR-0028 の上限は、動画の raw とそれに頼るページの前提に効き、親の要約ページがなければ出発点を使う（4 回目の 4）。
- 書き漏らした訂正は、confidence を出発点より上げない。`verify` が、用意したページの本文から raw にない数字、英字、カタカナの並びを「raw にない語」として挙げ、利用者に示す。保証ではないと書いた（4 回目の 1）。
- `metadata`、`caption`、`wiki_source` は、訂正した語がその場所に逐語であるときだけ使え、`verify` が照らす。1 件は字幕の中の 1 回の出現とした（4 回目の軽微な指摘）。

4 回目までに崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。特に、新しい構造（raw ごとの表、`none` の重み、出発点、目印）に抜け道がないかを探す。前の回と同じ指摘は、直っていなければそう書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`〜`review-4.md`
- 関係する ADR: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- ADR-0028（別のブランチ、読むだけ）: `C:/Works/info-hive-dev/.claude/worktrees/query-confidence/docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の 8 章（Q-01〜Q-08 と検証状態）、F-I02、F-I03、F-I08、S-01、O-14
- 今の取り込みの手順と規約: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/references/graph-workflow.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）

重大の指摘には、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常の使い方で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを書き添える。確かめられない主張は「推測」と書く。
