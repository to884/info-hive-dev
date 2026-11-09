"""GPU 構築ベクトルと CPU 構築ベクトルの差を、同じ入力で独立に測る。"""
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json


def main():
    import numpy as np
    from rag_index import Embedder
    work=POC_DATA/'full-20261104'
    db=sqlite3.connect(work/'corpus.sqlite')
    db.execute('ATTACH DATABASE ? AS embeddings',(str(work/'embeddings-130m/ledger.sqlite'),))
    candidates=db.execute('SELECT c.embedding_text,e.position FROM chunks c JOIN embeddings.vectors e ON e.id=c.id ORDER BY c.id LIMIT 100000').fetchall()
    positions=np.random.default_rng(20261104).choice(len(candidates),32,replace=False)
    rows=[candidates[p] for p in positions]
    db.close()
    cfg=Config({'embedding_model':'cl-nagoya/ruri-v3-130m','model_cache_dir':str(POC_DATA/'model-cache'),'cpu_threads':4})
    embedder=Embedder(cfg)
    started=time.perf_counter()
    cpu=embedder.encode([r[0] for r in rows])
    seconds=time.perf_counter()-started
    gpu=np.memmap(work/'embeddings-130m/vectors.f32',mode='r',dtype=np.float32,shape=((work/'embeddings-130m/vectors.f32').stat().st_size//2048,512))[[r[1] for r in rows]]
    cosine=np.sum(cpu*gpu,axis=1)/(np.linalg.norm(cpu,axis=1)*np.linalg.norm(gpu,axis=1))
    write_json(ROOT/'docs/research/rag-validation-remaining-2026-11-04/embedding-device-drift.json',{'model':cfg.model,'revision':cfg.revision,'samples':len(rows),'cpu_embedding_seconds':seconds,'cosine_min':float(cosine.min()),'cosine_mean':float(cosine.mean()),'max_absolute_element_difference':float(np.max(np.abs(cpu-gpu))),'gpu_tf32':False,'note':'32件の数値差の標本。CPU による全量の構築時間や全入力の同一性を保証しない。'})


if __name__=='__main__': main()
