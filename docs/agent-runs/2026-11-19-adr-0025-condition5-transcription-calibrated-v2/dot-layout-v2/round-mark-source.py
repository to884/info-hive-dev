"""v9監査で割れた丸印1字の符号を、同じ元PDFの描画命令まで照合する。"""

from contextlib import closing
import importlib.util
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source-codes.py"
spec = importlib.util.spec_from_file_location("source", SOURCE)
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
load, sha = data.load, data.sha
CORPUS, geo = data.CORPUS, data.geometry
KEY, PAGE, LINE = "disaster-p0133", 133, 3


class Track(geo.OriginAggregator):
    def __init__(self, manager):
        super().__init__(manager, laparams=data.LAParams(**geo.public_truth.rag_pdf_layer.LAPARAMS))
        self.round_marks = []

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        result = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        char = self.cur_item._objs[-1]
        code = char.get_text()
        if code in ("•", "・") and hasattr(font, "unicode_map") and font.unicode_map.cid2unichr.get(cid) == code:
            self.round_marks.append({"cid": cid, "unicode": f"U+{ord(code):04X}", "origin": char.gt_origin,
                                     "declared_font": font.fontname})
        return result


def main():
    fixed = CORPUS / "public/region-v9" / (KEY + ".json")
    geometry_file = CORPUS / "region-repair-v9/geometry" / (KEY + ".json")
    png = CORPUS / "probe-v4/png" / (KEY + ".png")
    region, saved = load(fixed), load(geometry_file)
    if sha(geometry_file.read_bytes()) != region["geometry_sha256"] or sha(png.read_bytes()) != region["image_sha256"]:
        raise ValueError("固定した画像と幾何が異なる")
    row = region["lines"][LINE]
    index = row["certification"]["native_glyphs"][0]
    glyph, = [g for g in saved["native_glyphs"] if g["index"] == index]
    if glyph["text"] not in ("•", "・"):
        raise ValueError("照合対象の行頭の丸印が変化")
    relation, = [m for m in saved["matches"] if m["native"] == index]
    original = saved["source_lines"][relation["line"]]["chars"][relation["char"]]
    if original["text"] != glyph["text"] or glyph["map_error"]:
        raise ValueError("PDFMinerとPDFiumの文字対応が一意に決まらない")
    expected = load(CORPUS / "public/disaster.truth.json")
    payload = (CORPUS / expected["file"]).read_bytes()
    if sha(payload) != expected["pdf_sha256"]:
        raise ValueError("元のPDFのSHAと一致しない")
    manager = geo.SourceResources()
    with closing(Track(manager)) as device:
        interp = data.PDFPageInterpreter(manager, device)
        page, = data.PDFPage.get_pages(io.BytesIO(payload), pagenos={PAGE - 1})
        interp.process_page(page)
        cid, = [m for m in device.round_marks if m["origin"] is not None and
                math.dist(m["origin"], glyph["origin"]) <= geo.ORIGIN_TOLERANCE_PT]
    if cid["unicode"] != f"U+{ord(glyph['text']):04X}":
        raise ValueError("描画命令の符号と固定した符号が一致しない")
    import region_truth
    with Image.open(png) as opened:
        image = np.asarray(opened.convert("L"))
    pixels = region_truth.char_ink(image, glyph["box"])
    mask, _ = region_truth.ink_mask(image, glyph["box"])
    _, count = label(mask, structure=np.ones((3, 3)))
    if pixels is None or count != 1 or region_truth.inside(pixels, region_truth.corners(row["box"]), False) < region_truth.INSIDE:
        raise ValueError("固定画像の丸印の所属が確かめられない")
    proof = {"scope": "development-source-diagnosis", "page": KEY, "line_index": LINE,
             "pdf_sha256": sha(payload), "image_sha256": region["image_sha256"], "geometry_sha256": region["geometry_sha256"],
             "ink_bounds": pixels, "pixel_counted_as_one_mark": True, "raw_source": cid}
    with (HERE / "round-mark-source.json").open("x", encoding="utf-8") as stream:
        json.dump(proof, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"page": KEY, "line": LINE, "cid": cid["cid"], "same_code": cid["unicode"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
