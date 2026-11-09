"""製品 MCP の PDF 登録から、実 OCR・埋め込みの中断と再開まで検証する。"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
import unicodedata
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config, write_json
from rag_jobs import Jobs

WORK = Path(os.environ.get("RAG_TEST_WORK", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".cache"))) / "info-hive/rag-poc/2026-11-04"))).resolve()
RUN = Path(os.environ.get("RAG_TEST_RUN_ROOT", str(POC_DATA))) / f"j{int(time.time())}"
OUT = Path(os.environ.get("RAG_TEST_OUTPUT", str(ROOT / "docs/research/rag-pdf-job-integration-2026-11-04")))
RESULTS = []


def record(name, passed, **values):
    row = {"name": name, "passed": bool(passed), **values}
    RESULTS.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if not passed:
        raise AssertionError(name)


def fixture(path: Path):
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    for number in range(1, 41):
        pdf.setFont("HeiseiMin-W3", 18)
        pdf.drawString(40, 780, f"永続ジョブの検証：第 {number} 章")
        pdf.setFont("HeiseiMin-W3", 12)
        for line, text in enumerate([
            "原本を変更せずに参照し、ページごとに抽出結果を保存します。",
            "中断した処理は、保存済みのページと埋め込みバッチから再開します。",
            "受付と索引化の完了を区別し、途中の索引は検索に公開しません。",
            "再開識別子は、おおたかです。出典にはページ番号を付けます。",
        ]):
            pdf.drawString(40, 720 - line * 30, text)
        pdf.showPage()
    font = ImageFont.truetype(os.environ.get("RAG_TEST_FONT", r"C:\Windows\Fonts\meiryo.ttc"), 44)
    for vertical in (False, True):
        image = Image.new("RGB", (1000, 1400), "white")
        draw = ImageDraw.Draw(image)
        text = "原本は複製しません。進捗を保存して再開します。"
        if vertical:
            for index, char in enumerate(text):
                draw.text((800 - index // 18 * 75, 80 + index % 18 * 60), char, fill="black", font=font)
        else:
            for line, value in enumerate(["日本語の検索検証", "原本は複製しません。", "進捗を保存して再開します。"]):
                draw.text((60, 120 + line * 100), value, fill="black", font=font)
        pdf.drawImage(ImageReader(image), 0, 0, width=595, height=842)
        pdf.showPage()
    pdf.save()


@asynccontextmanager
async def connect(config: Path, via_uv: bool = False):
    before = {p.pid for p in psutil.Process().children(recursive=True)}
    manifest = json.loads((ROOT / "info-hive-rag/.mcp.json").read_text(encoding="utf-8"))["mcpServers"]["rag"]
    parameters = StdioServerParameters(command=manifest["command"] if via_uv else sys.executable,
        args=[arg.replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT / "info-hive-rag")) for arg in manifest["args"]] if via_uv else [str(ROOT / "info-hive-rag/scripts/rag_server.py")],
        env={**os.environ, "INFO_HIVE_RAG_CONFIG": str(config), "PYTHONUTF8": "1",
             "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            candidates = []
            for process in psutil.Process().children(recursive=True):
                try:
                    if process.pid not in before and any(arg.replace("\\", "/").endswith("/rag_server.py") for arg in process.cmdline()):
                        candidates.append(process)
                except psutil.NoSuchProcess:
                    pass
            server = max(candidates, key=lambda p: len(p.parents()))
            yield session, server


async def call(session, name, **values):
    result = await session.call_tool(name, values)
    if result.isError:
        raise RuntimeError(str(result.content))
    return result.structuredContent or json.loads(result.content[0].text)


async def wait_until(predicate, timeout=300):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        await asyncio.sleep(.015)
    raise TimeoutError("進捗の待機が時間切れになりました。")


async def kill_server(server, phase):
    descendants = server.children(recursive=True)
    server.kill()  # 子ワーカーは手動で kill しない。親の消失を自分で検出させる。
    _, alive = psutil.wait_procs(descendants + [server], timeout=12)
    record(phase + "_parent_death_stops_descendants", not alive, descendants=len(descendants))


async def main():
    RUN.mkdir(parents=True)
    references = RUN / "references"
    references.mkdir()
    source = references / "日本語の再開検証.pdf"
    fixture(source)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    wiki = RUN / "wiki"
    (wiki / "sources").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_text("# 検証用 wiki\n", encoding="utf-8")
    (wiki / "index.md").write_text("# 検証用 wiki\n", encoding="utf-8")
    (wiki / "log.md").write_text("# 操作記録\n", encoding="utf-8")
    config_file = RUN / "config.json"
    write_json(config_file, {"data_dir": str(RUN / "data"),
        "embedding_model": "cl-nagoya/ruri-v3-30m", "cpu_threads": 4, "batch_size": 1,
        "model_cache_dir": os.environ.get("RAG_TEST_MODEL_CACHE", str(WORK / "models")),
        "uv_cache_dir": str(Path(os.environ.get("RAG_TEST_UV_CACHE") or subprocess.check_output(["uv", "cache", "dir"], encoding="utf-8").strip()).resolve())})
    config = Config(json.loads(config_file.read_text(encoding="utf-8")))
    jobs = Jobs(config.data_dir)
    folder = config.workspace(str(wiki))
    try:
        async with connect(config_file) as (session, server):
            started = time.perf_counter()
            submitted = await call(session, "register_pdf", wiki_root=str(wiki), source=str(source),
                                   source_page="sources/日本語の再開検証.md", title="日本語の再開検証")
            identity = submitted["job_id"]
            record("registration_is_short_and_persistent", submitted["status"] in {"queued", "running"},
                   milliseconds=(time.perf_counter()-started)*1000, job_id=identity)
            duplicate = await call(session, "ingest_pdf", wiki_root=str(wiki), source=str(source),
                                   source_page="sources/日本語の再開検証.md", title="日本語の再開検証")
            record("ingest_alias_deduplicates_registration", duplicate["job_id"] == identity)
            def ocr_started():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed": raise RuntimeError(state["error"])
                # 抽出の結果は data_dir/extracted/<SHA-256>/<抽出の設定>/ に置く（ADR-0014）。
                pages = list(config.extraction_root.glob("*/*/page-*.json"))
                descendants = server.children(recursive=True)
                ocr = [p for p in descendants if any("rag_ocr.py" in arg for arg in p.cmdline())]
                return pages if len(pages) == 40 and ocr else None
            cached = await wait_until(ocr_started)
            saved_hashes = {p.name: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in cached}
            cache = cached[0].parent
            state = await call(session, "status", wiki_root=str(wiki))
            record("ocr_partial_generation_not_published", state["documents"] == 0, cached_pages=len(cached))
            await kill_server(server, "ocr")
        paused = jobs.status(str(wiki), identity)
        record("ocr_job_saved_after_parent_death", paused["status"] == "paused", phase=paused["phase"])

        async with connect(config_file) as (session, server):
            def embedding_saved():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed": raise RuntimeError(state["error"])
                return state if state["phase"] == "埋め込み" and 1 <= state["completed"] < state["total"] else None
            partial = await wait_until(embedding_saved, 600)
            record("real_ocr_completed_before_embedding", len(list(cache.glob("page-*.json"))) == 42)
            record("text_pages_reused_on_resume", all((cache/name).stat().st_mtime_ns == value[0] and hashlib.sha256((cache/name).read_bytes()).hexdigest() == value[1] for name,value in saved_hashes.items()))
            record("embedding_checkpoint_saved", partial["completed"] > 0, completed=partial["completed"], total=partial["total"])
            await kill_server(server, "embedding")
        record("embedding_job_saved_after_parent_death", jobs.status(str(wiki), identity)["status"] == "paused")
        page_mtimes = {p.name: p.stat().st_mtime_ns for p in cache.glob("page-*.json")}

        async with connect(config_file) as (session, server):
            def finished():
                state = jobs.status(str(wiki), identity)
                if state["status"] == "failed": raise RuntimeError(state["error"])
                return state if state["status"] == "completed" else None
            completed = await wait_until(finished, 300)
            result = await call(session, "job_status", wiki_root=str(wiki), job_id=identity)
            record("reconnect_completes_same_job", result["job_id"] == identity and result["attempts"] == 3,
                   attempts=result["attempts"], pages=result["result"]["pages"], chunks=result["result"]["chunks"])
            record("all_extracted_pages_reused", all((cache/name).stat().st_mtime_ns == stamp for name,stamp in page_mtimes.items()))
            import lancedb
            table = lancedb.connect(str(folder / "lance")).open_table("chunks")
            rows = table.to_arrow().to_pylist()
            record("embedding_resume_has_no_duplicate_rows", len(rows) == len({r["chunk_id"] for r in rows}) == result["result"]["chunks"])
            answer = await call(session, "search", wiki_root=str(wiki), query="中断した処理はどこから再開しますか", limit=3)
            record("completed_generation_searchable_with_citations", bool(answer["results"]) and all(r["source_pages"] == ["sources/日本語の再開検証.md"] and r["page"] > 0 for r in answer["results"]))
            state = await call(session, "status", wiki_root=str(wiki))
            record("published_document_count", state["documents"] == 1 and state["chunks"] == len(rows))
            record("extracted_markdown_available", Path(result["result"]["extracted_markdown"]).is_file())
        normalize = lambda text: "".join(unicodedata.normalize("NFKC", text).split())
        scan = json.loads((cache / "page-000041.json").read_text(encoding="utf-8"))
        vertical = json.loads((cache / "page-000042.json").read_text(encoding="utf-8"))
        record("horizontal_and_vertical_real_ocr", scan["ocr"] and vertical["ocr"] and "進捗を保存して再開します。" in normalize(scan["text"]) and "進捗を保存して再開します。" in normalize(vertical["text"]))
        record("original_pdf_unchanged", hashlib.sha256(source.read_bytes()).hexdigest() == before)
    finally:
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "pipeline-results.json", {"run_dir": str(RUN), "checks": RESULTS})


if __name__ == "__main__":
    asyncio.run(main())
