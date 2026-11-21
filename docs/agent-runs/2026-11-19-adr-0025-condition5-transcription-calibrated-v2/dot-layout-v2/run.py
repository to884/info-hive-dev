"""同じ横軸行を診断し、点の物理数と符号化の違いを区別する。"""

from collections import Counter, defaultdict
import importlib.util
import io
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "dot-layout/run.py"
spec = importlib.util.spec_from_file_location("dot_layout_v1", V1)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
ink, load, sha = old.ink, old.load, old.sha
POINTS = {c: 1 for c in ".．・･·•‧∙⋅"}
POINTS.update({"‥": 2, "…": 3, "⋯": 3})
POINT_SEQUENCE = re.compile(rf"[{re.escape(''.join(POINTS))}](?:\s*[{re.escape(''.join(POINTS))}])*")


def reference_point_counts(text):
    counts = [sum(POINTS.get(c, 0) for c in m.group()) for m in POINT_SEQUENCE.finditer(text)]
    return [n for n in counts if n >= old.MIN_DOTS]


def regular_groups(points):
    """各縦帯と各開始位置で最大の等間隔列を列挙する。"""
    centers = sorted({p[1] + p[3] for p in points})
    candidates = set()
    for y in centers:
        band = sorted(p for p in points if y <= p[1] + p[3] <= y + 2)
        for i, first in enumerate(band):
            group = [first]
            small, large = 13, 3
            for p in band[i + 1:]:
                gap = p[0] - group[-1][0]
                lo, hi = min(small, gap), max(large, gap)
                if not 3 <= gap <= 13 or hi - lo > 1:
                    break
                group.append(p)
                small, large = lo, hi
            if len(group) >= old.MIN_DOTS:
                candidates.add(tuple(group))
    remaining = sorted(candidates, key=lambda run: (-len(run), run))
    groups, used, competing = [], set(), 0
    for run in remaining:
        row = set(run)
        if not row & used:
            groups.append(run)
            used.update(run)
        elif not row <= used and any(len(other) == len(run) and row & set(other) for other in groups):
            competing += 1
    return sorted(groups), competing


def read_points(entry, image_index):
    view = entry["asset"]["views"][0]
    if view["dpi"] != 150 or view["display_scale"] != 3:
        raise ValueError("150 DPI固定画像からの表示ではない")
    x, y, w, h = entry["box"]
    cx, cy, _, _ = view["crop_rectangle"]
    target = x - cx, y - cy, x - cx + w, y - cy + h
    if [v * 3 for v in target] != view["target_rectangle"]:
        raise ValueError("画像上の箱の位置または寸法と固定整数箱が違う")
    source, = [v["image"] for v in view["images"] if v["kind"] == "plain"]
    path = old.REGION / "assets" / source
    content = path.read_bytes()
    if sha(content) != image_index[path.resolve().as_posix()]:
        raise ValueError("画像のSHAが変化した")
    with Image.open(io.BytesIO(content)) as image:
        w0, h0 = image.size
        if w0 % 3 or h0 % 3:
            raise ValueError("画像が整数3倍表示ではない")
        size = w0 // 3, h0 // 3
        l, t, r, b = ink.checked_rectangle(target, size)
        window = max(l - 12, 0), max(t - 12, 0), min(r + 12, size[0]), min(b + 12, size[1])
        surrounding = ink.expanded_window(window, size)
        layout = np.asarray(image.crop(tuple(v * 3 for v in surrounding)).convert("L"))
    reduced = layout[::3, ::3]
    if not np.array_equal(layout, reduced.repeat(3, axis=0).repeat(3, axis=1)):
        raise ValueError("固定画像の最近傍表示と異なる")
    left, top, right, bottom = window
    dx, dy = surrounding[:2]
    patch = reduced[top - dy:bottom - dy, left - dx:right - dx]
    measured = ink.measure(patch, window, target, 0, float(np.median(reduced)), ())
    points = []
    for part in measured["components"]:
        a, c, e, g = part["bounds"]
        if (not part["touches_window_edge"] and part["cross_axis_center_inside"]
                and 2 * part["axis_overlap"] >= part["axis_length"]
                and 2 <= e - a <= 5 and 2 <= g - c <= 5 and part["pixels"] >= 4):
            points.append((a - l, c - t, e - l, g - t))
    groups, competing = regular_groups(points)
    return {"runs": groups, "competing": competing, "small_components": sorted(points)}


def validate():
    first = [(x, 10 + i % 2, x + 3, 13 + i % 2) for i, x in enumerate((0, 4, 10, 16, 22))]
    runs, competing = regular_groups(first)
    if competing or [p[0] for p in runs[0]] != [4, 10, 16, 22]:
        raise ValueError("紛らわしい先頭点と上下1画素差の反例を復元できない")
    if reference_point_counts("… ⋯ 項目・・．") != [6, 3] or reference_point_counts("‥") != []:
        raise ValueError("点字形の内訳を物理数に変換できない")


def main():
    result_file = HERE / "result.json"
    if result_file.exists():
        raise FileExistsError("診断結果を上書きしない")
    validate()
    source_file, final_file = old.REGION / "start.json", old.REGION / "final.json"
    segment_file = old.SEGMENT_DIR / "lock.json"
    inputs = (source_file, final_file, segment_file, old.METHOD, V1, Path(__file__), HERE / "protocol.md")
    manifest = {p.parent.name + "/" + p.name: sha(p.read_bytes()) for p in inputs}
    start = load(source_file)
    if sha(source_file.read_bytes()) != load(final_file)["start_sha256"]:
        raise ValueError("固定の画像一覧と転記台帳がつながらない")
    # 文字列やラベルを照合する前に、全横軸画像の成分を確定する。
    visual = {old.identity(r): read_points(r, start["assets"]) for r in start["entries"] if r["allocation_axis"] == "x"}
    selected = {old.identity(r): i for i, r in load(segment_file)["targets"].items()}
    if not set(selected) <= visual.keys():
        raise ValueError("区画比較の対象が全て横軸画像にない")
    outcome = {}
    counts = defaultdict(Counter)
    for row in load(final_file)["rows"]:
        key = old.identity(row)
        if key not in visual:
            continue
        if row["status"] not in ("readable", "empty", "unreadable"):
            raise ValueError("想定外の既存状態")
        found = visual[key]
        group = "unknown" if row["status"] == "unreadable" else "known"
        points = [len(r) for r in found["runs"]]
        expected = reference_point_counts(row["text"]) if group == "known" else None
        bucket = counts[row["side"] + "/" + group]
        bucket["rows"] += 1
        bucket["image_run"] += bool(points)
        bucket["ambiguous_geometry"] += bool(found["competing"])
        if expected is not None:
            bucket["reference_run"] += bool(expected)
            bucket["both_run"] += bool(points and expected)
            bucket["counts_match_nonempty"] += bool(expected) and points == expected
        if points or expected or key in selected:
            outcome[key] = {"key": row["key"], "line_index": row["line_index"], "side": row["side"],
                            "previous": group, "reference_point_counts": expected, **found}
    if manifest != {p.parent.name + "/" + p.name: sha(p.read_bytes()) for p in inputs}:
        raise ValueError("診断中に資料かコードが変化")
    summary = {i: [len(r) for r in outcome[key]["runs"]] for key, i in selected.items()}
    result = {"scope": "development-only", "inputs": manifest, "counts": counts,
              "segmentation_rows": summary, "geometries": list(outcome.values())}
    with result_file.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"counts": counts, "segmentation_rows": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
