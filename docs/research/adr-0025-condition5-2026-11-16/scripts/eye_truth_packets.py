"""公開の PDF で、文字の層から正解を決められない OCR の行を集め、目で書き起こすための画像を作る。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/eye_truth_packets.py <side>
対象は、score.page_records で "pessimistic"（正解とつながらない、1 対 1 でない対応の誤り、除いた正解の行と同じまとまり）か
"excluded"（除いた正解の行と直接つながる）になる OCR の行である。行ごとに、ページの画像を前後に余白を付けて切り出し、
対象の行を赤い枠で囲んだ画像を corpus/public/eyetruth/<side>/<tag>-p<ページ>-l<行>.png に書く。
一覧を corpus/public/eyetruth/<side>/index.json に書く（OCR の本文は書かない。書き起こす人に見せないため）。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from score import CORPUS, load_truths, page_records  # noqa: E402

MARGIN = 40
# 行を取る OCR の結果の置き場所。2 回目の測り方では、採点する ocr2 から作る
SOURCE = os.environ.get("EYE_TRUTH_OCR", "ocr2")


def main() -> None:
    side = sys.argv[1]
    out = CORPUS / "public" / "eyetruth" / side
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for truth in load_truths():
        if truth["side"] != side or truth["stratum"] != "public":
            continue
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            ocr = json.loads((CORPUS / SOURCE / f"{key}.json").read_bytes().decode("utf-8"))
            if ocr["pdf_sha256"] != truth["pdf_sha256"]:
                raise SystemExit(f"OCR の結果の PDF が正解と違う: {key}")
            lines = [{**line, "box": [line["box"][0], line["box"][1], line["box"][0] + line["box"][2],
                                      line["box"][1] + line["box"][3]]} for line in ocr["lines"]]
            records, _ = page_records(page["lines"], lines, "public")
            targets = sorted(r["line_index"] for r in records if r["rule"] in ("pessimistic", "excluded"))
            if not targets:
                continue
            image = Image.open(CORPUS / "public" / "eyecheck" / f"{key}.png").convert("RGB")
            for j in targets:
                x0, y0, x1, y1 = lines[j]["box"]
                crop_box = (max(0, int(x0) - MARGIN), max(0, int(y0) - MARGIN),
                            min(image.width, int(x1) + MARGIN), min(image.height, int(y1) + MARGIN))
                crop = image.crop(crop_box)
                draw = ImageDraw.Draw(crop)
                draw.rectangle([x0 - crop_box[0] - 2, y0 - crop_box[1] - 2, x1 - crop_box[0] + 2, y1 - crop_box[1] + 2],
                               outline=(255, 0, 0), width=2)
                if crop.width < 400 and crop.height < 400:
                    crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
                name = f"{key}-l{j:04d}.png"
                crop.save(out / name)
                index.append({"file": name, "key": key, "line_index": j, "vertical": bool(lines[j].get("vertical")),
                              "source": SOURCE, "box": ocr["lines"][j]["box"],
                              "ocr_text_sha256": hashlib.sha256(ocr["lines"][j]["text"].encode("utf-8")).hexdigest()})
    (out / "index.json").write_bytes(json.dumps(index, ensure_ascii=False, indent=1).encode("utf-8"))
    print(len(index), "行")


if __name__ == "__main__":
    main()
