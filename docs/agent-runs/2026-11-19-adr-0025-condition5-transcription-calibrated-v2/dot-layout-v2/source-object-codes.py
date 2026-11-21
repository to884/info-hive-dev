"""PDF描画命令と描画オブジェクトの一対一対応で三点リーダーの根拠を調べる。"""

from collections import Counter, defaultdict
from contextlib import closing
import ctypes
import importlib.util
import io
import json
import math
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source-codes.py"
spec = importlib.util.spec_from_file_location("source_codes", SOURCE)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
sha, load = source.sha, source.load
CORPUS = source.CORPUS
FONT_CODE = "…"
SPACE_CID = 1
TOLERANCE = source.geometry.ORIGIN_TOLERANCE_PT


class DrawCommands(source.PDFPageInterpreter):
    def __init__(self, manager, device):
        super().__init__(manager, device)
        self.commands = []

    def do_TJ(self, seq):
        font = self.textstate.font
        proof = self.rsrcmgr.evidence.get(font)
        if proof:
            alternatives, _, cmap_sha = proof
            data = b"".join(v for v in seq if isinstance(v, bytes))
            if len(data) % 2:
                raise ValueError("Identity-Hの文字列が2バイト境界にない")
            cids = tuple(int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2))
            is_ellipsis = lambda cid: alternatives.get(cid) == FONT_CODE
            matrix = self.textstate.matrix
            a, b, c, d, _, _ = matrix
            if (len(cids) > 1 and cids[0] == SPACE_CID and all(map(is_ellipsis, cids[1:]))
                    and self.textstate.linematrix == (0, 0) and a > 0 and d > 0 and b == c == 0):
                self.commands.append({"matrix": matrix, "count": len(cids), "font": font.fontname,
                                      "raw_cid": cids[1], "cmap_sha256": cmap_sha})
        return super().do_TJ(seq)


def commands(pdf, page_numbers):
    manager = source.FontSources()
    device = source.Capture(manager, laparams=source.LAParams(**source.geometry.public_truth.rag_pdf_layer.LAPARAMS))
    interp = DrawCommands(manager, device)
    groups = {}
    try:
        pages = source.PDFPage.get_pages(io.BytesIO(pdf), pagenos={n - 1 for n in page_numbers})
        for n, page in zip(sorted(page_numbers), pages, strict=True):
            interp.commands.clear()
            interp.process_page(page)
            groups[n] = tuple(interp.commands)
    finally:
        device.close()
    return groups


def font_name(pointer):
    n = raw.FPDFFont_GetBaseFontName(pointer, None, 0)
    if not n:
        raise ValueError("PDFiumのフォント名を確かめられない")
    buf = ctypes.create_string_buffer(n)
    if not raw.FPDFFont_GetBaseFontName(pointer, buf, n):
        raise ValueError("PDFiumのフォント名を取得できない")
    return buf.value.decode("ascii")


def objects(page, old_native):
    groups = {}
    with closing(page.get_textpage()) as text:
        for g in old_native:
            n = g["index"]
            if g["text"] != FONT_CODE:
                continue
            if raw.FPDFText_GetUnicode(text, n) != ord(FONT_CODE):
                raise ValueError("保存したPDFiumの正規化前の字種と異なる")
            obj = raw.FPDFText_GetTextObject(text, n)
            address = ctypes.cast(obj, ctypes.c_void_p).value
            if address is None:
                raise ValueError("対応するPDF描画オブジェクトがない")
            if address not in groups:
                matrix = raw.FS_MATRIX()
                if not raw.FPDFPageObj_GetMatrix(obj, ctypes.byref(matrix)):
                    raise ValueError("描画オブジェクトの行列を確かめられない")
                groups[address] = {"font": font_name(raw.FPDFTextObj_GetFont(obj)),
                                   "matrix": tuple(getattr(matrix, k) for k in "abcdef"), "glyphs": []}
            groups[address]["glyphs"].append(g)
    return list(groups.values())


