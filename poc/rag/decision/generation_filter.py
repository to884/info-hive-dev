"""E4: 世代の絞り込み（generation IN ...）を、usearch と FAISS と Tantivy でどう実現し、いくらかかるかを測る。

統一の測定の usearch と FAISS の行は、全世代が有効なので絞り込みを付けずに測っており、費用を含まない。
製品では、作り直し中の文書や古い世代を検索から外す必要がある。

(a) 後段での絞り込み: 文書単位で 1%、5%、20% を無効とし、usearch は候補を多めに取って無効な行を落とす。
    FAISS は IVF の IDSelector で検索の中で外す。有効な行だけの厳密な上位 30 件に対する recall と p95 を測る。
(b) 削除: 10% の文書の行を usearch の remove と FAISS の remove_ids で消し、時間と、消した後の recall を測る。
(c) Tantivy: 文書の欄を持つ索引を作り、10% の文書を delete_documents で消して commit と reload の時間を測る。
"""
from __future__ import annotations

import argparse
import gc
import math
import random
import shutil
import time

import numpy as np

from decision_common import DWORK, save
from common import Timer, limit_threads, p95
from db_bench import CANDIDATES_PER_SIDE
from full_common import USEARCH_KEPT, load_full, exact_top

FRACTIONS = [0.01, 0.05, 0.20]
MULTIPLIERS = [1.0, 1.25, 1.5, 2.0, 3.0]
REMOVE_FRACTION = 0.10


def recall_vs(found, truth):
    return float(np.mean([len(set(f[:30]) & t) / 30 for f, t in zip(found, truth)]))


def timed_runs(search, qvecs):
    # 1 巡して写像したページと分岐を温めてから測る（最初の構成だけ冷えた状態で測らないため）。
    for v in qvecs:
        search(v)
    found, times = [], []
    for v in qvecs:
        started = time.perf_counter()
        found.append(search(v))
        times.append((time.perf_counter() - started) * 1000)
    return found, times


