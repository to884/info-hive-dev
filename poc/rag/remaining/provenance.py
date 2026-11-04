"""承認された評価質問と、再開対象の全量データをハッシュで対応付ける。"""
import csv
import hashlib
import importlib.metadata
import json
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'
WORK=ROOT/'.rag-poc-data/full-20261104'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(8*1024*1024): h.update(block)
    return h.hexdigest()


def lexical_fingerprint():
    versions={name:importlib.metadata.version(name) for name in ['sudachipy','sudachidict-core']}
    return hashlib.sha256((digest(ROOT/'info-hive-rag/scripts/rag_index.py')+json.dumps(versions,sort_keys=True)).encode()).hexdigest()


def approved_queries():
    record_path=OUT/'human-review.json'
    record=json.loads(record_path.read_text(encoding='utf-8'))
    review=WORK/'review/qa-review.csv'
    if digest(review)!=record['reviewed_csv_sha256']:
        raise RuntimeError('承認時の CSV から変更されています。')
    with review.open(encoding='utf-8-sig',newline='') as stream: rows=list(csv.DictReader(stream))
    path=Path(__file__).with_name('reviewed-queries.json')
    queries=json.loads(path.read_text(encoding='utf-8'))
    expected={r['id']:(r['proposed_question'],json.loads(r['proposed_relevant_pages'])) for r in rows}
    if len(queries)!=record['questions'] or any((q['query'],q['expected'])!=expected[q['id']] for q in queries):
        raise RuntimeError('承認済み CSV と質問・正解ページが一致しません。')
    value=digest(path)
    if record.get('reviewed_queries_sha256',value)!=value:
        raise RuntimeError('承認記録に対応する質問のハッシュが一致しません。')
    if 'reviewed_queries_sha256' not in record:
        write_json(record_path,{**record,'reviewed_queries_sha256':value})
    return queries


def full_fingerprint():
    embedded=json.loads((WORK/'embeddings-130m/complete.json').read_text(encoding='utf-8'))
    h=hashlib.sha256()
    h.update(digest(WORK/'manifest.json').encode())
    h.update(json.dumps({k:embedded[k] for k in ['model','revision','dimension','device']},sort_keys=True).encode())
    h.update(digest(WORK/'embeddings-130m/vectors.f32').encode())
    db=sqlite3.connect(WORK/'corpus.sqlite')
    for row in db.execute('SELECT id,doc_id,page,number,embedding_text FROM chunks ORDER BY id'):
        h.update(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        h.update(b'\n')
    db.close()
    return h.hexdigest()


if __name__=='__main__':
    approved_queries()
    print('承認済み CSV と評価質問の一致を確認しました。',flush=True)
