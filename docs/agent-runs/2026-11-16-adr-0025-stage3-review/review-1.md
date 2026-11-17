## 判定

**却下。確信度：高。** 中断後の再開で索引行を欠落させる経路、0 行の版の取り込み直しで旧索引を消して失敗する経路、未公開の本文が公開済みの本文を上書きする経路を再現した。確認の取りこぼしと、同時更新の検出をすり抜ける競合もある。

## 致命的・重大な欠陥

### 1. 【重大】中断した確認版の途中経過が残り、PDF を元に戻すと埋め込みを飛ばす

**再現手順**

1. PDF A を確認版 0 で公開する。
2. 確認版 1 の作り直しを、最後の埋め込みを保存した後、公開前に止める。
3. 同じ場所の PDF を B に置き換えて取り込む。A の登録場所はここだけとする。
4. 同じ場所に元の A を戻して取り込む。OCR は以前と同じ本文を返す条件とする。

B の公開時、A の全索引行は削除される。一方、途中経過から消すのは A の版 0 と公開中の generation だけで、未公開の版 1 の `completed` が残る。A を戻すと版 1 の途中経過を再利用し、既に消した行の埋め込みを飛ばす。

メモリー上の SQLite と索引テーブルの代替で、実際の `ingest_pdf` を実行した結果：

```text
after_replace_with_B A_checkpoint 1 A_rows 0
after_restore_A status indexed claimed_chunks 1 actual_A_rows 0 published_version 1
```

**根拠：** [rag_index.py:587](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:587) の再開位置、[rag_index.py:688](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:688) の限定的な途中経過削除、同ファイル 708–711 行の文書全行削除。説明された「途中経過を消して埋め込みを最初からやり直す」と**食い違う**。

### 2. 【重大】0 行の確認版を方針変更後に取り込むと、索引を消してから例外になる

**再現手順**

1. 1 ページの PDF を取り込む。
2. そのページを却下し、確認版 1・0 チャンクを公開する。
3. `EXTRACT_REVISION` または埋め込み設定を変えて、同じ PDF を取り込み直す。

`stale and not chunks` の分岐で `_reset_index` が catalog の `jobs` を全削除する。その直後、対象 generation の途中経過を作らずに `fetchone()[0]` を読む。

実際の分岐をメモリー上で実行すると、次の結果になった。

```text
TypeError 'NoneType' object is not subscriptable
documents_remaining 0
checkpoints_remaining 0
```

旧索引全体を消した後の失敗になる。

**根拠：** [rag_index.py:581](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:581)〜588 行、[rag_index.py:242](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:242)〜252 行。ADR の「0 行の版」と「設定変更後も確認結果を当てる」の組み合わせで**食い違う**。

### 3. 【重大】確認のコミット後、ジョブ登録前に停止すると、自動反映が永久に取り残される

**再現手順**

1. 未完了の作り直しジョブがない状態から確認を送る。
2. `reviews.sqlite` のコミット後、`register_rebuild` のコミット前に MCP プロセスを停止する。
3. 再接続する。

台帳には確認版 1 が残るが、実行するジョブがない。`recover` は既存の実行中ジョブを待機状態に戻すだけで、台帳と公開版の差を走査しない。

メモリー上でこの停止境界を再現すると、`ledger_version=1` のまま `claim=None`、`unfinished=False` になった。元の `base_version=0` で呼び直しても版不一致になる。MCP 呼び出しは未完了でも、確認だけが保存済みになる。

**根拠：** [rag_server.py:175](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_server.py:175)〜176 行、[rag_review.py:121](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:121)〜123 行、[rag_jobs.py:205](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:205)〜209 行。「確認の取りこぼしを防ぐ」という目的と**食い違う**。

### 4. 【重大】未公開の本文と確信度要約が、公開済みの成果物を上書きする

`reviewed/<doc>/<V>/document.md` は確認版だけを鍵にし、指紋を含まない。`confidence.json` は確認版さえ含まない。どちらも埋め込み・公開より前に書かれる。

**再現手順**

1. OCR 本文 H0 を修正した確認版 1 を公開する。
2. OCR の描画設定を変え、本文 H1 を抽出する。
3. 最初の埋め込みで失敗させる。
4. 設定を元に戻す。

catalog は旧 generation・旧指紋・確認版 1 のままだが、以前返された本文パスの中身は H1 に変わっている。確信度要約も H1 のものになり、旧索引に正しく適用されている確認が `stale` と判定される。

実際の制御経路を、ファイル出力をメモリーに置き換えて実行した結果：

```text
catalog_after_failure ('published-old', 'old-policy', 1)
previously_returned_markdown_now NEW UNAPPROVED OCR
old_published_decision_state stale
```

**根拠：** [rag_index.py:494](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:494)〜499 行、[rag_index.py:578](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:578)〜593 行、[rag_review.py:172](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:172)〜177 行。公開済みの本文・状態を維持する要件と**食い違う**。

### 5. 【重大】`ocr_page_detail` が古い確認内容に新しい版番号を付け、同時更新の検出をすり抜ける

確認内容、履歴、台帳版を別々の接続で読むため、同じスナップショットにならない。

**再現手順**

1. 台帳版 1 の確認内容と履歴を `ocr_page_detail` が読む。
2. 最後の `ledger.version` の前に、別の呼び出しが版 2 の「却下」を保存する。
3. 詳細応答は、版 1 の確認内容・履歴と `ledger_version=2` を返す。
4. 利用者がその応答に基づき `base_version=2` で修正を送る。

版の照合は成功し、利用者に示していない版 2 の判断を上書きする。

実際の `page_detail` と `Ledger.decide` で、次を再現した。

