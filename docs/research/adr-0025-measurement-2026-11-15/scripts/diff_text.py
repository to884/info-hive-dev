# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdfminer.six==20260107"]
# ///
"""measure_time.py の same_text で一致しなかったページを探し、違い方を数える。

使い方: uv run --script diff_text.py <PDF> [結果の名前に付ける接尾辞]
本文そのものは出さない。ページの番号、文字数、違う範囲、並べ替えだけの違いかを出し、
ページごとの本文の SHA-256 を results/text-<PDF の名前><接尾辞>.json に書く。別のプロセスで走らせた結果の
SHA-256 を比べると、pdfminer が毎回同じ本文を返すかがわかる。
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path


def pass_pages(path: Path) -> list[str]:
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    texts, output, manager = [], io.StringIO(), PDFResourceManager()
    with path.open("rb") as handle, TextConverter(manager, output, codec="utf-8",
                                                  laparams=LAParams(detect_vertical=True)) as device:
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(handle):
            interpreter.process_page(page)
            texts.append(output.getvalue().rstrip(chr(12)))
            output.seek(0)
            output.truncate(0)
    return texts


def main() -> None:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    path = Path(sys.argv[1]).resolve()
    whole_text = extract_text(str(path), laparams=LAParams(detect_vertical=True))
    whole = whole_text.split(chr(12))
    passed = pass_pages(path)
    rows = []
    for i, (a, b) in enumerate(zip(whole, passed)):
        if a == b:
            continue
        pos = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        same_without_space = "".join(a.split()) == "".join(b.split())
        end = next((k for k in range(min(len(a), len(b))) if a[-1 - k] != b[-1 - k]), 0)
        rows.append({"page": i + 1, "whole_chars": len(a), "pass_chars": len(b), "first_diff_at": pos,
                     "differing_span_chars": len(a) - end - pos,
                     "same_without_whitespace": same_without_space,
                     "same_characters_reordered": sorted(a) == sorted(b),
                     "same_lines_reordered": sorted(a.splitlines()) == sorted(b.splitlines()),
                     "formfeeds_in_pass_page": b.count(chr(12))})
    found = {"pages_whole_split": len(whole), "pages_pass": len(passed),
             "formfeeds_in_whole": whole_text.count(chr(12)), "differing": rows,
             # 別のプロセスで走らせた結果と比べて、毎回同じ本文になるかを見るためのページごとの SHA-256
             "pass_sha256": [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in passed]}
    suffix = sys.argv[2] if len(sys.argv) > 2 else ""
    out = Path(__file__).resolve().parent.parent / "results" / f"text-{path.stem}{suffix}.json"
    out.write_bytes(json.dumps(found, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: v for k, v in found.items() if k != "pass_sha256"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
