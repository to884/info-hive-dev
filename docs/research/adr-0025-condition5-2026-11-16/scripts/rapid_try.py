"""RapidOCR（PaddleOCR の日本語の認識モデル）で、行の画像を 1 つ読めるかを確かめる（試し）。

使い方: uv run --with rapidocr==3.10.0 --with onnxruntime==1.31.1 python -X utf8 scripts/rapid_try.py <ページの画像> <x> <y> <w> <h>
"""

from __future__ import annotations

import sys

import numpy as np
from PIL import Image


def main() -> None:
    from rapidocr import LangRec, RapidOCR

    engine = RapidOCR(params={"Rec.lang_type": LangRec.JAPAN})
    path, x, y, w, h = sys.argv[1], *map(int, sys.argv[2:6])
    crop = np.array(Image.open(path).convert("RGB").crop((x, y, x + w, y + h)))
    result = engine(crop, use_det=False, use_cls=False, use_rec=True)
    print(repr(result.txts), result.scores)


if __name__ == "__main__":
    main()
