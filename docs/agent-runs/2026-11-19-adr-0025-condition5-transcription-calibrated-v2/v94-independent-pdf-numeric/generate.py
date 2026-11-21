"""独立した開発PDFを生成し、描画を一つずつ除いた画像差で正解の位置を測る。"""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE = Path(__file__).resolve().parent
POINT = 72 / 150
PAGE = (384, 424)
FONTS = (("ReadingSans", 9, "arial.ttf"), ("ReadingSerif", 9, "times.ttf"), ("ReadingMono", 9, "cour.ttf"))
DIGITS = (
    ("39821", "81764", "67259", "52483", "26849", "73596", "91472", "35618"),
    ("58247", "75481", "29168", "63475", "18792", "46957", "92536", "81379"),
    ("68529", "47261", "26795", "93647", "57186", "84931", "31586", "69274"),
)
POSITIONS = ("inside", "edge", "outside")


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def rows():
    items = []
    for page, ((font, size, _), numbers) in enumerate(zip(FONTS, DIGITS, strict=True), start=1):
        for index, digits in enumerate(numbers):
            n = len(items) + 1
            group = POSITIONS[index // 2] if index < 6 else "no-comma"
            items.append({"id": f"X{n:03d}", "page": page, "digits": digits,
                          "position": group, "noise": bool((index + page) % 2),
                          "font": font, "size": size, "x": 115.2, "y": 343.2 - 38.4 * index})
    return items


def show_page_doc(data, shift, mode):
    memory = BytesIO()
    doc = Canvas(memory, pagesize=PAGE, invariant=True, pageCompression=1)
    doc.setTitle("Development sample - numbered measurements")
    for page in range(1, 4):
        doc.setFillColor(HexColor("#12263a"))
        doc.setFont("Helvetica-Bold", 15)
        doc.drawString(30, 392, "Instrument readings")
        doc.setFont("Helvetica", 8)
        doc.drawString(30, 376, "Development table  /  Sheet " + str(page))
        doc.setFillColor(HexColor("#e4edf5"))
        doc.rect(30, 357, 324, 13, fill=1, stroke=0)
        doc.setFillColor(HexColor("#23364e"))
        for x, name in ((39, "Sample"), (115, "Reading"), (257, "Status")):
            doc.drawString(x, 361, name)
        for row in (x for x in data if x["page"] == page):
            x, y, ident = row["x"], row["y"], row["id"]
            if int(ident[1:]) % 2 == 0:
                doc.setFillColor(HexColor("#f4f7fa"))
                doc.rect(30, y - 14, 324, 35, fill=1, stroke=0)
            doc.setFillColor(HexColor("#26364a"))
            doc.setFont("Helvetica", 8)
            doc.drawString(39, y, f"M-{ident[1:]}")
            doc.drawString(257, y, "Measured")
            doc.setFillColor(HexColor("#161c25"))
            font, size = row["font"], row["size"]
            doc.setFont(font, size)
            # 左右の数値は、それぞれ実際のフォントで描画する。
            digits = row["digits"]
            separator_x = x + stringWidth(digits[:2], font, size) + 1.9
            end_x = separator_x + stringWidth(",", font, size) + 3.7
            doc.drawString(x, y, digits[:2])
            doc.drawString(end_x, y, digits[2:])
            if row["position"] != "no-comma" and mode != "no-comma":
                offset, size_delta = shift.get(ident, (0.0, 0.0))
                doc.setFont(font, size + size_delta)
                doc.drawString(separator_x, y + offset, ",")
            if row["noise"] and mode != "no-noise":
                doc.setStrokeColor(HexColor("#4e5664"))
                doc.setLineWidth(.76)
                nx = separator_x + stringWidth(",", font, size) + .75
                if int(ident[1:]) % 3 == 0:
                    doc.line(nx - .14, y + 1.18, nx + .43, y + 2.45)
                else:
                    doc.line(nx, y + .88, nx + .72, y + 2.13)
        doc.showPage()
    doc.save()
    return memory.getvalue()


def render(renderer, pdf, output, dpi):
    subprocess.run([str(renderer), "-png", "-r", str(dpi), str(pdf), str(output)], check=True)
    pages = [output.with_name(f"{output.name}-{n}.png") for n in range(1, 4)]
    if not all(p.is_file() for p in pages):
        raise ValueError("独立PDFを三頁とも描画できない")
    return pages


def local_window(row):
    left = round(row["x"] / POINT) - 4
    top = round((PAGE[1]-row["y"]) / POINT) - 24
    return left, top, left + 98, top + 38


def gray_pages(paths):
    result = []
    for file in paths:
        with Image.open(file) as im:
            result.append(np.array(im.convert("L")))
    return result


def region(full, empty, row):
    x, y, right, bottom = local_window(row)
    area = full[row["page"]-1][y:bottom,x:right]
    control = empty[row["page"]-1][y:bottom,x:right]
    threshold = int(np.median(area)) - 64
    ys, xs = np.nonzero((area < threshold) & (control >= threshold))
    if not len(xs):
        return None
    return [x+int(xs.min()), y+int(ys.min()), x+int(xs.max())+1, y+int(ys.max())+1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdftoppm", required=True, type=Path)
    args = parser.parse_args()
    pdf = HERE / "development-measurements.pdf"
    output = HERE / "fixed-pages"
    truth_path = HERE / "physical-truth.json"
    if any(p.exists() for p in (pdf, output, truth_path)):
        raise FileExistsError("開発用資料を上書きしない")
    font_dir = Path(os.environ["WINDIR"]) / "Fonts"
    fonts = {font: font_dir / name for font, _, name in FONTS}
    for font, file in fonts.items():
        registerFont(TTFont(font, str(file)))
    data = rows()
    with TemporaryDirectory(prefix="adr25-v94-") as temp:
        scratch = Path(temp)
        base = scratch / "no-comma.pdf"
        base.write_bytes(show_page_doc(data, {}, "no-comma"))
        blank = gray_pages(render(args.pdftoppm, base, scratch/"nc", 150))
        phase = {}
        open_rows = {r["id"] for r in data if r["position"] != "no-comma"}
        # 150 DPIで中心が整数画素になる最初の位相をPDF側で選ぶ。
        for n, step in enumerate(((0, 0), (.23, 0), (-.23, 0), (0, .5), (0, -.5), (0, 1), (0, -1), (.25, 1.5), (-.25, -1.5))):
            attempt = scratch/f"phase-{n}.pdf"
            attempt.write_bytes(show_page_doc(data, {key:step for key in open_rows}, "full"))
            rendered = gray_pages(render(args.pdftoppm, attempt, scratch/f"p{n}", 150))
            for row in data:
                key = row["id"]
                if key not in open_rows:
                    continue
                bounds = region(rendered, blank, row)
                if bounds and (bounds[1]+bounds[3]) % 2 == 0:
                    phase[key] = step
            open_rows.difference_update(phase)
            if not open_rows:
                break
        if open_rows:
            raise ValueError("中心を整数画素にそろえられない: " + ", ".join(sorted(open_rows)))
        whole = scratch / "main.pdf"
        whole.write_bytes(show_page_doc(data, phase, "full"))
        clean = scratch / "clean.pdf"
        clean.write_bytes(show_page_doc(data, phase, "no-noise"))
        proof_150 = render(args.pdftoppm, whole, scratch/"main-150", 150)
        proof_450 = render(args.pdftoppm, whole, scratch/"main-450", 450)
        full = gray_pages(proof_150)
        no_noise = gray_pages(render(args.pdftoppm, clean, scratch/"noise-free", 150))
        for row in data:
            ident, kind = row["id"], row["position"]
            box = region(full, blank, row)
            adjacent = region(full, no_noise, row)
            x, _, _, _ = local_window(row)
            baseline = round((PAGE[1]-row["y"]) / POINT)
            if (box is not None) != (kind != "no-comma") or (adjacent is not None) != row["noise"]:
                raise ValueError("コンマか余分な筆画の有無が設計と異なる: " + ident)
            if box:
                mid = (box[1]+box[3]) // 2
                if box[1]+box[3] != 2*mid:
                    raise ValueError("固定ラスターの中心が境界に一致しない: " + ident)
                lower = mid + {"inside": 1, "edge": 0, "outside": -1}[kind]
            else:
                lower = baseline + 1
            font, size = row["font"], row["size"]
            ending = (stringWidth(row["digits"], font, size) + stringWidth(",", font, size) + 5.6) / POINT
            width = round(ending) + 9
            top = baseline - 18
            row["box"] = [x, top, width, lower-top]
            row["allocation_axis"] = "x"
            row["expected"] = row["digits"] if kind in ("outside","no-comma") else row["digits"][:2] + "," + row["digits"][2:]
            row["comma_150"], row["noise_150"], row["comma_offset_and_size_delta_pt"] = box, adjacent, phase.get(ident)
            if box and adjacent:
                hgap = max(box[0]-adjacent[2], adjacent[0]-box[2], 0)
                vgap = max(box[1]-adjacent[3], adjacent[1]-box[3], 0)
                if max(hgap, vgap) > 8:
                    raise ValueError("余分な筆画がコンマから離れすぎている: " + ident)
        output.mkdir()
        pdf.write_bytes(whole.read_bytes())
        pins = {}
        for dpi, pages in ((150, proof_150),(450, proof_450)):
            for n, path in enumerate(pages, start=1):
                saved = output / f"page-{n}-{dpi}.png"
                saved.write_bytes(path.read_bytes())
                pins[saved.name] = sha(saved)
    payload = {"scope":"new-synthetic-development-pdf", "pdf_sha256":sha(pdf),
               "page_png_sha256":pins, "font_sha256":{k:sha(v) for k,v in fonts.items()}, "rows":data}
    truth_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(len(data), "枠、PDF SHA-256", payload["pdf_sha256"])


if __name__ == "__main__":
    main()
