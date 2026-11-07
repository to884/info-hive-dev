"""複数の実 MCP が一つのワーカーを共有し、取り込み中も制御できるか確認する。"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from contextlib import AsyncExitStack

import psutil
from filelock import FileLock
from verify_pipeline import ROOT,connect,call,wait_until
from rag_config import Config,write_json
from rag_jobs import Jobs


async def main():
    run=ROOT/'.rag-poc-data'/f'concurrent-{int(time.time())}'
    run.mkdir(parents=True)
    baseline=sorted((ROOT/'.rag-poc-data').glob('j*/config.json'))[-1]
    values=json.loads(baseline.read_text(encoding='utf-8'))
    source=sorted((ROOT/'.rag-poc-data').glob('k*/references/controls.pdf'))[-1]
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    values.update(data_dir=str(run/'data'),batch_size=1,model_cache_dir=str(ROOT/'.rag-poc-data/model-cache'),ocr_mode='off')
    path=run/'config.json'; write_json(path,values)
    cfg=Config(values); jobs=Jobs(cfg.data_dir)
    wikis=[run/'wiki-a',run/'wiki-b']
    for wiki in wikis:
        (wiki/'sources').mkdir(parents=True)
        (wiki/'SCHEMA.md').write_text('# 同時接続の検証\n',encoding='utf-8')
    checks=[]
    def record(name,passed,**details):
        checks.append({'name':name,'passed':bool(passed),**details})
        print(json.dumps(checks[-1],ensure_ascii=False),flush=True)
        assert passed,name
    lock=FileLock(str(cfg.data_dir/'worker.lock'))
    stack=AsyncExitStack()
    try:
        with lock:
            a,server_a=await stack.enter_async_context(connect(path))
            b,server_b=await stack.enter_async_context(connect(path))
            submitted=await asyncio.gather(*[call(a if i%2 else b,'register_pdf',wiki_root=str(wikis[0]),source=str(source),source_page='sources/fixture.md') for i in range(8)])
            identity=submitted[0]['job_id']
            record('two_mcp_sessions_deduplicate_eight_registrations',len({j['job_id'] for j in submitted})==1)
            second=await call(b,'register_pdf',wiki_root=str(wikis[1]),source=str(source),source_page='sources/fixture.md')
            record('same_pdf_in_another_wiki_has_independent_job',second['job_id']!=identity)
            wrong=await b.call_tool('job_status',{'wiki_root':str(wikis[1]),'job_id':identity})
            record('mcp_rejects_cross_wiki_job_access',wrong.isError)
            cancel=await call(a,'cancel_job',wiki_root=str(wikis[1]),job_id=second['job_id'])
            record('second_session_can_cancel_pending_job',cancel['status']=='cancelled')
        def running():
            state=jobs.status(str(wikis[0]),identity)
            if state['status']=='failed': raise RuntimeError(state['error'])
            return state if state['status']=='running' else None
        await wait_until(running,120)
        await asyncio.sleep(1)
        pending=asyncio.create_task(call(a,'search',wiki_root=str(wikis[0]),query='進捗を保存して再開する方法',limit=3))
        await asyncio.sleep(.2)
        record('search_waits_while_indexing',not pending.done())
        start=time.perf_counter()
        state=await call(b,'job_status',wiki_root=str(wikis[0]),job_id=identity)
        delay=time.perf_counter()-start
        record('status_is_responsive_during_index_and_pending_search',state['status']=='running' and delay<2,seconds=delay)
        answer=await asyncio.wait_for(pending,1200)
        record('queued_search_reads_completed_generation',bool(answer['results']) and jobs.status(str(wikis[0]),identity)['status']=='completed')
        workers=[]
        for server in [server_a,server_b]:
            for proc in server.children(recursive=True):
                try:
                    # ロックを取れず終了する起動直後の待機プロセスをモデル保持と数えない。
                    if any(arg.replace('\\','/').endswith('/rag_worker.py') for arg in proc.cmdline()) and proc.memory_info().rss>150_000_000:
                        workers.append(proc.pid)
                except psutil.NoSuchProcess: pass
        record('only_one_model_worker_across_two_mcp_sessions',len(set(workers))==1,worker_pids=workers)
        start=time.perf_counter()
        answers=await asyncio.gather(*[call(a if i%2 else b,'search',wiki_root=str(wikis[0]),query='中断した処理を再開する方法',limit=3) for i in range(8)])
        record('eight_concurrent_search_requests_complete',all(x['results'] for x in answers),total_seconds=time.perf_counter()-start)
        # ワーカーを保持する接続だけを終了し、残る接続で新しいワーカーが立つことを確認する。
        owner=server_a if any(pid in {p.pid for p in server_a.children(recursive=True)} for pid in workers) else server_b
        remaining=b if owner.pid==server_a.pid else a
        owner.kill()
        await asyncio.sleep(2)
        after=await call(remaining,'search',wiki_root=str(wikis[0]),query='進捗の保存と再開',limit=3)
        record('remaining_mcp_session_takes_over_worker',bool(after['results']))
        record('completed_job_is_not_reexecuted_on_takeover',jobs.status(str(wikis[0]),identity)['attempts']==1)
        record('cancelled_other_wiki_job_remains_cancelled',jobs.status(str(wikis[1]),second['job_id'])['status']=='cancelled')
        record('source_pdf_unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==source_hash)
    finally:
        await stack.aclose()
        write_json(ROOT/'docs/research/rag-validation-remaining-2026-11-04/concurrency-results.json',{'run_dir':str(run),'checks':checks,'execution':'索引化と検索は直列。要求受付と進捗確認が並行する。'})


if __name__=='__main__': asyncio.run(main())
