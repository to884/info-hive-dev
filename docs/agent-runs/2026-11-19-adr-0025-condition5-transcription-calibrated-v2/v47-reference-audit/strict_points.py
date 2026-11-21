"""小点の候補が固定450 DPIの二つの閾値でそれぞれ一意のときだけ小点を確認する。"""

import math
from pathlib import Path

import run as previous
from point_ink import components

implementation = previous.module("isolated_150_dpi_glyph", Path(__file__).resolve().parent.parent
                                 / "v44-small-point-pixel-pilot/run.py")


def physical(gray, rect, box, location):
    left, top, right, bottom = rect
    x, y, w, h = box
    sx, sy = (right - left) / w, (bottom - top) / h
    if not 2.9 < sx < 3.2 or not 2.9 < sy < 3.2:
        raise ValueError("固定した450 DPIと枠の対応が不明")
    l = max(0, math.floor(left + (min(location) - 15) * sx))
    r = min(gray.shape[1], math.ceil(left + (max(location) + 15) * sx))
    t = max(0, math.floor(top - 4 * sy))
    b = min(gray.shape[0], math.ceil(bottom + 4 * sy))
    pairs = []
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
        if len(candidates) != 1:
            raise ValueError("片方の閾値で両票の位置に同じ点を一つに絞れない")
        pairs.append(candidates[0])
    if max(abs(i - j) for i, j in zip(*pairs, strict=True)) > 2:
        raise ValueError("二つの閾値で得た点が同じ位置にない")
    l, t, r, b = pairs[1]
    box150 = (math.floor(x + (l - left) / sx), math.floor(y + (t - top) / sy),
              math.ceil(x + (r - left) / sx), math.ceil(y + (b - top) / sy))
    return pairs[1], box150


implementation.physical = physical
confirm = implementation.confirm
