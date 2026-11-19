"""全量の実ベクトルを製品テーブルに投入する。索引は MCP の取り込みに作成させる。"""
from __future__ import annotations

import hashlib
import json
import os
import time

os.environ.setdefault('RAYON_NUM_THREADS', '4')
os.environ.setdefault('OMP_NUM_THREADS', '4')

from common import BASE, OUT, WORK, configuration, digest, initialize, phase_lock, readonly, write_json
from rag_index import Engine, file_id


def main():
    initialize()
    while not (WORK / 'embedding-complete.json').exists():
        time.sleep(5)
    import numpy as np
    import pyarrow.compute as pc

    prepared = json.loads((WORK / 'prepared-complete.json').read_text(encoding='utf-8'))
    embedded = json.loads((WORK / 'embedding-complete.json').read_text(encoding='utf-8'))
    if embedded['chunks'] != prepared['chunks']:
        raise RuntimeError('本文と埋め込みの件数が一致しません。')
    cfg = configuration()
    engine = Engine(cfg)
    wiki = WORK / 'wiki'
    (wiki / 'sources').mkdir(parents=True, exist_ok=True)
    for name in ['SCHEMA.md', 'index.md', 'log.md']:
        path = wiki / name
        if not path.exists():
            path.write_text('# 全量 ANN 検証用の wiki\n', encoding='utf-8', newline='\n')
    folder = cfg.workspace(str(wiki))
    folder.mkdir(parents=True, exist_ok=True)
    engine._check_policy(folder)
    table = engine._table(folder, create=True)
    complete_path = WORK / 'stage-complete.json'
    if complete_path.exists():
        print(complete_path.read_text(encoding='utf-8'), flush=True)
        return
    if table.list_indices():
        raise RuntimeError('大量投入が完了する前に索引が作成されています。')
    seed = json.loads((OUT / 'seed-cache.json').read_text(encoding='utf-8'))
    seed_path = BASE / 'embeddings-130m/vectors.f32'
    if digest(seed_path) != seed['vector_sha256'] or digest(WORK / 'new-vectors.f32') != embedded['new_vector_sha256']:
        raise RuntimeError('確定済みのベクトルファイルが変わっています。')
    new_path = WORK / 'new-vectors.f32'
    vectors = {'seed': np.memmap(seed_path, dtype='float32', mode='r', shape=(seed_path.stat().st_size // 2048, 512)),
               'new': np.memmap(new_path, dtype='float32', mode='r', shape=(new_path.stat().st_size // 2048, 512))}
    checkpoint = WORK / 'import-progress.json'
    saved = json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {}
    if saved and saved['documents_digest'] != prepared['documents_digest']:
        raise RuntimeError('大量投入の入力が変わっています。')
    last = saved.get('last_id', 0)
    imported = saved.get('rows', 0)
    repair = table.count_rows() != imported
    if repair and not imported <= table.count_rows() <= imported + 2048:
        raise RuntimeError('投入台帳とテーブルの差が 1 バッチを超えています。')
    started = time.perf_counter()
    with readonly(WORK / 'prepared.sqlite') as db:
        while True:
            batch = db.execute('SELECT * FROM chunks WHERE id>? ORDER BY id LIMIT 2048', (last,)).fetchall()
            if not batch:
                break
            rows = []
            for row in batch:
                if hashlib.sha256(row['embedding_text'].encode('utf-8')).hexdigest() != row['input_hash']:
                    raise RuntimeError('投入する本文の入力ハッシュが一致しません。')
                vector = vectors[row['vector_source']][row['position']]
                if not np.isfinite(vector).all() or abs(float(np.linalg.norm(vector)) - 1) > 0.001:
                    raise RuntimeError('投入するベクトルが有限の正規化ベクトルではありません。')
                generation = cfg.generation(row['doc_id'])
                rows.append({'chunk_id': f"{generation}:{row['number']}", 'doc_id': row['doc_id'],
                             'generation': generation, 'page': row['page'], 'section': row['section'],
                             'title': row['title'], 'text': row['text'], 'terms': row['terms'], 'vector': vector.tolist()})
            if repair:
                table.merge_insert('chunk_id').when_matched_update_all().when_not_matched_insert_all().execute(rows)
                imported = table.count_rows()
                repair = False
            else:
                table.add(rows)
                imported += len(rows)
            last = batch[-1]['id']
            progress = {'last_id': last, 'rows': imported, 'expected_rows': prepared['chunks'],
                        'documents_digest': prepared['documents_digest'], 'seconds_this_run': time.perf_counter() - started}
            write_json(checkpoint, progress)
            if imported % 32768 < 2048:
                print(json.dumps(progress), flush=True)
        if table.count_rows() != prepared['chunks']:
            raise RuntimeError('投入後の行数が一致しません。')
        ids = table.search().select(['chunk_id']).limit(None).to_arrow()['chunk_id']
        if pc.count_distinct(ids).as_py() != prepared['chunks']:
            raise RuntimeError('チャンク ID が重複しています。')
        # 公開台帳の大量投入も検証用の準備。以降の追加・差し替えは製品の受付で行う。
        from pathlib import Path
        root = Path(json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))['root'])
        with engine._catalog(folder) as catalog:
            for doc in db.execute('SELECT * FROM documents'):
                generation = cfg.generation(doc['doc_id'])
                catalog.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?)',
                                (doc['doc_id'], generation, doc['title'], doc['pages'], doc['chunks'], cfg.fingerprint, time.time()))
                source_page = f"sources/{doc['doc_id']}.md"
                catalog.execute('INSERT OR IGNORE INTO citations VALUES (?,?)', (doc['doc_id'], source_page))
                catalog.execute("INSERT OR REPLACE INTO jobs VALUES (?,?,'complete',NULL)", (generation, doc['chunks']))
                (wiki / source_page).write_text('---\ntype: source\n---\n全量検証の出典。\n', encoding='utf-8', newline='\n')
            with readonly(BASE / 'corpus.sqlite', frozen=True) as old:
                for location in old.execute("SELECT relative_path,doc_id,size,mtime_ns FROM documents WHERE status='completed'"):
                    path = root / location['relative_path']
                    info = path.stat()
                    if (info.st_size, info.st_mtime_ns) != (location['size'], location['mtime_ns']):
                        raise RuntimeError(f'原本の属性が固定目録と異なります。{path}')
                    identity = file_id(info) or (None, None)
                    catalog.execute('INSERT OR REPLACE INTO locations VALUES (?,?,?,?,?,?,?)',
                                    (str(path), location['doc_id'], info.st_size, info.st_mtime_ns, time.time(), *identity))
    result = {'status': 'completed', 'documents': prepared['documents'], 'chunks': imported,
              'ocr_pages': prepared['ocr_pages'], 'table_version': table.version, 'indexes_before_mcp': [],
              'config': str(WORK / 'product-config.json'), 'wiki': str(wiki), 'folder': str(folder),
              'seconds_this_run': time.perf_counter() - started, 'source_pdf_ingest_e2e': False,
              'bulk_preparation': True, 'documents_digest': prepared['documents_digest']}
    write_json(complete_path, result)
    write_json(OUT / 'stage-complete.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    with phase_lock('stage'):
        main()
