# browse の概要表示の設計：Astra の敵対的レビュー

作業先は `C:/Works/info-hive-dev/.claude/worktrees/wiki-overview`。各コマンドで明示する。
ユーザーは、段階1をコミットで区切り、段階2の表示設計を作り Astra でレビューする進め方を承認した。

段階1のコミットは、親 `17b381c`、プラグイン `03446f6`。
対象は新規 `docs/plans/wiki-browse-overview-2026-11-17.md`（第1版、全文）。
保存の基礎は `docs/plans/wiki-overview-2026-11-17.md` 第6版と `docs/adr/0031-wiki-page-overview-lives-in-a-sidecar.md`。

既存実装の正本は `info-hive-wiki/skills/info-hive/scripts/` の `wiki_overview.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_browse.py`、`browse_assets/figures.js`、`browse_assets/style.css`。
必要な部分だけ実装へ照合し、設計の反例を探す。

重点は次のとおり。

1. 走査を共通化する境界、一覧不明と1件の読み取り失敗、入力の署名と世代、読み取り回復、status/lint の既存の意味を維持できるか。
2. 同じ Snapshot の全 page 入力からの結び付け、読めないページと NFC/P の衝突、状態の優先順。Core で I/O を行わないこと。
3. h1 の直後への差し込み、元の見出しと検索の不変、閉じた概要の SVG/Mermaid、両方式の整合。
4. SVG の出力の表と内容による URL、HTTP と静的出力、CSP と DOM、公開前の情報の検査。
5. format 2 の本文検査を共有する提案が、既存の規約との互換性と、描画の失敗の扱いを保てるか。

ファイルを変更しない。別エージェントや LLM に再委譲しない。全試験や公開は不要。
必要なら LLM を使わない小さな反例だけを実行する。未実装の部分を実装済みと見なさない。
致命的・重大・軽微を区別し、欠陥が現れる入力と根拠を示す。単なる好みと、作者が明示して承認する判断点は欠陥に数えない。
日本語で、採用可・条件付き採用可・却下と確信度、指摘、検証した事実、崩せなかった点を報告する。
