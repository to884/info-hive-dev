"""本物の小数点と追加の黒点を分けて描き、固定画像を生成する。"""

from io import BytesIO
from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFont


WINDOWS_FONTS = Path("C:/Windows/Fonts")
BLOCKS = (("arial.ttf", "46329"), ("times.ttf", "82647"),
          ("calibri.ttf", "29738"), ("consola.ttf", "71864"))
GROUPS = ("decimal-only", "aligned-noise", "offset-noise", "both")
SIZE = (142, 47)
BOX = (24, 12, 94, 24)
BASELINE = 32
THRESHOLD = 72


def png(pixels, dpi):
    output = BytesIO()
    pixels.save(output, format="PNG", dpi=(dpi, dpi))
    return output.getvalue()


def downsample(pixels):
    return pixels.resize(SIZE, Image.Resampling.LANCZOS)


def bounds(pixels):
    return pixels.point(lambda x: 255 if x >= THRESHOLD else 0).getbbox()


def blank():
    return Image.new("L", (SIZE[0] * 3, SIZE[1] * 3))


def contact(a, b):
    al, at, ar, ab = a
    bl, bt, br, bb = b
    return min(ar, br) > max(al, bl) and min(ab, bb) > max(at, bt)


def inside(b, k):
    x, y, w, h = BOX
    l, t, r, z = b
    return x*k < l < r < (x+w)*k and y*k < t < z < (y+h)*k


def render(block, group):
    name, digits = BLOCKS[block]
    font = ImageFont.truetype(str(WINDOWS_FONTS/name), 56)
    left, baseline = 32*3, BASELINE*3
    split = 2
    ldigits, rdigits = digits[:split], digits[split:]
    left_bound = left + round(font.getlength(ldigits))
    point_x = left_bound + 18
    right = point_x + round(font.getlength(".")) + 18
    digits_pixels = blank()
    draw = ImageDraw.Draw(digits_pixels)
    draw.text((left, baseline), ldigits, font=font, anchor="ls", fill=231)
    draw.text((right, baseline), rdigits, font=font, anchor="ls", fill=231)
    decimal = blank()
    ImageDraw.Draw(decimal).text((point_x, baseline), ".", font=font, anchor="ls", fill=231)
    text_dot = bounds(decimal)
    if not text_dot:
        raise ValueError("フォントの小数点を描けない")
    noise = blank()
    if group in {"aligned-noise", "offset-noise", "both"}:
        offset = 0 if group == "aligned-noise" else (-1 if block % 2 else 1) * 15
        lift = 0 if group == "aligned-noise" else (-9 if block < 2 else 6)
        noise = ImageChops.offset(decimal, offset, lift)
    pieces = {}
    if group in {"decimal-only","both"}:
        pieces["decimal"] = decimal
    if group != "decimal-only":
        pieces["noise"] = noise
    measurement, pixels = {}, {}
    for dpi,k in ((150,1),(450,3)):
        rendered_digits = digits_pixels if k==3 else downsample(digits_pixels)
        actual = rendered_digits
        dots = {}
        for role, piece in pieces.items():
            paint = piece if k==3 else downsample(piece)
            b = bounds(paint)
            if b is None or not inside(b,k) or b[0] <= left_bound*k/3 or b[2] >= right*k/3:
                raise ValueError(f"点が枠内の数字間にない: {name} {group} {dpi} {b}")
            if any(contact(b,other) for other in dots.values()):
                raise ValueError(f"点が分離していない: {name} {group} {dpi}")
            dots[role] = b
            actual = ImageChops.lighter(actual, paint)
        digit_box = bounds(rendered_digits)
        if digit_box is None or not inside(digit_box,k):
            raise ValueError("数字が枠内にない")
        measurement[dpi] = dots
        pixels[dpi] = ImageChops.invert(actual).convert("RGB")
    by_position = sorted(pieces, key=lambda key: measurement[150][key][0])
    if by_position != sorted(pieces,key=lambda key: measurement[450][key][0]):
        raise ValueError("点の並びが解像度間で異なる")
    components = [{"id": ident, "role": kind, "bounds": measurement[150][kind],
                   "high_bounds": measurement[450][kind]}
                  for ident,kind in enumerate(by_position,6)]
    return digits, components, pixels


def schedule():
    rows = [(block,group) for block in range(len(BLOCKS)) for group in GROUPS]
    Random(250516).shuffle(rows)
    return [(f"Q{index:03d}", block, group) for index,(block,group) in enumerate(rows,1)]

