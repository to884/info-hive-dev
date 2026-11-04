"""実モデルで 2,048 トークンを超える入力が切り捨てられないことを確認する。"""
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_index import Embedder


def main():
    import numpy as np
    work=ROOT/'.rag-poc-data/full-20261104'
    db=sqlite3.connect(work/'corpus.sqlite')
    text=db.execute('SELECT embedding_text FROM chunks WHERE id=474293').fetchone()[0]; db.close()
    cfg=Config({'embedding_model':'cl-nagoya/ruri-v3-30m','model_cache_dir':str(ROOT/'.rag-poc-data/model-cache'),'cpu_threads':4})
    embedder=Embedder(cfg)
    expected=len(embedder.model.tokenizer('検索文書: '+text,truncation=False)['input_ids'])
    seen=[]; original=embedder.model.preprocess
    def observed(*args,**kwargs):
        features=original(*args,**kwargs)
        seen.append(int(features['attention_mask'].sum().item()))
        return features
    embedder.model.preprocess=observed
    start=time.perf_counter()
    try: vector=embedder.encode([text])
    finally: embedder.model.preprocess=original
    seconds=time.perf_counter()-start
    passed=expected>2048 and max(seen,default=0)==expected and vector.shape==(1,cfg.dimension) and np.isfinite(vector).all()
    result={'passed':bool(passed),'model':cfg.model,'revision':cfg.revision,'device':'cpu','source_chunk_id':474293,'input_tokens':expected,'observed_tokens':seen,'model_limit':embedder.model.max_seq_length,'output_shape':list(vector.shape),'vector_norm':float(np.linalg.norm(vector[0])),'seconds':seconds}
    write_json(ROOT/'docs/research/rag-validation-remaining-2026-11-04/native-context-results.json',result)
    print(json.dumps(result),flush=True)
    assert passed


if __name__=='__main__': main()
