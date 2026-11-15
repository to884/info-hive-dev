# 対象が果たすべき目的

閲覧（`/wiki:browse`）の画面を、製品の Chrome と Edge のサーバーの方式で開いたとき、ページを開くたびに `/favicon.ico` の 404 が出て、コンソールにエラーが出ていた。0.19.3 の直しは、閲覧のページ（`wiki_browse_core.py` の `_head`）と、サーバーの「見つからない」のページ（`wiki_browse.py`）の `<head>` に `<link rel="icon" href="data:,">` を足す。

守るべき約束:

- 閲覧の画面の CSP は `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'` のまま変えない。HTTP のヘッダーと `<meta>` の両方で出す。
- 外への通信は 0 件、`[style]` は 0 件、インラインのスクリプトはない。
- 静的の書き出し（`file://`）とサーバー（`http://127.0.0.1`）の 2 方式で、同じ画面になる。
- 製品の Chrome と Edge で、閲覧のサーバーのどの画面を開いても、`/favicon.ico` の 404 でコンソールにエラーが出ない。

確かめたこと: 直す前に、製品の Chrome と Edge で `/favicon.ico` の 404 がコンソールに出ることを Playwright で確かめた（記録は開発リポジトリの `docs/agent-runs/2026-11-15-wiki-browse-cross-browser/README.md`）。

見てほしいこと: この直しが目的を果たすか。宣言のない HTML や、HTML 以外の応答（503 のテキストなど）で要求が残らないか。`data:,` が CSP、ブラウザごとの扱い、静的の方式で問題を起こさないか。試験（開発リポジトリの `tests/wiki/test_browse.py` と `tests/wiki/test_browse_server.py` の差分）が退行を捕まえるか。

開発リポジトリのルートは `C:/Works/info-hive-dev/.claude/worktrees/browse-fluent2`、プラグインは その下の `info-hive-wiki` である。
