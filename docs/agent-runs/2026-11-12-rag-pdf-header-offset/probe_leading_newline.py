# 実データの PDF を読み取りだけで調べる。原本は書き換えない。
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(r"D:\Users\toshiki\OneDrive - Mokumoku.Net\Documents\My eBooks\L4")
NAMES = [
    "Comprehensive-Formal-Verification-of-an-OS-Microkernel.pdf",
    "From-L3-to-seL4-What-Have-We-Learnt-in-20-Years-of-L4-Microkernels.pdf",
]
print("pypdfium2", pdfium.PYPDFIUM_INFO, pdfium.PDFIUM_INFO)
for name in NAMES:
    path = ROOT / name
    data = path.read_bytes()
    print(name, len(data), repr(data[:16]), "find:", data.find(b"%PDF-", 0, 1029))
    with pdfium.PdfDocument(data) as doc:
        n = len(doc)
        text = doc[0].get_textpage().get_text_range()[:120]
        print("  pages", n, "page1:", repr(text))
        # 先頭の改行を除いても同じに読めるか（抽出の結果が先頭のバイトに左右されないか）
    with pdfium.PdfDocument(data[data.find(b"%PDF-"):]) as doc2:
        same = all(doc2[i].get_textpage().get_text_range() == pdfium.PdfDocument(data)[i].get_textpage().get_text_range()
                   for i in range(min(3, len(doc2))))
        print("  stripped pages", len(doc2), "same text (first 3):", same)
