"""別々の連結探索と水平投影で、固定画素の点の数と幅を照合する。"""

from collections import defaultdict
import itertools
from statistics import median

import numpy as np


def components(mask):
    remaining = {(int(y), int(x)) for y, x in zip(*np.nonzero(mask), strict=True)}
    neighbors = tuple((dy, dx) for dy, dx in itertools.product(range(-1, 2), repeat=2) if dy or dx)
    boxes = []
    while remaining:
        seed = remaining.pop()
        todo, found = [seed], [seed]
        while todo:
            y, x = todo.pop()
            for dy, dx in neighbors:
                point = y + dy, x + dx
                if point in remaining:
                    remaining.remove(point)
                    todo.append(point)
                    found.append(point)
        ys, xs = zip(*found, strict=True)
        boxes.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, len(found)))
    return boxes


def col_runs(bits):
    breaks = np.flatnonzero(np.diff(np.r_[False, bits, False]))
    return tuple((int(a), int(b)) for a, b in zip(breaks[::2], breaks[1::2], strict=True))


def projection_matches(mask, marks):
    left, top = min(d[0] for d in marks), min(d[1] for d in marks)
    right, bottom = max(d[2] for d in marks), max(d[3] for d in marks)
    projection = col_runs(mask[top:bottom, left:right].any(axis=0))
    expected = tuple((a - left, b - left) for a, _, b, _ in marks)
    if projection != expected:
        return False
    return any(sum(bits[a:b].any() for a, b in projection) == len(marks) for bits in mask[top:bottom, left:right])


def groups(gray, box):
    """中間の記号を含め、所属がはっきりしない点は返さない。"""
    x, y, w, h = box
    if w < 2 or h < 2 or y < 0 or x < 0 or y + h > gray.shape[0] or x + w > gray.shape[1]:
        return {}
    left, top, right, bottom = max(0, x - 8), max(0, y - 8), min(gray.shape[1], x + w + 8), min(gray.shape[0], y + h + 8)
    image = gray[top:bottom, left:right]
    background = float(np.median(image))
    if background < 200:
        return {}
    mask = image < min(192, background - 45)
    candidates = []
    for a, b, c, d, mass in components(mask):
        width, height = c - a, d - b
        if (2 <= width <= 8 and 2 <= height <= 8 and mass >= 4 and
                y <= top + (b + d) / 2 < y + h and min(c + left, x + w) - max(a + left, x) >= width / 2):
            candidates.append((a, b, c, d))
    trails = set()
    vertical = defaultdict(set)
    for a, b, c, d in candidates:
        if c - a <= 5 and d - b <= 5:
            for mark in range(max(0, (b + d) // 2 - 1), (b + d) // 2 + 2):
                vertical[mark].add((a, b, c, d))
    for aligned in vertical.values():
        line = sorted(aligned)
        chain = []
        for dot in line:
            if chain:
                separation = (dot[0] + dot[2] - chain[-1][0] - chain[-1][2]) / 2
                if not 3 <= separation <= 17:
                    keep(trails, mask, chain)
                    chain = []
            chain.append(dot)
        keep(trails, mask, chain)

    def globalize(run):
        return tuple((a + left, b + top, c + left, d + top) for a, b, c, d in run)

    maximal = [r for r in trails if not any(set(r) < set(other) for other in trails)]
    round_marks = [(d,) for d in candidates if not any(d in run for run in maximal) and projection_matches(mask, (d,))]
    return {"trail": [globalize(run) for run in sorted(maximal)], "round": [globalize(run) for run in sorted(round_marks)]}


def keep(result, mask, run):
    if len(run) < 3:
        return
    gaps = [(b[0] + b[2] - a[0] - a[2]) / 2 for a, b in zip(run, run[1:])]
    average = median(gaps)
    if all(abs(x - average) <= 1.3 for x in gaps) and projection_matches(mask, run):
        result.add(tuple(run))
