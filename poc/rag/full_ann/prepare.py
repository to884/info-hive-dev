"""製品の抽出結果からチャンクを作り、同じ入力の確定ベクトルを再利用する。"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import BASE, OCR, OUT, WORK, configuration, digest, frozen_uri, initialize, phase_lock, readonly, write_json
from rag_index import Engine, read_pdf
from rag_pdf import chunks_for, extract_pages


def connect():
    db = sqlite3.connect(WORK / "prepared.sqlite", timeout=60, uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA cache_size=-262144")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY, relative_path TEXT, title TEXT, pages INTEGER, chunks INTEGER,
            size INTEGER, mtime_ns INTEGER, extraction_digest TEXT, ocr_pages INTEGER, ocr_empty INTEGER);
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY, doc_id TEXT, number INTEGER, page INTEGER, section TEXT,
            title TEXT, text TEXT, embedding_text TEXT, input_hash TEXT, terms TEXT,
            vector_source TEXT, position INTEGER, UNIQUE(doc_id,number));
        CREATE INDEX IF NOT EXISTS chunks_hash ON chunks(input_hash);
        CREATE INDEX IF NOT EXISTS chunks_missing ON chunks(vector_source,input_hash);
        CREATE TABLE IF NOT EXISTS seed (
            input_hash TEXT PRIMARY KEY, position INTEGER);
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
    """)
    return db


def seed_cache(db):
    if db.execute("SELECT 1 FROM metadata WHERE key='seed'").fetchone():
        return
    complete = json.loads((BASE / "embeddings-130m/complete.json").read_text(encoding="utf-8"))
    cfg = configuration()
    if (complete['model'], complete['revision'], complete['dimension']) != (cfg.model, cfg.revision, cfg.dimension):
        raise RuntimeError("再利用するベクトルのモデル設定が異なります。")
    raw = BASE / "embeddings-130m/vectors.f32"
    if raw.stat().st_size != complete['vectors_including_retired_ids'] * cfg.dimension * 4:
        raise RuntimeError("再利用するベクトルファイルの長さが一致しません。")
    db.execute("ATTACH DATABASE ? AS old_vectors", (frozen_uri(BASE / "embeddings-130m/ledger.sqlite"),))
    with db:
        db.execute("INSERT INTO seed SELECT input_hash,MIN(position) FROM old_vectors.vectors GROUP BY input_hash")
        value = {"vector_sha256": digest(raw), "vector_rows": complete['vectors_including_retired_ids'],
                 "terms_recomputed": True}
        db.execute("INSERT INTO metadata VALUES ('seed',?)", (json.dumps(value),))
    db.execute("DETACH DATABASE old_vectors")
    write_json(OUT / "seed-cache.json", value)


def page_records(row, cfg, root, reader):
    cache = OCR / 'data/extracted' / row['doc_id'] / cfg.extraction_key
    if row['status'] == 'completed':
        files = sorted(cache.glob('page-*.json'))
        if len(files) != row['pages'] or not (cache / 'document.md').is_file():
            raise RuntimeError(f"抽出済みのページが不足しています。{row['relative_path']}")
        checksum = hashlib.sha256()
        pages = []
        for number, (path, raw) in enumerate(zip(files, reader.map(Path.read_bytes, files)), 1):
            entry = json.loads(raw)
            if entry['page'] != number:
                raise RuntimeError(f"ページ番号が一致しません。{path}")
            checksum.update(path.name.encode() + b'\0' + hashlib.sha256(raw).digest())
            pages.append(entry)
        return pages, checksum.hexdigest()
    if row['planned_ocr'] != 0:
        raise RuntimeError("未完了の OCR 文書が残っています。")
    path = root / row['relative_path']
    info = path.stat()
    if getattr(info, 'st_file_attributes', 0) & (0x1000 | 0x40000 | 0x400000):
        raise RuntimeError(f'オンラインだけの原本は読み込みません。{path}')
    if (info.st_size, info.st_mtime_ns) != (row['size'], row['mtime_ns']):
        raise RuntimeError(f"原本の属性が固定目録と異なります。{path}")
    data, _ = read_pdf(path)
    if hashlib.sha256(data).hexdigest() != row['doc_id']:
        raise RuntimeError("再抽出する原本のハッシュが一致しません。")
    local = WORK / 'recovered-extracted' / row['doc_id'] / cfg.extraction_key
    pages = extract_pages(data, cfg, local)
    if any(page['ocr'] for page in pages):
        raise RuntimeError("テキストだけと見込んだ文書に OCR が含まれています。")
    Engine._write_markdown(local / 'document.md', pages)
    checksum = hashlib.sha256()
    for file in sorted(local.glob('page-*.json')):
        checksum.update(file.name.encode() + b'\0' + hashlib.sha256(file.read_bytes()).digest())
    return pages, checksum.hexdigest()


