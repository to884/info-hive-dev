"""原本を複製せず並列に読み、主プロセスだけが SQLite の確定結果を保存する。"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_pdf import inspect_page,chunks_for
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def extract(task):
    import pypdfium2 as pdfium
    root,item=task
    path=Path(root)/item['relative_path']
    before=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(item['bytes'],item['mtime_ns']):
        raise RuntimeError('原資料が検証開始時の一覧から変わりました。')
    started=time.perf_counter()
    payload=path.read_bytes()
    read_seconds=time.perf_counter()-started
    digest=hashlib.sha256(payload).hexdigest()
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise RuntimeError('読み込み中に原資料が変わりました。')
    cfg=Config({'embedding_model':'cl-nagoya/ruri-v3-130m'})
    pages,chunk_rows,kinds=[],[],collections.Counter()
    started=time.perf_counter()
    previous_section=''
    with pdfium.PdfDocument(payload) as pdf:
        for i in range(len(pdf)):
            with closing(pdf[i]) as page: text,quality=inspect_page(page)
            pages.append((digest,i+1,text,json.dumps(quality,ensure_ascii=False)))
            kinds[quality['kind']]+=1
            for number,chunk in enumerate(chunks_for([{'page':i+1,'text':text}],path.stem,cfg)):
                section=chunk['section'] or previous_section
                previous_section=section
                chunk_rows.append((digest,i+1,number,chunk['text'],f"{path.stem}\n{section}\n{chunk['text']}"))
    del payload
    return {'item':item,'digest':digest,'pages':pages,'chunks':chunk_rows,'text_bytes':sum(len(p[2].encode('utf-8')) for p in pages),'kinds':dict(kinds),'read_seconds':read_seconds,'extract_seconds':time.perf_counter()-started}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--workers',type=int,default=3); parser.add_argument('--max-new',type=int,default=0); args=parser.parse_args()
    manifest=json.loads((WORK/'manifest.json').read_text(encoding='utf-8'))
    db=sqlite3.connect(WORK/'corpus.sqlite',timeout=60)
    db.execute('PRAGMA journal_mode=WAL')
    done={r[0]:(r[1],r[2],r[3]) for r in db.execute('SELECT relative_path,size,mtime_ns,status FROM documents')}
    pending=[item for item in manifest['files'] if not item['cloud_only'] and done.get(item['relative_path'])!=(item['bytes'],item['mtime_ns'],'completed')]
    all_pending=len(pending)
    if args.max_new: pending=pending[:args.max_new]
    started=time.perf_counter(); initial=len(done); new=0
    import psutil
    stopped=threading.Event(); peak=[0]
    def monitor():
        parent=psutil.Process()
        while not stopped.wait(.1):
            total=0
            for p in [parent]+parent.children(recursive=True):
                try: total+=p.memory_info().rss
                except psutil.NoSuchProcess: pass
            peak[0]=max(peak[0],total)
    threading.Thread(target=monitor,daemon=True).start()
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            iterator=iter(pending)
            active={}
            def submit():
                item=next(iterator,None)
                if item is not None: active[pool.submit(extract,(manifest['root'],item))]=item
            for _ in range(args.workers): submit()
            while active:
                finished,_=concurrent.futures.wait(active,timeout=30,return_when=concurrent.futures.FIRST_COMPLETED)
                if not finished:
                    print(json.dumps({'phase':'reading_or_extracting','active':len(active),'new_documents':new,'seconds':time.perf_counter()-started}),flush=True)
                for future in finished:
                    item=active.pop(future)
                    try:
                        result=future.result()
                        with db:
                            db.executemany('INSERT OR REPLACE INTO pages VALUES (?,?,?,?)',result['pages'])
                            db.executemany('INSERT OR REPLACE INTO chunks(doc_id,page,number,text,embedding_text) VALUES (?,?,?,?,?)',result['chunks'])
                            db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',(item['relative_path'],item['bytes'],item['mtime_ns'],result['digest'],len(result['pages']),result['text_bytes'],len(result['chunks']),result['read_seconds'],result['extract_seconds'],'completed',None))
                        new+=1
                        print(json.dumps({'phase':'extracted','new_documents':new,'pages':len(result['pages']),'read_seconds':result['read_seconds'],'extract_seconds':result['extract_seconds'],'kinds':result['kinds']}),flush=True)
                        del result
                    except Exception as error:
                        with db: db.execute('INSERT OR REPLACE INTO documents(relative_path,size,mtime_ns,status,error) VALUES (?,?,?,?,?)',(item['relative_path'],item['bytes'],item['mtime_ns'],'failed',str(error)))
                        print(json.dumps({'phase':'failed','error':str(error)}),flush=True)
                    totals=db.execute("SELECT COUNT(*),SUM(size),SUM(pages),SUM(text_bytes),SUM(chunks) FROM documents WHERE status='completed'").fetchone()
                    progress={'completed_files':totals[0],'source_bytes':totals[1],'pages':totals[2],'text_bytes':totals[3],'chunks_before_dedup':totals[4],'distinct_chunks':db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0],'failed_files':db.execute("SELECT COUNT(*) FROM documents WHERE status='failed'").fetchone()[0],'wall_seconds_this_run':time.perf_counter()-started,'parallel_workers':args.workers,'peak_extraction_process_tree_rss_bytes':peak[0],'extraction_includes_ocr':False}
                    write_json(WORK/'progress.json',progress); write_json(OUT/'full-extraction-progress.json',progress)
                    submit()
        if len(pending)==all_pending:
            failed=db.execute("SELECT COUNT(*) FROM documents WHERE status='failed'").fetchone()[0]
            write_json(WORK/'extraction-complete.json',{'status':'completed' if not failed else 'partial','failed_files':failed,'include_cloud':False,'ocr_included':False})
    finally:
        stopped.set(); db.close()


if __name__=='__main__': main()
