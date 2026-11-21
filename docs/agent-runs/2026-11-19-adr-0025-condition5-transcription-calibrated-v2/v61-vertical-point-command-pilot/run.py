"""縦組の中黒を一字ずつ非表示にして、元のCIDと固定画素の対応を確かめる。"""

from contextlib import closing
import io
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ByteStringObject, NumberObject
from pypdfium2 import PdfDocument

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
import official

core, previous = official.core, official.core.previous
strict = previous.module("unique_round_at_high_resolution", official.audit.draft.raster_file)
proof = strict.implementation.glyphs
trace = proof.trace
CODEPOINT = 0x30FB
CID = 638


def matching_fonts(page, description):
    name, sha = description
    matches = set()
    for label, lookup in page["/Resources"].get("/Font", {}).items():
        font = lookup.get_object()
        if font.get("/Encoding") != "/Identity-V" or "/ToUnicode" in font or "/DescendantFonts" not in font:
            continue
        descendant = font["/DescendantFonts"][0].get_object()
        if str(descendant.get("/BaseFont")).lstrip("/") != name:
            continue
        descriptor = descendant["/FontDescriptor"]
        streams = (descriptor[key].get_data() for key in ("/FontFile", "/FontFile2", "/FontFile3") if key in descriptor)
        if not any(trace.sha(s) == sha for s in streams):
            continue
        ros = descendant["/CIDSystemInfo"]
        if (str(ros.get("/Registry")), str(ros.get("/Ordering"))) != ("Adobe", "Japan1"):
            raise ValueError("縦組の中黒をAdobe-Japan1の字として確認できない")
        matches.add(str(label))
    return matches


def candidates(page, fonts):
    found, state = [], []
    font, mode = None, 0
    encoded = CID.to_bytes(2, "big")
    for number, (operands, op) in enumerate(page.get_contents().operations):
        if op == b"q":
            state.append((font, mode))
        elif op == b"Q":
            font, mode = state.pop()
        elif op == b"Tf":
            font = str(operands[0])
        elif op == b"Tr":
            mode = int(operands[0])
        elif op == b"Tj" and font in fonts and mode == 0:
            payload = operands[0].original_bytes
            if len(payload) % 2:
                raise ValueError("縦組のCIDが2バイト境界に対応しない")
            for offset in range(0, len(payload), 2):
                if payload[offset:offset + 2] == encoded:
                    found.append((number, offset, font))
    if state:
        raise ValueError("元資料の描画状態を一意に追えない")
    return found


