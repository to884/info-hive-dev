"""条件 5 の 3 回目の確かめる資料の合成の原稿（12 本）を作る（測り方は ../../adr-0025-condition5-v3-2026-11-17.md）。

使い方: uv run --python 3.12 --with reportlab==4.4.4 --with pypdfium2==5.15.2 --with pillow --with numpy \
    python -X utf8 scripts/make_synthetic_v3.py

原稿は、docs/adr/ のファイル名の順で 26〜29 個目の ADR と、docs/research/ の Markdown（名前が adr-0025-condition5 で
始まらないもの）をファイル名の順に並べ、Markdown の記号を除いて 1,520 文字以上ある先頭の 8 本。作り方は make_synthetic.py
と同じ。corpus/synthetic/n00〜n11.pdf と .truth.json（side は evaluation3）に書く。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_synthetic as base  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402


def main() -> None:
    for name, path in base.FONTS.values():
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
    cmaps = {font: set(pdfmetrics.getFont(base.FONTS[font][0]).face.charToGlyph) for font in base.FONTS}
    adrs = sorted((base.ROOT / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md"))[25:29]
    research = [p for p in sorted((base.ROOT / "docs" / "research").glob("*.md"))
                if not p.name.startswith("adr-0025-condition5")]
    sources = list(adrs)
    for path in research:
        if len(sources) == 12:
            break
        if len(base.manuscript_text(path, cmaps["gothic"])) >= base.CHARS * base.LINES:
            sources.append(path)
    assert len(sources) == 12, len(sources)
    base.OUT.mkdir(parents=True, exist_ok=True)
    for i, path in enumerate(sources):
        font = "gothic" if i % 4 in (0, 1) else "mincho"
        seed = 1000 + i
        name = f"n{i:02d}"
        text = base.manuscript_text(path, cmaps[font])
        vector, lines = base.draw_vector(text, font)
        images = [base.degrade(vector, variant, seed) for variant in base.VARIANTS]
        pdf = base.image_pdf(images)
        (base.OUT / f"{name}.pdf").write_bytes(pdf)
        truth = {"name": name, "source": path.relative_to(base.ROOT).as_posix(), "font": font, "side": "evaluation3",
                 "seed": seed, "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
                 "pages": [{"page": n, "variant": variant, "kind": "scan",
                            "lines": [{"id": k, "text": line["text"], "box": base.pixel_box(line["pt"], variant)}
                                      for k, line in enumerate(lines)]}
                           for n, variant in enumerate(base.VARIANTS, start=1)]}
        (base.OUT / f"{name}.truth.json").write_bytes(json.dumps(truth, ensure_ascii=False, indent=1).encode("utf-8"))
        print(name, font, path.relative_to(base.ROOT).as_posix(), len(text), "文字", len(lines), "行")


if __name__ == "__main__":
    main()
