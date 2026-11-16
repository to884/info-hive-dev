"""契約の試験（ADR-0025）で使う合成の PDF を作る。reportlab 4.4.4 と Pillow で作る。

どのページも、PDFium の判定（kind）が決まった値になるように作る。作った PDF の判定は、
試験の側でも確かめる（判定がずれたら、試料が意図どおりでない）。
"""

from __future__ import annotations

import random
from pathlib import Path

# 合成の PDF のページと、期待する判定
KINDS_PDF = ["text", "vertical", "garbled", "scan", "blank", "text"]


def _long_text(seed: int, lines: int) -> list[str]:
    rng = random.Random(seed)
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "theta", "kappa", "lambda", "sigma"]
    return [" ".join(rng.choice(words) for _ in range(8)) + f" {seed}-{i}" for i in range(lines)]


def make_kinds_pdf(path: Path) -> None:
    """判定の 5 つの種類と、長い本文のページを含む 6 ページの PDF。"""
    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    import reportlab

    font = Path(reportlab.__file__).parent / "fonts" / "Vera.ttf"
    pdfmetrics.registerFont(TTFont("Vera", str(font)))
    width, height = A4
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1)

    # 1: 横書きの本文（text）
    c.setFont("Helvetica", 11)
    for i, line in enumerate(_long_text(1, 30)):
        c.drawString(60, height - 60 - i * 16, line)
    c.showPage()

    # 2: 文字を 90 度回して縦に並べる（vertical。PDFium の文字の角度で判定される）
    c.setFont("Helvetica", 12)
    for column in range(6):
        text = c.beginText()
        text.setTextOrigin(width - 80 - column * 40, height - 80)
        text.setTextTransform(0, -1, 1, 0, width - 80 - column * 40, height - 80)
        text.textLine(f"vertical column {column} reads down the page")
        c.drawText(text)
    c.showPage()

    # 3: garbled のページは、あとで _garbled_page_pdf のページに差しかえる（ここは場所だけを取る）
    c.setFont("Helvetica", 12)
    c.drawString(60, height - 60, "placeholder")
    c.showPage()

    # 4: ページを覆う画像と、わずかな文字（scan）
    image = Image.new("RGB", (400, 560), "white")
    for x in range(0, 400, 8):
        for y in range(0, 560, 8):
            if (x * 7 + y * 3) % 5 == 0:
                image.putpixel((x, y), (0, 0, 0))
    c.drawImage(ImageReader(image), 0, 0, width=width, height=height)
    c.setFont("Helvetica", 9)
    c.drawString(40, 40, "p4")
    c.showPage()

    # 5: 何もない（blank）
    c.showPage()

    # 6: 長い本文（分けて読む試験で、ページの途中で分ける）
    c.setFont("Helvetica", 10)
    for i, line in enumerate(_long_text(6, 45)):
        c.drawString(50, height - 50 - i * 15, line)
    c.showPage()
    c.save()

    # 3 ページ目を、文字が私用領域に対応づいたページに差しかえる
    from pypdf import PdfReader, PdfWriter
    import io

    base = PdfReader(str(path))
    garbled = PdfReader(io.BytesIO(_garbled_page_pdf()))
    cid = PdfReader(io.BytesIO(_cid_page_pdf()))
    writer = PdfWriter()
    for number, page in enumerate(base.pages, start=1):
        writer.add_page(garbled.pages[0] if number == 3 else page)
    writer.add_page(cid.pages[0])
    with path.open("wb") as handle:
        writer.write(handle)


# 7 ページ目（_cid_page_pdf）を足したあとの判定。7 ページ目は判定によらず、確かめるべきページになる
CHECK_PAGES = [4, 7]


