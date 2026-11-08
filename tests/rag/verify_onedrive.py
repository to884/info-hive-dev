"""OneDrive の同期のアプリが動いているときに、オンラインだけの PDF を登録から検索まで通す。

RAG_TEST_ONEDRIVE_PDF に、ローカルに実体のない（RECALL_ON_DATA_ACCESS の）PDF の絶対パスを指定する。
読み込むと同期のアプリが実体を取得する。試験の終わりに `attrib -P +U` でオンラインだけに戻す。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

if sys.platform != "win32":
    raise SystemExit("この試験は Windows だけで動く。")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_pipeline as base  # noqa: E402
from rag_config import Config, write_json  # noqa: E402
from rag_jobs import Jobs  # noqa: E402

ROOT = base.ROOT
SOURCE = Path(os.environ["RAG_TEST_ONEDRIVE_PDF"])
RUN = Path(os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data"))) / f"o{int(time.time())}"
OUT = Path(os.environ.get("RAG_TEST_OUTPUT", str(ROOT / "docs/research/rag-network-and-onedrive-2026-11-09")))
RECALL_ON_DATA_ACCESS = 0x400000
record = base.record


def attributes(path: Path) -> int:
    return os.stat(path, follow_symlinks=False).st_file_attributes


def onedrive_running() -> bool:
    listing = subprocess.run(["tasklist", "/FI", "IMAGENAME eq OneDrive.exe", "/NH"],
                             capture_output=True, text=True, encoding="cp932", errors="replace")
    return "OneDrive.exe" in listing.stdout


async def main():
    RUN.mkdir(parents=True)
    record("onedrive_app_running", onedrive_running())
    before = attributes(SOURCE)
    record("source_is_online_only", bool(before & RECALL_ON_DATA_ACCESS), attributes=hex(before))
    wiki = RUN / "wiki"
    (wiki / "sources").mkdir(parents=True)
    for name, text in (("SCHEMA.md", "# 検証用 wiki\n"), ("index.md", "# 検証用 wiki\n"), ("log.md", "# 操作記録\n")):
        (wiki / name).write_text(text, encoding="utf-8")
    config_file = RUN / "config.json"
    write_json(config_file, {"data_dir": str(RUN / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m",
        "cpu_threads": 4, "batch_size": 8,
        "model_cache_dir": os.environ.get("RAG_TEST_MODEL_CACHE", str(base.WORK / "models")),
        "uv_cache_dir": str(Path(os.environ.get("RAG_TEST_UV_CACHE") or subprocess.check_output(["uv", "cache", "dir"], encoding="utf-8").strip()).resolve())})
    config = Config(json.loads(config_file.read_text(encoding="utf-8")))
    jobs = Jobs(config.data_dir)
    try:
        async with base.connect(config_file) as (session, _server):
            started = time.perf_counter()
            submitted = await base.call(session, "register_pdf", wiki_root=str(wiki), source=str(SOURCE),
                                        source_page="sources/onedrive.md", title="OneDrive の原本")
            identity = submitted["job_id"]
            record("online_only_registers_without_reading", submitted["status"] in {"queued", "running"},
                   milliseconds=(time.perf_counter() - started) * 1000)

            def finished():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed":
                    raise RuntimeError(state["error"])
                return state if state["status"] == "completed" else None
            started = time.perf_counter()
            await base.wait_until(finished, 1800)
            result = await base.call(session, "job_status", wiki_root=str(wiki), job_id=identity)
            record("online_only_completes", True, seconds=round(time.perf_counter() - started, 1),
                   pages=result["result"]["pages"], chunks=result["result"]["chunks"])
            answer = await base.call(session, "search", wiki_root=str(wiki), query="manual", limit=3)
            record("online_only_searchable", bool(answer["results"]) and all(r["source_pages"] == ["sources/onedrive.md"] for r in answer["results"]))
            catalog = await base.call(session, "status", wiki_root=str(wiki))
            record("status_has_one_document", catalog["documents"] == 1)
        record("hydrated_after_read", not (attributes(SOURCE) & RECALL_ON_DATA_ACCESS), attributes=hex(attributes(SOURCE)))
        digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        with sqlite3.connect(config.workspace(str(wiki)) / "catalog.sqlite") as catalog_db:
            recorded = [row[0] for row in catalog_db.execute("SELECT doc_id FROM locations")]
        record("doc_id_matches_content", recorded == [digest], sha256=digest, recorded=recorded)
    finally:
        restored = subprocess.run(["attrib", "-P", "+U", str(SOURCE)], capture_output=True, text=True,
                                  encoding="cp932", errors="replace")
        time.sleep(5)
        after = attributes(SOURCE)
        record("restored_to_online_only", restored.returncode == 0 and bool(after & RECALL_ON_DATA_ACCESS),
               attributes=hex(after), output=(restored.stdout + restored.stderr).strip())
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "onedrive-results.json", {"run_dir": str(RUN), "source": SOURCE.name, "checks": base.RESULTS})


if __name__ == "__main__":
    asyncio.run(main())