def match_objects(drawing, rendered):
    one_to_one = {}
    for i, cmd in enumerate(drawing):
        nearby = [(j, obj) for j, obj in enumerate(rendered) if obj["font"] == cmd["font"]
                  and len(obj["glyphs"]) == cmd["count"]
                  and math.dist(obj["matrix"], cmd["matrix"]) <= TOLERANCE]
        if len(nearby) == 1:
            one_to_one[i] = nearby[0][0]
    reuse = Counter(one_to_one.values())
    mapped, excluded_space, anchors = {}, set(), []
    for i, j in one_to_one.items():
        if reuse[j] != 1:
            continue
        ordered = sorted(rendered[j]["glyphs"], key=lambda g: g["index"])
        cmd = drawing[i]
        if (any(g["origin"] is None for g in ordered)
                or any(b["origin"][0] <= a["origin"][0] for a, b in zip(ordered, ordered[1:]))):
            continue
        excluded_space.add(ordered[0]["index"])
        for g in ordered[1:]:
            mapped[g["index"]] = g
        anchors.append(cmd)
    return mapped, excluded_space, anchors


def validate_points(box, runs, mapped, excluded):
    x, y, _, _ = box
    dots = [(x + l, y + t, x + r, y + b) for run in runs for l, t, r, b in run]
    points = Counter()
    failed = Counter()
    for dot in dots:
        options = [g for g in mapped.values() if g["box"] and source.overlaps(dot, g["box"])]
        if len(options) != 1:
            failed["unmapped" if not options else "multiple"] += 1
        else:
            points[options[0]["index"]] += 1
    failed["glyphs_not_three_points"] = sum(n != 3 for n in points.values())
    hit_excluded = sum(any(g["box"] and source.overlaps(dot, g["box"]) for g in excluded) for dot in dots)
    return {"candidate_points": len(dots), "corroborated_ellipsis": sum(n == 3 for n in points.values()),
            "all_points_corroborated": bool(dots) and not any(failed.values()) and not hit_excluded,
            "failures": failed, "points_in_space_bbox": hit_excluded}


def main():
    target = HERE / "source-object-codes.json"
    if target.exists():
        raise FileExistsError("元の診断結果を上書きしない")
    scan_path = HERE / "result.json"
    scan = load(scan_path)
    truth = load(CORPUS / "public/defense.truth.json")
    pdf = (CORPUS / truth["file"]).read_bytes()
    if sha(pdf) != truth["pdf_sha256"]:
        raise ValueError("固定の防衛白書が変更されている")
    selected = defaultdict(list)
    for r in scan["geometries"]:
        if r["previous"] == "unknown" and r["runs"] and r["key"].startswith("defense-p"):
            selected[int(r["key"].rsplit("-p", 1)[1])].append(r)
    drawing = commands(pdf, selected.keys())
    results, page_report = [], {}
    with pdfium.PdfDocument(pdf) as doc:
        for n, rows in selected.items():
            key = f"defense-p{n:04d}"
            saved = CORPUS / "region-repair-v9/geometry" / (key + ".json")
            prior = load(CORPUS / "public/region-v9" / (key + ".json"))
            if sha(saved.read_bytes()) != prior["geometry_sha256"]:
                raise ValueError("固定したPDFiumの幾何が変化")
            native = load(saved)["native_glyphs"]
            with closing(doc[n - 1]) as page:
                rendered = objects(page, native)
            mapped, spaces, anchors = match_objects(drawing[n], rendered)
            used_spaces = [g for g in native if g["index"] in spaces]
            counts = Counter()
            for r in rows:
                line_index = r["line_index"]
                answer = validate_points(prior["lines"][line_index]["box"], r["runs"], mapped, used_spaces)
                counts["rows"] += 1
                counts["rows_corroborated"] += answer["all_points_corroborated"]
                counts["glyphs_corroborated"] += answer["corroborated_ellipsis"]
                results.append({"key": key, "line_index": line_index, **answer})
            page_report[key] = {"raw_groups": len(drawing[n]), "pdfium_groups": len(rendered),
                                "unique_object_matches": len(anchors), **counts}
    with target.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "source-character-diagnosis", "pdf_sha256": sha(pdf),
                   "dot_scan_sha256": sha(scan_path.read_bytes()), "pages": page_report,
                   "rows": results}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(page_report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
