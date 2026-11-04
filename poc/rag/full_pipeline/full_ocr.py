"""固定した全資料の OCR 対象を処理し、ページごとに結果を確定して再開する。"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import multiprocessing as mp
import os
import queue
import sqlite3
import sys
import threading
import time
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,OCR_REVISION,write_json
BASE=ROOT/'.rag-poc-data/full-20261104'
WORK=ROOT/'.rag-poc-data/full-ocr-20261104'
OUT=ROOT/'docs/research/rag-full-pipeline-2026-11-04'
EVENTS=None
CLIENT=None
CFG=None

def fingerprint(device,threads):
    import importlib.metadata
    values={'revision':OCR_REVISION,'dpi':150,'threads':threads,'device':device,'runtime':'prepared_library_product_worker'}
    for name in ['numpy','onnxruntime','onnxruntime-gpu','networkx','Pillow','pypdfium2']:
        try: values[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: values[name]=None
    for name in ['rag_ocr.py','rag_ocr_client.py','rag_pdf.py']:
        values[name]=hashlib.sha256((ROOT/'info-hive-rag/scripts'/name).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(),values

def prepare(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS targets(doc_id TEXT,page INTEGER,status TEXT DEFAULT 'pending',
          attempts INTEGER DEFAULT 0,text TEXT,error TEXT,seconds REAL,pid INTEGER,line_count INTEGER,
          text_sha256 TEXT,PRIMARY KEY(doc_id,page));
        CREATE TABLE IF NOT EXISTS source_documents(doc_id TEXT PRIMARY KEY,relative_path TEXT,size INTEGER,mtime_ns INTEGER,pages INTEGER);
    ''')
    if db.execute('SELECT COUNT(*) FROM targets').fetchone()[0]: return
    source=sqlite3.connect(f'file:{(BASE/"corpus.sqlite").as_posix()}?mode=ro',uri=True)
    docs=source.execute("SELECT doc_id,MIN(relative_path),MAX(pages) FROM documents WHERE status='completed' GROUP BY doc_id").fetchall()
    for doc_id,relative,pages in docs:
        size,mtime=source.execute('SELECT size,mtime_ns FROM documents WHERE relative_path=?',(relative,)).fetchone()
        db.execute('INSERT INTO source_documents VALUES (?,?,?,?,?)',(doc_id,relative,size,mtime,pages))
    for doc_id,page in source.execute("SELECT p.doc_id,p.page FROM pages p WHERE json_extract(p.quality,'$.kind') IN ('scan','garbled','vertical') AND EXISTS (SELECT 1 FROM documents d WHERE d.doc_id=p.doc_id AND d.status='completed') ORDER BY p.doc_id,p.page"):
        db.execute('INSERT INTO targets(doc_id,page) VALUES (?,?)',(doc_id,page))
    db.commit(); source.close()

def initialize(events,work,device,threads):
    global EVENTS,CLIENT,CFG,WORK
    WORK=Path(work)
    EVENTS=events
    from rag_ocr_client import OcrClient
    CFG=Config({'data_dir':str(WORK/'runtime'/str(os.getpid())),'cpu_threads':threads,'ocr_dpi':150})
    CFG.data_dir.mkdir(parents=True,exist_ok=True)
    if device=='cuda': os.environ['INFO_HIVE_OCR_PROFILE_DIR']=str(WORK/'gpu-profiles')
    CLIENT=OcrClient(CFG,command=[sys.executable,str(ROOT/'poc/rag/remaining/ocr_local_runtime.py')],device=device)
    # 親の消失時に、認識中の子プロセスを含めて残さない。
    parent=mp.parent_process()
    def parent_closed():
        from multiprocessing.connection import wait
        wait([parent.sentinel])
        import psutil
        for child in reversed(psutil.Process().children(recursive=True)):
            try: child.kill()
            except psutil.NoSuchProcess: pass
        os._exit(0)
    threading.Thread(target=parent_closed,daemon=True).start()

def recognize_batch(task):
    import pypdfium2 as pdfium
    from rag_pdf import ocr_page
    relative,size,mtime,doc_id,numbers=task
    root=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))['root']
    path=Path(root)/relative
    def check():
        stat=path.stat()
        if (stat.st_size,stat.st_mtime_ns)!=(size,mtime): raise RuntimeError('原本のサイズまたは mtime が変わりました。')
    class Capture:
        last=None
        def recognize(self,image):
            self.last=CLIENT.recognize(image)
            return self.last
    capture=Capture()
    try:
        check()
        with pdfium.PdfDocument(path) as pdf:
            for number in numbers:
                started=time.perf_counter()
                try:
                    with closing(pdf[number-1]) as page:
                        text=ocr_page(page,CFG,CFG.data_dir,client=capture)
                    check()
                    EVENTS.put({'doc_id':doc_id,'page':number,'status':'completed' if text else 'empty','text':text,
                        'seconds':time.perf_counter()-started,'pid':capture.last['pid'],'line_count':capture.last['line_count'],
                        'gpu_execution':capture.last.get('gpu_execution')})
                except Exception as error:
                    EVENTS.put({'doc_id':doc_id,'page':number,'status':'failed','error':str(error),'seconds':time.perf_counter()-started})
    except Exception as error:
        for number in numbers:
            EVENTS.put({'doc_id':doc_id,'page':number,'status':'failed','error':str(error),'seconds':0})
    return len(numbers)

def main():
    global WORK
    parser=argparse.ArgumentParser(); parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--limit',type=int,default=0); parser.add_argument('--retry-failed',action='store_true')
    parser.add_argument('--workspace',type=Path,default=WORK); parser.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    parser.add_argument('--threads',type=int,default=2)
    args=parser.parse_args()
    WORK=args.workspace.resolve()
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    identity,policy=fingerprint(args.device,args.threads); meta=WORK/'ocr-policy.json'
    if meta.exists() and json.loads(meta.read_text(encoding='utf-8'))['fingerprint']!=identity:
        raise RuntimeError('OCR の実行方針またはコードが変わりました。異なる実行結果を混ぜて再開しません。')
    write_json(meta,{'fingerprint':identity,**policy})
    db=sqlite3.connect(WORK/'ocr.sqlite',timeout=60); db.execute('PRAGMA journal_mode=WAL')
    prepare(db)
    db.execute("UPDATE targets SET status='pending' WHERE status='running'")
    if args.retry_failed: db.execute("UPDATE targets SET status='pending',error=NULL WHERE status='failed'")
    db.commit()
    rows=db.execute("SELECT d.relative_path,d.size,d.mtime_ns,t.doc_id,t.page FROM targets t JOIN source_documents d USING(doc_id) WHERE t.status='pending' ORDER BY t.doc_id,t.page").fetchall()
    if args.limit: rows=rows[:args.limit]
    tasks=[]
    for row in rows:
        key=row[:4]
        if not tasks or tasks[-1][:4]!=key or len(tasks[-1][4])>=16: tasks.append((*key,[]))
        tasks[-1][4].append(row[4])
    expected=len(rows); received=0; remaining={(row[3],row[4]) for row in rows}; started=time.perf_counter(); last=0
    initial=db.execute("SELECT COUNT(*) FROM targets WHERE status IN ('completed','empty')").fetchone()[0]
    context=mp.get_context('spawn'); events=context.Queue(maxsize=64)
    peak=[0]; stopped=threading.Event()
    def memory():
        import psutil
        process=psutil.Process()
        while not stopped.wait(.2):
            total=0
            for child in [process,*process.children(recursive=True)]:
                try: total+=child.memory_info().rss
                except psutil.NoSuchProcess: pass
            peak[0]=max(peak[0],total)
    threading.Thread(target=memory,daemon=True).start()
    def progress():
        counts=dict(db.execute('SELECT status,COUNT(*) FROM targets GROUP BY status'))
        record={'fingerprint':identity,'target_pages':sum(counts.values()),'counts':counts,'new_pages_this_run':received,
            'completed_before_run':initial,'seconds_this_run':time.perf_counter()-started,'workers':args.workers,
            'sampled_peak_process_tree_rss_bytes':peak[0],'runtime':policy['runtime'],'dpi':150}
        write_json(WORK/'progress.json',record); write_json(OUT/'full-ocr-progress.json',record)
        print(json.dumps(record),flush=True)
        return record
    try:
        with concurrent.futures.ProcessPoolExecutor(args.workers,mp_context=context,initializer=initialize,initargs=(events,str(WORK),args.device,args.threads)) as pool:
            pending=iter(tasks); active={}
            def submit():
                task=next(pending,None)
                if task is None: return
                with db:
                    db.executemany("UPDATE targets SET status='running',attempts=attempts+1 WHERE doc_id=? AND page=?",[(task[3],page) for page in task[4]])
                active[pool.submit(recognize_batch,task)]=task
            for _ in range(args.workers): submit()
            while active or received<expected:
                try:
                    row=events.get(timeout=.2)
                    key=(row['doc_id'],row['page'])
                    if key not in remaining: continue
                    remaining.remove(key)
                    text=row.get('text','')
                    if row.get('gpu_execution'):
                        write_json(WORK/'gpu-evidence'/f'{row["pid"]}.json',row['gpu_execution'])
                    with db:
                        db.execute('UPDATE targets SET status=?,text=?,error=?,seconds=?,pid=?,line_count=?,text_sha256=? WHERE doc_id=? AND page=?',
                            (row['status'],text,row.get('error'),row['seconds'],row.get('pid'),row.get('line_count'),hashlib.sha256(text.encode('utf-8')).hexdigest(),row['doc_id'],row['page']))
                    received+=1
                except queue.Empty: pass
                for future in list(active):
                    if future.done():
                        future.result(); del active[future]; submit()
                if time.perf_counter()-last>15:
                    progress(); last=time.perf_counter()
        result=progress()
        if not result['counts'].get('pending',0) and not result['counts'].get('running',0):
            result['status']='completed' if not result['counts'].get('failed',0) else 'partial'
            write_json(WORK/'ocr-complete.json',result); write_json(OUT/'full-ocr-summary.json',result)
    finally:
        stopped.set(); db.close(); events.close()

if __name__=='__main__':
    os.environ['PYTHONUTF8']='1'; os.environ['PYTHONIOENCODING']='utf-8'; os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['OMP_NUM_THREADS']='1'; os.environ['OPENBLAS_NUM_THREADS']='1'
    main()
