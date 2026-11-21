# Claude Desktop での wiki 確認 5 の 1 回目

2026-11-21、新しい Windows 11 Enterprise 評価版 26H2 の VM で、Claude Desktop 6.6395.0.0 の Code タブと wiki 0.39.1 を使用した。開始前の練習用フォルダーは空で、uv キャッシュは 441,267,870 バイト、e5 と ruri のモデルキャッシュはなかった。

- `/wiki:init` は選択式の質問を順に表示した。プロジェクトの既定の配置とモデルキャッシュを選び、グラフ層を後回しにし、標準の `CLAUDE.md` を承認した。ツール出力は `status: ready`。e5 キャッシュは 252,425,348 バイトになった。
- 付録の `raw/味噌.md` を取り込むと、味噌と麹のページができ、一覧に味噌が加わり、ログの取り込みは 1 件だった。「味噌の原料は？」の回答には `[[味噌]]`、`[[麹]]`、`**確信度（confidence）: 高**` があった。エージェントは索引とページを読み、MCP の `query` と `wiki:wiki-reader` は呼ばなかった。保存した表示からはフックの通知を確認できなかった。
- 同じセッションで `raw/醤油.md` の差分を承認すると、醤油のページと索引の行が増え、取り込みログは 2 件になった。browse の JSON は `http://127.0.0.1:` で始まる URL と `scope: project` を返した。Code のブラウザペインで、Index の味噌と醤油、麹のページの両方の被リンクを確認した。
- `/wiki:lint` は CLI の `wiki_lint.py` を呼び、3 ページを調べた。孤立ページ、リンク切れ、読み込みエラーは報告されなかった。

証拠はホストの `C:\stage2-records\autotest` の `05-s1b-checkpoint.json`、`05-run1-w1.json`、`05-run1-w2.json`、W1・W2 の判定 JSON、`05-run1-w1-query.jpg`、`05-run1-browse-index.jpg`、`05-run1-browse-koji-backlinks.jpg` にある。今回の記録の範囲は 3 回の試行のうち 1 回。
