# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["docling"]
# ///
"""Docling で試料を Markdown にし、時間を測る（書き直しの案の下調べ。比べる方式には入れていない）。

使い方: uv run --script try_docling.py
OCR は使わない（do_ocr=False）。版面の解析と表の構造の推定は、Docling の既定のモデルを使う。
outputs/<試料>__docling.md（全体）、outputs/<試料>__docling.txt（ページごとに export_to_markdown(page_no=N) で
書き出し、改ページの文字 U+000C でつないだもの。判定に使う）、outputs/docling-times.json を書く。
"""

from __future__ import annotations

import importlib.metadata as md
import json
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
NAMES = ["whitepaper-point", "whitepaper-summary", "kanpo-p1", "kanpo-p2", "kanpo-p3", "kanpo-p4", "bert"]


def main() -> None:
    start = time.perf_counter()
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
    times = {"import_and_init_s": round(time.perf_counter() - start, 2), "docling": md.version("docling")}
    for name in NAMES:
        t0 = time.perf_counter()
        result = converter.convert(str(BENCH / "corpus" / f"{name}.pdf"))
        markdown = result.document.export_to_markdown()
        times[name] = round(time.perf_counter() - t0, 2)
        (BENCH / "outputs" / f"{name}__docling.md").write_bytes(markdown.encode("utf-8"))
        pages = [result.document.export_to_markdown(page_no=n) for n in range(1, len(result.pages) + 1)]
        (BENCH / "outputs" / f"{name}__docling.txt").write_bytes(chr(12).join(pages).encode("utf-8"))
        print(name, times[name], "s", len(markdown), "chars", flush=True)
    (BENCH / "outputs" / "docling-times.json").write_bytes(json.dumps(times, ensure_ascii=False, indent=2).encode("utf-8"))
    print(times)


if __name__ == "__main__":
    main()
