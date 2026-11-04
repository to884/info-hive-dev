# LanceDB ANN API 調査（0.29.2）

## 結論

`info-hive-rag/scripts/rag_index.py` はチャンクを `merge_insert` し、FTS がまだ無ければ一度だけ作ります。IVF_SQ、generation BITMAP の自動作成、`optimize()` は呼んでいません。検索は既存の vector index がある場合にだけ `nprobes` / `refine_factor` を設定します。旧世代行は catalog 公開後に `delete()` します。

全ページを順番に確認・抽出しますが、`ocr_mode=auto` では画像スキャン、文字化け、縦書き等と判定したページだけOCRします。全ページOCRは `ocr_mode=always` の場合です。各ページの抽出JSONを保存し、再開時は保存済みページを読み飛ばします。

## LanceDB 0.29.2 のAPIと実測

`.rag-venv` の実装シグネチャは次のとおりです。

```python
# LanceTable.create_index (0.29.2)
table.create_index(
    metric="l2", num_partitions=None, num_sub_vectors=None,
    vector_column_name="vector", replace=True,
    accelerator=None, index_cache_size=None, num_bits=8,
    index_type="IVF_PQ", max_iterations=50, sample_rate=256,
    m=20, ef_construction=300, *, name=None, train=True,
    target_partition_size=None,
)

table.create_scalar_index(
    column, *, replace=True, index_type="BTREE", name=None
)
table.wait_for_index(index_names, timeout=timedelta(seconds=300))
table.index_stats(index_name)
table.optimize(*, cleanup_older_than=None,
                delete_unverified=False, retrain=False)
```

IVF_SQ は `index_type="IVF_SQ"`、BITMAP は `create_scalar_index("generation", index_type="BITMAP")` です。既定 `sample_rate=256` は学習に使うベクトル数の目安を `sample_rate * num_partitions` として指定します。固定のAPI最低行数とは説明されていません。

使い捨てPoC（8次元、固定乱数）で `num_partitions=1` と既定 `sample_rate=256` を使い、1/2/16/255/256行で作成・`wait_for_index` がすべて成功しました。`num_partitions=None` の自動設定でも1/2/16/256行は成功しました。1行時は空partitionを飛ばす警告が出ました。よって「最低1行成功」はこの8次元スモーク条件の結果で、品質要件ではありません。製品側の `rows >= 256` は品質・運用方針として設定する値であり、0.29.2 APIのハード制約ではありません。

実例:

```python
table.create_index(
    index_type="IVF_SQ", vector_column_name="vector",
    num_partitions=1, sample_rate=256,
    name="vector_ivfsq", replace=False,
)
table.create_scalar_index(
    "generation", index_type="BITMAP",
    name="generation_bitmap", replace=False,
)
table.wait_for_index(["vector_ivfsq", "generation_bitmap"])
```

