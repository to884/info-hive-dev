"""実プロセスと stdio MCP を使う中断・再開 PoC。"""
from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from job_core import Store

ROOT = Path(__file__).resolve().parent
WORK = Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04"
SOURCE = WORK / "fixtures/protocol.pdf"
RUN = WORK / f"protocol-{time.time_ns()}"
RUN.mkdir(parents=True)
RESULTS = []


def record(name, passed, **details):
    RESULTS.append({"name": name, "passed": bool(passed), **details})
    print(json.dumps(RESULTS[-1], ensure_ascii=False), flush=True)


@asynccontextmanager
async def client(db, mode="child", delay=.06):
    pid_file = db.with_suffix(".pid.json")
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "job_app.py"), "server", "--db", str(db), "--mode", mode,
                                                               "--delay", str(delay), "--lease", ".5", "--pid-file", str(pid_file)],
                                   env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield session, pid_file


async def call(session, name, **values):
    result = await session.call_tool(name, values)
    if result.isError:
        raise RuntimeError(str(result.content))
    if result.structuredContent:
        return result.structuredContent
    return json.loads(result.content[0].text)


async def wait_for(store, identity, predicate, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = store.status(identity)
        if predicate(state):
            return state
        await asyncio.sleep(.03)
    raise TimeoutError(store.status(identity))


async def main():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    wiki = str(RUN / "wiki-a")
    db = RUN / "main.sqlite"
    store = Store(str(db))
    start = time.perf_counter()
    submitted = store.submit(wiki, str(SOURCE))
    direct_ms = (time.perf_counter() - start) * 1000
    cli = subprocess.run([sys.executable, str(ROOT / "job_app.py"), "submit", "--db", str(db), "--wiki", wiki, "--source", str(SOURCE)],
                         capture_output=True, encoding="utf-8", check=True)
    async with client(db, "none") as (session, _):
        mcp = await call(session, "submit", wiki=wiki, source=str(SOURCE))
        samples = []
        for _ in range(20):
            start = time.perf_counter()
            await call(session, "status", identity=submitted["id"])
            samples.append((time.perf_counter() - start) * 1000)
        record("P0_same_job_core_cli_mcp", submitted["id"] == json.loads(cli.stdout)["id"] == mcp["id"],
               submit_ms=direct_ms, status_p50_ms=statistics.median(samples), status_p95_ms=sorted(samples)[18], status=mcp["status"])
        record("P0_acceptance_not_completion", mcp["status"] == "queued" and not store.active(wiki, str(SOURCE)))
        start = time.perf_counter()
        synchronous = await call(session, "run_sync", wiki=wiki, source=str(SOURCE))
        record("P0_sync_mcp_same_job_and_completion", synchronous["id"] == submitted["id"] and synchronous["status"] == "completed",
               synchronous_ms=(time.perf_counter()-start)*1000)
    with concurrent.futures.ThreadPoolExecutor(8) as executor:
        ids = list(executor.map(lambda _: store.submit(wiki, str(SOURCE))["id"], range(32)))
    record("P1_concurrent_duplicate_submit", len(set(ids)) == 1)
    other = store.submit(str(RUN / "wiki-b"), str(SOURCE))
    record("P1_wiki_isolation", other["id"] != submitted["id"] and not store.active(str(RUN / "wiki-b"), str(SOURCE)))

    for mode in ("thread", "child"):
        scoped = RUN / f"{mode}.sqlite"
        local = Store(str(scoped))
        job = local.submit(wiki, str(SOURCE))
        killed_pids = []
        async with client(scoped, mode, .12) as (session, pid_file):
            state = await wait_for(local, job["id"], lambda state: 2 <= state["completed"] < 8)
            checkpoint = state["completed"]
            record(f"P1_{mode}_unpublished_partial", not local.active(wiki, str(SOURCE)), checkpoint=checkpoint)
            process_ids = json.loads(pid_file.read_text(encoding="utf-8"))
            server = psutil.Process(process_ids["server"])
            children = server.children(recursive=True)
            for process in reversed(children):
                killed_pids.append(process.pid)
                process.kill()
            killed_pids.append(server.pid)
            server.kill()
            psutil.wait_procs(children + [server], timeout=5)
        await asyncio.sleep(.6)
        async with client(scoped, mode, .02):
            finished = await wait_for(local, job["id"], lambda state: state["status"] == "completed")
        with local.connect() as connection:
            executions = connection.execute("SELECT step,COUNT(*) n FROM executions GROUP BY step").fetchall()
        record(f"P1_{mode}_forced_kill_resume", finished["completed"] == 10 and len(executions) == 10 and all(row["n"] == 1 for row in executions),
               attempts=finished["attempts"], initial_checkpoint=checkpoint, published_pages=len(local.active(wiki, str(SOURCE))),
               killed_processes_gone=all(not psutil.pid_exists(pid) for pid in killed_pids))
        # 明示キャンセルは、次回のサーバー起動でも再開しない。
        cancelled = local.submit(wiki, str(SOURCE), "cancel-case")
        async with client(scoped, mode, .1) as (session, _):
            await wait_for(local, cancelled["id"], lambda state: state["completed"] >= 1)
            result = await call(session, "cancel", identity=cancelled["id"])
            saved = result["completed"]
        async with client(scoped, mode):
            await asyncio.sleep(.25)
        cancelled_state = local.status(cancelled["id"])
        record(f"P1_{mode}_cancel_not_resumed", cancelled_state["status"] == "cancelled" and cancelled_state["completed"] == saved)

    failed_db = RUN / "failure.sqlite"
    failed_store = Store(str(failed_db))
    original = failed_store.submit(wiki, str(SOURCE), "old")
    failed_store.work_once()
    published = failed_store.active(wiki, str(SOURCE))
    changed = failed_store.submit(wiki, str(SOURCE), "new")
    failed_store.work_once(fail_at=2)
    record("P1_failed_generation_preserves_previous", failed_store.status(changed["id"])["status"] == "failed" and failed_store.active(wiki, str(SOURCE)) == published)
    failed_store.retry(changed["id"])
    failed_store.work_once()
    record("P1_retry_after_failure", failed_store.status(changed["id"])["status"] == "completed" and len(failed_store.active(wiki, str(SOURCE))) == 10)
    record("P1_source_unchanged", hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before)
    product_server = (ROOT.parents[1] / "info-hive-rag/scripts/rag_server.py").read_text(encoding="utf-8")
    ingest = (ROOT.parents[1] / "info-hive-wiki/commands/ingest.md").read_text(encoding="utf-8")
    record("P2_product_bridge_present", "register_pdf" in product_server and ("ingest_pdf" in ingest or "register_pdf" in ingest),
           note="静的な接続有無の検査。Claude Code の実セッション E2E の代用にはしない。")
    product_wiki = RUN / "product-wiki"
    (product_wiki / "sources").mkdir(parents=True)
    (product_wiki / "SCHEMA.md").write_text("# PoC wiki\n", encoding="utf-8")
    config_file = RUN / "product-config.json"
    config_file.write_text(json.dumps({"reference_roots": {"fixture": str(SOURCE.parent)}, "data_dir": str(RUN / "product-data")}), encoding="utf-8")
    parameters = StdioServerParameters(command=sys.executable, args=[str(ROOT.parents[1] / "info-hive-rag/scripts/rag_server.py")],
                                      env={**os.environ, "INFO_HIVE_RAG_CONFIG": str(config_file), "PYTHONUTF8": "1"})
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool("ingest_pdf", {"wiki_root": str(product_wiki), "source": str(SOURCE), "source_page": "sources/fixture.md"})
            record("P2_current_product_pdf_ingest", not result.isError,
                   response=[item.text for item in result.content if hasattr(item, "text")])
    output = ROOT.parents[1] / "docs/research/rag-poc-2026-11-04"
    output.mkdir(parents=True, exist_ok=True)
    (output / "protocol-results.json").write_text(json.dumps({"run_dir": str(RUN), "checks": RESULTS}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
