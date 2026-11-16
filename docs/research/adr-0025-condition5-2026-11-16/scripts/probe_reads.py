"""2 つ目の読みを試す（選ぶ資料だけ）。rag_ocr.py と同じ設定で NDLOCR-Lite を動かし、行ごとに、製品の読みに加えて、
3 つの認識器それぞれの読みと、画像を少し変えた読みを記録する。

使い方（rag の OCR の環境の python で動かす）:
    <rag-ocr の python> -X utf8 scripts/probe_reads.py corpus/probe/png/*.png
corpus/probe/reads/<名前>.json に書く。あれば飛ばす。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
from PIL import Image

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))

import ocr  # noqa: E402  NDLOCR-Lite
from rag_ocr_confidence import ConfidentRecognizer, line_records  # noqa: E402

OUT = BENCH / "corpus" / "probe" / "reads"


def summary(text) -> dict:
    values = list(getattr(text, "chars", [])) + list(getattr(text, "eos", []))
    return {"text": str(text), "min": round(min(values), 4) if values else (0.0 if not str(text) else None)}


def main() -> None:
    package = Path(ocr.__file__).resolve().parent
    args = SimpleNamespace(device="cpu", det_weights=str(package / "model/deim-s-1024x1024.onnx"),
                           det_classes=str(package / "config/ndl.yaml"), det_score_threshold=.2,
                           det_conf_threshold=.25, det_iou_threshold=.2,
                           rec_weights=str(package / "model/parseq-ndl-24x768-100-tiny-153epoch-tegaki3-r8data-202604.onnx"),
                           rec_weights30=str(package / "model/parseq-ndl-24x256-30-tiny-189epoch-tegaki3-r8data-202604.onnx"),
                           rec_weights50=str(package / "model/parseq-ndl-24x384-50-tiny-300epoch-tegaki3-r8data-202604.onnx"),
                           rec_classes=str(package / "config/NDLmoji.yaml"), enable_tcy=False)
    detector = ocr.get_detector(args)
    raw = [ocr.get_recognizer(args, args.rec_weights30), ocr.get_recognizer(args, args.rec_weights50), ocr.get_recognizer(args)]
    r30, r50, r100 = [ConfidentRecognizer(model) for model in raw]
    extra: dict[int, dict] = {}
    original = ocr.process_cascade

    def cascade(alllineobj, recognizer30, recognizer50, recognizer100, is_cascade=True):
        results = original(alllineobj, recognizer30, recognizer50, recognizer100, is_cascade=is_cascade)
        extra.clear()
        for line in alllineobj:
            image = line.npimg
            padded = cv2.copyMakeBorder(image, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            blurred = cv2.GaussianBlur(image, (0, 0), 0.7)
            extra[line.idx] = {"r30": summary(r30.read(image)), "r50": summary(r50.read(image)),
                               "r100": summary(r100.read(image)), "pad100": summary(r100.read(padded)),
                               "blur100": summary(r100.read(blurred)), "pred_char_cnt": line.pred_char_cnt}
        return results

    ocr.process_cascade = cascade
    OUT.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        path = Path(name)
        target = OUT / (path.stem + ".json")
        if target.exists():
            continue
        with Image.open(path) as original_image:
            pixels = np.array(original_image.convert("RGB"))
        result = ocr._run_ocr_on_image_array(detector, r30, r50, r100, path.name, pixels, str(path.parent), save_viz=False)
        records = line_records(result["json_lines"])
        for index, record in enumerate(records):
            record["reads"] = extra.get(index)
        target.write_bytes(json.dumps({"page": path.stem, "lines": records}, ensure_ascii=False).encode("utf-8"))
        print(path.stem, len(records), "行", flush=True)


if __name__ == "__main__":
    main()
