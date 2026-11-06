"""M1 と M1': モデル × ベクター DB の組ごとに、速度・容量・精度を同じ手順で測る。

- 文書ベクトルは GPU で作ったもの（R-130 は既存の全量）、クエリベクトルは製品の CPU 実行系で作ったもの。
- 製品と同じく、dense と語彙をそれぞれ 200 件取り、有効な世代での絞り込み（generation IN ...）を付け、RRF で融合する。
- 各 DB のつまみを掃引し、厳密解に対する dense の recall@30 が TARGET に届く最も安い設定を動作点にする。
- 端から端までの精度は、融合した上位 30 件のページ再現率と nDCG@10 を 60 問の正解ラベルで直接測る。
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import shutil
import sqlite3
import time

import numpy as np
import psutil

import backends
from backends import CANDIDATES
from common import FULL, MODELS, OUT, WORK, Timer, Tokenizer, full_mapping, full_queries, limit_threads, metric, p95, read_json, rrf, subset_ids, write_json

TARGET = 0.95
CANDIDATES_PER_SIDE = 200
PRODUCT_RUNTIME = {"E-s": "fastembed-fp16", "E-l": "fastembed", "S-ja": "st-cpu", "R-30": "onnx-fp32", "R-130": "onnx-fp32", "R-310": "onnx-fp32"}


def load_data(key, dataset):
    mapping = full_mapping()
    if dataset == "subset":
        wanted = set(subset_ids())
        mapping = [row for row in mapping if row[0] in wanted]
    ids = np.array([row[0] for row in mapping], dtype=np.int64)
    if key == "R-130":
        raw = FULL / "embeddings-130m/vectors.f32"
        mapped = np.memmap(raw, mode="r", dtype=np.float32, shape=(raw.stat().st_size // 2048, 512))
        vectors = np.array(mapped[[row[1] for row in mapping]], dtype=np.float32)
    else:
        vectors = np.load(WORK / f"vectors/{dataset}/{key}.npy")
    assert len(vectors) == len(ids)
    labels = {int(row[0]): f"{row[2]}:p{row[3]}" for row in mapping}
    generations = [hashlib.sha256(row[2].encode()).hexdigest() for row in mapping]
    connection = sqlite3.connect(FULL / "terms.sqlite")
    connection.execute("CREATE TEMP TABLE wanted(id INTEGER PRIMARY KEY)")
    connection.executemany("INSERT INTO wanted VALUES(?)", ((int(i),) for i in ids))
    terms = [row[0] for row in connection.execute("SELECT t.terms FROM terms t JOIN wanted w ON w.id=t.id ORDER BY t.id")]
    connection.close()
    assert len(terms) == len(ids)
    return ids, vectors, terms, generations, labels


def query_vectors(key, runtime):
    path = WORK / f"runtime-queries/{key}__{runtime}.npy"
    if not path.exists():
        raise RuntimeError(f"{path.name} がありません。runtime_parity.py を先に実行してください。")
    return np.load(path)


def process_rss(backend):
    total = psutil.Process().memory_info().rss
    child = getattr(backend, "process", None)
    if child is not None:
        try:
            total += psutil.Process(child.pid).memory_info().rss
        except psutil.Error:
            pass
    return total


def measure_lexical(backend, query_terms, allowed):
    """語彙検索はつまみに関係しないので、1 度だけ測って全てのつまみで使い回す。"""
    for terms in query_terms[:5]:
        backend.lexical(terms, CANDIDATES_PER_SIDE, allowed)
    results = []
    for terms in query_terms:
        started = time.perf_counter()
        ids = backend.lexical(terms, CANDIDATES_PER_SIDE, allowed)
        results.append({"ids": [int(i) for i in ids], "ms": (time.perf_counter() - started) * 1000})
    return results


def combine(queries, dense_runs, lexical_runs, labels, exact, knob):
    """1 問ごとに dense + 語彙 + RRF の時間を足し、融合した順位で精度を測る。"""
    rows = []
    for q, d, lx, truth in zip(queries, dense_runs, lexical_runs, exact):
        started = time.perf_counter()
        fused = rrf(d["ids"], lx["ids"])
        fusion = (time.perf_counter() - started) * 1000
        row = {"id": q["id"], "dense_ms": d["ms"], "lexical_ms": lx["ms"], "fusion_ms": fusion, "db_ms": d["ms"] + lx["ms"] + fusion,
               "dense_recall_vs_exact_at_30": len(set(d["ids"][:30]) & truth) / 30}
        if q["expected"]:
            row["recall_at_30"], row["ndcg_at_10"] = metric([labels[i] for i in fused], q["expected"])
        rows.append(row)
    positive = [r for r in rows if "recall_at_30" in r]
    return {"knob": knob, "dense_p95_ms": p95([r["dense_ms"] for r in rows]), "lexical_p95_ms": p95([r["lexical_ms"] for r in rows]),
            "db_p95_ms": p95([r["db_ms"] for r in rows]), "db_median_ms": float(np.median([r["db_ms"] for r in rows])),
            "dense_recall_vs_exact_at_30": float(np.mean([r["dense_recall_vs_exact_at_30"] for r in rows])),
            "recall_at_30": float(np.mean([r["recall_at_30"] for r in positive])),
            "ndcg_at_10": float(np.mean([r["ndcg_at_10"] for r in positive])), "measurements": rows}


def measure_dense(backend, knob, qvecs, allowed):
    for vector in qvecs[:5]:
        backend.dense(vector, CANDIDATES_PER_SIDE, knob, allowed)
    results = []
    for vector in qvecs:
        started = time.perf_counter()
        ids = backend.dense(vector, CANDIDATES_PER_SIDE, knob, allowed)
        results.append({"ids": [int(i) for i in ids], "ms": (time.perf_counter() - started) * 1000})
    return results


def save_rankings(dataset, key, queries, dense_runs, lexical_runs, knob):
    folder = WORK / "rankings" / dataset
    folder.mkdir(parents=True, exist_ok=True)
    name = key.replace(" × ", "__").replace(" ", "_").replace("+", "_").replace("[", "").replace("]", "")
    import json
    (folder / f"{name}.json").write_text(json.dumps({"knob": knob, "queries": [q["id"] for q in queries], "dense": dense_runs, "lexical": lexical_runs}), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--dataset", required=True, choices=["subset", "full"])
    parser.add_argument("--candidates", nargs="*", help="backends.CANDIDATES の名前で絞る")
    parser.add_argument("--keep", action="store_true", help="計測後も索引を消さない")
    parser.add_argument("--runtime", help="クエリを作った実行系。既定は PRODUCT_RUNTIME")
    parser.add_argument("--lexical", choices=["fts5", "tantivy"], default="fts5",
                        help="FTS5 を使う DB の語彙検索のエンジン。tantivy なら組の名前に「+ Tantivy」を付ける")
    args = parser.parse_args()
    backends.LEXICAL_ENGINE = args.lexical
    native_lexical = ("LanceDB", "Qdrant HNSW")
    limit_threads()
    runtime = args.runtime or PRODUCT_RUNTIME[args.model]
    out = OUT / f"db-bench-{args.dataset}.json"
    report = read_json(out) if out.exists() else {"target_dense_recall_vs_exact_at_30": TARGET, "results": {}}
    ids, vectors, terms, generations, labels = load_data(args.model, args.dataset)
    queries = full_queries()
    qvecs = query_vectors(args.model, runtime)
    tokenize = Tokenizer()
    query_terms = [tokenize(q["query"]) for q in queries]
    scores = qvecs @ vectors.T
    exact = [set(ids[np.argpartition(-row, 29)[:30]].tolist()) for row in scores]
    del scores
    allowed = sorted(set(generations))
    for name, cls, variant in CANDIDATES:
        if args.candidates and name not in args.candidates:
            continue
        if args.lexical == "tantivy" and name.startswith(native_lexical):
            continue
        suffix = " + Tantivy" if args.lexical == "tantivy" else ""
        # 製品の実行系と違うクエリで測るときは、組の名前に実行系を入れて、製品の実行系の結果と混ぜない。
        if runtime != PRODUCT_RUNTIME[args.model]:
            suffix += f" [{runtime}]"
        key = f"{args.model} × {name}{suffix}"
        saved = report["results"].get(key, {})
        if saved.get("status") == "ok" and saved.get("query_runtime") == runtime:
            print("計測済み", key, flush=True)
            continue
        folder = WORK / "db" / args.dataset / args.model / (name + suffix).replace(" ", "_").replace("+", "_").replace("[", "").replace("]", "")
        backend = cls(folder, MODELS[args.model]["dimension"], variant)
        record = {"model": args.model, "candidate": name, "query_runtime": runtime, "rows": len(ids), "dimension": MODELS[args.model]["dimension"],
                  "lexical_engine": "LanceDB native FTS" if name.startswith("LanceDB") else
                  "Qdrant BM25 sparse（IDF は Qdrant）" if name.startswith("Qdrant HNSW") else
                  "Tantivy" if args.lexical == "tantivy" else "SQLite FTS5"}
        try:
            print("構築", key, flush=True)
            with Timer() as build:
                backend.build(ids, vectors, terms, generations)
            gc.collect()
            record["build_seconds"] = build.seconds
            record["build_steps"] = getattr(backend, "build_steps", None)
            record["size"] = backend.size()
            with Timer() as opened:
                backend.open()
            record["open_seconds"] = opened.seconds
            scope = allowed if backend.filter_native else None
            lexical_runs = measure_lexical(backend, query_terms, scope)
            sweep, dense_by_knob = [], {}
            knobs = list(backend.knobs)
            for index, knob in enumerate(knobs):
                dense_by_knob[knob] = measure_dense(backend, knob, qvecs, scope)
                result = combine(queries, dense_by_knob[knob], lexical_runs, labels, exact, knob)
                sweep.append(result)
                print(f"  {backend.knob_name}={knob} dense={result['dense_p95_ms']:.1f}ms lexical={result['lexical_p95_ms']:.1f}ms "
                      f"recall_vs_exact={result['dense_recall_vs_exact_at_30']:.3f} recall@30={result['recall_at_30']:.3f}", flush=True)
                if result["dense_recall_vs_exact_at_30"] >= TARGET and index + 1 < len(knobs):
                    # 目標に届いたら、比較のために 1 段だけ上を測ってやめる。
                    following = knobs[index + 1]
                    dense_by_knob[following] = measure_dense(backend, following, qvecs, scope)
                    sweep.append(combine(queries, dense_by_knob[following], lexical_runs, labels, exact, following))
                    break
            reached = [s for s in sweep if s["dense_recall_vs_exact_at_30"] >= TARGET]
            point = min(reached, key=lambda s: s["db_p95_ms"]) if reached else max(sweep, key=lambda s: s["dense_recall_vs_exact_at_30"])
            save_rankings(args.dataset, key, queries, dense_by_knob[point["knob"]], lexical_runs, point["knob"])
            unfiltered = None
            if backend.filter_native:
                unfiltered = combine(queries, measure_dense(backend, point["knob"], qvecs, None),
                                     measure_lexical(backend, query_terms, None), labels, exact, point["knob"])
            record.update(knob_name=backend.knob_name, operating_point={k: v for k, v in point.items() if k != "measurements"},
                          operating_point_measurements=point["measurements"], target_reached=bool(reached),
                          sweep=[{k: v for k, v in s.items() if k != "measurements"} for s in sweep],
                          unfiltered=({k: v for k, v in unfiltered.items() if k != "measurements"} if unfiltered else None),
                          filter="native" if backend.filter_native else "なし（全世代が有効なので結果は同じ。絞り込みの費用は含まない）",
                          rss_bytes_after_search=process_rss(backend), status="ok")
        except Exception as error:
            import traceback
            record.update(status="failed", error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc()[-2000:])
            print("失敗", key, error, flush=True)
        finally:
            backend.close()
            gc.collect()
        report["results"][key] = record
        report.update(dataset=args.dataset, note="DB の時間は dense + 語彙 + RRF。クエリの埋め込み時間は runtime-parity.json の query_p95_ms を足して総合時間にする")
        write_json(out, report)
        if not args.keep:
            time.sleep(1)
            shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
