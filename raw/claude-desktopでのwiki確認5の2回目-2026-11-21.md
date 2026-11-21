# Claude Desktop での wiki 確認 5 の 2 回目

2026-11-21、Windows 11 の Claude Desktop 6.6395.0.0 の Code タブで wiki 0.39.1 を使用した。練習フォルダーが空、e5 と ruri が未取得の状態から始めた。

- 初期化のグラフ層の質問には「後回し」が選択肢として表示された。初期化の出力に `"status": "ready"` があり、e5 のキャッシュは 252,425,348 バイト。標準版の `CLAUDE.md` を作成した。
- 味噌の取り込みで `wiki/sources/味噌.md`、`wiki/concepts/麹.md`、味噌の索引の行と 1 件のログを確認した。質問の答えには `[[味噌]]`、`[[麹]]` と `**確信度（confidence）: 高**` が表示された。
- 醤油の取り込み後に `wiki/sources/醤油.md`、索引の行と 2 件目のログを確認した。browse の JSON はループバックの URL と `"scope": "project"` を返した。Code のブラウザペインの Index に味噌と醤油の要約があり、麹のページに醤油の記述と 2 件の被リンクがあった。
- 構造点検は MCP の `mcp__plugin_wiki_wiki__lint` を使った。JSON は `total_pages: 3`、`orphans: 0`、`broken_links: 0`、`read_errors: 0`、`missing_frontmatter: 3` を示した。欠落は 3 ページの空の `tags` だった。修正の提案は見送った。

1 回目の構造点検は CLI を使い、同じタグの欠落を構造エラーとしては報告しなかった。2 回目では醤油の取り込み後に実行したグラフの補足ログの書き込みが、エージェントが差分を引数として渡したため一度失敗した。ハッシュだけを取り出して再実行し、補足ログが追加された。

証拠はホストの `C:\stage2-records\autotest` にある `05-run2-init.json`、`05-run2-w1.json`、`05-run2-w2.json`、`05-run2-checklist-verdict.json`、`05-run2-w1-query.jpg`、`05-run2-browse-index.jpg`、`05-run2-browse-koji-backlinks.jpg`。
