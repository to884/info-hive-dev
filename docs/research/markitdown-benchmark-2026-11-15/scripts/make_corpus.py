# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["python-docx==1.2.0", "python-pptx==1.0.2", "openpyxl==3.1.5"]
# ///
"""ベンチマークの試料を corpus/ に作る。

Office の形式は python-docx、python-pptx、openpyxl で作る。PDF と XLS への書き出しと、
Excel の式の値の計算は export_office.ps1（Office の COM）で行う。
"""

from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from openpyxl import Workbook
from pptx import Presentation
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content as C  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "corpus"


def _page_field(paragraph) -> None:
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = "1"
    run.append(text)
    field.append(run)
    paragraph._p.append(field)


def make_docx(path: Path, two_columns: bool) -> None:
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Yu Gothic"
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "Yu Gothic")
    style.font.size = Pt(11)
    section = document.sections[0]
    section.header.paragraphs[0].text = C.HEADER
    footer = section.footer.paragraphs[0]
    footer.text = "ページ "
    _page_field(footer)
    if two_columns:
        cols = section._sectPr.find(qn("w:cols"))
        if cols is None:
            cols = OxmlElement("w:cols")
            section._sectPr.append(cols)
        cols.set(qn("w:num"), "2")
        cols.set(qn("w:space"), "425")
    document.add_heading(C.TITLE, level=1)
    for index, sec in enumerate(C.SECTIONS + [C.EXTRA_SECTION]):
        if index == 3 and not two_columns:
            document.add_page_break()
        document.add_heading(sec["heading"], level=2)
        for text in sec["paragraphs"]:
            document.add_paragraph(text)
        for text in sec.get("bullets", []):
            document.add_paragraph(text, style="List Bullet")
        for text in sec.get("numbered", []):
            document.add_paragraph(text, style="List Number")
        if "table" in sec:
            rows = sec["table"]
            table = document.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    table.cell(r, c).text = value
    document.save(path)


def make_pptx(path: Path) -> None:
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    for spec in C.SLIDES:
        if "subtitle" in spec:
            slide = deck.slides.add_slide(deck.slide_layouts[0])
            slide.shapes.title.text = spec["title"]
            slide.placeholders[1].text = spec["subtitle"]
        elif "bullets" in spec:
            slide = deck.slides.add_slide(deck.slide_layouts[1])
            slide.shapes.title.text = spec["title"]
            body = slide.placeholders[1].text_frame
            body.text = spec["bullets"][0]
            for text in spec["bullets"][1:]:
                body.add_paragraph().text = text
        elif "table" in spec:
            slide = deck.slides.add_slide(deck.slide_layouts[5])
            slide.shapes.title.text = spec["title"]
            rows = spec["table"]
            shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(1), Inches(1.8),
                                           Inches(11), Inches(4))
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    shape.table.cell(r, c).text = value
        else:
            slide = deck.slides.add_slide(deck.slide_layouts[3])
            slide.shapes.title.text = spec["title"]
            slide.placeholders[1].text = spec["left"]
            slide.placeholders[2].text = spec["right"]
        if "notes" in spec:
            slide.notes_slide.notes_text_frame.text = spec["notes"]
    deck.save(path)


def make_xlsx(path: Path) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "経費"
    for r, row in enumerate(C.SHEET_EXPENSES, start=1):
        for c, value in enumerate(row, start=1):
            if value is None:
                value = f"=SUM(C{r}:E{r})"
            sheet.cell(r, c, value)
    days = book.create_sheet("日別")
    for r, row in enumerate(C.SHEET_DAYS, start=1):
        for c, value in enumerate(row, start=1):
            if r > 1 and c == 1:
                value = dt.date.fromisoformat(value)
            cell = days.cell(r, c, value)
            if isinstance(value, dt.date):
                cell.number_format = "yyyy-mm-dd"
    book.save(path)


