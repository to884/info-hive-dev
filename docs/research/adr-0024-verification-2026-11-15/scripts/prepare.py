# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pypdfium2==5.15.2", "pillow==11.3.0", "reportlab==4.4.4", "matplotlib==3.10.7"]
# ///
"""試料の情報（ページ数、作成したソフト）を調べ、合成のスキャンの試料を作り、ページの画像を書き出す。

使い方: uv run --script prepare.py
- corpus/synth-scan.pdf: 官報の 1 ページ目を画像にしただけの PDF（文字の層なし）
- corpus/synth-scan-header.pdf: 同じ画像に、ヘッダーの文字（英数字 37 文字）だけを文字の層として重ねた PDF
- corpus/synth-outline.pdf: 日本語の文をアウトライン（パス）で描いた PDF（文字の層も画像もない）
- pages/<試料>-p<番号>.png: 判定と目視のためのページの画像（100 dpi）
- pages/<試料>-sheet.png: 目視のための一覧（6 ページずつ）
- info.json: 試料ごとのページ数、作成したソフト（Producer、Creator）
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
PAGES = BENCH / "pages"


def synth_scan() -> None:
    with pdfium.PdfDocument(CORPUS / "kanpo-p1.pdf") as doc:
        image = doc[0].render(scale=150 / 72).to_pil().convert("RGB")
    image.save(CORPUS / "synth-scan.pdf", "PDF", resolution=150)

    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    width, height = image.size[0] * 72 / 150, image.size[1] * 72 / 150
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    c = canvas.Canvas(str(CORPUS / "synth-scan-header.pdf"), pagesize=(width, height))
    c.drawImage(ImageReader(io.BytesIO(buffer.getvalue())), 0, 0, width, height)
    c.setFont("Helvetica", 8)
    c.drawString(36, height - 20, "Official Gazette No.1828 - 2026-11-13")
    c.showPage()
    c.save()


def synth_outline() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import PathPatch
    from matplotlib.textpath import TextPath

    font = FontProperties(fname=r"C:\Windows\Fonts\YuGothR.ttc")
    lines = ["この文はアウトラインで描いた。", "文字の層も画像もないので、", "抽出では何も取れない。"]
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 595)
    ax.set_ylim(0, 842)
    ax.axis("off")
    for i, line in enumerate(lines):
        path = TextPath((60, 760 - i * 40), line, size=24, prop=font)
        ax.add_patch(PathPatch(path, color="black", lw=0))
    fig.savefig(CORPUS / "synth-outline.pdf")
    plt.close(fig)


def render_pages(name: str) -> int:
    with pdfium.PdfDocument(CORPUS / name) as doc:
        images = []
        for i in range(len(doc)):
            image = doc[i].render(scale=100 / 72).to_pil().convert("RGB")
            image.save(PAGES / f"{Path(name).stem}-p{i + 1}.png")
            images.append(image)
    for start in range(0, len(images), 6):
        group = images[start:start + 6]
        thumb_w = 400
        thumbs = [im.resize((thumb_w, int(im.size[1] * thumb_w / im.size[0]))) for im in group]
        h = max(t.size[1] for t in thumbs)
        sheet = Image.new("RGB", (thumb_w * 3, h * ((len(thumbs) + 2) // 3)), "white")
        for k, t in enumerate(thumbs):
            sheet.paste(t, ((k % 3) * thumb_w, (k // 3) * h))
        sheet.save(PAGES / f"{Path(name).stem}-sheet{start // 6 + 1}.png")
    return len(images)


def main() -> None:
    synth_scan()
    synth_outline()
    PAGES.mkdir(exist_ok=True)
    (PAGES / ".gitignore").write_bytes(b"*.png\n")
    info = {}
    for path in sorted(CORPUS.glob("*.pdf")):
        with pdfium.PdfDocument(path) as doc:
            meta = {k: v for k, v in doc.get_metadata_dict().items() if k in ("Producer", "Creator")}
        info[path.name] = {"pages": render_pages(path.name), **meta}
        print(path.name, info[path.name])
    (BENCH / "info.json").write_bytes(json.dumps(info, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
