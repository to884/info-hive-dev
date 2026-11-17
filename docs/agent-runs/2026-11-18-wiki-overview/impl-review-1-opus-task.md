# 概要の段階2の実装：敵対的レビュー

作業先は `C:/Works/info-hive-dev/.claude/worktrees/wiki-overview`。プラグインはその下の `info-hive-wiki` という独立した Git リポジトリ。
作者は表示設計第3版での実装継続を指示した。更新された AGENTS.md に従い、Codex から ask-claude で Opus の実装レビューを依頼する。

## 正本と差分

- 設計：`docs/plans/wiki-browse-overview-2026-11-17.md`。第3版、承認・実装中。保存設計は `docs/plans/wiki-overview-2026-11-17.md` と ADR-0033。
- 保存の ADR は承認時には0031だったが、main の Codex 対応との番号の衝突を解消し、内容を保って0033に移した。
- 親 HEAD `73bc9c7`、プラグイン HEAD `022013c`。main の 0.31.1 を取り込み、段階1を保った統合後の、未コミットの差分が段階2である。
- プラグインの `git diff HEAD` を読む。元のページの読み取りは最新 main の `article_path` にも合わせている。

主な実装は `skills/info-hive/scripts/wiki_overview.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_browse.py`、`browse_assets/style.css`。
文書は README、commands/browse.md、commands/overview.md、docs/commands.md、SKILL.md、SCHEMA.md.template、references/codex.md、CHANGELOG。
親の新しい試験は `tests/wiki/test_browse_overview.py` と `tests/wiki/browse/overview.test.mjs`。
`tests/wiki/browse_read_sweep.py` は、概要だけの一覧の失敗を、記事の名前の集合の失敗と区別するようにした。記事側の失敗の判定は維持している。

## 重点

1. 同じ Snapshot の全 page 入力と副作用のない view による状態判定。ページの不在・読めない・NFC/P の衝突、不完全な走査、壊れた本文の優先順。
2. 保存済み本文の正確な抽出。ヘッダー後の1 LFと本文後の2 LFだけを外し、先頭の空白・字下げ・末尾改行・64 KiB境界を保つ。下書きと保存済みの本文構造検査を共用する。
3. h1 直後への配置、見出し ID・検索・リンク・ページ数の不変。描画失敗を概要へ局所化し、再試行できるか。
4. SVG の内容で決まる名前、同じ SVG の共有、衝突を全関係ページで拒否すること。SVG を DOM へ入れない、HTTP で専用 CSP、静的の世代にも全図を入れること。
5. 概要だけの追加・変更・削除、一覧不明、観測した読み取り失敗からの回復、キャッシュ。署名不変の権限喪失は明記された保証外である。
6. 閉じた概要の図と配色、ネイティブの開閉、CSP、記事のリンクを読まない main の規則との統合。

## 検証と範囲

関連 Python 試験410件は失敗0（8件skip）。最新の表示・HTTP試験は別実行で20件を確認中。
プラグイン内の既存試験116件は失敗0（4件skip）、encoding の検査63ファイルも成功。
5つのブラウザ×2方式×2配色の20ケースは、図・配色・CSP・外部通信・開閉・320pxで成功。Tab操作を追加して再確認中。
ブラウザ結果と画面はこのディレクトリに置く。GUI の確認を試験コードの静的な読み取りだけで実測済みとは言わない。

まだ版の番号を上げず、push・PR・リリースは行っていない。
ファイルの変更、他のモデル・エージェントへの委譲、全試験、公開は不要。必要な反例は一時 wiki を使う狭いものだけとする。
レビュー作業を、リポジトリ開発の完了として扱って worktree とブランチを削除しない。
日本語で、致命的・重大・軽微の欠陥、具体的な反例と根拠、実測と推論を区別し、判定と確信度を報告する。
