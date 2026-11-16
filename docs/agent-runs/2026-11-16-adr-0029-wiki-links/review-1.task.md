# 依頼：ADR-0029（wiki と raw の木にリンクを置かない）の敵対的レビュー

対象は `docs/adr/0029-wiki-and-raw-hold-no-links.md`（この worktree）である。応答は日本語で書く。

## ADR が果たすべき目的

info-hive の wiki プラグインで、wiki の根と raw の根の下にリンク（シンボリックリンク、ジャンクション、ハードリンク）を置かない規則を、wiki の全体に関わる決定として定める。次の 3 点は作者が決めたもので、ADR はこれを具体化する。

1. raw と wiki の根の下に、シンボリックリンク（ファイルとディレクトリ）、ジャンクション、ハードリンク（`st_nlink` が 2 以上のふつうのファイル）を認めない。
2. lint でも確かめる（新しい指摘 `links`）。
3. 取り込むソースにリンクがあれば、リンクを写さず、先の中身を取り込む（ディレクトリのソースの中のリンクも同じ）。

ADR はさらに、外の原本の PDF（rag）、rag の `result.raw` と `raw:`、リンクとみなすものの根拠、bind mount の扱い、`wiki_links.py` と `SERVER_FILES`、決まった名前の一時ファイル、今ある配置の直し方を決めている。

この規則は、2 つの wiki を引く問い合わせ（`/wiki:query --both`）の設計の敵対的レビューで、リンクと別名による反例が 6 回続いたことから生まれた。問い合わせの設計はこの ADR を参照する。問い合わせの設計そのもの（`wiki_roots.py` の `shared` など）はこのレビューの対象ではないが、ADR がそれに頼る部分（mount の扱い）は対象に含める。

## 確かめてほしいこと

- 規則の範囲（守る木、根とその祖先、相対と絶対の `raw:`）に、規則の目的（根の下の名前が木の外の実体を指さないこと、wiki の書き込みが別の場所を書き換えないこと）を破る穴がないか。
- 「リンクとみなすもの」の条件（`os.lstat()`、名前の代理のビット、`st_nlink`）が、実際の Python と OS の振る舞いと合うか。見逃すものや、誤って挙げるものがないか。
- 外の原本を対象外にする論法、`result.raw` を変えない判断が、ADR-0013 と rag のコードと矛盾しないか。
- 取り込み、lint、移行の手順が、既存の ADR（0008、0013、0017、0019、0020、0023）と矛盾しないか。
- 一時ファイルの直し、`SERVER_FILES` の扱いに、漏れや誤りがないか。
- ADR が「確かめた」と書く事実が、コードと合うか。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コード、設計書、レビューの記録は、次の主のチェックアウトの絶対パスで読む（読み取りだけ）。

- ADR（対象）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0013、0017、0019、0020、0023）
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- そのレビュー: `C:/Works/info-hive-dev/docs/agent-runs/2026-11-16-wiki-query-two-wikis/review-1.md`〜`review-6.md`
- wiki のコード（v0.19.5、`2452f59`）: `C:/Works/info-hive-dev/info-hive-wiki/`（`skills/info-hive/scripts/wiki_pages.py`、`wiki_mcp_common.py`、`wiki_mcp_server.py`、`wiki_mcp_relay.py`、`wiki_search.py`、`wiki_rawcheck.py`、`wiki_session.py`、`wiki_lint.py`、`wiki_index.py`、`commands/ingest.md`、`commands/lint.md`、`skills/info-hive/references/ingest-workflow.md`）
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`（`rag_config.py`、`rag_index.py`、`rag_jobs.py`）

ファイルは変えない。
