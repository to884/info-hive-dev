"""PARSeq の ONNX の出力が確率（行の和が 1）か、ロジットかを、合成の行の画像で確かめる。"""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ocr

package = Path(ocr.__file__).resolve().parent
args = SimpleNamespace(device="cpu", rec_weights=str(package / "model/parseq-ndl-24x768-100-tiny-153epoch-tegaki3-r8data-202604.onnx"),
                       rec_classes=str(package / "config/NDLmoji.yaml"))
rec = ocr.get_recognizer(args)
font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 40)
for text in ["防衛白書の本文です", "これは試験の行です。"]:
    img = Image.new("RGB", (40 * len(text) + 20, 56), "white")
    ImageDraw.Draw(img).text((10, 8), text, font=font, fill="black")
    arr = np.array(img)
    out = rec.session.run(rec.output_names, {rec.input_names[0]: rec.preprocess(arr)})[0]
    rows = out[0]
    sums = rows.sum(axis=1)
    print("shape", out.shape, "min", float(rows.min()), "max", float(rows.max()),
          "row sums", float(sums.min()), float(sums.max()))
    e = np.exp(rows - rows.max(axis=1, keepdims=True))
    p = e / e.sum(axis=1, keepdims=True)
    idx = rows.argmax(axis=1)
    stop = np.where(idx == 0)[0]
    end = stop[0] if stop.size else len(idx)
    print("read:", rec.read(arr), "| softmax max per char:", np.round(p.max(axis=1)[:end], 3).tolist())
