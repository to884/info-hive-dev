"""保存済み実ベクトルのスナップショットで ANN 圧縮・再順位付けを計測する。"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def size(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())


def save(path,data):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(path)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=100000); a=p.parse_args()
    os.environ['RAYON_NUM_THREADS']='4'
    os.environ['OMP_NUM_THREADS']='4'
    import numpy as np
    import pyarrow as pa
    import lancedb
    import psutil
    from threadpoolctl import threadpool_limits
    threadpool_limits(4)
    source=sqlite3.connect(f'file:{WORK / "corpus.sqlite"}?mode=ro',uri=True,timeout=30)
    source.execute('ATTACH DATABASE ? AS embeddings',(str(WORK/'embeddings-130m/ledger.sqlite'),))
    selected=source.execute('SELECT c.id,e.position FROM chunks c JOIN embeddings.vectors e ON e.id=c.id ORDER BY c.id LIMIT ?',(a.limit,)).fetchall()
    if len(selected)<a.limit: raise RuntimeError(f'まだ {len(selected)} ベクトルしかありません。')
    source.close()
    mapped=np.memmap(WORK/'embeddings-130m/vectors.f32',dtype=np.float32,mode='r',shape=((WORK/'embeddings-130m/vectors.f32').stat().st_size//2048,512))
    vectors=np.asarray(mapped[[r[1] for r in selected]],dtype=np.float32)
    del mapped
    # 保存された FP32 配列を厳密検索の基準にする。CPU/GPU の埋め込み差はここへ混ぜない。
    rng=np.random.default_rng(20261104)
    positions=rng.choice(len(vectors),size=64,replace=False)
    queries=vectors[positions].copy()
    queries[32:]+=rng.normal(0,.015,queries[32:].shape).astype(np.float32)
    queries/=np.linalg.norm(queries,axis=1,keepdims=True)
    norms=np.linalg.norm(vectors,axis=1)
    scores=queries@vectors.T/norms
    exact=np.argsort(-scores,axis=1)[:,:30]
    del scores
    folder=WORK/f'ann-{a.limit}-{time.time_ns()}'
    folder.mkdir()
    peaks={'rss':0}; stopped=threading.Event()
    def monitor():
        proc=psutil.Process()
        while not stopped.wait(.05): peaks['rss']=max(peaks['rss'],proc.memory_info().rss)
    threading.Thread(target=monitor,daemon=True).start()
    result={'rows':len(vectors),'dimension':512,'source':'実資料の自動分割から得た埋め込み。完了した先頭 id のスナップショット。','source_extraction_complete':(WORK/'extraction-complete.json').exists(),'query_kind':'32保存ベクトルと32微小ノイズ付き保存ベクトル。日本語質問の関連性評価ではない。','exact_baseline':'同じ保存 FP32 配列の cosine 全件検索上位30','profiles':[]}
    try:
        for kind,dtype in [('IVF_PQ','float32'),('IVF_PQ','float16'),('IVF_SQ','float32'),('IVF_HNSW_SQ','float32')]:
            name=kind.lower()+'-'+dtype
            location=folder/name
            db=lancedb.connect(str(location))
            value_type=pa.float16() if dtype=='float16' else pa.float32()
            schema=pa.schema([('id',pa.int64()),('vector',pa.list_(value_type,512))])
            table=db.create_table('vectors',schema=schema)
            for start in range(0,len(vectors),8192):
                values=vectors[start:start+8192].astype(np.float16 if dtype=='float16' else np.float32)
                batch=pa.Table.from_arrays([pa.array(np.arange(start,start+len(values))),pa.FixedSizeListArray.from_arrays(pa.array(values.reshape(-1),type=value_type),512)],schema=schema)
                table.add(batch)
            raw_bytes=size(location)
            partitions=max(4,min(4096,int(len(vectors)**.5)))
            started=time.perf_counter()
            options={'vector_column_name':'vector','metric':'cosine','index_type':kind,'num_partitions':partitions}
            if kind=='IVF_PQ': options.update(num_sub_vectors=64,num_bits=8)
            table.create_index(**options)
            build_seconds=time.perf_counter()-started
            measurements=[]
            for nprobes in [min(8,partitions),min(32,partitions),min(128,partitions)]:
                times=[]; recalls=[]
                for i,query in enumerate(queries):
                    started=time.perf_counter()
                    search=table.search(query).distance_type('cosine').nprobes(nprobes).refine_factor(4)
                    if kind=='IVF_HNSW_SQ': search=search.ef(120)
                    found=search.limit(30).select(['id']).to_list()
                    times.append((time.perf_counter()-started)*1000)
                    recalls.append(len({row['id'] for row in found}&set(exact[i]))/30)
                measurements.append({'nprobes':nprobes,'refine_factor':4,'ef':120 if kind=='IVF_HNSW_SQ' else None,'ann_recall_at_30':float(np.mean(recalls)),'p50_ms':float(np.quantile(times,.5)),'p95_ms':float(np.quantile(times,.95)),'max_ms':max(times)})
            result['profiles'].append({'index':kind,'vector_dtype':dtype,'num_partitions':partitions,'build_seconds':build_seconds,'raw_table_bytes':raw_bytes,'table_and_index_bytes':size(location),'peak_process_rss_bytes':peaks['rss'],'measurements':measurements})
            save(OUT/f'ann-{a.limit}-results.json',result)
            print(json.dumps(result['profiles'][-1]),flush=True)
            del table,db; gc.collect()
    finally:
        stopped.set()
        result['run_dir']=str(folder)
        save(OUT/f'ann-{a.limit}-results.json',result)


if __name__=='__main__': main()
