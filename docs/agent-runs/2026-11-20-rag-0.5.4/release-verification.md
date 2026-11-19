# rag 0.5.4 のマージと公開の確認

2026年11月20日、[PR #13](https://github.com/to884/info-hive-rag/pull/13) を main にマージした。
コミットは `9af30c3d46fd1699638ea87c908c8d1bb313bae8` で、`v0.5.4` のタグと [GitHub リリース](https://github.com/to884/info-hive-rag/releases/tag/v0.5.4)を作成した。

Claude Code 2.1.325 の設定を隔離し、公開マーケットプレイス `to884/info-hive-marketplace` から `rag@info-hive` を新規導入した。
rag 0.5.4 と依存先 wiki 0.39.0 が有効になり、v0.5.3 から変更された全 6 ファイルのバイト列が v0.5.4 のタグと一致した。
プラグインの manifest の検査も成功した。
利用中の Claude Code の設定は変更せず、隔離用ディレクトリは検証後に削除した。

製品コードの SHA-256 は `021ea0774ec104f2b1b827498a6192bf64a68fc2d3dcb0d8d1d2373240aa7ab6` で、[キャッシュの検証](../../research/rag-cache-retirement-2026-11-20.md)と同じである。
Windows 回帰 84 件、Linux 82 件成功・2 件スキップ、実 MCP 21 項目の証跡を再利用した。
バージョンと変更履歴だけを更新し、製品のスクリプトは変更していない。

導入結果の詳細は `claude-marketplace.json` にある。
マージ後のリモートブランチと作業用ローカルブランチは削除した。
