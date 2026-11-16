# レビューの目的（4 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

3 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-3.md`、採用可）のあと、作者の求め（2026-11-16）で次を変えた。

- 自動字幕の聞き違いを、raw でなく要約ページと関係するページの文で訂正する。訂正は `## 字幕の訂正` の表に 1 件ずつ、字幕の逐語、訂正した語、根拠の種類（`metadata`、`caption`、`wiki_source`、`model`）とともに残し、利用者に示す。
- 動画のソースの要約ページに `confidence`（`high`、`medium`、`low`）を足し、字幕の種類と訂正の率から、下げる方向だけの規則で決める。
- `wiki_youtube.py verify` で、表の字幕の語が raw にあることと、confidence の計算を照らす。
- `/wiki:query` の回答の確からしさ（ADR-0028、提案、別のブランチ）の上限に、動画のソースの `confidence` を足す必要があると書いた。

新しい節は「決定」の「字幕の訂正と confidence」で、「理由」「検討した選択肢」「影響」「見直す条件」にも書き足した。3 回目のあとに足した直し（`slug_taken` の範囲、`inspect` のハッシュを `write` で照らすこと、同時の取り込みの重複を受け入れたこと、`inspect` が json3 をメモリに取ること）は、まだレビューを受けていないので、これも対象にする。

特に次を崩せるかを探す。

- 訂正の記録と照合が、外れた訂正や、記録のない訂正が wiki に広がるのを防げるか。表に書かずに本文だけで直した語を、どう見つけるか。
- confidence の規則が、訂正の多いソースを確かに下げるか。規則の抜け道（根拠の種類の付け替え、訂正を留保に替える、行数の数え方）で、高く見せられるか。
- confidence と、要件定義書の検証状態（8 章、Q-02）、ADR-0028 の回答の確からしさ、グラフのエッジの `confidence` との関係に、矛盾や二重の意味がないか。
- raw を変えない決定（スクリプトだけが書く、json3 のハッシュで同一性を決める）と、新しい節が食い違わないか。

前の回と同じ指摘は、直っていなければそう書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`、`review-2.md`、`review-3.md`
- 関係する ADR: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- ADR-0028（別のブランチ、読むだけ）: `C:/Works/info-hive-dev/.claude/worktrees/query-confidence/docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の 8 章（Q-01〜Q-08 と検証状態）、F-I02、F-I03、F-I08、S-01、O-14
- 今の取り込みの手順と規約: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/references/graph-workflow.md`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）

重大の指摘には、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常の使い方で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを書き添える。確かめられない主張は「推測」と書く。
