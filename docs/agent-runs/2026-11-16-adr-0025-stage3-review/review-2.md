同じ文書の作り直しを 2 件有効にできる並行実行も再現しました。再試行側の「ほかに有効なジョブがない」という確認と、待機状態への更新が別トランザクションになっています。検証結果を重大度別にまとめます。
## 判定

**却下。確信度：高。** 再登録が明示キャンセルを無効にする経路と、公開状態を誤表示する反例を再現した。wiki の手順には、古くなった確認を再確認せず要約に使う経路もある。

## 致命的・重大な欠陥

### 1. 【重大】キャンセル・失敗した作り直しを、自動的に別 ID で再登録する

**再現手順**

1. 台帳版 1、公開版 0 の文書について、作り直しジョブ J1 を登録する。
2. J1 をキャンセルする。
3. `reconcile_rebuilds` を実行する。

実際の台帳・ジョブ処理をメモリー上の SQLite で実行した結果：

```text
キャンセル後の再登録: queued、新しい job_id
失敗後の再登録:       queued、新しい job_id
```

`pending_rebuilds` は台帳と公開版の差だけを調べ、キャンセル・失敗の記録を考慮しない。`register_rebuild` は有効なジョブがなければ新規作成するため、明示キャンセルしても次の起動時または待機中の走査で復活する。

PDF の移動、ネットワーク切断、埋め込みの継続的な失敗でも、公開版が追いつかない限り再実行と失敗ジョブの蓄積が続く。`cancel_job` の「次回接続時の自動再開から外す」、`unfinished` の「失敗したジョブは明示的な再試行でしか動かない」という説明と**食い違う**。

**根拠：** [rag_review.py:321](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:321)、[rag_worker.py:151](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_worker.py:151)、[rag_jobs.py:100](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:100)、[rag_server.py:181](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_server.py:181)。

### 2. 【重大】公開版の OCR ページが 0 件になると、古いジョブの確認状態を復活させる

**反例**

1. 文字の層がある PDF を `ocr_mode=always` で取り込み、1 ページ目の OCR を却下して公開する。
2. `ocr_mode=auto` に変えて同じ PDF を取り込み直す。
3. 最初のジョブを `job_status` で照会する。

新しい公開版では OCR していないため、確認は適用されず、文字の層の本文が索引に入る。公開版の確信度要約は正しく空になる。

ところが `_with_review` の次の式は、空の要約を失敗扱いし、古いジョブの要約へ戻す。

```python
summary = load_summary(folder, doc_id, published["generation"]) or summary
```

実際の `_with_review` にこの状態を渡した結果：

```text
review:rejected.count = 1
ocr_low_confidence.count = 1
```

現在は検索対象になっているページを「却下済み」と報告する。検索と `status` は空の公開要約をそのまま扱うため、同じ公開版について表示が食い違う。前回指摘 6 の原因は、空の公開要約で残っている。

**根拠：** [rag_jobs.py:164](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:164)、[rag_review.py:193](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:193)、[rag_review.py:204](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:204)、[rag_index.py:799](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:799)。

### 3. 【重大】wiki の手順が `stale` を確認対象から落とし、未確認の本文を要約に使う

**反例**

1. OCR 本文 H0 のページをユーザーが却下する。
2. 描画設定を変更して取り込み直し、異なる本文 H1 が確信度 `0.99` で得られる。
3. wiki の記載どおりに要約を進める。

実装の一覧生成を実行した結果：

```text
review:stale          = [1]
review:pending        = []
ocr_low_confidence    = []
```

旧判断は SHA の不一致で適用されず、H1 が返す本文と索引に入る。一方、wiki の確認手順に入る条件は `ocr_low_confidence` の存在であり、要約から除く対象も `review:pending` と「あとで」だけである。したがって、このページでは質問を省略し、H1 を要約に使える。

ADR は、OCR 本文が変わったページを確認待ちに戻すと定めている。高い確信度で返った `stale` は、この手順をすり抜ける。

**根拠：** [ingest-workflow.md:245](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:245)、[同:256](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:256)、[rag_review.py:173](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:173)、[ADR:197](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md:197)。

### 4. 【重大】割り当てたネットワークドライブの PDF は、作り直しで UNC 拒否に当たる

**成立条件と手順**

`Z:\本.pdf` が `Path.resolve()` で `\\server\share\本.pdf` に解決される Windows 環境を前提とする。

1. `Z:\本.pdf` を登録する。割り当てたネットワークドライブなので登録できる。
2. 取り込みは解決後の UNC パスを `locations.path` に保存する。
3. OCR の確認を送る。
4. `rebuild_reviewed` は `locations` から UNC パスを取り出し、そのまま `ingest_pdf` に渡す。
5. `Config.pdf_path` が UNC パスとして拒否する。

