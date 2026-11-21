"""割当軸の長さと直交軸の中心を、固定画素の両辺で見せる。"""

import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v40-frame-edge-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("rectangular_frame_example", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
earlier.HERE = pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v43-frame-rectangle-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
earlier.GUIDE += (
    "色を付けていない範囲は上下と左右の両方で囲った元の枠です。"
    "横方向で半分以上入る字でも、上下方向で字の中心が枠から離れていれば所属しません。"
    "縦方向で半分以上入る字でも、左右方向で字の中心が枠から離れていれば所属しません。"
    "右側の同じ元画像は字の全幅・全高を確かめるために用い、色の付いた所にある周囲の参照本文を追加しません。"
)


def panel(im, rect, axis, side, dpi, font):
    l, t, r, b = earlier.crop_bounds(im, rect, axis, side, dpi)
    raw = im.crop((l, t, r, b)).convert("RGB")
    magnification = 8 if dpi == 150 else 3
    pixels = raw.resize((raw.width * magnification, raw.height * magnification), Image.Resampling.NEAREST)
    expanded = np.array(pixels)
    height, width = expanded.shape[:2]
    x0, y0, x1, y1 = rect
    x = (np.arange(width) + .5) / magnification + l
    y = (np.arange(height) + .5) / magnification + t
    inner = (y0 <= y[:, None]) & (y[:, None] < y1) & (x0 <= x[None, :]) & (x[None, :] < x1)
    outside = [248, 214, 196]
    expanded[~inner] = expanded[~inner] / 8 + np.asarray(outside, dtype=float) * 7 / 8
    tile = Image.new("RGB", (max(280, 2 * width + 22), height + 46), "white")
    draw = ImageDraw.Draw(tile)
    for x, label, image in ((5, f"{dpi} DPI 上下・左右の枠内", Image.fromarray(expanded)),
                            (width + 16, "同じ元画像", pixels)):
        draw.text((x, 3), label, font=font, fill="#222222")
        tile.paste(image, (x, 29))
    return tile


def snapshot():
    plan = earlier.snapshot()
    methods = (Path(__file__), BASE, BASE.parent / "lock.json")
    plan["files"].update({str(p): pilot.audit.sha(p) for p in methods})
    return plan


if __name__ == "__main__":
    earlier.panel = panel
    pilot.snapshot = snapshot
    pilot.main()
