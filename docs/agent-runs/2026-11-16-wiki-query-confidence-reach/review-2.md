## 判定

**条件付きで採用可。確信度: 中。** Shift_JIS の写しに対する前回の反例は解消した。一方、RAG の取り込み手順は、新しい例外が要求する「本文からの参照」を保証しておらず、抽出 Markdown が依然として排除されるケースが残る。

## 致命的・重大な欠陥

### 重大：既存手順どおりに作った RAG の要約ページが、抽出 Markdown の許可条件を満たさない

**主張：** 正本は、原本以外のファイルを許す条件として「取り込みの手順がそのソースのために作って**本文から参照している**」ことを要求する。しかし RAG の取り込み手順には、抽出 Markdown を要約ページの本文から参照する指示がない。

**反例・再現手順：**

1. RAG で PDF を取り込み、`result.extracted_markdown` を読んで要約する。
2. 指示どおり、要約ページには `raw`、`raw_sha256`、`rag_job_id` を記録する。本文には抽出ファイルへの参照を書かない。この状態は取り込み手順に違反しない。
3. 後のクエリで、要約に省かれた詳細を質問する。ユーザーは原本の確認を承認する。
4. ジョブに対応する抽出 Markdown を読んでも、正本の条件では「本文から参照しているファイル」に当たらず、回答の前提に使えない。

抽出 Markdown を例示しただけでは、その直前にある本文参照の条件は満たされない。コマンドの「rag の抽出済みの Markdown も除く」を無条件に読む場合と、正本の条件を適用する場合で判断も分かれる。

**根拠：**

- 許可条件：[query-confidence.md:17](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/query-confidence.md:17)
- 抽出本文を読み、原本・ハッシュ・ジョブ ID を記録する手順：[ingest-workflow.md:30](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:30)
- 本文には抽出 Markdown を使う規定：[ingest-workflow.md:246](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:246)
- コマンド側の例外：[commands/query.md:28](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/commands/query.md:28)

文書間の条件の不一致は確認した。モデルが実際に拒否する頻度は未測定である。

## 崩れる前提

- **「正規の派生ファイルは、要約ページの本文から参照されている」**  
  Shift_JIS の変換版では取り込み手順が参照を要求するが、RAG の抽出 Markdown では要求していない。通常の取り込みでも崩れる。

- **「例示されたファイルと、例外の条件を満たすファイルが一致する」**  
  RAG の抽出 Markdown は例示されている一方、本文参照の有無によって条件から外れる。例示を優先するか条件を優先するかで判定が変わる。

## 見落としと軽微な問題

上記と独立した、新規の軽微な欠陥は確認できなかった。

前回指摘した ADR の正本の場所、利用者向け文書の例外欠落、CHANGELOG の原因の断定には、それぞれ追記・修正がある。これらを未修正の指摘として再掲する根拠はない。

## 検証した事実

| 確認事項 | 結果 |
| --- | --- |
| 対象コミット | `17362bf` と一致 |
| Shift_JIS の写し | **解消を確認。** [取り込み手順49行目](C:/Works/info-hive-dev/.claude/worktrees/query-confidence-reach/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:49) が本文への参照を要求するため、新定義の条件を満たす |
| RAG の抽出 Markdown | **未解消のケースを確認。** 抽出ファイルの本文参照を残す指定がない |
| 判定表 | 前コミットと全行一致。今回の変更は正本の17行目のみ |
| 利用者向け文書 | `docs/commands.md:75` に raw 層の例外が追加されている |
| CHANGELOG | 原因を「読み違いで説明できた」とし、修正効果の再測定を未完了としている |
| ADR-0028 | 37行目に日付付きで移動先と旧手順の役割を追記済み |
| 改訂版のモデル実行 | 実施していない。読込率・判定一致率は確かめられず |

## 崩せなかった点

- **無関係なファイルへの通常のリンクだけで raw 扱いにする攻撃。** 正本には「raw ソースとして」「そのソースのために作って」という条件があり、単なる本文リンクだけでは成立しない。
- **Shift_JIS の変換版を外部知識として排除する前回の反例。** 指定手順を守って作った写しは、新しい例外に含まれる。
- **判定条件の移動・変更による欠落。** 今回の差分で出発点・導き方・上限の表は変わっていない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
