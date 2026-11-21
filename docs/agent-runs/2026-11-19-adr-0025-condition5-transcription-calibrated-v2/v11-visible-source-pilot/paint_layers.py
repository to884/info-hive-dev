"""行頭の丸印にテキストの描画が関与するかを固定画素で調べる。"""

from contextlib import closing
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter, __version__
from pypdf.generic import ContentStream, NameObject
from pypdfium2 import PdfDocument

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parents[2] / "research/adr-0025-condition5-2026-11-16/corpus"
ARCHIVE = CORPUS / "reference-audit-v10"
OUT = CORPUS / "reference-v11-visible-source-pilot"
CASES = {("defense-p0107", 22): (-2, 3, 12, 17),
         ("wp-summary-p0002", 13): (-3, 3, 23, 27),
         ("wp-summary-p0010", 34): (-2, 6, 4, 12)}
SHOW_TEXT = {b"Tj", b"TJ", b"'", bytes((34,))}


def load(path):
    return json.loads(path.read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def suppress(content, resources, writer, removed, seen):
    stream = ContentStream(content, writer)
    keep, counts = [], {"text": 0, "image": 0}
    objects = resources.get("/XObject", {})
    if hasattr(objects, "get_object"):
        objects = objects.get_object()
    for operands, operator in stream.operations:
        if operator in SHOW_TEXT:
            counts["text"] += 1
            if "text" in removed:
                continue
        if operator == b"INLINE IMAGE":
            counts["image"] += 1
            if "image" in removed:
                continue
        if operator == b"Do":
            obj = objects[operands[0]].get_object()
            if obj.get("/Subtype") == "/Image":
                counts["image"] += 1
                if "image" in removed:
                    continue
            elif obj.get("/Subtype") == "/Form" and id(obj) not in seen:
                seen.add(id(obj))
                inherited = obj.get("/Resources", resources).get_object()
                nested, changes = suppress(obj, inherited, writer, removed, seen)
                for k, v in changes.items():
                    counts[k] += v
                if removed:
                    new = nested.flate_encode()
                    for k, v in obj.items():
                        if k not in {"/Filter", "/Length", "/DecodeParms"}:
                            new[NameObject(k)] = v
                    objects[operands[0]] = writer._add_object(new)
        keep.append((operands, operator))
    stream.operations = keep
    return stream, counts


def rewrite(blob, number, removed):
    original = PdfReader(io.BytesIO(blob))
    writer = PdfWriter()
    page = writer.add_page(original.pages[number - 1])
    contents, seen = page.get_contents(), set()
    rendered, counts = suppress(contents, page["/Resources"], writer, removed, seen)
    page.replace_contents(rendered)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue(), counts


def render_pixels(data, index):
    with closing(PdfDocument(data)) as doc, closing(doc[index]) as page:
        with closing(page.render(scale=150 / 72)) as bitmap:
            return np.array(bitmap.to_pil().convert("RGB"))


def main():
    pngs = load(CORPUS / "probe-v4/manifest.json")
    selected = {(r["key"], r["line_index"]): r for r in load(ARCHIVE / "selection.json")["selected"]}
    source_requests = set(load(ARCHIVE / "source-requests.json")["pages"])
    catalog = {}
    for path in (CORPUS / "public").glob("*.truth.json"):
        authority = load(path)
        for page in authority["pages"]:
            catalog[f"{authority['name']}-p{page['page']:04d}"] = (authority["file"], authority["pdf_sha256"], page["page"])
    results = []
    for k, part in CASES.items():
        key, idx = k
        if key not in source_requests:
            raise ValueError("丸印の元の照合依頼にない")
        filename, expected, page = catalog[key]
        original = (CORPUS / filename).read_bytes()
        png = CORPUS / "probe-v4/png" / (key + ".png")
        if sha(original) != expected or sha(png.read_bytes()) != pngs[key]["png_sha256"]:
            raise ValueError("固定した元の資料と画像が異なる")
        with Image.open(png) as im:
            fixed = np.array(im.convert("RGB"))
        x, y = selected[k]["box"][:2]
        l, t, r, b = part
        region = np.s_[y + t:y + b, x + l:x + r]
        untouched = render_pixels(original, page - 1)
        if not np.array_equal(untouched, fixed):
            raise ValueError("元PDFの描画が固定画像と異なる")
        sets = {"all": set(), "no-text": {"text"}, "no-image": {"image"}, "no-text-or-image": {"text", "image"}}
        outcome = {}
        for name, removed in sets.items():
            updated, commands = rewrite(original, page, removed)
            pixels = render_pixels(updated, 0)
            if pixels.shape != fixed.shape:
                raise ValueError("隔離描画で元ページの寸法が変わった")
            window = pixels[region]
            outcome[name] = {"removed": sorted(removed), "commands": commands,
                             "equal_fixed_page": np.array_equal(pixels, fixed),
                             "equal_fixed_window": np.array_equal(window, fixed[region]),
                             "dark_pixels": int((window.mean(axis=2) < 192).sum()),
                             "window_sha256": sha(window.tobytes())}
        if not outcome["all"]["equal_fixed_window"]:
            print(f"{key}: 書き出した対照の丸印付近が一致しない", flush=True)
        results.append({"page": key, "line_index": idx, "window": part, "layers": outcome})
    report = {"scope": "development-only-paint-isolation", "pypdf": __version__,
              "script_sha256": sha(Path(__file__).read_bytes()), "rows": results}
    with (OUT / "paint-layers.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    for r in results:
        print(r["page"], {k: v["dark_pixels"] for k, v in r["layers"].items()}, flush=True)


if __name__ == "__main__":
    main()
