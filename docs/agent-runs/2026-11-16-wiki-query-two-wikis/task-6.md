# レビューの目的（6 回目）

`docs/plans/wiki-query-two-wikis-2026-11-16.md`（9 版目）は、info-hive の wiki プラグイン（`info-hive-wiki`）の `/wiki:query` で、利用者が求めたときだけ、ユーザースコープの wiki とプロジェクトの wiki の 2 つを引く設計である。1〜5 回目のレビュー（`review-1.md`〜`review-5.md`）はどれも却下で、崩れた前提と直し方の対照は第 8 節にある。第 6 節の事項（raw と wiki にリンクを認めない、取り込みはリンクの先の中身を写す、など）は作者が決めた。決定そのものではなく、決定のもとで設計が崩れる点を探してほしい。

5 回目の指摘を受けて、9 版目は次のようにした。

- 補助 `wiki_roots.py check` は、`null`、`same`、`links`（`wiki_links.find_links()`）、`shared`（2 つの根の下に現れるすべてのディレクトリとファイルの識別子の集まりが重なる）、`key_collision`、`disjoint` の順に確かめる。別名の仕組み（bind mount、`subst` など）を数え上げず、識別子を直接比べる。
- rag の `register_pdf` と外の原本の `raw:` には、利用者が指定したパスを解決せずに渡す。指定したパスそのものがシンボリックリンクなら、先のパスを頼む。

次を崩すことを狙ってほしい。

- `shared` の比べ方で見つからないのに、2 つの wiki が同じ実体を分け合うか、問い合わせが他方の中身を読むか、許したキャッシュの書き込みが他方を変える配置。第 5 節に保証しないこととして書いたもの（識別子を安定して返さないファイルシステム、同じ共有の別々のマウント、確かめたあとの変化、MCP の古い本文）は数えない。
- 補助が、ふつうの配置（OneDrive などのクラウドの同期フォルダー、Git の作業ツリー、Windows の大文字小文字を区別しないボリューム）で、不当に `links`、`shared`、`null` を返して 2 つを引けなくなる反例。lint の `links` が、今の正しい wiki や raw を誤って挙げる配置。`info-hive-wiki/skills/info-hive/scripts/wiki_pages.py` の `win_file_id()`、`_is_junction()` などと照らして。
- 取り込みと rag の規則（第 3.8 節）と、今の実装（`info-hive-wiki/commands/ingest.md`、`skills/info-hive/references/ingest-workflow.md`、`info-hive-rag/scripts/rag_config.py`）との矛盾。
- 1〜5 回目の直しが 9 版目で崩れていないか。第 2 節と第 5 節の誤りと漏れ。

設計の段階なので、細かな文言より、設計を覆す欠陥を優先する。
