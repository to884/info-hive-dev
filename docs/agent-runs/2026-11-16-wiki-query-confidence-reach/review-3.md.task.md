# 3 回目のレビュー

2 回目（review-2.md）の重大な指摘を直した。rag の要約ページは、抽出済みの Markdown を本文から参照せず、frontmatter の rag_job_id で指す。例外の条件を「要約ページがそのソースの raw として指しているもの」にし、指し方を 3 つ（raw の原本、rag_job_id のジョブの抽出済みの Markdown、本文が raw として参照するファイル）に分けた。差分は git -C info-hive-wiki show HEAD（3b6077f）にある。

確かめてほしいこと:
- 重大の反例（rag で取り込んだページ）が解消したか。
- 新しい抜け道が出ていないか。
- 4 つのファイルの書き方がそろっているか（query-confidence.md、commands/query.md、docs/commands.md、CHANGELOG）。

重大度は、普通に使う場面で起きる度合いで分けてほしい。
