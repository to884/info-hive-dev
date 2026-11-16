"""製品の OCR（corpus/ocr2/）の横書きの行を、RapidOCR（PaddleOCR の日本語の認識モデル）で読み直す（試し）。

使い方:
    uv run --with rapidocr==3.10.0 --with onnxruntime==1.31.1 --with pypdfium2==5.15.2 \
        python -X utf8 scripts/probe_rapid.py tuning evaluation

ページを製品と同じく 150 dpi で描き、ocr2 の行の箱で切り出して、認識だけ（検出なし）で読む。縦書きの行は読まない。
結果は corpus/probe/rapid/<tag>-p<ページ>.json に、ocr2 の結果の SHA-256 と一緒に書く（同じなら飛ばす）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
OUT = CORPUS / "probe" / "rapid"


def pages(sides: list[str]):
    for path in sorted((CORPUS / "synthetic").glob("*.truth.json")) + sorted((CORPUS / "public").glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] not in sides:
            continue
        pdf = path.with_name(truth["name"] + ".pdf") if path.parent.name == "synthetic" else CORPUS / truth["file"]
        for page in truth["pages"]:
            yield truth, pdf, page["page"]


def main() -> None:
    from rapidocr import LangRec, RapidOCR

    engine = RapidOCR(params={"Rec.lang_type": LangRec.JAPAN})
    OUT.mkdir(parents=True, exist_ok=True)
    documents = {}
    for truth, pdf, number in pages(sys.argv[1:]):
        key = f"{truth['name']}-p{number:04d}"
        raw = (CORPUS / "ocr2" / f"{key}.json").read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        target = OUT / f"{key}.json"
        if target.exists() and json.loads(target.read_bytes().decode("utf-8"))["ocr2_sha256"] == sha:
            continue
        ocr = json.loads(raw.decode("utf-8"))
        if pdf not in documents:
            documents[pdf] = pdfium.PdfDocument(pdf.read_bytes())
        page = documents[pdf][number - 1]
        bitmap = page.render(scale=150 / 72)
        image = np.array(bitmap.to_pil().convert("RGB"))
        bitmap.close()
        page.close()
        reads = []
        for line in ocr["lines"]:
            x, y, w, h = (int(round(v)) for v in line["box"])
            if line.get("vertical") or w <= 0 or h <= 0:
                reads.append(None)
                continue
            crop = image[max(0, y):y + h, max(0, x):x + w]
            result = engine(crop, use_det=False, use_cls=False, use_rec=True)
            texts = list(result.txts or [])
            scores = [float(s) for s in (result.scores or [])]
            reads.append({"text": "".join(texts), "score": min(scores) if scores else None})
        target.write_bytes(json.dumps({"key": key, "ocr2_sha256": sha, "reads": reads}, ensure_ascii=False).encode("utf-8"))
        print(key, len(reads), flush=True)


if __name__ == "__main__":
    main()
