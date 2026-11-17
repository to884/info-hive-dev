## 判定

**却下。確信度：高。** 過去の再現手順は塞がれているが、遅れて続行した確認受付がキャンセル済みの同じ版を復活させる。また、`rerun` で待機に戻ったジョブをキャンセルできない経路を再現した。

## 致命的・重大な欠陥

### 1. 【重大】状態から登録したジョブをキャンセルしても、確認受付の続行が同じ版を復活させる

**再現手順**

1. 接続 A の `decide_ocr_pages` が確認版 1 を台帳へコミットし、ジョブ登録の直前で停止する。
2. ワーカーの `reconcile_rebuilds` が版 1 を検出し、ジョブ J1 を登録する。
3. 接続 B から J1 をキャンセルする。キャンセルは受理される。
4. 接続 A が続行し、版 1 の `register_rebuild` を呼ぶ。

受付側は `only_if_uncovered=False` なので、J1 が版 1 を受け持った記録を無視する。有効なジョブがないため、同じ版を別 ID の J2 として登録する。新しい確認も明示的な再試行もないまま、キャンセルした処理が復活する。

実際の `decide_ocr_pages` の関数本体と `Jobs` を使い、台帳処理から戻る境界に割り込みを挿入した結果：

```text
受付の戻り値: ledger_version=1、rebuild_job.status=queued
ジョブ行: [('cancelled', 1), ('queued', 1)]
J1 と J2 の ID は異なる
```

SQLite はメモリー上で動かし、台帳処理を割り込み用の代替へ差し替えた。ジョブの登録・キャンセル・照会は実装の SQL を実行した。

**根拠：** [rag_server.py:175](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_server.py:175) は台帳コミット後に通常の登録を呼ぶ。[rag_worker.py:181](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_worker.py:181) は同じ版を先に登録できる。[rag_jobs.py:105](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:105) の終端状態を含む確認は、`only_if_uncovered=True` の呼び出しにしか適用されない。接続 A の `_lock` は、別プロセスのワーカーや接続 B を排除しない。

「取り消したジョブが受け持った版は復活しない」という説明とは**食い違う**。

### 2. 【重大】`rerun` 後の待機・再試行に、前回の公開開始済みの印が残る

**再現手順**

1. 版 1 のジョブ J を開始し、`begin_publication` を呼ぶ。
2. J の終了直前に版 2 の確認を受け付け、J に `review_version=2`、`rerun=1` を付ける。
3. 版 1 の結果で `finish` を呼ぶ。J は `queued` に戻る。
4. 版 2 の処理を始める前に J をキャンセルする。

実際の `Jobs` をメモリー上の SQLite で実行した結果：

```text
status=queued、review_version=2、publication_started=1
cancellation_accepted=False
```

版 2 は未公開で、ジョブも待機中なのにキャンセルできない。さらに、その後の処理を失敗させて `retry` しても印は残り、再試行待ちのキャンセルも拒否された。

**根拠：** [rag_jobs.py:289](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:289) は印を立てるが、[同:298](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:298) の待機への遷移と [同:332](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:332) の再試行は印を戻さない。[同:318](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:318) は `publication_started=0` を要求する。

## 崩れる前提

- **確認受付がジョブを登録するまで、その版を受け持つジョブは存在しない。** 台帳コミット直後からワーカーが登録できる。そのジョブのキャンセル後にも、元の受付は続行できる。
- **通常の登録呼び出しは、まだ受け持たれていない新しい版を渡す。** 状態からの登録が先行すると、既にキャンセル済みの版を渡す呼び出しになる。
- **`publication_started` は、これから実行する処理の公開状態を表す。** `rerun` や再試行では、過去の試行の印が新しい待機状態へ持ち越される。
- **完了したジョブが受け持った版は、公開済みである。** `deferred` でも完了するため成立しない。ただし、方針変更後の通常の取り込みで確認を適用する設計は明記されており、この点だけを新たな欠陥とは判定していない。

## 見落としと軽微な問題

- **【軽微】古いジョブの `result.extracted_markdown` が、削除済みの成果物を指す。** 版 1 の作り直し J1 が完了した後、版 2 を公開すると版 1 の成果物は削除される。しかし J1 の保存済み `result.extracted_markdown` は書き換わらない。`page_report.review.extracted_markdown` には現在のパスが入るため回避できるが、同じ応答に有効なパスと削除済みのパスが並ぶ。これは静的確認であり、実ファイルでの再現は未実施。根拠は [rag_index.py:727](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:727)、[rag_jobs.py:146](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:146)。wiki の [ingest-workflow.md:30](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:30) は、先に `result.extracted_markdown` を読むよう指示している。

- **【軽微】回帰試験は今回の競合を通らない。** [test_rag_review.py:529](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:529) はキャンセル後に新しい版を受け付ける順序であり、同じ版の受付処理が後から続行する順序を扱わない。[同:475](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:475) は `rerun` 後にすぐ実行し、待機中のキャンセルを確かめない。

## 検証した事実

| 主張 | 結果 |
|---|---|
| 走査で読んだ版を、そのままジョブへ持たせる | **一致。** 登録後に台帳版を読み直して記録する処理はなくなった。 |
| キャンセル・失敗した版を、後続の走査が復活させない | **一致。** 両状態について、同じ版の登録が `None`、次の `claim` も `None` になることを実行確認した。 |
| キャンセル後に受け付けた新しい版は登録できる | **一致。** 版 1 の終端ジョブを残して、版 2 が別 ID で登録された。 |
| 登録と版の記録の間の停止で、記録だけが失われる | **旧反例は成立しない。** 同じジョブ行への書き込みが登録のトランザクションに含まれる。 |
| `Ledger.state` が台帳版と確認内容を一度に読む | **一致。** 同じ接続の明示的な `BEGIN` 内で読むことを静的確認した。 |
| 契約試験が 27 件ある | **一致。** AST で試験メソッドを数えた。 |
| 依頼元が挙げた試験一式が通る | **確かめられず。** この環境には必要な依存パッケージがない。 |

動的検証は Python 3.14.6 とメモリー上の SQLite で行った。Python 3.12、実 OCR、LanceDB、実ファイルロックを含む統合動作は検証していない。リポジトリのファイルは変更していない。

## 崩せなかった点

- 3 回目の「走査後の版の再読で、新しい未登録版まで登録済みにする」反例は崩せなかった。
- 3 回目の「登録と記録の間の停止後、走査がキャンセル済みジョブを復活させる」反例は崩せなかった。
- 待機中のジョブへ新しい版を引き受けさせ、公開開始前にキャンセルした場合、後続の走査で復活させる反例は得られなかった。
- `MAX` による受け持つ版の更新と、`rerun` を伴う `finish` の遷移自体について、版を小さく戻す経路は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
