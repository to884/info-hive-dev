"""画素が同じ点線に異なる文字の対応を持たせ、現行の正規化で照合する。"""

from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import sys

from pdfminer.high_level import extract_text
from pypdfium2 import PdfDocument

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
sys.path.insert(0, str(BENCH / "scripts"))
from region_audit_v6 import normalize


def stream(data):
    return b"<< /Length " + str(len(data)).encode("ascii") + b" >>\nstream\n" + data + b"\nendstream"


def pdf_with_mapping(destination):
    marking = b"BT /F1 36 Tf 24 80 Td <85> Tj ET"
    # 同じWinAnsiの三点リーダー字形を描き、ToUnicodeだけ変える。
    cmap = ("/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
            "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n"
            "1 begincodespacerange\n<00> <FF>\nendcodespacerange\n"
            f"1 beginbfchar\n<85> <{destination}>\nendbfchar\n"
            "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend").encode("ascii")
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 144 144] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding /ToUnicode 6 0 R >>",
        stream(marking), stream(cmap),
    )
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets:
        pdf.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


def proof(encoded, label):
    pdf = pdf_with_mapping(encoded)
    text = normalize(extract_text(io.BytesIO(pdf)))
    if text != normalize(label):
        raise ValueError("文字層の対応を再現できない")
    pixels = {}
    with closing(PdfDocument(pdf)) as doc, closing(doc[0]) as page:
        for dpi in (150, 450):
            with closing(page.render(scale=dpi / 72)) as bitmap:
                image = bitmap.to_pil().convert("RGB")
                if min(image.getextrema()[0]) == 255:
                    raise ValueError("点線が描かれていない")
                pixels[str(dpi)] = hashlib.sha256(image.tobytes()).hexdigest()
    return {"pdf_sha256": hashlib.sha256(pdf).hexdigest(),
            "normalized_codepoints": [f"U+{ord(c):04X}" for c in text], "image_sha256": pixels}


def main():
    rows = [proof("2026", "…"), proof("30FB30FB30FB", "・・・")]
    if rows[0]["image_sha256"] != rows[1]["image_sha256"] or rows[0]["normalized_codepoints"] == rows[1]["normalized_codepoints"]:
        raise ValueError("画素の一致と正解の差が再現しない")
    output = HERE / "glyph-ambiguity.json"
    with output.open("x", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
    print(json.dumps(rows), flush=True)


if __name__ == "__main__":
    main()
