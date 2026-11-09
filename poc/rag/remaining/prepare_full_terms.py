"""語彙検索用の正規化を、GPU 埋め込みの残りの処理と並行して準備する。"""
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_index import Engine
from provenance import lexical_fingerprint
WORK=POC_DATA/'full-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def main():
    while not (WORK/'extraction-complete.json').exists():
        print(json.dumps({'phase':'waiting_for_frozen_source'}),flush=True); time.sleep(30)
    if json.loads((WORK/'extraction-complete.json').read_text(encoding='utf-8'))['status']!='completed':
        raise RuntimeError('全量抽出が正常終了していません。')
    source=sqlite3.connect(WORK/'corpus.sqlite')
    source.execute('ATTACH DATABASE ? AS lexical',(str(WORK/'terms.sqlite'),))
    terms=sqlite3.connect(WORK/'terms.sqlite')
    terms.execute('PRAGMA journal_mode=WAL')
    terms.execute('CREATE TABLE IF NOT EXISTS terms(id INTEGER PRIMARY KEY,input_hash TEXT,terms TEXT)')
    terms.commit()
    signature=lexical_fingerprint(); meta=WORK/'terms-meta.json'
    if meta.exists() and json.loads(meta.read_text(encoding='utf-8'))['lexical_fingerprint']!=signature:
        raise RuntimeError('語彙検索用の正規化設定が変わっています。別の保存先で準備してください。')
    write_json(meta,{'lexical_fingerprint':signature})
    for text,expected in source.execute('SELECT c.embedding_text,t.input_hash FROM chunks c JOIN lexical.terms t ON t.id=c.id'):
        if hashlib.sha256(text.encode('utf-8')).hexdigest()!=expected: raise RuntimeError('正規化済み入力が変更されています。')
    last=terms.execute('SELECT COALESCE(MAX(id),-1) FROM terms').fetchone()[0]
    engine=Engine(Config({'data_dir':str(WORK/'term-data'),'embedding_model':'cl-nagoya/ruri-v3-130m'}))
    started=time.perf_counter(); new=0
    while True:
        rows=source.execute('SELECT id,embedding_text FROM chunks WHERE id>? ORDER BY id LIMIT 2048',(last,)).fetchall()
        if not rows: break
        values=[(identity,hashlib.sha256(text.encode('utf-8')).hexdigest(),engine.tokenize(text)) for identity,text in rows]
        with terms: terms.executemany('INSERT INTO terms VALUES (?,?,?)',values)
        last=rows[-1][0]; new+=len(rows)
        progress={'lexical_fingerprint':signature,'new_rows_this_run':new,'completed_rows':terms.execute('SELECT COUNT(*) FROM terms').fetchone()[0],'seconds_this_run':time.perf_counter()-started}
        write_json(OUT/'full-terms-progress.json',progress)
        print(json.dumps(progress),flush=True)
    total=source.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    completed=terms.execute('SELECT COUNT(*) FROM terms').fetchone()[0]
    if total!=completed: raise RuntimeError('正規化用の台帳件数が一致しません。')
    terms.close(); source.close()
    write_json(WORK/'terms-complete.json',{'rows':completed,'lexical_fingerprint':signature,'seconds_this_run':time.perf_counter()-started})


if __name__=='__main__': main()
