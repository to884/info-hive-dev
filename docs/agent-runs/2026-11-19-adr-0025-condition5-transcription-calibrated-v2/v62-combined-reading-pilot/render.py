"""検証した短枠・横書き・縦軸の表示を固定画素から組み合わせる。"""

from contextlib import contextmanager
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
import official

audit, core = official.audit, official.core
draft, previous = audit.draft, audit.previous
orientation = previous.module("column_orientations", HERE.parent / "v50-reading-orientation-pilot/prepare.py")
instructions = previous.module("physical_instructions", HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py")
short = previous.module("short_crossing_columns", HERE.parent / "v53-short-column-order-pilot/prepare.py")
horizontal = previous.module("display_coordinates", HERE.parent / "v54-horizontal-mark-coordinates-pilot/prepare.py")
base_frame, base_fit, base_module = draft.frame, audit.fit, core.module
typeface = previous.packets.old.base.FONTS / "meiryo.ttc"
legacy_bullets = draft.bullet_stage.old.GUIDE
bullet_guide = legacy_bullets.replace(instructions.OLD_CIRCLE, instructions.CIRCLE)


def plan(reference_plan):
    guide = reference_plan["guides"]["x"]
    guide = guide.replace(horizontal.OLD_RULER, "").replace(audit.COORDINATE_NOTE, "")
    guide = guide.replace(instructions.OLD_CIRCLE, instructions.CIRCLE)
    return {"guides": {**reference_plan["guides"], "x": guide}, "ruler": reference_plan["ruler"]}


def short_frame(row):
    w, h = row["box"][2:]
    return row["allocation_axis"] == "x" and 16 <= w <= 120 and 12 <= h <= 35


def narrow(row):
    w, h = row["box"][2:]
    return short_frame(row) and w <= 30 and h <= 20


def cross(view, rect):
    left, top, right, bottom = rect
    if right - left < 3 * (bottom - top):
        return False
    bands = orientation.ink_bands(np.array(view.convert("L")), left, top, right, bottom)
    return len(bands) >= 2 and any(a < top < b or a < bottom < b for a, b in bands)


def display(row, original, origins, ident, font):
    images, guide, slots = base_frame(row, original, origins, ident, font)
    w, h = row["box"][2:]
    x_axis = row["allocation_axis"] == "x"
    if x_axis:
        guide += horizontal.GUIDE
        if short_frame(row):
            guide = guide.replace(previous.packets.SHORT, "") + short.GUIDE
            slots = []
        guide += horizontal.NEW_RULER if w > 120 else horizontal.OLD_RULER
    if x_axis and h > 35:
        return images, guide, slots
    low, high, transform = draft.opened(row, original, origins)
    with Image.open(high) as image:
        if not x_axis:
            for name, pixels in orientation.vertical(image, transform, ident, font).items():
                images[name] = pixels
            if h <= 120:
                images[f"{ident}-turn-preview.png"] = orientation.turned(image, transform, ident, font)
            guide += orientation.VERTICAL + instructions.VERTICAL
            return images, guide, slots
        if narrow(row):
            images[f"{ident}-short-context.png"] = short.context(image, transform, ident, font)
            images[f"{ident}-quarter-turns.png"] = orientation.turned(image, transform, ident, font)
            guide += short.VISUAL
        if w >= 90 and cross(image, transform):
            images[f"{ident}-cross-frame.png"] = orientation.cross_frame(image, transform, ident, font)
            guide += orientation.HORIZONTAL
        if w > 1200:
            images[f"{ident}-paragraph-margin.png"] = draft.bullet_stage.old.margin(low, row["box"], ident, font)
    return images, guide, slots


def coordinate_display(row, png, label, segments, font_path):
    if row["box"][2] <= 120:
        ordinary = base_module("archived_ruler", HERE.parent / "v35-coordinate-pilot/ruler.py")
        return ordinary.cards(row, png, label, segments, font_path)
    font = ImageFont.truetype(font_path, size=15)
    with Image.open(png) as im:
        return horizontal.rulers(row, im, label, segments, font)


def modules(name, path):
    leaf = base_module(name, path)
    if path.parent.name == "v35-coordinate-pilot" and path.name == "ruler.py":
        leaf.cards = coordinate_display
    return leaf


ADDITIONS = ("-short-context", "-quarter-turns", "-column-shapes-", "-cross-frame", "-turn-preview", "-paragraph-margin")


def fit(primary, extra, required):
    return base_fit(primary, extra, required | {name for name in extra if any(part in name for part in ADDITIONS)})


@contextmanager
def active():
    draft.frame, audit.fit, core.module = display, fit, modules
    draft.bullet_stage.old.GUIDE = bullet_guide
    try:
        yield
    finally:
        draft.frame, audit.fit, core.module = base_frame, base_fit, base_module
        draft.bullet_stage.old.GUIDE = legacy_bullets


def verify(rows, packets):
    seen = set()
    for entry in packets.values():
        (label, part), = entry["mapping"].items()
        names, prompt = set(entry["request"]["images"]), entry["request"]["prompt"]
        index = part["entry"]
        row = rows[index]
        w, h = row["box"][2:]
        if index in seen:
            raise ValueError("表示の比較に同じ行が複数ある")
        seen.add(index)
        if row["allocation_axis"] == "y":
            if (not any("-column-shapes-" in s for s in names) or (h <= 120 and f"{label}-turn-preview.png" not in names)):
                raise ValueError("縦列の見本や向きが正式な束にない")
        elif (short_frame(row) and part["partitions"] or narrow(row)
              and not {f"{label}-short-context.png", f"{label}-quarter-turns.png"} <= names):
            raise ValueError("短い枠に全文の形式と必要な画素の説明がない")
        elif w > 1200 and h <= 35 and (f"{label}-paragraph-margin.png" not in names or bullet_guide not in prompt):
            raise ValueError("長い横書きの行頭の拡大がない")
    if seen != set(range(len(rows))):
        raise ValueError("対象の全行に候補の表示を用意したか確認できない")
