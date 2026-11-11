対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、ブランチ `feature/browse-stage1`、0.9.4 の上の 0.10.0）に足した、閲覧（browse）の第 1 段階の実装の全体である。中核、書き込みの守り、静的の書き出し、中核の子プロセスの入出力、サーバー（`serve` と `stop`）、`/wiki:browse` のコマンド、試験、CI を含む。

1 回目の実装のレビュー（`docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-review-1.md`、中核まで）の指摘は直した。対応は `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-responses.md` にある。直ったかも確かめる。

目的（対象が果たすべきこと）:
- 設計 `docs/plans/wiki-browse-stage1-2026-11-09.md` の全体を満たし、設計の「守ること」の 1〜9 を守る。とくに、サーバーの 8（要求の扱い、開いたときに描く、作り直し、「古い」状態、1 つの Wiki に 1 つのサーバー、`serve` と `stop` の流れ）。
- ADR-0010、ADR-0002 のうち ADR-0010 で置き換えていない行（127.0.0.1、起動ごとのトークン、Host の確認、閲覧専用）、ADR-0016（2 方式の合格の条件）、ADR-0001 の 3 条件に従う。
- 既存のスクリプトの振る舞いを変えない。

読むもの:
- 実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`browse_assets/`、`info-hive-wiki/commands/browse.md`
- 文書と版: `info-hive-wiki/CHANGELOG.md` の 0.10.0、`info-hive-wiki/docs/commands.md` の `/wiki:browse`、`info-hive-wiki/README.md`、`info-hive-wiki/skills/info-hive/SKILL.md`
- 試験: `tests/wiki/test_browse_fs.py`、`tests/wiki/test_browse.py`、`tests/wiki/test_browse_server.py`、`tests/wiki/browse/browse.test.mjs`、`tests/wiki/browse/startup.test.mjs`、`.github/workflows/wiki-browse.yml`
- 既存の関数: `wiki_pages.py`、`wiki_lint.py`、`wiki_graph_extract.py`、`wiki_graph_common.py`、`wiki_mcp_common.py`

手元（Windows 11、Python 3.12）で確かめたこと:
- `uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -B -m unittest tests/wiki/test_browse_fs.py tests/wiki/test_browse.py tests/wiki/test_browse_server.py` が通る（Linux と POSIX だけの 4 件を飛ばす）。
- `tests/wiki/browse/browse.test.mjs` を Chromium、Firefox、WebKit、Edge で、静的版とサーバーの 2 方式で流し、失敗が 0 件だった。
- `startup.test.mjs` は 1,000 ページで中央値 3.45 秒だった。
- Linux では、まだ流していない（CI で流す）。

とくに崩してほしい点:
1. サーバーの安全（守ること 7）: Host、トークン、パスの確かめの穴、中核が知らない名前やファイルシステムへの到達、エラーの応答への絶対パスやトークンの混入、操作の口への閲覧のトークンでの到達。
2. サーバーの作り直しと「古い」状態（守ること 3、8、9）: 要求ごとの写しの固定、組み立ての重なり、待ちの上限、失敗と復帰、読み取りの失敗からの読み直し、`shutdown_requested` の扱い。
3. `serve` と `stop` の競合（守ること 7、8）: 2 つの `serve`、`stop` の後片付けとの競合、別のインスタンスを止める経路、記録の削除、操作がないときの終了。
4. 閲覧専用（守ること 1）: サーバーの状態の書き込みが守りを通らない経路、Wiki の中のファイルを作る経路。
5. 1 回目の指摘の直しが不十分なところ、直しで新しく生じた欠陥。
6. 試験が、主張していることを本当に確かめているか。CI のワークフローが、主張する試験を本当に流すか（Linux と Windows で）。
