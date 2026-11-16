## 判定

**却下。確信度：中。** 補助が検査する根と MCP が実際に読む根の一致が仕様化されておらず、NFC 正規化によって他方の wiki を読む反例が残る。また、PDF の取り込み手順は、作者が決めたハードリンク禁止と整合していない。補助は未実装のため、その判定結果は仕様からの推論である。

## 致命的・重大な欠陥

### 1. 重大：`shared` が比較した根と、MCP が検索する根が異なりうる

**反例：** Windows 上に、次のディレクトリを別々の実体として置く。リンクはなく、識別子は安定し、検査後も変更しない。

```text
C:/kb/é/                 ← ユーザー wiki。e + U+0301
  SCHEMA.md
  own.md

C:/kb/é/                 ← U+00E9。上とは別ディレクトリ
  SCHEMA.md
  P/                     ← プロジェクト wiki
    SCHEMA.md
    secret.md
```

登録する根は `C:/kb/é` と `C:/kb/é/P` である。

**補助が入力された根を走査する、という仕様の読みを前提とする。** この場合、両方の識別子集合は交わらず、リンクもない。`key_collision` の段階で正規化しても、比較するキーは `C:/kb/é` と `C:/kb/é/P` なので異なり、仕様上は `disjoint` になる。

しかし、MCP の `wiki_root()` は、入力を **NFC 化してから**初期化確認と根の解決を行う。したがってユーザー wiki の問い合わせ先は `C:/kb/é` に変わり、その配下の `P/secret.md` をユーザースコープのページとして検索する。これは第1回レビューの「包含する根から他方のページを読む」欠陥の再発である。

Windows がファイル名を NFC に自動統一するという前提は置けない。Microsoft は、ファイルシステムがパスを WCHAR の列として扱うと説明している。[Microsoft の説明](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)

**根拠：**

- [設計書:196](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:196)：`shared` は二つの根の配下の識別子集合を比較する。
- [設計書:205](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:205)：`normalize_wiki_root()` の適用が明記されているのは `key_collision`。走査前の全判定に適用する記述はない。
- [wiki_mcp_server.py:102](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:102)：初期化確認前に NFC 化する。
- [wiki_mcp_common.py:78](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:78)：NFC 化したパスを解決する。
- [wiki_pages.py:49](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:49)：`P/secret.md` はページとして受理される。

**検証結果：食い違い。** 実際の `normalize_wiki_root()` と `wiki_key()` を抽出し、ディスクアクセスだけを差し替えた確認で、ユーザー側の根の変更、変更後の包含関係、キーの不一致を確認した。補助の実行結果や実 NTFS 上での配置作成は確認していない。

### 2. 重大：ハードリンクの PDF を、禁止対象の raw として取り込み終えられる

**再現手順：**

1. 両 wiki の外に通常の PDF を置き、そのハードリンクをもう一つ作る。指定する PDF の `st_nlink` は 2 とする。
2. rag を有効にして、その PDF を `/wiki:ingest` に渡す。
3. ファイル自体はシンボリックリンクではないため、設計が追加する PDF 用の停止条件に当たらない。
4. 現実装の `Config.pdf_path()` もハードリンク数を検査せず受け付ける。
5. 既存手順に従い、原本を複製せず、完了結果のパスを source ページの `raw:` に書く。

これにより、取り込み完了時点で `raw:` がリンク数2のファイルを指す。第3.8節では、このファイル自体が禁止対象である。

通常ソースには「中身を新しいファイルに写す」という扱いがあるが、PDF の rag 分岐には「原本を複製しない」という指示が残る。予定されている検査の追加はシンボリックリンクだけで、外部 PDF のハードリンクを処理する手順がない。後から lint が指摘できることは、取り込み時の矛盾を解消しない。

**根拠：**

- [設計書:150](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:150)：リンク数2以上の通常ファイルを禁止。
- [設計書:151](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:151)：外部原本も、指すファイルそのものがリンクであってはならない。
- [設計書:173](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:173)：PDF 登録に追加する停止条件はシンボリックリンク。
- [commands/ingest.md:49](/C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:49)：原本をコピーしない。
- [commands/ingest.md:51](/C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:51)：`result.raw` を source ページに書く。
- [rag_config.py:199](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_config.py:199)：解決後の通常ファイルと拡張子などを検査するが、リンク数は検査しない。

