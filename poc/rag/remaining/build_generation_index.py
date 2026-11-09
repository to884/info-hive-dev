"""公開世代の絞り込みに索引を付け、全量検索の遅延を比較する準備。"""
import json
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
WORK=POC_DATA/'full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def main():
    os.environ['RAYON_NUM_THREADS']='4'; os.environ['OMP_NUM_THREADS']='4'
    from rag_index import Engine
    cfg=Config(json.loads((WORK/'product-config.json').read_text(encoding='utf-8')))
    folder=cfg.workspace(str(WORK/'product-wiki'))
    table=Engine(cfg)._table(folder)
    def state():
        version=table.version
        return {'version':version() if callable(version) else version,'rows':table.count_rows(),'indices':[{'name':index.name,'type':index.index_type,'columns':index.columns} for index in table.list_indices()],'disk_bytes':sum(path.stat().st_size for path in folder.rglob('*') if path.is_file())}
    before=state()
    if any('generation' in index['columns'] for index in before['indices']):
        raise RuntimeError('比較用の世代索引は作成済みです。元の記録を上書きしません。')
    with sqlite3.connect(folder/'catalog.sqlite') as db:
        generations=[row[0] for row in db.execute('SELECT generation FROM documents')]
    active='generation IN ('+','.join("'"+generation+"'" for generation in generations)+')'
    with (WORK/'embeddings-130m/vectors.f32').open('rb') as stream:
        vector=list(struct.unpack('<512f',stream.read(2048)))
    def plan():
        query=table.search(vector).distance_type('cosine').where(active,prefilter=True).nprobes(cfg.search_nprobes).refine_factor(cfg.search_refine_factor).limit(200).select(['chunk_id','doc_id','page','section','title','text'])
        return query.explain_plan(verbose=True) if hasattr(query,'explain_plan') else None
    plan_before=plan()
    started=time.perf_counter()
    table.create_scalar_index('generation',index_type='BITMAP',replace=False)
    seconds=time.perf_counter()-started
    after=state()
    if before['rows']!=after['rows']: raise RuntimeError('世代索引の作成で行数が変わりました。')
    write_json(OUT/'full-generation-index.json',{'source_fingerprint':json.loads((WORK/'product-index-complete.json').read_text(encoding='utf-8'))['source_fingerprint'],'generation_values':len(generations),'type':'BITMAP','build_seconds':seconds,'before':before,'after':after,'added_disk_bytes':after['disk_bytes']-before['disk_bytes'],'dense_plan_before':plan_before,'dense_plan_after':plan(),'scope':'検証用の全量テーブルへ公開世代のスカラー索引を追加。本文・ベクトル・検索設定は維持し、別タグで実 MCP を再計測する。'} )


if __name__=='__main__': main()
