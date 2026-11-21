"""pypdfとAdobeの一次表で、元PDFの点線命令の字種を独立に読み取る。"""

from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request

from pypdf import PdfReader, __version__
from pypdf.generic import ContentStream

HERE = Path(__file__).resolve().parent
BENCH = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16"
CORPUS = BENCH / "corpus"
ADOBE = ("https://raw.githubusercontent.com/adobe-type-tools/cmap-resources/"
         "f5cf3bca7fdfeaceb77aa82847e974f2306c20b4/Adobe-Japan1-7/cid2code.txt")
PAGES = {"defense": (6, 7), "disaster": (8, 15, 133)}
IDENTITY = (1, 0, 0, 1, 0, 0)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def file_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def matrix_product(a, b):
    x, y, z, w, e, f = a
    X, Y, Z, W, E, F = b
    return (x * X + y * Z, x * Y + y * W, z * X + w * Z,
            z * Y + w * W, e * X + f * Z + E, e * Y + f * W + F)


def adobe_table():
    with urllib.request.urlopen(ADOBE, timeout=30) as response:
        data = response.read()
    lines = [line.split("\t") for line in data.decode("ascii").splitlines() if line and not line.startswith("#")]
    names = next(line for line in lines if line[0] == "CID")
    col = names.index("UniJIS-UTF16")
    values = {int(line[0]): line[col] for line in lines if line[0].isdigit()}
    if values[668].lower() != "2026" or values[638].lower() != "30fb":
        raise ValueError("固定したAdobeの横組みの対応表と違う")
    return data, {str(cid): values[cid] for cid in (1, 135, 638, 668)}


def font_mapping(resource):
    encoding = resource.get("/Encoding")
    kind = resource.get("/Subtype")
    if encoding != "/Identity-H" or kind != "/Type0":
        return None
    desc = resource["/DescendantFonts"][0].get_object()
    ros = desc["/CIDSystemInfo"]
    if "/ToUnicode" not in resource:
        return None
    raw = resource["/ToUnicode"].get_data()
    pairs = {}
    for section in re.findall(rb"beginbfchar(.*?)endbfchar", raw, re.S):
        for cid, value in re.findall(rb"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", section):
            pairs[int(cid, 16)] = value.decode("ascii").upper()
    for section in re.findall(rb"beginbfrange(.*?)endbfrange", raw, re.S):
        for first, last, utf in re.findall(rb"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]{4})>", section):
            a, b, dest = int(first, 16), int(last, 16), int(utf, 16)
            for cid in range(a, b + 1):
                pairs[cid] = f"{dest + cid - a:04X}"
    return {"font": str(resource["/BaseFont"]), "embedded_sha256": sha(raw),
            "glyph_codes": pairs, "collection": (ros.get("/Registry"), ros.get("/Ordering")),
            "supplement": int(ros["/Supplement"])}


def content_records(stream, resources, reader, ctm=IDENTITY, depth=0):
    if depth > 8:
        raise ValueError("PDFの図形を安全に追跡できる深さを超える")
    fonts = {str(k): font_mapping(v.get_object()) for k, v in resources.get("/Font", {}).items()}
    pdf_objects = resources.get("/XObject", {})
    saved_ctm, saved_font, marked = [], [], []
    font, text_matrix = None, None
    for operands, operator in stream.operations:
        if operator == b"q":
            saved_ctm.append(ctm)
            saved_font.append(font)
        elif operator == b"Q":
            ctm, font = saved_ctm.pop(), saved_font.pop()
        elif operator == b"cm":
            ctm = matrix_product(tuple(map(float, operands)), ctm)
        elif operator == b"BT" or operator in (b"Td", b"TD", b"T*", b"ET"):
            text_matrix = None
        elif operator == b"Tf":
            font = fonts.get(str(operands[0]))
        elif operator == b"Tm":
            text_matrix = tuple(map(float, operands))
        elif operator == b"Do" and str(operands[0]) in pdf_objects:
            obj = pdf_objects[operands[0]].get_object()
            if obj.get("/Subtype") == "/Form":
                transform = tuple(map(float, obj.get("/Matrix", IDENTITY)))
                marked.extend(content_records(ContentStream(obj, reader), obj.get("/Resources", resources), reader,
                                              matrix_product(transform, ctm), depth + 1))
        elif operator in (b"Tj", b"TJ", b"'", b'"') and font is not None:
            strings = operands[0] if operator == b"TJ" else [operands[-1]]
            payload = b"".join(p.original_bytes for p in strings if hasattr(p, "original_bytes"))
            if len(payload) % 2:
                raise ValueError("Identity-Hで2バイトでない符号")
            cids = [int.from_bytes(payload[k:k + 2], "big") for k in range(0, len(payload), 2)]
            if cids and text_matrix is not None:
                table = font["glyph_codes"]
                ellipsis = (font["collection"] == ("Adobe", "Japan1") and cids[0] == 1
                            and len(cids) > 1 and set(cids[1:]) == {668} and table.get(668) == "FFFD")
                explicit = Counter(table[j] for j in cids if table.get(j) in ("2022", "30FB"))
                if ellipsis or explicit:
                    marked.append({"matrix": matrix_product(text_matrix, ctm), "font": font["font"],
                                   "embedded_sha256": font["embedded_sha256"], "level": depth,
                                   "ellipsis_cid_668": len(cids) - 1 if ellipsis else 0,
                                   "leading_cid": cids[0], "collection": font["collection"],
                                   "explicit_point_codepoints": explicit})
            text_matrix = None
    return marked


def main():
    target = HERE / "independent-pdf-commands-v2.json"
    if target.exists():
        raise FileExistsError("独立の命令抽出を上書きできない")
    adobe, mapping = adobe_table()
    pages, sums, inputs = {}, {}, {}
    for pub, numbers in PAGES.items():
        truth = file_json(CORPUS / "public" / (pub + ".truth.json"))
        pdf = (CORPUS / truth["file"]).read_bytes()
        if sha(pdf) != truth["pdf_sha256"]:
            raise ValueError("固定した元PDFが違う")
        inputs[pub] = sha(pdf)
        reader = PdfReader(io.BytesIO(pdf))
        for num in numbers:
            page = reader.pages[num - 1]
            cms = page.get_contents()
            if cms is None:
                raise ValueError("指定の頁に描画命令がない")
            records = content_records(cms, page["/Resources"], reader)
            key = f"{pub}-p{num:04d}"
            pages[key] = records
            sums[key] = {"commands_with_ellipsis": sum(bool(r["ellipsis_cid_668"]) for r in records),
                         "ellipsis_cids": sum(r["ellipsis_cid_668"] for r in records),
                         "explicit_point_codes": sum((Counter(r["explicit_point_codepoints"]) for r in records), Counter())}
    with target.open("x", encoding="utf-8") as stream:
        json.dump({"scope": "independent-source-command-check", "pypdf_version": __version__, "pdf_sha256": inputs,
                   "script_sha256": sha(Path(__file__).read_bytes()),
                   "adobe": {"url": ADOBE, "sha256": sha(adobe), "unicode_utf16_h": mapping},
                   "counts": sums, "commands": pages}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(sums, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
