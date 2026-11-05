"""M2: 評価セット（8,275 行、119 問）で、モデルごとの検索精度を DB の影響なしに測る。

dense は numpy の厳密解、語彙は全モデル共通の Sudachi + FTS5 の BM25、融合は RRF（k=60）。
候補数は製品と同じ 200 件。負例 12 問は再現率の集計から外す。
"""
from __future__ import annotations

import sqlite3

import numpy as np

from common import MODELS, OUT, WORK, Tokenizer, create_fts5, fts5_search, load_natural, metric, read_json, rrf, write_json

CANDIDATES = 200


def terms_cache(rows, queries):
    path = WORK / "natural-terms.json"
    if path.exists():
        return read_json(path)
    tokenize = Tokenizer()
    value = {"rows": [tokenize(r["embedding_text"]) for r in rows], "queries": [tokenize(q["query"]) for q in queries]}
    write_json(path, value)
    return value


def summarize(per_query, queries, kinds):
    summary = {}
    for group in ("pdf", "wiki", "all"):
        chosen = [r for r, q in zip(per_query, queries) if q["expected"] and (group == "all" or kinds[q["id"]] == group)]
        summary[group] = {"queries": len(chosen), "recall_at_30": float(np.mean([r[0] for r in chosen])),
                          "ndcg_at_10": float(np.mean([r[1] for r in chosen]))}
    return summary


def main():
    rows, queries = load_natural()
    terms = terms_cache(rows, queries)
    labels = [row["label"] for row in rows]
    kinds = {q["id"]: ("pdf" if q["expected"] and ":p" in q["expected"][0] else "wiki") for q in queries}
    connection = sqlite3.connect(":memory:")
    create_fts5(connection)
    connection.executemany("INSERT INTO lexical(rowid,terms) VALUES(?,?)", ((i + 1, t) for i, t in enumerate(terms["rows"])))
    lexical = [[i - 1 for i in fts5_search(connection, t, CANDIDATES)] for t in terms["queries"]]
    lexical_only = [metric([labels[i] for i in ranking], q["expected"]) if q["expected"] else None for ranking, q in zip(lexical, queries)]
    results = {"lexical_only": summarize(lexical_only, queries, kinds)}
    models = {}
    for key, spec in MODELS.items():
        folder = WORK / "vectors/natural"
        if not (folder / f"{key}.json").exists():
            continue
        meta = read_json(folder / f"{key}.json")
        vectors = np.load(folder / f"{key}.npy")
        query_vectors = np.load(folder / f"{key}.queries.npy")
        scores = query_vectors @ vectors.T
        dense = [np.argsort(-row, kind="stable")[:CANDIDATES].tolist() for row in scores]
        hybrid, dense_only = [], []
        for q, d, lx in zip(queries, dense, lexical):
            if not q["expected"]:
                hybrid.append(None)
                dense_only.append(None)
                continue
            fused = rrf(d, lx)
            hybrid.append(metric([labels[i] for i in fused], q["expected"]))
            dense_only.append(metric([labels[i] for i in d], q["expected"]))
        models[key] = {"model": spec["id"], "revision": spec["revision"], "dimension": spec["dimension"],
                       "embedding_device": meta["device"], "gpu_passage_seconds": meta["passage_seconds"],
                       "max_tokens": meta["max_tokens"], "over_model_limit": meta["over_model_limit"],
                       "over_model_limit_ratio": meta["over_model_limit_ratio"],
                       "hybrid": summarize(hybrid, queries, kinds), "dense_only": summarize(dense_only, queries, kinds),
                       "per_query_hybrid_recall": {q["id"]: (h[0] if h else None) for q, h in zip(queries, hybrid)}}
        print(key, models[key]["hybrid"]["pdf"], models[key]["hybrid"]["all"], flush=True)
    results["models"] = models
    write_json(OUT / "model-accuracy.json", {
        "dataset": "natural-20261104（8,275 行、PDF 60 問 + wiki 47 問 + 負例 12 問）",
        "method": "dense は厳密解、語彙は Sudachi SplitMode C + FTS5 BM25（全モデル共通）、RRF k=60、候補 200 件。指標は poc/rag/remaining/evaluate_mcp.py の metric と同じ",
        "note": "埋め込みは GPU の sentence-transformers（TF32 なし）。製品の実行系との差は runtime-parity.json にある。評価セットの PDF 60 問は利用者が承認した質問、wiki 47 問は暫定の質問",
        **results})


if __name__ == "__main__":
    main()
