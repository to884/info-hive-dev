"""実 OCR・実モデル・実 MCP による、退役キャッシュの再利用と回収の試験。"""
import asyncio
import hashlib
import json
import os
import sys
import time
import psutil
from pathlib import Path

from filelock import FileLock
from verify_pipeline import ROOT, POC_DATA, call, connect, wait_until
from rag_config import Config, write_json
from rag_index import Engine
from rag_jobs import Jobs

WORK = POC_DATA / 'cache-retirement-20261120'
OUT = ROOT / 'docs/research/rag-cache-retirement-2026-11-20'
REQUIRED = {
    'initial_real_ocr_saved', 'cleanup_fault_persisted', 'reactivation_reuses_original_ocr',
    'reset_reclaims_unshared_cache', 'reset_reclaims_legacy_and_all_extraction_keys',
    'reset_keeps_current_document_cache', 'reset_drains_unshared_retirement',
    'shared_real_ocr_saved', 'second_wiki_reuses_ocr', 'reset_preserves_other_wiki_cache',
    'reset_retains_cache_only_intent', 'last_reference_reclaims_shared_cache',
    'reconnect_drains_cache_only_intent', 'forbid_ocr_hook_loaded_in_workers',
    'only_initial_scans_called_ocr', 'all_jobs_completed', 'final_catalogs_match_tables',
    'reset_reactivation_reuses_ocr', 'interrupted_reset_resumes_same_job',
    'reset_preserve_doc_id_witnessed', 'product_sources_unchanged',
}


def product_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / 'info-hive-rag/scripts').glob('*.py'))}


def native_pdf(path):
    from reportlab.pdfgen import canvas
    pdf = canvas.Canvas(str(path))
    for number in range(3):
        pdf.drawString(40, 750 - number * 35, 'Native replacement keeps original saved OCR and cache references. ' + str(number))
    pdf.showPage()
    pdf.save()


