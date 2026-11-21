"""点線の候補がすべて行の正解まで確定した場合の配置数だけを試算する。"""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
MODEL = BENCH / "corpus/flag-revalidation-v9"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(row):
    return row["key"], row["line_index"]


def assignments(counts):
    return math.prod(n + 1 for n in counts.values())


def without_flags(counts):
    units = Counter()
    for (unit, _), n in counts.items():
        units[unit] += n
    return assignments(units)


def main():
    output = HERE / "assignment-impact.json"
    if output.exists():
        raise FileExistsError("配置の診断を上書きできない")
    plan_path, result_path = (BENCH / "results" / name for name in
                              ("v9-revalidation-plan.json", "v9-fixed-revalidation.json"))
    plan, result = load(plan_path), load(result_path)
    scoring_path, predictions_path = MODEL / "scoring-data.json", MODEL / "predictions.npz"
    if (sha(plan_path) != result["plan_sha256"] or sha(predictions_path) != result["prediction_sha256"]
            or sha(scoring_path) != plan["scoring_data_sha256"] or plan["threshold"] != .15):
        raise ValueError("固定モデルと採点資料のSHAが一致しない")
    with np.load(predictions_path, allow_pickle=False) as raw:
        predictions = raw["probabilities"]
    if predictions.shape != (15658,) or not np.isfinite(predictions).all():
        raise ValueError("固定した全行の予測がそろわない")
    flags = predictions >= plan["threshold"]
    scan, cid, middle = (HERE / name for name in
                         ("result.json", "source-object-groups.json", "source-middle-dot-runs.json"))
    visual = {identity(r) for r in load(scan)["geometries"] if r["previous"] == "unknown" and r["runs"]}
    supported = {identity(r) for r in load(cid)["rows"] if r["corroborated"]}
    supported |= {identity(r) for r in load(middle)["rows"] if r["covered"] or r["pairwise_covered"]}
    if not supported <= visual:
        raise ValueError("出典で照合した行が点線候補の外にある")
    measures = {"visual_candidates": visual, "point_codes_supported": supported}
    packed = load(scoring_path)
    identities = load(MODEL / "row-identities.json")
    if sha(MODEL / "row-identities.json") != plan["identities_sha256"]:
        raise ValueError("予測する全行の固定順と異なる")
    cursor, values, used = 0, {}, set()
    for group in packed["group_order"]:
        rows = packed["samples"][group]["lines"]
        next_row = cursor + len(rows)
        if [identity(r) for r in rows] != [identity(r) for r in identities[cursor:next_row]]:
            raise ValueError("予測と採点の行順が違う")
        original = Counter()
        after = {name: Counter() for name in measures}
        for row, flagged in zip(rows, flags[cursor:next_row], strict=True):
            if row["rule"] != "unresolved":
                continue
            ident = identity(row)
            used.add(ident)
            slot = row["unit"], bool(flagged)
            original[slot] += 1
            for name, covered in measures.items():
                if ident not in covered:
                    after[name][slot] += 1
        cursor = next_row
        n = sum(original.values())
        values[group] = {"unknown_rows": n, "current_assignments": assignments(original),
                         "hypothetical": {name: {"resolved_rows": n - sum(remaining.values()),
                                                 "fixed_flag_assignments": assignments(remaining),
                                                 "minimum_ignoring_flags": without_flags(remaining)}
                                          for name, remaining in after.items()}}
    if cursor != len(flags) or not visual <= used:
        raise ValueError("画像候補と未決定行の対応が変化")
    evidence = {"scope": "hypothetical-assignment-count-only",
                "inputs": {f.name: sha(f) for f in (plan_path, result_path, scoring_path, predictions_path,
                                                    scan, cid, middle, Path(__file__))},
                "groups": values}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
    print(json.dumps({g: v for g, v in values.items() if g.endswith("-public")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
