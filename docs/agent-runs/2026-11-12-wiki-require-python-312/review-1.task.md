# レビューの目的

info-hive-wiki の 0.11.0（同梱のスクリプトの対象を Python 3.10 以上から 3.12 以上にする）の変更を壊してほしい。決定は `docs/adr/0018-wiki-requires-python-312.md` にある。0.11.0 は、まだリリースしていない wiki をたどる経路の修正（0.10.2 として準備し、実装のレビューを 2 回受けたもの）と一緒に出す。

## 対象

- `docs/agent-runs/2026-11-12-wiki-require-python-312/py312.wiki.diff`: info-hive-wiki の `8addd33`（0.10.2 として準備した状態）から `4da26b6`（0.11.0）への差分
  - PEP 723 の `requires-python` を 8 つのスクリプトで `">=3.12"` にした
  - `wiki_text.py` に版の確かめを足した（3.12 より古い版では、理由を標準エラーに書いて `SystemExit(1)`）
  - `wiki_pages._is_junction()` を `DirEntry.is_junction()` にした（項目の `stat(follow_symlinks=False)` を呼ばない）
  - `wiki_lint.missing_assets()` で、NUL を含む参照を `resolve()` の前に「パスにできない」とした（3.13 から `Path.resolve()` が NUL で `ValueError` を出さない）
  - README、CONTRIBUTING、`references/retrieval-setup.md`、`.github/workflows/wiki-tests.yml`（行列を 3.12 と 3.14）、`plugin.json`、`CHANGELOG.md`
- `docs/agent-runs/2026-11-12-wiki-require-python-312/py312.dev.diff`: info-hive-dev の差分（試験、CI、ADR、計画）
- `tests/wiki/test_python_version.py`（新しい試験）、`tests/wiki/test_walk.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_text.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（変更のあとの全体）

## 確かめてほしい点

1. 3.12 より古い Python（3.10、3.11、それより古い版も含む）で、`python` で直接動かすスクリプト（`commands/` と `skills/info-hive/` の手順が `python "<スクリプト>"` で呼ぶもの）が、版の確かめに届く前に別の理由で壊れる経路。構文、読み込みの順、`from __future__`、`_vendor` の読み込み、`wiki_text` より先に走るトップレベルのコード。試験の `DIRECT` の一覧から漏れている入口のスクリプト。
2. uv で動くスクリプトで、宣言を変えたことで壊れる経路（MCP のサーバーの環境の作り直し、`wiki_mcp_launch.py` と `wiki_mcp_relay.py` が子を起動するときの Python の選び方、uv のキャッシュ、`--python` を明示している呼び出しとの食い違い）。
3. `DirEntry.is_junction()` への置き換えが、0.10.2 の `stat(follow_symlinks=False)` による見分けと違う結果を出す入力（Windows のジャンクション、シンボリックリンク、ほかの再解析点、一覧の情報が古い場合、ネットワークのドライブ）。設計（`docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`）の口の表と失敗の分け方との食い違い。
4. lint の NUL の扱いの変更で、3.12、3.13、3.14 のどれかで結果が変わる参照（`%00` 以外の書き方、`from_root` の側）。
5. 3.12 以上を前提にしたことで、文書、コマンド、スキルの手順、試験、CI に残った 3.10 と 3.11 の前提や、黙って飛ばされて確かめられなくなる試験。
6. 変更履歴、ADR、計画の記述が、実装と食い違う箇所。版の決め方（0.11.0）が AGENTS.md のリリースの規則と食い違う箇所。

## 分かっていること

- 確かめた試験: Windows 11 で `test_walk.py`（3.12.13、3.13.7、3.14.6）、`test_python_version.py`、`test_page_set.py`、`test_wiki_lint.py`、info-hive-wiki の `eval/scripts`（3.12、3.13、3.14）、`test_mcp_server.py`、`test_wiki_index.py`、`test_browse*.py`（3.12、依存あり）。Linux（WSL の Ubuntu 24.04）で `test_walk.py`、`test_page_set.py`、`test_wiki_lint.py`、`eval/scripts`（3.12、3.14）、`test_python_version.py`（3.12）。
- 3.10 の Python で版の確かめが止まることは、手元の 3.10.11 で確かめた。試験は、`sys.version_info` を差し替えて確かめる。
- `wiki_lint.py` の未使用の読み込み（`Counter` など）は、この変更の前からある。

指摘のそれぞれに、反例（入力と、結果）と根拠を書く。推測の指摘は、推測と書く。応答は日本語で書く。
