"""固定画像と出典の字形から、公式正解と切り離した仮の全文を計算する。"""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
DOT_LAYOUT = HERE.parent / "dot-layout-v2"
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"
PRIVATE = CORPUS / HERE.name
sys.path.insert(0, str(BENCH / "scripts"))
import region_truth as truth


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(r):
    return r["key"], r["line_index"]


def contains_center(box, dot):
    x0, y0, x1, y1 = dot
    return box[0] <= (x0 + x1) / 2 < box[2] and box[1] <= (y0 + y1) / 2 < box[3]


def provisional_row(row, pattern, symbol, position, native, mapping, inks, gray):
    flags = []
    target = truth.corners(row["box"])
    x, y, _, _ = row["box"]
    point_boxes = [(x + l, y + t, x + r, y + b) for run in pattern["runs"] for l, t, r, b in run]
    covered = {i for i, item in native.items() if item["text"] == symbol
               and any(contains_center(item["box"], p) for p in point_boxes)}
    retained = set(row["certification"]["native_glyphs"]) - covered
    if not retained or any(i not in mapping or mapping[i]["vertical"] for i in retained):
        return None, ["unverifiable-body"]
    if any(i not in retained and i not in covered and trace and truth.inside(trace, target, False) >= truth.INSIDE
           for i, trace in inks.items()):
        flags.append("other-owned-glyph")
    if any(a < target[0] or b < target[1] or c > target[2] or d > target[3] for a, b, c, d in point_boxes):
        flags.append("point-not-entirely-contained")
    if truth.stray_ink(gray, target, [truth.reach(native[i]["box"], False) for i in retained] + point_boxes) > truth.STRAY_INK:
        flags.append("uncovered-ink")
    dots = (min(p[0] for p in point_boxes), max(p[2] for p in point_boxes))
    letters = [((native[i]["box"][0] + native[i]["box"][2]) / 2, mapping[i]["text"]) for i in retained]
    if any(dots[0] <= center <= dots[1] for center, _ in letters):
        flags.append("body-interleaves-dot-run")
    if len({center for center, _ in letters}) != len(letters):
        flags.append("equal-text-positions")
    if pattern["competing"]:
        flags.append("competing-points")
    if flags:
        return None, flags
    merged = letters + [((dots[0] + dots[1]) / 2, symbol * position)]
    return "".join(text for _, text in sorted(merged)), []


def material():
    scan = DOT_LAYOUT / "result.json"
    cid = DOT_LAYOUT / "source-object-groups.json"
    middot = DOT_LAYOUT / "source-middle-dot-runs.json"
    if load(cid)["files_sha256"][scan.relative_to(HERE.parents[2]).as_posix()] != sha(scan):
        raise ValueError("点数診断と描画命令の記録が違う")
    points = {identity(r): r for r in load(scan)["geometries"]}
    admitted = {identity(r): ("…", next(iter(r["objects"].values()))["encoded_ellipsis_count"])
                for r in load(cid)["rows"] if r["corroborated"]}
    for r in load(middot)["rows"]:
        if r["covered"] or r["pairwise_covered"]:
            key = identity(r)
            admitted[key] = ("・", sum(len(run) for run in points[key]["runs"]))
    report = {"script_sha256": sha(Path(__file__)), "method_sha256": sha(HERE / "protocol.md"),
              "inputs": {p.name: sha(p) for p in (scan, cid, middot,
                         BENCH / "scripts/region_truth.py", BENCH / "scripts/score_v4.py")}}
    return points, admitted, report


def run():
    output = HERE / "result.json"
    if output.exists() or PRIVATE.exists():
        raise FileExistsError("開発用の仮記録を上書きしない")
    points, admitted, fixed = material()
    reports, private_rows, pages, totals = [], [], {}, Counter()
    grouped = defaultdict(list)
    for key, index in admitted:
        grouped[key].append(index)
    for key, indices in grouped.items():
        raw_region = CORPUS / "public/region-v9" / (key + ".json")
        raw_source = CORPUS / "region-repair-v9/geometry" / (key + ".json")
        png = CORPUS / "probe-v4/png" / (key + ".png")
        region, source = load(raw_region), load(raw_source)
        if sha(raw_source) != region["geometry_sha256"] or sha(png) != region["image_sha256"]:
            raise ValueError("固定の字形または画像のSHAが違う")
        with Image.open(png) as opened:
            gray = np.asarray(opened.convert("L"))
        native = {item["index"]: item for item in source["native_glyphs"] if item["box"] is not None}
        mapping = {r["native"]: source["source_lines"][r["line"]]["chars"][r["char"]] for r in source["matches"]}
        inks = {i: truth.char_ink(gray, g["box"]) for i, g in native.items() if g["text"].strip()}
        pages[key] = {"region_sha256": sha(raw_region), "geometry_sha256": sha(raw_source), "image_sha256": sha(png)}
        for i in indices:
            identity_key = key, i
            row = region["lines"][i]
            kind, k = admitted[identity_key]
            text, reasons = provisional_row(row, points[identity_key], kind, k, native, mapping, inks, gray)
            report = {"key": key, "line_index": i, "box": row["box"], "canonical_dot_codepoint": f"U+{ord(kind):04X}",
                      "symbol_count": k, "provisional": text is not None, "reasons": reasons}
            reports.append(report)
            if text is not None:
                private_rows.append(dict(report, text=text, ocr_text_sha256=row["ocr_text_sha256"]))
            totals[key + "/total"] += 1
            totals[key + "/provisional"] += text is not None
    if material()[-1] != fixed:
        raise ValueError("仮転記の作業中に固定資料が変化")
    PRIVATE.mkdir(parents=True)
    private_file = PRIVATE / "full-lines.json"
    with private_file.open("x", encoding="utf-8") as stream:
        json.dump(private_rows, stream, ensure_ascii=False, indent=2)
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-only-provisional-transcriptions", "fixed": fixed, "pages": pages,
                   "rows": reports, "counts": totals, "private_full_lines_sha256": sha(private_file)},
                  stream, ensure_ascii=False, indent=2)
    print(json.dumps({"counts": totals}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    run()
