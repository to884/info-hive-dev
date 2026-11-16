"""公開の PDF のページを決まりどおりに選び、正解の行（pdfminer の LTTextLine の文字と箱）を書く。

使い方（rag の依存の環境で動かす）:
    python -X utf8 scripts/public_truth.py extract   # 選んで corpus/public/<tag>.truth.json と目で確かめる画像を書く
    python -X utf8 scripts/public_truth.py apply     # corpus/public/eyecheck.json の結果を正解に当てる

測り方は ../../adr-0025-condition5-2026-11-16.md の「公開の PDF」と「正解から除く行」。
正解と画像は公開の PDF の中身を含むので、corpus/ の外に置かない。
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import re
import sys
from contextlib import closing
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pypdfium2 as pdfium  # noqa: E402
import rag_pdf_layer  # noqa: E402
from score import normalize  # noqa: E402

CORPUS = BENCH / "corpus"
OUT = CORPUS / "public"
DPI = 150
SEED = 20261116
# tag、ファイル、側、選び方（"all" か、乱数で選ぶページの数）
PLAN = [
    ("wp-summary", "whitepaper-summary.pdf", "tuning", "all"),
    ("wp-point", "whitepaper-point.pdf", "tuning", "all"),
    ("kanpo1828-p1", "kanpo-p1.pdf", "tuning", "all"),
    ("kanpo1828-p2", "kanpo-p2.pdf", "tuning", "all"),
    ("kanpo1828-p3", "kanpo-p3.pdf", "tuning", "all"),
    ("kanpo1828-p4", "kanpo-p4.pdf", "tuning", "all"),
    ("defense", "defense-white-paper-2025.pdf", "evaluation", 20),
    ("kanpo1827-p1", "kanpo-1827-p1.pdf", "evaluation", "all"),
    ("kanpo1827-p2", "kanpo-1827-p2.pdf", "evaluation", "all"),
    ("bert", "bert.pdf", "dev", [1]),
]
CID = re.compile(r"\(cid:\d+\)")


def layout_pages(data: bytes):
    """製品と同じ組の順（rag_pdf_layer の StablePage と同じ手順）で、ページの組み立ての結果を順に返す。"""
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.layout import LAParams, LTPage
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.utils import apply_matrix_rect

    class StablePage(LTPage):
        def group_textboxes(self, laparams, boxes):
            return rag_pdf_layer._stable_group_textboxes(self, laparams, boxes)

    class StableAggregator(PDFPageAggregator):
        def begin_page(self, page, ctm):
            (x0, y0, x1, y1) = apply_matrix_rect(ctm, page.mediabox)
            self.cur_item = StablePage(self.pageno, (0, 0, abs(x0 - x1), abs(y0 - y1)))

    manager = PDFResourceManager()
    device = StableAggregator(manager, laparams=LAParams(**rag_pdf_layer.LAPARAMS))
    interpreter = PDFPageInterpreter(manager, device)
    for number, page in enumerate(PDFPage.get_pages(io.BytesIO(data)), start=1):
        interpreter.process_page(page)
        yield number, device.get_result()


def truth_lines(layout, page) -> list[dict]:
    from pdfminer.layout import LTTextBox, LTTextLine, LTTextLineVertical

    left, bottom, right, top = page.get_cropbox()
    m_left, m_bottom, _, _ = page.get_mediabox()
    scale = DPI / 72
    lines = []
    for box in layout:
        if not isinstance(box, LTTextBox):
            continue
        for line in box:
            if not isinstance(line, LTTextLine):
                continue
            text = line.get_text().rstrip("\n")
            x0, y0, x1, y1 = line.bbox
            pixel = [(x0 - (left - m_left)) * scale, ((top - m_bottom) - y1) * scale,
                     (x1 - (left - m_left)) * scale, ((top - m_bottom) - y0) * scale]
            excluded = None
            if any(0xE000 <= ord(c) <= 0xF8FF or c == "�" for c in text) or CID.search(text):
                excluded = "garbled"
            elif not normalize(text):
                excluded = "empty"
            lines.append({"id": len(lines), "text": text, "box": [round(v, 2) for v in pixel],
                          "vertical": isinstance(line, LTTextLineVertical), "excluded": excluded})
    return lines


def extract() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "eyecheck").mkdir(exist_ok=True)
    for tag, file, side, rule in PLAN:
        data = (CORPUS / file).read_bytes()
        eligible, pages = [], {}
        with pdfium.PdfDocument(data) as document:
            for number, layout in layout_pages(data):
                with closing(document[number - 1]) as page:
                    if page.get_rotation() != 0:
                        continue
                    _, quality = rag_pdf_layer.inspect_page(page)
                    if quality["kind"] not in ("text", "vertical"):
                        continue
                    lines = truth_lines(layout, page)
                if sum(line["excluded"] is None for line in lines) >= 10 or isinstance(rule, list):
                    eligible.append(number)
                    pages[number] = {"page": number, "kind": quality["kind"], "lines": lines}
            if rule == "all":
                chosen = eligible
            elif isinstance(rule, list):
                chosen = [n for n in rule if n in pages]
            else:
                chosen = sorted(random.Random(SEED).sample(sorted(eligible), rule))
            for number in chosen:
                with closing(document[number - 1]) as page:
                    bitmap = page.render(scale=DPI / 72)
                    bitmap.to_pil().convert("RGB").save(OUT / "eyecheck" / f"{tag}-p{number:04d}.png")
                    bitmap.close()
        truth = {"name": tag, "file": file, "side": side, "stratum": "public",
                 "pdf_sha256": hashlib.sha256(data).hexdigest(), "eligible": eligible,
                 "pages": [pages[n] for n in chosen]}
        (OUT / f"{tag}.truth.json").write_bytes(json.dumps(truth, ensure_ascii=False, indent=1).encode("utf-8"))
        counted = sum(line["excluded"] is None for n in chosen for line in pages[n]["lines"])
        print(tag, side, "当たるページ", len(eligible), "選んだページ", chosen, "数える正解の行", counted, flush=True)


def apply() -> None:
    """目で確かめて画像と違った行を、正解から除く（excluded = "eyecheck"）。"""
    checked = json.loads((OUT / "eyecheck.json").read_bytes().decode("utf-8"))
    for tag, file, side, rule in PLAN:
        path = OUT / f"{tag}.truth.json"
        truth = json.loads(path.read_bytes().decode("utf-8"))
        for page in truth["pages"]:
            key = f"{tag}-p{page['page']:04d}"
            if key not in checked:
                raise SystemExit(f"目で確かめていないページ: {key}")
            wrong = set(checked[key]["wrong"])
            for line in page["lines"]:
                if line["id"] in wrong and line["excluded"] is None:
                    line["excluded"] = "eyecheck"
        path.write_bytes(json.dumps(truth, ensure_ascii=False, indent=1).encode("utf-8"))
    print("目で確かめた結果を当てた")


if __name__ == "__main__":
    {"extract": extract, "apply": apply}[sys.argv[1]]()
