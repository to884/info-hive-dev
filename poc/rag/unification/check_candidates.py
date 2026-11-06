"""M0: 各ベクター DB が Windows の Python 3.12 で投入、dense、語彙、世代の絞り込みまで通るかを 10,000 件で確かめる。"""
from __future__ import annotations

import hashlib
import platform
import sqlite3
import sys
import traceback
from importlib import metadata

import numpy as np

from backends import CANDIDATES
from common import FULL, NATURAL, OUT, WORK, Timer, limit_threads, read_json, write_json

ROWS = 10_000
DIMENSION = 512


def main():
    limit_threads()
    connection = sqlite3.connect(FULL / "terms.sqlite")
    terms = [row[0] for row in connection.execute("SELECT terms FROM terms ORDER BY id LIMIT ?", (ROWS,))]
    connection.close()
    rng = np.random.default_rng(20261105)
    vectors = rng.standard_normal((ROWS, DIMENSION)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    ids = np.arange(1, ROWS + 1, dtype=np.int64)
    generations = [hashlib.sha256(f"doc-{i // 50}".encode()).hexdigest() for i in range(ROWS)]
    allowed = sorted(set(generations[: ROWS // 2]))
    allowed_set = set(allowed)
    queries = vectors[rng.choice(ROWS, 20, replace=False)] + rng.standard_normal((20, DIMENSION)).astype(np.float32) * .05
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    exact = [set(ids[np.argsort(-(vectors @ q))[:30]].tolist()) for q in queries]
    results = []
    for label, cls, variant in CANDIDATES:
        backend = cls(WORK / "m0" / label.replace(" ", "_").replace("+", "_"), DIMENSION, variant)
        record = {"candidate": label, "variant": variant}
        try:
            with Timer() as build:
                backend.build(ids, vectors, terms, generations)
            backend.open()
            knob = backend.knobs[-1]
            with Timer() as search:
                found = [backend.dense(q, 30, knob, None) for q in queries]
            record.update(build_seconds=build.seconds, dense_mean_ms=search.seconds / len(queries) * 1000,
                          recall_at_30_at_largest_knob=float(np.mean([len(set(f) & e) / 30 for f, e in zip(found, exact)])))
            lexical = backend.lexical(terms[0], 30, None)
            record["lexical_hits"] = len(lexical)
            record["lexical_finds_own_row"] = 1 in lexical
            if backend.filter_native:
                filtered = backend.dense(queries[0], 30, knob, allowed)
                record["filter_native"] = True
                record["filter_respected"] = all(generations[i - 1] in allowed_set for i in filtered) and len(filtered) == 30
            else:
                record["filter_native"] = False
            record["size_bytes"] = backend.size()["total_bytes"]
            record["status"] = "ok"
        except Exception as error:
            record["status"] = "failed"
            record["error"] = f"{type(error).__name__}: {error}"
            record["traceback"] = traceback.format_exc()[-2000:]
        finally:
            backend.close()
        print(record.get("candidate"), record.get("status"), record.get("error", ""), flush=True)
        results.append(record)
    rows = read_json(NATURAL / "corpus.json")["rows"]
    packages = {name: metadata.version(name) for name in
                ["sqlite-vec", "lancedb", "qdrant-client", "usearch", "faiss-cpu", "chromadb", "fastembed", "sentence-transformers", "torch", "sudachipy", "numpy"]}
    write_json(OUT / "candidates.json", {
        "rows": ROWS, "dimension": DIMENSION, "vectors": "乱数の単位ベクトル（DB の動作確認用。精度の評価ではない）",
        "python": sys.version.split()[0], "platform": platform.platform(), "sqlite": sqlite3.sqlite_version, "packages": packages,
        "qdrant_server": "1.20.0（公式の Windows バイナリ）",
        "natural_set_has_terms": all("terms" in row for row in rows),
        "natural_terms_note": "natural-20261104 の corpus.json に terms はない。M2 で Engine.tokenize と同じ Sudachi の分かち書きを作る。",
        "excluded": [
            {"candidate": "Milvus Lite", "reason": "Windows に対応しない"},
            {"candidate": "Milvus standalone、Weaviate", "reason": "Windows では Docker か WSL が要る"},
            {"candidate": "DuckDB VSS、hnswlib", "reason": "索引全体を RAM に載せる（japanese-pdf-local-rag-options.md:110）"},
            {"candidate": "Typesense、Meilisearch", "reason": "既存調査の除外理由（同 :108-109）"},
            {"candidate": "PostgreSQL + pgvector", "reason": "別のデータベースサーバーの導入と管理が要り、プラグインの配布に合わない（同 :416）"},
        ],
        "results": results})


if __name__ == "__main__":
    main()
