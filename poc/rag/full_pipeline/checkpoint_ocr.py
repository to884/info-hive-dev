"""OS を止めず、全量 OCR のプロセス消失とページ単位の再開を検証する。"""
import argparse
import json
import sqlite3
import time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
WORK=ROOT/'.rag-poc-data/full-ocr-20261104'
OUT=ROOT/'docs/research/rag-full-pipeline-2026-11-04'

def saved():
    with sqlite3.connect(WORK/'ocr.sqlite') as db:
        return {f'{doc}:{page}':[attempts,digest] for doc,page,attempts,digest in db.execute("SELECT doc_id,page,attempts,text_sha256 FROM targets WHERE status IN ('completed','empty')")}

def main():
    global WORK
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=['stop','verify'])
    p.add_argument('--workspace',type=Path,default=WORK); p.add_argument('--tag',default='cpu')
    args=p.parse_args(); WORK=args.workspace.resolve()
    snapshot=WORK/f'interrupt-{args.tag}-snapshot.json'
    result_path=OUT/f'ocr-{args.tag}-interruption.json'
    if args.stage=='stop':
        candidates=[]
        for process in psutil.process_iter(['name','cmdline']):
            command=process.info['cmdline'] or []
            if process.info['name'].lower().startswith('python') and any(arg.replace('\\','/').endswith('/full_ocr.py') for arg in command) and any(WORK.name in arg for arg in command):
                candidates.append(process)
        owner=max(candidates,key=lambda process:len(process.parents()))
        children=owner.children(recursive=True)
        initial=saved(); assert initial
        write_json(snapshot,{'saved':initial,'owner':owner.pid,'children':[process.pid for process in children]})
        owner.kill()
        _,alive=psutil.wait_procs([owner,*children],timeout=20)
        write_json(result_path,{'process_tree_stopped':not alive,'descendants':len(children),'saved_pages_before_interrupt':len(initial),'os_power_cut':False,'resumed':False})
        if alive: raise RuntimeError('検証用の子プロセスが残りました。')
    else:
        before=json.loads(snapshot.read_text(encoding='utf-8'))['saved']
        after=saved()
        assert len(after)>len(before)
        assert all(after.get(key)==value for key,value in before.items())
        record=json.loads(result_path.read_text(encoding='utf-8'))
        write_json(result_path,{**record,'resumed':True,'saved_pages_after_resume':len(after),'saved_page_attempts_and_hashes_unchanged':True})
    print('全量 OCR のチェックポイント検証を記録しました。',flush=True)

if __name__=='__main__': main()
