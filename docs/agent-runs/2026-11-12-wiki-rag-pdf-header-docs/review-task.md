対象は info-hive-wiki（Claude Code プラグイン wiki）の 1 コミット（origin/main..HEAD）。

目的: wiki の PDF 取り込み手順（skills/info-hive/references/ingest-workflow.md）が、rag プラグインの受け付ける PDF の条件を正しく案内すること。
rag 0.5.1（to884/info-hive-rag#7、未マージ）は、`read_pdf`（info-hive-rag/scripts/rag_index.py）で、`%PDF-` が先頭から 1024 バイト目までに始まれば PDF として受け付けるように変わった（今までは先頭がちょうど `%PDF-` のときだけ）。rag 側の差分は `gh pr diff 7 --repo to884/info-hive-rag` で読める。

確かめてほしいこと:
- 直した文が rag 0.5.1 の実際の条件（境界の 1024 バイト、どの段階で拒むか、拡張子・通常のファイル・UNC・派生データの条件）と食い違っていないか。
- info-hive-wiki の中に、古い条件（先頭が %PDF-）を前提にした記述がほかに残っていないか（README、docs、commands、SKILL.md、テンプレート、試験の期待値など）。
- バージョン（0.10.x → 0.11.0 は公開済み、今回 0.11.1 の PATCH）と CHANGELOG の書き方が、AGENTS.md のリリースの節と既存の CHANGELOG の慣例に合っているか。
- rag 0.5.0 以前と wiki 0.11.1 を組み合わせたときに、案内が利用者を誤らせないか。
