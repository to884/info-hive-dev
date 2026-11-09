"""検証用の全量データの抽出と OCR を、rag 0.5.0 の製品の関数で進め、製品と同じ鍵と形で残す。

製品の `rag_pdf.extract_pages()` を文書ごとに呼ぶ。結果は rag の data_dir の
`extracted/<内容の SHA-256>/<ocr_mode>-<ocr_dpi>-<OCR_REVISION の先頭 12 文字>-<EXTRACT_REVISION>/`
に、ページごとの `page-<6 桁>.json` と `document.md` として置く（ADR-0014）。
ページのファイルは 1 枚ずつ確定するので、どこで止めても、次の起動で保存済みのページを読み直して続ける。

サブコマンド:
  start    rag のスクリプトを固定した写しと台帳を用意し、セッションから切り離して run を起動する。
  run      前面で処理する（start が起動する）。
  stop     STOP ファイルを置き、処理を止める。
  status   進み具合（progress.json）を表示する。
  compare  2026-11-04 の PoC の経路で OCR したページと、製品の経路の結果を比べる。

原本の PDF は読むだけで、移動・複製・書き換えはしない。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import multiprocessing as mp
import os
import queue
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import io
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
RAG_EXTRACT_KEY_DEFAULTS = {"ocr_mode": "auto", "ocr_dpi": 150}
# 2026-11-04 の計画で数えた、auto が OCR に回すページの数（重複を除いた 905 文書）。製品の判定で数え直すまでの目安。
PLANNED_OCR_PAGES = 22335


def _default_poc_data() -> Path:
    try:
        sys.path.insert(0, str(HERE.parents[2]))
        from poc_data import POC_DATA
        return POC_DATA
    except ImportError:
        # 作業領域に写したこのスクリプトから起動したときは、作業領域の 1 つ上が POC_DATA である。
        return HERE.parents[2]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for attempt in range(8):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    os.replace(temporary, path)


class Layout:
    """作業領域の配置。"""

    def __init__(self, workspace: Path):
        self.root = workspace.resolve()
        self.data_dir = self.root / "data"          # rag の data_dir。extracted/ と uv-cache/ を置く
        self.rag_root = self.root / "rag"           # 固定した rag のスクリプトの写し
        self.bin = self.root / "bin"                # 起動に使うこのスクリプトの写し
        self.ledger = self.root / "ledger.sqlite"
        self.policy = self.root / "run-policy.json"
        self.progress = self.root / "progress.json"
        self.history = self.root / "progress-history.jsonl"
        self.log = self.root / "run.log"
        self.stop = self.root / "STOP"
        self.pid = self.root / "runner.pid"
        self.comparison = self.root / "poc-comparison.json"


# ---------------------------------------------------------------- 準備

def pinned_rag_commit(repo: Path) -> str:
    out = subprocess.run(["git", "-C", str(repo), "ls-tree", "HEAD", "info-hive-rag"], capture_output=True,
                         text=True, encoding="utf-8", check=True).stdout.split()
    return out[2]


def freeze_rag(layout: Layout, repo: Path, main: Path) -> Path:
    """開発リポジトリが固定した rag のコミットのスクリプトを、作業領域に写す。
    worktree を消したり、サブモジュールを別の版に進めたりしても、走っている処理の読むコードが変わらないようにする。"""
    commit = pinned_rag_commit(repo)
    target = layout.rag_root / commit[:12]
    if (target / "scripts" / "rag_pdf.py").is_file():
        return target / "scripts"
    archive = subprocess.run(["git", "-C", str(main / "info-hive-rag"), "archive", "--format=tar", commit,
                              "scripts", ".claude-plugin/plugin.json"], capture_output=True, check=True).stdout
    staging = target.with_name(target.name + ".tmp")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(staging, filter="data")
    os.replace(staging, target)
    return target / "scripts"


def build_ledger(layout: Layout, base: Path, poc_work: Path) -> None:
    db = sqlite3.connect(layout.ledger)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS documents(
          doc_id TEXT PRIMARY KEY, relative_path TEXT, size INTEGER, mtime_ns INTEGER, pages INTEGER,
          planned_ocr INTEGER, poc_saved INTEGER, priority INTEGER,
          status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0, error TEXT,
          seconds REAL, ocr_pages INTEGER, ocr_empty INTEGER, ocr_new INTEGER, markdown INTEGER,
          started_at TEXT, finished_at TEXT);
    """)
    if db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]:
        db.close()
        return
    source = sqlite3.connect(f"file:{(base / 'corpus.sqlite').as_posix()}?mode=ro", uri=True)
    planned = dict(source.execute(
        "SELECT doc_id, COUNT(*) FROM pages WHERE json_extract(quality,'$.kind') IN ('scan','garbled','vertical') GROUP BY doc_id"))
    saved: dict[str, int] = {}
    if (poc_work / "ocr.sqlite").is_file():
        poc = sqlite3.connect(f"file:{(poc_work / 'ocr.sqlite').as_posix()}?mode=ro", uri=True)
        saved = dict(poc.execute("SELECT doc_id, COUNT(*) FROM targets WHERE status IN ('completed','empty') GROUP BY doc_id"))
        poc.close()
    rows = []
    # 同じ内容の PDF が複数の場所にあれば、1 つ（パスの最小）だけを処理する。鍵は内容の SHA-256 なので、結果は 1 つで足りる。
    for doc_id, relative, pages in source.execute(
            "SELECT doc_id, MIN(relative_path), MAX(pages) FROM documents WHERE status='completed' GROUP BY doc_id"):
        size, mtime = source.execute("SELECT size, mtime_ns FROM documents WHERE relative_path=?", (relative,)).fetchone()
        ocr = planned.get(doc_id, 0)
        # 順番: PoC の結果と比べられる文書、OCR の多い文書（最後に長い文書が 1 つだけ残らないように）、テキストだけの文書。
        priority = 0 if saved.get(doc_id) else (1 if ocr else 2)
        rows.append((doc_id, relative, size, mtime, pages, ocr, saved.get(doc_id, 0), priority))
    db.executemany("INSERT INTO documents(doc_id, relative_path, size, mtime_ns, pages, planned_ocr, poc_saved, priority)"
                   " VALUES (?,?,?,?,?,?,?,?)", rows)
    db.commit()
    db.close()
    source.close()


