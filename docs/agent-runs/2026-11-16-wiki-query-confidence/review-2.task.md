# 2 回目のレビュー

1 回目のレビュー（`docs/agent-runs/2026-11-16-wiki-query-confidence/review-1.md`、却下）の指摘を受けて、規則の作りを直した。差分は `git -C info-hive-wiki show HEAD`（6055b6b）にある。ADR-0028 の「理由」に、崩れた 3 つの前提と直し方を書いた。

直した構造は次のとおりである。

1. 判定の単位を「結論」と「結論を導いた前提」に分けた。
2. 前提の出発点は、書かれていた場所で決める。「高」は、ソースの要約ページか raw の中で主張そのものを確かめたときだけにした。ページ単位の `sources` だけでは「高」にしない。
3. シンセシスのページを根拠から外した。その主張は前提をたどって決め直し、前提が見つからなければ「低」にする。
4. 結論は導き方で決める。そのまま述べたものは前提と同じ、決まった手順（計算など）は前提の最小、判断を加えたものは前提の最小と「中」の低いほうにする。
5. 検索の縮退は、結果の `mode` と `index.state` で見分ける。直し方は 4 つの理由ごとに分け、`--decide` の `failed_open` は上限から外した。
6. 矛盾の上限は「このクエリで読んだページ（別の wiki のページを含む）」にした。
7. SKILL.md、docs/commands.md、CHANGELOG の例外の書き漏れを直した。

前回と同じ対象を、同じ観点で読み直してほしい。直しが元の指摘を本当に解消したか、直しの仕組みから新しい欠陥が出ていないかを、特に確かめてほしい。たとえば次の点である。

- 決まった手順と判断の境目
- 「ソースの要約ページで確かめる」のために読むページが増えること
- シンセシスの前提をたどるときの循環（シンセシスが別のシンセシスを引くなど）
- `mode` と `index.state` の値が、MCP と CLI の実際の出力と合っているか（`scripts/wiki_index.py`、`scripts/wiki_search.py`、`scripts/wiki_mcp_server.py`）

対象のファイルは前回と同じである。

- `docs/adr/0028-wiki-query-answer-confidence-by-rules.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/docs/commands.md`
- `info-hive-wiki/CHANGELOG.md`
