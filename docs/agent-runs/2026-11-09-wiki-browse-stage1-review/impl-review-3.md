## 判定

**却下。確信度：高。** 終了処理が保護対象の更新より先に走り、Wiki が参照する入力を削除する競合を確認した。また、誤った YAML の日付で、関係表だけでなく中核全体が停止する。

## 致命的・重大な欠陥

### 1. 【重大】終了処理が古い保護対象を使い、外部入力になった `server.json` を削除する

次の手順で成立する。

1. サーバーを起動する。
2. Wiki に、稼働中の `state_dir/server.json` を指すページのシンボリックリンクを追加する。
3. 閲覧要求で再構築を開始し、`take_snapshot()` がその入力を読み終えた直後、`guard.set_protected()` より前で処理が止まる。
4. 別の要求から、正しい操作トークンで `control/stop` を呼ぶ。
5. 終了処理は `shutdown_requested == False` と古い Guard を見て、`server.json` を削除する。
6. 再構築が進んで重なりを検出しても、削除には間に合わない。

要求処理のスレッドは `daemon_threads = True` なので、`server_close()` は再構築の完了を待たない。終了処理と、保護対象・終了フラグの更新を同期する仕組みがない。

実際の `serve()` と `BrowseState.get()` を使い、ファイル操作を mock に置き換えて順序を固定した結果：

```text
serve の終了コード: 0
読取済みの server.json への unlink: 発生
削除時の shutdown_requested: False
再構築を再開した後の shutdown_requested: True
```

また、リンク追加後に閲覧要求を送らず、アイドル終了を待つだけでも、保護対象は更新されず記録が削除される。この場合、Wiki 内のリンクは参照先を失う。

前回の「フラグを見て記録を残す」という修正は、**終了処理より先にフラグが設定済みであること**を前提としている。ディレクトリやジャンクションの差し替えを必要としないため、設計 §6.5 の既知の限界とは異なる。

根拠：[保護対象とフラグの更新](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:381)、[要求スレッドの扱い](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:613)、[終了時の記録削除](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:728)、[保存済み保護対象での削除判定](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:189)、[設計の外部入力保護](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:218)。

実ファイルの削除や実プロセス間の競合は実行していない。

### 2. 【重大】YAML の誤った日付が、関係表のエラー処理をすり抜けて中核全体を停止させる

反例となる `graph/ontology.yaml`：

```yaml
node_types: {}
predicates: {}
updated: 2026-99-99
```

PyYAML 6.0.3 は、この入力に `YAMLError` ではなく `ValueError` を投げる。`parse_ontology()` はそれを `OntologyError` に変換せず、browse 側も捕捉しない。

通常のページが一つある写しで、実関数の結果は次のとおりだった。

```text
Core(): ValueError
BrowseState.get(): 中核なし / failed / ValueError
core の page 要求: {"ok": false, "error": "bad_request"}
```

初回閲覧は503になり、静的書き出しも失敗する。「関係表だけを使えない状態にして、ページを読む」という設計 §3.6 を満たさない。

さらに、**正常なオントロジーがある場合**、ページの次の frontmatter だけでも同じ障害になる。

```yaml
---
type: concept
created: 2026-99-99
---
# A
```

グラフ用のページを作る際、関係表と無関係な `created` まで PyYAML で解析する。その呼び出しも、追加された例外捕捉の外にある。

前回の `node_types: []` は現在 `relations: "error"` になることを確認したが、誤ったオントロジーへの対応は完結していない。

根拠：[オントロジー解析の捕捉範囲](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:212)、[browse 側の捕捉範囲](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:605)、[グラフ用 frontmatter の解析](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:612)、[要求不正として返す処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:317)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| 終了処理に入れば、再構築による保護対象の更新も終わっている | 再構築要求を残したまま `control/stop` で終了する |
| `shutdown_requested` の確認で、安全な後片付けを選べる | 写しの読み取り後、フラグ設定前に終了処理が進む |
| 起動時の Guard は、アイドル終了時にも有効である | 起動後に、状態ファイルを参照するページが追加される |
| YAML の解析失敗は `YAMLError` として捕捉できる | 暗黙の日付型の構築が `ValueError` を投げる |
| 列挙できた索引には、出力にも対応するグループがある | 索引を列挙できるが、その内容を読めない |

