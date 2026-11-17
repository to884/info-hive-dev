"""4 回目の測り方: 公開の PDF の正解を、OCR の箱の中の字で作る（../../adr-0025-condition5-v4-2026-11-17.md の 1）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/region_truth.py <side ...>
文字の層の字（pdfminer の LTChar）を取り出し、ページの画像（corpus/public/eyecheck/、150 dpi）でその字のインクの範囲を
測り、OCR の行の箱（corpus/ocr3/）に割り当てる。OCR の行ごとに「決められる行」の正解か、決められない理由を、
corpus/public/region/<ページの鍵>.json に書く。正解は公開の PDF の中身を含むので、corpus/ の外に置かない。
"""

from __future__ import annotations

import hashlib
import json
import sys
from contextlib import closing
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pypdfium2 as pdfium  # noqa: E402
from public_truth import CORPUS, DPI, OUT, layout_pages  # noqa: E402
from rag_ocr_flags import corners  # noqa: E402

REGION_REVISION = "region-v6"
CONTRAST = 64  # 背景の明るさ（周りの中央値）とこの値を超えて違う画素をインクとする（濃い字にも、地の色の上の白い字にも効く）
INSIDE = 0.5  # 字のインクの、読む向きの長さのこの割合以上が箱に入り、直交する向きのインクの中心が箱に入れば、字は箱に入る
GROW = 0.3  # 説明できないインクを数えるとき、字の箱を直交する向きに字の大きさのこの倍だけ広げた範囲を、字で説明できる範囲とする
STRAY_INK = 8  # 箱の中の、どの字のインクでも説明できないインクの画素がこの数を超えれば、決められない


def page_chars(layout, page) -> list[dict]:
    """文字の層の行ごとの字（行の中の並びの順）。行の番号は public_truth.truth_lines と同じ順で数える。"""
    from pdfminer.layout import LTChar, LTTextBox, LTTextLine, LTTextLineVertical

    left, bottom, right, top = page.get_cropbox()
    m_left, m_bottom, _, _ = page.get_mediabox()
    scale = DPI / 72

    def pixel(bbox):
        x0, y0, x1, y1 = bbox
        return [(x0 - (left - m_left)) * scale, ((top - m_bottom) - y1) * scale,
                (x1 - (left - m_left)) * scale, ((top - m_bottom) - y0) * scale]

    lines = []
    for box in layout:
        if not isinstance(box, LTTextBox):
            continue
        for line in box:
            if not isinstance(line, LTTextLine):
                continue
            vertical = isinstance(line, LTTextLineVertical)
            chars = [{"text": item.get_text(), "box": pixel(item.bbox), "vertical": vertical} for item in line
                     if isinstance(item, LTChar) and item.get_text().strip()]
            lines.append({"text": line.get_text().rstrip("\n"), "chars": chars})
    return lines


def clip(gray: np.ndarray, box, pad: float = 0.0) -> tuple[int, int, int, int]:
    h, w = gray.shape
    return (max(0, int(np.floor(box[0] - pad))), max(0, int(np.floor(box[1] - pad))),
            min(w, int(np.ceil(box[2] + pad))), min(h, int(np.ceil(box[3] + pad))))


def ink_mask(gray: np.ndarray, box) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """箱の中のインクの画素（背景は、箱の周りを箱の短い辺だけ広げた範囲の明るさの中央値）。"""
    x0, y0, x1, y1 = clip(gray, box)
    if x1 <= x0 or y1 <= y0:
        return np.zeros((0, 0), dtype=bool), (x0, y0, x1, y1)
    pad = min(box[2] - box[0], box[3] - box[1])
    wx0, wy0, wx1, wy1 = clip(gray, box, pad)
    background = float(np.median(gray[wy0:wy1, wx0:wx1]))
    return np.abs(gray[y0:y1, x0:x1].astype(np.int16) - background) > CONTRAST, (x0, y0, x1, y1)


def char_ink(gray: np.ndarray, char_box) -> list[float] | None:
    """字の箱の中のインクの範囲 [x0, y0, x1, y1]（インクがなければ None）。字をどの OCR の箱に割り当てるかに使う。"""
    mask, (x0, y0, _, _) = ink_mask(gray, char_box)
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    return [x0 + float(xs.min()), y0 + float(ys.min()), x0 + float(xs.max()) + 1, y0 + float(ys.max()) + 1]


def reach(char_box, vertical: bool) -> list[float]:
    """字のインクがありうる範囲。説明できないインクを数えるときに、文字の層で説明できる範囲として使う。

    pdfminer の字の箱は、読む向きに直交する向きの位置がフォントの寸法で決まり、インクと数画素ずれることがある
    （白書の本文で、字の上の部分が箱の外に出ていた）。そこで、直交する向きに字の大きさの GROW 倍だけ広げる。
    字の割り当て（char_ink）には広げた範囲を使わない。隣の行のインクが混ざるためである。
    """
    size = (char_box[2] - char_box[0]) if vertical else (char_box[3] - char_box[1])
    grow = GROW * size
    return ([char_box[0] - grow, char_box[1], char_box[2] + grow, char_box[3]] if vertical
            else [char_box[0], char_box[1] - grow, char_box[2], char_box[3] + grow])


