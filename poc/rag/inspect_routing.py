"""ページ分類を、資源の close を補う PoC アダプターで測る。製品コードは変更しない。"""
import collections
import contextlib
import json
import os
import sys
import time
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_pdf import inspect_page


class PageAdapter:
    def __init__(self, page):
        self.page = page
    def get_textpage(self):
        return contextlib.closing(self.page.get_textpage())
    def __getattr__(self, name):
        return getattr(self.page, name)


work = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
manifest = json.loads((work / "sample-manifest.json").read_text(encoding="utf-8"))
rows, representatives = [], {}
for index, entry in enumerate(manifest["files"]):
    data = (Path(manifest["root"]) / entry["relative_path"]).read_bytes()
    counts = collections.Counter()
    errors = []
    start = time.perf_counter()
    with pdfium.PdfDocument(data) as pdf:
        for number in range(len(pdf)):
            try:
                with contextlib.closing(pdf[number]) as page:
                    _, quality = inspect_page(PageAdapter(page))
                    counts[quality["kind"]] += 1
                    if quality["kind"] not in representatives and number > 10:
                        representatives[quality["kind"]] = {"sample": index, "page": number + 1, "quality": quality}
                        if quality["kind"] in {"scan", "vertical"}:
                            output = work / "real-ocr-input"
                            output.mkdir(exist_ok=True)
                            bitmap = page.render(scale=150 / 72)
                            bitmap.to_pil().save(output / f"{quality['kind']}-{index}-{number+1}.png")
                            bitmap.close()
            except Exception as error:
                errors.append({"page": number + 1, "error": str(error)})
    rows.append({"sample": index, "seconds": time.perf_counter() - start, "counts": dict(counts), "errors": errors})
    print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
result = {"files": rows, "representatives": representatives, "notes": ["製品の PdfTextPage に contextlib.closing を使うアダプターを挟んだ。製品コードそのままの成功ではない。", "自動分類であり、全ページの人手正解ラベルとの精度比較ではない。"]}
(ROOT / "docs/research/rag-poc-2026-11-04/routing-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
