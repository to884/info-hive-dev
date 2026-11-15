## 判定

**条件付きで採用可。確信度：高。**  
ruri の計測経路について、3 回目の重大指摘は解消されています。ただし、正常な索引を失敗と判定する目印と、対応対象の古い uv で MCP 起動を妨げる証明書設定が残っています。致命的な欠陥は確認できませんでした。

## 致命的・重大な欠陥

### 1. 重大：`UV_SYSTEM_CERTS=true` の一律設定が、古い uv では自動復旧を止めます

**反例となる条件：**

- `UV_NATIVE_TLS` だけを認識する古い uv を使用する。
- OS の証明書ストアに社内 CA があり、既定の証明書では依存取得に失敗する。
- MCP の依存を初めて取得するか、再構築する。

設定なしなら、起動処理は uv の対応する変数を調べ、`UV_NATIVE_TLS=true` で再試行します。しかし、計画どおりユーザー環境変数に `UV_SYSTEM_CERTS=true` を設定すると、uv はこれを無視する一方、起動処理は「利用者の設定あり」と判断して再試行を打ち切ります。

通信処理を差し替えた読み取り専用の関数実行では、同じ成功条件に対して次の結果になりました。

```text
設定なし                    → 2 回呼び出し、終了コード 0
UV_SYSTEM_CERTS=true のみ    → 1 回呼び出し、UvTlsError
```

**照合結果：食い違い。** 古い uv の実機試験ではありませんが、変数の選択と再試行を止める分岐は確認できました。計画には uv の最低対応版もありません。

根拠：[計画:89](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:89)、[wiki_mcp_common.py:420](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:420) の変数選択、同 452〜465 行の再試行条件。[test_uv_tls.py:104](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/tests/wiki/test_uv_tls.py:104) も古い uv の経路を扱っています。

### 2. 重大：索引の目印 `[[味噌]]` は、定義が固定している文字列ではありません

**反例：** 正常な取り込みで、索引に次の行が追加される場合です。

```markdown
- [[味噌|味噌の要約]]: 味噌の原料と作り方
```

別名付きの wikilink は規約で認められています。索引の更新規則も「ページへの wikilink と 1 文の要約」を要求するだけで、別名を禁止していません。

実際の解析関数にこの行を渡すと、リンク先は `味噌` に解決されました。しかし、目印として指定された文字列 `[[味噌]]` は含まれません。ファイル作成と取り込みが成功していても、読者が目印との不一致を失敗と判断できます。

**照合結果：食い違い。** 索引の増分を 1 行に限定する問題は解消されていますが、参照先の固定と、その表記の固定が混同されています。3 回の試行で別名なしの表記が続いても、別名付きの正常経路は消えません。

根拠：[計画:149](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:149)、[page-conventions.md:56](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/references/page-conventions.md:56)、[ingest-workflow.md:321](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:321)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 証明書設定の変数名は、どの uv でも同じ | `UV_NATIVE_TLS` だけを認識する uv を使う |
| コマンドが参照先を指定すれば、その文字列表記も固定される | 許可された別名付き wikilink を索引に書く |
| S1 に戻せば、後続リリース後も適切な検証状態になる | 更新前のプラグインを含む S1 を復元する |
| `read_errors` が空なら、対象ページを読み落としていない | ディレクトリの一覧取得に失敗し、ページを発見できない |

## 見落としと軽微な問題

1. **軽微：W2 を待つ決定に、S1 の版を合わせる条件がありません。**

   C1・W1 を先に確認して 0.16.0 の S1 を保存し、browse の変更後に W2 を確認する順序が許されています。その後、指定どおり S1 に戻すと、導入済みプラグインも更新前に戻ります。計画自身が、独自マーケットプレイスの自動更新は既定で無効としています。

   したがって、「W2 は後で確認する」と「各回を S1 から始める」だけでは、新しい browse を検証することになりません。これは将来の実行条件による反例で、実機で再現したものではありません。

   根拠：[計画:68](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:68)、同 191・247・257 行。

2. **軽微：`read_errors` を足しても、検査できなかった状態を成功として受け入れます。**

   `wiki_pages.iter_page_files()` は、走査結果の `unlistable` と `unknown` を捨てます。`sources/` などの一覧取得に失敗すると、その中のページは `wiki_lint.collect_pages()` に届かず、`read_errors` にも入りません。

   走査結果を「一覧取得不能のディレクトリあり、発見ファイルなし」に差し替えた関数実行では、次の結果になりました。

   ```text
   orphans = []
   broken_links = []
   read_errors = []
   調べたページ数: 0
   問題は見つからなかった。
   ```

   計画の目印をすべて満たします。前回の対応は、発見済みファイルの読み取り失敗には届いていますが、発見自体の失敗には届いていません。

   根拠：[計画:152](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/docs/plans/usage-docs-2026-11-15.md:152)、[wiki_pages.py:324](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:324)、[wiki_lint.py:333](C:/Works/info-hive-dev/.claude/worktrees/usage-docs-plan/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:333)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 対象プラグインは 0.16.0 の `8c400d7` | **一致**。HEAD は `8c400d72a6b4ba7b60d974ea5ac7b551e3e1549f` |
| 起動・setup・MCP 検索で取得処理が分かれる | **一致** |
| 起動や `stats` では ruri を取得しない | **一致** |
| 明示した MCP `query` が ruri の取得を始める | **一致**。空の初期化済み wiki でも取得処理を通る |
| `verified.json` がファイル取得・ハッシュ確認後に作られる | **一致** |
| setup の `ready` が E5 側の準備を示す | **一致**。MCP 接続成功は示さない |
| `--ensure` がホストとの MCP 接続を確認しない | **一致** |
| `/wiki:help ingest` にセッション取り込みの説明が残る | **一致**。実際の出力で確認 |
| 現行ヘルプの読み取り専用テスト | **8 件合格**。`RealPluginTests` と `HelpCommandTextTests` |
| 新規 Windows、Code タブ、Cowork、取得量・時間 | **確かめられず**。実機検証は行っていない |

## 崩せなかった点

- ruri の計測を W1 の質問から分離し、MCP の `query` 呼び出しを確認する手順は、前回の反例を除いています。
- `commands.md` を Markdown の正本として残す決定は、現行ヘルプの実装と一致します。
- 公開 URL とヘルプからの遷移を終了条件に含めた点には、前回指摘の欠落は残っていません。
- ADR-0021 の無改変 CSS 同梱・版合わせ・`fluent2.js` 不使用と、ADR-0022 の間に直接の矛盾は確認できませんでした。
- セッション取り込みのハウツーを増やさない決定自体が、既存のコマンドやヘルプを壊す根拠は見つかりませんでした。

使用した MCP サーバー: なし  
使用した Agent Skills: diataxis
