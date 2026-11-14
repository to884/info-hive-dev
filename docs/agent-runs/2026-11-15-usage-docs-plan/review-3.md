## 判定

**条件付きで採用可。確信度：高。**  
取得処理を3つに分けた点は実装と一致しますが、「W1の最初の質問」がMCP検索を呼ぶ保証はなく、ruriの計測が完了しない反例が残っています。致命的な欠陥は確認できませんでした。

## 致命的・重大な欠陥

1. **重大：ruriの取得を「W1の最初の質問」に対応付けたため、計測の終点に到達しない正常経路があります。**

   反例は、次の手順です。

   1. ruri未取得のS1からW1を始める。
   2. `/wiki:init` を完了し、「味噌」を取り込む。
   3. `/wiki:query 味噌の原料は？` と質問する。
   4. エージェントが索引から「味噌」の要約を選び、そのページを読んで出典付きで答える。

   これはコマンド定義に従った動作です。`commands/query.md` は、索引から適切な候補が見つからない場合だけ検索するよう定めています。この経路ではMCPの `query` を呼ばず、ruriの取得も始まりません。

   したがって、計画251行の終点である `verified.json` は待っていても現れません。一方、146行の「出典が1つ以上」という成功の目印は満たせます。S1に毎回戻しても、この経路は消えません。113行の「最初の質問のあと、裏で日本語のモデルを取ります」も、正常な利用者に対して誤った説明になります。

   **照合結果：食い違い。** 前回レビューも、索引から回答すれば取得不足を検出できない点を指摘していました。第3版は、取得開始の条件と利用者の操作の違いを取り除いていません。

   根拠：[計画:111](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:111)、[計画:251](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:251)、[query.md:15](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/commands/query.md:15)の手順2〜4、[wiki_mcp_server.py:255](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:255)、`docs/agent-runs/2026-11-15-usage-docs-plan/review-2.md` の重大1。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 最初の質問が、最初のMCP検索になる | 索引と候補ページを読むだけで回答できる |
| S1への復元と3回の試行で、ruriの初回取得を確認できる | 3回ともMCP検索を呼ばず、出典付き回答だけで成功する |
| lintで2つの一覧が空なら、検査対象に問題はない | ファイルの読み取りに失敗し、そのページがリンク検査から除外される |
| `--ensure` の成功は、Claude側との接続成功を表す | サーバーの手動起動は成功するが、ホスト側の接続は失敗する |

## 見落としと軽微な問題

1. **軽微：lintの目印は、検査できなかった状態も成功として受け入れます。**

   読み取りエラーのページを1件渡す、書き込みを伴わない関数実行で、次の結果を確認しました。

   ```json
   {
     "orphans": [],
     "broken_links": [],
     "read_errors": [
       {"path": "sources/味噌.md", "error": "UTF-8 として読めない"}
     ]
   }
   ```

   CLI表示にも孤立ページ・リンク切れの項目は出ません。計画148行の目印を満たしますが、ページを検査できていません。実装は読み取りエラーを報告した後、そのページを検査対象から外しています。「該当する問題がない」と「検査できなかった」を、この目印では区別できません。

   根拠：[計画:148](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:148)、[wiki_lint.py:437](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:437)、同728行以降。

2. **軽微：`--ensure` の終了コード0を「MCPサーバーがつながった」と記録するのは、確認内容と一致しません。**

   `--ensure` は `ensure_server()` を呼び、サーバー情報を表示して終了します。MCPの `session.initialize()` は別の接続経路にあり、実行しません。依存取得とサーバー起動の計測終点にはなりますが、Codeタブとの接続確認にはなりません。

   また、今回の環境では `uv` が見つからなくても、ヘルプスクリプトは終了コード0で11本を表示しました。C1のヘルプの目印も、MCP接続の成否を補いません。

   根拠：[計画:249](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:249)、[wiki_mcp_relay.py:313](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_relay.py:313)、同184行以降、[commands/help.md:11](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/commands/help.md:11)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 対象は0.16.0の `8c400d7` | **一致**。HEADは `8c400d72a6b4ba7b60d974ea5ac7b551e3e1549f` |
| MCP起動・init・MCP検索で取得処理が分かれる | **一致**。ただし通常の質問とMCP検索は同一ではない |
| initの `ready` はE5側の準備完了を示す | **一致**。`setup_wiki.py` は `wiki_search` のバックエンドと索引を準備する |
| `verified.json` はruriの取得完了の印になる | **一致**。所定ファイルの取得とハッシュ確認後に作られる |
| lintはCLIで0件の項目を省略する | **一致**。読み取りエラー時にも2つの対象項目が省略されることを関数実行で確認 |
| `/wiki:help` と `commands.md` の関係 | **一致**。一覧はfrontmatter、詳細は `commands.md` |
| ADR-0021とのCSS方針 | **一致**。ローカルの `origin/docs/wiki-browse-fluent2` にあるADR本文を読み、無改変同梱とJS不使用を照合 |
| Codeタブ、Cowork、新規Windowsでの再現性 | **確かめられず**。今回の実行確認はスクリプトとメモリ上の関数実行に限定 |

## 崩せなかった点

- S1を「依存取得済み、E5・ruri未取得」と定義すること自体に、実装との矛盾はありません。
- 各回をS1のスナップショットから始める手順は、前回のwiki・会話・モデルキャッシュの混入を防ぐ条件になっています。
- initのJSONとlint結果を、返答本文ではなくツール欄で確認する方針に、コマンド定義との矛盾はありません。デスクトップアプリでの閲覧可否は未確認と明記されています。
- 共通リンクを固定の目印から外したこと、P0を分類対象から外したこと、削除対象への参照をプラグイン全体で探すことは崩せませんでした。
- `commands.md` の維持、変更した作業ツリーの試験、公開URLの確認を終了条件に含める点は崩せませんでした。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