def scan_pdf(path, title):
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    image = Image.new('RGB', (1000, 1400), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(os.environ.get('RAG_TEST_FONT', r'C:\Windows\Fonts\meiryo.ttc'), 44)
    for number, text in enumerate([title, '保存した日本語の認識結果を使います。', '不要になった結果だけを回収します。']):
        draw.text((50, 120 + number * 110), text, font=font, fill='black')
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    pdf.drawImage(ImageReader(image), 0, 0, width=595, height=842)
    pdf.showPage()
    pdf.save()


def stamp(cache):
    files = [*sorted(cache.glob('page-*.json')), cache / 'document.md']
    assert len(files) > 1 and all(path.is_file() for path in files)
    return {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mtime_ns': p.stat().st_mtime_ns} for p in files}


async def main():
    initial_product = product_hashes()
    run = WORK / f'mcp-{time.time_ns()}'
    run.mkdir(parents=True)
    OUT.mkdir(parents=True, exist_ok=True)
    source = run / 'scan.pdf'
    replacement = run / 'native.pdf'
    scan_pdf(source, '退役した資料の再登録')
    native_pdf(replacement)
    scan_bytes, native_bytes = source.read_bytes(), replacement.read_bytes()
    wikis = [run / 'wiki', run / 'other-wiki']
    for wiki in wikis:
        (wiki / 'sources').mkdir(parents=True)
        for name in ['SCHEMA.md', 'index.md', 'log.md']:
            (wiki / name).write_text('# キャッシュの検証\n', encoding='utf-8')
    values = {'data_dir': str(run / 'data'), 'embedding_model': 'cl-nagoya/ruri-v3-30m',
              'model_cache_dir': os.environ.get('RAG_TEST_MODEL_CACHE', str(POC_DATA / 'model-cache')),
              'uv_cache_dir': os.environ.get('RAG_TEST_UV_CACHE', str(WORK / 'uv-cache')),
              'cpu_threads': 4, 'batch_size': 1, 'chunk_chars': 500}
    config_file = run / 'config.json'
    write_json(config_file, values)
    cfg = Config(values)
    engine = Engine(cfg)
    jobs = Jobs(cfg.data_dir)
    trace = run / 'trace.jsonl'
    checks = []
    completed = []

    def record(name, passed, **detail):
        checks.append({'name': name, 'passed': bool(passed), **detail})
        print(json.dumps(checks[-1], ensure_ascii=False), flush=True)
        if not passed:
            raise AssertionError(name)

    def environment(forbid=True, defer=None, gate=None):
        return {'PYTHONPATH': str(ROOT / 'tests/rag/cache_fault'), 'RAG_CACHE_TEST_TRACE': str(trace),
                'RAG_CACHE_TEST_SCRIPTS': str(ROOT / 'info-hive-rag/scripts'),
                'RAG_CACHE_TEST_FORBID_OCR': '1' if forbid else '0', 'RAG_CACHE_TEST_DEFER_DOC': defer or '',
                'RAG_CACHE_TEST_EMBED_GATE': str(gate) if gate else ''}

    async def ingest(wiki, *, forbid=True, defer=None, config=config_file, gate=None):
        async with connect(config, extra_env=environment(forbid, defer, gate)) as (session, server):
            accepted = await call(session, 'register_pdf', wiki_root=str(wiki), source=str(source), source_page='sources/scan.md')
            def finished():
                state = jobs.status(str(wiki), accepted['job_id'])
                if state['status'] == 'failed':
                    if gate:
                        return state
                    raise RuntimeError(state['error'])
                return state if state['status'] == 'completed' else None
            state = await wait_until(finished, 1800)
            if gate:
                assert state['status'] == 'failed' and '埋め込み保存後に中断' in state['error'] and not gate.exists()
                await call(session, 'retry_job', wiki_root=str(wiki), job_id=state['job_id'])
                def resumed():
                    current = jobs.status(str(wiki), accepted['job_id'])
                    if current['status'] == 'failed':
                        raise RuntimeError(current['error'])
                    return current if current['status'] == 'completed' else None
                state = await wait_until(resumed, 1800)
                record('interrupted_reset_resumes_same_job', state['job_id'] == accepted['job_id'] and state['attempts'] == 2)
            descendants = {p.pid for p in server.children(recursive=True)}
            events = [json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()]
            workers = {e['pid'] for e in events if e['kind'] == 'hook_loaded' and e['target'] == 'rag_worker.py'
                       and e['pid'] in descendants and e['forbid_ocr'] == forbid}
            assert len(workers) == 1, workers
            completed.append({'job_id': state['job_id'], 'status': state['status'], 'result_status': state['result']['status'],
                              'worker_pid': workers.pop(), 'forbid_ocr': forbid})
            return state['result']

    def pending(wiki, doc_id):
        with engine._catalog(cfg.workspace(str(wiki))) as catalog:
            row = catalog.execute('SELECT rows_pending FROM retired_documents WHERE doc_id=?', (doc_id,)).fetchone()
            return None if row is None else row[0]

    state = 'failed'
    try:
        first = await ingest(wikis[0], forbid=False)
        old_id = first['document_id']
        cache = cfg.extraction_dir(old_id)
        entry = json.loads((cache / 'page-000001.json').read_text(encoding='utf-8'))
        before = stamp(cache)
        record('initial_real_ocr_saved', entry['ocr'] and len(entry['text'].strip()) > 20, doc_id=old_id, text_chars=len(entry['text']))
        source.write_bytes(native_bytes)
        deferred = await ingest(wikis[0], defer=old_id)
        record('cleanup_fault_persisted', bool(deferred['cleanup_error']) and pending(wikis[0], old_id) == 1 and cache.exists())
        source.write_bytes(scan_bytes)
        restored = await ingest(wikis[0])
        record('reactivation_reuses_original_ocr', restored['document_id'] == old_id and stamp(cache) == before)

        source.write_bytes(native_bytes)
        await ingest(wikis[0], defer=old_id)
        source.write_bytes(scan_bytes)
        values['chunk_chars'] = 550
        write_json(config_file, values)
        gate = run / 'embedding.gate'
        gate.write_text('最初の保存のあとに一度だけ中断\n', encoding='utf-8')
        restored = await ingest(wikis[0], gate=gate)
        record('reset_reactivation_reuses_ocr', restored['document_id'] == old_id and stamp(cache) == before)
        source.write_bytes(native_bytes)
        await ingest(wikis[0], defer=old_id)
        folder = cfg.workspace(str(wikis[0]))
        with engine._catalog(folder) as catalog:
            generation = json.loads(catalog.execute('SELECT legacy_generations FROM retired_documents WHERE doc_id=?', (old_id,)).fetchone()[0])[0]
        legacy = folder / 'extracted' / generation
        legacy.mkdir(parents=True)
        (legacy / 'page-000001.json').write_bytes((cache / 'page-000001.json').read_bytes())
        alternate = cache.parent / 'unused-extraction-key'
        alternate.mkdir()
        (alternate / 'page-000001.json').write_bytes((cache / 'page-000001.json').read_bytes())
        current_cache = cfg.extraction_dir(deferred['document_id'])
        current_before = stamp(current_cache)
        values['chunk_chars'] = 600
        write_json(config_file, values)
        reset = await ingest(wikis[0])
        record('reset_reclaims_unshared_cache', reset['index_reset'] and not cache.parent.exists())
        record('reset_reclaims_legacy_and_all_extraction_keys', not legacy.exists() and not alternate.exists())
        record('reset_keeps_current_document_cache', stamp(current_cache) == current_before)
        record('reset_drains_unshared_retirement', pending(wikis[0], old_id) is None)

        scan_pdf(source, '共有参照を持つ資料の検証')
        shared = await ingest(wikis[0], forbid=False)
        shared_id = shared['document_id']
        shared_cache = cfg.extraction_dir(shared_id)
        shared_before = stamp(shared_cache)
        shared_entry = json.loads((shared_cache / 'page-000001.json').read_text(encoding='utf-8'))
        record('shared_real_ocr_saved', shared_entry['ocr'] and len(shared_entry['text'].strip()) > 20)
        other_config = run / 'other-config.json'
        write_json(other_config, values)
        other = await ingest(wikis[1], config=other_config)
        record('second_wiki_reuses_ocr', other['document_id'] == shared_id and stamp(shared_cache) == shared_before)
        source.write_bytes(native_bytes)
        await ingest(wikis[0], defer=shared_id)
        values['chunk_chars'] = 700
        write_json(config_file, values)
        reset = await ingest(wikis[0])
        record('reset_preserves_other_wiki_cache', reset['index_reset'] and stamp(shared_cache) == shared_before)
        record('reset_retains_cache_only_intent', pending(wikis[0], shared_id) == 0)
        await ingest(wikis[1], config=other_config)
        record('last_reference_reclaims_shared_cache', not shared_cache.parent.exists())
        await ingest(wikis[0])
        record('reconnect_drains_cache_only_intent', pending(wikis[0], shared_id) is None)

        events = [json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()]
        forbidden_workers = {e['pid'] for e in events if e['kind'] == 'hook_loaded' and e['target'] == 'rag_worker.py' and e['forbid_ocr']}
        expected_workers = {job['worker_pid'] for job in completed if job['forbid_ocr']}
        record('forbid_ocr_hook_loaded_in_workers', len(expected_workers) == 11 and forbidden_workers == expected_workers)
        record('reset_preserve_doc_id_witnessed', any(e['kind'] == 'index_reset' and e['preserve_doc_id'] == old_id for e in events))
        calls = [event for event in events if event['kind'] == 'ocr_called']
        record('only_initial_scans_called_ocr', len(calls) == 2 and not any(e['forbidden'] for e in calls), actual_calls=len(calls))
        record('all_jobs_completed', len(completed) == 13 and all(j['status'] == 'completed' for j in completed), jobs=len(completed))
        consistent = True
        for wiki in wikis:
            folder = cfg.workspace(str(wiki))
            with engine._catalog(folder) as catalog:
                documents, chunks = catalog.execute('SELECT COUNT(*),SUM(chunks) FROM documents').fetchone()
                retired = catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0]
            consistent &= documents == 1 and chunks == engine._table(folder).count_rows() and retired == 0
        record('final_catalogs_match_tables', consistent)
        record('product_sources_unchanged', product_hashes() == initial_product)
        assert REQUIRED == {check['name'] for check in checks} and all(check['passed'] for check in checks)
        state = 'completed'
    finally:
        result = {'status': state, 'run_dir': str(run), 'checks': checks, 'jobs': completed,
                  'real_ocr': True, 'real_embeddings': True, 'transport': 'product stdio MCP via prepared Python',
                  'product_sha256': hashlib.sha256((ROOT / 'info-hive-rag/scripts/rag_index.py').read_bytes()).hexdigest(),
                  'initial_product_hashes': initial_product, 'final_product_hashes': product_hashes(),
                  'os_power_interruption': False}
        write_json(run / 'results.json', result)
        write_json(OUT / 'mcp-results.json', result)


if __name__ == '__main__':
    WORK.mkdir(parents=True, exist_ok=True)
    with FileLock(str(WORK / 'mcp.lock'), timeout=0):
        asyncio.run(main())
