"""FP32 のまま GPU 文書構築バッチの速度と数値差を少量で確認する。"""
import json
import os
import sqlite3
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'.rag-poc-data/full-20261104'


def main():
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TOKENIZERS_PARALLELISM']='false'
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    torch.cuda.set_per_process_memory_fraction(.3)
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    model=SentenceTransformer('cl-nagoya/ruri-v3-130m',revision='e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6',device='cuda',cache_folder=str(ROOT/'.rag-poc-data/model-cache'),model_kwargs={'attn_implementation':'sdpa'})
    model.max_seq_length=2048
    db=sqlite3.connect(WORK/'corpus.sqlite')
    texts=['検索文書: '+r[0] for r in db.execute('SELECT embedding_text FROM chunks ORDER BY id LIMIT 128 OFFSET 20000')]; db.close()
    lengths=[len(t) for t in model.tokenizer(texts,truncation=False,padding=False)['input_ids']]
    texts=[texts[i] for i in np.argsort(lengths)]
    model.encode(texts[:1],normalize_embeddings=True,batch_size=1,show_progress_bar=False)
    results=[]; baseline=None
    for batch in [8,16,32]:
        try:
            torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
            start=time.perf_counter()
            vector=model.encode(texts,normalize_embeddings=True,batch_size=batch,show_progress_bar=False,convert_to_numpy=True)
            torch.cuda.synchronize(); elapsed=time.perf_counter()-start
            if baseline is None: baseline=vector
            cosine=np.sum(baseline*vector,axis=1)/(np.linalg.norm(baseline,axis=1)*np.linalg.norm(vector,axis=1))
            results.append({'batch_size':batch,'seconds':elapsed,'documents_per_second':len(texts)/elapsed,'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated(),'cosine_min_vs_batch8':float(cosine.min()),'max_absolute_difference_vs_batch8':float(np.max(np.abs(baseline-vector)))})
        except torch.cuda.OutOfMemoryError:
            results.append({'batch_size':batch,'out_of_memory':True}); torch.cuda.empty_cache()
        print(json.dumps(results[-1]),flush=True)
    (ROOT/'docs/research/rag-validation-remaining-2026-11-04/gpu-batch-probe.json').write_text(json.dumps({'samples':len(texts),'max_tokens':max(lengths),'dtype':'float32','tf32':False,'other_gpu_builder_running':True,'results':results},indent=2),encoding='utf-8')


if __name__=='__main__': main()
