"""同じ官報ページの固定画素で二字目の形を照らす。"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation


def glyphs(root, batches, hashes, key, expected_sha):
    info = batches[key]["mapping"]
    (bind,) = info.values()
    high = bind["image_reference"]["source_view"]["views"][1]
    name = next(x["image"] for x in high["images"] if x["kind"] == "plain")
    path = root / "source-assets" / name
    if expected_sha(path) != hashes[name]:
        raise ValueError("字体を確認する450 DPIが固定画像と異なる")
    l, t, r, b = map(round, high["target_rectangle"])
    with Image.open(path) as src:
        gray = np.array(src.crop((l, t, r, b)).convert("L"))
    extracted, boxes = {}, {}
    for level in (105, 140, 186, 225):
        ink = gray < level
        active = np.flatnonzero(ink.any(axis=1))
        bands = [v for v in np.split(active, np.flatnonzero(np.diff(active) > 1) + 1) if v.size]
        second = bands[1]
        top, bottom = int(second[0]), int(second[-1]) + 1
        part = ink[top:bottom, :]
        xs = np.flatnonzero(part.any(axis=0))
        left, right = int(xs[0]), int(xs[-1]) + 1
        extracted[level] = part[:, left:right]
        boxes[level] = [l + left, t + top, l + right, t + bottom]
    return extracted, boxes, Path(path)


def agreement(a, b):
    h, w = max(a.shape[0], b.shape[0]) + 4, max(a.shape[1], b.shape[1]) + 4
    fixed = np.zeros((h, w), dtype=bool)
    fixed[2:2 + a.shape[0], 2:2 + a.shape[1]] = a
    best = 0
    shifted = None
    for y in range(5):
        for x in range(5):
            moved = np.zeros_like(fixed)
            moved[y:y + b.shape[0], x:x + b.shape[1]] = b
            similarity = (fixed & moved).sum() / (fixed | moved).sum()
            if similarity > best:
                best, shifted = similarity, moved
    if shifted is None:
        raise ValueError("比較する二字目に同じ場所の筆画がない")
    covered = binary_dilation(fixed, structure=np.ones((3, 3), dtype=bool))
    reverse = binary_dilation(shifted, structure=np.ones((3, 3), dtype=bool))
    return {"iou": round(float(best), 4),
            "within_one_pixel": [round(float((a & b).sum() / a.sum()), 4)
                                  for a, b in ((shifted, covered), (fixed, reverse))]}