**検証結果：食い違い。** 実際の `Config.pdf_path()` に対し、パス解決と属性取得だけを差し替え、`st_nlink=2` の通常ファイルが受理されることを確認した。PDF の抽出処理全体は実行していない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 補助に渡した根と MCP に渡した根は、同じ実体を指す | NFC 化前後の名前が別ディレクトリとして存在する |
| `key_collision` で根を正規化すれば、先行した `shared` の検査も有効である | 正規化によって、検査していないディレクトリへ問い合わせ先が変わる |
| PDF のリンク問題は、シンボリックリンクだけを止めれば閉じる | 外部 PDF がハードリンクであり、rag が原本を複製せず参照する |
| rag に指定時のパスを渡せば、source ページにもそのパスが残る | rag の完了結果が解決済みパスを返し、既存手順がそれを保存する |

## 見落としと軽微な問題

- **軽微：`raw:` に指定時のパスを残す規則と、rag の完了結果が食い違う。** [設計書:153](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:153) は外部原本の `raw:` にも利用者の指定パスをそのまま使うとする。一方、[rag_index.py:485](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:485) は解決済みパスを受け取り、[同:661](/C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:661) でそれを `result.raw` に返す。既存の取り込み手順はこれを保存する。`Z:/book.pdf` の登録自体は直っても、保存される `raw:` は UNC になりうる。第4節には、この保存手順を変える記述がない。

- **軽微：新しい共通モジュールが MCP の更新検出対象にない。** 計画では MCP の lint も `wiki_links.py` を使うが、[wiki_mcp_common.py:40](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:40) の `SERVER_FILES` に同ファイルはなく、変更予定にも同一覧の更新がない。以後 `wiki_links.py` だけを変更してもコードの版が変わらず、[wiki_mcp_relay.py:114](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_relay.py:114) は既存サーバーを再利用する。CLI の補助と MCP の lint が異なる検査規則で動く状態が成立する。初回導入時は `wiki_lint.py` も変わるため、その時点の再起動失敗を指摘しているわけではない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 第5回の bind mount の反例は、新しい `shared` でも通る | **食い違い。** 共有先の識別子が双方の走査に現れ、仕様上は止まる |
| MCP は入力された根をそのまま検索する | **食い違い。** 初期化確認前から NFC 化する |
| CLI も MCP と同じ根の正規化を行う | **食い違い。** CLI は渡された `Path` を初期化確認とページ収集に使う（[wiki_search.py:1151](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:1151)） |
| rag は指定時の PDF パスをジョブに保存する | **一致。** `pdf_source()` と `Jobs.register()` で確認 |
| rag の `result.raw` も指定時のパスである | **食い違い。** 解決済みパスを返す |
| rag の PDF 検査はハードリンクを拒む | **食い違い。** モックで受理を確認 |
| クラウド用リパースポイントをすべてジャンクション扱いする実装である | **確認できず。** `_is_junction()` は `DirEntry.is_junction()` に委ねており、その主張の根拠はない |

`wiki_roots.py` と `wiki_links.py` は存在しないことを確認した。実 OS のマウント、OneDrive、PDF の取り込み全体は試験していない。リポジトリのファイルは変更していない。

## 崩せなかった点

- **同じ実体を指す根を検査・検索に一貫して使う条件では、** 全ディレクトリ・全ファイルの安定した識別子集合を比較する `shared` をすり抜ける共有配置は見つからなかった。
- 第3・4回の索引、キャッシュ、ファイルシンボリックリンクの反例は、現在の検査範囲と `links` の仕様では停止する。
- OneDrive、通常の Git 作業ツリー、大文字小文字を区別しないボリュームについて、不当な `links`・`shared`・`null` を返す確実な反例は立証できなかった。
- 保存とグラフ再抽出の禁止、スコープ別の登録解決、`same` と `key_collision` の区別について、新たな破綻は確認できなかった。
- 古い MCP 本文、検査後の変化、別々にマウントしたネットワーク共有、外部 raw のスコープは、明記された保証外として欠陥に数えていない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
