"""条件 5 の合成の試料を作る（測り方は ../../adr-0025-condition5-2026-11-16.md の「合成の PDF」）。

使い方: uv run --python 3.12 --with reportlab==4.4.4 --with pypdfium2==5.15.2 --with pillow --with numpy \
    python -X utf8 scripts/make_synthetic.py

docs/adr/ の ADR をファイル名の順に並べ、1 つ目を試しの原稿（dev）、2〜25 個目を測る原稿（m00〜m23）にする。
原稿ごとに、5 つの画像（clean、lowres、blur、noise、skew）を 1 ページずつ貼った、画像だけの PDF（5 ページ）を作る。
正解（行の文字と、150 dpi の画像の左上を原点とする行の箱）を <名前>.truth.json に書く。
"""

from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parents[2]
OUT = BENCH / "corpus" / "synthetic"
DPI = 150
CHARS, LINES, SIZE, LEADING = 40, 38, 10.5, 18.0
MARGIN = 20 / 25.4 * 72
VARIANTS = ("clean", "lowres", "blur", "noise", "skew")
FONTS = {"gothic": ("MSGothic", "C:/Windows/Fonts/msgothic.ttc"), "mincho": ("MSMincho", "C:/Windows/Fonts/msmincho.ttc")}


def manuscript_text(path: Path, cmap: set[int]) -> str:
    """ADR の本文から Markdown の記号を除き、空白を詰め、フォントにない文字を除いて、先頭の 1,520 文字を返す。"""
    s = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    s = re.sub(r"```.*?```", " ", s, flags=re.S)          # コードの囲み
    s = re.sub(r"^\s*\|?\s*:?-{3,}.*$", " ", s, flags=re.M)  # 表の区切りの行
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)       # リンクは文字だけ残す
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)           # 見出しの #
    s = s.replace("|", " ").replace("**", "").replace("*", "").replace("`", "")
    s = re.sub(r"\s+", " ", s).strip()
    s = "".join(c for c in s if ord(c) in cmap or c == " ")
    return s[:CHARS * LINES]


def draw_vector(text: str, font: str) -> tuple[bytes, list[dict]]:
    """原稿を A4 に描いた PDF と、行の正解（PDF の座標、左下が原点）を返す。"""
    name = FONTS[font][0]
    face = pdfmetrics.getFont(name).face
    ascent, descent = face.ascent * SIZE / 1000, face.descent * SIZE / 1000
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont(name, SIZE)
    width, height = A4
    lines = []
    for i in range(LINES):
        chunk = text[i * CHARS:(i + 1) * CHARS]
        if not chunk:
            break
        baseline = height - MARGIN - SIZE - i * LEADING
        c.drawString(MARGIN, baseline, chunk)
        lines.append({"text": chunk, "pt": [MARGIN, baseline + descent, MARGIN + pdfmetrics.stringWidth(chunk, name, SIZE),
                                            baseline + ascent]})
    c.showPage()
    c.save()
    return buffer.getvalue(), lines


def render(data: bytes, dpi: int) -> Image.Image:
    with pdfium.PdfDocument(data) as document:
        page = document[0]
        bitmap = page.render(scale=dpi / 72, grayscale=True)
        image = bitmap.to_pil().convert("L")
        bitmap.close()
        page.close()
    return image


def degrade(data: bytes, variant: str, seed: int) -> Image.Image:
    if variant == "lowres":
        return render(data, 100)
    image = render(data, DPI)
    if variant == "blur":
        return image.filter(ImageFilter.GaussianBlur(radius=1.0))
    if variant == "noise":
        rng = np.random.default_rng(seed)
        values = np.asarray(image, dtype=np.float64) + rng.normal(0, 20, size=(image.height, image.width))
        return Image.fromarray(np.clip(values, 0, 255).round().astype(np.uint8), mode="L")
    if variant == "skew":
        return image.rotate(1.0, resample=Image.BICUBIC, fillcolor=255)
    return image


def pixel_box(pt: list[float], variant: str) -> list[float]:
    """PDF の座標の箱を、150 dpi の画像の左上を原点とする箱 [x0, y0, x1, y1] にする。skew は 4 隅を回して囲む。"""
    scale = DPI / 72
    width, height = A4
    x0, y0, x1, y1 = pt[0] * scale, (height - pt[3]) * scale, pt[2] * scale, (height - pt[1]) * scale
    if variant != "skew":
        return [x0, y0, x1, y1]
    # PIL の rotate と同じ中心（画像の中心）で、見た目で反時計回りに 1 度回す（y は下向き）
    cx, cy = round(width * scale) / 2, round(height * scale) / 2
    theta = math.radians(1.0)
    xs, ys = [], []
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        dx, dy = x - cx, y - cy
        xs.append(cx + dx * math.cos(theta) + dy * math.sin(theta))
        ys.append(cy - dx * math.sin(theta) + dy * math.cos(theta))
    return [min(xs), min(ys), max(xs), max(ys)]


def image_pdf(images: list[Image.Image]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    for image in images:
        c.drawImage(ImageReader(image), 0, 0, width=width, height=height)
        c.showPage()
    c.save()
    return buffer.getvalue()


def main() -> None:
    for name, path in FONTS.values():
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
    cmaps = {font: set(pdfmetrics.getFont(FONTS[font][0]).face.charToGlyph) for font in FONTS}
    adrs = sorted((ROOT / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md"))[:25]
    OUT.mkdir(parents=True, exist_ok=True)
    plan = [("dev", adrs[0], 99, "gothic")] + [
        (f"m{i:02d}", adrs[i + 1], i, "gothic" if i % 4 in (0, 1) else "mincho") for i in range(24)]
    for name, path, seed, font in plan:
        text = manuscript_text(path, cmaps[font])
        vector, lines = draw_vector(text, font)
        images = [degrade(vector, variant, seed) for variant in VARIANTS]
        (OUT / f"{name}.pdf").write_bytes(image_pdf(images))
        side = "dev" if name == "dev" else ("tuning" if seed % 2 == 0 else "evaluation")
        truth = {"name": name, "source": path.relative_to(ROOT).as_posix(), "font": font, "side": side, "seed": seed,
                 "pages": [{"page": n, "variant": variant, "kind": "scan",
                            "lines": [{"id": k, "text": line["text"], "box": pixel_box(line["pt"], variant)}
                                      for k, line in enumerate(lines)]}
                           for n, variant in enumerate(VARIANTS, start=1)]}
        (OUT / f"{name}.truth.json").write_bytes(json.dumps(truth, ensure_ascii=False, indent=1).encode("utf-8"))
        print(name, side, font, path.name, len(text), "文字", len(lines), "行")


if __name__ == "__main__":
    main()
