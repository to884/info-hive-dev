"""固定画像の水平走査から、連結成分を使わずに小さな点列を確認する。"""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"
DOT = HERE.parent / "dot-layout-v2"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def intervals(values):
    edges = np.flatnonzero(np.diff(np.pad(values.astype(np.int8), 1)))
    return zip(edges[::2], edges[1::2], strict=True)


def runs_at(mask, i):
    points = []
    for left, right in intervals(mask[i, :]):
        if not 2 <= right - left <= 5:
            continue
        center = int((left + right - 1) // 2)
        vertical = [(a, b) for a, b in intervals(mask[:, center]) if a <= i < b]
        if vertical and 2 <= vertical[0][1] - vertical[0][0] <= 5:
            points.append((int(left), int(right)))
    for start, first in enumerate(points):
        row = [first]
        gaps = []
        for next_point in points[start + 1:]:
            diff = next_point[0] - row[-1][0]
            if not 3 <= diff <= 13 or max([diff, *gaps]) - min([diff, *gaps]) > 1:
                break
            row.append(next_point)
            gaps.append(diff)
        if len(row) >= 3:
            yield tuple(row)


def from_image(gray, box):
    """異なる走査線で支えられた最大点列を取り、同じ長さが競合した場合は保留する。"""
    x, y, width, height = box
    H, W = gray.shape
    if not (0 <= x < x + width <= W and 0 <= y < y + height <= H):
        raise ValueError("枠が固定画像の範囲外")
    top, bottom = max(0, y - 6), min(H, y + height + 6)
    # 連結成分版と別に、上下の余白を含む画素の局所背景を推定する。
    band = gray[top:bottom, x:x + width]
    background = int(np.median(band))
    mask = band.astype(np.int16) < background - 64
    observed = defaultdict(list)
    for i in range(y - top, y - top + height):
        for run in runs_at(mask, i):
            observed[run].append(i + top - y)
    if not observed:
        return {"state": "none"}
    ranked = sorted(observed, key=lambda v: (-len(v), -len(observed[v]), v))
    first = ranked[0]
    # 同じ物理点のアンチエイリアス差は1画素まで寄せて比較する。
    close = lambda a, b: len(a) == len(b) and all(abs(i[0] - j[0]) <= 1 for i, j in zip(a, b, strict=True))
    if any(len(r) == len(first) and len(observed[r]) >= len(observed[first]) and not close(first, r) for r in ranked[1:]):
        return {"state": "competing"}
    return {"state": "measured", "points": len(first), "ranges": [list(p) for p in first],
            "scan_lines": observed[first]}


def main():
    output = HERE / "point-projection.json"
    if output.exists():
        raise FileExistsError("元の測定を上書きしない")
    scan = DOT / "result.json"
    source_files = [scan, Path(__file__), DOT / "source-render-objects.json", DOT / "source-middle-dot-runs.json"]
    detected = {(r["key"], r["line_index"]): r for r in read(scan)["geometries"]
                if r["previous"] == "unknown" and r["runs"]}
    keys = sorted({key for key, _ in detected})
    measured, counts = [], Counter()
    for key in keys:
        path = CORPUS / "probe-v4/png" / (key + ".png")
        region_path = CORPUS / "public/region-v9" / (key + ".json")
        region = read(region_path)
        if sha(path) != region["image_sha256"]:
            raise ValueError("固定画像のSHAと異なる")
        source_files.extend((path, region_path))
        with Image.open(path) as im:
            gray = np.asarray(im.convert("L"))
        for k, i in detected:
            if k != key:
                continue
            group = detected[k, i]
            result = from_image(gray, region["lines"][i]["box"])
            a = group["runs"]
            counts["rows"] += 1
            matched = (result["state"] == "measured" and len(a) == 1 and result["points"] == len(a[0])
                       and all(abs(position[0] - box[0]) <= 1
                               for position, box in zip(result["ranges"], a[0], strict=True)))
            counts["independent_image_count_and_positions_match"] += matched
            counts["projection-" + result["state"]] += 1
            measured.append({"key": k, "line_index": i, "matches_component_measurement": matched, **result})
    manifest = {p.resolve().as_posix(): sha(p) for p in source_files}
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-image-measurement", "inputs": manifest,
                   "counts": counts, "rows": measured}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
