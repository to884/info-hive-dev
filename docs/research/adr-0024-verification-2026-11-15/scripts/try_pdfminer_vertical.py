# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdfminer.six==20260107"]
# ///
"""pdfminer の縦書きの検出（LAParams(detect_vertical=True)）で、官報と白書の本文がどう変わるかを試す。

使い方: uv run --script try_pdfminer_vertical.py
outputs/<試料>__pdfminer-vertical.txt に書く。比べる方式には入れていない（書き直しの案の下調べ）。
"""

from __future__ import annotations

from pathlib import Path

from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

BENCH = Path(__file__).resolve().parent.parent


def main() -> None:
    for name in ["kanpo-p1", "kanpo-p2", "kanpo-p3", "kanpo-p4", "whitepaper-point", "whitepaper-summary", "bert"]:
        text = extract_text(str(BENCH / "corpus" / f"{name}.pdf"), laparams=LAParams(detect_vertical=True))
        (BENCH / "outputs" / f"{name}__pdfminer-vertical.txt").write_bytes(text.encode("utf-8"))
        lines = [line for line in text.splitlines() if line.strip()]
        one_char = sum(len(line.strip()) == 1 for line in lines)
        print(f"{name}: {len(lines)} 行、1 文字だけの行 {one_char}")


if __name__ == "__main__":
    main()
