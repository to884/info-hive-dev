import hashlib
from contextlib import closing
import io
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path("scripts").resolve()))
from region_audit_v6 import normalize
from pdfminer.high_level import extract_text
from pypdfium2 import PdfDocument

def make_pdf(codepoint):
    text = b"BT /F1 36 Tf 24 80 Td <95> Tj ET"
    cmap = (
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n"
        "1 begincodespacerange\n<00> <FF>\nendcodespacerange\n"
        f"1 beginbfchar\n<95> <{codepoint:04X}>\nendbfchar\n"
        "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend"
    ).encode("ascii")
    stream=lambda data:b"<< /Length "+str(len(data)).encode()+b" >>\nstream\n"+data+b"\nendstream"
    objects=(
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 144 144] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding /ToUnicode 6 0 R >>",
        stream(text),stream(cmap),
    )
    out=bytearray(b"%PDF-1.4\n")
    offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode()+obj+b"\nendobj\n")
    xref=len(out)
    out.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for position in offsets[1:]:
        out.extend(f"{position:010} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)

records=[]
for codepoint in (0x2022,0x30fb):
    data=make_pdf(codepoint)
    text=normalize(extract_text(io.BytesIO(data)))
    assert text == chr(codepoint)
    with PdfDocument(data) as doc, closing(doc[0]) as page:
        rasters={}
        for dpi in (150,450):
            with closing(page.render(scale=dpi/72)) as bitmap:
                image=bitmap.to_pil().convert("RGB")
                assert min(image.getextrema()[0])<255
                rasters[str(dpi)]={"size":image.size,"rgb_sha256":hashlib.sha256(image.tobytes()).hexdigest()}
    records.append({"normalized_code_point":f"U+{ord(text):04X}","pdf_sha256":hashlib.sha256(data).hexdigest(),"rasters":rasters})
assert records[0]["rasters"] == records[1]["rasters"]
print(json.dumps({"same_pixels":True,"different_normalized_labels":True,"pdfs":records}))