512行でIVF_SQ、generation BITMAP、FTSを作成後、3行をappendすると、3索引とも `num_indexed_rows=512`, `num_unindexed_rows=3` でした。FTS検索は `optimize()` 前から追加3行を返し、`optimize()` 後は3索引とも `num_unindexed_rows=0` になりました。FTSのdeltaは完全性のため未索引fragmentへの検索fallbackがあり、`optimize()` が新規行を索引へ取り込みます（[LanceDB公式FTS文書](https://github.com/lancedb/docs/blob/main/docs/search/full-text-search.mdx)）。FTSをappendごとに再作成する必要は確認されませんでした。

削除は異なる点があります。旧generationを削除すると、その直後から `index_stats` は現行3行を `num_indexed_rows=3`, `num_unindexed_rows=0` と報告しました。削除済み行数やtombstone数は `index_stats` に出ず、削除後にoptimizeが必要かどうかをunindexedだけで判定できません。

### optimize再試行

300行・変更なしのテーブルで引数なし `optimize()` を2回続けると、versionは2→3→4、vector `num_indices` は1→2→3に増加し、`indexed=300`, `unindexed=0` のままでした。0.29.2のこの実測では、成功済みoptimizeの無条件再試行は同じ状態を保たず、別のindex partを増やします。append後や削除後など、明示的なdirty状態がある場合だけ呼ぶ必要があります。

同じIVF_SQに `replace=True` で再作成すると、4 partsから1 partに置き換わり、全512行indexed/unindexed=0となりました。意図した全面再構築には使えますが、再開時に毎回呼ばないよう状態判定が必要です。

## 状態・再開判定に使えるAPIと限界

- `table.schema` と `table.version` は公開されています。versionは索引作成・optimizeでも進み、索引専用の世代番号ではありません。
- `list_indices()` の0.29.2実オブジェクトの公開属性は `name`, `index_type`, `columns` だけでした。UUID/index_uuid、fragment IDs、index version、trained rows、partition数、IVF設定値はありません。optimizeで同名のIVF_SQ configが複数返ることがあり、index part単位の世代識別には使えません。
- `index_stats(name)` の属性は `num_indexed_rows`, `num_unindexed_rows`, `index_type`, `distance_type`, `num_indices`, `loss` です。FTS/BITMAPにもindexed/unindexedは返ります。deleted rows属性はありません。ローカル型注釈の `index_type` LiteralはIVF_SQを欠きますが、実行時には `IVF_SQ` を返しました。
- `table.stats()` にもdeleted rowsはありません。削除確認はgenerationごとの `count_rows(filter)`、削除操作のpending状態、versionを別に記録します。

作成・全面再構築は、実行前に外部台帳へpending操作、事前version、想定schema/config、予定row countを記録するのが復帰判定に使えます。再起動時に予定indexの名前・列・型が存在し、`index_stats` が `num_unindexed_rows=0`、かつ事前versionより新しければ、作成/replace成功としてpendingを完了扱いにできます。`trained_rows` はAPIから読めないため、予定row countを台帳から復元する必要があります。

append後optimizeは、pending操作と事前versionを記録してから実行し、再起動後に `num_unindexed_rows=0` なら成功済みとして再実行を避けられます。最適化対象が削除tombstoneだけの場合は、削除直後からunindexed=0になり得るため、削除intentと削除後versionも記録してください。最適化途中で強制終了した場合の内部部分commit原子性は今回検証していません。0.29.2の `optimize()` ドキュメントもexperimentalとしています。

## プロセス中断・OCR

`Jobs.recover()` は起動時にrunning jobをpausedへ移し、`claim()` はqueued/pausedを再取得します。埋め込みバッチは `merge_insert("chunk_id")` 後にcompletedをSQLiteへ保存するため、この間でプロセスが落ちても、再実行は同じchunk IDでupsertされます。抽出済みページもページJSONから再利用されます。

ただしANN作成/optimizeは現行実装に存在せず、ANNの再開ライフサイクルは製品コードでまだ自動化されていません。PoCでは実データや製品コード、OS操作に触れていません。

## 根拠

- ローカル0.29.2: [table.py create_index/optimize/index_stats](</C:/Works/info-hive-dev/.rag-venv/Lib/site-packages/lancedb/table.py:2075>), [IndexStatistics](</C:/Works/info-hive-dev/.rag-venv/Lib/site-packages/lancedb/table.py:4647>), [IndexConfig型定義](</C:/Works/info-hive-dev/.rag-venv/Lib/site-packages/lancedb/_lancedb.pyi:199>), [IvfSqとsample_rate](</C:/Works/info-hive-dev/.rag-venv/Lib/site-packages/lancedb/index.py:484>)
- 製品実装: [rag_index.py](</C:/Works/info-hive-dev/info-hive-rag/scripts/rag_index.py:237>), [rag_jobs.py recover/claim](</C:/Works/info-hive-dev/info-hive-rag/scripts/rag_jobs.py:96>), [rag_worker.py](</C:/Works/info-hive-dev/info-hive-rag/scripts/rag_worker.py:127>), [rag_pdf.py](</C:/Works/info-hive-dev/info-hive-rag/scripts/rag_pdf.py:88>)
- 公式API文書（現行版。0.29.2の正確なシグネチャは上記ローカル実装を優先）: [LanceDB Python API](https://lancedb.github.io/lancedb/python/python/)
- 実測JSON: `C:\Works\info-hive-dev\.rag-poc-data\ann-api-followup\`（削除せず保持）

使用した MCP サーバー: なし  
使用した Agent Skills: research