## 再レビューの結果

**結論:** Critical・Major はありません。新たな指摘は Minor が 2 件です。初回の Minor のうち 3 件（`_prune_previous` が回収の記録を残さない件、別 wiki の中断中ジョブの件、`OSError` で回収が止まる件）は、製品の構造を変えて直っています。

### 前提として確認したこと

- **製品のハッシュ:** `rag_index.py` の SHA-256 は `021ea077…aab6` で、依頼の値と一致します。
- **差分の再構成:** 現在の `cache-fix.patch` を逆適用すると `791998a3…`（前回承認版）に戻ります。`first-pass/cache-fix.patch` を当てると `d4df397c…`（初回版）になります。初回版から今回までの差分は、依頼の変更点 1〜3 だけで、範囲外の変更はありませんでした。
- **反例の再現:** `review-counterexamples-before-fix.log` では、修正前のコードで 3 件の反例が失敗しています（`ERROR` 1 件、`FAIL` 2 件）。
- **回帰試験:** Windows は 84 件 OK、Linux は 84 件中 2 件 skip で OK です。ログの時刻（00:52）は、製品の更新（00:47:58）と試験の更新（00:50:35）より後です。
- **実 MCP 試験は実行中です。** `OUT/mcp-results.json`（00:36）は初回の結果で、今回の 21 項目の合否はまだ確認できません。今の実行の trace で確認できたのは次のとおりです。
  - `index_reset` の `preserve_doc_id` が退役文書（`b030…`）だった。
  - `embedding_interrupted` が 1 回あった。
  - forbid を有効にしていない最初の OCR が 1 回あった。

---

### [Minor] 未完了の `jobs` を使用中とみなすため、キャンセルや放棄で残ったジョブがキャッシュを無期限に保持させる

対象
- `info-hive-rag/scripts/rag_index.py`: `_extraction_in_use` に追加した `jobs` の判定（`status!='complete'`）
- `info-hive-rag/scripts/rag_jobs.py` 198–204 行（`cancel`）
- `tests/rag/test_jobs.py` 568–574 行（手で `status='complete'` に変えてから回収を確かめている箇所）

根拠
- 台帳の `jobs` の行が消えるのは次の 3 つのときだけです。
  - 退役の後始末（494 行）
  - 差し替えの公開（708 行）
  - `_reset_index`
- `Jobs.cancel` は `ingest_jobs` の状態を変えるだけで、wiki の台帳の `jobs` には触れません。
- 埋め込みの途中で失敗すると `status='failed'` になります（638 行）。公開の直前に PDF の変更を検出して例外になった場合は、`pending` のまま残ります。
- 単体試験は、手で `complete` に書き換えない限り回収されないことを、そのまま仕様として固定しています。

問題
次の手順で到達します。
1. 文書 D を wiki A と B の両方で公開する。
2. A で D を差し替え、元に戻す。
3. A での再登録が失敗し、利用者が `cancel` する（または放置する）。
4. B で D を差し替える。
5. B の `_extraction_in_use(D)` は A の未完了ジョブを見て「使用中」と判定する。

その結果、B の退役記録と D の抽出キャッシュは、A の設定が変わってリセットされるか、D を A で取り込み直すまで、永久に残ります。B の取り込みと保守のたびに、残った記録の走査も続きます。

検索や OCR の再利用の正しさは損なわないため、Minor とします。ただし、利用者がキャンセルという正規の操作をしても回収が進まなくなる点は、設計の「不要なキャッシュを回収する」と食い違います。

検証方法
`test_other_wiki_keeps_ocr_for_an_interrupted_reactivation` を元に試験を組みます。
1. 中断の後に、A 側の `Jobs.cancel` 相当の操作（`ingest_jobs` だけを変える）を行う。D を A で再投入はしない。
2. B で差し替える。
3. `maintain_indexes(B)` を何度実行しても、キャッシュと B の記録が残ることを確かめる。

修正の方向性
台帳の `jobs` が残っていることを、参照の根拠にする条件を絞ります。
- 再開できる `ingest_jobs`（`queued`・`paused`・`running`・`failed`）が、その wiki で D を指している間だけ、使用中とみなす。
- あるいは、`cancel` や、同じ場所に別の版を公開したときに、その文書の未完了の `jobs` の行を消す。

`jobs` に `doc_id` の列を持たせると、この照合が簡単になります。

---

### [Minor] 実 MCP の「中断後の再開」が、途中までの埋め込みからの再開を確かめていない

