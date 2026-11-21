"""固定150 DPIの閉じた輪郭を、塗りつぶした丸と区別する開発試験。"""

from collections import Counter
import re
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_fill_holes, label

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as audit

reference = audit.as_reference()


def closed_hole(gray, bounds):
    l, t, r, b = bounds
    patch = gray[max(0, t - 2):b + 2, max(0, l - 2):r + 2]
    if patch.size == 0:
        return False
    # 両方の濃淡閾値で同じ明るい穴が閉じ、外周とつながらない場合だけ採る。
    holes = []
    for cutoff in (160, 192):
        ink = patch < cutoff
        holes.append(binary_fill_holes(ink) & ~ink)
    joint = holes[0] & holes[1] & (patch >= 192)
    dy, dx = t - max(0, t - 2), l - max(0, l - 2)
    core = joint[dy:dy + b - t, dx:dx + r - l]
    groups, number = label(core)
    sizes = np.bincount(groups.ravel(), minlength=number + 1)[1:]
    return bool(sizes.size and sizes.max() >= max(3, (r - l) * (b - t) * .12))


def unverified_round(answer, row, flags, positions):
    if answer["status"] != "readable" or row["allocation_axis"] != "x":
        return False
    first = reference.MARK.match(answer["text"])
    left, top, width, height = row["box"]
    gray = reference.png_checked(row, flags)
    for l, t, r, b in reference.small_round(gray, (left, top, min(width, 24), height)):
        center = (l + r) / 2 - left
        if not (9 <= max(r - l, b - t) <= 10 and abs(center) <= 12):
            continue
        placed = first and first[1] == "round" and positions and all(abs(center - n) <= 10 for n in positions[0])
        if not placed and not closed_hole(gray, (l, t, r, b)):
            return True
    return False


def synthetic():
    gray = np.full((15, 15), 250, dtype=np.uint8)
    y, x = np.ogrid[:15, :15]
    radius = (x - 7) ** 2 + (y - 7) ** 2
    window = (3, 3, 12, 12)
    gray[radius <= 18] = 40
    assert not closed_hole(gray, window)
    gray[radius <= 5] = 245
    assert closed_hole(gray, window)
    gray[3:6, 6:9] = 245
    assert not closed_hole(gray, window)
    gray[radius <= 18] = 40
    gray[7, 7] = 250
    assert not closed_hole(gray, window)
    return 4


def main():
    reference_out = audit.OUT / "reference-evidence.json"
    earlier = audit.load(audit.ENDED)
    archive = audit.load(reference_out)
    if earlier["reference_sha256"] != audit.sha(reference_out):
        raise ValueError("照合するv19の参照証跡が変化")
    old = reference.unverified_round
    reference.unverified_round = unverified_round
    try:
        cases, _ = reference.cases()
    finally:
        reference.unverified_round = old
    counts, changed, controls = Counter(), [], []
    for case in cases:
        row = case["row"]
        key = f"{row['key']}/{row['line_index']}"
        before = archive[key]
        text = case["answer"]["text"]
        if before["evidence"] == "unverified-small-round":
            if case["reason"] == "unverified-small-round":
                counts["still-held"] += 1
                continue
            if case["answer"]["status"] != "readable" or reference.MARK.search(text):
                raise ValueError("輪郭を確認した後も本文の二票が不明")
            by_target = {k: "same" if text == reference.NORMALIZE(v["text"]) else "different"
                         for k, v in row["targets"].items() if v["known"]}
            changed.append({"page": row["key"], "line_index": row["line_index"], "comparison": by_target})
            counts.update(by_target.values())
        elif isinstance(before["evidence"], dict) and re.match(r"⟦round:", text):
            x, y, w, h = row["box"]
            gray = reference.png_checked(row, case["assets"]["sha"])
            boxes = reference.small_round(gray, (x, y, min(w, 24), h))
            first = case["coordinates"][0]
            matching = [rect for rect in boxes if all(abs((rect[0] + rect[2]) / 2 - x - n) <= 10 for n in first)]
            for rect in matching:
                if closed_hole(gray, rect):
                    raise ValueError("実際に描いた塗り丸を閉じた輪郭と誤認")
                controls.append({"page": row["key"], "line_index": row["line_index"], "box": rect})
            if matching:
                counts["original-source-controls"] += 1
    if not controls:
        raise ValueError("固定画像の正の対照を確認できない")
    audit.save_once(HERE / "result.json", audit.encoded({
        "scope": "development-only", "results": counts, "changed": changed, "controls": controls,
        "synthetic_development_controls": synthetic(), "audit_sha256": audit.sha(audit.ENDED),
        "method_sha256": audit.sha(Path(__file__)),
    }))
    print(dict(counts), changed, flush=True)


if __name__ == "__main__":
    main()
