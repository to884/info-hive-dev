"""点列を実際に描いたオブジェクトと、登録済みの三点リーダのCIDを結ぶ。"""

from collections import Counter
from contextlib import closing
import ctypes
import importlib.util
import io
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v21-trail-source-pilot/run.py"
spec = importlib.util.spec_from_file_location("trail_with_cid_origin", BASE)
trail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trail)
audit, trace = trail.audit, trail.trace


def unique_command(operations, transform, maps, mode):
    scale = max(1, abs(transform[0]), abs(transform[3]))
    candidates = [op for op in operations
                  if op["embedded_sha256"] in {h for _, h, _ in maps}
                  and op["text_rendering_mode"] == mode
                  and max(abs(a - b) for a, b in zip(transform, op["matrix"], strict=True)) < scale * 1e-4]
    if len(candidates) != 1:
        raise ValueError("隔離後の描画オブジェクトを元のPDF命令に一意に結べない")
    return candidates[0]


def cid_sequence(op, maps, dots, flags):
    anchors = op["positioned_points"]
    if (op["collection"] != ["Adobe", "Japan1"] or op["ellipsis_cid_668"] != len(anchors)
            or len(dots) != 3 * len(anchors) or op["explicit_point_codepoints"]):
        raise ValueError("描画命令と固定画素で数えた三点リーダの個数が異なる")
    matching = [(collection, cmap) for collection, digest, cmap in maps if digest == op["embedded_sha256"]]
    if not matching or any(collection != ("Adobe", "Japan1") or cmap.get(668) not in (None, 0xFFFD, 0x2026)
                           for collection, cmap in matching):
        raise ValueError("Adobe-Japan1の宣言と埋め込みフォントのCID対応が矛盾")
    a, b, c, d, origin_x, origin_y = op["matrix"]
    if a <= 0 or d <= 0 or max(abs(b), abs(c)) > 1e-5:
        raise ValueError("横向きの実描画から点の位置を確かめられない")
    for cid, code, _, width in anchors:
        if cid != 668 or code not in (None, "FFFD", "2026") or width <= 0:
            raise ValueError("同じ登録済みCIDで三点ずつ描いたことを確認できない")
    origin = np.asarray(flags["150_origin"])
    grid = np.asarray(flags["150_matrix"])
    predictions = [float((grid @ (np.asarray((origin_x + a * (start + width * j / 3), origin_y)) - origin))[0])
                   for _, _, start, width in anchors for j in range(3)]
    true = [(l + r) / 2 for l, _, r, _ in dots]
    phase = true[0] - predictions[0]
    if abs(phase) > 3 or any(abs(p + phase - x) > 2 for p, x in zip(predictions, true, strict=True)):
        raise ValueError("元のCIDの順序と固定画素の点位置を説明できない")
    return {"cid": 668, "codepoint": "2026", "glyphs": len(anchors), "points": len(dots),
            "to_unicode_sha256": op["embedded_sha256"], "matrix": op["matrix"], "anchors": anchors}


def spell(pdf, page_no, fixed, dots, flags, operations):
    l, t = min(p[0] for p in dots), min(p[1] for p in dots)
    r, b = max(p[2] for p in dots), max(p[3] for p in dots)
    if l < 1 or t < 1 or r >= fixed.shape[1] or b >= fixed.shape[0]:
        raise ValueError("元の固定画像で点列の周囲を確認できない")
    box = np.s_[t - 1:b + 1, l - 1:r + 1]
    with closing(trace.pypdfium2.PdfDocument(pdf)) as doc, closing(doc[page_no - 1]) as page:
        with closing(page.get_textpage()) as text:
            objects = list(page.get_objects(filter=[trace.raw.FPDF_PAGEOBJ_TEXT], textpage=text))
            owner, = trace.reproduce(page, fixed[box], box, objects)
            mode = trace.raw.FPDFTextObj_GetTextRenderMode(owner)
            matrix = trace.raw.FS_MATRIX()
            if mode != 0 or not trace.raw.FPDFPageObj_GetMatrix(owner, ctypes.byref(matrix)):
                raise ValueError("実際の塗りの描画オブジェクトを特定できない")
            transformation = matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f
            name, font_sha = trace.font_name(owner)
    original_page = trace.PdfReader(io.BytesIO(pdf)).pages[page_no - 1]
    maps = trace.resources(original_page, name, font_sha)
    command = unique_command(operations, transformation, maps, mode)
    resolved = cid_sequence(command, maps, dots, flags)
    return {**resolved, "font_data_sha256": font_sha, "pdfium_font": name, "bounds": [l, t, r, b],
            "isolated_pixels_sha256": trace.sha(fixed[box].tobytes())}


