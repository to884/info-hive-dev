"""固定450 DPIの枠を切れ目の前後が重ならない連続区間で提示する。"""

from hashlib import sha256
import io
import math

import numpy as np
from PIL import Image, ImageDraw

COMMON = (
    "『連続区間』は同じ枠の固定450 DPIの画素を、一度ずつ番号順に表示しています。"
    "区間の境界は画像の切れ目で、字や本文の区切りを示しません。区間の端を次の区間と見比べます。"
    "本文と所属は元の枠と前後の画像でも確認し、連続区間と元の画像にある同じ字を一回だけ写します。"
    "似た字体は部品の交差、はね、短い点と長い斜線を一画ずつ確かめます。"
    "固有名詞やよく使われる表記から文字を補わず、見える画に対応する字を写します。"
)
HORIZONTAL = (
    "括弧に見える曲線が仮名の一画を作る場合は、その字の他の画とつなげて確認します。"
    "字の間に独立して印刷された括弧だけを写します。"
)
VERTICAL = (
    "縦の各区間を番号順に、各区間内は上から下に確認します。"
    "意味をつなげるだけで読み飛ばさず、細い横画が二本ある一字も始点と終点を確かめます。"
    "四角い字は同じ列の四角い字体があれば輪郭、角の向きと下端、空白の幅を比べます。"
)


def eligible(row):
    w, h = row["box"][2:]
    if row["allocation_axis"] == "y":
        return 12 <= w <= 48 and h > 120
    return w >= 100 and 15 <= h <= 35


def measure(body, vertical):
    gray = np.array(body.convert("L"))
    if not vertical:
        gray = gray.T
    projections = []
    for level in (140, 186):
        ink = gray < level
        reliable = ink[:, ink.mean(axis=0) < .78]
        if reliable.shape[1] == 0:
            reliable = ink
        projections.append(reliable.sum(axis=1))
    return np.maximum(*projections)


def sections(profile, size):
    extent = len(profile)
    points = [0]
    cut = size
    spread = round(.23 * size)
    while cut + size * .46 < extent:
        lo, hi = cut - spread, min(extent - 2, cut + spread + 1)
        border = min(range(lo, hi), key=lambda p: (max(profile[p - 1:p + 2]), sum(profile[p - 1:p + 2]), abs(p - cut), p))
        points.append(border)
        cut += size
    points.append(extent)
    return list(zip(points[:-1], points[1:], strict=True))


def strip_images(source, rectangle, label, font, axis):
    l, t, r, b = rectangle
    x, y = max(0, math.floor(l)), max(0, math.floor(t))
    end_x, end_y = min(source.width, math.ceil(r)), min(source.height, math.ceil(b))
    body = source.crop((x, y, end_x, end_y)).convert("RGB")
    vertical = axis == "y"
    pixels = measure(body, vertical)
    standard = min(440, max(165, (body.width if vertical else body.height) * (4 if vertical else 5)))
    parts = sections(pixels, standard)
    canvas = Image.new("RGB", body.size)
    tiles = []
    for start, end in parts:
        bounds = (0, start, body.width, end) if vertical else (start, 0, end, body.height)
        fragment = body.crop(bounds)
        canvas.paste(fragment, bounds[:2])
        tiles.append(fragment)
    if canvas.tobytes() != body.tobytes():
        raise ValueError("全区間を連結した画素が元の固定画像と異なる")

    panels = {}
    for panel, first in enumerate(range(0, len(tiles), 4), 1):
        display = [piece.resize((piece.width * 2, piece.height * 2), Image.Resampling.NEAREST)
                   for piece in tiles[first:first + 4]]
        if vertical:
            advance = max(128, 2 * body.width + 16)
            width, height = advance * len(display), 76 + max(p.height for p in display)
            places = [(i * advance + 8, 66) for i in range(len(display))]
        else:
            advance = 2 * body.height + 39
            width, height = max(p.width for p in display) + 16, 42 + advance * len(display)
            places = [(8, 71 + i * advance) for i in range(len(display))]
        sheet = Image.new("RGB", (max(315, width), height), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((5, 5), f"{label}　連続区間 {panel}　固定450 DPI", font=font, fill="#202020")
        for idx, ((px, py), img) in enumerate(zip(places, display, strict=True), first + 1):
            draw.text((px, py - 26), f"区間 {idx}", font=font, fill="#254b76")
            sheet.paste(img, (px, py))
            if sheet.crop((px, py, px + img.width, py + img.height)).tobytes() != img.tobytes():
                raise ValueError("拡大した固定画素の上に表示が重なった")
        out = io.BytesIO()
        sheet.save(out, "PNG")
        panels[f"{label}-continuous-strips-{panel:02d}.png"] = out.getvalue()
    return panels, {"rectangle": [x, y, end_x, end_y], "segments": parts, "content_sha256": sha256(body.tobytes()).hexdigest()}
