"""E3: 全量で usearch と FAISS IVF_SQ8 の構築時のつまみを変え、動作点を測り直す。

統一の測定では、usearch は connectivity=16、expansion_add=128 だけを作り、動作点が掃引の上限（ef=2048）に張り付いた。
FAISS は nlist=√N（873）だけを作り、nprobe=128（上限）で目標に届いた。上限の外にもっと良い点があるかを確かめる。

- 動作点の規則は db_bench.py と同じ（厳密解に対する dense の recall@30 が 0.95 以上で、DB の p95 が最も小さい設定）。
- 語彙は全量の Tantivy を 1 度だけ測り、全ての構成で使い回す（語彙はつまみに関係しない）。
- 最初に、残してある既存の索引（M16/ea128）を開き直し、p95 が既存値（dense 41.1 ms @ ef=2048）の ±10% に入るかで環境の差を確かめる。
- 最良の構成は DWORK/db-knobs/ に残す（E4、E5、E6 で使う）。ほかは消す。
"""
from __future__ import annotations

import argparse
import gc
import math
import shutil

import numpy as np

from decision_common import DWORK, load, read_json, save
from common import Timer, directory_bytes, limit_threads, metric, p95, rrf
from db_bench import TARGET, CANDIDATES_PER_SIDE, combine
from full_common import TANTIVY_FULL, USEARCH_KEPT, load_full, exact_top

# M16/ea128 は統一の測定で残した索引を使う（作り直さない）。
USEARCH_CONFIGS = [(16, 256), (32, 128), (32, 256)]
USEARCH_EF = [256, 512, 1024, 2048, 3072, 4096]
FAISS_LISTS = [873, 2048, 4096]
FAISS_NPROBE = [32, 64, 128, 192, 256, 384, 512]
EXISTING_DENSE_P95_AT_2048 = 41.1


def lexical_runs(query_terms):
    from lexical_bench import Tantivy
    import time
    index = Tantivy(TANTIVY_FULL)
    index.open()
    for terms in query_terms[:5]:
        index.search(terms, CANDIDATES_PER_SIDE)
    runs = []
    for terms in query_terms:
        started = time.perf_counter()
        ids = index.search(terms, CANDIDATES_PER_SIDE)
        runs.append({"ids": [int(i) for i in ids], "ms": (time.perf_counter() - started) * 1000})
    return runs


def dense_runs(search, qvecs):
    import time
    for vector in qvecs[:5]:
        search(vector)
    runs = []
    for vector in qvecs:
        started = time.perf_counter()
        ids = search(vector)
        runs.append({"ids": [int(i) for i in ids], "ms": (time.perf_counter() - started) * 1000})
    return runs


