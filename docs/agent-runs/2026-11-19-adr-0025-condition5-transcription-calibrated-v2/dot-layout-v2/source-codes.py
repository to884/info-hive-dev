"""点線の画像成分とPDFの明示的な字形対応を、診断として照合する。"""

from collections import Counter, defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import sys

from pdfminer.cmapdb import CMapDB, CMapParser, FileUnicodeMap
from pdfminer.layout import LAParams, LTChar, LTTextBox, LTTextLine
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import dict_value, list_value, resolve1
from pdfminer.psparser import literal_name

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"
sys.path.insert(0, str(BENCH / "scripts"))
import glyph_geometry_v9 as geometry


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FontSources(geometry.SourceResources):
    def __init__(self):
        super().__init__()
        self.evidence = {}

    def get_font(self, objid, spec):
        font = super().get_font(objid, spec)
        encoding = resolve1(spec.get("Encoding"))
        encoding_name = literal_name(encoding) if encoding is not None else None
        if font in self.evidence or encoding_name != "Identity-H" or "DescendantFonts" not in spec:
            return font
        desc = dict_value(list_value(spec["DescendantFonts"])[0])
        collection = dict_value(desc["CIDSystemInfo"])
        cmap = resolve1(spec.get("ToUnicode"))
        if (collection.get("Registry") != b"Adobe" or collection.get("Ordering") != b"Japan1"
                or cmap is None):
            return font
        primary = FileUnicodeMap()
        cmap_bytes = cmap.get_data()
        CMapParser(primary, io.BytesIO(cmap_bytes)).run()
        standard = CMapDB.get_unicode_map("Adobe-Japan1", vertical=False)
        alternatives = {cid: standard.cid2unichr[cid] for cid, text in primary.cid2unichr.items()
                        if text == "\ufffd" and standard.cid2unichr.get(cid) in ("…", "‥", "・")}
        self.evidence[font] = (alternatives, objid, sha(cmap_bytes))
        return font


class Capture(geometry.OriginAggregator):
    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        advance = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        char = self.cur_item._objs[-1]
        source = self.rsrcmgr.evidence.get(font)
        if source and cid in source[0] and char.get_text() == "\ufffd":
            char.underlying_cid = cid, source[0][cid], source[1], source[2]
        return advance


def extract_anchors(pdf, wanted):
    manager = FontSources()
    received = {}
    device = Capture(manager, laparams=LAParams(**geometry.public_truth.rag_pdf_layer.LAPARAMS))
    interp = PDFPageInterpreter(manager, device)
    try:
        for n, page in zip(sorted(wanted), PDFPage.get_pages(io.BytesIO(pdf), pagenos={n - 1 for n in wanted}), strict=True):
            interp.process_page(page)
            layout = device.get_result()
            result = {}
            for li, line in enumerate(line for box in layout if isinstance(box, LTTextBox)
                                      for line in box if isinstance(line, LTTextLine)):
                chars = [c for c in line if isinstance(c, LTChar) and c.get_text().strip()]
                for ci, char in enumerate(chars):
                    if hasattr(char, "underlying_cid"):
                        result[li, ci] = {"origin": char.gt_origin, "anchor": char.underlying_cid}
            received[n] = result
    finally:
        device.close()
    if set(received) != wanted:
        raise ValueError("固定のページを読み取れない")
    return received


def overlaps(point, glyph):
    l, t, r, b = glyph
    x0, y0, x1, y1 = point
    return l <= (x0 + x1) / 2 < r and t <= (y0 + y1) / 2 < b


