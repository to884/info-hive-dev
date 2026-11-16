"""2 つ目の読みを試すために、選ぶ資料のページを、製品と同じ描き方（pypdfium2、150 dpi）で画像にする。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/probe_render.py
corpus/probe/png/<tag>-p<ページ>.png に書く。選ぶ資料（side が tuning）だけを描く。
"""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

import pypdfium2 as pdfium

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
OUT = CORPUS / "probe" / "png"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted((CORPUS / "synthetic").glob("*.truth.json")) + sorted((CORPUS / "public").glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] != "tuning":
            continue
        pdf = path.with_name(truth["name"] + ".pdf") if path.parent.name == "synthetic" else CORPUS / truth["file"]
        with pdfium.PdfDocument(pdf.read_bytes()) as document:
            for page in truth["pages"]:
                target = OUT / f"{truth['name']}-p{page['page']:04d}.png"
                with closing(document[page["page"] - 1]) as p:
                    bitmap = p.render(scale=150 / 72)
                    bitmap.to_pil().save(target)
                    bitmap.close()
                count += 1
    print(count, "ページ")


if __name__ == "__main__":
    main()