対象
- `tests/rag/verify_cache_retirement.py` 156–164 行と、判定 `interrupted_reset_resumes_same_job`
- `tests/rag/cache_fault/sitecustomize.py` の `interrupt_after_saved_embedding`

根拠
- 実行中の trace（`mcp-1795103499219890700/trace.jsonl`）は `{"kind": "embedding_interrupted", "completed": 1, "total": 1}` です。
- スキャン PDF は短い 3 行だけで、`chunk_chars` が 550 のため、チャンクは 1 個です。
- 判定は `job_id` が同じことと `attempts == 2` だけを見ています。`completed < total` は確かめていません。

問題
中断はすべてのチャンクを保存した後、索引の保守と公開の前に起きています。再試行では `range(completed, len(chunks))` が空になります。

そのため、カーソル（`completed`）の途中から埋め込みを続ける経路を、実モデルの MCP では一度も通っていません。初回で求めた「部分埋め込み後の再開」は、今も単体試験（`batch_size` の小さいモック）だけで確かめています。

`review-response.md` の「埋め込み保存後の一度の失敗」という記述は事実に合っていますが、依頼の「再開」の検証としては弱い状態です。

検証方法
1. 実行が終わった後、`trace.jsonl` の `embedding_interrupted` の `completed` と `total` を見る。
2. `results.json` に `completed < total` を示す値がないことを確かめる。

修正の方向性
- 試験用のスキャン PDF を、2 チャンク以上になる長さにする。
- 判定に `0 < completed < total` を加える。
- 再試行の後、行数がチャンク数と一致し、重複がないことも確かめる。

---

### 確認できた点（指摘なし）

- **`_prune_previous`:** 一覧を書き換える前に、回収の意図を同じ台帳にコミットしています。既存の記録は世代を合併し、`rows_pending=1` を上書きしません。実際の削除は `_finish_retirements` だけが行います。途中で止まっても、ロック中でも、再試行の経路に乗ります。
- **剪定で残る途中の行:** 剪定の記録（`rows_pending=0`）が残した、途中まで取り込んだ文書の行とカーソルは、再登録の 554 行で消されません。同じ世代のまま再開できます。
- **`_extraction_in_use` の世代:** 相手の wiki の `policy.json` の指紋から世代を求めています。`_write_policy` が書く値と、`Config.generation` の式は同じです。`policy.json` がない場合や読めない場合は、使用中とみなします。安全側の扱いです。
- **自分の wiki のジョブ:** 取り込み中の文書自身のジョブは、公開のコミットより前に `complete` になります。そのため、最後の後始末で自分のジョブに引っかかることはありません。
- **`OSError` の扱い:** `_remove_extraction` は `Timeout` も含む `OSError` で False を返します。`_remove_legacy_extraction` も失敗を返すようになったので、記録を残したまま後続の文書の処理を続けます。
- **移行の試験:** trace の callback が `BEGIN IMMEDIATE` の実行時に barrier で待ち合わせるので、2 接続とも旧スキーマを確認した状態がそろいます。そのうえで、`BEGIN IMMEDIATE` が 2 回、`ALTER` が 1 回であることを検査しています。順序は決まっています。
- **MCP のフック:** 各ジョブのワーカーの PID を、サーバーの子孫プロセスと対応づけています。製品の全スクリプトのハッシュを開始時と終了時に比べています。

### 未確認事項

- 実 MCP の 21 項目の最終結果。実行中のため、`OUT/mcp-results.json` はまだ初回（17 項目）のものです。

`✶ Insight ─────────────────────────────────────`
- 「使用中」の根拠に台帳の状態を使うと、ロックが外れた中断を守れます。その代わり、その状態を誰がいつ終わらせるかという寿命の管理が必要になります。今回の Minor 1 件目は、`ingest_jobs`（利用者が操作する台帳）と `jobs`（埋め込みのカーソル）の寿命がずれていることから生じています。
- 障害を注入する試験は、注入した時点の状態（`completed`/`total`）も判定に含めないと、狙った経路を通ったかどうかを保証できません。
`─────────────────────────────────────────────────`

このレビューに適したモデルとエフォートは Opus・high でした。次の作業（`jobs` の寿命を `ingest_jobs` とそろえる修正と、MCP 試験のスキャンを複数チャンクにする修正）は Opus・medium が適しています。

使用した MCP サーバー: なし
使用した Agent Skills: なし

Final Result: APPROVED
