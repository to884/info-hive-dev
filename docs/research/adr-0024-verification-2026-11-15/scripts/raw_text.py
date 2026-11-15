# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2"]
# ///
"""判定で本文を出さないページも含めて、rag の inspect_page が返す文字の層の本文を outputs/<試料>__pdfium-raw.txt に書く。

使い方: uv run --script raw_text.py <試料の名前>...
判定で隠したページの中身を確かめるためのもので、比べる方式には入れない。
"""

from __future__ import annotations

import sys
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH.parents[2] / "info-hive-rag" / "scripts"))


def main() -> None:
    import pypdfium2 as pdfium
    from rag_pdf import inspect_page
    for name in sys.argv[1:]:
        path = BENCH / "corpus" / name
        chunks = []
        with pdfium.PdfDocument(path.read_bytes()) as document:
            for number in range(len(document)):
                with closing(document[number]) as page:
                    text, quality = inspect_page(page)
                chunks.append(f"## p. {number + 1}（{quality['kind']}）\n\n{text}")
        (BENCH / "outputs" / f"{path.stem}__pdfium-raw.txt").write_bytes("\n\n".join(chunks).encode("utf-8"))
        print(name, "ok")


if __name__ == "__main__":
    main()
