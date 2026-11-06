"""E1: 融合の k、語彙の重み、候補数を、保存済みの順位で掃引する（索引の作り直しは要らない）。

- full: 統一の測定の rankings/full/*.json（72 問 × dense と語彙の上位 200 件）。正解ありの 60 問で測る。
- natural: 8,275 行の評価セット（PDF 60 問、wiki 47 問）。dense は既存の R-130 ベクトルで厳密に、
  語彙は統一の測定と同じ Tantivy（IDF を BM25 にそろえる）で順位を作り直す。
値は natural で選び、full で確かめる（同じ問いで選んで同じ問いで測ると、良く見えすぎるため）。
採る条件: full で再現率@30 が 2 問ぶん（+0.033）以上か nDCG@10 が +0.02 以上上がり、
どのセット（full、natural の PDF、natural の wiki）でも 1 問ぶんを超えて悪化しない。届かなければ k=60、候補 200 件のまま。
"""
from __future__ import annotations

import itertools
import json

import numpy as np

from decision_common import DWORK, save
from common import WORK, full_mapping, full_queries, limit_threads, load_natural, metric, read_json, rrf, write_json

KS = [10, 20, 30, 60, 100, 200]
WEIGHTS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
CANDIDATES = [30, 50, 100, 200]
COMBOS = {"usearch": "R-130__usearch_HNSW_f16___Tantivy", "sqlite-vec f32": "R-130__sqlite-vec_f32___Tantivy",
          "FAISS IVF_SQ8": "R-130__FAISS_IVF_SQ8___Tantivy"}
BASE = {"k": 60, "lexical_weight": 1.0, "candidates": 200}


def weighted_rrf(dense, lexical, k, weight, n):
    scores = {}
    for rank, key in enumerate(dense[:n], 1):
        scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
    if weight:
        for rank, key in enumerate(lexical[:n], 1):
            scores[key] = scores.get(key, 0.0) + weight / (k + rank)
    return sorted(scores, key=lambda key: (-scores[key], key))


def evaluate(cases, k, weight, n):
    """cases: {"labels": id → ページ, "items": [(expected, dense_ids, lexical_ids)]}。1 問ごとの (recall, ndcg) を返す。

    融合はチャンクの id で行い、そのあとでページに読み替える（製品の Engine.search と統一の測定の rrf と同じ）。
    """
    labels = cases["labels"]
    return [metric([labels[i] for i in weighted_rrf(d, lx, k, weight, n)], expected) for expected, d, lx in cases["items"]]


def only(cases, side):
    labels = cases["labels"]
    return [metric([labels[i] for i in (d if side == "dense" else lx)], e) for e, d, lx in cases["items"]]


def full_cases(name):
    saved = json.loads((WORK / f"rankings/full/{name}.json").read_text(encoding="utf-8"))
    labels = {int(row[0]): f"{row[2]}:p{row[3]}" for row in full_mapping()}
    queries = {q["id"]: q for q in full_queries()}
    items = []
    for qid, d, lx in zip(saved["queries"], saved["dense"], saved["lexical"]):
        q = queries[qid]
        if q["expected"]:
            items.append((q["expected"], [int(i) for i in d["ids"]], [int(i) for i in lx["ids"]]))
    return {"labels": labels, "items": items}, saved["knob"]


def natural_cases():
    cache = DWORK / "natural-rankings.json"
    if cache.exists():
        return read_json(cache)
    rows, queries = load_natural()
    labels = [r["label"] for r in rows]
    vectors = np.load(WORK / "vectors/natural/R-130.npy")
    qvectors = np.load(WORK / "vectors/natural/R-130.queries.npy")
    terms = read_json(WORK / "natural-terms.json")  # {"rows": 行ごとの語, "queries": 問いごとの語}（Sudachi 済み）
    from lexical_bench import Tantivy
    folder = DWORK / "natural-tantivy"
    import shutil
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    index = Tantivy(folder)
    index.build(list(range(len(rows))), terms["rows"])
    index.open()
    out = {"labels": labels, "pdf": [], "wiki": []}
    for q, qv, q_terms in zip(queries, qvectors, terms["queries"]):
        if not q["expected"]:
            continue
        dense = [int(i) for i in np.argsort(-(vectors @ qv))[:200]]
        lexical = [int(i) for i in index.search(q_terms, 200)]
        group = "wiki" if str(q["id"]).startswith("j") else "pdf"
        out[group].append([q["expected"], dense, lexical])
    write_json(cache, out)
    return out


