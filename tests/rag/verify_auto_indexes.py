"""実 MCP の PDF 取り込みを起点に、ANN 作成・追加・置換・再接続を検証する。"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from verify_pipeline import ROOT,POC_DATA,connect,call,wait_until
from rag_config import Config,write_json
from rag_jobs import Jobs
from rag_index import Engine
from rag_indexes import version

OUT=Path(os.environ.get('RAG_TEST_OUTPUT',str(ROOT/'docs/research/rag-full-pipeline-2026-11-04')))
CHECKS=[]

def record(name,passed,**detail):
    CHECKS.append({'name':name,'passed':bool(passed),**detail})
    print(json.dumps(CHECKS[-1],ensure_ascii=False),flush=True)
    assert passed,name

def fixture(path,pages,marker):
    from reportlab.pdfgen import canvas
    pdf=canvas.Canvas(str(path),pagesize=(595,842))
    for page in range(pages):
        pdf.setFont('Helvetica',5)
        for line in range(45):
            text=f'{marker} page {page} line {line}. Persistent indexing keeps saved vectors and source pages. A separate generation filters replaced documents. '
            pdf.drawString(25,810-line*16,text)
        pdf.showPage()
    pdf.save()

async def main():
    run=Path(os.environ.get('RAG_TEST_RUN_ROOT',str(POC_DATA)))/f'auto-index-{int(time.time())}'
    refs=run/'refs'; refs.mkdir(parents=True)
    wiki=run/'wiki'; (wiki/'sources').mkdir(parents=True)
    for name in ['SCHEMA.md','index.md','log.md']:
        (wiki/name).write_text('# 自動索引の検証\n',encoding='utf-8')
    (wiki/'sources/a.md').write_text('---\ntype: source\n---\n出典の検証\n',encoding='utf-8')
    (wiki/'concept.md').write_text('---\nsources: [a]\n---\n資料を参照する概念。\n',encoding='utf-8')
    a=refs/'source-a.pdf'; b=refs/'source-b.pdf'
    fixture(a,40,'ANN_INITIAL_Q83'); fixture(b,4,'ANN_APPEND_Q83')
    values={'data_dir':str(run/'data'),'embedding_model':'cl-nagoya/ruri-v3-30m',
        'model_cache_dir':os.environ.get('RAG_TEST_MODEL_CACHE',str(POC_DATA/'model-cache')),
        'uv_cache_dir':os.environ.get('RAG_TEST_UV_CACHE',str(POC_DATA/'uv-cache-ocr')),
        'cpu_threads':4,'batch_size':16,'index_cleanup_age_days':3650,'search_nprobes':20}
    config_file=run/'config.json'; write_json(config_file,values)
    cfg=Config(values); jobs=Jobs(cfg.data_dir); engine=Engine(cfg); folder=cfg.workspace(str(wiki))
    snapshots=[]
    def covered(expected=None):
        state=json.loads((folder/'index-state.json').read_text(encoding='utf-8'))
        assert state['ann_ready']
        if expected is not None: assert state['rows']==expected
        assert all(stats['num_unindexed_rows']==0 and stats['num_indexed_rows']==state['rows'] for stats in state['indexes'].values())
        snapshots.append(state); return state
    async def ingest(session,source,page):
        submitted=await call(session,'register_pdf',wiki_root=str(wiki),source=str(source),source_page=page)
        def finished():
            state=jobs.status(str(wiki),submitted['job_id'])
            if state['status']=='failed': raise RuntimeError(state['error'])
            return state if state['status']=='completed' else None
        return await wait_until(finished,900)
    try:
        async with connect(config_file) as (session,_):
            initial=await ingest(session,a,'sources/a.md'); first=covered()
            record('pdf_ingest_automatically_creates_ann',first['rows']>=256 and first['trained_rows']==first['rows'],rows=first['rows'],partitions=first['num_partitions'])
            added=await ingest(session,b,'sources/b.md'); second=covered()
            record('pdf_append_automatically_updates_all_indexes',second['rows']==first['rows']+added['result']['chunks'])
            answer=await call(session,'search',wiki_root=str(wiki),query='ANN_APPEND_Q83',limit=10)
            record('appended_pdf_is_searchable',any(row['doc_id']==added['result']['document_id'] for row in answer['results']))
            old_id=initial['result']['document_id']
            fixture(a,44,'ANN_REPLACED_Q83')
            changed=await ingest(session,a,'sources/a.md'); third=covered()
            record('changed_pdf_replaces_old_generation',changed['result']['document_id']!=old_id and third['rows']==added['result']['chunks']+changed['result']['chunks'])
            record('old_generation_rows_are_removed',engine._table(folder).count_rows(f"doc_id = '{old_id}'")==0)
            record('replacement_automatically_rebuilds_ann',third['trained_rows']==third['rows'] and third['indexes']['vector_idx']['num_indices']==1)
            record('replacement_marks_dependent_wiki_page','review_required: true' in (wiki/'concept.md').read_text(encoding='utf-8'))
            record('replacement_has_no_maintenance_error',changed['result']['cleanup_error'] is None)
        before=version(engine._table(folder))
        async with connect(config_file) as (session,_):
            duplicate=await call(session,'register_pdf',wiki_root=str(wiki),source=str(a),source_page='sources/a.md')
            record('unchanged_pdf_is_not_reprocessed',duplicate['status']=='completed' and duplicate['attempts']==changed['attempts'])
            await asyncio.sleep(.5)
            record('reconnect_does_not_duplicate_index_updates',version(engine._table(folder))==before)
            result=await call(session,'search',wiki_root=str(wiki),query='ANN_REPLACED_Q83',limit=10)
            record('reconnected_search_excludes_old_document',bool(result['results']) and all(row['doc_id']!=old_id for row in result['results']))
    finally:
        write_json(OUT/'auto-indexes-mcp.json',{'run_dir':str(run),'checks':CHECKS,'snapshots':snapshots})

if __name__=='__main__': asyncio.run(main())
