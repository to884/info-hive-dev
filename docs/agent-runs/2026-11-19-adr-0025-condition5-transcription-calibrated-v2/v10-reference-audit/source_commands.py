"""画素だけの票と別に、監査対象の元PDFから丸印・点線の描画命令を確かめる。"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from pypdf import PdfReader, __version__
from pypdf.generic import ContentStream

HERE = Path(__file__).resolve().parent
EXTRACTOR = HERE.parent / "dot-layout-v2/independent-pdf-commands.py"
spec = importlib.util.spec_from_file_location("published_pdf_commands", EXTRACTOR)
raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw)
CORPUS = raw.CORPUS


def cid_width(font, cid):
    if cid is None or "/DescendantFonts" not in font:
        return None
    descendant = font["/DescendantFonts"][0].get_object()
    widths = descendant.get("/W", ())
    i = 0
    while i < len(widths):
        first = int(widths[i])
        item = widths[i + 1]
        if isinstance(item, list):
            if first <= cid < first + len(item):
                return float(item[cid - first])
            i += 2
        else:
            last = int(item)
            if first <= cid <= last:
                return float(widths[i + 2])
            i += 3
    return float(descendant.get("/DW", 1000))


def shifted(matrix, x, y):
    return raw.matrix_product((1, 0, 0, 1, x, y), matrix)


def rectangle(matrix, x0, y0, x1, y1):
    a, b, c, d, e, f = matrix
    if b or c:
        return None
    xs = a * x0 + e, a * x1 + e
    ys = d * y0 + f, d * y1 + f
    return min(xs), min(ys), max(xs), max(ys)


def luminance(red, green, blue):
    return .2126 * red + .7152 * green + .0722 * blue


def fill_color(space, components):
    if space == "/DeviceN-ProcessBlack" and len(components) == 1:
        return 1 - float(components[0])
    if space == "/DeviceGray" and len(components) == 1:
        return float(components[0])
    if space == "/DeviceRGB" and len(components) == 3:
        return luminance(*map(float, components))
    if space == "/DeviceCMYK" and len(components) == 4:
        c, m, y, k = map(float, components)
        return luminance((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return None


def color_space(resources, operand):
    name = str(operand)
    if name in ("/DeviceGray", "/DeviceRGB", "/DeviceCMYK"):
        return name
    doc = resources.get("/ColorSpace", {}).get(operand)
    doc = doc.get_object() if doc is not None else None
    if isinstance(doc, list) and len(doc) == 2 and doc[0] == "/ICCBased":
        profile = doc[1].get_object()
        return profile.get("/Alternate", {1: "/DeviceGray", 3: "/DeviceRGB", 4: "/DeviceCMYK"}.get(profile["/N"]))
    if (isinstance(doc, list) and len(doc) == 5 and doc[0] == "/DeviceN"
            and doc[1] == ["/Black"] and doc[2] == "/DeviceCMYK"):
        process = doc[4].get_object().get("/Process")
        if process is not None:
            process = process.get_object()
            if (process.get("/ColorSpace") == "/DeviceCMYK"
                    and process.get("/Components") == ["/Cyan", "/Magenta", "/Yellow", "/Black"]):
                return "/DeviceN-ProcessBlack"
    return str(doc) if doc in ("/DeviceGray", "/DeviceRGB", "/DeviceCMYK") else None


def spacing(stream, resources, document, ctm=raw.IDENTITY, depth=0, inherited=None):
    if depth > 8:
        raise ValueError("描画の資源が循環しているか深すぎる")
    fonts = {str(name): (font, raw.font_mapping(font))
             for name, ref in resources.get("/Font", {}).items() if (font := ref.get_object())}
    objects = resources.get("/XObject", {})
    graphic_settings = resources.get("/ExtGState", {})
    initial = {"font": (None, None), "size": 1.0, "char": 0.0, "stretch": 1.0, "leading": 0.0,
               "mode": 0, "space": "/DeviceGray", "fill": 0.0, "opacity_proven": True, "clips": (), "clip_known": True}
    state, stack = initial if inherited is None else inherited.copy(), []
    position = text_line = raw.IDENTITY
    pending_clip, path = False, []
    marked = []
    for operands, operator in stream.operations:
        if operator == b"q":
            stack.append((ctm, state.copy()))
        elif operator == b"Q":
            ctm, state = stack.pop()
        elif operator == b"cm":
            ctm = raw.matrix_product(tuple(map(float, operands)), ctm)
        elif operator == b"BT":
            position = text_line = raw.IDENTITY
        elif operator == b"Tm":
            position = text_line = tuple(map(float, operands))
        elif operator in (b"Td", b"TD"):
            x, y = map(float, operands)
            position = text_line = shifted(text_line, x, y)
            if operator == b"TD":
                state["leading"] = -y
        elif operator == b"TL":
            state["leading"] = float(operands[0])
        elif operator == b"T*":
            position = text_line = shifted(text_line, 0, -state["leading"])
        elif operator == b"Tf":
            state["font"] = fonts.get(str(operands[0]), (None, None))
            state["size"] = float(operands[1])
        elif operator == b"Tc":
            state["char"] = float(operands[0])
        elif operator == b"Tz":
            state["stretch"] = float(operands[0]) / 100
        elif operator == b"Tr":
            state["mode"] = int(operands[0])
            if state["mode"] >= 4:
                state["clip_known"] = False
        elif operator == b"g":
            state["space"], state["fill"] = "/DeviceGray", fill_color("/DeviceGray", operands)
        elif operator == b"rg":
            state["space"], state["fill"] = "/DeviceRGB", fill_color("/DeviceRGB", operands)
        elif operator == b"k":
            state["space"], state["fill"] = "/DeviceCMYK", fill_color("/DeviceCMYK", operands)
        elif operator == b"cs":
            state["space"] = color_space(resources, operands[0])
            state["fill"] = None
        elif operator in (b"sc", b"scn"):
            state["fill"] = fill_color(state["space"], operands)
        elif operator == b"gs":
            graph = graphic_settings.get(operands[0])
            if graph is None:
                state["opacity_proven"] = False
            else:
                graph = graph.get_object()
                if (("/ca" in graph and float(graph["/ca"]) < .99) or graph.get("/SMask") not in (None, "/None")
                        or graph.get("/BM") not in (None, "/Normal", "/Compatible")):
                    state["opacity_proven"] = False
        elif operator == b"re":
            x, y, width, height = map(float, operands)
            path.append(rectangle(ctm, x, y, x + width, y + height))
        elif operator in (b"m", b"l", b"c", b"v", b"y"):
            path.append(None)
        elif operator in (b"W", b"W*"):
            pending_clip = True
        elif operator in (b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"n"):
            if pending_clip:
                if len(path) == 1 and path[0] is not None:
                    state["clips"] += (path[0],)
                else:
                    state["clip_known"] = False
            pending_clip, path = False, []
        elif operator == b"Do" and str(operands[0]) in objects:
            obj = objects[operands[0]].get_object()
            if obj.get("/Subtype") == "/Form":
                matrix = tuple(map(float, obj.get("/Matrix", raw.IDENTITY)))
                transform = raw.matrix_product(matrix, ctm)
                box = rectangle(transform, *map(float, obj["/BBox"])) if "/BBox" in obj else None
                nested_state = state.copy()
                if box is None:
                    nested_state["clip_known"] = False
                else:
                    nested_state["clips"] += (box,)
                nested = spacing(ContentStream(obj, document), obj.get("/Resources", resources), document,
                                 transform, depth + 1, nested_state)
                marked.extend(nested)
        elif operator in (b"Tj", b"TJ", b"'", b'"'):
            if operator in (b"'", b'"'):
                position = text_line = shifted(text_line, 0, -state["leading"])
            if operator == b'"':
                state["char"] = float(operands[1])
            font, props = state["font"]
            if props is None:
                continue
            values = operands[0] if operator == b"TJ" else [operands[-1]]
            cursor, dots, glyphs = 0.0, [], []
            for value in values:
                if not hasattr(value, "original_bytes"):
                    cursor -= float(value) * state["size"] * state["stretch"] / 1000
                    continue
                data = value.original_bytes
                if len(data) % 2:
                    raise ValueError("同じIdentity-Hの命令で奇数バイトの符号")
                for i in range(0, len(data), 2):
                    cid = int.from_bytes(data[i:i + 2], "big")
                    glyphs.append(cid)
                    width = cid_width(font, cid) / 1000 * state["size"] * state["stretch"]
                    code = props["glyph_codes"].get(cid)
                    if code in ("2022", "30FB") or (cid == 668 and props["collection"] == ("Adobe", "Japan1")):
                        dots.append([cid, code, cursor, width])
                    cursor += width + state["char"] * state["stretch"]
            if dots:
                matrix = raw.matrix_product(position, ctm)
                collection = props["collection"]
                codes = props["glyph_codes"]
                ellipses = sum(cid == 668 for cid, _, _, _ in dots) if collection == ("Adobe", "Japan1") else 0
                marked.append({"matrix": matrix, "font": props["font"], "font_size": state["size"],
                               "embedded_sha256": props["embedded_sha256"], "collection": collection,
                               "explicit_point_codepoints": Counter(code for _, code, _, _ in dots if code in ("2022", "30FB")),
                               "leading_cid": glyphs[0], "leading_explicit_unicode": codes.get(glyphs[0]),
                               "ellipsis_cid_668": ellipses, "positioned_points": dots, "text_rendering_mode": state["mode"],
                               "visible_fill_proven": (state["mode"] == 0 and state["opacity_proven"] and state["clip_known"]
                                                       and state["fill"] is not None and state["fill"] < .78),
                               "clips": state["clips"], "color_space": state["space"], "luminance": state["fill"],
                               "clip_known": state["clip_known"], "opacity_proven": state["opacity_proven"]})
            position = shifted(position, cursor, 0)
    return marked


def run(selected, destination):
    cases = json.loads(selected.read_text(encoding="utf-8"))
    if not isinstance(cases["pages"], list) or len(set(cases["pages"])) != len(cases["pages"]):
        raise ValueError("出典を調べる頁のリストが違う")
    docs = {}
    for path in (CORPUS / "public").glob("*.truth.json"):
        authority = raw.file_json(path)
        for page in authority["pages"]:
            key = f"{authority['name']}-p{page['page']:04d}"
            docs[key] = authority["file"], authority["pdf_sha256"], page["page"]
    pdfs, facts = {}, {}
    for key in cases["pages"]:
        file, expected, number = docs[key]
        if file not in pdfs:
            blob = (CORPUS / file).read_bytes()
            if raw.sha(blob) != expected:
                raise ValueError("固定された公開の元PDFとは異なる")
            pdfs[file] = PdfReader(io.BytesIO(blob))
        pdf = pdfs[file]
        page = pdf.pages[number - 1]
        contents = page.get_contents()
        try:
            operations = spacing(contents, page["/Resources"], pdf) if contents is not None else []
        except (ValueError, KeyError, AttributeError, TypeError, IndexError) as error:
            facts[key] = {"pdf_sha256": expected, "unsupported": type(error).__name__, "commands": []}
        else:
            facts[key] = {"pdf_sha256": expected, "commands": operations}
    adobe_bytes, crosswalk = raw.adobe_table()
    proof = {"scope": "independent-audit-pdf-drawing-commands", "request_sha256": raw.sha(selected.read_bytes()),
             "pypdf": __version__, "table": {"source": raw.ADOBE, "sha256": raw.sha(adobe_bytes), "subset": crosswalk},
             "methods": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), EXTRACTOR)},
             "evidence": facts}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(proof, stream, ensure_ascii=False, indent=2)
    print(len(facts), "頁の補助資料を読み取った", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    run(args.requests, args.artifacts)
