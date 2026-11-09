"""全量の確定ベクトルと本文を製品検索用の形式へ投入し、ANN と FTS を作る。"""
import hashlib
import json
import math
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from provenance import full_fingerprint,lexical_fingerprint
WORK=POC_DATA/'full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def build_index(memory_peak):
    os.environ['RAYON_NUM_THREADS']='4'
    os.environ['OMP_NUM_THREADS']='4'
    extraction=json.loads((WORK/'extraction-complete.json').read_text(encoding='utf-8'))
    embedded=json.loads((WORK/'embeddings-130m/complete.json').read_text(encoding='utf-8'))
    if extraction['status']!='completed' or embedded.get('status')!='completed':
        raise RuntimeError('全量抽出と埋め込みの正常終了が必要です。')
    import numpy as np
    from rag_index import Engine
    manifest=json.loads((WORK/'manifest.json').read_text(encoding='utf-8'))
    wiki=WORK/'product-wiki'
    (wiki/'sources').mkdir(parents=True,exist_ok=True)
    (wiki/'SCHEMA.md').write_text('# 全量索引の検証\n',encoding='utf-8')
    if embedded['model']!='cl-nagoya/ruri-v3-130m' or embedded['dimension']!=512:
        raise RuntimeError('埋め込みモデルまたは次元数が全量索引の設定と一致しません。')
    fingerprint=full_fingerprint()
    previous=WORK/'product-import.json'
    if previous.exists() and json.loads(previous.read_text(encoding='utf-8')).get('source_fingerprint')!=fingerprint:
        raise RuntimeError('再開元のコーパスまたは埋め込みが変更されています。別の保存先で構築してください。')
    values={'reference_roots':{'books':manifest['root']},'data_dir':str(WORK/'product-data'),'model_cache_dir':str(POC_DATA/'model-cache'),'embedding_model':embedded['model'],'embedding_revision':embedded['revision'],'cpu_threads':4,'search_nprobes':128,'search_refine_factor':4,'reranker':'off'}
    config_file=WORK/'product-config.json'; write_json(config_file,values)
    cfg=Config(values); engine=Engine(cfg); folder=cfg.workspace(str(wiki))
    engine._check_policy(folder); table=engine._table(folder,create=True)
    db=sqlite3.connect(WORK/'corpus.sqlite',timeout=60)
    db.execute('CREATE INDEX IF NOT EXISTS documents_by_doc_id ON documents(doc_id)')
    db.commit()
    db.execute('ATTACH DATABASE ? AS embeddings',(str(WORK/'embeddings-130m/ledger.sqlite'),))
    cached_terms=(WORK/'terms-complete.json').exists()
    if cached_terms:
        if json.loads((WORK/'terms-complete.json').read_text(encoding='utf-8'))['lexical_fingerprint']!=lexical_fingerprint():
            raise RuntimeError('準備済みの語彙検索設定が異なります。')
        db.execute('ATTACH DATABASE ? AS lexical',(str(WORK/'terms.sqlite'),))
    source_count=db.execute('SELECT COUNT(*) FROM chunks c WHERE EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=c.doc_id AND d.status=\'completed\')').fetchone()[0]
    joined=db.execute('SELECT COUNT(*) FROM chunks c JOIN embeddings.vectors e ON e.id=c.id WHERE EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=c.doc_id AND d.status=\'completed\')').fetchone()[0]
    if joined!=source_count: raise RuntimeError('未埋め込みのチャンクがあります。')
    vector_file=WORK/'embeddings-130m/vectors.f32'
    vectors=np.memmap(vector_file,mode='r',dtype=np.float32,shape=(vector_file.stat().st_size//2048,512))
    checkpoint=WORK/'product-import.json'
    saved=json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {}
    last_id=saved.get('last_id',-1)
    imported=table.count_rows()
    repair=imported!=saved.get('completed_rows',0)
    started=time.perf_counter()
    while True:
        rows=db.execute('SELECT c.id,c.doc_id,c.page,c.text,c.embedding_text,e.position,e.input_hash FROM chunks c JOIN embeddings.vectors e ON e.id=c.id WHERE c.id>? AND EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=c.doc_id AND d.status=\'completed\') ORDER BY c.id LIMIT 2048',(last_id,)).fetchall()
        if not rows: break
        batch=[]
        prepared={r[0]:(r[1],r[2]) for r in db.execute('SELECT id,input_hash,terms FROM lexical.terms WHERE id>? AND id<=?',(last_id,rows[-1][0]))} if cached_terms else {}
        for identity,doc_id,page,text,embedding_text,position,input_hash in rows:
            if hashlib.sha256(embedding_text.encode('utf-8')).hexdigest()!=input_hash:
                raise RuntimeError('台帳の埋め込み入力ハッシュが一致しません。')
            title=embedding_text.split('\n',1)[0]
            section=embedding_text[len(title)+1:-(len(text)+1)]
            generation=hashlib.sha256((doc_id+cfg.fingerprint).encode()).hexdigest()
            if cached_terms and (identity not in prepared or prepared[identity][0]!=input_hash):
                raise RuntimeError('語彙検索用の入力ハッシュが一致しません。')
            normalized=prepared[identity][1] if cached_terms else engine.tokenize(embedding_text)
            batch.append({'chunk_id':f'{generation}:{identity}','doc_id':doc_id,'generation':generation,'page':page,'section':section,'title':title,'text':text,'terms':normalized,'vector':vectors[position].tolist()})
        if repair:
            # テーブル追加直後、台帳保存前に終了した一つのバッチだけを修復する。
            table.merge_insert('chunk_id').when_matched_update_all().when_not_matched_insert_all().execute(batch)
            imported=table.count_rows(); repair=False
        else:
            table.add(batch); imported+=len(batch)
        last_id=rows[-1][0]
        write_json(checkpoint,{'last_id':last_id,'completed_rows':imported,'total_expected':source_count,'source_fingerprint':fingerprint,'seconds_this_run':time.perf_counter()-started})
        print(json.dumps({'phase':'import','last_id':last_id,'total_expected':source_count,'seconds':time.perf_counter()-started}),flush=True)
    if table.count_rows()!=source_count: raise RuntimeError('投入件数が一致しません。')
    fts_start=time.perf_counter()
    if not any(i.index_type=='FTS' for i in table.list_indices()):
        table.create_fts_index('terms',base_tokenizer='whitespace',stem=False,remove_stop_words=False,ascii_folding=False)
    fts_seconds=time.perf_counter()-fts_start
    ann_start=time.perf_counter(); partitions=max(4,min(4096,math.ceil(math.sqrt(source_count))))
    if not any('vector' in i.columns for i in table.list_indices()):
        table.create_index(vector_column_name='vector',metric='cosine',index_type='IVF_SQ',num_partitions=partitions)
    ann_seconds=time.perf_counter()-ann_start
    with engine._catalog(folder) as catalog:
        documents=db.execute("SELECT doc_id,MIN(relative_path),MAX(pages) FROM documents WHERE status='completed' GROUP BY doc_id").fetchall()
        for doc_id,relative,pages in documents:
            generation=hashlib.sha256((doc_id+cfg.fingerprint).encode()).hexdigest()
            count=db.execute('SELECT COUNT(*) FROM chunks WHERE doc_id=?',(doc_id,)).fetchone()[0]
            catalog.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?)',(doc_id,generation,Path(relative).stem,'books',relative,pages,count,cfg.fingerprint,time.time()))
            catalog.execute('INSERT OR IGNORE INTO citations VALUES (?,?)',(doc_id,'sources/'+doc_id+'.md'))
        for relative,size,mtime,doc_id in db.execute("SELECT relative_path,size,mtime_ns,doc_id FROM documents WHERE status='completed'"):
            catalog.execute('INSERT OR REPLACE INTO locations VALUES (?,?,?,?,?)',('books',relative,doc_id,size,mtime))
    db.close()
    disk_bytes=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
    write_json(OUT/'full-product-index.json',{'source_fingerprint':fingerprint,'documents':len(documents),'chunks':source_count,'num_partitions':partitions,'vector_index':'IVF_SQ','index_selection':'10万実ベクトルで IVF_PQ より ANN 再現率が高く、今回の容量予算内だった方式を全量検証に使用。最終採用ではない。','import_seconds_this_run':fts_start-started,'fts_seconds_this_run':fts_seconds,'ann_seconds_this_run':ann_seconds,'index_bytes':disk_bytes,'sampled_peak_process_rss_bytes':memory_peak[0],'rss_sample_interval_ms':50,'data_dir':str(folder),'config':str(config_file),'native_text_only':True,'source_pdf_ingest_e2e':False,'model':cfg.model,'revision':cfg.revision,'document_embedding_device':embedded['device'],'search_device':'cpu'})
    write_json(WORK/'product-index-complete.json',{'source_fingerprint':fingerprint,'config':str(config_file),'wiki':str(wiki)})


def main():
    import psutil
    process=psutil.Process()
    memory_peak=[process.memory_info().rss]
    stopped=threading.Event()
    def monitor():
        while not stopped.wait(.05):
            memory_peak[0]=max(memory_peak[0],process.memory_info().rss)
    thread=threading.Thread(target=monitor,daemon=True)
    thread.start()
    try:
        build_index(memory_peak)
    finally:
        stopped.set(); thread.join(timeout=1)


if __name__=='__main__': main()
