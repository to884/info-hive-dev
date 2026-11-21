"""保存した点線の二票を、描画オブジェクトと点数から開発用に照合する。"""

from collections import Counter, defaultdict
from contextlib import closing
import ctypes
import importlib.util
import io
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


audit = module("v15_fixed", HERE.parent / "v15-reference-audit/run.py")
vision = audit.reference
trace = module("round_object_binding", HERE.parent / "v19-object-source-pilot/trace.py")
from point_ink import groups

OUT = audit.prior.old.CORPUS / "reference-v20-trail-source-pilot"
SCALARS = {0x2026: 3, 0x30FB: 1}


def dot_groups(case, png, mark, coordinates):
    row = case["row"]
    with Image.open(png) as im:
        gray = np.array(im.convert("L"))
    zones = groups(gray, row["box"])
    close = []
    for dots in zones.get(mark[1], []):
        x0 = row["box"][0]
        first = (dots[0][0] + dots[0][2]) / 2 - x0
        last = (dots[-1][0] + dots[-1][2]) / 2 - x0
        if max(abs(first - coordinates[0]), abs(last - coordinates[1]), abs(first - coordinates[2]), abs(last - coordinates[3])) <= 10:
            close.append(dots)
    dots, = close
    return dots


def intersections(glyph, centers):
    return {i for i, (x, y) in enumerate(centers)
            if glyph[:, 0].min() - 1 <= x <= glyph[:, 0].max() + 1 and glyph[:, 1].min() - 1 <= y <= glyph[:, 1].max() + 1}


def visible_glyphs(textpage, owners, coords, flags):
    selected = {trace.pointer(item.raw): item for item in owners}
    fonts = {p: trace.font_name(obj) for p, obj in selected.items()}
    trans = np.asarray(flags["150_matrix"])
    origin = np.asarray(flags["150_origin"])
    solid = defaultdict(set)
    for i in range(textpage.count_chars()):
        oid = trace.pointer(trace.raw.FPDFText_GetTextObject(textpage, i))
        if oid not in fonts or trace.raw.FPDFText_IsGenerated(textpage, i):
            continue
        x, y, r, b = textpage.get_charbox(i, loose=False)
        polygon = np.array([trans @ (np.asarray(p) - origin) for p in ((x, y), (r, b), (x, b), (r, y))])
        matches = intersections(polygon, coords)
        if not matches:
            continue
        code = trace.raw.FPDFText_GetUnicode(textpage, i)
        u, v = ctypes.c_double(), ctypes.c_double()
        if not trace.raw.FPDFText_GetCharOrigin(textpage, i, ctypes.byref(u), ctypes.byref(v)):
            raise ValueError("描画した字の原点を決められない")
        mode = trace.raw.FPDFTextObj_GetTextRenderMode(selected[oid])
        solid[(fonts[oid], code, (round(u.value, 5), round(v.value, 5)), tuple(sorted(matches)))].add((oid, mode))
    return solid


