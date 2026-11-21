"""三点リーダーの描画命令だけを複製PDFに残し、固定画像の点を再現する。"""

from collections import Counter
from contextlib import closing
import ctypes
import importlib.util
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from pdfminer.utils import mult_matrix
from scipy.ndimage import find_objects, label

HERE = Path(__file__).resolve().parent
OLDER = HERE / "source-object-codes.py"
spec = importlib.util.spec_from_file_location("drawing_codes", OLDER)
object_codes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(object_codes)
source, raw, pdfium = object_codes.source, object_codes.raw, object_codes.pdfium
sha, load = source.sha, source.load
CORPUS = source.CORPUS


class EffectiveDrawing(object_codes.DrawCommands):
    def do_TJ(self, seq):
        former = len(self.commands)
        result = super().do_TJ(seq)
        if len(self.commands) > former:
            item = self.commands[-1]
            item["matrix"] = mult_matrix(mult_matrix(item["matrix"], self.ctm), self.device.gt_inverse_ctm)
            item["cid_1_to_unicode"] = self.textstate.font.unicode_map.cid2unichr.get(1)
        return result


def commands_for(pdf, numbers):
    manager = source.FontSources()
    device = source.Capture(manager, laparams=source.LAParams(**source.geometry.public_truth.rag_pdf_layer.LAPARAMS))
    interp = EffectiveDrawing(manager, device)
    try:
        pages = source.PDFPage.get_pages(io.BytesIO(pdf), pagenos={n - 1 for n in numbers})
        result = {}
        for n, page in zip(sorted(numbers), pages, strict=True):
            interp.commands.clear()
            interp.process_page(page)
            result[n] = tuple(interp.commands)
        return result
    finally:
        device.close()


def object_identity(obj):
    if obj.type != raw.FPDF_PAGEOBJ_TEXT:
        return None
    font = object_codes.font_name(raw.FPDFTextObj_GetFont(obj))
    matrix = raw.FS_MATRIX()
    if not raw.FPDFPageObj_GetMatrix(obj, ctypes.byref(matrix)):
        raise ValueError("PDFiumの描画行列が取れない")
    return font, tuple(getattr(matrix, key) for key in "abcdef")


def isolated_pixels(doc, number, commands, expected_transform):
    with closing(pdfium.PdfDocument.new()) as copy:
        copy.import_pages(doc, pages=[number - 1])
        with closing(copy[0]) as page:
            pairs = Counter()
            for obj in list(page.get_objects(max_depth=1)):
                data = object_identity(obj)
                candidates = []
                if data is not None:
                    font, matrix = data
                    candidates = [i for i, item in enumerate(commands) if item["font"] == font
                                  and math.dist(matrix[:4], item["matrix"][:4]) <= 1e-5
                                  and math.dist(matrix[4:], item["matrix"][4:]) <= 1e-3]
                if len(candidates) > 1:
                    raise ValueError("一つの描画オブジェクトに複数の描画命令が対応")
                if not candidates:
                    page.remove_obj(obj)
                else:
                    pairs[candidates[0]] += 1
            if len(pairs) != len(commands) or any(n != 1 for n in pairs.values()):
                raise ValueError("描画命令とオブジェクトが一対一に対応しない")
            page.gen_content()
            with closing(page.render(scale=150 / 72)) as bitmap:
                actual_origin, actual_matrix = source.geometry.pixel_transform(bitmap, page)
                if (not np.array_equal(actual_origin, expected_transform["page_origin"])
                        or not np.array_equal(actual_matrix, expected_transform["page_to_pixel"])):
                    raise ValueError("複製したページの150 DPIの座標変換が変わった")
                return np.asarray(bitmap.to_pil().convert("L")).copy()


def main():
    output = HERE / "source-render-objects.json"
    if output.exists():
        raise FileExistsError("既存の根拠を上書きしない")
    scan = HERE / "result.json"
    truth_path = CORPUS / "public/defense.truth.json"
    truth = load(truth_path)
    pdf_path = CORPUS / truth["file"]
    pdf = pdf_path.read_bytes()
    if sha(pdf) != truth["pdf_sha256"]:
        raise ValueError("固定したPDFと異なる")
    found = [r for r in load(scan)["geometries"] if r["previous"] == "unknown" and r["runs"]
             and r["key"].startswith("defense-p")]
    numbers = {int(r["key"].rsplit("-p", 1)[1]) for r in found}
    commands = commands_for(pdf, numbers)
    recorded, summary = [], {}
    paths = [scan, truth_path, OLDER, Path(__file__), object_codes.SOURCE]
    with closing(pdfium.PdfDocument(pdf)) as doc:
        for n in sorted(numbers):
            key = f"defense-p{n:04d}"
            saved = CORPUS / "region-repair-v9/geometry" / (key + ".json")
            region_path = CORPUS / "public/region-v9" / (key + ".json")
            original_path = CORPUS / "probe-v4/png" / (key + ".png")
            region = load(region_path)
            if sha(saved.read_bytes()) != region["geometry_sha256"] or sha(original_path.read_bytes()) != region["image_sha256"]:
                raise ValueError("保存した幾何か固定画像が変わった")
            plane = isolated_pixels(doc, n, commands[n], load(saved)["pixel_transform"])
            paths.extend((saved, region_path, original_path))
            with Image.open(original_path) as original:
                if plane.shape != (original.height, original.width):
                    raise ValueError("複製画像の寸法が固定画像と異なる")
            points = {(xs.start, ys.start, xs.stop, ys.stop)
                      for ys, xs in find_objects(label(plane < 191, structure=np.ones((3, 3)))[0])}
            expected = 3 * sum(command["count"] - 1 for command in commands[n])
            if len(points) != expected:
                raise ValueError("描画命令のCID数と物理的な点の数が異なる")
            c = Counter()
            for r in found:
                if r["key"] != key:
                    continue
                i = r["line_index"]
                x, y, _, _ = region["lines"][i]["box"]
                subset = {(x + l, y + t, x + a, y + b) for run in r["runs"] for l, t, a, b in run}
                missing = subset - points
                c["rows"] += 1
                c["same_pixel_components"] += not missing
                recorded.append({"key": key, "line_index": i, "points": len(subset),
                                 "unreproduced_points": len(missing), "same_pixel_components": not missing})
            summary[key] = dict(c, isolated_points=len(points), expected_points=expected,
                                paired_objects=len(commands[n]), isolated_150dpi_sha256=sha(plane.tobytes()),
                                cid_1_embedded_unicode=sorted({f"U+{ord(s):04X}" for item in commands[n]
                                                               if (s := item["cid_1_to_unicode"]) and len(s) == 1}))
    if sha(pdf_path.read_bytes()) != truth["pdf_sha256"]:
        raise ValueError("元のPDFが変わった")
    manifest = {f.relative_to(HERE.parents[2]).as_posix(): sha(f.read_bytes()) for f in paths}
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "development-render-isolation", "source_pdf_sha256": sha(pdf), "files_sha256": manifest,
                   "pages": summary, "rows": recorded}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
