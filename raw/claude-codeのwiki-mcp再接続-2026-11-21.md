# Claude Desktop の Code での wiki MCP 再接続

2026-11-21、Windows 11 検証 VM の Claude Desktop 6.6395.0.0、wiki 0.39.1 で確認表の確認 7 を実行した。`S2-wiki-0.39.1` を復元して練習セッションを開いた。

1. Code で `/mcp` を実行すると「MCP サーバー」が開き、`wiki` の状態にチェックが付いていた。
2. `wiki` の行を開くと「接続済み・7 個のツール」と「再接続」が表示された。「再接続」を押すと、再接続中の表示のあと「wiki が接続されました。」と通知された。
3. Code で `/mcp reconnect all` を送ると、`Reconnect, enable, and disable aren't available in this session.` と表示された。

画像は `C:\stage2-records\autotest\07-mcp-connected.jpg`、`07-mcp-wiki-details.jpg`、`07-mcp-reconnected.jpg`、`07-mcp-reconnect-all.jpg`。
