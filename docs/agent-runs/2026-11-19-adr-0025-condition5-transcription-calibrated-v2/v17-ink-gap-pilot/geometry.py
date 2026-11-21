"""固定画像の字を切らない位置で、長い行の読取用の表示を分ける。"""

import io
from itertools import pairwise
import math

import numpy as np
from PIL import Image, ImageDraw


def gaps(ink, target):
    """最大長を超える部分を、両側にインクのある空白の中央で区切る。"""
    if not ink.any() or len(ink) < 2:
        return [0, len(ink)]
    edges = np.flatnonzero(np.diff(np.r_[True, ink, True]))
    candidates = [(int(a + b) // 2, int(b - a)) for a, b in zip(edges[::2], edges[1::2], strict=True)
                  if b - a >= 2 and 0 < a < b < len(ink) and ink[:a].any() and ink[b:].any()]
    points = [0]
    while len(ink) - points[-1] > target * 1.45:
        start = points[-1]
        local = [p for p, _ in candidates if target * .55 <= p - start <= target * 1.45
                 and (len(ink) - p >= target * .45)]
        if not local:
            return [0, len(ink)]
        # 同じ距離なら空白が長い方を先にし、画像が同じなら同じ位置を選ぶ。
        widths = dict(candidates)
        points.append(min(local, key=lambda p: (abs(p - start - target), -widths[p], p)))
    return [*points, len(ink)]


def positions(page, box, axis):
    x, y, width, height = box
    if min(width, height) < 11:
        return []
    pixels = np.asarray(page.crop((x, y, x + width, y + height)).convert("L"))
    background = int(np.median(pixels))
    minimum = 220 if axis == "x" else 205
    if background < minimum:
        return []
    # 低いしきい値で空白となる場所でも、薄い筆画がある間は切らない。
    close = pixels < min(217, background - 25)
    if axis == "y":
        close = close.T
    threshold = 150 if axis == "x" else 105
    ink = close.any(axis=0)
    bounds = gaps(ink, threshold)
    if len(bounds) <= 2 or len(bounds) > 19:
        return []
    return bounds


def clear_at_high_resolution(high, view, boundaries, axis):
    """二つ目の解像度でも、区切りに文字の画がないことを確かめる。"""
    if len(boundaries) <= 2:
        return False
    left, top, right, bottom = view
    total = boundaries[-1]
    a, b = (left, right) if axis == "x" else (top, bottom)
    difference = b - a
    for value in boundaries[1:-1]:
        point = a + value * difference / total
        low, high_line = math.floor(point) - 1, math.ceil(point) + 2
        if axis == "x":
            bounds = low, math.floor(top), high_line, math.ceil(bottom)
        else:
            bounds = math.floor(left), low, math.ceil(right), high_line
        pixels = np.asarray(high.crop(bounds).convert("L"))
        if pixels.size == 0 or np.min(pixels) < 217:
            return False
    return True


def segment_cards(high, view, boundaries, axis, ids, font):
    if len(ids) != len(boundaries) - 1:
        raise ValueError("分割点と対象の数が異なる")
    left, top, right, bottom = view
    total = boundaries[-1]
    a, b = (left, right) if axis == "x" else (top, bottom)
    guide = [a + (b - a) * point / total for point in boundaries]
    result = {}
    for label, (begin, end) in zip(ids, pairwise(guide), strict=True):
        if axis == "x":
            l, t, r, s = begin, top, end, bottom
        else:
            l, t, r, s = left, begin, right, end
        x0, y0 = max(0, math.floor(l) - 25), max(0, math.floor(t) - 25)
        x1, y1 = min(high.width, math.ceil(r) + 25), min(high.height, math.ceil(s) + 25)
        crop = high.crop((x0, y0, x1, y1)).convert("RGB")
        tile = Image.new("RGB", (max(225, crop.width + 16), crop.height + 42), "white")
        tile.paste(crop, (8, 36))
        draw = ImageDraw.Draw(tile)
        draw.text((6, 4), f"{label}  固定450 DPI  枠あり", font=font, fill="#222222")
        lx, rx, ty, by = 8 + round(l - x0), 8 + round(r - x0), 36 + round(t - y0), 36 + round(s - y0)
        draw.rectangle((lx - 2, ty - 2, rx + 1, by + 1), outline="#a01b29", width=1)
        png = io.BytesIO()
        tile.save(png, "PNG")
        result[f"{label}-ink-gap.png"] = png.getvalue()
    return result
