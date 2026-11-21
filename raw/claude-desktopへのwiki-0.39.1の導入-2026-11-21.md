# Claude Desktop の Code タブでの wiki 0.39.1 導入

2026-11-20〜21（日本時間）に、新しい Hyper-V VM の Windows 11 Enterprise 評価版 26H2 と Claude Desktop MSIX 5.11492.5.0 で確認した。ローカルユーザーには Git 2.56.0.windows.4、uv 0.13.9、Python 3.12.10、Visual C++ ランタイム 14.52.37029.0 を導入済みだった。

## マーケットプレイスと Wiki

コードの「カスタマイズ → プラグイン → 追加 → マーケットプレイスを追加 → リポジトリから追加」から `to884/info-hive-marketplace` を選び、同期した。ディレクトリで「プラグイン → Code → info-hive」を開き、Wiki の「+」を押した。ローカル MCP サーバー `wiki` の警告で「続ける」を押すと「ローカルにインストール済み」が表示された。個別の `userConfig` 画面は見なかった。

ローカルの `.ssh` ディレクトリと `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` のユーザー設定はなかった。SSH の確認はホスト鍵の厳密な検査で終了コード 255 だった。この出力だけで GitHub の利用者認証まで到達したとは言えない。Claude にリポジトリの候補が表示されたため、Claude のクラウド側の GitHub 連携が使われたかは判定対象外とした。

記録は `02-before-marketplace.txt`、`02-install-plugin.txt`、`02-local-mcp-dialog.jpg`、`02-wiki-local-install.jpg`。

## MCP の準備とチェックポイント

実際にユーザースコープに入った wiki 0.39.1 を指定した `wiki_mcp_launch.py --ensure` は 32.78 秒で終了コード 0。uv キャッシュは 441,267,870 バイトで、e5 と ruri のモデルキャッシュは存在しなかった。Claude Desktop をトレイから終了してプロセスの停止を確認し、`S1-wiki-0.39.1` を保存した。

記録は `03-deps-gui.txt` と `03-s1-checkpoint.json`。

## Code タブのヘルプ

再起動後、確認専用フォルダーの Claude Code タブから `/wiki:help` を送信した。「Showed wiki command list」を展開すると、Bash が `python .../wiki_help.py` を実行したコマンドと出力を読めた。返答とツール出力の両方に `/wiki:overview` を含む 12 本があった。

記録は `04-help-code.json` と `04-help-code-tool.jpg`。