def compare(row, dots, source, native, anchors, matched):
    x, y, w, h = row["box"]
    weight = {"・": 1, "‥": 2, "…": 3}
    dots = [(x + l, y + t, x + r, y + b) for run in dots for l, t, r, b in run]
    glyph_candidates = [g for g in native if g["box"] and g["text"] in weight
                        and g["box"][0] < x + w and g["box"][2] > x
                        and g["box"][1] < y + h and g["box"][3] > y]
    used, codes, states, proof = Counter(), Counter(), Counter(), {}
    for dot in dots:
        near = [g for g in glyph_candidates if overlaps(dot, g["box"])]
        if len(near) != 1:
            states["unmapped" if not near else "multiple-geometries"] += 1
            continue
        g, = near
        index, text = g["index"], g["text"]
        used[index] += 1
        codes[f"U+{ord(text):04X}"] += 1
        if index in matched and not g["map_error"]:
            li, ci = matched[index]
            if source[li]["chars"][ci]["text"] == text:
                proof[index] = "pdfminer-pdfium"
        if index in proof:
            continue
        if g["origin"] is None:
            continue
        candidates = [m for m in anchors.values() if m["origin"] is not None and m["anchor"][1] == text
                      and math.dist(m["origin"], g["origin"]) <= geometry.ORIGIN_TOLERANCE_PT]
        if len(candidates) == 1:
            proof[index] = "embedded-cid-pdfium"
    for index, count in used.items():
        g = next(g for g in glyph_candidates if g["index"] == index)
        if index not in proof or count != weight[g["text"]]:
            states["indeterminate-glyph"] += 1
        else:
            states[proof[index]] += 1
    complete = bool(used) and not any(states[x] for x in ("unmapped", "multiple-geometries", "indeterminate-glyph"))
    return {"covered": complete, "positions": len(dots), "codes_by_point": codes, "matching": states}


def main():
    output = HERE / "source-codes.json"
    if output.exists():
        raise FileExistsError("診断の元記録を上書きしない")
    scan = HERE / "result.json"
    candidates = [r for r in load(scan)["geometries"] if r["previous"] == "unknown" and r["runs"]]
    # 文書別・頁別に固定したPDFの字形資料と照合する。
    pages = {}
    proofs, known_sha = {}, {scan.name: sha(scan.read_bytes()), Path(__file__).name: sha(Path(__file__).read_bytes())}
    for row in candidates:
        key = row["key"]
        publication, number = key.rsplit("-p", 1)
        pages.setdefault(publication, set()).add(int(number))
    for publication, numbers in pages.items():
        index = load(CORPUS / "public" / (publication + ".truth.json"))
        pdf = (CORPUS / index["file"]).read_bytes()
        if sha(pdf) != index["pdf_sha256"]:
            raise ValueError("元のPDFが固定のSHAと一致しない")
        known_sha[publication + ".pdf"] = sha(pdf)
        extracted = extract_anchors(pdf, numbers)
        for n in numbers:
            key = f"{publication}-p{n:04d}"
            source_file = CORPUS / "region-repair-v9/geometry" / (key + ".json")
            raw = source_file.read_bytes()
            region = load(CORPUS / "public/region-v9" / (key + ".json"))
            if sha(raw) != region["geometry_sha256"]:
                raise ValueError("保存した字形の幾何が固定と異なる")
            known_sha[source_file.name] = sha(raw)
            schema = json.loads(raw)
            anchors = extracted[n]
            for (li, ci), a in anchors.items():
                char = schema["source_lines"][li]["chars"][ci]
                if tuple(a["origin"]) != tuple(char["origin"]) or char["text"] != "\ufffd":
                    raise ValueError("PDFMinerを再実行して得たCIDの位置が元と異なる")
            proofs[key] = (region["lines"], schema["source_lines"], schema["native_glyphs"], anchors,
                           {m["native"]: (m["line"], m["char"]) for m in schema["matches"]})
    results, counts = [], defaultdict(Counter)
    for row in candidates:
        key, i = row["key"], row["line_index"]
        lines, source, native, anchors, matches = proofs[key]
        info = compare(lines[i], row["runs"], source, native, anchors, matches)
        results.append({"key": key, "line_index": i, "side": row["side"], **info})
        tally = counts[key]
        tally["rows"] += 1
        tally["all_points_covered"] += info["covered"]
        tally.update(info["matching"])
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-source-diagnosis", "inputs": known_sha, "pages": counts,
                   "rows": results}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
