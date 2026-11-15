"""撮った画像を、ページと配色と幅ごとに 5 つのブラウザを横に並べた 1 枚にまとめる。

使い方: uv run --with pillow python sheet.py <撮った画像の置き場所> <まとめた画像の置き場所>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

BROWSERS = ["chromium", "firefox", "webkit", "msedge", "chrome"]
PAGES = ["index", "design", "release"]
SCHEMES = ["light", "dark"]
WIDTHS = [1280, 360]

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dst.mkdir(parents=True, exist_ok=True)
for page in PAGES:
    for scheme in SCHEMES:
        for width in WIDTHS:
            shots = [Image.open(src / f"{b}-{page}-{scheme}-{width}.png").convert("RGB") for b in BROWSERS]
            # 幅 1280 は半分に縮めて並べる
            scale = 0.5 if width == 1280 else 1.0
            shots = [s.resize((int(s.width * scale), int(s.height * scale))) for s in shots]
            w = sum(s.width for s in shots) + 10 * (len(shots) - 1)
            h = max(s.height for s in shots) + 24
            sheet = Image.new("RGB", (w, h), (128, 128, 128))
            draw = ImageDraw.Draw(sheet)
            x = 0
            for name, s in zip(BROWSERS, shots):
                draw.text((x + 4, 4), name, fill=(0, 0, 0))
                sheet.paste(s, (x, 24))
                x += s.width + 10
            sheet.save(dst / f"{page}-{scheme}-{width}.png")
print("ok")
