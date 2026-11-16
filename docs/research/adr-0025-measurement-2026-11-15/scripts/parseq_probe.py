"""NDLOCR-Lite の認識器（PARSeq）の ONNX の出力が、確率（位置ごとの和が 1）か、ロジットかを確かめる。

使い方: rag の OCR の環境（uv の environments-v2/rag-ocr-*）の Python で、`python -I parseq_probe.py <結果の JSON>`
合成の行の画像（MS ゴシックで描いた日本語の行）を、30、50、100 文字用の 3 つの認識器に通す。
出力の形、値の範囲、位置ごとの和、softmax をかけたときの選んだ文字の確率、読んだ文字の数を JSON に書く。
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ocr

package = Path(ocr.__file__).resolve().parent
args = SimpleNamespace(device="cpu", rec_weights=str(package / "model/parseq-ndl-24x768-100-tiny-153epoch-tegaki3-r8data-202604.onnx"),
                       rec_classes=str(package / "config/NDLmoji.yaml"))
models = {
    "rec30": str(package / "model/parseq-ndl-24x256-30-tiny-189epoch-tegaki3-r8data-202604.onnx"),
    "rec50": str(package / "model/parseq-ndl-24x384-50-tiny-300epoch-tegaki3-r8data-202604.onnx"),
    "rec100": args.rec_weights,
}
font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 40)
found = {"lines": ["防衛白書の本文です", "これは試験の行です。"], "models": {}}
for name, weights in models.items():
    rec = ocr.get_recognizer(args, weights)
    rows_out = []
    for text in found["lines"]:
        img = Image.new("RGB", (40 * len(text) + 20, 56), "white")
        ImageDraw.Draw(img).text((10, 8), text, font=font, fill="black")
        arr = np.array(img)
        out = rec.session.run(rec.output_names, {rec.input_names[0]: rec.preprocess(arr)})[0]
        rows = out[0]
        sums = rows.sum(axis=1)
        e = np.exp(rows - rows.max(axis=1, keepdims=True))
        p = e / e.sum(axis=1, keepdims=True)
        idx = rows.argmax(axis=1)
        stop = np.where(idx == 0)[0]
        end = int(stop[0]) if stop.size else len(idx)
        read = rec.read(arr)
        rows_out.append({"shape": list(out.shape), "min": round(float(rows.min()), 3), "max": round(float(rows.max()), 3),
                         "row_sum_min": round(float(sums.min()), 3), "row_sum_max": round(float(sums.max()), 3),
                         "read_chars": len(read), "read_equals_drawn": read == text,
                         "softmax_max_per_char": [round(float(v), 4) for v in p.max(axis=1)[:end]]})
    found["models"][name] = rows_out
Path(sys.argv[1]).write_bytes(json.dumps(found, ensure_ascii=False, indent=1).encode("utf-8"))
print(json.dumps({k: [(r["shape"], r["row_sum_min"], r["read_equals_drawn"]) for r in v] for k, v in found["models"].items()}))
