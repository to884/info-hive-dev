"""枠端をまたぐ安定した成分の幅・高さを、字形とは別に表示する。"""

import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v43-frame-rectangle-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("frame_component_measurement", BASE)
rectangle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rectangle)
earlier, pilot = rectangle.earlier, rectangle.pilot
earlier.HERE = pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v45-edge-measurement-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
from point_ink import components

earlier.GUIDE += (
    "450 DPI画像の番号は、二つの濃さで枠端をまたぐ同じインク成分です。"
    "数値は元の枠に入る割当軸の長さと、その成分全体の長さを示します。"
    "番号の枠が字全体に当たることを右の字形から確かめた場合に、その字の所属に数値を使います。"
    "複数の成分で一字を描いているときは字全体を見ます。印の番号や数値そのものは本文には含めません。"
)


def near_edge(pixels, local_rect, axis, side):
    x0, y0, x1, y1 = local_rect
    limit = (x0, x1) if axis == "x" else (y0, y1)
    other = (y0, y1) if axis == "x" else (x0, x1)
    edge = limit[0 if side == "start" else 1]
    values = []
    for cutoff in (136, 188):
        items = []
        for x, y, r, b, mass in components(pixels < cutoff):
            a, z = (x, r) if axis == "x" else (y, b)
            c, d = (y, b) if axis == "x" else (x, r)
            sw, sh = r - x, b - y
            if not (a < edge < z and 5 <= sw <= 92 and 5 <= sh <= 95
                    and other[0] <= (c + d) / 2 < other[1] and .20 <= mass / (sw * sh) <= .67):
                continue
            items.append((x, y, r, b))
        values.append(items)
    result = []
    for c in sorted(values[1]):
        candidates = [v for v in values[0] if max(abs(a - b) for a, b in zip(c, v, strict=True)) <= 2]
        if len(candidates) != 1:
            continue
        start, end = (c[0], c[2]) if axis == "x" else (c[1], c[3])
        inside = min(limit[1], end) - max(limit[0], start)
        result.append((c, inside, end - start))
    return result[:4]


def panel(im, rect, axis, side, dpi, font):
    normal = rectangle.panel(im, rect, axis, side, dpi, font)
    if dpi != 450:
        return normal
    l, t, r, b = earlier.crop_bounds(im, rect, axis, side, dpi)
    native = np.array(im.crop((l, t, r, b)).convert("L"))
    shift = (rect[0] - l, rect[1] - t, rect[2] - l, rect[3] - t)
    found = near_edge(native, shift, axis, side)
    if not found:
        return normal
    tile = Image.new("RGB", (normal.width, normal.height + len(found) * 23 + 28), "white")
    tile.paste(normal, (0, 0))
    draw = ImageDraw.Draw(tile)
    draw.text((8, normal.height + 3), "枠端をまたぐ成分　枠内の長さ / 全体の長さ（450 DPIの画素）",
              font=font, fill="#222222")
    for number, (box, inside, width) in enumerate(found, 1):
        px, py, pr, pb = (box[0] * 3 + 5, box[1] * 3 + 29,
                          box[2] * 3 + 5 - 1, box[3] * 3 + 29 - 1)
        color = ("#223d86", "#5a2386", "#063a54", "#6f3260")[number - 1]
        draw.rectangle((px, py, pr, pb), outline=color, width=2)
        draw.text((max(5, px - 11), max(23, py - 19)), str(number), fill=color, font=font)
        draw.text((8, normal.height + 8 + number * 23), f"{number}　{inside:.1f} / {width}",
                  font=font, fill=color)
    return tile


def snapshot():
    info = earlier.snapshot()
    methods = (Path(__file__), BASE, BASE.parent / "lock.json")
    info["files"].update({str(p): pilot.audit.sha(p) for p in methods})
    return info


if __name__ == "__main__":
    earlier.panel = panel
    pilot.snapshot = snapshot
    pilot.main()
