## 判定

**却下。確信度：高。** `review_registered` と実際のジョブが食い違い、未登録の確認が回収されなくなる経路と、キャンセル済みジョブが復活する経路を再現した。登録済み版の記録では、停止と複数接続の境界をまだ処理できていない。

## 致命的・重大な欠陥

### 1. 【重大】登録後に受け付けた確認まで登録済みと記録し、その確認を取り残す

`reconcile_rebuilds` はジョブ登録後に台帳版を読み直し、その値を `mark_registered` に渡す。登録時点の版とは限らない。

**再現手順：**

1. 台帳版1・公開版0・未登録の状態から、ワーカーが再登録を始める。
2. `register_rebuild` がジョブJを登録する。
3. 別のMCP接続がJをキャンセルする。
4. その接続で新しい確認を受け付け、台帳版2をコミットする。版2のジョブ登録前に、その接続が停止する。
5. ワーカーが続行し、現在の台帳版2を「登録済み」と記録する。

版2は、キャンセル後に受け付けた別の確認である。それにもかかわらず、実行するジョブがなく、回収対象からも外れる。

実際の `Ledger`、`Jobs`、`reconcile_rebuilds` に上記の割り込み順序を挿入した結果：

```text
ledger_version = 2
review_registered = 2
unregistered = {}
next_reconcile = []
claim = None
```

**根拠：** [rag_worker.py:181](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_worker.py:181) の登録後、183行で `ledger.version(doc_id)` を再読して記録する。[rag_review.py:90](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:90) は、その値以上の版だけを未登録として返す。

「確認を保存したあと、登録前に止まっても回収する」という説明と**食い違う**。

### 2. 【重大】登録後・記録前に停止すると、キャンセル済みジョブが別IDで復活する

**再現手順：**

1. 台帳版1の確認を保存する。
2. `register_rebuild` がジョブJをコミットする。
3. `mark_registered` のコミット前にMCP接続が停止する。
4. 別の接続で、未公開のJをキャンセルする。
5. 次の起動時または待機中に `reconcile_rebuilds` が走る。

登録済み版の記録がないため、キャンセル済みでも未登録として扱われる。`register_rebuild` はキャンセル済みジョブを重複排除の対象にしないため、新しいIDで再登録する。

実際の処理をメモリー上のSQLiteで実行した結果：

```text
キャンセル後: cancelled、unregistered = {'doc': 1}
再走査後:   queued、元とは異なる job_id
```

**根拠：** [rag_server.py:176](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_server.py:176) の登録と179行の記録は別DBへの別コミット。[rag_jobs.py:100](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:100) は `queued / running / paused` だけを再利用し、[rag_review.py:361](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:361) の走査はキャンセルの記録を調べない。

通常完了した登録では防げているが、明示的にレビューを求められた「登録したのに記録する前に止まった場合」では、前回の反例が残る。

## 崩れる前提

- **登録後に読んだ台帳版まで、そのジョブが担当している。** 登録と版の再読の間に、キャンセルと新しい確認が入ると崩れる。
- **登録済み記録がなければ、まだ一度もジョブを登録していない。** 登録後・記録前の停止では、キャンセル済みや失敗済みのジョブが存在しうる。
- **`page_report` の版番号と確認一覧は同じ時点の状態である。** 台帳版、公開版、確認内容を別々に読む間に、別接続から更新できる。
- **既存の `locations` に、利用者が渡したパスが残っている。** `source` 列追加以前の行では、その値が `NULL` のままになる。

## 見落としと軽微な問題

- **【軽微】`page_report` の台帳版と確認一覧が食い違う。** `_with_review` が台帳版1を読んだ直後に、別接続が版2の却下を保存すると、次の応答になることを実際の台帳更新で再現した。

  ```text
  ledger_version = 1
  published_version = 1
  review:accepted = [1]
  review:awaiting_publish = [1]
  実際の台帳版 = 2
  ```

  wikiの手順256行の版比較は成立する一方、同じ応答には反映待ちが残る。根拠は [rag_jobs.py:161](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:161) と、その後の別接続による確認内容の読み取り。

- **【軽微・互換性】既存の `source=NULL` の場所では、UNC拒否が残る。** 同じ指紋の既存台帳を引き継ぐ条件を置いた。`_catalog` は列を追加するだけで既存行を補完せず、`rebuild_reviewed` は解決済みUNCパスへ戻る。旧形式の台帳をメモリー上で移行して実行すると、`source=None` のまま、実際の `Config.pdf_path` がUNC拒否を返した。実ネットワークドライブでの再現ではない。根拠は [rag_index.py:175](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:175)、[同:793](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:793)。

- **【軽微】追加試験が停止境界を通っていない。** [test_rag_review.py:463](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:463) は登録済み版の記録まで終えてからキャンセルするため、重大指摘2を検出しない。名前に `failed` があるが、失敗経路も実行していない。

- **【軽微】パスの回帰試験は、解決前後のパスが同じローカルPDFを使う。** [test_rag_review.py:512](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:512) は、ドライブ文字からUNCへの変化も、既存行の `source=NULL` も通らない。

## 検証した事実

| 主張 | 結果 |
|---|---|
| 登録済みの版を記録した通常のキャンセルは復活しない | **一致。** 実際の登録・記録・キャンセル・再走査で確認した。 |
| 登録後・記録前の停止でもキャンセルを保持する | **食い違い。** 重大指摘2を再現した。 |
| 再登録時の記録が、新しい確認を取りこぼさない | **食い違い。** 重大指摘1を再現した。 |
| 空の公開要約を古いジョブの要約へ戻さない | **一致。** 実際の `load_summary` と `_with_review` で、却下件数・低確信度件数とも0になった。 |
| 高確信度の `stale` も確認対象にする | **一致。** 確信度0.99でも `review:stale` になり、wiki手順245・249・256行が対象に含める。 |
| 再試行の重複確認と待機状態への更新を一つのトランザクションで行う | **一致。** `BEGIN IMMEDIATE` 内に両方ある。 |
| 契約試験が24件ある | **一致。** 定義数を確認した。成功したかは未検証。 |

実行環境はPython 3.14.6。SQLiteをメモリー上で動かし、ファイル操作・外部依存を代替し、競合は割り込み順序の挿入で検証した。Python 3.12、LanceDB、実OCR、実ファイルロックによる統合試験の成功は**確かめられず**。リポジトリのファイルは変更していない。

## 崩せなかった点

- 空の公開要約から古い確認状態が復活する反例は、今回の修正後には崩せなかった。
- 高確信度の `stale` をwikiの確認手順が落とす反例は、今回の記述では崩せなかった。
- 内部ループで追いついたあとの追加実行について、結果を欠落させる経路は今回の静的確認では見つからなかった。追加された試験も、その境界に確認を挿入している。
- `Ledger.snapshot` の確認内容と台帳版の読み取りについて、前回と同じ不整合は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
