"""全 PDF を参照して抽出量を測る。原本は読み取り専用で開き、途中結果から再開する。"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config, write_json
from rag_pdf import inspect_page, chunks_for

WORK = POC_DATA / "full-20261104"
OUT = ROOT / "docs/research/rag-validation-remaining-2026-11-04"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-cloud", action="store_true")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    old_work = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
    source_root = Path(json.loads((old_work / "sample-manifest.json").read_text(encoding="utf-8"))["root"])
    manifest_path = WORK / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        files = []
        started = time.perf_counter()
        directories = [source_root]
        while directories:
            directory = directories.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        if not os.path.isjunction(entry.path):
                            directories.append(Path(entry.path))
                        continue
                    if not entry.name.lower().endswith(".pdf"):
                        continue
                    # Windows の列挙情報を使い、クラウド再解析ポイントを stat で開かない。
                    stat = entry.stat(follow_symlinks=False)
                    attributes = getattr(stat, "st_file_attributes", 0)
                    files.append({"relative_path": Path(entry.path).relative_to(source_root).as_posix(), "bytes": stat.st_size,
                                  "mtime_ns": stat.st_mtime_ns, "cloud_only": bool(attributes & (0x1000 | 0x40000 | 0x400000))})
                    if len(files) % 100 == 0:
                        print(json.dumps({"phase":"inventory_scan","files":len(files)}),flush=True)
        files.sort(key=lambda row: (row["cloud_only"], row["relative_path"]))
        manifest = {"root": str(source_root), "files": files, "scan_seconds": time.perf_counter()-started}
        write_json(manifest_path, manifest)
    summary = {"files": len(manifest["files"]), "bytes": sum(row["bytes"] for row in manifest["files"]),
               "cloud_files": sum(row["cloud_only"] for row in manifest["files"]),
               "largest_bytes": max(row["bytes"] for row in manifest["files"]),
               "include_cloud": args.include_cloud}
    write_json(OUT / "full-inventory.json", summary)
    print(json.dumps({"phase": "inventory", **summary}), flush=True)
    import pypdfium2 as pdfium
    config = Config({"data_dir": str(WORK / "data"), "reference_roots": {"books": str(source_root)},
                     "embedding_model": "cl-nagoya/ruri-v3-130m", "cpu_threads": 4})
    db = sqlite3.connect(WORK / "corpus.sqlite")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
          relative_path TEXT PRIMARY KEY, size INTEGER, mtime_ns INTEGER, doc_id TEXT,
          pages INTEGER, text_bytes INTEGER, chunks INTEGER, read_seconds REAL,
          extract_seconds REAL, status TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS pages (
          doc_id TEXT, page INTEGER, text TEXT, quality TEXT, PRIMARY KEY(doc_id,page));
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY, doc_id TEXT, page INTEGER, number INTEGER,
          text TEXT, embedding_text TEXT, UNIQUE(doc_id,page,number));
    """)
    started = time.perf_counter()
    for index, item in enumerate(manifest["files"]):
        saved = db.execute("SELECT size,mtime_ns,status FROM documents WHERE relative_path=?", (item["relative_path"],)).fetchone()
        if saved and saved == (item["bytes"], item["mtime_ns"], "completed"):
            continue
        if item["cloud_only"] and not args.include_cloud:
            continue
        path = source_root / item["relative_path"]
        try:
            before = path.stat()
            if (before.st_size,before.st_mtime_ns)!=(item['bytes'],item['mtime_ns']):
                raise RuntimeError("原資料が検証開始時の一覧から変わりました。対象を固定して再実行してください。")
            read_started = time.perf_counter()
            payload = path.read_bytes()
            read_seconds = time.perf_counter()-read_started
            digest = hashlib.sha256(payload).hexdigest()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError("読み込み中に原資料が変わりました。")
            extract_started = time.perf_counter()
            text_bytes, chunk_count, kinds = 0, 0, collections.Counter()
            with pdfium.PdfDocument(payload) as pdf:
                page_count = len(pdf)
                previous_section = ""
                for page_number in range(page_count):
                    with closing(pdf[page_number]) as page:
                        text, quality = inspect_page(page)
                    text_bytes += len(text.encode("utf-8"))
                    kinds[quality["kind"]] += 1
                    db.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?)",
                               (digest, page_number+1, text, json.dumps(quality, ensure_ascii=False)))
                    chunks = chunks_for([{"page":page_number+1,"text":text}], path.stem, config)
                    for number, chunk in enumerate(chunks):
                        section = chunk["section"] or previous_section
                        previous_section = section
                        db.execute("INSERT OR REPLACE INTO chunks(doc_id,page,number,text,embedding_text) VALUES (?,?,?,?,?)",
                                   (digest,page_number+1,number,chunk["text"],f"{path.stem}\n{section}\n{chunk['text']}"))
                    chunk_count += len(chunks)
                    if time.perf_counter()-extract_started > 30 and page_number % 100 == 0:
                        print(json.dumps({"phase":"extracting","document":index+1,"page":page_number+1,"pages":page_count}),flush=True)
            del payload
            extract_seconds = time.perf_counter()-extract_started
            db.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (item["relative_path"],after.st_size,after.st_mtime_ns,digest,page_count,text_bytes,chunk_count,read_seconds,extract_seconds,"completed",None))
            db.commit()
            row = {"phase":"extracted","document":index+1,"documents_total":summary["files"],
                   "pages":page_count,"chunks":chunk_count,"read_seconds":read_seconds,"extract_seconds":extract_seconds,"kinds":dict(kinds)}
            print(json.dumps(row,ensure_ascii=False),flush=True)
        except Exception as error:
            db.rollback()
            db.execute("INSERT OR REPLACE INTO documents(relative_path,size,mtime_ns,status,error) VALUES (?,?,?,?,?)",
                       (item["relative_path"],item["bytes"],item["mtime_ns"],"failed",str(error)))
            db.commit()
            print(json.dumps({"phase":"error","document":index+1,"error":str(error)},ensure_ascii=False),flush=True)
        totals = db.execute("SELECT COUNT(*),COALESCE(SUM(size),0),COALESCE(SUM(pages),0),COALESCE(SUM(text_bytes),0),COALESCE(SUM(chunks),0) FROM documents WHERE status='completed'").fetchone()
        progress = {"completed_files":totals[0],"source_bytes":totals[1],"pages":totals[2],"text_bytes":totals[3],"chunks_before_dedup":totals[4],
                    "distinct_chunks":db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],"wall_seconds":time.perf_counter()-started,
                    "failed_files":db.execute("SELECT COUNT(*) FROM documents WHERE status='failed'").fetchone()[0],
                    "extraction_includes_ocr":False,"corpus_sqlite":str(WORK / "corpus.sqlite")}
        write_json(WORK / "progress.json", progress)
        write_json(OUT / "full-extraction-progress.json", progress)
    failed=db.execute("SELECT COUNT(*) FROM documents WHERE status='failed'").fetchone()[0]
    write_json(WORK/'extraction-complete.json',{'status':'completed' if not failed else 'partial','failed_files':failed,'include_cloud':args.include_cloud,'ocr_included':False})
    db.close()


if __name__ == "__main__":
    main()
