"""150 DPIで成分の位置が決まらない小点を、固定450 DPIと隔離描画で確かめる。"""

import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

audit = previous.module("selected_v27_source_pilot", HERE.parent / "v27-reference-audit/run.py")
colored = previous.module("uniform_background_round", HERE.parent / "v28-colored-point-source-pilot/run.py")
glyphs = previous.module("exact_glyph_origin", HERE.parent / "v21-trail-source-pilot/run.py")
from point_ink import components


def physical(gray, rect, box, location):
    """二票の全座標から6画素以内にあり、二閾値で一致する一つの候補を返す。"""
    left, top, right, bottom = rect
    x, y, w, h = box
    sx, sy = (right - left) / w, (bottom - top) / h
    if not 2.9 < sx < 3.2 or not 2.9 < sy < 3.2:
        raise ValueError("固定した450 DPIと枠の対応が不明")
    lower, upper = min(location), max(location)
    l = max(0, math.floor(left + (lower - 15) * sx))
    r = min(gray.shape[1], math.ceil(left + (upper + 15) * sx))
    t = max(0, math.floor(top - 4 * sy))
    b = min(gray.shape[0], math.ceil(bottom + 4 * sy))
    marks = []
    for level in (140, 186):
        candidates = []
        for a, c, d, e, mass in components(gray[t:b, l:r] < level):
            width, height = d - a, e - c
            rr = (l + a, t + c, l + d, t + e)
            center = ((rr[0] + rr[2]) / 2 - left) / sx
            if (5 <= width <= 28 and 5 <= height <= 28 and abs(width - height) <= 5
                    and mass >= .45 * width * height and max(abs(center - n) for n in location) <= 6
                    and top <= (rr[1] + rr[3]) / 2 < bottom
                    and min(rr[2], right) - max(rr[0], left) >= width / 2):
                candidates.append(rr)
        marks.append(candidates)
    selected = [candidate for candidate in marks[1] if
                sum(max(abs(i - j) for i, j in zip(candidate, inner, strict=True)) <= 2 for inner in marks[0]) == 1]
    if len(selected) != 1:
        raise ValueError("450 DPIの二閾値で両票の位置に同じ点が一つ見えない")
    l, t, r, b = selected[0]
    box150 = (math.floor(x + (l - left) / sx), math.floor(y + (t - top) / sy),
              math.ceil(x + (r - left) / sx), math.ceil(y + (b - top) / sy))
    return selected[0], box150


def glyph(pdf, number, rgb, span, flags, commands):
    trace = colored.trace
    saved = trace.reproduce
    trace.reproduce = colored.reproduce
    try:
        match = trace.trace(pdf, number, rgb, span, flags)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        match, = glyphs.spell(pdf, number, rgb, [span], flags, commands)
    finally:
        trace.reproduce = saved
    if match["codepoint"] not in ("2022", "30FB"):
        raise ValueError("許可を得た丸印の符号であることを確かめられない")
    return match


def confirm(case, img450, expected_sha, png, pdf, expected_pdf, number, commands):
    row, asset = case["row"], case["assets"]
    flags = asset["sha"]
    bounds = asset["source_view"]["views"][1]["target_rectangle"]
    marker = list(previous.ref.MARK.finditer(case["answer"]["text"]))
    coordinates = case["coordinates"]
    if (row["allocation_axis"] != "x" or not marker or len(marker) != len(coordinates)
            or any(m[1] != "round" for m in marker)):
        return None
    if (previous.sha(img450) != expected_sha or previous.sha(png) != flags["150_dpi"]
            or flags["pdf_sha256"] != expected_pdf or colored.trace.sha(pdf) != expected_pdf):
        raise ValueError("固定画像、実描画または元資料の来歴が違う")
    with Image.open(img450) as image:
        gray = np.array(image.convert("L"))
    with Image.open(png) as image:
        rgb = np.array(image.convert("RGB"))
    evidence = []
    last_x = None
    try:
        for place in coordinates:
            high, low = physical(gray, bounds, row["box"], place)
            if last_x is not None and last_x > low[0]:
                return None
            selected = glyph(pdf, number, rgb, low, flags, commands)
            evidence.append({"image_450_box": high, "image_150_box": low, "two_readings": place, "statement": selected})
            last_x = low[2]
    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
        return None
    digits = iter([e["statement"]["codepoint"] for e in evidence])
    text = previous.ref.MARK.sub(lambda _: chr(int(next(digits), 16)), case["answer"]["text"])
    return {"status": "readable", "text": previous.ref.NORMALIZE(text)}, evidence


def main():
    result = HERE / "result.json"
    if result.exists():
        raise FileExistsError("固定画像の開発出典照合は実行済み")
    audit.verify_methods()
    folder = audit.OUT / "delivery"
    manifest = folder / "packages.json"
    ship = audit.transport.check(folder, audit.sha(manifest))
    original = audit.OUT / "source-commands.json"
    baseline = audit.load(audit.HERE / "result.json")
    if baseline["source_sha256"] != audit.sha(original):
        raise ValueError("確定した元の出典と異なる")
    source = audit.load(original)["evidence"]
    cases, _ = audit.image_cases(ship, audit.old_sessions())
    saved = {(item["row"]["key"], item["row"]["line_index"]): item for item in cases}
    catalog = previous.packets.old.lookup()[1]
    take = (("defense-p0136", 79), ("disaster-p0015", 10), ("wp-summary-p0010", 14))
    result_rows = []
    for key, i in take:
        if (key, i) not in saved:
            continue
        item = saved[key, i]
        binding = item["assets"]
        v = binding["source_view"]["views"][1]
        raw = next(x["image"] for x in v["images"] if x["kind"] == "plain")
        high = folder / "source-assets" / raw
        png = audit.CORPUS / "probe-v4/png" / (key + ".png")
        filename, sha, number = catalog[key]
        pdf = (audit.CORPUS / filename).read_bytes()
        read = confirm(item, high, ship.document["source_assets"][raw], png, pdf, sha, number,
                       source.get(key, {}).get("commands", ()))
        row = {"page": key, "line_index": i, "confirmed": bool(read)}
        if read:
            row["evidence"] = read[1]
            row["comparison"] = {a: previous.ref.NORMALIZE(s["text"]) == read[0]["text"]
                                 for a, s in item["row"]["targets"].items() if s["known"]}
            wrong = {**item, "coordinates": [item["coordinates"][0]] * len(item["coordinates"])}
            # 同じ点の位置を再利用すると、先に使った箱との重なりで停止する。
            if len(item["coordinates"]) > 1 and confirm(wrong, high, ship.document["source_assets"][raw],
                                                       png, pdf, sha, number, source[key]["commands"]) is not None:
                raise ValueError("一つの丸印を別の印にも使ってしまった")
        result_rows.append(row)
        print(key, i, row["confirmed"], row.get("comparison"), flush=True)
    if any((k, i) not in {(r["page"], r["line_index"]) for r in result_rows} for k, i in take[:2]):
        raise ValueError("既定の開発行が不足")
    used = (Path(__file__), original, manifest, audit.HERE / "result.json", Path(colored.__file__), Path(glyphs.__file__))
    audit.save_once(result, audit.encoded({"scope": "development-only", "cases": result_rows,
                                           "inputs": {str(f): audit.sha(f) for f in used}}))


if __name__ == "__main__":
    main()
