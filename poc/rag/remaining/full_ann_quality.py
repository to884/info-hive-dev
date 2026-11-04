"""全量索引で、実際の質問ベクトルに対する ANN と厳密検索を比べる。"""
import json
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def main():
    os.environ['RAYON_NUM_THREADS']='4'; os.environ['OMP_NUM_THREADS']='4'
    import numpy as np
    import psutil
    from threadpoolctl import threadpool_limits
    from rag_index import Embedder,Engine
    threadpool_limits(4)
    stopped=threading.Event(); peak=[0]
    def monitor():
        process=psutil.Process()
        while not stopped.wait(.05): peak[0]=max(peak[0],process.memory_info().rss)
    threading.Thread(target=monitor,daemon=True).start()
    try:
        cfg=Config(json.loads((WORK/'product-config.json').read_text(encoding='utf-8')))
        queries=json.loads((WORK/'corpus.json').read_text(encoding='utf-8'))['queries']
        started=time.perf_counter()
        query_vectors=Embedder(cfg).encode([q['query'] for q in queries],query=True).astype(np.float32)
        embedding_seconds=time.perf_counter()-started
        db=sqlite3.connect(WORK/'corpus.sqlite')
        db.execute('ATTACH DATABASE ? AS embeddings',(str(WORK/'embeddings-130m/ledger.sqlite'),))
        mapping=db.execute("SELECT c.id,e.position FROM chunks c JOIN embeddings.vectors e ON e.id=c.id WHERE EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=c.doc_id AND d.status='completed') ORDER BY c.id").fetchall()
        db.close()
        ids=np.array([r[0] for r in mapping],dtype=np.int64)
        raw=WORK/'embeddings-130m/vectors.f32'
        mapped=np.memmap(raw,mode='r',dtype=np.float32,shape=(raw.stat().st_size//2048,512))
        vectors=np.array(mapped[[r[1] for r in mapping]],dtype=np.float32)
        del mapped,mapping
        norms=np.sqrt(np.einsum('ij,ij->i',vectors,vectors))
        started=time.perf_counter()
        scores=query_vectors@vectors.T/norms
        exact_seconds=time.perf_counter()-started
        exact=[set(ids[np.argpartition(-row,29)[:30]].tolist()) for row in scores]
        thresholds=[float(np.partition(row,-30)[-30]) for row in scores]
        engine=Engine(cfg)
        table=engine._table(cfg.workspace(str(WORK/'product-wiki')))
        sweep=[]
        for probes in sorted({20,64,cfg.search_nprobes}):
            measurements=[]
            # 同じ問い合わせを一巡させ、索引読み込みを計時から分ける。
            for vector in query_vectors:
                table.search(vector).distance_type('cosine').nprobes(probes).refine_factor(cfg.search_refine_factor).limit(30).select(['chunk_id']).to_list()
            for i,(query,vector) in enumerate(zip(queries,query_vectors)):
                started=time.perf_counter()
                found=table.search(vector).distance_type('cosine').nprobes(probes).refine_factor(cfg.search_refine_factor).limit(30).select(['chunk_id']).to_list()
                ms=(time.perf_counter()-started)*1000
                found_ids=[int(r['chunk_id'].rsplit(':',1)[1]) for r in found]
                positions=np.searchsorted(ids,found_ids)
                measurements.append({'id':query['id'],'milliseconds':ms,'id_recall_at_30':len(set(found_ids)&exact[i])/30,'tie_aware_recall_at_30':sum(scores[i,position]>=thresholds[i]-1e-6 for position in positions)/30})
            sweep.append({'nprobes':probes,'refine_factor':cfg.search_refine_factor,'p95_ms':float(np.quantile([r['milliseconds'] for r in measurements],.95)),'mean_id_recall_at_30':float(np.mean([r['id_recall_at_30'] for r in measurements])),'mean_tie_aware_recall_at_30':float(np.mean([r['tie_aware_recall_at_30'] for r in measurements])),'measurements':measurements})
        selected=next(result for result in sweep if result['nprobes']==cfg.search_nprobes)
        write_json(OUT/'full-ann-quality.json',{'rows':len(ids),'queries':len(queries),'model':cfg.model,'revision':cfg.revision,'query_embedding_device':'cpu','query_batch_load_and_embedding_seconds':embedding_seconds,'exact_matrix_seconds':exact_seconds,**selected,'probe_sweep':sweep,'tie_tolerance':1e-6,'peak_process_rss_bytes':peak[0],'scope':'全量索引に対する ANN 部分のみ。質問の正解ページ再現率や MCP 全体の時間とは別。'})
    finally: stopped.set()


if __name__=='__main__': main()
