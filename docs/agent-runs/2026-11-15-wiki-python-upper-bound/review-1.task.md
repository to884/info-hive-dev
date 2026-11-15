# 依頼: Python の上限と、依存を解決できない失敗の扱いの直し（wiki 0.19.5）の敵対的レビュー

## 対象の目的

利用者向け文書の段階 2 で、Python の入っていない新しい Windows 11 に wiki 0.19.4 を入れると、MCP サーバーが起動しなかった。uv で動くスクリプトは `requires-python = ">=3.12"` で上限がなく、uv 0.13.8 は CPython 3.15 を取った。`onnxruntime==1.31.1` には 3.15 の wheel がなく、`No solution found when resolving dependencies` で止まった。中継は、これを「環境が作りかけで壊れている」とみなして入れ直し、`RuntimeError` で止まった。理由は `server.log` にしか残らなかった。

直し方（ADR-0025）:

1. uv で動く 8 つのスクリプトの宣言を、プラグインの CI の行列の範囲 `">=3.12,<3.15"` にそろえた。`tests/wiki/test_python_version.py` が、宣言と `info-hive-wiki/.github/workflows/wiki-tests.yml` の行列を結ぶ。
2. `wiki_mcp_common.py`: `UvSetupError`（入れ直しても直らない失敗）を基にし、`UvTlsError` と新しい `UvResolveError` をその下にした。`_uv_sync` は、依存を解決できない失敗を `UvResolveError` にして `launch.log` に記録する。`prepare_script` は、ほかの失敗も `launch.log` に記録する（入口は記録しなくなった）。
3. README、CONTRIBUTING、`references/retrieval-setup.md`、CHANGELOG（0.19.5）、`plugin.json`、ADR-0025、ADR-0018 の状態。

手元で、uv 0.13.8 と空の Python の置き場所（`UV_MANAGED_PYTHON=1`）で、直す前の宣言は 3.15.2 を取って同じ失敗になり、直したあとの宣言は 3.14.10 を取って onnxruntime 1.31.1 が入ることを確かめた。

## 対象

- プラグイン: サブモジュール `info-hive-wiki` のコミット 1cdd88e（`git -C info-hive-wiki show 1cdd88e`）
- 親: コミット fca89e8（`tests/wiki/test_python_version.py`、`tests/wiki/test_uv_tls.py`、`docs/adr/0025-*.md`、`docs/adr/0018-*.md`、`docs/adr/README.md`、`.github/workflows/wiki-mcp.yml`）

## 確かめてほしいこと

- 上限を付けたことで、新しく起動しなくなる環境がないか。たとえば、利用者の PC に 3.15 だけがあり、uv が Python を取れない（`UV_PYTHON_DOWNLOADS=never`、オフライン、社内のプロキシ）とき。0.19.4 から更新した利用者の既存の環境。`python` で直接動くスクリプトとの食い違い。
- 依存を解決できない失敗の見分け（`no solution found when resolving`）に、誤判定や漏れがないか。uv の版で文言が違うか。壊れた環境の失敗を `UvResolveError` と取り違えて、直るはずの入れ直しを止めることがないか。
- `prepare_script` で記録するようにしたことで、記録が二重になる、または漏れる経路がないか（入口、中継の `--ensure`、中継の serve）。
- 宣言と CI の行列を結ぶ試験が、行列の書き方の変化で黙って通らないか。
- ADR-0025 と CHANGELOG の記述が実装と合うか。