def sweep(name, knobs, make_search, queries, qvecs, lexical, labels, exact):
    points = []
    for knob in knobs:
        result = combine(queries, dense_runs(make_search(knob), qvecs), lexical, labels, exact, knob)
        points.append(result)
        print(f"  {name} knob={knob} dense={result['dense_p95_ms']:.1f}ms db={result['db_p95_ms']:.1f}ms "
              f"recall_vs_exact={result['dense_recall_vs_exact_at_30']:.3f} recall@30={result['recall_at_30']:.3f}", flush=True)
    reached = [p for p in points if p["dense_recall_vs_exact_at_30"] >= TARGET]
    point = min(reached, key=lambda p: p["db_p95_ms"]) if reached else max(points, key=lambda p: p["dense_recall_vs_exact_at_30"])
    strip = lambda p: {k: v for k, v in p.items() if k != "measurements"}  # noqa: E731
    return {"operating_point": strip(point), "target_reached": bool(reached), "sweep": [strip(p) for p in points]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["usearch", "faiss"], help="片方だけ測る")
    args = parser.parse_args()
    limit_threads()
    from usearch.index import Index
    import faiss
    ids, vectors, _, _, labels, queries, qvecs, query_terms = load_full()
    exact = exact_top(qvecs, vectors, ids)
    lexical = lexical_runs(query_terms)
    tantivy_bytes = directory_bytes(TANTIVY_FULL)
    out_path = DWORK / "db-knobs-full.partial.json"
    report = read_json(out_path) if out_path.exists() else {"results": {}}

    def store(key, value):
        report["results"][key] = value
        from common import write_json
        write_json(out_path, report)

    keep = DWORK / "db-knobs"
    keep.mkdir(parents=True, exist_ok=True)
    if args.only in (None, "usearch"):
        # 環境の差の確認: 残してある既存の索引。
        if "usearch M16 ea128 (既存)" not in report["results"]:
            index = Index.restore(str(USEARCH_KEPT), view=True)
            def make(knob, index=index):
                def search(vector):
                    index.expansion_search = knob
                    return index.search(np.asarray(vector, dtype=np.float32), CANDIDATES_PER_SIDE, threads=1).keys
                return search
            result = sweep("existing", USEARCH_EF, make, queries, qvecs, lexical, labels, exact)
            dense = next(p["dense_p95_ms"] for p in result["sweep"] if p["knob"] == 2048)
            result.update(reproduction={"dense_p95_ms": dense, "expected": EXISTING_DENSE_P95_AT_2048,
                                        "within_10_percent": abs(dense - EXISTING_DENSE_P95_AT_2048) <= EXISTING_DENSE_P95_AT_2048 * .1},
                          size={"vector_bytes": USEARCH_KEPT.stat().st_size, "lexical_bytes": tantivy_bytes},
                          path=str(USEARCH_KEPT), params={"connectivity": 16, "expansion_add": 128}, build_seconds=635.0)
            store("usearch M16 ea128 (既存)", result)
            del index
            gc.collect()
        for connectivity, expansion_add in USEARCH_CONFIGS:
            key = f"usearch M{connectivity} ea{expansion_add}"
            if key in report["results"]:
                continue
            path = keep / f"usearch-M{connectivity}-ea{expansion_add}.usearch"
            if not path.exists():
                with Timer() as build:
                    index = Index(ndim=512, metric="cos", dtype="f16", connectivity=connectivity, expansion_add=expansion_add)
                    index.add(ids.astype(np.uint64), vectors, threads=4)
                    index.save(str(path))
                build_seconds = build.seconds
                del index
                gc.collect()
            else:
                build_seconds = None
            index = Index.restore(str(path), view=True)
            def make(knob, index=index):
                def search(vector):
                    index.expansion_search = knob
                    return index.search(np.asarray(vector, dtype=np.float32), CANDIDATES_PER_SIDE, threads=1).keys
                return search
            result = sweep(key, USEARCH_EF, make, queries, qvecs, lexical, labels, exact)
            result.update(build_seconds=build_seconds, size={"vector_bytes": path.stat().st_size, "lexical_bytes": tantivy_bytes},
                          path=str(path), params={"connectivity": connectivity, "expansion_add": expansion_add})
            store(key, result)
            del index
            gc.collect()
    if args.only in (None, "faiss"):
        faiss.omp_set_num_threads(4)
        for lists in FAISS_LISTS:
            key = f"FAISS IVF_SQ8 nlist{lists}"
            if key in report["results"]:
                continue
            path = keep / f"faiss-ivfsq8-{lists}.faiss"
            with Timer() as build:
                if not path.exists():
                    quantizer = faiss.IndexFlatIP(512)
                    inner = faiss.IndexIVFScalarQuantizer(quantizer, 512, lists, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT)
                    sample = vectors[np.random.default_rng(0).choice(len(vectors), min(len(vectors), 256 * lists), replace=False)]
                    inner.train(np.ascontiguousarray(sample))
                    wrapped = faiss.IndexIDMap2(inner)
                    wrapped.add_with_ids(np.ascontiguousarray(vectors), ids.astype(np.int64))
                    faiss.write_index(wrapped, str(path))
                    del wrapped
            faiss.omp_set_num_threads(1)
            index = faiss.read_index(str(path))
            inner = faiss.downcast_index(index.index)
            def make(knob, index=index, inner=inner):
                def search(vector):
                    inner.nprobe = knob
                    _, found = index.search(np.asarray(vector, dtype=np.float32)[None, :], CANDIDATES_PER_SIDE)
                    return [i for i in found[0] if i >= 0]
                return search
            result = sweep(key, FAISS_NPROBE, make, queries, qvecs, lexical, labels, exact)
            result.update(build_seconds=build.seconds, size={"vector_bytes": path.stat().st_size, "lexical_bytes": tantivy_bytes},
                          path=str(path), params={"nlist": lists})
            store(key, result)
            faiss.omp_set_num_threads(4)
            del index, inner
            gc.collect()
    save("db-knobs-full.json", {
        "purpose": "全量で usearch と FAISS IVF_SQ8 の構築時のつまみを変え、動作点を測り直す",
        "target_dense_recall_vs_exact_at_30": TARGET, "candidates_per_side": CANDIDATES_PER_SIDE,
        "lexical": "全量の Tantivy（IDF を BM25 にそろえる）を 1 度だけ測って使い回す", **report})


if __name__ == "__main__":
    main()
