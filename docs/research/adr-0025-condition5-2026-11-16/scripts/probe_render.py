"""2 つ目の読みを試すために、選ぶ資料のページを、製品と同じ描き方（pypdfium2、150 dpi）で画像にする。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/probe_render.py [dpi]（既定は 150。ほかの dpi は png<dpi>/ に書く）
corpus/probe/png/<tag>-p<ページ>.png に書く。選ぶ資料（side が tuning）だけを描く。
"""

from __future__ import annotations

import hashlib
import json
import sys
from contextlib import closing
from pathlib import Path

import pypdfium2 as pdfium

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
DPI = int(sys.argv[1]) if len(sys.argv) > 1 else 150
OUT = CORPUS / "probe" / ("png" if DPI == 150 else f"png{DPI}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    manifest = {}
    for path in sorted((CORPUS / "synthetic").glob("*.truth.json")) + sorted((CORPUS / "public").glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] != "tuning":
            continue
        pdf = path.with_name(truth["name"] + ".pdf") if path.parent.name == "synthetic" else CORPUS / truth["file"]
        data = pdf.read_bytes()
        if hashlib.sha256(data).hexdigest() != truth["pdf_sha256"]:
            raise SystemExit(f"PDF が正解と違う: {pdf.name}")
        with pdfium.PdfDocument(data) as document:
            for page in truth["pages"]:
                target = OUT / f"{truth['name']}-p{page['page']:04d}.png"
                with closing(document[page["page"] - 1]) as p:
                    bitmap = p.render(scale=DPI / 72)
                    bitmap.to_pil().save(target)
                    bitmap.close()
                manifest[target.name] = {"pdf_sha256": truth["pdf_sha256"], "page": page["page"], "dpi": DPI,
                                         "png_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
                count += 1
    (OUT / "manifest.json").write_bytes(json.dumps(manifest, ensure_ascii=False, indent=1).encode("utf-8"))
    print(count, "ページ")


if __name__ == "__main__":
    main()
