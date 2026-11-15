対象は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、プラグインのエージェント `wiki:web-raw`（`agents/web-raw.md`、`model: sonnet`、`omitClaudeMd: true`）に任せる変更の、設計の 3 版と実装の 2 回目である。3 回目のレビュー（review-3.md、却下）の指摘は root-causes-3.md で分類して直した（呼び直しで language_override を依頼に写す、実地の確かめのスクリプトの穴を塞ぐ）。後段（W9 と取り込みの手順 3〜8）は、呼び出す側のモデルが行う。

経緯: 設計の 1 版と 2 版は却下された（docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/design-review-1.md、design-review-2.md）。分類は design-root-causes-1.md と design-root-causes-2.md にある。3 版では、2 版で足した仕組み（メインの check のやり直し、--finish を log のあとに移すこと、汎用の差分の合成、報告のモデルによる作者の記録）を削って 0.14.0 の W8 に戻し、主張を狭めた。実装（info-hive-wiki の差分は docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/impl-2.submodule.diff）を、英語と日本語のページで実際に動かし、セッションの記録から分担を確かめた（docs/research/wiki-web-raw-agent-trial-2026-11-14.md、14 項目とも通過）。

この変更の範囲の外として扱うもの（指摘してよいが、この変更の欠陥としては数えない）:
- 0.14.0 の main からある問題: `--html-file` で取得した取り込みを途中でやめ、URL だけで取り直すと、wiki_fetch.py が作業用の写しを見る前に終了コード 3 で止まる（再現済み）。取り込みの途中の条件や理由が、会話の外に残らない。ほかのセッションとの同じスラッグの同時の取り込み。
- 設計の「言えないこと」に書いたもの: どのモデルが文を考えたかの証明、モデルの名前の自己申告の正しさ、呼び出す側が手順に従わないことを仕組みで止めること、許可リストやフォールバックの連鎖でのモデルの変化。

見てほしい点:
- 3 版の設計と実装が、設計に書いた「言えること」を本当に満たすか。満たさない入力や経路。
- 実装（agents/web-raw.md、skills/info-hive/references/web-raw.md、commands/ingest.md、SKILL.md と ingest-workflow.md の変更）と、設計の食い違い。参照文書の手順の矛盾、抜け、読み違えやすいところ（とくに、呼び出す側の手順の status ごとの扱い、needs_user の表、warnings の流れ、エージェントがないときの代わり）。
- エージェントの本文と omitClaudeMd、tools の選び方で起きる問題。
- 試験（tests/wiki/test_web_raw_agent.py、tests/wiki/check_web_raw_agent.py）が、確かめていると言いながら確かめていないこと。実地の確かめの判定の誤り（偽陽性と偽陰性）。
- 0.15.0 の版と CHANGELOG の書き方。

読むもの: docs/plans/wiki-web-raw-agent-2026-11-14.md、docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/（design-review-1.md、design-review-2.md、design-root-causes-1.md、design-root-causes-2.md、review-3.md、root-causes-3.md、impl-2.submodule.diff、trial-cqrs.json、trial-bloom.json）、docs/research/wiki-web-raw-agent-probe-2026-11-14.md、docs/research/wiki-web-raw-agent-trial-2026-11-14.md、info-hive-wiki/agents/web-raw.md、info-hive-wiki/skills/info-hive/references/web-raw.md、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/SKILL.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、tests/wiki/test_web_raw_agent.py、tests/wiki/check_web_raw_agent.py、info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py と wiki_fetch.py。

試験は `python -X utf8 -m unittest tests/wiki/test_web_raw_agent.py` で流せる（標準ライブラリだけ）。
