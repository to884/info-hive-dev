# Claude Desktop Code の Wiki ハウツーの確認

2026-11-21、Claude Desktop 6.6395.0.0、Wiki 0.39.1。確認 5 の 3 回目から作った `S2-wiki-0.39.1` に戻し、ハウツーごとに新しい Code セッションを使った。

- 起動診断。`%LOCALAPPDATA%\info-hive\logs\server.log` を確認した。確認 3 の `--ensure` は終了コード 0、32.78 秒。`10-C3.txt`。
- ユーザー wiki。`/wiki:init --user` で `%USERPROFILE%\info-hive\wiki` と `raw` を作成した。標準案の承認後、グローバルな `%USERPROFILE%\.claude\CLAUDE.md` が新規作成された。ユーザー wiki の `SCHEMA.md` にある検索例には `--wiki wiki/` が残っていた。`10-W3.txt`。
- Web。IANA の `https://www.iana.org/help/example-domains` をプロジェクト wiki に取り込んだ。`wiki:web-raw` の原題併記の警告 3 件をログに記録後、親エージェントの検査は `ok: true` と `completed: true`。コマンド出力が 1,800 バイトに切り詰められ `work_dir_removed` は見えなかったが、実際の作業用ディレクトリは見つからなかった。`10-W4.txt`。
- アップグレード。`/wiki:upgrade` は `ready`、e5 は 4 ページの 25 セクションを埋め込み済み。`SCHEMA.md` は最新版で前後の SHA-256 が一致した。`10-W5.txt`。
- プラグイン更新。ディレクトリの「Code」で `info-hive` のアップデート確認後、「マーケットプレイスを更新しました。」。設定の Wiki の更新確認は「前回のリリース以降、変更はありません。」。導入済みの版は 0.39.1。`10-C4.txt`。
