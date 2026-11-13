# 設計の敵対的レビューの依頼（1 回目）

info-hive-dev の `docs/plans/wiki-uninitialized-root-2026-11-13.md`（設計、1 版目）と `docs/adr/0019-wiki-root-is-marked-by-schema.md`（ADR の案）をレビューしてほしい。実装はまだない。

## 対象が果たすべき目的

`/wiki:init` をしていないディレクトリ（`SCHEMA.md` のない `wiki/`、GitHub の wiki の写し、空のディレクトリ、ないパス）を、wiki プラグイン `info-hive-wiki` のどの入口も wiki として扱わないこと。具体的には次の 3 つである。

1. 「初期化された wiki」の判定を 1 か所に決める。
2. wiki を読む入口と wiki のために書く入口（CLI、MCP のツール、browse、Web ページの取得 `wiki_fetch.py`、経験の記録 `wiki_evolve.py capture`、`init_wiki.py --upgrade`）が、すべてその判定を通る。未初期化なら何も書かずに止まり、`/wiki:init` を案内する。
3. コマンドの文章（`info-hive-wiki/commands/*.md`）とスキルの指示（`info-hive-wiki/skills/info-hive/SKILL.md`、`references/`）が同じ扱いを書く。

## 読むもの

- 設計: `docs/plans/wiki-uninitialized-root-2026-11-13.md`
- ADR の案: `docs/adr/0019-wiki-root-is-marked-by-schema.md`
- 今のコード（サブモジュール `info-hive-wiki/`、0.12.1）: `skills/info-hive/scripts/` の `wiki_lint.py`、`wiki_stats.py`、`wiki_search.py`、`wiki_graph_lint.py`、`wiki_graph_query.py`、`wiki_graph_extract.py`、`wiki_decide.py`、`setup_wiki.py`、`wiki_evolve.py`、`wiki_evolve_loop.py`、`wiki_browse.py`、`wiki_mcp_server.py`、`wiki_mcp_common.py`、`wiki_fetch.py`、`init_wiki.py`、`wiki_workspace.py`
- コマンドとスキル: `info-hive-wiki/commands/*.md`、`info-hive-wiki/skills/info-hive/SKILL.md`、`info-hive-wiki/skills/info-hive/references/`
- 関連する規則: `AGENTS.md`、`docs/adr/0008-numbered-workspace-layout.md`、`docs/adr/0018-wiki-requires-python-312.md`、`info-hive-rag/scripts/rag_config.py`（rag の `SCHEMA.md` の確かめ）
- 試験: `tests/workspace/`、`tests/wiki/`、`info-hive-wiki/eval/`

## 特に崩してほしいこと

- 判定を通らずに wiki として読むか書く入口が、設計の表から漏れていないか（コードを読んで確かめる）。
- 判定の表（`os.stat()` の扱い、リンク、大文字と小文字）に、版や OS で結果が変わる穴がないか。
- 「入口だけで判定し、ライブラリの関数は判定しない」が、MCP のサーバーの索引のキャッシュ、browse のサーバーの再読み込み、`wiki_evolve_loop.py` などで崩れないか。
- `wiki_fetch.py` に `--wiki` を必須で足すこと、`capture` が wiki を確かめることが、今の利用者（rag を含む）や手順を壊さないか。
- アップグレードの扱い（`SCHEMA.md` を消した wiki を断る）と、初期化を止めないことの組み合わせに矛盾がないか。
- 試験の計画が、未初期化のときに「何も書かない」ことを本当に確かめられるか。
- 版（0.13.0）の判断。

出力は日本語で書く。
