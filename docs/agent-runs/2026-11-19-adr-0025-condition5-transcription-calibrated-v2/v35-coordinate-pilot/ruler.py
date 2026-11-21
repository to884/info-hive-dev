"""固定150 DPIの横座標に、10画素ごとの数値と5画素の小目盛りを付ける。"""

import io
import math

from PIL import Image, ImageDraw, ImageFont


def cards(row, png, ident, segments, typeface):
    x, y, w, h = row["box"]
    if row["allocation_axis"] != "x":
        raise ValueError("横軸の固定枠にだけ横座標を付ける")
    font = ImageFont.truetype(typeface, size=15)
    labels = ImageFont.truetype(typeface, size=17)
    scale = 5
    out = {}
    with Image.open(png) as image:
        for i, (start, stop) in enumerate(segments(w * 3), 1):
            l, r = max(0, x + start // 3 - 5), min(image.width, x + math.ceil(stop / 3) + 5)
            t, b = max(0, y - 5), min(image.height, y + h + 5)
            raw = image.crop((l, t, r, b)).convert("RGB")
            window = raw.resize((raw.width * scale, raw.height * scale), Image.Resampling.NEAREST)
            width, height = window.size
            tile = Image.new("RGB", (max(300, width + 42), height + 108), "white")
            draw = ImageDraw.Draw(tile)
            left, top = 21, 62
            draw.text((8, 3), f"{ident}　横座標 {i}　固定150 DPI　数字の間隔は10", fill="#222222", font=labels)
            draw.line((left, top - 4, left + width, top - 4), fill="#777777")
            draw.line((left, top + height + 4, left + width, top + height + 4), fill="#777777")
            for axis in range(0, w + 1, 5):
                tick = left + scale * (x + axis - l)
                if not left <= tick <= left + width:
                    continue
                primary = axis % 10 == 0
                size = 11 if primary else 5
                color = "#7a1931" if primary else "#999999"
                draw.line((tick, top - 4 - size, tick, top - 4), fill=color)
                draw.line((tick, top + height + 4, tick, top + height + 4 + size), fill=color)
                if primary:
                    draw.text((tick, top - 20), str(axis), anchor="mb", fill="#222222", font=font)
                    draw.text((tick, top + height + 18), str(axis), anchor="mt", fill="#222222", font=font)
            tile.paste(window, (left, top))
            out_file = io.BytesIO()
            tile.save(out_file, "PNG")
            out[f"{ident}-coordinate-{i:02d}.png"] = out_file.getvalue()
    return out