def negatives(op, maps, dots, flags):
    other_collection = {**op, "collection": ["Adobe", "Identity"]}
    short = {**op, "positioned_points": op["positioned_points"][:-1]}
    cid, text, coordinate, width = op["positioned_points"][0]
    contradicts = {**op, "positioned_points": [[cid, "30FB", coordinate, width]] + op["positioned_points"][1:]}
    for item in (other_collection, short, contradicts):
        try:
            cid_sequence(item, maps, dots, flags)
        except ValueError:
            continue
        raise ValueError("対照で矛盾するCID対応を受理した")
    return 3


def main():
    result = HERE / "result.json"
    if result.exists():
        raise FileExistsError("固定した開発の出典照合は実行済み")
    prior = audit.OUT / "source-commands.json"
    if audit.load(audit.HERE / "result.json")["source_sha256"] != audit.sha(prior):
        raise ValueError("保存した出典の証跡と異なる")
    proofs = audit.load(prior)["evidence"]
    catalog, documents, target = audit.prior.old.lookup()[1], {}, []
    counts = Counter()
    for earlier, case in trail.old.cases():
        row = case["row"]
        key, line = row["key"], row["line_index"]
        name, expected, page = catalog[key]
        flags = case["assets"]["sha"]
        png = audit.prior.old.CORPUS / "probe-v4/png" / (key + ".png")
        if name not in documents:
            documents[name] = (audit.prior.old.CORPUS / name).read_bytes()
        pdf = documents[name]
        if trace.sha(pdf) != expected or flags["pdf_sha256"] != expected or audit.sha(png) != flags["150_dpi"]:
            raise ValueError("固定した元資料か画像が異なる")
        with Image.open(png) as image:
            grid = np.array(image.convert("RGB"))
        for mark, position in zip(trail.vision.MARK.finditer(case["answer"]["text"]), case["coordinates"], strict=True):
            if mark[1] != "trail":
                continue
            record = {"page": key, "line_index": line, "initial_status": earlier}
            try:
                dots = trail.old.dot_groups(case, png, mark, position)
                proof = spell(pdf, page, grid, dots, flags, proofs[key]["commands"])
            except (ValueError, KeyError, TypeError, AttributeError, IndexError) as e:
                record.update(status="unproven", reason=str(e)[:170])
            else:
                record.update(status="proven", evidence=proof)
                original = next(op for op in proofs[key]["commands"] if op["matrix"] == proof["matrix"]
                                and op["embedded_sha256"] == proof["to_unicode_sha256"] and op["text_rendering_mode"] == 0)
                maps = [(("Adobe", "Japan1"), proof["to_unicode_sha256"], {})]
                counts["contradictory_controls_rejected"] += negatives(original, maps, dots, flags)
            target.append(record)
            counts[record["status"]] += 1
            print(key, line, record["status"], record.get("reason") or proof["glyphs"], flush=True)
    audit.save_once(result, audit.encoded({
        "scope": "development-only", "counts": counts, "cases": target,
        "inputs": {str(p): audit.sha(p) for p in (Path(__file__), BASE, Path(trace.__file__), prior)},
    }))


if __name__ == "__main__":
    main()
