# PDFium が先頭の何バイトまでの前置きを許すかを、作った PDF で確かめる。
import io

import pypdfium2 as pdfium
from reportlab.pdfgen import canvas

buffer = io.BytesIO()
pdf = canvas.Canvas(buffer)
pdf.drawString(40, 700, "Leading bytes")
pdf.showPage()
pdf.save()
body = buffer.getvalue()

for prefix in [b"\n", b"\r\n", b" \t\n", b"\x00", b"garbage\n", b" " * 1023, b" " * 1024, b" " * 1025, b"x" * 1024]:
    try:
        with pdfium.PdfDocument(prefix + body) as doc:
            text = doc[0].get_textpage().get_text_range().strip()
            result = f"ok pages={len(doc)} text={text!r}"
    except Exception as error:  # noqa: BLE001
        result = f"error {type(error).__name__}: {error}"
    print(len(prefix), repr(prefix[:10]), result)
