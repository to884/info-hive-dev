"""画像だけで点線候補を測り、既知の点線文字と事後に照合する開発診断。"""

from collections import Counter, defaultdict
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
REGION = BENCH / "corpus/region-visual-v9"
SEGMENT_DIR = HERE.parent / "horizontal-segments"
METHOD = BENCH / "scripts/measure_visual_ink.py"
spec = importlib.util.spec_from_file_location("ink", METHOD)
ink = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ink)
SCALE, PAD, MIN_DOTS = 3, 12, 3
DOTS = re.compile(r"[.・]{3,}")


def sha(content):
    return hashlib.sha256(content).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def runs(components, target):
    tracks = defaultdict(list)
    for part in components:
        left, top, right, bottom = part["bounds"]
        width, height = right - left, bottom - top
        if (not part["touches_window_edge"] and 2 <= width <= 5 and 2 <= height <= 5
                and part["pixels"] >= 4 and part["cross_axis_center_inside"]
                and 2 * part["axis_overlap"] >= part["axis_length"]):
            tracks[top, height].append(left)
    result = []
    for (top, height), positions in sorted(tracks.items()):
        group, spacings = [], []
        for left in sorted(positions):
            gap = left - group[-1] if group else 0
            if group and (not 3 <= gap <= 13 or max([gap, *spacings]) - min([gap, *spacings]) > 1):
                if len(group) >= MIN_DOTS:
                    result.append({"top": top - target[1], "height": height, "count": len(group),
                                   "positions": [value - target[0] for value in group]})
                group, spacings = [], []
            if group:
                spacings.append(gap)
            group.append(left)
        if len(group) >= MIN_DOTS:
            result.append({"top": top - target[1], "height": height, "count": len(group),
                           "positions": [value - target[0] for value in group]})
    return sorted(result, key=lambda item: (item["positions"][0], item["top"]))


def geometry(entry, image_index):
    low = entry["asset"]["views"][0]
    if low["dpi"] != 150 or low["display_scale"] != SCALE:
        raise ValueError("固定150 DPIの画像がない")
    if any(type(v) is not int or v % SCALE for v in low["target_rectangle"]):
        raise ValueError("固定の整数枠が異なる")
    l, t, r, b = (v // SCALE for v in low["target_rectangle"])
    if (r - l, b - t) != tuple(entry["box"][2:]):
        raise ValueError("保存した整数箱の寸法と異なる")
    plain, = [p for p in low["images"] if p["kind"] == "plain"]
    path = REGION / "assets" / plain["image"]
    content = path.read_bytes()
    if sha(content) != image_index[path.resolve().as_posix()]:
        raise ValueError("元画像が変化した")
    with Image.open(io.BytesIO(content)) as im:
        if im.width % SCALE or im.height % SCALE:
            raise ValueError("元画像が3倍表示ではない")
        box = max(l - PAD, 0), max(t - PAD, 0), min(r + PAD, im.width // SCALE), min(b + PAD, im.height // SCALE)
        shown = np.asarray(im.crop(tuple(v * SCALE for v in box)).convert("L"))
    original = shown[::SCALE, ::SCALE]
    if not np.array_equal(shown, original.repeat(SCALE, axis=0).repeat(SCALE, axis=1)):
        raise ValueError("固定画素の最近傍3倍表示が変化した")
    components = ink.measure(original, box, (l, t, r, b), 0, float(np.median(original)), ())["components"]
    return runs(components, (l, t, r, b))


def identity(entry):
    return entry["key"], entry["line_index"]


def main():
    result_path = HERE / "result.json"
    if result_path.exists():
        raise FileExistsError("診断結果を上書きしない")
    files = (REGION / "start.json", REGION / "final.json", SEGMENT_DIR / "lock.json",
             HERE / "protocol.md", Path(__file__), METHOD)
    fingerprints = {p.name if p != METHOD else str(p.relative_to(BENCH)): sha(p.read_bytes()) for p in files}
    start, final, segments = [load(p) for p in files[:3]]
    if fingerprints["start.json"] != final["start_sha256"]:
        raise ValueError("画像と既存判定の版がつながらない")
    index = {identity(r): r for r in start["entries"]}
    selected = {identity(row): name for name, row in segments["targets"].items()}
    answers, counts, source_meta = [], defaultdict(Counter), {}
    for row in final["rows"]:
        if row["allocation_axis"] != "x":
            continue
        entry = index[identity(row)]
        if any(row[k] != entry[k] for k in ("box", "allocation_axis", "ocr_text_sha256")):
            raise ValueError("画像と既存の行の同一性が違う")
        found = geometry(entry, start["assets"])
        group = "unknown" if row["status"] == "unreadable" else "known"
        stats = counts[f"{row['side']}/{group}"]
        stats["rows"] += 1
        stats["image_run"] += bool(found)
        spans = [len(match.group()) for match in DOTS.finditer(row["text"])] if group == "known" else None
        if spans is not None:
            stats["reference_run"] += bool(spans)
            stats["both_run"] += bool(found and spans)
            stats["counts_match_nonempty"] += bool(spans) and [v["count"] for v in found] == spans
        if found or identity(row) in selected:
            answers.append({"key": row["key"], "line_index": row["line_index"], "side": row["side"], "previous": group,
                            "dot_runs": found, "reference_dot_counts": spans})
        if identity(row) in selected:
            source_meta[selected[identity(row)]] = found
    if any(fingerprints[p.name if p != METHOD else str(p.relative_to(BENCH))] != sha(p.read_bytes()) for p in files):
        raise ValueError("診断中に版が変わった")
    output = {"inputs": fingerprints, "counts": counts, "segmentation_rows": source_meta,
              "geometries": answers, "updates_ground_truth": False}
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"counts": counts, "segmentation_rows": {n: [r["count"] for r in rows]
                                                             for n, rows in source_meta.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
