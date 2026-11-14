対象は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、プラグインの Sonnet のサブエージェント（`agents/web-raw.md`、`model: sonnet`）に任せる設計である（docs/plans/wiki-web-raw-agent-2026-11-14.md）。後段（W9 と取り込みの手順 3〜8）は、メインの会話のモデルが行う。まだ実装していない。

今の手順は info-hive-wiki/commands/ingest.md（Web の節が W1〜W9）と info-hive-wiki/skills/info-hive/references/ingest-workflow.md（「Web ページ」の節）、スキルの概要は info-hive-wiki/skills/info-hive/SKILL.md にある。raw の書き換えの検査は wiki_rawcheck.py（freeze と check）、取得は wiki_fetch.py が行う（この設計では変えない）。Claude Code のサブエージェントの仕様は、設計の「前提」の表に、公式の文書の URL とともにまとめた。

見てほしい点:
- 設計の目的（raw の段だけを Sonnet にし、後段はユーザーのモデルにする）が、この形で本当に達せられるか。モデルが Sonnet 以外になる経路、メインのモデルが raw の段を自分で行ってしまう経路。
- メインとエージェントの分担の境目で、今の手順から抜け落ちる判断、ユーザーとのやり取り、状態（作業用の写し、`--finish`、`--accept-warnings` と log.md、途中からの再開、`work_stage`）。エージェントがユーザーに聞けないことが、今の手順のどこで問題になるか。
- 報告の JSON の形と `status`、`question.kind` の網羅。メインが報告を誤読するとき、エージェントが形を守らないとき。
- 手順を参照文書 1 か所に移すことと、エージェントを呼べないときにメインが代わりに行う作り。プラグインの外のスキル、入れ子の上限、Codex などほかのエージェントで使う場合。
- 表示名（translated_by）の決め方。
- 前提の表の仕様の読み違い。試験の計画が、目的を確かめられるか（とくに実地の確かめ）。
- 費用、時間、並列の呼び出しで起きる問題。

読むもの: docs/plans/wiki-web-raw-agent-2026-11-14.md、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/SKILL.md、info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py と wiki_fetch.py（終了コードと出力のキー）、docs/research/wiki-ingest-model-comparison-2026-11-13.md、AGENTS.md。
