"""E2: 全量で、候補数を 200 件より増やした融合と、スコアを正規化する融合を測る。

残してある usearch の索引（view で開く）と全量の Tantivy を使う。候補数は片側 200、400、800 件。
dense の expansion_search は max(2048, 候補数)。距離と BM25 のスコアも保存し、次の融合を比べる。
- RRF（k=60、語彙の重み 1）と、E1 で選んだ設定
- スコアの正規化: 1 問ごとに cosine 類似度と BM25 を min-max で 0〜1 にし、α × dense + (1 − α) × 語彙
採る条件は E1 と同じ。候補数を増やしたときの p95 の増分も記録する。
"""
from __future__ import annotations

import numpy as np

from decision_common import load, save
from common import limit_threads, metric, p95
from full_common import USEARCH_KEPT, ScoredTantivy, load_full, timed

CANDIDATES = [200, 400, 800]
ALPHAS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def rrf_weighted(dense, lexical, k, weight, n):
    scores = {}
    for rank, key in enumerate(dense[:n], 1):
        scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
    for rank, key in enumerate(lexical[:n], 1):
        scores[key] = scores.get(key, 0.0) + weight / (k + rank)
    return sorted(scores, key=lambda key: (-scores[key], key))


def normalized(dense, dense_sim, lexical, lexical_score, alpha):
    def scale(values):
        if not values:
            return []
        low, high = min(values), max(values)
        return [(v - low) / (high - low) if high > low else 1.0 for v in values]
    scores = {}
    for key, value in zip(dense, scale(dense_sim)):
        scores[key] = scores.get(key, 0.0) + alpha * value
    for key, value in zip(lexical, scale(lexical_score)):
        scores[key] = scores.get(key, 0.0) + (1 - alpha) * value
    return sorted(scores, key=lambda key: (-scores[key], key))


def main():
    limit_threads()
    from usearch.index import Index
    _, _, _, _, labels, queries, qvecs, query_terms = load_full()
    index = Index.restore(str(USEARCH_KEPT), view=True)
    lexical = ScoredTantivy()
    e1 = load("fusion-sweep.json")["chosen"]
    runs = {}
    for n in CANDIDATES:
        index.expansion_search = max(2048, n)
        # 1 巡して温めてから測る（1 回目の測定は最初の候補数だけ冷えた状態で測っていた）。
        for vector, terms in zip(qvecs, query_terms):
            index.search(np.asarray(vector, dtype=np.float32), n, threads=1)
            lexical.search(terms, n)
        rows = []
        for q, vector, terms in zip(queries, qvecs, query_terms):
            matches, dense_ms = timed(lambda v: index.search(np.asarray(v, dtype=np.float32), n, threads=1), vector)
            (lex_ids, lex_scores), lexical_ms = timed(lexical.search, terms, n)
            rows.append({"id": q["id"], "dense": [int(k) for k in matches.keys], "dense_sim": [1 - float(d) for d in matches.distances],
                         "lexical": [int(i) for i in lex_ids], "lexical_score": lex_scores, "dense_ms": dense_ms, "lexical_ms": lexical_ms})
        runs[n] = rows
        print(n, "dense p95", round(p95([r["dense_ms"] for r in rows]), 1), "lexical p95", round(p95([r["lexical_ms"] for r in rows]), 1), flush=True)
    positives = [(i, q) for i, q in enumerate(queries) if q["expected"]]

    def score(rank_fn, n):
        values = [metric([labels[k] for k in rank_fn(runs[n][i])], q["expected"]) for i, q in positives]
        return {"recall_at_30": float(np.mean([v[0] for v in values])), "ndcg_at_10": float(np.mean([v[1] for v in values])),
                "per_question_recall": [v[0] for v in values]}

    results = []
    for n in CANDIDATES:
        timing = {"dense_p95_ms": p95([r["dense_ms"] for r in runs[n]]), "lexical_p95_ms": p95([r["lexical_ms"] for r in runs[n]]),
                  "db_p95_ms": p95([r["dense_ms"] + r["lexical_ms"] for r in runs[n]])}
        variants = {"dense_only": lambda r: r["dense"], "rrf_k60_w1": lambda r: rrf_weighted(r["dense"], r["lexical"], 60, 1.0, n),
                    "rrf_e1": lambda r: rrf_weighted(r["dense"], r["lexical"], e1["k"], e1["lexical_weight"], n)}
        for alpha in ALPHAS:
            variants[f"minmax_a{alpha}"] = (lambda a: lambda r: normalized(r["dense"], r["dense_sim"], r["lexical"], r["lexical_score"], a))(alpha)
        for name, fn in variants.items():
            results.append({"candidates": n, "fusion": name, **timing, **score(fn, n)})
    base = next(r for r in results if r["candidates"] == 200 and r["fusion"] == "rrf_k60_w1")
    one = 1 / len(positives)
    for r in results:
        r["delta_recall_vs_base"] = r["recall_at_30"] - base["recall_at_30"]
        r["delta_ndcg_vs_base"] = r["ndcg_at_10"] - base["ndcg_at_10"]
        r["wins"] = sum(a > b + 1e-9 for a, b in zip(r["per_question_recall"], base["per_question_recall"]))
        r["losses"] = sum(a < b - 1e-9 for a, b in zip(r["per_question_recall"], base["per_question_recall"]))
        r["meets_adoption"] = (r["delta_recall_vs_base"] >= 2 * one - 1e-9 or r["delta_ndcg_vs_base"] >= 0.02)
    best = max(results, key=lambda r: (r["recall_at_30"], r["ndcg_at_10"], -r["candidates"]))
    save("fusion-deep.json", {
        "purpose": "全量で候補数 200 件超えと、スコアを正規化する融合を測る（usearch を view で開く）",
        "e1_chosen": e1, "base": {k: base[k] for k in ("candidates", "fusion", "recall_at_30", "ndcg_at_10", "db_p95_ms")},
        "best": {k: best[k] for k in ("candidates", "fusion", "recall_at_30", "ndcg_at_10", "db_p95_ms", "wins", "losses")},
        "results": results, "one_question": one,
        "note": "全量の 60 問だけで選んでいるので、ここでの最良は参考値。採るかどうかは E1 の natural と合わせて判断する"})


if __name__ == "__main__":
    main()