def _garbled_page_pdf() -> bytes:
    """Helvetica の A〜Z を描くが、ToUnicode で U+E041〜U+E05A（私用領域）に対応づけた 1 ページの PDF。

    字形はあるので、PDFium は文字を数え、私用領域の文字として返す（判定は garbled になる）。
    """
    cmap = (b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
            b"/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
            b"/CMapName /Garbled def /CMapType 2 def\n1 begincodespacerange <00> <FF> endcodespacerange\n"
            b"1 beginbfrange <41> <5A> <E041> endbfrange\nendcmap CMapName currentdict /CMap defineresource pop end end\n")
    lines = b"".join(b"BT /F1 12 Tf 60 %d Td (ABCDEFGHIJKLMNOPQRSTUVWXYZ) Tj ET\n" % (780 - i * 20) for i in range(12))
    return _one_page_pdf(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /ToUnicode 6 0 R >>", lines, cmap)


def _cid_page_pdf() -> bytes:
    """本文は Helvetica で読めるが、1 行だけ ToUnicode のない Identity-H の CID フォントで描いた 1 ページの PDF。

    pdfminer は、その行の文字を (cid:<数>) と出す（確かめるべきページになる）。
    """
    lines = b"".join(b"BT /F1 11 Tf 60 %d Td (ordinary readable line %d with plain words) Tj ET\n" % (780 - i * 18, i)
                     for i in range(20))
    lines += b"BT /F2 11 Tf 60 380 Td <0021002200230024> Tj ET\n"
    fonts = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
             b"<< /Type /Font /Subtype /Type0 /BaseFont /NoUnicode /Encoding /Identity-H /DescendantFonts [7 0 R] >>",
             b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /NoUnicode "
             b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor 8 0 R >>",
             b"<< /Type /FontDescriptor /FontName /NoUnicode /Flags 4 /FontBBox [0 0 1000 1000] /ItalicAngle 0 "
             b"/Ascent 800 /Descent -200 /CapHeight 700 /StemV 80 >>")
    return _one_page_pdf(fonts[0], lines, None, extra_fonts=fonts[1:])


def _one_page_pdf(font: bytes, content: bytes, cmap: bytes | None, extra_fonts: tuple[bytes, ...] = (),
                  extra_objects: tuple[bytes, ...] = ()) -> bytes:
    """1 ページの PDF を手で組み立てる。オブジェクトの番号は 1〜5 が固定で、6 以降に ToUnicode、足したフォント、
    足したオブジェクトの順に並べる。extra_fonts の 1 つ目を /F2 にする（cmap がないときの 6 番）。"""
    font_names = b"/F1 4 0 R" + (b" /F2 6 0 R" if extra_fonts else b"")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << " + font_names
        + b" >> >> /Contents 5 0 R >>",
        font,
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
    ]
    if cmap is not None:
        objects.append(b"<< /Length %d >>\nstream\n" % len(cmap) + cmap + b"endstream")
    objects.extend(extra_fonts)
    objects.extend(extra_objects)
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def make_ties_pdf(path: Path, pages: int = 3) -> None:
    """距離の同じテキストボックスの組ができる PDF（試験 7）。

    字の幅を 0.5 em、高さ（Ascent - Descent）を 1 em と決めた自作のフォントを使い、座標を整数にして、
    距離の計算に誤差が出ないようにする。8 文字の行を 2 行 2 列に並べ、横の組と縦の組の距離
    （まとめたときの余白の面積）をちょうど同じにする。横の組を先にまとめると行の順、縦の組を先に
    まとめると列の順で本文が並ぶ。1 ページに格子を 3 つ置く。
    """
    from pypdf import PdfReader, PdfWriter
    import io

    writer = PdfWriter()
    for page in range(pages):
        content = b""
        for grid in range(3):
            top = 760 - grid * 240
            # 文字の大きさ 8 で、字の幅 4、高さ 8。8 文字の行の幅は 32。縦の間隔 8 で、縦の組の距離は 32 * 8 = 256。
            # 横の間隔 32 で、横の組の距離も 32 * 8 = 256 になる
            for row in range(2):
                for column in range(2):
                    x = 100 + column * (32 + 32)
                    y = top - row * (8 + 8)
                    label = (b"P%dG%dR%dC%d" % (page, grid, row, column)).ljust(8, b"x")[:8]
                    content += b"BT /F1 8 Tf %d %d Td (%s) Tj ET\n" % (x, y, label)
        single = _one_page_pdf(_TIE_FONT, content, None, extra_objects=_TIE_EXTRA)
        writer.add_page(PdfReader(io.BytesIO(single)).pages[0])
    with path.open("wb") as handle:
        writer.write(handle)


# 自作のフォント。字の幅はどれも 500（0.5 em）、Ascent 750、Descent -250（高さ 1 em）
_TIE_FONT = (b"<< /Type /Font /Subtype /Type1 /BaseFont /TieMetrics /FirstChar 32 /LastChar 126 /Widths ["
             + b" ".join([b"500"] * 95) + b"] /FontDescriptor 6 0 R /Encoding /WinAnsiEncoding >>")
_TIE_EXTRA = (b"<< /Type /FontDescriptor /FontName /TieMetrics /Flags 32 /FontBBox [0 -250 500 750] /ItalicAngle 0 "
              b"/Ascent 750 /Descent -250 /CapHeight 700 /StemV 80 >>",)
