# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdf_oxide==0.3.78", "pdfplumber==0.11.10"]
# ///
"""pdf_oxide と pdfplumber で公開の試料を取り出し、時間を測る（書き直しの案のための比較）。

使い方: uv run --script try_more.py
- pdfoxide:   pdf_oxide 0.3.78 の PdfDocument.to_markdown(ページ)。縦書きの並べ替えと表の検出を含む既定の設定
- pdfplumber: pdfplumber 0.11.10 の page.extract_text()。既定の設定（縦書きの方向の指定はしない）
outputs/<試料>__<方式>.txt（ページを改ページの文字 U+000C でつないだもの）と outputs/more-times.json を書く。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
NAMES = ["whitepaper-point", "whitepaper-summary", "kanpo-p1", "kanpo-p2", "kanpo-p3", "kanpo-p4", "bert"]


def pdfoxide(path: Path) -> list[str]:
    import pdf_oxide
    doc = pdf_oxide.PdfDocument(str(path))
    return [doc.to_markdown(i) for i in range(doc.page_count())]


def pdfplumber_pages(path: Path) -> list[str]:
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def main() -> None:
    times = {}
    for method, fn in (("pdfoxide", pdfoxide), ("pdfplumber", pdfplumber_pages)):
        for name in NAMES:
            t0 = time.perf_counter()
            pages = fn(BENCH / "corpus" / f"{name}.pdf")
            times[f"{name}__{method}"] = {"seconds": round(time.perf_counter() - t0, 3), "pages": len(pages)}
            (BENCH / "outputs" / f"{name}__{method}.txt").write_bytes(chr(12).join(pages).encode("utf-8"))
            print(method, name, times[f"{name}__{method}"], flush=True)
    (BENCH / "outputs" / "more-times.json").write_bytes(json.dumps(times, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
