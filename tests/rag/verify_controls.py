"""配布用の uv 起動設定を使い、待機中のキャンセルと明示再試行を確認する。"""
import asyncio
import json
import os
import time
from pathlib import Path

from filelock import FileLock
from verify_pipeline import ROOT, OUT, connect, call, wait_until
from rag_config import Config, write_json
from rag_jobs import Jobs


async def main():
    run = Path(os.environ.get('RAG_TEST_RUN_ROOT',str(ROOT/'.rag-poc-data'))) / f"k{int(time.time())}"
    references = run / "references"
    references.mkdir(parents=True)
    source = references / "controls.pdf"
    from reportlab.pdfgen import canvas
    pdf = canvas.Canvas(str(source))
    for number in range(4):
        pdf.drawString(40, 700, "Persistent controls " + str(number))
        pdf.showPage()
    pdf.save()
    wiki = run / "wiki"
    (wiki / "sources").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_text("# 制御試験\n", encoding="utf-8")
    base = Path(os.environ['RAG_TEST_BASE_CONFIG']) if os.environ.get('RAG_TEST_BASE_CONFIG') else sorted((ROOT / ".rag-poc-data").glob("j*/config.json"))[-1]
    values = json.loads(base.read_text(encoding="utf-8"))
    values.update(reference_roots={"fixture": str(references)}, data_dir=str(run / "data"), batch_size=2)
    if os.environ.get('RAG_TEST_MODEL_CACHE'):
        values['model_cache_dir']=os.environ['RAG_TEST_MODEL_CACHE']
    if os.environ.get('RAG_TEST_UV_CACHE'):
        values['uv_cache_dir']=os.environ['RAG_TEST_UV_CACHE']
    config_file = run / "config.json"
    write_json(config_file, values)
    config = Config(values)
    jobs = Jobs(config.data_dir)
    checks = []
    def record(name, passed, fail_fast=True, **details):
        checks.append({"name": name, "passed": bool(passed), **details})
        print(json.dumps(checks[-1], ensure_ascii=False), flush=True)
        if fail_fast:
            assert passed, name
    lock = FileLock(str(config.data_dir / "worker.lock"))
    try:
        with lock:
            async with connect(config_file, via_uv=True) as (session, _):
                job = await call(session, "register_pdf", wiki_root=str(wiki), source=str(source), source_page="sources/controls.md")
                identity = job["job_id"]
                rejected = await session.call_tool("configure", {"reference_roots": {"fixture": str(references)}})
                record("configure_rejects_unfinished_jobs", rejected.isError)
                pending = asyncio.create_task(call(session, "job_status", wiki_root=str(wiki), job_id=identity, wait_seconds=30))
                await asyncio.sleep(.1)
                started = time.perf_counter()
                cancel = await call(session, "cancel_job", wiki_root=str(wiki), job_id=identity)
                cancel_returned = time.perf_counter()
                waited = await pending
                record("long_poll_does_not_block_cancel", cancel["cancellation_accepted"] and waited["status"] == "cancelled" and time.perf_counter()-started < 2,
                       cancel_seconds=time.perf_counter()-started,
                       cancel_call_seconds=cancel_returned-started,
                       pending_completion_seconds=time.perf_counter()-cancel_returned,
                       fail_fast=False)
        async with connect(config_file, via_uv=True) as (session, _):
            await asyncio.sleep(.5)
            state = await call(session, "job_status", wiki_root=str(wiki), job_id=identity)
            record("cancelled_job_not_resumed_after_reconnect", state["status"] == "cancelled" and state["attempts"] == 0)
            await call(session, "retry_job", wiki_root=str(wiki), job_id=identity)
            def finished():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed": raise RuntimeError(state["error"])
                return state if state["status"] == "completed" else None
            result = await wait_until(finished, 600)
            record("explicit_retry_runs_real_embedding", result["attempts"] == 1 and result["result"]["pages"] == 4)
        async with connect(config_file, via_uv=True) as (session, _):
            await asyncio.sleep(.5)
            result = await call(session, "job_status", wiki_root=str(wiki), job_id=identity, wait_seconds=30)
            record("completed_job_is_not_reexecuted", result["status"] == "completed" and result["attempts"] == 1)
        assert all(check['passed'] for check in checks), '制御試験に失敗した項目があります。'
    finally:
        write_json(OUT / "controls-results.json", {"run_dir": str(run), "checks": checks})


if __name__ == "__main__":
    asyncio.run(main())
