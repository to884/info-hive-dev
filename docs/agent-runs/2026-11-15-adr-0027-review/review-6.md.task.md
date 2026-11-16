# レビューの目的（6 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

5 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-5.md`、却下、重大 3）の指摘を、次のように構造から直した。「決定」の「字幕の訂正と confidence」の節を中心に、「理由」「検討した選択肢」「影響」も書き直した。

- 別の表をやめ、訂正と留保を、それを使う文の中の印（`訂正した語〔字幕 12:34「字幕の語」 根拠 種類:場所〕`、`「字幕の語」〔字幕 12:34 訂正なし〕`）で残す。印を作るのは、その raw を `raw` に持つ要約ページだけで、関係するページは要約ページの印を指す短い印を添える（5 回目の 1）。
- 1 件は、時刻と字幕の語の組（字幕の 1 つの出現）である。出現ごとに別の印なので、同じ字幕の語を時刻ごとに別の語へ訂正できる（5 回目の 2）。
- confidence を、raw とその要約ページの印から、いつでも同じ計算で決まる値にし、印が変われば計算し直す。数え直す場面を限る規則をなくした（5 回目の 3）。
- 計算は標準ライブラリだけの共通のモジュールに置き、`verify` と lint が使う。

5 回目までに崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。特に、印の形（読み取りの曖昧さ、Markdown や引用との衝突、関係するページの短い印）、confidence が印から決まることの抜け道、ADR-0028 との関係を探す。前の回と同じ指摘は、直っていなければそう書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`〜`review-5.md`
- 関係する ADR: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- ADR-0028（別のブランチ、読むだけ）: `C:/Works/info-hive-dev/.claude/worktrees/query-confidence/docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の 8 章（Q-01〜Q-08 と検証状態）、F-I02、F-I03、F-I08、S-01、O-14
- 今の取り込みの手順と規約: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/references/graph-workflow.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）

重大の指摘には、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常の使い方で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを書き添える。確かめられない主張は「推測」と書く。