def _html_body() -> str:
    parts = [f"<h1>{html.escape(C.TITLE)}</h1>"]
    for sec in C.SECTIONS:
        parts.append(f"<h2>{html.escape(sec['heading'])}</h2>")
        parts += [f"<p>{html.escape(t)}</p>" for t in sec["paragraphs"]]
        if "bullets" in sec:
            parts.append("<ul>" + "".join(f"<li>{html.escape(t)}</li>" for t in sec["bullets"]) + "</ul>")
        if "numbered" in sec:
            parts.append("<ol>" + "".join(f"<li>{html.escape(t)}</li>" for t in sec["numbered"]) + "</ol>")
        if "table" in sec:
            head, *rows = sec["table"]
            parts.append("<table><thead><tr>" + "".join(f"<th>{html.escape(t)}</th>" for t in head)
                         + "</tr></thead><tbody>"
                         + "".join("<tr>" + "".join(f"<td>{html.escape(t)}</td>" for t in row) + "</tr>"
                                   for row in rows) + "</tbody></table>")
    return "\n".join(parts)


def make_html(path: Path) -> None:
    noise = C.HTML_NOISE
    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>{html.escape(C.TITLE)}</title>
<script>window.dataLayer = [];</script><style>body{{font-family:sans-serif}}</style></head>
<body>
<header><nav><a href="/">{noise[0]}</a> | <a href="/login">{noise[1]}</a></nav></header>
<main><article>
{_html_body()}
</article>
<aside class="ad"><p>広告：在宅ワークに最適なチェア、今だけ30%オフ</p></aside>
</main>
<footer><a href="/cookies">{noise[2]}</a><p>{noise[3]}</p></footer>
</body></html>
"""
    path.write_bytes(page.encode("utf-8"))


def make_csv(path: Path, encoding: str) -> None:
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\r\n").writerows(C.CSV_ROWS)
    path.write_bytes(buffer.getvalue().encode(encoding))


def make_epub(path: Path) -> None:
    chapters = []
    for i, ch in enumerate(C.EPUB_CHAPTERS, start=1):
        body = "".join(f"<p>{html.escape(t)}</p>" for t in ch["paragraphs"])
        chapters.append((f"ch{i}.xhtml", f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja"><head><title>{html.escape(ch['title'])}</title></head>
<body><h1>{html.escape(ch['title'])}</h1>{body}</body></html>"""))
    manifest = "".join(f'<item id="c{i}" href="{name}" media-type="application/xhtml+xml"/>'
                       for i, (name, _) in enumerate(chapters, start=1))
    spine = "".join(f'<itemref idref="c{i}"/>' for i in range(1, len(chapters) + 1))
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">urn:uuid:00000000-0000-4000-8000-000000000001</dc:identifier>
<dc:title>在宅の春（試料）</dc:title><dc:creator>試料の作者</dc:creator><dc:language>ja</dc:language>
<meta property="dcterms:modified">2026-11-15T00:00:00Z</meta></metadata>
<manifest>{manifest}<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest>
<spine>{spine}</spine></package>"""
    nav = """<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目次</title></head><body><nav epub:type="toc"><ol><li><a href="ch1.xhtml">第1章</a></li><li><a href="ch2.xhtml">第2章</a></li></ol></nav></body></html>"""
    container = """<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        for name, text in chapters:
            z.writestr(f"OEBPS/{name}", text, compress_type=zipfile.ZIP_DEFLATED)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    make_docx(ROOT / "handbook.docx", two_columns=False)
    make_docx(ROOT / "handbook-2col.docx", two_columns=True)
    make_pptx(ROOT / "slides.pptx")
    make_xlsx(ROOT / "expenses.xlsx")
    make_html(ROOT / "article.html")
    make_csv(ROOT / "staff-utf8.csv", "utf-8")
    make_csv(ROOT / "staff-cp932.csv", "cp932")
    (ROOT / "policy.json").write_bytes(json.dumps(C.JSON_DATA, ensure_ascii=False, indent=2).encode("utf-8"))
    (ROOT / "policy.xml").write_bytes(C.XML_TEXT.encode("utf-8"))
    make_epub(ROOT / "story.epub")
    print("作った試料:", ", ".join(sorted(p.name for p in ROOT.iterdir())))


if __name__ == "__main__":
    main()