def inside(ink, box, vertical: bool) -> float:
    """字のインクが OCR の箱に入る割合（直交する向きでインクの中心が箱に入らなければ 0。入れば読む向きの重なりの割合）。"""
    a0, a1 = (1, 3) if vertical else (0, 2)  # 読む向き
    c0, c1 = (0, 2) if vertical else (1, 3)  # 直交する向き
    center = (ink[c0] + ink[c1]) / 2
    if not box[c0] <= center <= box[c1]:
        return 0.0
    length = ink[a1] - ink[a0]
    return max(0.0, min(ink[a1], box[a1]) - max(ink[a0], box[a0])) / length if length > 0 else 1.0


def assign(truth_lines: list[dict], chars_by_line: list[list[dict]], ocr_lines: list[dict],
           gray: np.ndarray) -> tuple[list[dict], dict]:
    """OCR の行ごとに、決められる行の正解か、決められない理由を返す。あわせて、行ごと検出されなかった字の数を返す。"""
    boxes = [corners(x["box"]) for x in ocr_lines]
    vertical = [bool(x.get("vertical")) for x in ocr_lines]
    owner = {}  # (行, 字) → 属する OCR の行
    unboxed = set()  # 箱に入らなかった字（インクのない字を含む）
    shared = set()  # 取り合う字が入る OCR の行
    inks = []
    for i, chars in enumerate(chars_by_line):
        for k, c in enumerate(chars):
            inks.append(reach(c["box"], c["vertical"]))
            ink = char_ink(gray, c["box"])
            if ink is None:
                unboxed.add((i, k))
                continue
            hits = [j for j, (b, v) in enumerate(zip(boxes, vertical)) if inside(ink, b, v) >= INSIDE]
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
        elif any((sources[0], k) not in owner for k in range(len(chars_by_line[sources[0]]))):
            reason = "line-partly-outside"
        elif stray_ink(gray, boxes[j], inks) > STRAY_INK:
            reason = "stray-ink"
        record = {"line_index": j, "box": line["box"],
                  "ocr_text_sha256": hashlib.sha256(line["text"].encode("utf-8")).hexdigest()}
        if reason:
            record["undecided"] = reason
        else:
            record["text"] = "".join(chars_by_line[sources[0]][k]["text"] for _, k in mine)
            record["source_line"] = sources[0]
        records.append(record)
    lost = sum(len(chars) for i, chars in enumerate(chars_by_line) if not truth_lines[i].get("excluded")
               and chars and all((i, k) in unboxed for k in range(len(chars))))
    return records, {"lost_chars": lost, "chars": sum(len(c) for i, c in enumerate(chars_by_line)
                                                      if not truth_lines[i].get("excluded"))}


def stray_ink(gray: np.ndarray, box, inks: list[list[float]]) -> int:
    """箱の中のインクの画素のうち、文字の層のどの字のインクがありうる範囲（reach、1 画素広げる）にも入らないものの数。

    画像や図形で描いた字、アイコン、罫線、丸の中の番号など、文字の層にないものが箱の中にあれば、ここに現れる。
    PDF の中でどう描かれたか（入れ子の図形かどうか）によらず、描いた結果の画像で確かめる（12 回目のレビュー）。
    """
    mask, (x0, y0, x1, y1) = ink_mask(gray, box)
    if not mask.size:
        return 0
    covered = np.zeros_like(mask)
    for ink in inks:
        a0, b0 = max(x0, int(ink[0]) - 1), max(y0, int(ink[1]) - 1)
        a1, b1 = min(x1, int(np.ceil(ink[2])) + 1), min(y1, int(np.ceil(ink[3])) + 1)
        if a1 > a0 and b1 > b0:
            covered[b0 - y0:b1 - y0, a0 - x0:a1 - x0] = True
    return int((mask & ~covered).sum())


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
                    chars_by_line = page_chars(layout, page)
                page_truth = wanted[number]
                if [x["text"] for x in chars_by_line] != [x["text"] for x in page_truth["lines"]]:
                    raise SystemExit(f"文字の層の行が正解と合わない: {truth['name']} の {number}")
                key = f"{truth['name']}-p{number:04d}"
                ocr = json.loads((CORPUS / "ocr3" / f"{key}.json").read_bytes().decode("utf-8"))
                if ocr["pdf_sha256"] != truth["pdf_sha256"]:
                    raise SystemExit(f"OCR の結果の PDF が正解と違う: {key}")
                gray = np.asarray(Image.open(OUT / "eyecheck" / f"{key}.png").convert("L"))
                records, lost = assign(page_truth["lines"], [x["chars"] for x in chars_by_line], ocr["lines"], gray)
                (target / f"{key}.json").write_bytes(json.dumps(
                    {"key": key, "revision": REGION_REVISION, "pdf_sha256": truth["pdf_sha256"], **lost,
                     "lines": records}, ensure_ascii=False, indent=1).encode("utf-8"))
                for r in records:
                    name = r.get("undecided", "decided")
                    counts[name] = counts.get(name, 0) + 1
        print(truth["name"], truth["side"], json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
