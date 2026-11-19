"""試験後に OCR の集約ハッシュ、原本の属性、全索引の件数を再確認する。"""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from common import BASE, OCR, OUT, WORK, configuration, digest, initialize, phase_lock, readonly, validate_checks, write_json
from rag_index import Engine
from rag_indexes import statistics, version


def main():
    initialize()
    result = json.loads((WORK / 'mcp-workflow.json').read_text(encoding='utf-8'))
    if result.get('status') != 'completed' or not all(row['passed'] for row in result['checks']):
        raise RuntimeError('MCP の検証が完了していません。')
    validate_checks(result['checks'])
    cfg = configuration()
    with readonly(WORK / 'prepared.sqlite') as db:
        documents = db.execute('SELECT * FROM documents ORDER BY doc_id').fetchall()
    prepared = json.loads((WORK / 'prepared-complete.json').read_text(encoding='utf-8'))
    metadata_digest = hashlib.sha256(json.dumps([dict(row) for row in documents],
        sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    if metadata_digest != prepared['documents_digest']:
        raise RuntimeError('準備時の文書台帳が変わっています。')
    with readonly(OCR / 'ledger.sqlite', frozen=True) as db:
        completed = {row['doc_id'] for row in db.execute("SELECT doc_id FROM documents WHERE status='completed'")}
    started = time.perf_counter()
    checked_pages = 0
    ocr_pages = 0
    empty_pages = 0
    aggregate = hashlib.sha256()
    def audit_document(document):
        root = OCR / 'data/extracted' if document['doc_id'] in completed else WORK / 'recovered-extracted'
        cache = root / document['doc_id'] / cfg.extraction_key
        checksum = hashlib.sha256()
        recognized = 0
        empty = 0
        files = sorted(cache.glob('page-*.json'))
        if len(files) != document['pages'] or not (cache / 'document.md').is_file():
            raise RuntimeError('抽出結果のページ数が準備時から変わっています。')
        for number, file in enumerate(files, 1):
            raw = file.read_bytes()
            entry = json.loads(raw)
            if entry['page'] != number:
                raise RuntimeError(f'抽出結果のページ番号が一致しません。{file}')
            checksum.update(file.name.encode() + b'\0' + hashlib.sha256(raw).digest())
            recognized += bool(entry['ocr'])
            empty += bool(entry.get('ocr_empty'))
        if checksum.hexdigest() != document['extraction_digest']:
            raise RuntimeError(f"抽出結果が準備時から変わっています。{document['relative_path']}")
        if (recognized, empty) != (document['ocr_pages'], document['ocr_empty']):
            raise RuntimeError(f"OCR の件数が準備時から変わっています。{document['relative_path']}")
        return document['doc_id'], checksum.digest(), len(files), recognized, empty

    # 読み取りだけを並行し、集約の順序は準備時と同じ doc_id 順に保つ。
    with ThreadPoolExecutor(max_workers=4) as readers:
        for doc_id, checksum, pages, recognized, empty in readers.map(audit_document, documents):
            aggregate.update(doc_id.encode() + checksum)
            checked_pages += pages
            ocr_pages += recognized
            empty_pages += empty
    manifest = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
    root = Path(manifest['root'])
    original_locations = 0
    with readonly(BASE / 'corpus.sqlite', frozen=True) as db:
        for document in db.execute("SELECT relative_path,size,mtime_ns FROM documents WHERE status='completed'"):
            path = root / document['relative_path']
            info = path.stat()
            if (info.st_size, info.st_mtime_ns) != (document['size'], document['mtime_ns']):
                raise RuntimeError(f'原本の属性が固定目録と異なります。{path}')
            original_locations += 1
    seed = json.loads((OUT / 'seed-cache.json').read_text(encoding='utf-8'))
    if digest(BASE / 'embeddings-130m/vectors.f32') != seed['vector_sha256']:
        raise RuntimeError('既存ベクトルが準備時から変わっています。')
    stop = json.loads((WORK / 'embedding-interruption.json').read_text(encoding='utf-8'))
    count = stop['committed_vectors']
    with readonly(WORK / 'prepared.sqlite') as db:
        mapping = [tuple(row) for row in db.execute('SELECT input_hash,position FROM new_vectors WHERE position<? ORDER BY position', (count,))]
    if len(mapping) != count or hashlib.sha256(json.dumps(mapping).encode()).hexdigest() != stop['mapping_sha256']:
        raise RuntimeError('中断前に確定済みだった埋め込みの対応が変わっています。')
    prefix = hashlib.sha256()
    with (WORK / 'new-vectors.f32').open('rb') as stream:
        remaining = count * 2048
        while remaining:
            block = stream.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise RuntimeError('中断前のベクトルが不足しています。')
            prefix.update(block)
            remaining -= len(block)
    if prefix.hexdigest() != stop['committed_prefix_sha256']:
        raise RuntimeError('中断前に確定済みだったベクトルが変わっています。')
    engine = Engine(cfg)
    folder = cfg.workspace(str(WORK / 'wiki'))
    table = engine._table(folder)
    rows = table.count_rows()
    stats = {name: statistics(table, name) for name in ['terms_idx', 'generation_idx', 'vector_idx']}
    if any(s['num_indexed_rows'] != rows or s['num_unindexed_rows'] != 0 for s in stats.values()):
        raise RuntimeError('最終索引の網羅に不足があります。')
    if (ocr_pages, checked_pages, empty_pages) != (prepared['ocr_pages'], prepared['pages'], prepared['ocr_empty']):
        raise RuntimeError('全量のページ数が固定した数と異なります。')
    audit = {'status': 'passed', 'checked_documents': len(documents), 'checked_pages': checked_pages,
             'ocr_pages': ocr_pages, 'ocr_empty': empty_pages, 'extraction_aggregate_sha256': aggregate.hexdigest(),
             'prepared_documents_digest': metadata_digest,
             'original_locations_with_unchanged_size_mtime': original_locations,
             'original_full_content_reread': False, 'seed_vector_unchanged': True,
             'embedding_restart_prefix_vectors_verified': count,
             'reader_threads': 4, 'seconds': time.perf_counter() - started}
    write_json(OUT / 'integrity-audit.json', audit)
    embedded = json.loads((WORK / 'embedding-complete.json').read_text(encoding='utf-8'))
    summary = {'status': 'completed', 'completed_at': datetime.now().astimezone().isoformat(timespec='seconds'),
               'source_documents': len(documents), 'source_chunks': prepared['chunks'],
               'reused_vector_chunks': prepared['reused_vectors'], 'new_unique_vectors': embedded['new_unique_vectors'],
               'ocr_pages': ocr_pages, 'final_rows': rows, 'table_version': version(table), 'indexes': stats,
               'checks_passed': len(result['checks']), 'bulk_preparation': True,
               'stop_boundaries': {name: result[name]['commit_state'] for name in ['ann_creation_interrupt', 'ann_update_interrupt']},
               'replacement_stop_boundary': 'catalog_published_cleanup_pending',
               'index_bytes_including_retained_versions': sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()),
               'config': str(WORK / 'product-config.json'), 'wiki': str(WORK / 'wiki')}
    write_json(OUT / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    with phase_lock('finish'):
        main()
