"""承認済みの正解ページを全量索引の内容ハッシュに対応付ける。"""
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
from provenance import approved_queries
WORK=ROOT/'.rag-poc-data/full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def main():
    old=(Path(os.environ['LOCALAPPDATA'])/'info-hive/rag-poc/2026-11-04').resolve()
    samples=json.loads((old/'sample-manifest.json').read_text(encoding='utf-8'))['files']
    db=sqlite3.connect(WORK/'corpus.sqlite')
    docs={r[0]:r[1] for r in db.execute("SELECT relative_path,doc_id FROM documents WHERE status='completed'")}
    queries=approved_queries()
    for q in queries:
        mapped=[]
        for label in q['expected']:
            sample,page=label.split(':p')
            doc_id=docs[samples[int(sample.removeprefix('sample-'))]['relative_path']]
            assert db.execute('SELECT 1 FROM chunks WHERE doc_id=? AND page=? LIMIT 1',(doc_id,int(page))).fetchone()
            mapped.append(f'{doc_id}:p{page}')
        q['expected']=mapped
    tokens=['IH-ABSENT-'+hashlib.sha256(f'20261104:{i}'.encode()).hexdigest()[:20] for i in range(12)]
    for text, in db.execute('SELECT text FROM pages'):
        assert not any(token in text for token in tokens)
    for i,token in enumerate(tokens):
        queries.append({'id':f'negative-{i:02}','query':f'資料中の識別子「{token}」に定義されている'+('検索設定値' if i%2 else '手順と制約')+'を教えてください。','expected':[],'negative_kind':'absent_identifier'})
    total=db.execute("SELECT COUNT(*),SUM(size),SUM(pages) FROM documents WHERE status='completed'").fetchone()
    chunks=db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    write_json(WORK/'corpus.json',{'queries':queries})
    write_json(OUT/'full-corpus.json',{'pdf_files':total[0],'source_bytes':total[1],'pages':total[2],'chunks':chunks,'positive_queries':60,'negative_queries':12,'forced_answer_chunks':0,'ocr_included':False,'source_extraction_complete':True})
    db.close()


if __name__=='__main__': main()
