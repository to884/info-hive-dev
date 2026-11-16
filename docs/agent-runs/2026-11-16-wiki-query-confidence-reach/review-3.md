RAG の抽出 Markdown は、本文リンクなしでも `rag_job_id` 経由で許可されるようになり、前回の反例は解消しています。4文書の3つの参照方法も一致しています。残る点は、Web 画像の例で「本文」が要約ページと raw 本文のどちらを指すか曖昧なことです。## 判定

**採用可。確信度: 中。** `rag_job_id` を独立した参照方法にしたことで、前回の重大な反例は解消した。4文書の例外条件は一致しており、通常の利用で成立する新しい重大な抜け道は崩せなかった。

## 致命的・重大な欠陥

なし。

## 崩れる前提

**「本文」がどのファイルの本文か、一意に分かるという前提。**  
Web 画像へのリンクは、要約ページではなく raw Markdown の本文に置かれる。要約ページが原本だけを参照している場合、「本文が raw として参照するファイル」を要約ページの直接参照に限定すると、画像が条件から外れる。以下の軽微な曖昧さに当たる。

## 見落としと軽微な問題

**軽微：「本文」の指す範囲が、Web 画像の例では曖昧。**

[query-confidence.md:17](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/query-confidence.md:17) は、要約ページによる3つ目の指し方を「本文が raw として参照しているファイル」とし、Web ページの画像を例示している。

一方、取り込み手順では画像リンクは raw Markdown に置かれる。[ingest-workflow.md:154](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:154) の例と、[同:165](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:165) の相対パスの説明で確認できる。要約ページから画像への直接参照は要求されていない。

したがって、要約ページ→raw Markdown→画像という間接参照を含むかが明文化されていない。ただし、Web 画像を許可対象として明示しているため、画像の排除が必ず起きる重大な反例とは判定しない。モデルの挙動は未測定である。

## 検証した事実

| 確認事項 | 結果 |
| --- | --- |
| 対象 HEAD | `3b6077f` と一致 |
| RAG の前回の反例 | **解消。** 本文参照なしでも、frontmatter の `rag_job_id` のジョブが返す抽出 Markdown を許可する |
| 取り込み手順との対応 | **一致。** [ingest-workflow.md:31](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:31) が `rag_job_id` の記録を要求する |
| Shift_JIS の写し | **引き続き許可される。** 同49行目が要約本文への参照を要求しており、3つ目の指し方に該当する |
| 4文書の例外条件 | **一致。** 正本17行目、コマンド28行目、利用者向け文書75行目、CHANGELOG 17行目に同じ3種類がある |
| 判定表 | 前コミットと全行一致 |
| 改訂版の実行結果 | **確かめられず。** 今回は静的レビューのみ |

## 崩せなかった点

- **無関係なファイルへの通常のリンクだけで raw 扱いにする攻撃。** 「そのソースの raw として」という条件が残っており、単なる参考リンクでは成立しない。
- **リポジトリにあるだけの `AGENTS.md` を回答の根拠にする攻撃。** 正本はこれを明示的に対象外としている。
- **RAG の抽出 Markdown に本文リンクを要求する前回の反例。** 今回は本文参照とジョブ参照が別の選択肢になっている。
- **正本の移動に伴う判定条件の欠落。** 今回の差分では確認できなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
