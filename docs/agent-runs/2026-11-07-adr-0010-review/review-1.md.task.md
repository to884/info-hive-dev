ADR-0010（`/wiki:browse` の中核と表示の方式の分離）の改訂案と、その判断材料のレポート、PoC の試作をレビューしてほしい。

目的: 作者（ユーザー）が、ADR-0010 の未決の 7 件を決めて ADR を承認できる状態にすること。各未決の「推す案」は提案であり、ユーザーが決める。レビューでは、推す案の根拠が事実と食い違っていないか、PoC の結果が主張を支えているか（測り方の欠陥、過大な一般化）、見落とした選択肢や影響がないかを探してほしい。

読むもの:
- 改訂案: `docs/adr/0010-wiki-browse-separates-core-from-delivery.md`（`git diff ec0b407 -- docs/adr/` で最初の版との差分が見られる）
- レポート: `docs/research/wiki-browse-adr-0010-poc-2026-11-07.md` と、同名のフォルダーの測定の JSON
- 試作: `poc/browse/`（`gen.py`、`serve.py`、`test.mjs`、`static-test/probe.js`、`static-test/kinsoku.html`、`mcp_origin_probe.py`、`app/src/main.rs`、`app/src/driver.js`）
- 関連する決定: `docs/adr/0001-*.md`、`0002-*.md`、`0007-*.md`、`0012-*.md`、`0013-*.md`、`docs/research/wiki-mcp-server-2026-11-06.md`
- コードの事実: サブモジュールの `info-hive-wiki` は wiki 0.6.0（36a4089）、`info-hive-rag` は rag 0.4.0（6a760b9）。この worktree ではサブモジュールが空なので、`C:\Works\info-hive-dev\info-hive-wiki` と `C:\Works\info-hive-dev\info-hive-rag` で `git show 36a4089:<path>`、`git show 6a760b9:<path>` を使って読む（作業ツリーは別のセッションが変えているかもしれないので、作業ツリーのファイルではなくコミットを読む）。

特に崩してほしい主張:
1. 未決 1：lint と search のページ集合の違いの記述と、lint を正とする案の影響（MCP の `query` の索引にも効く）
2. 未決 2：書き出し先を ADR-0012 と同じ data の領域にする案
3. 未決 3：`export_name()` の規則（200 バイト、接尾辞、大文字と小文字の衝突）が、ページを足しても URL を変えないという主張
4. 未決 4：ブラウザのページは MCP サーバーに接続できない、アダプタを MCP のクライアントにする案（D'）が ADR-0001、ADR-0012 と矛盾しないこと、ADR-0007 の見直しが要らないという主張
5. 未決 7：`raw:` の絶対パスの表示の案と、ブラウザの `file:///` のリンクの実測
6. PoC の 5 項目の結論（とくに「12 通りの結果が一致した」「禁則の違反 0 件」が何を示し、何を示さないか）

レビュアーは読み取り専用で動く。ファイルを書き換えない。