def spell(pdf, page_no, fixed, dots, flags):
    l, t = min(p[0] for p in dots), min(p[1] for p in dots)
    r, b = max(p[2] for p in dots), max(p[3] for p in dots)
    window = np.s_[t - 1:b + 1, l - 1:r + 1]
    coords = [((a + c) / 2, (u + v) / 2) for a, u, c, v in dots]
    with closing(trace.pypdfium2.PdfDocument(pdf)) as doc, closing(doc[page_no - 1]) as page:
        with closing(page.get_textpage()) as text:
            objects = list(page.get_objects(filter=[trace.raw.FPDF_PAGEOBJ_TEXT], textpage=text))
            owners = trace.reproduce(page, fixed[window], window, objects)
            fields = visible_glyphs(text, owners, coords, flags)
    fontpage = trace.PdfReader(io.BytesIO(pdf)).pages[page_no - 1]
    used, encoded = set(), []
    font_data = {}
    for (font, code, _, dots_next), source in sorted(fields.items(), key=lambda pair: pair[0][-1]):
        modes = sorted(mode for _, mode in source)
        if modes not in ([0], [0, 1]) or used.intersection(dots_next):
            raise ValueError("同じ点に別の描画が重なった")
        name, digest = font
        if code in SCALARS:
            marker = (name, digest, code)
            if marker not in font_data:
                font_data[marker] = trace.glyph_cid(fontpage, name, digest, code)
            identity = font_data[marker]
        elif code == 0xFFFD:
            mappings = trace.resources(fontpage, name, digest)
            ids = {k for ros, _, data in mappings if ros == ("Adobe", "Japan1") for k, v in data.items() if v == 0xFFFD}
            if ids != {668}:
                raise ValueError("Adobe-Japan1の三点リーダのCIDを一意に裏づけられない")
            code = 0x2026
            identity = {"cid": 668, "codepoint": "2026", "font_data_sha256": digest, "pdfium_font": name}
        else:
            raise ValueError("点線の位置に対象外の字が重なる")
        if SCALARS[code] != len(dots_next) or dots_next != tuple(range(dots_next[0], dots_next[-1] + 1)):
            raise ValueError("描画上の一字と固定画素の点数が合わない")
        used.update(dots_next)
        encoded.append({**identity, "physical_positions": dots_next})
    if used != set(range(len(dots))):
        raise ValueError("固定画素に見える点の全数を出典に結び付けられない")
    return encoded


def cases():
    vision.OUT = audit.OUT
    delivery = vision.DELIVERY = audit.OUT / "delivery"
    vision.READ, vision.START, vision.PACKS = (delivery / name for name in ("received.json", "delivery-started.json", "packages.json"))
    vision.receive = audit.receive
    final = audit.load(audit.HERE / "result.json")
    detail = audit.OUT / "reference-evidence.json"
    if audit.sha(detail) != final["reference_sha256"]:
        raise ValueError("確定済みの監査と異なる")
    prior = audit.load(detail)
    cases, _ = vision.cases()
    missing, control = [], []
    for c in cases:
        row = c["row"]
        record = prior[f"{row['key']}/{row['line_index']}"]["evidence"]
        if not any(token[0] == "trail" for token in vision.MARK.findall(c["answer"]["text"])):
            continue
        if record == "source-location-not-proven":
            missing.append(("held", c))
        elif isinstance(record, dict) and "source-confirmed" in record:
            control.append(("confirmed", c))
    return missing + control[:2]


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("保存した点線の開発結果がある")
    documents, catalog = {}, audit.prior.old.lookup()[1]
    result = []
    for earlier, case in cases():
        row = case["row"]
        key, line = row["key"], row["line_index"]
        filename, digest, no = catalog[key]
        flags = case["assets"]["sha"]
        if filename not in documents:
            documents[filename] = (audit.prior.old.CORPUS / filename).read_bytes()
        blob = documents[filename]
        png = audit.prior.old.CORPUS / "probe-v4/png" / (key + ".png")
        if trace.sha(blob) != digest or flags["pdf_sha256"] != digest or audit.sha(png) != flags["150_dpi"]:
            raise ValueError("固定した描画か元資料が異なる")
        with Image.open(png) as image:
            pixels = np.array(image.convert("RGB"))
        for marker, coord in zip(vision.MARK.finditer(case["answer"]["text"]), case["coordinates"], strict=True):
            if marker[1] != "trail":
                continue
            entry = {"page": key, "line_index": line, "earlier": earlier}
            try:
                dots = dot_groups(case, png, marker, coord)
                proof = spell(blob, no, pixels, dots, flags)
            except (ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
                entry.update(outcome="unproven", reason=str(error)[:130])
            else:
                entry.update(outcome="proven", points=len(dots), rendered_glyphs=len(proof),
                             codepoints=Counter(p["codepoint"] for p in proof), evidence=proof)
            result.append(entry)
            print(key, line, entry["outcome"], entry.get("codepoints") or entry.get("reason"), flush=True)
    OUT.mkdir()
    bound = (Path(__file__), Path(trace.__file__), audit.HERE / "result.json", audit.OUT / "reference-evidence.json")
    audit.save_once(HERE / "result.json", audit.encoded({"scope": "development-only",
                   "inputs": {str(p): audit.sha(p) for p in bound}, "cases": result}))


if __name__ == "__main__":
    main()
