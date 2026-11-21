"""全公開行の固定画像に同じ物理候補検出を適用した結果をまとめる。"""

from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(r):
    return r["key"], r["line_index"]


def main():
    target = HERE / "result.json"
    if target.exists():
        raise FileExistsError("画像候補の目録を上書きしない")
    identities = CORPUS / "flag-revalidation-v9/row-identities.json"
    original = BENCH / "results/v9-revalidation-plan.json"
    feature_path = CORPUS / "visual-dot-flag-candidate/extra.npy"
    feature_plan = HERE.parent / "visual-dot-flag-candidate/lock.json"
    anchor = HERE.parent / "dot-layout-v2/source-render-objects.json"
    middle = HERE.parent / "dot-layout-v2/source-middle-dot-runs.json"
    images = CORPUS / "region-visual-v9/final.json"
    plan, features = load(original), load(feature_plan)
    if sha(identities) != plan["identities_sha256"] or sha(feature_path) != features["extra_sha256"]:
        raise ValueError("全行と画素由来の特徴が固定と異なる")
    rows = load(identities)
    matrix = np.load(feature_path, allow_pickle=False)
    if matrix.shape != (len(rows), len(features["names"])) or len(rows) != 15658:
        raise ValueError("固定した全行がそろわない")
    point_evidence = {identity(r) for r in load(anchor)["rows"] if r["same_pixel_components"]}
    point_evidence |= {identity(r) for r in load(middle)["rows"] if r["covered"] or r["pairwise_covered"]}
    earlier = {identity(r): r for r in load(images)["rows"]}
    eligible, seen, counts = {}, set(), Counter()
    present = features["names"].index("has_regular_visual_points")
    measured = features["names"].index("horizontal_points_measured")
    for row, values in zip(rows, matrix, strict=True):
        if row["stratum"] != "public":
            continue
        i = identity(row)
        if i in seen:
            raise ValueError("公開行に重複")
        seen.add(i)
        subset = row["group"]
        counts[subset + "/rows"] += 1
        counts[subset + "/measured_horizontal"] += bool(values[measured])
        if values[present]:
            counts[subset + "/possible_round_point_run"] += 1
            kind = "source-proved" if i in point_evidence else "source-not-established"
            existing = earlier[i]["status"] if i in earlier else "outside-old-image-supplement"
            counts[subset + "/" + kind] += 1
            counts[subset + "/previous-" + existing] += 1
            eligible[i] = {"key": row["key"], "line_index": row["line_index"], "group": subset,
                           "source_status": kind, "previous_status": existing}
    if len(seen) != 8822 or not point_evidence <= set(eligible):
        raise ValueError("初期の照合済み点線と、全公開行の画像候補の差がある")
    fixed = {p.name: sha(p) for p in (identities, original, feature_path, feature_plan, anchor, middle, images, Path(__file__))}
    result = {"scope": "development-public-line-inventory", "inputs": fixed, "public_rows": len(seen),
              "counts": counts, "candidates": list(eligible.values())}
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
