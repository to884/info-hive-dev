"""Windows の実物のネットワークドライブで、PDF の登録から検索までを確かめる。

自分の PC の管理共有（既定は \\\\localhost\\C$）を、空いているドライブ文字に `net use` で一時的に割り当てる。
SMB を通る本物のネットワークパスになる。割り当ては、試験の終わりに必ず外す。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import string
import subprocess
import sys
import time
from pathlib import Path

if sys.platform != "win32":
    raise SystemExit("この試験は Windows だけで動く。")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_pipeline as base  # noqa: E402
from rag_config import Config, write_json  # noqa: E402
from rag_index import Engine  # noqa: E402
from rag_jobs import Jobs  # noqa: E402

ROOT = base.ROOT
SHARE = os.environ.get("RAG_TEST_SHARE", r"\\localhost\C$")
RUN = Path(os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data"))) / f"n{int(time.time())}"
OUT = Path(os.environ.get("RAG_TEST_OUTPUT", str(ROOT / "docs/research/rag-network-and-onedrive-2026-11-09")))
record = base.record


def fixture(path: Path):
    """OCR を通らない、文字のページだけの PDF を作る。"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    for number in range(1, 4):
        pdf.setFont("HeiseiMin-W3", 14)
        pdf.drawString(40, 780, f"ネットワークドライブの検証：第 {number} 節")
        pdf.drawString(40, 740, "共有フォルダーに置いた原本を、複製せずに参照して索引に入れます。")
        pdf.showPage()
    pdf.save()


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="cp932", errors="replace")


def free_letter() -> str:
    used = {p[0].upper() for p in os.listdrives()} if hasattr(os, "listdrives") else set()
    for letter in reversed(string.ascii_uppercase[4:]):
        if letter not in used and not Path(f"{letter}:\\").exists():
            return letter + ":"
    raise RuntimeError("空いているドライブ文字がない。")


async def main():
    RUN.mkdir(parents=True)
    references = RUN / "references"
    references.mkdir()
    local = references / "ネットワークの原本.pdf"
    fixture(local)
    before = hashlib.sha256(local.read_bytes()).hexdigest()
    drive, rest = os.path.splitdrive(str(references))
    if drive.upper() != "C:" and SHARE.lower().endswith("\\c$"):
        raise SystemExit("RAG_TEST_RUN_ROOT は C: に置くか、RAG_TEST_SHARE を合わせて指定する。")
    unc_folder = SHARE.rstrip("\\") + rest
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
    letter = free_letter()
    mapped = run("net", "use", letter, unc_folder, "/persistent:no")
    record("drive_mapped", mapped.returncode == 0, letter=letter, target=unc_folder, output=(mapped.stdout + mapped.stderr).strip())
    try:
        source = f"{letter}\\{local.name}"
        resolved = config.pdf_path(source)
        record("mapped_drive_resolves_to_unc", str(resolved).lower().startswith(SHARE.lower()), resolved=str(resolved))
        async with base.connect(config_file) as (session, _server):
            try:
                await base.call(session, "register_pdf", wiki_root=str(wiki), source=str(Path(unc_folder) / local.name),
                                source_page="sources/ネットワークの原本.md")
                rejected, message = False, ""
            except RuntimeError as error:
                rejected, message = True, str(error)
            record("unc_source_rejected", rejected and "UNC" in message, message=message[:200])
            started = time.perf_counter()
            submitted = await base.call(session, "register_pdf", wiki_root=str(wiki), source=source,
                                        source_page="sources/ネットワークの原本.md", title="ネットワークの原本")
            identity = submitted["job_id"]
            record("mapped_drive_registers", submitted["status"] in {"queued", "running"},
                   milliseconds=(time.perf_counter() - started) * 1000)

            def finished():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed":
                    raise RuntimeError(state["error"])
                return state if state["status"] == "completed" else None
            completed = await base.wait_until(finished, 600)
            result = await base.call(session, "job_status", wiki_root=str(wiki), job_id=identity)
            record("mapped_drive_completes", completed["status"] == "completed",
                   pages=result["result"]["pages"], chunks=result["result"]["chunks"])
            answer = await base.call(session, "search", wiki_root=str(wiki), query="共有フォルダーの原本を索引に入れる", limit=3)
            record("mapped_drive_searchable", bool(answer["results"]) and all(r["source_pages"] == ["sources/ネットワークの原本.md"] for r in answer["results"]))
            extracted = list(config.extraction_root.glob("*/*/document.md"))
            record("extraction_kept_on_local_data_dir", len(extracted) == 1 and not str(extracted[0]).startswith("\\\\"), path=str(extracted[0]) if extracted else "")
            state = await base.call(session, "status", wiki_root=str(wiki))
            record("status_has_no_reingest", not state.get("reingest_required") and state["documents"] == 1)
    finally:
        removed = run("net", "use", letter, "/delete", "/y")
        record("drive_unmapped", removed.returncode == 0 and not Path(f"{letter}\\").exists(), output=(removed.stdout + removed.stderr).strip())
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "network-drive-results.json", {"run_dir": str(RUN), "share": SHARE, "checks": base.RESULTS})
    # 割り当てを外したあとも、解決した UNC の場所はたどれるので、消えたとはみなさない。
    record("unc_place_not_gone_after_unmap", not Engine._gone(str(resolved)))
    # 届かないサーバーの UNC は、ファイルもフォルダーも見えないので、消えたとはみなさない。
    unreachable = r"\\info-hive-no-such-host.invalid\share\missing.pdf"
    started = time.perf_counter()
    record("unreachable_server_not_gone", not Engine._gone(unreachable), seconds=round(time.perf_counter() - started, 2))
    record("original_pdf_unchanged", hashlib.sha256(local.read_bytes()).hexdigest() == before)
    write_json(OUT / "network-drive-results.json", {"run_dir": str(RUN), "share": SHARE, "checks": base.RESULTS})


if __name__ == "__main__":
    asyncio.run(main())