def main():
    parser = argparse.ArgumentParser()
    # E3 で選んだ動作点。usearch は M16/ea256 の ef=1024、FAISS は nlist=4096 の nprobe=384。
    parser.add_argument("--usearch", default=str(DWORK / "db-knobs/usearch-M16-ea256.usearch"))
    parser.add_argument("--usearch-ef", type=int, default=1024)
    parser.add_argument("--faiss-lists", type=int, default=4096)
    parser.add_argument("--faiss-nprobe", type=int, default=384)
    args = parser.parse_args()
    limit_threads()
    from usearch.index import Index
    import faiss
    faiss.omp_set_num_threads(1)
    ids, vectors, terms, _, labels, queries, qvecs, query_terms = load_full()
    docs = np.array([labels[int(i)].rsplit(":p", 1)[0] for i in ids])
    unique_docs = sorted(set(docs.tolist()))
    rng = random.Random(20261106)
    shuffled = unique_docs[:]
    rng.shuffle(shuffled)
    report = {"documents": len(unique_docs), "rows": len(ids)}

    # (a) 絞り込み
    usearch_view = Index.restore(args.usearch, view=True)
    usearch_view.expansion_search = args.usearch_ef
    # FAISS は IndexIDMap2 で包まず、IVF に直接 id を付けて作る。IndexIDMap2 で包んだ IVF に remove_ids を使うと、
    # IDMap2 が内側の索引の詰め直しを前提に id の対応を作り直し、IVF は詰め直さないので対応が壊れる（1 回目の測定で再現率 0.019）。
    direct = DWORK / f"db-knobs/faiss-ivfsq8-{args.faiss_lists}-direct.faiss"
    if not direct.exists():
        faiss.omp_set_num_threads(4)
        quantizer = faiss.IndexFlatIP(512)
        built = faiss.IndexIVFScalarQuantizer(quantizer, 512, args.faiss_lists, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT)
        sample = vectors[np.random.default_rng(0).choice(len(vectors), min(len(vectors), 256 * args.faiss_lists), replace=False)]
        built.train(np.ascontiguousarray(sample))
        built.add_with_ids(np.ascontiguousarray(vectors), ids.astype(np.int64))
        faiss.write_index(built, str(direct))
        del built
        faiss.omp_set_num_threads(1)
    faiss_index = faiss.read_index(str(direct))
    inner = faiss_index
    inner.nprobe = args.faiss_nprobe
    all_truth = exact_top(qvecs, vectors, ids)
    base_found, base_times = timed_runs(lambda v: [int(k) for k in usearch_view.search(np.asarray(v, dtype=np.float32), CANDIDATES_PER_SIDE, threads=1).keys], qvecs)
    faiss_found, faiss_times = timed_runs(lambda v: [int(i) for i in faiss_index.search(np.asarray(v, dtype=np.float32)[None, :], CANDIDATES_PER_SIDE)[1][0] if i >= 0], qvecs)
    report["unfiltered"] = {"usearch": {"dense_p95_ms": p95(base_times), "recall_vs_exact": recall_vs(base_found, all_truth)},
                            "faiss": {"dense_p95_ms": p95(faiss_times), "recall_vs_exact": recall_vs(faiss_found, all_truth)}}
    filtering = []
    for fraction in FRACTIONS:
        invalid_docs = set(shuffled[:max(1, round(len(shuffled) * fraction))])
        mask = ~np.isin(docs, list(invalid_docs))
        invalid_ids = ids[~mask]
        invalid_set = set(invalid_ids.tolist())
        truth = exact_top(qvecs, vectors, ids, mask=mask)
        row = {"fraction_documents": fraction, "invalid_rows": int((~mask).sum()), "usearch_postfilter": []}
        for m in MULTIPLIERS:
            k = math.ceil(CANDIDATES_PER_SIDE * m)
            usearch_view.expansion_search = max(args.usearch_ef, k)

            def search(v, k=k):
                keys = usearch_view.search(np.asarray(v, dtype=np.float32), k, threads=1).keys
                return [int(key) for key in keys if int(key) not in invalid_set][:CANDIDATES_PER_SIDE]
            found, times = timed_runs(search, qvecs)
            row["usearch_postfilter"].append({"multiplier": m, "fetch": k, "dense_p95_ms": p95(times),
                                              "p95_increase_ms": p95(times) - report["unfiltered"]["usearch"]["dense_p95_ms"],
                                              "recall_vs_exact_valid": recall_vs(found, truth),
                                              "shortfall_queries": sum(len(f) < CANDIDATES_PER_SIDE for f in found)})
        usearch_view.expansion_search = args.usearch_ef
        selector = faiss.IDSelectorNot(faiss.IDSelectorBatch(invalid_ids.astype(np.int64)))
        params = faiss.SearchParametersIVF(sel=selector, nprobe=args.faiss_nprobe)

        def faiss_search(v):
            return [int(i) for i in faiss_index.search(np.asarray(v, dtype=np.float32)[None, :], CANDIDATES_PER_SIDE, params=params)[1][0] if i >= 0]
        found, times = timed_runs(faiss_search, qvecs)
        row["faiss_selector"] = {"dense_p95_ms": p95(times), "p95_increase_ms": p95(times) - report["unfiltered"]["faiss"]["dense_p95_ms"],
                                 "recall_vs_exact_valid": recall_vs(found, truth),
                                 "leaked_invalid": sum(1 for f in found for i in f if i in invalid_set)}
        good = [p for p in row["usearch_postfilter"]
                if p["recall_vs_exact_valid"] >= report["unfiltered"]["usearch"]["recall_vs_exact"] - 0.01 and p["shortfall_queries"] == 0]
        row["usearch_smallest_ok"] = min(good, key=lambda p: p["multiplier"]) if good else None
        filtering.append(row)
        print(fraction, row["usearch_smallest_ok"], row["faiss_selector"], flush=True)
    report["filtering"] = filtering
    del usearch_view
    gc.collect()

    # (b) 削除
    removed_docs = set(shuffled[:round(len(shuffled) * REMOVE_FRACTION)])
    mask = ~np.isin(docs, list(removed_docs))
    removed = ids[~mask].astype(np.uint64)
    truth = exact_top(qvecs, vectors, ids, mask=mask)
    with Timer() as loading:
        loaded = Index.restore(args.usearch, view=False)
    loaded.expansion_search = args.usearch_ef
    with Timer() as removing:
        loaded.remove(removed)
    found, times = timed_runs(lambda v: [int(k) for k in loaded.search(np.asarray(v, dtype=np.float32), CANDIDATES_PER_SIDE, threads=1).keys], qvecs)
    report["usearch_remove"] = {"fraction_documents": REMOVE_FRACTION, "rows": len(removed), "load_seconds": loading.seconds,
                                "remove_seconds": removing.seconds, "dense_p95_ms": p95(times), "recall_vs_exact_remaining": recall_vs(found, truth),
                                "recall_drop": report["unfiltered"]["usearch"]["recall_vs_exact"] - recall_vs(found, truth),
                                "size_after": int(loaded.size)}
    del loaded
    gc.collect()
    with Timer() as removing:
        faiss_index.remove_ids(faiss.IDSelectorBatch(removed.astype(np.int64)))
    found, times = timed_runs(lambda v: [int(i) for i in faiss_index.search(np.asarray(v, dtype=np.float32)[None, :], CANDIDATES_PER_SIDE)[1][0] if i >= 0], qvecs)
    report["faiss_remove"] = {"rows": len(removed), "remove_seconds": removing.seconds, "dense_p95_ms": p95(times),
                              "recall_vs_exact_remaining": recall_vs(found, truth),
                              "recall_drop": report["unfiltered"]["faiss"]["recall_vs_exact"] - recall_vs(found, truth)}
    print("remove", report["usearch_remove"], report["faiss_remove"], flush=True)
    del faiss_index, inner
    gc.collect()

    # (c) Tantivy の削除
    import tantivy
    folder = DWORK / "tantivy-deletable"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("id", stored=True, fast=True, indexed=True)
    builder.add_text_field("doc", stored=False, tokenizer_name="raw")
    builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
    schema = builder.build()
    index = tantivy.Index(schema, path=str(folder))
    index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
    with Timer() as build:
        writer = index.writer(heap_size=1_000_000_000, num_threads=4)
        for i, d, t in zip(ids, docs, terms):
            writer.add_document(tantivy.Document(id=int(i), doc=str(d), terms=t))
        writer.commit()
        writer.wait_merging_threads()
    index.reload()
    with Timer() as deleting:
        writer = index.writer(heap_size=200_000_000, num_threads=1)
        for d in removed_docs:
            writer.delete_documents_by_term("doc", d)
        writer.commit()
    with Timer() as reloading:
        index.reload()
        searcher = index.searcher()
    with Timer() as merging:
        writer.wait_merging_threads()
    report["tantivy_delete"] = {"build_seconds": build.seconds, "documents": len(removed_docs), "rows": len(removed),
                                "delete_commit_seconds": deleting.seconds, "reload_seconds": reloading.seconds,
                                "merge_wait_seconds": merging.seconds, "num_docs_after": searcher.num_docs,
                                "expected_after": int(mask.sum())}
    print("tantivy", report["tantivy_delete"], flush=True)
    criteria = {
        "postfilter_5pct_increase_le_20ms": all((r["usearch_smallest_ok"] or {}).get("p95_increase_ms", 1e9) <= 20
                                                for r in filtering if r["fraction_documents"] <= 0.05),
        "remove_10pct_drop_le_0_02": report["usearch_remove"]["recall_drop"] <= 0.02,
    }
    save("generation-filter.json", {"purpose": "世代の絞り込みと削除の費用（usearch、FAISS、Tantivy）",
                                    "usearch": args.usearch, "usearch_ef": args.usearch_ef, "faiss": str(direct), "faiss_lists": args.faiss_lists,
                                    "faiss_nprobe": args.faiss_nprobe, **report, "criteria": criteria,
                                    "note": "1 回目の測定は最初の構成だけ冷えた状態で測っており、増分が負になった。温めてから測り直した"})


if __name__ == "__main__":
    main()