元の取り込みジョブは利用者が渡したドライブ文字のパスを保持するが、新しい作り直し経路はそれを失う。ネットワークドライブから取り込めても、確認を本文と索引へ反映できない。

これは静的な経路照合による指摘であり、実ネットワークドライブでの再現は未実施。

**根拠：** [rag_config.py:242](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_config.py:242)、[同:264](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_config.py:264)、[rag_index.py:524](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:524)、[同:686](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:686)、[同:783](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:783)。

## 崩れる前提

- **台帳版と公開版の差は、常に実行してよい仕事を意味する。** 明示キャンセルや、原因が解消していない失敗でも差は残る。
- **空の公開要約は、利用できる要約がないことを意味する。** OCR をしなくなった公開版では、空が正しい結果になる。
- **再確認が必要なページは、確信度も低い。** OCR 本文が変わっても、新しい確信度が高い場合がある。
- **catalog に保存した PDF パスを、登録用の検査へそのまま戻せる。** ドライブ文字のパスが UNC に解決されると崩れる。
- **重複確認と再試行の更新の間に、別接続は登録しない。** 2 つの MCP 接続では、その間に別ジョブを登録できる。

## 見落としと軽微な問題

- **【軽微】並行した再試行では、作り直しの重複排除をすり抜ける。** 接続 A の `retry` が「ほかの有効ジョブなし」を読み、接続 B が新規ジョブを登録し、その後 A が旧ジョブを `queued` に戻すと、2 件とも有効になる。この割り込み順序を挿入し、実際の `Jobs` で `queued` が 2 件になることを再現した。確認と更新は別トランザクションである。[rag_jobs.py:314](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:314)。

- **【軽微】失敗した作り直しの `page_report` が文書の識別を失う。** `process_job` は例外時に `page_report` だけを保存し、`Jobs.status` は `result.sha256` だけを確認表示へ渡す。ジョブ行に `doc_id` があっても使わない。再現では、失敗した作り直しが `ledger_version=0`、`published_version=0`、`indexed=false`、反映待ち 0 件を返した。[rag_worker.py:207](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_worker.py:207)、[rag_jobs.py:141](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:141)。

- **【軽微】回帰試験が、元の競合境界を通っていない。** `test_detail_reads_one_snapshot` は更新をすべて終えてから詳細を読む。`test_rerun_keeps_the_full_result` は、最初の作り直しが戻った後に次の判断を入れるため、前回指摘 7 の「内部ループで追いついた後、追加実行が何もしない」経路を通らない。[test_rag_review.py:410](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:410)、[同:436](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/tests/contract/test_rag_review.py:436)。

## 検証した事実

| 主張 | 結果 |
|---|---|
| 前回指摘 1：未公開版の途中経過も文書単位で消す | **一致。** 公開時と文書除外時の SQL を静的確認した。 |
| 前回指摘 2：0 行・方針変更後に途中経過を作り直す | **一致。** `_reset_index` 後の登録を確認した。 |
| 前回指摘 3：DB 間で失った登録を状態から回収する | **一致。** 実際の走査・登録をメモリー上で実行した。ただし重大指摘 1 がある。 |
| 前回指摘 4：成果物を generation ごとに分ける | **一致。** 保存先に指紋と確認版が含まれる。 |
| 前回指摘 5：詳細の確認内容と台帳版を同じトランザクションで読む | **一致。** `Ledger.snapshot` の `BEGIN` と読み取りを確認した。 |
| 前回指摘 6：現在の公開要約から表示する | **食い違いあり。** 空の公開要約で古い記録へ戻る。 |
| 前回指摘 7：追加実行でも本文と報告を返す | **静的には一致。** `ingest_pdf` の取り込み済み分岐を通る。 |

加えて、方針の指紋が異なる wiki が走査から外れること、wiki の `SCHEMA.md` がなくなった場合に新規登録を省くことを、該当分岐を実行して確認した。

実行環境は Python 3.14.6。SQLite はメモリー上で動かし、ファイル操作と外部依存を代替した。Python 3.12、LanceDB、実 OCR、実ファイルロックでの統合動作と、依頼元が挙げた試験一式の成功は**確かめられず**。リポジトリのファイルは変更していない。

## 崩せなかった点

- generation ごとの保存先への変更について、異なる指紋の未公開成果物が公開中の成果物を上書きする経路は崩せなかった。
- 通常の取り込み・作り直しは同じ `write.lock` 内で公開と後始末を行い、後始末は公開した generation を除外する。公開中の成果物そのものを削除する経路は、今回の静的確認では見つからなかった。
- `Ledger.decide` の版照合と版上げ、`snapshot` の確認内容と版の読み取りについて、今回の変更から前回と同じ不整合を起こす経路は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
