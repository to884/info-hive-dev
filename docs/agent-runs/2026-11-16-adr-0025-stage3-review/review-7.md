## 判定

**却下。確信度：高。** 6 回目の反例は再現しなくなったが、失敗を完了扱いにして確認を取り残す経路と、公開処理との競合で `stale` を `fixed` と誤表示する経路を再現した。

## 致命的・重大な欠陥

### 1. 【重大】空の例外メッセージで失敗すると、未公開の確認が完了扱いになり、再試行も再登録もできない

`process_job` は例外を `str(error)` に変換する。一方、`Jobs.finish` は成功処理の条件に `error is None`、最終状態の決定に `if error` を使っている。`error=''` では、失敗したのに `completed` になる。

**再現手順**

1. 確認版 1 の作り直しジョブ J を登録して取得する。
2. 公開前に `RuntimeError()` を発生させる。`MemoryError()` もメッセージが空になる例である。
3. `process_job` の例外処理から `finish(error='')` が呼ばれる。
4. J を再試行し、同じ確認版を再登録する。

実際の `process_job` と `Jobs` を使った例外注入の結果：

```text
status                   completed
error                    ''
result                   None
review_version           1
retry 後の status        completed
同じ版の register_rebuild None
```

公開していない版を完了済みジョブが受け持つため、自動回収も拒否される。取り込みジョブでも、同じ空文字列による完了誤判定と再試行拒否を確認した。

**根拠：**

- [rag_worker.py:225](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_worker.py:225)：例外を文字列に変換して渡す。
- [rag_jobs.py:313](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:313)：`error is None` の場合だけ担当版を更新する。
- [rag_jobs.py:329](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:329)：空文字列では `completed` を記録する。
- [rag_jobs.py:105](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:105)、[同:357](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:357)：担当済み版の再登録と、完了済みジョブの再試行を拒否する。

### 2. 【重大】公開版の読み取りと旧成果物の削除が競合すると、古くなった確認を適用済みと誤表示する

`Jobs._with_review` は公開 generation を読んだ後、その generation の確信度要約をファイルから読む。両者の間に公開と後始末が入ると、要約が消え、古いジョブの OCR 記録へ戻る。

**再現手順**

1. 元の取り込みジョブには OCR 本文 H0 が保存されている。H0 に対する修正を確認版 1 として保存する。
2. 設定変更で OCR 本文 H1 を取り込み直す。公開 generation G1 では、その修正は `stale` になる。
3. 別ページの確認版 2 を受け付け、ワーカーが次の generation G2 を作る。対象ページの本文は引き続き H1 とする。
4. 元のジョブの `job_status` が G1 を読んだ直後、ワーカーが G2 を公開して G1 の成果物を削除する。
5. `load_summary(G1)` が `None` になり、H0 の要約と H0 に対する修正を組み合わせる。

実際の `_with_review`、台帳処理、SQLite と、メモリー上の成果物を使って再現した結果：

```text
応答の published_version  1
応答の review:fixed       1 件
応答の review:stale       0 件
実際の公開 generation     G2
実際の対象ページの状態    stale
```

**G1 と G2 のどちらでも対象ページは `stale` である。** 単に一つ前の状態を返した結果ではなく、異なる世代の情報を混ぜた誤表示になる。

**根拠：**

- [rag_jobs.py:187](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:187)：公開 generation を先に読む。
- [rag_jobs.py:192](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:192)：要約がなくなると、古いジョブの要約を使う。
- [rag_index.py:719](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:719)、[同:727](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:727)：公開をコミットした後、旧 generation の成果物を削除する。
- [ADR-0025:192](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md:192)：確認状態を公開した版から作る規定と食い違う。

## 崩れる前提

- **例外を文字列化すれば、失敗を表す空でない値になる。** 引数なしの例外では成立しない。
- **公開 generation を読めたら、その成果物も読める。** 読み取り中に次の版の公開と旧成果物の削除が入る。
- **公開要約がなければ、ジョブ保存時の要約で代用できる。** OCR 本文が変わった後は、古くなった確認を適用済みと誤判定する。

## 見落としと軽微な問題

- 契約試験には、空の例外メッセージから `process_job`、`finish`、再試行まで通す検証がない。
- [古いジョブの公開状態を確かめる試験](C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:423)は、公開完了後に照会する。generation の取得と要約の読み取りの間で旧成果物が消える競合を通らない。

## 検証した事実

- 契約試験は 32 件、`tests/rag/test_jobs.py` は 33 件あることを AST で確認した。
- 取り込み・作り直しの両方について、取消後の遅れた完了、再試行、公開開始後の取消拒否、`pause`・`recover` 後の旧 owner による更新拒否を実行確認した。
- Python 3.14.6 とメモリー上の SQLite で検証した。外部依存、ファイル操作などは必要箇所を代替した。
- 必要な依存パッケージがないため、Python 3.12、LanceDB、実 OCR、実ファイルロックを含む既存試験一式の成功は確認していない。ファイルは変更していない。

## 崩せなかった点

- 6 回目の「取消後の `finish(deferred)` が担当版を消し、同じ版を復活させる」反例は再現しなかった。
- `pause`・`recover` 後、別 owner が取得したジョブを旧 owner の `finish`、`progress`、`begin_publication` で更新する反例は得られなかった。
- `rerun` 後は担当版を保持し、公開開始の印を戻した待機ジョブを取り消せた。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
