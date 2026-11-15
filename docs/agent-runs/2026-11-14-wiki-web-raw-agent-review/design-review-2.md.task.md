対象は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、プラグインの Sonnet のサブエージェント（`agents/web-raw.md`、`model: sonnet`、`omitClaudeMd: true`）に任せる設計の 2 版である（docs/plans/wiki-web-raw-agent-2026-11-14.md）。後段（W9 と取り込みの手順 3〜8）は、メインの会話のモデルが行う。まだ実装していない。

1 版は却下された（docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/design-review-1.md）。指摘は原因の構造で分けて直した（同じフォルダーの design-root-causes-1.md）。要点: 取り込みの状態（依頼）をメインが持ち、呼び直すたびに全体を渡す。エージェントのモデルと完了を、報告ではなくメインが確かめる（モデルの ID と、メインが自分で実行する check の出力）。作業用の写しを消す check --finish を、log を書いたあとのメインの段に移す。条件を依頼の conditions で渡し、エージェントは SCHEMA.md を読み、omitClaudeMd でユーザーの指示を受け取らない。実地の確かめで、誰が何をしたかをセッションの記録から調べる。設計の前提の一部は、試しのプラグインで確かめた（docs/research/wiki-web-raw-agent-probe-2026-11-14.md）。

見てほしい点:
- design-review-1.md の指摘が、2 版で本当に起きなくなったか。design-root-causes-1.md の主張を崩せるか。
- 2 版が新しく持ち込んだ欠陥。とくに、check --finish を log の段に移したことの影響（今の wiki_rawcheck.py と wiki_fetch.py の動き、途中でやめたとき、再開、W9 から log までの間）、依頼の changes の合成、メインが check で完了を確かめる手順、omitClaudeMd で失うもの。
- モデルが Sonnet 以外になる経路と、メインが raw の段を自分で行ってしまう経路が、まだ残っていないか。
- 報告と依頼の形の網羅と、誤読。
- 試験の計画が、目的（raw の段だけを Sonnet にし、後段はメインのモデル）を偽陽性なく確かめられるか。

読むもの: docs/plans/wiki-web-raw-agent-2026-11-14.md、docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/design-review-1.md と design-root-causes-1.md、docs/research/wiki-web-raw-agent-probe-2026-11-14.md、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/SKILL.md、info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py と wiki_fetch.py。
