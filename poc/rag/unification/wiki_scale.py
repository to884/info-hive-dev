"""M5: wiki 規模で、MCP サーバーとして常駐させる前提の起動費用、ウォーム検索、2 プロセス同時の書き込みを測る。

wiki 規模の代わりに評価セットの 8,275 行（大きめの wiki に相当）を使う。wiki 規模では
実行系（モデル）と DB の費用を分けて測れるので、それぞれを新しいプロセスで測る。

(a) 実行系: import + モデル読み込み + 最初のクエリの埋め込み（コールド）と、その後のクエリの p95（ウォーム）
(b) DB: import + 索引を開く + 最初の検索（コールド）と、その後の dense + 語彙の p95（ウォーム）
(c) 現行の wiki: `uv run --script wiki_search.py` を検索 1 回ごとに起動したときの壁時計時間
(d) 同時アクセス: 別プロセスが 500 行を追記している間に検索し、追記の後で開き直さずに新しい行が見えるか
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from common import NATURAL, OUT, ROOT, WORK, limit_threads, load_natural, p95, read_json, write_json

HERE = Path(__file__).resolve().parent
RUNTIMES = [("E-s", "fastembed-fp16"), ("R-30", "onnx-fp32"), ("R-130", "onnx-fp32"), ("R-130", "torch-cpu"), ("R-310", "onnx-fp32")]
DATABASES = ["sqlite-vec f32", "sqlite-vec int8", "LanceDB IVF_SQ", "Qdrant HNSW f32", "usearch HNSW f16", "FAISS IVF_SQ8", "FAISS HNSW", "Chroma HNSW"]
DB_MODEL = "R-130"
REPEATS = 3


def runtime_worker(key, kind):
    started = time.perf_counter()
    limit_threads()
    from runtime_parity import Runtime
    runtime = Runtime(key, kind)
    runtime.load()
    loaded = time.perf_counter()
    _, queries = load_natural()
    texts = [q["query"] for q in queries]
    runtime.queries(texts[:1])
    first = time.perf_counter()
    timings = []
    for text in texts[1:41]:
        t = time.perf_counter()
        runtime.queries([text])
        timings.append((time.perf_counter() - t) * 1000)
    import psutil
    return {"import_and_load_seconds": loaded - started, "first_query_seconds": first - loaded, "cold_total_seconds": first - started,
            "warm_query_p95_ms": p95(timings), "rss_bytes": psutil.Process().memory_info().rss}


def natural_data():
    rows, queries = load_natural()
    terms = read_json(WORK / "natural-terms.json")
    vectors = np.load(WORK / f"vectors/natural/{DB_MODEL}.npy")
    query_vectors = np.load(WORK / f"vectors/natural/{DB_MODEL}.queries.npy")
    import hashlib
    generations = [hashlib.sha256(r["doc_id"].encode()).hexdigest() for r in rows]
    return rows, queries, terms, vectors, query_vectors, generations


def backend_for(name):
    from backends import CANDIDATES
    from common import MODELS
    for label, cls, variant in CANDIDATES:
        if label == name:
            return cls(WORK / "wiki-scale" / name.replace(" ", "_").replace("+", "_"), MODELS[DB_MODEL]["dimension"], variant)
    raise KeyError(name)


def build_worker(name):
    rows, queries, terms, vectors, _, generations = natural_data()
    backend = backend_for(name)
    ids = np.arange(1, len(rows) + 1, dtype=np.int64)
    started = time.perf_counter()
    backend.build(ids, vectors, terms["rows"], generations)
    return {"build_seconds_without_embedding": time.perf_counter() - started, "size_bytes": backend.size()["total_bytes"]}


def search_worker(name):
    started = time.perf_counter()
    limit_threads()
    _, queries, terms, _, query_vectors, generations = natural_data()
    data_loaded = time.perf_counter()
    backend = backend_for(name)
    knob = backend.knobs[len(backend.knobs) // 2]
    allowed = sorted(set(generations)) if backend.filter_native else None
    backend.open()
    backend.dense(query_vectors[0], 200, knob, allowed)
    backend.lexical(terms["queries"][0], 200, allowed)
    first = time.perf_counter()
    timings = []
    for vector, words in zip(query_vectors[1:], terms["queries"][1:]):
        t = time.perf_counter()
        backend.dense(vector, 200, knob, allowed)
        backend.lexical(words, 200, allowed)
        timings.append((time.perf_counter() - t) * 1000)
    backend.close()
    return {"cold_open_and_first_search_seconds": first - data_loaded, "warm_search_p95_ms": p95(timings), "knob": knob,
            "note_data_loading_seconds": data_loaded - started}


APPEND_ROWS = 500


def append_rows(backend, name, ids, vectors, terms, generations):
    """各 DB の通常の追記の方法で書く。backends.py の build は作り直しなので使わない。"""
    import sqlite3
    if name.startswith("sqlite-vec"):
        connection = backend._connect()
        connection.execute("PRAGMA journal_mode=WAL")
        wrap = {"f32": "?", "int8": "vec_int8(?)", "bit": "vec_bit(?)"}[backend.variant]
        with connection:
            connection.executemany(f"INSERT INTO vectors(rowid,embedding,generation) VALUES(?,{wrap},?)",
                                   [(int(i), e, g) for i, e, g in zip(ids, backend._encode(vectors), generations)])
            connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", zip(map(int, ids), terms))
        connection.close()
    elif name.startswith("LanceDB"):
        import lancedb
        import pyarrow as pa
        table = lancedb.connect(backend.folder / "lance").open_table("chunks")
        flat = pa.array(np.ascontiguousarray(vectors).reshape(-1), type=pa.float32())
        table.add(pa.table({"id": pa.array(ids, type=pa.int64()), "generation": generations, "terms": terms,
                            "vector": pa.FixedSizeListArray.from_arrays(flat, backend.dimension)}))
    elif name.startswith("Qdrant"):
        from qdrant_client import QdrantClient, models as qm
        port = int((backend.folder / "port").read_text())
        client = QdrantClient(host="127.0.0.1", port=port, timeout=60)
        client.upsert("chunks", [qm.PointStruct(id=int(i), vector={"dense": v.tolist()}, payload={"generation": g})
                                 for i, v, g in zip(ids, vectors, generations)], wait=True)
        client.close()
    elif name.startswith("usearch"):
        from usearch.index import Index
        index = Index.restore(str(backend.folder / "vectors.usearch"))
        index.add(np.asarray(ids, dtype=np.uint64), np.asarray(vectors, dtype=np.float32))
        index.save(str(backend.folder / "vectors.usearch"))
    elif name.startswith("FAISS"):
        import faiss
        index = faiss.read_index(str(backend.folder / "vectors.faiss"))
        index.add_with_ids(np.ascontiguousarray(vectors, dtype=np.float32), np.asarray(ids, dtype=np.int64))
        faiss.write_index(index, str(backend.folder / "vectors.faiss"))
    elif name.startswith("Chroma"):
        import chromadb
        client = chromadb.PersistentClient(path=str(backend.folder / "chroma"), settings=chromadb.Settings(anonymized_telemetry=False))
        client.get_collection("chunks").add(ids=[str(int(i)) for i in ids], embeddings=np.asarray(vectors, dtype=np.float32),
                                            metadatas=[{"generation": g} for g in generations])
    if not name.startswith(("sqlite-vec", "LanceDB", "Qdrant")):
        connection = sqlite3.connect(backend.folder / "lexical.sqlite", timeout=30)
        with connection:
            connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", zip(map(int, ids), terms))
        connection.close()


def writer_worker(name):
    rows, _, terms, vectors, _, generations = natural_data()
    backend = backend_for(name)
    rng = np.random.default_rng(7)
    picked = rng.choice(len(rows), APPEND_ROWS, replace=False)
    ids = np.arange(100_001, 100_001 + APPEND_ROWS, dtype=np.int64)
    started = time.perf_counter()
    append_rows(backend, name, ids, vectors[picked], [terms["rows"][i] for i in picked], [generations[i] for i in picked])
    return {"append_seconds": time.perf_counter() - started}


def concurrency(name):
    """読み手を開いたまま、別プロセスで追記する。追記の後で読み手が開き直さずに新しい行を見つけられるかを確かめる。"""
    rows, _, terms, vectors, query_vectors, generations = natural_data()
    backend = backend_for(name)
    backend.open()
    if name.startswith("Qdrant"):
        (backend.folder / "port").write_text(str(backend.http), encoding="utf-8")
    knob = backend.knobs[-1]
    process = subprocess.Popen([sys.executable, "-X", "utf8", __file__, "--worker", "writer", "--name", name],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    errors, searches = [], 0
    while process.poll() is None:
        try:
            backend.dense(query_vectors[searches % len(query_vectors)], 30, knob, None)
            searches += 1
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}"[:300])
            time.sleep(.05)
    stdout, stderr = process.communicate()
    writer = {"returncode": process.returncode, "stderr_tail": stderr[-600:] if process.returncode else ""}
    if process.returncode == 0:
        writer.update(json.loads(stdout.strip().splitlines()[-1]))
    rng = np.random.default_rng(7)
    picked = rng.choice(len(rows), APPEND_ROWS, replace=False)
    probe = vectors[picked[0]]
    try:
        found = backend.dense(probe, 2, knob, None)
        visible = 100_001 in found
    except Exception as error:
        visible, errors = False, errors + [f"再検索: {type(error).__name__}: {error}"[:300]]
    backend.close()
    reopened = backend_for(name)
    reopened.open()
    try:
        visible_after_reopen = 100_001 in reopened.dense(probe, 2, knob, None)
    except Exception as error:
        visible_after_reopen = False
        errors.append(f"開き直し: {type(error).__name__}: {error}"[:300])
    reopened.close()
    return {"writer": writer, "reader_searches_during_write": searches, "reader_errors": errors[:5], "reader_error_count": len(errors),
            "new_row_visible_without_reopen": visible, "new_row_visible_after_reopen": visible_after_reopen}


def current_wiki_cli():
    """現行の wiki: 検索 1 回ごとに uv run --script で起動する。W0_Wiki の複製に対して測る（原本は読むだけ）。"""
    source = Path.home() / "info-hive/W0_Wiki"
    copy = WORK / "wiki-cli/W0_Wiki"
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(source, copy, ignore=shutil.ignore_patterns(".wiki-cache"))
    script = ROOT / "info-hive-wiki/skills/info-hive/scripts/wiki_search.py"
    env = {**os.environ, "PYTHONUTF8": "1"}
    runs = []
    for i in range(REPEATS + 1):
        started = time.perf_counter()
        completed = subprocess.run(["uv", "run", "--script", str(script), "検索の設定", "--wiki", str(copy), "--json"],
                                   capture_output=True, text=True, encoding="utf-8", env=env)
        runs.append({"run": "初回（索引の作成を含む）" if i == 0 else "2 回目以降", "seconds": time.perf_counter() - started, "returncode": completed.returncode})
    pages = len(list(copy.rglob("*.md")))
    return {"wiki": "W0_Wiki の複製", "markdown_files": pages, "runs": runs,
            "warm_cli_median_seconds": float(np.median([r["seconds"] for r in runs[1:]]))}


def spawn(arguments):
    completed = subprocess.run([sys.executable, "-X", "utf8", __file__, *arguments], capture_output=True, text=True, encoding="utf-8")
    if completed.returncode:
        return {"status": "failed", "error": completed.stderr[-1200:]}
    return {"status": "ok", **json.loads(completed.stdout.strip().splitlines()[-1])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=["runtime", "build", "search", "writer"])
    parser.add_argument("--name")
    parser.add_argument("--part", nargs="*", default=["runtime", "db", "cli", "concurrency"])
    args = parser.parse_args()
    if args.worker == "runtime":
        key, kind = args.name.split(":")
        print(json.dumps(runtime_worker(key, kind)))
        return
    if args.worker in ("build", "search", "writer"):
        print(json.dumps({"build": build_worker, "search": search_worker, "writer": writer_worker}[args.worker](args.name)))
        return
    out = OUT / "wiki-scale.json"
    report = read_json(out) if out.exists() else {}
    report.update(scale="評価セットの 8,275 行（wiki の代わり）。クエリは 119 問", db_vectors=f"{DB_MODEL} の GPU 埋め込み（512 次元）", repeats=REPEATS)
    if "runtime" in args.part:
        report["runtimes"] = []
        for key, kind in RUNTIMES:
            trials = [spawn(["--worker", "runtime", "--name", f"{key}:{kind}"]) for _ in range(REPEATS)]
            ok = [t for t in trials if t["status"] == "ok"]
            report["runtimes"].append({"model": key, "runtime": kind, "trials": trials,
                                       "cold_total_seconds_median": float(np.median([t["cold_total_seconds"] for t in ok])) if ok else None,
                                       "warm_query_p95_ms_median": float(np.median([t["warm_query_p95_ms"] for t in ok])) if ok else None})
            print(key, kind, report["runtimes"][-1]["cold_total_seconds_median"], report["runtimes"][-1]["warm_query_p95_ms_median"], flush=True)
            write_json(out, report)
    if "db" in args.part:
        report["databases"] = []
        for name in DATABASES:
            build = spawn(["--worker", "build", "--name", name])
            trials = [spawn(["--worker", "search", "--name", name]) for _ in range(REPEATS)] if build["status"] == "ok" else []
            ok = [t for t in trials if t["status"] == "ok"]
            report["databases"].append({"candidate": name, "build": build, "trials": trials,
                                        "cold_open_seconds_median": float(np.median([t["cold_open_and_first_search_seconds"] for t in ok])) if ok else None,
                                        "warm_search_p95_ms_median": float(np.median([t["warm_search_p95_ms"] for t in ok])) if ok else None})
            print(name, report["databases"][-1]["cold_open_seconds_median"], report["databases"][-1]["warm_search_p95_ms_median"], flush=True)
            write_json(out, report)
    if "cli" in args.part:
        report["current_wiki_cli"] = current_wiki_cli()
        print(report["current_wiki_cli"], flush=True)
        write_json(out, report)
    if "concurrency" in args.part:
        report["concurrency"] = []
        for name in DATABASES:
            spawn(["--worker", "build", "--name", name])
            try:
                result = {"candidate": name, "status": "ok", **concurrency(name)}
            except Exception as error:
                result = {"candidate": name, "status": "failed", "error": f"{type(error).__name__}: {error}"[:600]}
            report["concurrency"].append(result)
            print(name, {k: v for k, v in result.items() if k in ("status", "reader_error_count", "new_row_visible_without_reopen", "new_row_visible_after_reopen", "error")}, flush=True)
            write_json(out, report)


if __name__ == "__main__":
    main()