def main():
    policy = initialize()
    cfg = configuration()
    recorded = json.loads((OCR / 'run-policy.json').read_text(encoding='utf-8'))
    if recorded['extraction_key'] != cfg.extraction_key:
        raise RuntimeError("保存済み OCR の抽出設定が一致しません。")
    db = connect()
    seed_cache(db)
    seed = {row['input_hash']: row['position'] for row in db.execute('SELECT * FROM seed')}
    manifest = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
    root = Path(manifest['root'])
    engine = Engine(cfg)
    started = time.perf_counter()
    with readonly(OCR / 'ledger.sqlite', frozen=True) as ledger:
        documents = ledger.execute('SELECT * FROM documents ORDER BY doc_id').fetchall()
    if len(documents) != 905:
        raise RuntimeError("文書数が固定目録と一致しません。")
    prepared_documents = db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    prepared_chunks = db.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    reused_vectors = db.execute("SELECT COUNT(*) FROM chunks WHERE vector_source='seed'").fetchone()[0]
    result = {}
    reader = ThreadPoolExecutor(max_workers=4)
    try:
        for row in documents:
            if db.execute('SELECT 1 FROM documents WHERE doc_id=?', (row['doc_id'],)).fetchone():
                continue
            pages, checksum = page_records(row, cfg, root, reader)
            title = Path(row['relative_path']).stem
            chunks = chunks_for(pages, title, cfg)
            if not chunks:
                raise RuntimeError(f"本文のない文書です。{title}")
            with db:
                for start in range(0, len(chunks), 1024):
                    batch = chunks[start:start + 1024]
                    keys = [hashlib.sha256(chunk['embedding_text'].encode('utf-8')).hexdigest() for chunk in batch]
                    prepared = []
                    for number, (chunk, key) in enumerate(zip(batch, keys), start):
                        position = seed.get(key)
                        normalized = engine.tokenize(chunk['embedding_text'])
                        reused_vectors += position is not None
                        prepared.append((row['doc_id'], number, chunk['page'], chunk['section'], title, chunk['text'],
                                         chunk['embedding_text'], key, normalized, 'seed' if position is not None else None, position))
                    db.executemany('''INSERT INTO chunks (doc_id,number,page,section,title,text,embedding_text,input_hash,terms,vector_source,position)
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?)''', prepared)
                db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)',
                           (row['doc_id'], row['relative_path'], title, len(pages), len(chunks), row['size'], row['mtime_ns'],
                            checksum, sum(bool(p['ocr']) for p in pages), sum(bool(p.get('ocr_empty')) for p in pages)))
            prepared_documents += 1
            prepared_chunks += len(chunks)
            result = {'documents': prepared_documents, 'chunks': prepared_chunks,
                      'reused_vectors': reused_vectors,
                      'seconds_this_run': time.perf_counter() - started}
            write_json(WORK / 'prepare-progress.json', result)
            if result['documents'] % 10 == 0:
                print(json.dumps(result), flush=True)
        counts = tuple(db.execute('SELECT SUM(pages),SUM(ocr_pages),SUM(ocr_empty),SUM(chunks) FROM documents').fetchone())
        if counts[1] != 22335:
            raise RuntimeError("保存済み OCR のページ数が一致しません。")
        rows = [dict(row) for row in db.execute('SELECT * FROM documents ORDER BY doc_id')]
        checksum = hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        result = {'documents': prepared_documents, 'chunks': prepared_chunks, 'reused_vectors': reused_vectors,
                  'seconds_this_run': time.perf_counter() - started,
                  'status': 'completed', 'pages': counts[0], 'ocr_pages': counts[1], 'ocr_empty': counts[2],
                  'documents_digest': checksum, 'policy_fingerprint': policy['fingerprint'],
                  'recovered_text_only_documents': [row['relative_path'] for row in documents if row['status'] != 'completed']}
        write_json(WORK / 'prepared-complete.json', result)
        write_json(OUT / 'prepared-corpus.json', result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        reader.shutdown(wait=True)
        db.close()


if __name__ == '__main__':
    with phase_lock('prepare'):
        main()