def run_policy(layout: Layout, scripts: Path, threads: int) -> dict:
    sys.path.insert(0, str(scripts))
    from rag_config import EXTRACT_REVISION, OCR_REVISION, Config
    config = Config({"data_dir": str(layout.data_dir), "cpu_threads": threads, **RAG_EXTRACT_KEY_DEFAULTS})
    plugin = json.loads((scripts.parent / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return {
        "rag_version": plugin["version"],
        "rag_commit_prefix": scripts.parent.name,
        "rag_scripts": str(scripts),
        "OCR_REVISION": OCR_REVISION,
        "EXTRACT_REVISION": EXTRACT_REVISION,
        "extraction_key": config.extraction_key,
        "ocr_mode": config.ocr_mode,
        "ocr_dpi": config.ocr_dpi,
        "data_dir": str(config.data_dir),
        "uv_cache_dir": str(config.uv_cache_dir),
        "ocr_runtime": "product_default_uv_script",
        "script_sha256": {name: sha256_file(scripts / name) for name in
                          ["rag_config.py", "rag_index.py", "rag_ocr.py", "rag_ocr_client.py", "rag_pdf.py"]},
    }


def check_policy(layout: Layout, policy: dict) -> None:
    """同じ作業領域に、違うコードや鍵の結果を混ぜない。鍵の中身が同じでも、コードが違えば止める。"""
    if layout.policy.exists():
        before = json.loads(layout.policy.read_text(encoding="utf-8"))
        keys = ["OCR_REVISION", "EXTRACT_REVISION", "extraction_key", "ocr_mode", "ocr_dpi", "data_dir", "script_sha256"]
        changed = [key for key in keys if before.get(key) != policy.get(key)]
        if changed:
            raise SystemExit(f"rag のコードか抽出の設定が前回と違います（{', '.join(changed)}）。"
                             "違う結果を混ぜないため、続けません。別の作業領域を指定してください。")
    write_json(layout.policy, {**policy, "created_at": json.loads(layout.policy.read_text(encoding="utf-8"))["created_at"]
                               if layout.policy.exists() else now()})


# ---------------------------------------------------------------- 子プロセス（文書ごとの抽出）

EVENTS = None
SETTINGS: dict = {}
CURRENT = {"doc_id": None}


def _lower_priority() -> None:
    import psutil
    try:
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
    except (psutil.Error, OSError):
        pass


def _watch_parent() -> None:
    """親が消えたら、認識中の OCR の子プロセスも含めて残さない。"""
    parent = mp.parent_process()
    if parent is None:
        return

    def closed():
        from multiprocessing.connection import wait
        wait([parent.sentinel])
        import psutil
        for child in reversed(psutil.Process().children(recursive=True)):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        os._exit(0)
    threading.Thread(target=closed, daemon=True).start()


def initialize(events, settings: dict) -> None:
    global EVENTS, SETTINGS
    EVENTS, SETTINGS = events, settings
    _lower_priority()
    _watch_parent()
    sys.path.insert(0, settings["scripts"])
    import rag_ocr_client
    original = rag_ocr_client.OcrClient.recognize

    def recognize(self, image, timeout=1800):
        # 製品の処理は変えず、OCR の 1 回ごとに時間と結果の有無を親に知らせる。
        started = time.perf_counter()
        response = original(self, image, timeout)
        EVENTS.put({"type": "ocr", "doc_id": CURRENT["doc_id"], "seconds": time.perf_counter() - started,
                    "empty": not response.get("text", "").strip()})
        return response
    rag_ocr_client.OcrClient.recognize = recognize


def _clean_leftovers(cache: Path) -> None:
    """強制終了で残った OCR の一時フォルダーと、書きかけの一時ファイルを消す。確定したページには触れない。"""
    if not cache.is_dir():
        return
    for item in cache.iterdir():
        if item.is_dir() and item.name.startswith("ocr-"):
            shutil.rmtree(item, ignore_errors=True)
        elif item.is_file() and item.name.endswith(".tmp"):
            item.unlink(missing_ok=True)


def extract_document(task: dict) -> dict:
    from filelock import FileLock
    from rag_config import Config
    from rag_index import Engine, read_pdf
    from rag_pdf import chunks_for, extract_pages

    started = time.perf_counter()
    CURRENT["doc_id"] = task["doc_id"]
    config = Config({"data_dir": SETTINGS["data_dir"], "cpu_threads": SETTINGS["threads"], **RAG_EXTRACT_KEY_DEFAULTS})
    path = Path(SETTINGS["source_root"]) / task["relative_path"]
    info = os.stat(path)
    if (info.st_size, info.st_mtime_ns) != (task["size"], task["mtime_ns"]):
        raise RuntimeError("原本のサイズか更新日時が、固定したときと違います。")
    data, _ = read_pdf(path)
    doc_id = hashlib.sha256(data).hexdigest()
    if doc_id != task["doc_id"]:
        raise RuntimeError("原本の内容の SHA-256 が、固定したときと違います。")
    config.extraction_root.mkdir(parents=True, exist_ok=True)
    cache = config.extraction_dir(doc_id)
    # 製品の取り込みと同じ、文書ごとのロックを取る（ADR-0014）。同じ data_dir を MCP が使っても競合しない。
    with FileLock(str(config.extraction_root / f"{doc_id}.lock"), timeout=600):
        _clean_leftovers(cache)
        before = {item.name for item in cache.glob("page-*.json")} if cache.is_dir() else set()

        def progress(_stage, number, total):
            EVENTS.put({"type": "page", "doc_id": doc_id, "number": number, "total": total})
        pages = extract_pages(data, config, cache, progress)
        markdown = cache / "document.md"
        # 製品は、検索できるテキストがない文書では document.md を書かない（取り込みを失敗にする）。それに合わせる。
        if chunks_for(pages, "", config) and not markdown.exists():
            Engine._write_markdown(markdown, pages)
    ocr = [page for page in pages if page["ocr"]]
    return {"doc_id": doc_id, "pages": len(pages), "ocr_pages": len(ocr),
            "ocr_empty": sum(page["ocr_empty"] for page in ocr),
            "ocr_new": sum(page["ocr"] and f"page-{page['page']:06d}.json" not in before for page in pages),
            "markdown": markdown.exists(), "seconds": time.perf_counter() - started}


# ---------------------------------------------------------------- 親プロセス

def _saved_ocr_pages(cache: Path) -> tuple[int, int]:
    """途中まで済んだ文書の、保存済みの OCR のページ数と、そのうち文字が得られなかったページ数。"""
    count = empty = 0
    if cache.is_dir():
        for item in cache.glob("page-*.json"):
            try:
                page = json.loads(item.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if page.get("ocr"):
                count += 1
                empty += bool(page.get("ocr_empty"))
    return count, empty


def run(args) -> None:
    layout = Layout(args.workspace)
    scripts = Path(args.scripts)
    sys.path.insert(0, str(scripts))
    _lower_priority()
    if args.uv_dir:
        os.environ["PATH"] = args.uv_dir + os.pathsep + os.environ.get("PATH", "")
    policy = run_policy(layout, scripts, args.threads)
    check_policy(layout, policy)
    layout.stop.unlink(missing_ok=True)
    layout.pid.write_text(str(os.getpid()), encoding="utf-8")
    from rag_config import Config
    config = Config({"data_dir": str(layout.data_dir), "cpu_threads": args.threads, **RAG_EXTRACT_KEY_DEFAULTS})

    db = sqlite3.connect(layout.ledger, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("UPDATE documents SET status='pending' WHERE status='running'")
    if args.retry_failed:
        db.execute("UPDATE documents SET status='pending', error=NULL WHERE status='failed'")
    db.commit()
    order = "priority, CASE priority WHEN 1 THEN -planned_ocr ELSE pages END, doc_id"
    todo = [dict(zip(["doc_id", "relative_path", "size", "mtime_ns"], row)) for row in db.execute(
        f"SELECT doc_id, relative_path, size, mtime_ns FROM documents WHERE status='pending' ORDER BY {order}")]
    if args.limit:
        todo = todo[:args.limit]
    # 途中まで済んだ文書の保存済みページを数えておく（進み具合の数を、再開しても正しく保つため）。
    partial = {}
    for task in todo:
        cache = config.extraction_dir(task["doc_id"])
        if cache.is_dir():
            partial[task["doc_id"]] = list(_saved_ocr_pages(cache))
    running: dict[str, dict] = {}
    run_started = time.time()
    rate_window: list[float] = []   # この実行で OCR したページの完了時刻
    totals = {"ocr_new_this_run": 0, "ocr_empty_this_run": 0}
    state = {"status": "running"}

    def progress(final: bool = False) -> dict:
        counts = dict(db.execute("SELECT status, COUNT(*) FROM documents GROUP BY status"))
        done_ocr, done_empty = db.execute(
            "SELECT COALESCE(SUM(ocr_pages),0), COALESCE(SUM(ocr_empty),0) FROM documents WHERE status='completed'").fetchone()
        saved = done_ocr + sum(value[0] for value in partial.values())
        empty = done_empty + sum(value[1] for value in partial.values())
        horizon = time.time() - 3600
        recent = [moment for moment in rate_window if moment >= horizon]
        rate_window[:] = recent
        elapsed = min(3600.0, time.time() - run_started)
        rate = len(recent) / elapsed * 3600 if elapsed > 120 else None
        remaining = max(0, PLANNED_OCR_PAGES - saved)
        record = {
            "updated_at": now(), "status": state["status"], "run_started_at": datetime.fromtimestamp(
                run_started, timezone.utc).astimezone().isoformat(timespec="seconds"),
            "extraction_key": policy["extraction_key"], "rag_version": policy["rag_version"],
            "data_dir": policy["data_dir"], "workers": args.workers, "threads_per_worker": args.threads,
            "documents": {"total": sum(counts.values()), **counts},
            "ocr_pages": {"saved": saved, "empty": empty, "planned_estimate": PLANNED_OCR_PAGES,
                          "new_this_run": totals["ocr_new_this_run"], "empty_this_run": totals["ocr_empty_this_run"]},
            "rate_ocr_pages_per_hour_last_hour": round(rate, 1) if rate else None,
            "eta_hours_estimate": round(remaining / rate, 1) if rate else None,
            "running": [{"relative_path": item["relative_path"], "page": item.get("page"), "pages": item.get("total")}
                        for item in running.values()],
        }
        write_json(layout.progress, record)
        return record

    context = mp.get_context("spawn")
    events = context.Queue()
    settings = {"scripts": str(scripts), "data_dir": str(layout.data_dir), "threads": args.threads,
                "source_root": args.source_root}
    pool = concurrent.futures.ProcessPoolExecutor(args.workers, mp_context=context, initializer=initialize,
                                                  initargs=(events, settings))
    pending = iter(todo)
    active: dict = {}

    def submit() -> None:
        task = next(pending, None)
        if task is None:
            return
        with db:
            db.execute("UPDATE documents SET status='running', attempts=attempts+1, started_at=? WHERE doc_id=?",
                       (now(), task["doc_id"]))
        running[task["doc_id"]] = dict(task)
        active[pool.submit(extract_document, task)] = task

    def drain() -> None:
        while True:
            try:
                event = events.get_nowait()
            except queue.Empty:
                return
            doc = event.get("doc_id")
            if event["type"] == "ocr":
                rate_window.append(time.time())
                totals["ocr_new_this_run"] += 1
                totals["ocr_empty_this_run"] += event["empty"]
                value = partial.setdefault(doc, [0, 0])
                value[0] += 1
                value[1] += event["empty"]
            elif event["type"] == "page" and doc in running:
                running[doc]["page"], running[doc]["total"] = event["number"], event["total"]

    last_progress = last_history = 0.0
    try:
        for _ in range(args.workers):
            submit()
        while active:
            time.sleep(0.5)
            drain()
            for future in [future for future in active if future.done()]:
                task = active.pop(future)
                drain()
                try:
                    result = future.result()
                    with db:
                        db.execute("UPDATE documents SET status='completed', error=NULL, seconds=?, ocr_pages=?, ocr_empty=?,"
                                   " ocr_new=?, markdown=?, pages=?, finished_at=? WHERE doc_id=?",
                                   (result["seconds"], result["ocr_pages"], result["ocr_empty"], result["ocr_new"],
                                    int(result["markdown"]), result["pages"], now(), task["doc_id"]))
                except concurrent.futures.process.BrokenProcessPool:
                    raise
                except Exception as error:  # noqa: BLE001 文書ごとの失敗は記録して次へ進む
                    with db:
                        db.execute("UPDATE documents SET status='failed', error=?, finished_at=? WHERE doc_id=?",
                                   (f"{type(error).__name__}: {error}"[:2000], now(), task["doc_id"]))
                    print(f"{now()} 失敗: {task['relative_path']}: {error}", flush=True)
                partial.pop(task["doc_id"], None)
                running.pop(task["doc_id"], None)
                if not layout.stop.exists():
                    submit()
            if layout.stop.exists():
                state["status"] = "stopped"
                break
            if time.time() - last_progress > 60:
                record = progress()
                last_progress = time.time()
                if time.time() - last_history > 1800:
                    with layout.history.open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({key: record[key] for key in
                                                 ["updated_at", "documents", "ocr_pages", "rate_ocr_pages_per_hour_last_hour",
                                                  "eta_hours_estimate"]}, ensure_ascii=False) + "\n")
                    last_history = time.time()
                    print(f"{now()} {json.dumps(record['ocr_pages'], ensure_ascii=False)}", flush=True)
        else:
            state["status"] = "completed" if not args.limit else "limit_reached"
    finally:
        if state["status"] == "running":
            state["status"] = "crashed"
        _stop_pool(pool)
        with db:
            db.execute("UPDATE documents SET status='pending' WHERE status='running'")
        drain()
        record = progress()
        with layout.history.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({key: record[key] for key in ["updated_at", "status", "documents", "ocr_pages"]},
                                    ensure_ascii=False) + "\n")
        print(f"{now()} 終了（{state['status']}）: {json.dumps(record['ocr_pages'], ensure_ascii=False)}", flush=True)
        db.close()
        events.close()
        layout.pid.unlink(missing_ok=True)


def _stop_pool(pool) -> None:
    """子プロセス（文書の抽出）と、その下の OCR のプロセスを止める。保存済みのページは残る。"""
    import psutil
    processes = list(getattr(pool, "_processes", {}).values())
    for process in processes:
        try:
            tree = psutil.Process(process.pid)
            for child in reversed(tree.children(recursive=True)):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            tree.kill()
        except psutil.NoSuchProcess:
            pass
    pool.shutdown(wait=False, cancel_futures=True)


# ---------------------------------------------------------------- 起動と停止

def start(args) -> None:
    layout = Layout(args.workspace)
    layout.root.mkdir(parents=True, exist_ok=True)
    if layout.pid.exists():
        import psutil
        pid = int(layout.pid.read_text(encoding="utf-8"))
        if psutil.pid_exists(pid) and "product_ocr" in " ".join(psutil.Process(pid).cmdline()):
            raise SystemExit(f"すでに動いています（PID {pid}）。")
    repo = HERE.parents[3]
    sys.path.insert(0, str(repo / "poc"))
    from poc_data import main_checkout
    main = main_checkout(repo)
    scripts = freeze_rag(layout, repo, main)
    base = Path(args.base)
    build_ledger(layout, base, Path(args.poc_work))
    source_root = json.loads((base / "manifest.json").read_text(encoding="utf-8"))["root"]
    layout.bin.mkdir(parents=True, exist_ok=True)
    runner = layout.bin / HERE.name
    shutil.copy2(HERE, runner)
    uv = shutil.which("uv")
    command = [sys.executable, "-X", "utf8", str(runner), "run", "--workspace", str(layout.root),
               "--scripts", str(scripts), "--source-root", source_root,
               "--workers", str(args.workers), "--threads", str(args.threads)]
    if uv:
        command += ["--uv-dir", str(Path(uv).parent)]
    if args.limit:
        command += ["--limit", str(args.limit)]
    if args.retry_failed:
        command += ["--retry-failed"]
    launcher = layout.bin / "launch.cmd"
    # 出力を run.log に残す。cmd を介して、WMI から起動する（このセッションのジョブの外で動かすため）。
    line = subprocess.list2cmdline(command)
    launcher.write_text("@echo off\r\nchcp 65001 > nul\r\nset PYTHONUTF8=1\r\nset PYTHONIOENCODING=utf-8\r\n"
                        f"set PYTHONDONTWRITEBYTECODE=1\r\n{line} >> \"{layout.log}\" 2>&1\r\n", encoding="utf-8")
    if args.foreground:
        subprocess.run(["cmd", "/c", str(launcher)], check=False)
        return
    script = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
              f"@{{CommandLine='cmd.exe /c \"{launcher}\"'; CurrentDirectory='{layout.root}'}}; "
              "Write-Output $r.ProcessId; Write-Output $r.ReturnValue")
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    print(result.stdout.strip(), result.stderr.strip())
    for _ in range(60):
        if layout.pid.exists():
            print(f"起動しました（PID {layout.pid.read_text(encoding='utf-8')}）。進み具合: {layout.progress}")
            return
        time.sleep(1)
    raise SystemExit(f"起動を確かめられませんでした。{layout.log} を見てください。")


def stop(args) -> None:
    layout = Layout(args.workspace)
    layout.stop.write_text(now(), encoding="utf-8")
    import psutil
    pid = int(layout.pid.read_text(encoding="utf-8")) if layout.pid.exists() else None
    for _ in range(120):
        if pid is None or not psutil.pid_exists(pid):
            print("止まりました。")
            return
        time.sleep(1)
    raise SystemExit("2 分で止まりませんでした。run.log を見てください。")


def status(args) -> None:
    layout = Layout(args.workspace)
    print(layout.progress.read_text(encoding="utf-8") if layout.progress.exists() else "まだ進み具合がありません。")


def compare(args) -> None:
    """PoC の経路（2026-11-04、0.3.0 の前のコード）で保存したページの本文と、製品の経路の結果を比べる。"""
    layout = Layout(args.workspace)
    policy = json.loads(layout.policy.read_text(encoding="utf-8"))
    poc = sqlite3.connect(f"file:{(Path(args.poc_work) / 'ocr.sqlite').as_posix()}?mode=ro", uri=True)
    rows = poc.execute("SELECT doc_id, page, status, text_sha256 FROM targets WHERE status IN ('completed','empty')"
                       " ORDER BY doc_id, page").fetchall()
    result = {"compared_at": now(), "poc_pages": len(rows), "matched": 0, "mismatched": 0, "not_yet": 0,
              "not_ocr_in_product": 0, "mismatches": []}
    for doc_id, page, poc_status, digest in rows:
        path = Path(policy["data_dir"]) / "extracted" / doc_id / policy["extraction_key"] / f"page-{page:06d}.json"
        if not path.exists():
            result["not_yet"] += 1
            continue
        entry = json.loads(path.read_text(encoding="utf-8"))
        if not entry["ocr"]:
            result["not_ocr_in_product"] += 1
            continue
        if hashlib.sha256(entry["text"].encode("utf-8")).hexdigest() == digest:
            result["matched"] += 1
        else:
            result["mismatched"] += 1
            if len(result["mismatches"]) < 20:
                result["mismatches"].append({"doc_id": doc_id, "page": page, "poc_status": poc_status,
                                             "product_chars": len(entry["text"])})
    write_json(layout.comparison, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    poc_data = _default_poc_data()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["start", "run", "stop", "status", "compare"]:
        command = sub.add_parser(name)
        command.add_argument("--workspace", type=Path, default=poc_data / "full-ocr-v050-20261109")
        if name in {"start", "run"}:
            command.add_argument("--workers", type=int, default=3)
            command.add_argument("--threads", type=int, default=2)
            command.add_argument("--limit", type=int, default=0)
            command.add_argument("--retry-failed", action="store_true")
        if name in {"start", "compare"}:
            command.add_argument("--poc-work", default=str(poc_data / "full-ocr-20261104"))
        if name == "start":
            command.add_argument("--base", default=str(poc_data / "full-20261104"))
            command.add_argument("--foreground", action="store_true")
        if name == "run":
            command.add_argument("--scripts", required=True)
            command.add_argument("--source-root", required=True)
            command.add_argument("--uv-dir")
    args = parser.parse_args()
    {"start": start, "run": run, "stop": stop, "status": status, "compare": compare}[args.command](args)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    main()
