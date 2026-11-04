"""保存した native 本文と全量 OCR を統合し、製品と同じ方法で再分割する。"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_pdf import chunks_for
BASE=ROOT/'.rag-poc-data/full-20261104'
OCR=ROOT/'.rag-poc-data/full-ocr-gpu-20261104'
WORK=ROOT/'.rag-poc-data/full-ocr-index-20261104'
OUT=ROOT/'docs/research/rag-full-pipeline-2026-11-04'

def initialize():
    WORK.mkdir(parents=True,exist_ok=True)
    if not (WORK/'corpus.sqlite').exists():
        temporary=WORK/f'corpus-{uuid.uuid4().hex}.sqlite'
        source=sqlite3.connect(f'file:{(BASE/"corpus.sqlite").as_posix()}?mode=ro',uri=True)
        target=sqlite3.connect(temporary); source.backup(target)
        target.close(); source.close(); temporary.replace(WORK/'corpus.sqlite')
    db=sqlite3.connect(WORK/'corpus.sqlite',timeout=60)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''CREATE TABLE IF NOT EXISTS pipeline_documents(
        doc_id TEXT PRIMARY KEY,relative_path TEXT,title TEXT,ocr_pages INTEGER,
        ready INTEGER DEFAULT 0,chunks INTEGER,empty_pdf INTEGER DEFAULT 0,error TEXT);
        CREATE TABLE IF NOT EXISTS ocr_applied(doc_id TEXT,page INTEGER,text_sha256 TEXT,status TEXT,
          PRIMARY KEY(doc_id,page));''')
    if not db.execute('SELECT COUNT(*) FROM pipeline_documents').fetchone()[0]:
        with sqlite3.connect(f'file:{(OCR/"ocr.sqlite").as_posix()}?mode=ro',uri=True) as ocr:
            counts=dict(ocr.execute('SELECT doc_id,COUNT(*) FROM targets GROUP BY doc_id'))
        for identity,relative in db.execute("SELECT doc_id,MIN(relative_path) FROM documents WHERE status='completed' GROUP BY doc_id").fetchall():
            db.execute('INSERT INTO pipeline_documents(doc_id,relative_path,title,ocr_pages) VALUES (?,?,?,?)',
                (identity,relative,Path(relative).stem,counts.get(identity,0)))
        db.commit()
    return db

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--watch',action='store_true'); args=parser.parse_args()
    db=initialize(); cfg=Config({'embedding_model':'cl-nagoya/ruri-v3-130m'})
    started=time.perf_counter(); merged=0
    try:
        while True:
            progressed=False
            with sqlite3.connect(f'file:{(OCR/"ocr.sqlite").as_posix()}?mode=ro',uri=True) as ocr:
                ready_counts=dict(ocr.execute("SELECT doc_id,COUNT(*) FROM targets WHERE status IN ('completed','empty') GROUP BY doc_id"))
                for identity,title,needed in db.execute('SELECT doc_id,title,ocr_pages FROM pipeline_documents WHERE ready=0 ORDER BY ocr_pages,doc_id').fetchall():
                    if ready_counts.get(identity,0)!=needed: continue
                    results=ocr.execute("SELECT page,text,text_sha256,status FROM targets WHERE doc_id=? AND status IN ('completed','empty') ORDER BY page",(identity,)).fetchall()
                    with db:
                        for page,text,digest,status in results:
                            db.execute('UPDATE pages SET text=? WHERE doc_id=? AND page=?',(text,identity,page))
                            db.execute('INSERT OR REPLACE INTO ocr_applied VALUES (?,?,?,?)',(identity,page,digest,status))
                        pages=[{'page':page,'text':text} for page,text in db.execute('SELECT page,text FROM pages WHERE doc_id=? ORDER BY page',(identity,))]
                        chunks=chunks_for(pages,title,cfg)
                        numbers=collections.Counter(); rows=[]
                        for chunk in chunks:
                            page=chunk['page']; number=numbers[page]; numbers[page]+=1
                            rows.append((identity,page,number,chunk['text'],chunk['embedding_text']))
                        db.execute('DELETE FROM chunks WHERE doc_id=?',(identity,))
                        db.executemany('INSERT INTO chunks(doc_id,page,number,text,embedding_text) VALUES (?,?,?,?,?)',rows)
                        db.execute('UPDATE pipeline_documents SET ready=1,chunks=?,empty_pdf=? WHERE doc_id=?',(len(chunks),not bool(chunks),identity))
                    merged+=1; progressed=True
            counts=db.execute('SELECT COUNT(*),SUM(ready),SUM(CASE WHEN ready THEN chunks ELSE 0 END),SUM(empty_pdf) FROM pipeline_documents').fetchone()
            record={'unique_documents':counts[0],'ready_documents':counts[1],'ready_chunks':counts[2],'empty_pdf_documents':counts[3],
                'ocr_pages_applied':db.execute('SELECT COUNT(*) FROM ocr_applied').fetchone()[0],'seconds_this_run':time.perf_counter()-started}
            write_json(WORK/'merge-progress.json',record); write_json(OUT/'merge-progress.json',record)
            print(json.dumps(record),flush=True)
            if counts[0]==counts[1]:
                marker=json.loads((OCR/'ocr-complete.json').read_text(encoding='utf-8'))
                assert marker['status']=='completed'
                assert record['ocr_pages_applied']==marker['target_pages']
                record.update(status='completed',ocr_fingerprint=marker['fingerprint'],total_chunks=db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0])
                write_json(WORK/'corpus-complete.json',record); write_json(OUT/'ocr-corpus-summary.json',record)
                return
            if not args.watch: return
            if not progressed: time.sleep(30)
    finally: db.close()

if __name__=='__main__': main()