```text
detail_decision_version 1
detail_history_versions [1]
returned_base_version 2
stale_screen_decision_accepted_as_version 3
```

**根拠：** [rag_review.py:250](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_review.py:250)〜252 行。版の更新自体は原子的でも、「別セッションの判断を知らずに上書きしない」という ADR の目的と**食い違う**。

### 6. 【重大】古いジョブの `page_report` が、現在の公開状態を誤表示する

`Jobs._with_review` は公開版を現在の catalog から読む一方、OCR の SHA と確信度はジョブ保存時の `page_report` から読む。

**反例**

OCR 本文 H0 を修正して公開した後、設定変更で H1 を OCR し直して取り込む。旧判断は現在の索引では `stale` になる。しかし最初の取り込みジョブを照会すると、H0 の保存済み要約と旧判断が一致し、`fixed` と報告される。

実際の `_with_review` に旧ジョブの記録を渡すと、`review:fixed=1`、`review:stale=0`。現在の H1 に対する `page_state` は `stale` だった。

さらに、確認反映後も元の取り込みジョブの `extracted_markdown` と `result.review` は更新されず、`page_report.review` だけが最新になる。同じ応答に「新しい公開版」と「確認前の本文パス」が混在する。

**根拠：** [rag_jobs.py:135](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:135)〜142 行、[rag_jobs.py:151](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:151)〜168 行。ADR の「公開した版から状態を作る」「確認を当てた本文を返す」と**食い違う**。

### 7. 【重大】`rerun` の追加実行が、完成したジョブ結果から本文パスと `page_report` を消す

**再現手順**

1. 確認版 1 の作り直し中に、版 2 の確認を受け付ける。ジョブに `rerun=1` が付く。
2. `rebuild_reviewed` 内のループが版 2 まで公開する。
3. `finish` が `rerun` を見てジョブを再び待機状態にする。
4. 追加実行は既に追いついているため、最小限の `unchanged` 結果を返す。
5. `finish` が、その結果で完成済みの結果を上書きする。

実際の `Jobs` の遷移で、再受付時には存在した `extracted_markdown` が、最終結果から消えた。`page_report` も同様に失われる。依頼元が案内する `rebuild_job` を待ち終えても、本文とページ報告を取得できない。

**根拠：** [rag_index.py:754](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_index.py:754)〜756 行、[rag_jobs.py:279](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:279)〜289 行。

## 崩れる前提

- **行を削除すると、その行の途中経過も消える。** 未公開の確認版がある文書を別の PDF で置き換えると崩れる。
- **確認版 V だけで、返す本文を一意に識別できる。** 台帳版を変えずに抽出・OCR の設定を変えると崩れる。
- **確認の保存とジョブ登録の間では停止しない。** プロセス停止やジョブ DB の書き込み失敗で崩れる。
- **詳細応答の内容と `base_version` は同時点のものになる。** 別の確認が読み取り途中に入ると崩れる。
- **古いジョブの OCR 要約で、現在の公開状態を判定できる。** OCR のやり直しで本文が変わると崩れる。
- **追加の作り直しは、結果を上書きしても情報を失わない。** 追加実行が `unchanged` になると崩れる。

## 見落としと軽微な問題

- **【軽微】再試行で同じ文書の作り直しジョブを複数有効にできる。** J1 をキャンセルし、次の確認で J2 を登録した後、J1 を `retry` すると待機中が 2 件になる。実際の `Jobs` で再現した。[rag_jobs.py:100](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_jobs.py:100) の重複排除を、303–307 行の再試行は通らない。
- **【軽微】確信度の版を上げても、保存済みの最小値が不明にならない。** ページの記録に確信度の版がなく、`page_report` は現在の版名を付ける。旧最小値 `0.2` が `confidence-v2` として返ることを再現した。ADR の旧版を不明扱いする規定と食い違う。[rag_pdf.py:244](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage2/info-hive-rag/scripts/rag_pdf.py:244)〜249 行、同ファイル 290–294 行。
- **試験の空白。** `test_rag_review.py` は、停止した版から別 PDF への置換と復帰、0 行と方針変更の組み合わせ、DB 間の停止、詳細取得中の同時確認を扱わない。途中失敗は `Engine` を直接呼び、`rerun` 試験は `rebuild_reviewed` が戻った後に次の確認を入れているため、上記の境界を通らない。

## 検証した事実

- 対象の ADR、指定された実装、契約試験、実 OCR 検証スクリプトを読み、上記の箇所を照合した。
- SQLite はメモリー上で動かし、ファイル出力・埋め込み・索引テーブルなどを代替して、実装の状態遷移を実行した。上記の再現結果はその実行結果である。
- 実行環境は Python 3.14。依頼元の Python 3.12、LanceDB、実 OCR 環境での統合再現は**確かめられず**。必要な依存がなく、既存試験一式は実行していない。
- `verify_ocr_confidence.py` が実際の cascade と個別認識器を検証する内容であることは**一致**。その実行成功と、`rag_ocr.py` の画像入力から応答全体までの動作は今回確認していない。
- リポジトリのファイルは変更していない。

## 崩せなかった点

- `Ledger.decide` 内の版照合と版上げは、同じ `BEGIN IMMEDIATE` に入っている。古い版番号をそのまま送る操作では崩せなかった。指摘 5 は、その前段の詳細取得の競合である。
- 確認版を先に固定し、`upto=review_version` で判断を読むため、索引生成中に後続の判断だけが混入する経路は見つからなかった。
- 通常の作り直しでは新旧の generation が分かれ、検索も公開中の generation に制限される。未公開の新しい索引行が、そのまま検索に混ざる経路は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
