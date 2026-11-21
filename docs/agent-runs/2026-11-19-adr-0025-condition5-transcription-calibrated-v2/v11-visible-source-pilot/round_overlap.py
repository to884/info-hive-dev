"""取得済みの丸印について同じ字の塗りと輪郭を切り分ける。"""

from collections import defaultdict
import copy
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v10-reference-audit"))
import resolve
from point_ink import col_runs, components

OUT = resolve.CORPUS / "reference-v11-visible-source-pilot"
POSITIVE = "defense-p0107", 22


def marks(gray, box):
    """連結成分と水平・垂直投影で丸の位置を比較する。"""
    x, y, w, h = box
    l, t, r, b = max(0, x - 12), max(0, y - 12), min(gray.shape[1], x + w + 12), min(gray.shape[0], y + h + 12)
    crop = gray[t:b, l:r]
    if np.median(crop) < 200:
        return []
    bright = crop < 192
    dim = crop < 128
    compact = components(dim)
    target = []
    for a, c, f, d, mass in components(bright):
        width, height = f - a, d - c
        if not (3 <= width <= 10 and 3 <= height <= 10 and abs(width - height) <= 2
                and .52 * width * height <= mass <= .98 * width * height):
            continue
        if not (y <= t + (c + d) / 2 < y + h and min(f + l, x + w) - max(a + l, x) >= width / 2):
            continue
        groups = [v for v in compact if v[0] >= a and v[1] >= c and v[2] <= f and v[3] <= d
                  and max(v[0] - a, v[1] - c, f - v[2], d - v[3]) <= 1]
        if len(groups) != 1:
            continue
        lower = dim[c:d, a:f]
        if len(col_runs(lower.any(axis=0))) != 1 or len(col_runs(lower.any(axis=1))) != 1:
            continue
        target.append((a + l, c + t, f + l, d + t))
    return target


def glyph_key(op, anchor):
    return (op["font"], op["embedded_sha256"], tuple(op["collection"]), tuple(op["matrix"]),
            op["font_size"], tuple(anchor))


def matching_mark(dots, proof, flags, box):
    origin = np.asarray(flags["150_origin"])
    matrix = np.asarray(flags["150_matrix"])
    to_pdf = np.linalg.inv(matrix)
    a, b, c, d = dots
    center = np.array([(a + c) / 2, (b + d) / 2])
    possibilities = defaultdict(list)
    for op in proof:
        mode = op["text_rendering_mode"]
        if mode in (3, 7):
            continue
        frame = op["matrix"]
        if abs(frame[1]) > 1e-5 or abs(frame[2]) > 1e-5 or frame[0] <= 0 or frame[3] <= 0:
            continue
        initial = matrix @ (np.asarray(frame[-2:]) - origin)
        fx, fy = np.abs(matrix @ np.asarray([frame[0], frame[3]]))
        em = op["font_size"] * fy
        if not (5 <= em <= 100 and -.64 * em <= center[1] - initial[1] <= .08 * em
                and box[1] - .5 <= initial[1] < box[1] + box[3] + .5):
            continue
        for anchor in op["positioned_points"]:
            cid, code, offset, width = anchor
            if not -2 <= center[0] - initial[0] - fx * offset <= fx * width + 2:
                continue
            # 位置が重なる命令は、表示の状態を証明できない限り候補として残す。
            corners = [origin + to_pdf @ np.array([u, v]) for u, v in ((a, b), (a, d), (c, b), (c, d))]
            clip_preserves = op["clip_known"] and all(
                l <= p[0] <= r and t <= p[1] <= q for l, t, r, q in op["clips"] for p in corners)
            admissible = clip_preserves and op["opacity_proven"] and mode in (0, 1)
            possibilities[glyph_key(op, anchor)].append((mode, code, admissible, op))
    if len(possibilities) != 1:
        return None
    group = next(iter(possibilities.values()))
    if not all(g[2] for g in group) or not any(g[3]["visible_fill_proven"] for g in group):
        return None
    registered = group[0][3]["collection"] == ["Adobe", "Japan1"]
    cid, code, *_ = next(iter(possibilities))[-1]
    if code not in {"2022", "30FB"} or (registered and cid == 638 and code != "30FB"):
        return None
    return {"codepoint": code, "cid": cid, "modes": sorted(x[0] for x in group),
            "commands": [x[-1] for x in group]}


def main():
    prior = resolve.load(OUT / "source-proof.json")
    request = resolve.load(resolve.REQUESTS)
    cases, _ = resolve.image_agreement()
    wanted = {POSITIVE, ("wp-summary-p0002", 13), ("wp-summary-p0010", 34)}
    result = []
    for obj in cases.values():
        r = obj["row"]
        key, index = r["key"], r["line_index"]
        if (key, index) not in wanted:
            continue
        flags = obj["assets"]["sha"]
        page = prior["evidence"][key]
        if key not in request["pages"] or flags["pdf_sha256"] != page["pdf_sha256"]:
            raise ValueError("元の資料と照合依頼が一致しない")
        png = resolve.CORPUS / "probe-v4/png" / (key + ".png")
        if resolve.sha(png) != flags["150_dpi"]:
            raise ValueError("固定150 DPIの画像と異なる")
        coords, = obj["coordinates"]
        with Image.open(png) as image:
            pixels = np.asarray(image.convert("L"))
        near = [b for b in marks(pixels, r["box"]) if all(abs((b[0] + b[2]) / 2 - r["box"][0] - u) <= 10 for u in coords)]
        confirmed = [(b, hit) for b in near if (hit := matching_mark(b, page["commands"], flags, r["box"]))]
        if (key, index) == POSITIVE:
            dot, hit = confirmed[0]
            if len(confirmed) != 1 or hit["modes"] != [0, 1]:
                raise ValueError("塗りと輪郭の再現ができない")
            changed = copy.deepcopy(hit["commands"][0])
            changed["positioned_points"][0][1] = "2022"
            if matching_mark(dot, page["commands"] + [changed], flags, r["box"]) is not None:
                raise ValueError("別の符号の重なりを保留しない")
            changed = copy.deepcopy(page["commands"])
            for op in changed:
                op["clip_known"] = False
            if matching_mark(dot, changed, flags, r["box"]) is not None:
                raise ValueError("不明な切り抜きを保留しない")
        result.append({"page": key, "line_index": index, "boxes": near,
                       "resolved": [{"box": b, **{k: v for k, v in hit.items() if k != "commands"}} for b, hit in confirmed]})
    if len(result) != len(wanted):
        raise ValueError("丸印の診断3行がそろわない")
    resolve.save_once(OUT / "round-overlap.json", resolve.encoded({"scope": "development-only",
                      "script_sha256": resolve.sha(Path(__file__)), "source_proof_sha256": resolve.sha(OUT / "source-proof.json"),
                      "paint_layer_sha256": resolve.sha(OUT / "paint-layers.json"), "cases": result}))
    print(result, flush=True)


if __name__ == "__main__":
    main()
