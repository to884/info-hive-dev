"""4 回目の測り方: 公開の PDF の正解を、OCR の箱の中の字で作る（../../adr-0025-condition5-v4-2026-11-17.md の 1）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/region_truth.py <side ...>
文字の層の字（pdfminer の LTChar）を取り出し、OCR の行の箱（corpus/ocr3/）に割り当て、OCR の行ごとに
「決められる行」の正解か、決められない理由を、corpus/public/region/<ページの鍵>.json に書く。
正解は公開の PDF の中身を含むので、corpus/ の外に置かない。
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pypdfium2 as pdfium  # noqa: E402
from public_truth import CORPUS, DPI, OUT, layout_pages  # noqa: E402
from rag_ocr_flags import corners  # noqa: E402

REGION_REVISION = "region-v3"
# 字の読む向きの長さのこの割合以上が OCR の箱に入れば、字はその箱に入る。入る箱が 1 つだけなら字はその箱に属し、
# 2 つ以上なら取り合う字で、それらの箱の行はどれも決められない。どの箱にも入らない字は、箱に入らなかった字。
# 字の箱は全角の送り幅で、句読点などのインクは一部しか占めないので、0.2 と小さくする
INSIDE = 0.2
OVERHANG = 0.5  # 箱が属する字の範囲から、読む向きの前か後ろに字の大きさのこの倍を超えてはみ出せば、決められない
FIGURE = 2.0  # 長い辺が字の大きさのこの倍以下の図形が箱に入れば（面積の半分以上）、決められない


def page_chars(layout, page) -> tuple[list[dict], list[list[float]]]:
    """文字の層の行ごとの字（行の中の並びの順）と、ページの図形の箱。行の番号は public_truth.truth_lines と同じ順で数える。"""
    from pdfminer.layout import LTChar, LTCurve, LTFigure, LTImage, LTTextBox, LTTextLine

    left, bottom, right, top = page.get_cropbox()
    m_left, m_bottom, _, _ = page.get_mediabox()
    scale = DPI / 72

    def pixel(bbox):
        x0, y0, x1, y1 = bbox
        return [(x0 - (left - m_left)) * scale, ((top - m_bottom) - y1) * scale,
                (x1 - (left - m_left)) * scale, ((top - m_bottom) - y0) * scale]

    lines, figures = [], []
    for box in layout:
        if isinstance(box, (LTCurve, LTImage, LTFigure)):  # LTRect と LTLine は LTCurve の一種
            figures.append(pixel(box.bbox))
        if not isinstance(box, LTTextBox):
            continue
        for line in box:
            if not isinstance(line, LTTextLine):
                continue
            chars = [{"text": item.get_text(), "box": pixel(item.bbox)} for item in line
                     if isinstance(item, LTChar) and item.get_text().strip()]
            lines.append({"text": line.get_text().rstrip("\n"), "chars": chars})
    return lines, figures


def inside(char_box, box, vertical: bool) -> float:
    """字が OCR の箱に入る割合。

    pdfminer の字の箱は、読む向きに直交する辺がフォントの高さ（縦書きは幅）で決まり、インクより大きい。OCR の箱は
    インクに沿う。そこで、直交する向きは字の中心が箱の範囲に入るかだけを見て、入り方は読む向きの重なりの割合で測る。
    """
    a0, a1 = (1, 3) if vertical else (0, 2)  # 読む向き
    c0, c1 = (0, 2) if vertical else (1, 3)  # 直交する向き
    center = (char_box[c0] + char_box[c1]) / 2
    if not box[c0] <= center <= box[c1]:
        return 0.0
    length = char_box[a1] - char_box[a0]
    if length <= 0:
        return float(box[a0] <= char_box[a0] <= box[a1])
    return max(0.0, min(char_box[a1], box[a1]) - max(char_box[a0], box[a0])) / length


def assign(truth_lines: list[dict], chars_by_line: list[list[dict]], ocr_lines: list[dict],
           figures: list[list[float]]) -> tuple[list[dict], dict]:
    """OCR の行ごとに、決められる行の正解か、決められない理由を返す。あわせて、行ごと検出されなかった字の数を返す。"""
    boxes = [corners(x["box"]) for x in ocr_lines]
    vertical = [bool(x.get("vertical")) for x in ocr_lines]
    owner = {}  # (行, 字) → 属する OCR の行
    unboxed = set()
    shared = set()  # 取り合う字が入る OCR の行
    for i, chars in enumerate(chars_by_line):
        for k, c in enumerate(chars):
            hits = [j for j, (b, v) in enumerate(zip(boxes, vertical)) if inside(c["box"], b, v) >= INSIDE]
            if len(hits) == 1:
                owner[(i, k)] = hits[0]
            elif hits:
                shared.update(hits)
            else:
                unboxed.add((i, k))
    members: dict[int, list[tuple[int, int]]] = {}
    for key, j in owner.items():
        members.setdefault(j, []).append(key)
    records = []
    for j, line in enumerate(ocr_lines):
        mine = sorted(members.get(j, []))
        sources = sorted({i for i, _ in mine})
        reason = None
        if j in shared:
            reason = "shared-char"
        elif not mine:
            reason = "no-chars"
        elif len(sources) > 1:
            reason = "many-lines"
        elif truth_lines[sources[0]].get("excluded"):
            reason = "excluded"
        else:
            i = sources[0]
            whole = range(len(chars_by_line[i]))
            if any((i, k) not in owner for k in whole):
                reason = "line-partly-outside"
            else:
                vertical = bool(line.get("vertical"))
                a0, a1 = (1, 3) if vertical else (0, 2)  # 読む向きの座標
                c0, c1 = (0, 2) if vertical else (1, 3)  # 直交する向きの座標
                got = [chars_by_line[i][k]["box"] for _, k in mine]
                size = statistics.median(b[c1] - b[c0] for b in got)
                head = min(b[a0] for b in got) - boxes[j][a0]
                tail = boxes[j][a1] - max(b[a1] for b in got)
                if max(head, tail) > OVERHANG * size:
                    reason = "box-overhang"
                elif any(small_figure(f, boxes[j], size) for f in figures):
                    reason = "figure-in-box"
        record = {"line_index": j, "box": line["box"],
                  "ocr_text_sha256": hashlib.sha256(line["text"].encode("utf-8")).hexdigest()}
        if reason:
            record["undecided"] = reason
        else:
            record["text"] = "".join(chars_by_line[sources[0]][k]["text"] for _, k in mine)
            record["source_line"] = sources[0]
        records.append(record)
    lost = sum(1 for i, chars in enumerate(chars_by_line) if not truth_lines[i].get("excluded")
               and chars and all((i, k) in unboxed for k in range(len(chars))) for _ in chars)
    return records, {"lost_chars": lost, "chars": sum(len(c) for i, c in enumerate(chars_by_line)
                                                      if not truth_lines[i].get("excluded"))}


def small_figure(figure, box, size: float) -> bool:
    """字の大きさの FIGURE 倍以下の図形で、面積の半分以上が箱に入るか（面積のない図形は、中心が入るか）。"""
    w, h = figure[2] - figure[0], figure[3] - figure[1]
    if max(w, h) > FIGURE * size:
        return False
    if w <= 0 or h <= 0:
        cx, cy = (figure[0] + figure[2]) / 2, (figure[1] + figure[3]) / 2
        return box[0] <= cx <= box[2] and box[1] <= cy <= box[3]
    iw = max(0.0, min(figure[2], box[2]) - max(figure[0], box[0]))
    ih = max(0.0, min(figure[3], box[3]) - max(figure[1], box[1]))
    return iw * ih >= 0.5 * w * h


def main() -> None:
    sides = set(sys.argv[1:])
    target = OUT / "region"
    target.mkdir(exist_ok=True)
    for path in sorted(OUT.glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        if truth["side"] not in sides:
            continue
        data = (CORPUS / truth["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != truth["pdf_sha256"]:
            raise SystemExit(f"PDF が正解と違う: {truth['name']}")
        wanted = {p["page"]: p for p in truth["pages"]}
        counts = {}
        with pdfium.PdfDocument(data) as document:
            for number, layout in layout_pages(data):
                if number not in wanted:
                    continue
                with closing(document[number - 1]) as page:
                    chars_by_line, figures = page_chars(layout, page)
                page_truth = wanted[number]
                if [x["text"] for x in chars_by_line] != [x["text"] for x in page_truth["lines"]]:
                    raise SystemExit(f"文字の層の行が正解と合わない: {truth['name']} の {number}")
                key = f"{truth['name']}-p{number:04d}"
                ocr = json.loads((CORPUS / "ocr3" / f"{key}.json").read_bytes().decode("utf-8"))
                if ocr["pdf_sha256"] != truth["pdf_sha256"]:
                    raise SystemExit(f"OCR の結果の PDF が正解と違う: {key}")
                records, lost = assign(page_truth["lines"], [x["chars"] for x in chars_by_line], ocr["lines"], figures)
                (target / f"{key}.json").write_bytes(json.dumps(
                    {"key": key, "revision": REGION_REVISION, "pdf_sha256": truth["pdf_sha256"], **lost,
                     "lines": records}, ensure_ascii=False, indent=1).encode("utf-8"))
                for r in records:
                    name = r.get("undecided", "decided")
                    counts[name] = counts.get(name, 0) + 1
        print(truth["name"], truth["side"], json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