def summary(values):
    return {"recall_at_30": float(np.mean([v[0] for v in values])), "ndcg_at_10": float(np.mean([v[1] for v in values]))}


def main():
    limit_threads()
    natural = natural_cases()
    sets = {"natural-pdf": {"labels": natural["labels"], "items": natural["pdf"]},
            "natural-wiki": {"labels": natural["labels"], "items": natural["wiki"]}}
    for label, name in COMBOS.items():
        sets[f"full-{label}"] = full_cases(name)[0]
    # 既存値の再現（k=60、重み 1、候補 200）と、dense だけ・語彙だけ。
    reproduction = {}
    for set_name, cases in sets.items():
        reproduction[set_name] = {"fused": summary(evaluate(cases, 60, 1.0, 200)), "dense_only": summary(only(cases, "dense")),
                                  "lexical_only": summary(only(cases, "lexical")), "questions": len(cases["items"])}
    sweep = []
    for k, weight, n in itertools.product(KS, WEIGHTS, CANDIDATES):
        row = {"k": k, "lexical_weight": weight, "candidates": n}
        for set_name, cases in sets.items():
            row[set_name] = summary(evaluate(cases, k, weight, n))
        sweep.append(row)
    # natural（PDF と wiki を合わせた平均）で最良の設定を選ぶ。同点なら基準に近い設定を優先する。
    def natural_score(row):
        return (row["natural-pdf"]["recall_at_30"] * len(sets["natural-pdf"]["items"]) + row["natural-wiki"]["recall_at_30"] * len(sets["natural-wiki"]["items"]),
                row["natural-pdf"]["ndcg_at_10"] + row["natural-wiki"]["ndcg_at_10"],
                -abs(row["k"] - 60), -abs(row["lexical_weight"] - 1), row["candidates"])
    best = max(sweep, key=natural_score)
    base = next(r for r in sweep if r["k"] == 60 and r["lexical_weight"] == 1.0 and r["candidates"] == 200)
    verdict = {}
    for set_name, cases in sets.items():
        one = 1 / len(cases["items"])
        delta_recall = best[set_name]["recall_at_30"] - base[set_name]["recall_at_30"]
        delta_ndcg = best[set_name]["ndcg_at_10"] - base[set_name]["ndcg_at_10"]
        before = evaluate(cases, 60, 1.0, 200)
        after = evaluate(cases, best["k"], best["lexical_weight"], best["candidates"])
        verdict[set_name] = {"delta_recall": delta_recall, "delta_ndcg": delta_ndcg, "one_question": one,
                             "worse_than_one_question": delta_recall < -one - 1e-9,
                             "wins": sum(a[0] > b[0] + 1e-9 for a, b in zip(after, before)),
                             "losses": sum(a[0] < b[0] - 1e-9 for a, b in zip(after, before))}
    full = verdict["full-usearch"]
    adopt = (full["delta_recall"] >= 2 * full["one_question"] - 1e-9 or full["delta_ndcg"] >= 0.02) and \
        not any(v["worse_than_one_question"] for v in verdict.values())
    dense_wins_everywhere = all(r["dense_only"]["recall_at_30"] > r["fused"]["recall_at_30"] + 1e-9 for r in reproduction.values())
    save("fusion-sweep.json", {
        "purpose": "融合の k、語彙の重み、候補数の掃引（保存済みの順位）",
        "grid": {"k": KS, "lexical_weight": WEIGHTS, "candidates": CANDIDATES}, "base": BASE,
        "reproduction": reproduction, "best_on_natural": {k: best[k] for k in ("k", "lexical_weight", "candidates")},
        "best_row": best, "base_row": base, "verdict": verdict, "adopt": adopt,
        "chosen": {k: best[k] for k in ("k", "lexical_weight", "candidates")} if adopt else BASE,
        "dense_beats_fusion_everywhere": dense_wins_everywhere, "sweep": sweep,
        "criterion": "full（usearch）で再現率 +2 問以上か nDCG@10 +0.02 以上、どのセットでも 1 問を超えて悪化しない"})


if __name__ == "__main__":
    main()
