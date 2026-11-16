2件の重大な反例を確認しました。根の比較は、配下のジャンクションによるページ集合の重複を検出できず、`wiki_key()` に合わせた比較は Windows上の別のディレクトリを同一視し得ます。一方、前回問題だった「設定だけに登録されたプロジェクトwikiを発見できない」配置は、今回の独立解決で扱えることを確認しました。## 判定

**却下。確信度：高。** 根同士の包含を除外しても、ページ集合の分離は保証できない。また、`wiki_key()` に合わせる比較には、Windows上の別の wiki を同一視する反例がある。

## 致命的・重大な欠陥

1. **重大：根が離れていても、配下のジャンクションを通じて相手の wiki が混ざる。**

   **反例：** 次の配置で、両方の根に `SCHEMA.md` があるとする。

   ```text
   ユーザー wiki: C:/Users/u/wiki
   プロジェクト wiki: C:/Projects/p/wiki
   C:/Users/u/wiki/project-alias → C:/Projects/p/wiki
                                  （ジャンクション）
   ```

   根だけを `resolve()` して比較すると `disjoint` になる。しかし、現行の走査は途中のジャンクションに降りる。ユーザー wiki の検索がプロジェクト wiki のページを収集し、両方の結果に同じ内容が現れる。ユーザー側から返されたページには、誤って「ユーザースコープ」の出典が付く。

   **検証結果：食い違い。** ファイルを書かず、OSの入口をモックに置き換えて、実際の `walk_pages()` を実行した。ユーザー側には次が入り、`unlistable` と `unknown` は空だった。

   ```text
   project-alias/SCHEMA.md
   project-alias/concepts/secret.md
   project-alias/raw/private.md
   ```

   第5節が除外している「根の別名」や「根同士の入れ子」とは異なる。登録された根自体は別々で、包含もしない。第7節の未確認事項には該当するが、**第8節の「包含を止めればページ集合が分かれる」という直しは、原因を閉じていない。**

   根拠：[設計の分離条件](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:83)、[補助が比較する対象](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:163)、[ジャンクションをたどる走査](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:229)、[収集したファイルを検索対象にする処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:264)。

2. **重大：`wiki_key()` の同一性は、実ディレクトリの同一性ではない。**

   **反例：** 通常のWindows上で、次の別々のディレクトリに wiki を置き、一方をユーザー、他方をプロジェクトとして登録する。

   ```text
   C:/kb/straße
   C:/kb/strasse
   ```

   `wiki_key()` は `casefold()` を使うため、両方が同じキーになる。この規則を補助の同一判定にも採用すると、第3.2節の項目3で一つに縮退し、片方の wiki が検索されない。

   **検証結果：食い違い。** この環境で、実際の `wiki_key()` とWindowsの `CompareStringOrdinal(..., True)` を呼んだ結果は次のとおりだった。

   ```text
   Path の等価比較:                  False
   wiki_key の一致:                  True
   Windows の大文字小文字無視比較:   不一致
   casefold 後の一致:                True
   ```

   実ディレクトリは作成していない。両方のディレクトリが存在し、初期化済みであることを反例の仮定としている。

   さらに、現行MCPのメモリ上の索引は `wiki_key()` ではなく `Path` をキーにしている。この二つは別の `WikiIndex` になりながら、ディスク上の保存先だけが衝突する。したがって、「MCPとそろえる」だけでは、この組合せの安全性を説明できない。これは既存コードにもある衝突だが、新しい補助がそれを**同じ wiki という判断に転用する**点が今回の欠陥である。

   根拠：[補助の同一判定](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:164)、[`wiki_key()`](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:84)、[メモリ上の索引の分離](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:188)、[索引の保存先](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:831)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 根同士が包含関係になければ、ページ集合も分かれる | 一方の配下に、他方へのジャンクションがある |
| `wiki_key()` と同じ比較は、同じ実ディレクトリを識別する | `straße` と `strasse` のように、別名が `casefold()` で一致する |
| MCPの索引は必ず wiki の外に置かれる | `INFO_HIVE_DATA_DIR` が wiki 内を指す |

## 見落としと軽微な問題

- **軽微：MCPの索引が必ず wiki 外にある、という第2節の断定には例外がある。** `INFO_HIVE_DATA_DIR=C:/Projects/p/wiki/mcp-data` とすれば、通常のMCP検索がその wiki 内の `mcp-data/index/...` に書く。第3.5節が許す `.wiki-cache/` 以外への書き込みになる。この配置は第5節にも記載されていない。実行して書き込む試験は行っておらず、設定値と保存処理の接続をコードで確認した。根拠：[`data_dir()`](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:47)、[`WikiIndex` の生成](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:831)、[書き込みの許容範囲](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:112)。

- **軽微：手動確認では、プロジェクト wiki の書き込み禁止を十分に検出できない。** 第4節は両方の `git status` と、ユーザー側の更新時刻だけを確認する。プロジェクト側で、Gitが無視する `graph.sqlite` だけが変わっても検出できない。既定でも、このファイルは無視される。根拠：[手動確認の条件](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:179)、[グラフ成果物の管理方法](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:170)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| `find_workspace()` は最初の一つで戻る | 一致。案内ファイルも読み、Gitの境界では止まらない |
| ユーザー側の設定を別に読める | 一致。`user_workspace_root()` と `load_workspace()` で可能 |
| 設定だけに登録されたプロジェクト wiki を今回の方式で発見できる | 一致。案内ファイル経由のプロジェクト設定と、固定位置のユーザー設定をモックで独立に解決できた |
| `normalize_wiki_root()` がNFC化、`~` 展開、厳密な実体解決を行う | 一致。ただし、比較対象の根の配下までは調べない |
| MCPのメモリ上の索引が `wiki_key()` で分かれる | 食い違い。実際は `Path` をキーにする |
| MCPのグラフ問い合わせ自体がDBを作らない | 一致。SQLiteを `mode=ro` で開く |
| 未埋め込み件数が64以下なら同期的に埋め込む | 一致。第2節の訂正と整合する |

補助は未実装のため、その終了コードやJSON出力は検証できない。実wikiへの問い合わせ、書き込みを伴う試験、ファイルの変更は行っていない。

## 崩せなかった点

- 前回の「古いグラフの再抽出による書き込み」は、今回の禁止規則と `graph-workflow.md` の変更予定によって、設計上は閉じている。
- 指示と設定を両方読み、二つのスコープを独立に決める方式は、前回の代表的な発見漏れを解消する。
- 定型文による読み込みを残すことは作者の決定であり、その限界も第5節に記載されている。同じ理由で再度の欠陥とは数えない。
- ページ集合が実際に分離している場合、根を明示した二回の検索と、順位を混ぜない扱いには障害を見つけられなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
