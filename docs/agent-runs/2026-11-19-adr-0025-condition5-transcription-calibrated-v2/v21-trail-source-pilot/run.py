"""固定画素で孤立した点線の各字を、PDF内の実際のCID起点に照合する。"""

from collections import Counter
from contextlib import closing
import importlib.util
import io
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v20-trail-source-pilot/run.py"
spec = importlib.util.spec_from_file_location("v20_trail_geometry", PREVIOUS)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
audit, vision, trace = old.audit, old.vision, old.trace
OUT = audit.prior.old.CORPUS / "reference-v21-trail-source-pilot"


def bind_origin(operations, font, code, origin, fonts):
    name, data_sha = font
    if font not in fonts:
        raise ValueError("点の描画に使ったフォントを原本から確認できない")
    maps = fonts[font]
    keys = {digest for _, digest, _ in maps}
    possible = set()
    px, py = origin
    for record in operations:
        if record["embedded_sha256"] not in keys or record["text_rendering_mode"] not in (0, 1):
            continue
        a, b, c, d, x, y = record["matrix"]
        if abs(b) > 1e-5 or abs(c) > 1e-5:
            continue
        for cid, value, cursor, width in record["positioned_points"]:
            if max(abs(px - (a * cursor + x)), abs(py - (b * cursor + y))) > .25:
                continue
            symbol = f"{code:04X}"
            if value == symbol:
                possible.add((cid, symbol))
            elif cid == 668 and code == 0x2026 and record["collection"] == ["Adobe", "Japan1"] and value in (None, "FFFD"):
                possible.add((cid, symbol))
            else:
                raise ValueError("描画したCIDとPDFiumの符号が矛盾")
    if len(possible) != 1:
        raise ValueError("実際に描いたCIDを原点から一意に特定できない")
    cid, symbol = next(iter(possible))
    return {"cid": cid, "codepoint": symbol, "font_data_sha256": data_sha, "pdfium_font": name}


def spell(pdf, page_no, fixed, dots, flags, operations):
    l, t = min(p[0] for p in dots), min(p[1] for p in dots)
    r, b = max(p[2] for p in dots), max(p[3] for p in dots)
    window = np.s_[t - 1:b + 1, l - 1:r + 1]
    coords = [((a + c) / 2, (u + v) / 2) for a, u, c, v in dots]
    with closing(trace.pypdfium2.PdfDocument(pdf)) as doc, closing(doc[page_no - 1]) as page:
        with closing(page.get_textpage()) as text:
            objects = list(page.get_objects(filter=[trace.raw.FPDF_PAGEOBJ_TEXT], textpage=text))
            owners = trace.reproduce(page, fixed[window], window, objects)
            fields = old.visible_glyphs(text, owners, coords, flags)
    fontpage = trace.PdfReader(io.BytesIO(pdf)).pages[page_no - 1]
    fonts = {f: trace.resources(fontpage, f[0], f[1]) for f in {k[0] for k in fields}}
    used, encoded = set(), []
    for (font, code, origin, indices), objects in sorted(fields.items(), key=lambda pair: pair[0][-1]):
        modes = sorted(mode for _, mode in objects)
        if modes not in ([0], [0, 1]) or used.intersection(indices) or code not in old.SCALARS:
            raise ValueError("点を描いたオブジェクトか符号を一意に区別できない")
        if len(indices) != old.SCALARS[code] or indices != tuple(range(indices[0], indices[-1] + 1)):
            raise ValueError("一字の点の数を固定画素から確定できない")
        datum = bind_origin(operations, font, code, origin, fonts)
        encoded.append({**datum, "physical_indices": indices})
        used.update(indices)
    if used != set(range(len(dots))):
        raise ValueError("描画命令で見える点の全数を説明できない")
    return encoded


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("この出典の試験は実行済み")
    original_proof = audit.OUT / "source-commands.json"
    summary = audit.load(audit.HERE / "result.json")
    if audit.sha(original_proof) != summary["source_sha256"]:
        raise ValueError("元の正式監査の出典の証跡が異なる")
    recorded = audit.load(original_proof)["evidence"]
    catalog, documents = audit.prior.old.lookup()[1], {}
    results = []
    for earlier, case in old.cases():
        row = case["row"]
        key, index = row["key"], row["line_index"]
        name, expected, page = catalog[key]
        flags = case["assets"]["sha"]
        png = audit.prior.old.CORPUS / "probe-v4/png" / (key + ".png")
        if name not in documents:
            documents[name] = (audit.prior.old.CORPUS / name).read_bytes()
        blob = documents[name]
        if trace.sha(blob) != expected or flags["pdf_sha256"] != expected or audit.sha(png) != flags["150_dpi"]:
            raise ValueError("固定した出典か画像と異なる")
        with Image.open(png) as im:
            rgb = np.array(im.convert("RGB"))
        for marker, positions in zip(vision.MARK.finditer(case["answer"]["text"]), case["coordinates"], strict=True):
            if marker[1] != "trail":
                continue
            current = {"page": key, "line_index": index, "prior": earlier}
            try:
                points = old.dot_groups(case, png, marker, positions)
                items = spell(blob, page, rgb, points, flags, recorded[key]["commands"])
            except (ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
                current.update(result="unproven", reason=str(error)[:180])
            else:
                current.update(result="proven", points=len(points), candidates=items,
                               codepoints=Counter(v["codepoint"] for v in items))
            results.append(current)
            print(key, index, current["result"], current.get("codepoints") or current.get("reason"), flush=True)
    OUT.mkdir()
    docs = Path(__file__), PREVIOUS, Path(trace.__file__), original_proof, audit.HERE / "result.json"
    audit.save_once(HERE / "result.json", audit.encoded({"scope": "development-only", "cases": results,
                  "inputs": {str(p): audit.sha(p) for p in docs}}))


if __name__ == "__main__":
    main()