def render(content, number, change=None):
    writer = PdfWriter()
    page = writer.add_page(PdfReader(io.BytesIO(content)).pages[number - 1])
    if change is not None:
        index, offset, _ = change
        stream = page.get_contents()
        ops = stream.operations
        words, operation = ops[index]
        bits = words[0].original_bytes
        if operation != b"Tj" or bits[offset:offset + 2] != CID.to_bytes(2, "big"):
            raise ValueError("非表示にする一つの描画命令が異なる")
        before, target, after = bits[:offset], bits[offset:offset + 2], bits[offset + 2:]
        steps = []
        if before:
            steps.append(([ByteStringObject(before)], b"Tj"))
        steps.extend([([NumberObject(3)], b"Tr"), ([ByteStringObject(target)], b"Tj"), ([NumberObject(0)], b"Tr")])
        if after:
            steps.append(([ByteStringObject(after)], b"Tj"))
        ops[index:index + 1] = steps
        stream.operations = ops
        page.replace_contents(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    with closing(PdfDocument(buffer.getvalue())) as document, closing(document[0]) as item:
        with closing(item.render(scale=150 / 72)) as pdf:
            return np.array(pdf.to_pil().convert("RGB"))


def prove(case, source_450, hash_450, source_150, pdf, hash_pdf, page_number):
    row, assets = case["row"], case["assets"]
    flags = assets["sha"]
    bound = assets["source_view"]["views"][1]["target_rectangle"]
    marker = previous.ref.MARK.findall(case["answer"]["text"])
    coords = case["coordinates"]
    if row["allocation_axis"] != "x" or len(coords) != 1 or len(marker) != 1 or marker[0][0] != "round":
        return None
    if (previous.sha(source_450) != hash_450 or previous.sha(source_150) != flags["150_dpi"]
            or trace.sha(pdf) != hash_pdf or flags["pdf_sha256"] != hash_pdf):
        raise ValueError("二票の固定画素と元PDFの来歴が異なる")
    with Image.open(source_450) as image:
        high, (l, t, r, b) = strict.physical(np.array(image.convert("L")), bound, row["box"], coords[0])
    if min(l, t) < 1:
        return None
    with Image.open(source_150) as image:
        fixed = np.array(image.convert("RGB"))
    roi = np.s_[t - 1:b + 1, l - 1:r + 1]
    centers = [((l + r) / 2, (t + b) / 2)]
    with closing(PdfDocument(pdf)) as doc, closing(doc[page_number - 1]) as page:
        with closing(page.get_textpage()) as text:
            objs = list(page.get_objects(filter=[trace.raw.FPDF_PAGEOBJ_TEXT], textpage=text))
            owners = trace.reproduce(page, fixed[roi], roi, objs)
            glyphs = proof.old.visible_glyphs(text, owners, centers, flags)
    if len(owners) != 1 or len(glyphs) != 1:
        return None
    ((font, scalar, origin, indexes), methods), = glyphs.items()
    if scalar != CODEPOINT or indexes != (0,) or [mode for _, mode in methods] != [0]:
        return None
    if trace.POINT_CIDS.get(CID) != CODEPOINT:
        raise ValueError("登録済みの中黒のCIDと符号が異なる")
    source = PdfReader(io.BytesIO(pdf)).pages[page_number - 1]
    ids = matching_fonts(source, font)
    if not ids:
        return None
    commands = candidates(source, ids)
    if not commands or not np.array_equal(fixed, render(pdf, page_number)):
        return None
    same, neutral = [], []
    for cmd in commands:
        changed = render(pdf, page_number, cmd)
        difference = np.any(fixed != changed, axis=2)
        overlap = int(difference[roi].sum())
        if not overlap:
            neutral.append({"operator": cmd[0], "offset": cmd[1], "changed_pixels": int(difference.sum())})
        elif overlap == int(difference.sum()) and np.all(changed[roi] == changed[roi][0, 0]):
            same.append({"operator": cmd[0], "offset": cmd[1], "font_resource": cmd[2],
                         "changed_pixels": overlap, "without_point_sha256": trace.sha(changed[roi].tobytes())})
        else:
            return None
    if len(same) != 1:
        return None
    detail = {"pdf_sha256": hash_pdf, "same_page_150_dpi": True, "physical_450_box": high, "physical_150_box": (l, t, r, b),
              "source_character_origin": origin, "two_read_positions": coords, "font_sha256": font[1], "font": font[0],
              "cid": CID, "codepoint": f"{CODEPOINT:04X}", "source_command": same[0], "controls": neutral}
    return {"status": "readable", "text": previous.ref.NORMALIZE(previous.ref.MARK.sub(chr(CODEPOINT), case["answer"]["text"]))}, detail


def main():
    output = HERE / "result.json"
    if output.exists():
        raise FileExistsError("縦組の中黒の開発で確定した証拠を上書きしない")
    core.verify_methods()
    old = official.audit.HERE / "result.json"
    delivery = core.OUT / "delivery"
    shipment = core.transport.check(delivery, core.sha(delivery / "packages.json"))
    cases, _ = core.image_cases(shipment, core.old_sessions())
    catalog = previous.packets.old.lookup()[1]
    selected = {("kanpo1828-p1-p0001", 117): True, ("defense-p0089", 88): False}
    records = []
    for case in cases:
        row = case["row"]
        key = row["key"], row["line_index"]
        if key not in selected:
            continue
        relative, digest, n = catalog[key[0]]
        source = core.CORPUS / "probe-v4/png" / (key[0] + ".png")
        high = case["assets"]["source_view"]["views"][1]
        raw = next(v["image"] for v in high["images"] if v["kind"] == "plain")
        try:
            found = prove(case, delivery / "source-assets" / raw, shipment.document["source_assets"][raw], source,
                          (core.CORPUS / relative).read_bytes(), digest, n)
        except ValueError as e:
            if selected[key]:
                raise
            found = None
            print("対照の保留理由", str(e), flush=True)
        if bool(found) != selected[key]:
            raise ValueError("許可された符号と対象外の対照を区別できない")
        record = {"page": key[0], "line_index": key[1], "confirmed": bool(found)}
        if found:
            value, detail = found
            if len(detail["controls"]) != 3 or value["text"] != "\u30fb":
                raise ValueError("同じCIDを別の位置に描いた3対照から区別できない")
            record["evidence"] = detail
        records.append(record)
        print(key[0], key[1], bool(found), flush=True)
    if len(records) != 2:
        raise ValueError("開発の対照を再現できない")
    docs = (Path(__file__), HERE / "protocol.md", old, delivery / "packages.json", delivery / "received.json",
            Path(strict.__file__))
    core.save_once(output, core.encoded({"scope": "development-only", "cases": records,
                                         "inputs": {str(f): core.sha(f) for f in docs}}))


if __name__ == "__main__":
    main()
