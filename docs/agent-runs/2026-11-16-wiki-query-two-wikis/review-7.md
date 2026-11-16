## 判定

**却下。確信度：中。** 補助が出した根を渡しても、MCP の再正規化によって別のディレクトリを開く反例が残る。許可された祖先リンクだけで成立し、第5節の保証外には依存しない。

## 致命的・重大な欠陥

### 1. 重大：正規化は冪等ではなく、補助の検査後に MCP の根が変わる

`normalize_wiki_root()` は **NFC 化してからリンクを解決する**。解決先のパスに NFC でない名前が含まれると、返されたパスを再び渡した際、別のディレクトリへ移りうる。

**反例の配置：**

```text
C:/alias/ → C:/kb/é/       ← 祖先のジャンクション
C:/kb/é/wiki/             ← ユーザースコープ。e + U+0301
  SCHEMA.md
  own.md

C:/kb/é/wiki/              ← 上とは別の実体。U+00E9
  SCHEMA.md
  index.md
  P/                      ← プロジェクト wiki
    SCHEMA.md
    secret.md
```

NFC と非 NFC の名前を別々のディレクトリとして作れるファイルシステムを仮定する。両 wiki の根の下にはリンクがなく、識別子は安定し、検査後も配置を変えない。

登録する根は `C:/alias/wiki` と `C:/kb/é/wiki/P`。

1. 補助が前者を正規化すると、祖先リンクの解決によって `C:/kb/é/wiki` になる。
2. **入力を正規化せずに解決しても同じ実体になる**ため、新設された `null` の条件には当たらない。
3. 検査する両根の識別子集合は交わらず、根の下にリンクもない。`wiki_key()` も `/wiki` と `/wiki/P` で異なるため、仕様上は `disjoint` になる。
4. 指示どおり、補助の `roots` に出た `C:/kb/é/wiki` を MCP に渡す。
5. MCP が再び NFC 化し、今度は **`C:/kb/é/wiki` を開く**。検索はその中の `P/secret.md` をユーザースコープのページとして返す。

CLI は渡された根を NFC 化しないため、この配置では同じ `roots` を渡しても MCP と CLI の対象が分かれる。

**根拠：**

- [設計書:151](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:151)：根の祖先のリンクを許可する。
- [設計書:196](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:196)：正規化した根を検査・出力する。197行の比較は、元の入力を解決した根との一致である。
- [wiki_mcp_common.py:78](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:78)：NFC 化、`expanduser()`、`resolve()` の順。
- [wiki_mcp_server.py:103](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:103)：受け取った根を再び NFC 化する。`query`・`get_page` は `State.wiki()`、`list_index`・`graph` は直接 `wiki_root()` を通る。
- [wiki_pages.py:49](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:49)：内側の `P/secret.md` をページから除外しない。

**検証結果：食い違い。** 実際の `normalize_wiki_root()` と `wiki_key()` を抽出し、パス解決とディレクトリ判定だけを差し替えて確認した。

```text
入力をそのまま解決した根 == 補助の根: True
補助の根 == MCP が再正規化した根: False
補助が比較する両根のキーは異なる: True
MCP の変更後の根がプロジェクト wiki を包含する: True
```

補助は未実装であり、`disjoint` は仕様からの推論である。実 NTFS 上での配置作成と MCP の検索全体は実行していない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 正規化した根を渡せば、次の正規化でも同じ実体になる | リンク解決後のパスに、NFC 化すると別の実体を指す名前が含まれる |
| 元の入力と正規化後の実体が一致すれば十分である | 最初の入力は祖先リンクの別名であり、解決結果を再入力したときだけ実体が変わる |
| 根の祖先のリンクは、正規化すれば検査と検索の一致に影響しない | 祖先リンクの解決が、NFC でないパスを生成する |

## 見落としと軽微な問題

- **軽微：正規化の試験が、今回の組み合わせを含まない。** [設計書:221](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:221)以降には祖先のジャンクションと NFC の試験があるが、「祖先リンクの解決先が非 NFC」「出力した `roots` を MCP が再正規化する」という条件がない。記載された試験をすべて通しても、上の欠陥は残る。
- **軽微：相対 `raw:` の説明は、現行 lint の分類を網羅していない。** [設計書:152](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:152)は相対パスを3候補で解決するとする。しかし Windows のドライブ相対パス `C:Books/x.pdf` は、[wiki_lint.py:233](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:233)で URL として読み飛ばされる。実関数の確認でも存在検査は一度も呼ばれなかった。新設のリンク検査が同じ分類を引き継ぐかは未実装のため確認できず、重大な欠陥には数えない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| MCP の4入口は、受け取った根を正規化する | **一致。** `query`、`get_page`、`list_index`、`graph` で確認 |
| CLI の検索・被リンクも根を NFC 化する | **食い違い。** `wiki_search.py:1151`以降は渡された `Path` を使用 |
| CLI のグラフ問い合わせは根を NFC 化する | **食い違い。** `wiki_graph_query.py:230`は `Path` 化のみ。NFC 化はノード ID に適用 |
| 通常の相対 `raw:` は3候補で存在確認する | **一致。** `missing_raw()` の実関数で確認 |
| `~/Books/x.pdf` は相対パスとして3候補を探す | **食い違い。** ホームを展開し、絶対扱いで確認する |
| グラフの問い合わせは DB を読み取り専用で開く | **一致。** `wiki_graph_query.py:60`の `mode=ro` |
| `wiki_roots.py`・`wiki_links.py` が実装済みである | **食い違い。** 現在は存在しない |

ファイルは変更していない。

## 崩せなかった点

- 検査と読み込みが同じ実体を使う条件では、全ディレクトリ・全ファイルの安定した識別子を比較する `shared` をすり抜ける共有配置は示せなかった。
- 根の下のファイルリンクやキャッシュのリンクを使う従来の反例は、今回の `links` の仕様では停止する。
- 外部原本のリンクを許した変更だけから、第5節の保証外に依存せず他方の wiki をキャッシュで上書きする経路は示せなかった。
- 第6回の外部 PDF のハードリンク指摘は、今回の作者の決定の下では欠陥として再計上しない。`result.raw` の記録形式も対象外とした。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