## 見落としと軽微な問題

- **【軽微】読めない分割索引へのリンクが、存在しないアンカーを指す。**  
  `index.md` に `- [[indexes/concepts]]` があり、`indexes/concepts.md` の読み取りが失敗すると、リンクは `state: "group"` のまま残る。一方、そのグループ本体は生成されない。メモリ上で、`href="#_gc5bef2c5e1"` が存在し、対応する `id` がないことを確認した。設計 §3.7 の「そのファイルの分を空にする」と食い違う。根拠：[グループIDの先行登録と読み取り失敗時のスキップ](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:679)、[グループへのリンク生成](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:756)。

- **【軽微】起動途中の停止試験は、停止対象が起動段階に入ったことを保証していない。**  
  `self.serve()` の直後に `self.stop()` を実行するだけである。停止側が先にロックを取る実行順序では、停止は「稼働していない」と成功し、その後でサーバーが起動する。続く `p.wait(30)` はタイムアウトする。コード上の実行順序から成立する反例であり、実プロセスでは未再現。根拠：[該当試験](/C:/Works/info-hive-dev/tests/wiki/test_browse_server.py:459)、[ロックを取れた停止側の処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:748)。

- **【軽微・試験不足】絶対パス検査の試験範囲が、設計の主張より狭い。**  
  設計は、別々の印を持つホーム・外部入力も含め、通常応答、エラー応答、記録、`core` 応答を確認するとしている。実装された静的出力の走査は主に Wiki と `data` の印で、サーバー側の確認も404などの個別例に限られる。この不足自体から漏洩の存在を主張するものではない。根拠：[設計の試験条件](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:405)、[Python側の出力検査](/C:/Works/info-hive-dev/tests/wiki/test_browse.py:597)、[ブラウザ側の出力検査](/C:/Works/info-hive-dev/tests/wiki/browse/browse.test.mjs:328)。

## 検証した事実

実行環境は **Windows／Python 3.14.6／PyYAML 6.0.3**。書き込みを伴う全試験、実ブラウザ、Linux、実際のCIは再実行していない。

| 確認事項 | 結果 |
|---|---|
| 出力名の `NamesTest` 5件 | **一致。全件成功** |
| 日本語コーパス27ページの未解決リンクと lint | **一致**。中核の31出力もメモリ上で描画できた |
| 衝突して非表示になったページの未解決リンク | **修正確認**。一覧に残った |
| 別の絶対パスまで警告として通す旧反例 | **修正確認**。漏洩として検出された |
| `raw: ~/papers/x.pdf` と `raw: "http://["` | **修正確認**。描画でき、前者でホームの誤検出なし |
| `node_types: []` | **修正確認**。関係表が `error` になった |
| 追加3スクリプトの文字コード静的検査 | **一致。指摘0件** |
| 版と案内文書 | **一致**。0.10.0と `/wiki:browse` の記載を確認 |
| 既存スクリプトの変更 | `origin/main` との差分は、指定された関数切り出しを確認。**既存動作の全試験による保証は未確認** |
| CIの両OS実行 | **設定上は一致**。Windows・UbuntuでPython試験、Chromiumの2方式、起動速度試験を指定。実行結果は未確認 |

リポジトリのファイルは変更していない。

## 崩せなかった点

メモリ上で実際のHTTP要求パーサーとハンドラーを通した11条件では、Host不一致、誤トークン、閲覧トークンによる停止、`..` とその符号化、`\`、NUL、不正UTF-8、未知名の拒否を越えられなかった。

確認範囲では、閲覧トークンから操作トークンを取得する経路や、要求パスから任意ファイルを返す経路も示せなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: research
