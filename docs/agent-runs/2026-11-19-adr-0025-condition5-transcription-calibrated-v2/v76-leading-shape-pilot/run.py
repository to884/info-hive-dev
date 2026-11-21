"""先頭の小成分が丸い点でないと固定150・450 DPIで分かる例を診断する。"""

from collections import Counter
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from math import ceil, floor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

HERE = Path(__file__).resolve().parent
EFFORT = HERE.parent / "v71-audit-effort-pilot"
spec = spec_from_file_location("effort_for_leading_shape", EFFORT / "run.py")
fixed = module_from_spec(spec)
spec.loader.exec_module(fixed)
core, launch, previous = fixed.core, fixed.launch, fixed.previous
GUARD = HERE.parent / "v23-round-pixel-pilot/run.py"
guard = previous.module("archived_leading_round", GUARD)
LEVELS = (160, 192)


def corner(gray, boxes, levels=LEVELS):
    choices = []
    densities = []
    for bounds, level in zip(boxes, levels, strict=True):
        l, t, r, b = bounds
        midx, midy = (l + r) // 2, (t + b) // 2
        quarters = [(gray[a:z, p:q] < level).mean() for a, z in ((t, midy), (midy, b))
                    for p, q in ((l, midx), (midx, r))]
        densities.append([round(float(v), 4) for v in quarters])
        choices.append({i for i, v in enumerate(quarters) if v <= .28 and quarters[3-i] >= .58})
    return choices[0] & choices[1], densities


def focused(gray, frame, box, coarse):
    x, y, w, h = box
    a, c, z, b = frame
    sx, sy = (z-a)/w, (b-c)/h
    expected = np.array([a+(coarse[0]-x)*sx, c+(coarse[1]-y)*sy, a+(coarse[2]-x)*sx, c+(coarse[3]-y)*sy])
    margin = max(4.0, min(expected[2] - expected[0], expected[3] - expected[1]) * .22)
    l, t = max(0, floor(expected[0]-2*margin)), max(0, floor(expected[1]-2*margin))
    r, end = min(gray.shape[1], ceil(expected[2]+2*margin)), min(gray.shape[0], ceil(expected[3]+2*margin))
    selected = []
    for level in LEVELS:
        indexes, _ = label(gray[t:end, l:r] < level, np.ones((3, 3), dtype=bool))
        windows = [(l+col.start, t+row.start, l+col.stop, t+row.stop) for row, col in find_objects(indexes)
                   if row.start > 0 and col.start > 0 and row.stop < end-t and col.stop < r-l]
        candidates = [rr for rr in windows if max(abs(expected-np.array(rr))) <= margin]
        if len(candidates) != 1:
            return None
        selected.append(candidates[0])
    if max(abs(a-b) for a,b in zip(*selected, strict=True)) > 2:
        return None
    return selected


@lru_cache(maxsize=8)
def gray(path, digest):
    if core.sha(path) != digest:
        raise ValueError("固定画像の来歴が異なる")
    with Image.open(path) as image:
        return np.asarray(image.convert("L"))


def synthetic():
    count = 0
    y, x = np.ogrid[:45, :45]
    for diameter in (6, 7, 8, 9, 10, 11):
        for cx, cy in ((20.0,20.0), (20.25,20.75), (20.5,20.5), (20.75,20.0)):
            for rgb in ((38, 250), (90, 215)):
                distance = np.hypot(x+.5-cx, y+.5-cy)
                edge = np.clip(distance-diameter/2+.5, 0, 1)
                picture = np.rint(rgb[0]+edge*(rgb[1]-rgb[0])).astype(np.uint8)
                bounds = []
                for cutoff in LEVELS:
                    v, u = np.nonzero(picture < cutoff)
                    bounds.append((int(u.min()), int(v.min()), int(u.max())+1, int(v.max())+1))
                choices, _ = corner(picture, bounds)
                if choices:
                    raise ValueError("合成の丸を丸でないと判断した")
                count += 1
    return count


def main():
    launch.configure()
    core.verify_methods()
    results = []
    receipts = {}
    for version in (27, 47, 64):
        root = core.CORPUS / f"reference-audit-v{version}"
        shipment = root / "delivery"
        selection, manifest, evidence = root / "selection.json", shipment / "packages.json", root / "reference-evidence.json"
        rows, packets, refs = core.load(selection)["selected"], core.load(manifest), core.load(evidence)
        result_dir = next(HERE.parent.glob(f"v{version}-reference-audit"))
        prior = core.load(result_dir / "result.json")
        if (prior["reference_sha256"] != core.sha(evidence) or packets["source_sha256"] != core.sha(selection)
                or core.load(shipment / "received.json")["packages_sha256"] != core.sha(manifest)):
            raise ValueError("正式結果と固定した配布の来歴が異なる")
        receipts.update({str(p): core.sha(p) for p in (selection, manifest, evidence, result_dir / "result.json")})
        for batch in packets["packs"].values():
            for binding in batch["mapping"].values():
                row = rows[binding["entry"]]
                if row["allocation_axis"] != "x":
                    continue
                page, line = row["key"], row["line_index"]
                ref = refs[f"{page}/{line}"]
                proof = ref["evidence"]
                archived_mark = isinstance(proof, dict) and ref["answer"]["text"].startswith(("•", "・", "…"))
                assets = binding["image_reference"]
                low = gray(core.CORPUS / "probe-v4/png" / f"{page}.png", assets["sha"]["150_dpi"])
                x, y, w, h = row["box"]
                for a,t,b,d in guard.reference.small_round(low, (x,y,min(w,24),h)):
                    if abs((a+b)/2-x)>12 or (max(b-a,d-t) not in (9,10) and not archived_mark):
                        continue
                    coarse = a,t,b,d
                    low_corners, low_density = corner(low, (coarse, coarse))
                    view = assets["source_view"]["views"][1]
                    name = next(v["image"] for v in view["images"] if v["kind"] == "plain")
                    high = gray(shipment / "source-assets" / name, packets["source_assets"][name])
                    high_boxes = focused(high, view["target_rectangle"], row["box"], coarse)
                    high_corners, high_density = corner(high, high_boxes) if high_boxes else (set(), [])
                    candidate = bool(low_corners & high_corners)
                    if archived_mark and candidate:
                        raise ValueError("出典確認済みの丸い点を除外する反例があった")
                    outcome = "confirmed-source-mark" if archived_mark else proof if isinstance(proof,str) else "source-other"
                    results.append({"version": version, "page": page, "line_index": line, "source_status": outcome,
                                    "coarse": coarse, "coarse_density": low_density, "fine": high_boxes,
                                    "fine_density": high_density, "not_round": candidate})
    tested = synthetic()
    confirmed = Counter(r["source_status"] for r in results)
    if not confirmed["confirmed-source-mark"]:
        raise ValueError("実資料の丸の対照が不足")
    counts = Counter(("not-round" if r["not_round"] else "held") for r in results)
    target = [r for r in results if r["page"]=="defense-p0500" and r["line_index"]==84]
    if len(target)!=1:
        raise ValueError("調べる固定資料の行が不足")
    core.save_once(HERE / "result.json", core.encoded({"scope": "development-only", "cases": results,
                  "synthetic_controls": tested, "counts": counts, "source_status": confirmed,
                  "inputs": {**receipts, str(Path(__file__)): core.sha(Path(__file__)), str(GUARD): core.sha(GUARD)}}))
    print(dict(counts), dict(confirmed), "合成丸", tested, "対象", target, flush=True)


if __name__ == "__main__":
    main()
