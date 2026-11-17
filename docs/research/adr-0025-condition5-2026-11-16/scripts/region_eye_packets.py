"""4 回目: 領域の正解で決められない行のうち、目で作った正解がまだない行の画像を作る（../../adr-0025-condition5-v4-2026-11-17.md の 1 の 5）。

使い方: python -X utf8 scripts/region_eye_packets.py <side>
corpus/public/region/ の結果と、前の回の目で作った正解（corpus/public/eyetruth/<side>/）を照らし、まだない行を
corpus/public/eyetruth/<side>-region/ に、eye_truth_packets.py と同じ形（赤い枠、index.json。OCR の本文は書かない）で書く。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eye_truth_packets import MARGIN  # noqa: E402
from score import CORPUS, load_truths  # noqa: E402


def load(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def main() -> None:
    side = sys.argv[1]
    old = CORPUS / "public" / "eyetruth" / side
    asked = {(x["key"], x["line_index"]) for x in load(old / "index.json")} if (old / "index.json").exists() else set()
    out = CORPUS / "public" / "eyetruth" / f"{side}-region"
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for truth in load_truths():
        if truth["side"] != side or truth["stratum"] != "public":
            continue
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            region = load(CORPUS / "public" / "region" / f"{key}.json")
            ocr = load(CORPUS / "ocr3" / f"{key}.json")
            targets = [r["line_index"] for r in region["lines"]
                       if "undecided" in r and (key, r["line_index"]) not in asked]
            if not targets:
                continue
            image = Image.open(CORPUS / "public" / "eyecheck" / f"{key}.png").convert("RGB")
            for j in targets:
                line = ocr["lines"][j]
                x, y, w, h = line["box"]
                x0, y0, x1, y1 = x, y, x + w, y + h
                crop_box = (max(0, int(x0) - MARGIN), max(0, int(y0) - MARGIN),
                            min(image.width, int(x1) + MARGIN), min(image.height, int(y1) + MARGIN))
                crop = image.crop(crop_box)
                ImageDraw.Draw(crop).rectangle(
                    [x0 - crop_box[0] - 2, y0 - crop_box[1] - 2, x1 - crop_box[0] + 2, y1 - crop_box[1] + 2],
                    outline=(255, 0, 0), width=2)
                if crop.width < 400 and crop.height < 400:
                    crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
                name = f"{key}-l{j:04d}.png"
                crop.save(out / name)
                index.append({"file": name, "key": key, "line_index": j, "vertical": bool(line.get("vertical")),
                              "source": "ocr3", "box": line["box"],
                              "ocr_text_sha256": hashlib.sha256(line["text"].encode("utf-8")).hexdigest()})
    (out / "index.json").write_bytes(json.dumps(index, ensure_ascii=False, indent=1).encode("utf-8"))
    print(side, len(index), "行")


if __name__ == "__main__":
    main()
