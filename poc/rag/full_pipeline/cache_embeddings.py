"""同じ入力の確定ベクトルを再利用し、OCR で変わった入力だけを埋め込む。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
BASE=POC_DATA/'full-20261104'
WORK=POC_DATA/'full-ocr-index-20261104'
OCR=POC_DATA/'full-ocr-gpu-20261104'
OUT=ROOT/'docs/research/rag-full-pipeline-2026-11-04'
MODEL='cl-nagoya/ruri-v3-130m'
REVISION='e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6'

def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(8*1024*1024): result.update(block)
    return result.hexdigest()

def initialize():
    WORK.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(WORK/'embedding-cache.sqlite',timeout=60)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''CREATE TABLE IF NOT EXISTS cache(input_hash TEXT PRIMARY KEY,position INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS chunk_vectors(id INTEGER PRIMARY KEY,input_hash TEXT,position INTEGER);
      CREATE TABLE IF NOT EXISTS pending(input_hash TEXT PRIMARY KEY,text TEXT);
      CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value INTEGER);''')
    if db.execute("SELECT value FROM meta WHERE key='next_position'").fetchone() is None:
        complete=json.loads((BASE/'embeddings-130m/complete.json').read_text(encoding='utf-8'))
        assert complete['model']==MODEL and complete['revision']==REVISION and complete['dimension']==512
        source=BASE/'embeddings-130m/vectors.f32'
        assert source.stat().st_size==complete['vectors_including_retired_ids']*2048
        value=digest(source)
        if not (WORK/'vectors.f32').exists():
            temporary=WORK/f'vectors-{uuid.uuid4().hex}.f32'
            shutil.copyfile(source,temporary)
            assert digest(temporary)==value
            temporary.replace(WORK/'vectors.f32')
        else: assert digest(WORK/'vectors.f32')==value
        db.execute('ATTACH DATABASE ? AS seed',(f'file:{(BASE/"embeddings-130m/ledger.sqlite").as_posix()}?mode=ro',))
        with db:
            db.execute('INSERT OR IGNORE INTO cache SELECT input_hash,MIN(position) FROM seed.vectors GROUP BY input_hash')
            db.execute("INSERT INTO meta VALUES ('next_position',?)",(complete['vectors_including_retired_ids'],))
            db.execute("INSERT INTO meta VALUES ('last_chunk_id',-1)")
        db.execute('DETACH DATABASE seed')
        write_json(WORK/'embedding-seed.json',{'model':MODEL,'revision':REVISION,'dimension':512,'raw_vector_sha256':value,'base_rows':complete['vectors_including_retired_ids']})
    return db

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--watch',action='store_true'); args=parser.parse_args()
    db=initialize(); cache=dict(db.execute('SELECT input_hash,position FROM cache'))
    started=time.perf_counter(); prepared=0; reused=0
    try:
        while True:
            if not (WORK/'corpus.sqlite').exists(): time.sleep(10); continue
            source=sqlite3.connect(f'file:{(WORK/"corpus.sqlite").as_posix()}?mode=ro',uri=True,timeout=60)
            last=db.execute("SELECT value FROM meta WHERE key='last_chunk_id'").fetchone()[0]
            rows=source.execute('SELECT c.id,c.embedding_text FROM chunks c JOIN pipeline_documents d USING(doc_id) WHERE d.ready=1 AND c.id>? ORDER BY c.id LIMIT 2048',(last,)).fetchall()
            source.close()
            if rows:
                with db:
                    for identity,text in rows:
                        key=hashlib.sha256(text.encode('utf-8')).hexdigest(); position=cache.get(key)
                        db.execute('INSERT OR REPLACE INTO chunk_vectors VALUES (?,?,?)',(identity,key,position))
                        if position is None: db.execute('INSERT OR IGNORE INTO pending VALUES (?,?)',(key,text))
                        else: reused+=1
                    db.execute("UPDATE meta SET value=? WHERE key='last_chunk_id'",(rows[-1][0],))
                prepared+=len(rows)
            if prepared%32768<2048 or not rows:
                record={'prepared_chunks':db.execute('SELECT COUNT(*) FROM chunk_vectors').fetchone()[0],
                    'reused_chunks':db.execute('SELECT COUNT(*) FROM chunk_vectors WHERE position IS NOT NULL').fetchone()[0],
                    'pending_unique_inputs':db.execute('SELECT COUNT(*) FROM pending').fetchone()[0],
                    'seconds_this_run':time.perf_counter()-started,'model':MODEL,'revision':REVISION}
                write_json(OUT/'embedding-cache-progress.json',record); write_json(WORK/'embedding-progress.json',record)
                print(json.dumps(record),flush=True)
            if not rows:
                if (WORK/'corpus-complete.json').exists(): break
                if not args.watch: return
                time.sleep(30)
        # OCR の GPU プロセスを終えてから埋め込みモデルを読み込む。
        import psutil
        while True:
            active=[]
            for process in psutil.process_iter(['cmdline']):
                command=process.info['cmdline'] or []
                if 'cuda' in command and any(arg.replace('\\','/').endswith('/ocr_local_runtime.py') for arg in command): active.append(process.pid)
            if not active: break
            time.sleep(5)
        import numpy as np
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(2); torch.set_num_interop_threads(1)
        if not torch.cuda.is_available(): raise RuntimeError('文書の GPU 埋め込みが利用できません。')
        torch.cuda.set_per_process_memory_fraction(.45)
        torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
        model=SentenceTransformer(MODEL,revision=REVISION,device='cuda',cache_folder=str(POC_DATA/'model-cache'),model_kwargs={'attn_implementation':'sdpa'})
        model.max_seq_length=min(int(model[0].auto_model.config.max_position_embeddings),8192)
        position=db.execute("SELECT value FROM meta WHERE key='next_position'").fetchone()[0]
        maximum=0; encoded=0; gpu_started=time.perf_counter()
        with (WORK/'vectors.f32').open('r+b') as stream:
            if stream.seek(0,2)<position*2048: raise RuntimeError('ベクトルファイルが確定台帳より短くなっています。')
            stream.truncate(position*2048); stream.seek(0,2)
            while True:
                rows=db.execute('SELECT input_hash,text FROM pending ORDER BY rowid LIMIT 128').fetchall()
                if not rows: break
                inputs=['検索文書: '+text for _,text in rows]
                lengths=[len(ids) for ids in model.tokenizer(inputs,truncation=False,padding=False)['input_ids']]
                maximum=max(maximum,max(lengths))
                if max(lengths)>model.max_seq_length: raise RuntimeError('OCR 後の入力がモデルの上限を超えています。本文を切り詰めず分割を確認してください。')
                batch=max(1,min(32,(32*1536**2)//max(lengths)**2))
                try: vectors=model.encode(inputs,batch_size=batch,normalize_embeddings=True,show_progress_bar=False).astype(np.float32)
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache(); vectors=model.encode(inputs,batch_size=1,normalize_embeddings=True,show_progress_bar=False).astype(np.float32)
                assert vectors.shape==(len(rows),512) and np.isfinite(vectors).all()
                stream.write(vectors.tobytes()); stream.flush(); os.fsync(stream.fileno())
                with db:
                    db.executemany('INSERT INTO cache VALUES (?,?)',[(key,position+i) for i,(key,_) in enumerate(rows)])
                    db.executemany('DELETE FROM pending WHERE input_hash=?',[(key,) for key,_ in rows])
                    position+=len(rows); encoded+=len(rows)
                    db.execute("UPDATE meta SET value=? WHERE key='next_position'",(position,))
                if encoded%2048==0:
                    write_json(OUT/'new-embedding-progress.json',{'encoded_new_unique_inputs':encoded,'seconds_this_run':time.perf_counter()-gpu_started,'max_input_tokens':maximum,'device':'cuda'})
        with db:
            db.execute('UPDATE chunk_vectors SET position=(SELECT position FROM cache WHERE cache.input_hash=chunk_vectors.input_hash) WHERE position IS NULL')
        assert db.execute('SELECT COUNT(*) FROM chunk_vectors WHERE position IS NULL').fetchone()[0]==0
        with sqlite3.connect(WORK/'corpus.sqlite') as source:
            total=source.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
        assert total==db.execute('SELECT COUNT(*) FROM chunk_vectors').fetchone()[0]
        result={'status':'completed','chunks':total,'model':MODEL,'revision':REVISION,'dimension':512,'new_unique_inputs_this_run':encoded,
            'stored_vector_rows':position,'raw_vector_sha256':digest(WORK/'vectors.f32'),'max_input_tokens_this_run':maximum,
            'gpu_seconds_this_run':time.perf_counter()-gpu_started,'gpu_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'document_embedding_device':'cuda'}
        write_json(WORK/'embeddings-complete.json',result); write_json(OUT/'embedding-summary.json',result)
    finally: db.close()

if __name__=='__main__':
    os.environ['PYTHONUTF8']='1'; os.environ['PYTHONIOENCODING']='utf-8'; os.environ['PYTHONDONTWRITEBYTECODE']='1'
    main()
