前のレビュー（merge-review.md）の重大な指摘 1〜3 と、短文・0 件・警告時の順序の指摘を受け、設計と実装を修正しました。未コミットの最終ファイルを再レビューしてください。PR の古い head ではなく、この worktree の内容が対象です。

変更は文字数の比率と推定した名前の除去をやめ、外国語の文や節の残存を調べる方式です。名前と区別が付かない句は、具体的な保持の理由が必要な警告にします。中国語の文ごとの残存や近似コピー、短い説明、各語が大文字の文章も検査します。検査対象の文章がなければ no_prose/checked_blocks: 0、あれば checked/1 以上と区別します。意味の正しい訳や、すべての言語の判別を保証する設計ではありません。

警告を受理する側は、W9 より前に prepare のログを残し、--finish --accept-warnings --json の completed: true と翻訳の状態を確認する手順にしました。取り込みの完了記録を先に書きません。

設計: docs/plans/wiki-ingest-translation-completion-2026-11-17.md
実装: info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py
手順: info-hive-wiki/skills/info-hive/references/web-raw.md、commands/ingest.md、agents/web-raw.md、skills/info-hive/SKILL.md、references/codex.md、references/ingest-workflow.md
回帰試験: tests/wiki/test_wiki_web_check.py の TranslationCompletionTest（23 メソッド）、tests/wiki/check_web_raw_agent.py の verified_completion、tests/wiki/test_web_raw_agent.py

前の反例が修正されたか、名前の誤検出を場当たり的な除外で逃がしていないか、部分的な訳や日本語の付け足しで現実的な未翻訳が通らないか、完了の状態と手順に矛盾がないかを確認してください。設計と実装の両方について最終判定をお願いします。

ファイルを編集せず、別エージェントを起動せず、再現用の作業は一時ディレクトリで行ってください。新しい欠陥は根拠と反例を添え、確認できない推測とは区別してください。
