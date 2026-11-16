# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["reportlab==4.4.4", "pypdf==6.1.3"]
# ///
"""ADR-0025 の承認の条件 2 のための合成の PDF を corpus/synthetic-pages.pdf に作る。

使い方: uv run --script make_synthetic.py
各ページに「MARKER-Pnn」（nn はページの番号）を書く。PDFium と pdfminer が、同じ番号のページで
同じ目印を返すかを check_pages.py で確かめる。期待は expected-pages.json に書く。

| ページ | 中身 |
| --- | --- |
| 1、2 | ふつうの縦長のページ |
| 3、4、5 | /Rotate 90、180、270 |
| 6 | 中身を 90 度回して描いたページ（/Rotate はない） |
| 7 | 注釈（FreeText）だけのページ。本文の文字はない |
| 8 | 白紙 |
| 9 | CropBox で下半分を隠したページ。隠した側に「HIDDEN-P09」を書く |
| 10、11 | /Rotate 90 を、親の /Pages から受け継ぐページ |
| 12 | 横長のページ |

ページツリーは入れ子にする: ルート → [Pages(1〜3), Pages(Pages(4〜6), 7), 8, Pages(Rotate 90: 10、11)、9、12]
のような形で、ページの順は 1〜12 のまま、親の /Pages を挟む。
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, RectangleObject
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

BENCH = Path(__file__).resolve().parent.parent
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))


def base_pdf() -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    for n in range(1, 13):
        size = landscape(A4) if n == 12 else A4
        c.setPageSize(size)
        w, h = size
        if n in (7, 8):
            c.showPage()
            continue
        c.setFont("HeiseiKakuGo-W5", 14)
        if n == 6:
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(90)
            c.drawString(-150, 0, f"MARKER-P{n:02d} これは {n} ページ目の本文です。")
            c.restoreState()
        else:
            c.drawString(72, h - 100, f"MARKER-P{n:02d} これは {n} ページ目の本文です。")
        if n == 9:
            c.drawString(72, 100, "HIDDEN-P09 CropBox の外にある文字です。")
        c.showPage()
    c.save()
    return buffer.getvalue()


def main() -> None:
    reader = PdfReader(io.BytesIO(base_pdf()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    pages = writer.pages
    pages[2].rotate(90)
    pages[3].rotate(180)
    pages[4].rotate(270)
    w, h = A4
    pages[8].cropbox = RectangleObject([0, h / 2, w, h])
    writer.add_annotation(page_number=6, annotation=FreeText(
        text="ANNOT-P07 注釈だけのページ", rect=(72, 600, 400, 640), font="Helvetica", font_size="12pt"))

    # 入れ子のページツリーを作る。ページの順は変えない。
    root = writer._root_object["/Pages"]
    page_refs = list(root["/Kids"])

    def make_node(kids, parent, extra=None):
        node = DictionaryObject({NameObject("/Type"): NameObject("/Pages"), NameObject("/Kids"): ArrayObject(kids),
                                 NameObject("/Parent"): parent})
        if extra:
            node.update(extra)
        ref = writer._add_object(node)
        count = 0
        for kid in kids:
            obj = kid.get_object()
            obj[NameObject("/Parent")] = ref
            count += int(obj["/Count"]) if obj["/Type"] == "/Pages" else 1
        node[NameObject("/Count")] = NumberObject(count)
        return ref

    root_ref = writer._root_object.raw_get("/Pages")
    a = make_node(page_refs[0:3], root_ref)
    inner = make_node(page_refs[3:6], root_ref)
    b = make_node([inner, page_refs[6]], root_ref)
    c_node = make_node(page_refs[9:11], root_ref, {NameObject("/Rotate"): NumberObject(90)})
    root[NameObject("/Kids")] = ArrayObject([a, b, page_refs[7], page_refs[8], c_node, page_refs[11]])
    root[NameObject("/Count")] = NumberObject(12)
    for ref in page_refs[9:11]:
        ref.get_object().pop(NameObject("/Rotate"), None)

    out = BENCH / "corpus" / "synthetic-pages.pdf"
    with out.open("wb") as handle:
        writer.write(handle)
    check = PdfReader(str(out))
    order = []
    for page in check.pages:
        text = page.extract_text() or ""
        order.append(next((t for t in text.split() if t.startswith("MARKER-P")), None))
    expected = {"pages": 12, "markers": {str(n): (None if n in (7, 8) else f"MARKER-P{n:02d}") for n in range(1, 13)},
                "hidden": {"9": "HIDDEN-P09"}, "annotation_only": {"7": "ANNOT-P07"},
                "pypdf_order": order, "rotate": {str(i + 1): int(p.rotation) for i, p in enumerate(check.pages)}}
    (BENCH / "corpus" / "expected-pages.json").write_bytes(json.dumps(expected, ensure_ascii=False, indent=2).encode("utf-8"))
    print(json.dumps(expected, ensure_ascii=False))


if __name__ == "__main__":
    main()
