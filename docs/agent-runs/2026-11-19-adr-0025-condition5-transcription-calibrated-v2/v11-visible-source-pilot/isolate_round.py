"""塗りと輪郭を残した隔離描画で、丸印の画素を再現する開発試験。"""

import argparse
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, DictionaryObject, NameObject, NumberObject

import commands
import paint_layers as layer

HERE = Path(__file__).resolve().parent
PDF = "defense-white-paper-2025.pdf"
KEY = "defense-p0107"


def rewrite(data, page_no, chosen=None):
    writer = PdfWriter()
    page = writer.add_page(PdfReader(io.BytesIO(data)).pages[page_no - 1])
    resource_key, object_key = map(NameObject, ("/Resources", "/XObject"))
    keys = []

    def edited(stream, resource, path=(), mode=0):
        contents = ContentStream(stream, writer)
        elements, modes = [], []
        replacements = DictionaryObject(resource.get(object_key, DictionaryObject()).get_object())
        if object_key in resource:
            resource[object_key] = replacements
        for i, (operands, operator) in enumerate(contents.operations):
            if operator == b"q":
                modes.append(mode)
            elif operator == b"Q":
                mode = modes.pop()
            elif operator == b"Tr":
                mode = int(operands[0])
            if operator in layer.SHOW_TEXT:
                position = path + (i,)
                keys.append(position)
                if chosen is not None and position not in chosen and mode not in (3, 7):
                    elements.append(([NumberObject(7 if mode >= 4 else 3)], b"Tr"))
                    elements.append((operands, operator))
                    elements.append(([NumberObject(mode)], b"Tr"))
                    continue
            elif operator == b"Do":
                former = replacements[operands[0]].get_object()
                if former.get("/Subtype") == "/Form":
                    if len(path) >= 12:
                        raise ValueError("入れ子の描画を隔離できない")
                    nested = DictionaryObject(former.get(resource_key, resource).get_object())
                    local = edited(former, nested, path + (i,), mode)
                    rewritten = local.flate_encode()
                    for name, value in former.items():
                        if name not in {"/Filter", "/Length", "/DecodeParms", "/Resources"}:
                            rewritten[NameObject(name)] = value
                    rewritten[resource_key] = nested
                    label = NameObject("/_adr0025Form" + "_".join(map(str, path + (i,))))
                    if label in replacements:
                        raise ValueError("隔離のための名前は元の資料に存在しないこと")
                    replacements[label] = writer._add_object(rewritten)
                    operands = [label]
            elements.append((operands, operator))
        if modes:
            raise ValueError("PDFの描画状態の境界を確認できない")
        contents.operations = elements
        return contents

    source_res = page[resource_key]
    page[resource_key] = DictionaryObject(source_res)
    page.replace_contents(edited(page.get_contents(), page[resource_key]))
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue(), tuple(keys)


def painted_points(data):
    doc = PdfReader(io.BytesIO(data))
    page = doc.pages[0]
    commands.old.cid_width = commands.cid_width
    commands.old.raw.font_mapping = commands.font_mapping
    return commands.old.spacing(page.get_contents(), page["/Resources"], doc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    destination = parser.parse_args().output
    source = layer.CORPUS / PDF
    digest = layer.load(layer.OUT / "source-proof.json")["evidence"][KEY]["pdf_sha256"]
    commands_seen = layer.load(layer.OUT / "round-overlap.json")
    case = next(r for r in commands_seen["cases"] if r["page"] == KEY)
    box = case["resolved"][0]["box"]
    blob = source.read_bytes()
    image = layer.CORPUS / "probe-v4/png" / (KEY + ".png")
    if layer.sha(blob) != digest or layer.sha(image.read_bytes()) != layer.load(layer.CORPUS / "probe-v4/manifest.json")[KEY]["png_sha256"]:
        raise ValueError("固定したPDF・PNGに一致しない")
    with Image.open(image) as opened:
        fixed = np.array(opened.convert("RGB"))
    l, t, r, b = box
    region = np.s_[t - 2:b + 2, l - 2:r + 2]
    around = np.s_[t - 40:b + 40, l - 40:r + 40]
    if not np.array_equal(layer.render_pixels(blob, 106), fixed):
        raise ValueError("元PDFの描画で固定の画素を再現できない")
    written, operators = rewrite(blob, 107)
    baseline = layer.render_pixels(written, 0)
    if baseline.shape != fixed.shape or not np.array_equal(baseline[around], fixed[around]):
        raise ValueError("対照の隔離描画で丸印と周囲の固定画素を再現できない")
    blank_pdf, _ = rewrite(blob, 107, set())
    blank = layer.render_pixels(blank_pdf, 0)[region]
    if np.any(blank < 254):
        raise ValueError("丸印の位置に文字命令以外の描画がある")
    renders = 0

    def render(group):
        nonlocal renders
        data, found = rewrite(blob, 107, set(group))
        if found != operators:
            raise ValueError("描画命令の順が変化")
        renders += 1
        return data, layer.render_pixels(data, 0)[region]

    body = []
    queue = [operators]
    while queue:
        batch = queue.pop()
        if np.array_equal(render(batch)[1], blank):
            continue
        if len(batch) == 1:
            body.append(batch[0])
        else:
            split = len(batch) // 2
            queue.extend((batch[:split], batch[split:]))
    if not body:
        raise ValueError("丸印の描画命令を単離できない")
    positive, recaptured = render(body)
    complementary, negative = render(set(operators) - set(body))
    if not np.array_equal(recaptured, fixed[region]) or not np.array_equal(negative, blank):
        raise ValueError("選んだ命令とその他の命令を切り分けられない")
    permitted = [op for op in painted_points(positive) if op["text_rendering_mode"] not in (3, 7)]
    outside = painted_points(complementary)
    if len(permitted) != len(body) or any(op["positioned_points"] != permitted[0]["positioned_points"] for op in permitted):
        raise ValueError("同じ文字命令の塗りと輪郭として確認できない")
    anchors, = [permitted[0]["positioned_points"]]
    if len(anchors) != 1 or anchors[0][:2] != [638, "30FB"]:
        raise ValueError("Adobe-Japan1の中黒の描画として確認できない")
    proof = {"scope": "development-only", "key": KEY, "line_index": case["line_index"], "box": box,
             "isolated_operators": sorted(body), "operator_total": len(operators), "renders": renders,
             "baseline_equal_fixed_page": np.array_equal(baseline, fixed),
             "baseline_equal_fixed_context": True,
             "fixed_window_sha256": layer.sha(fixed[region].tobytes()), "source_mark": {"cid": 638, "codepoint": "30FB"},
             "isolated_pdf_sha256": layer.sha(positive), "complement_no_ink": True, "complement_pdf_sha256": layer.sha(complementary),
             "complement_point_commands": len(outside), "source_pdf_sha256": digest}
    with destination.open("x", encoding="utf-8") as out:
        json.dump(proof, out, ensure_ascii=False, indent=2)
    print(proof, flush=True)


if __name__ == "__main__":
    main()
