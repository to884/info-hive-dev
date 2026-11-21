"""v10で間接参照の幅が失敗した公開PDFを検証する開発用の抽出器。"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
FILE = HERE.parent / "v10-reference-audit/source_commands.py"
spec = importlib.util.spec_from_file_location("fixed_source_commands", FILE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
original_font_mapping = old.raw.font_mapping


def dereference(value):
    return value.get_object() if hasattr(value, "get_object") else value


def cid_width(font, cid):
    if cid is None or "/DescendantFonts" not in font:
        return None
    desc = dereference(dereference(font["/DescendantFonts"])[0])
    values = dereference(desc.get("/W", ()))
    at = 0
    while at < len(values):
        first, item = (dereference(v) for v in values[at:at+2])
        if isinstance(item, list):
            if first <= cid < first + len(item):
                return float(dereference(item[cid - first]))
            at += 2
        else:
            if first <= cid <= item:
                return float(dereference(values[at+2]))
            at += 3
    return float(dereference(desc.get("/DW", 1000)))


def font_mapping(font):
    mapping = original_font_mapping(font)
    if mapping is not None:
        mapping["collection"] = tuple(str(dereference(v)) for v in mapping["collection"])
    return mapping


def drawing_key(op):
    return (op["font"], op["embedded_sha256"], tuple(op["collection"]), tuple(op["matrix"]), op["font_size"],
            op["leading_cid"], op["leading_explicit_unicode"], op["ellipsis_cid_668"],
            tuple(sorted(op["explicit_point_codepoints"].items())),
            tuple(tuple(point) for point in op["positioned_points"]), tuple(tuple(clip) for clip in op["clips"]),
            op["clip_known"])


def fold_drawings(commands):
    grouped = {}
    for op in commands:
        if op["text_rendering_mode"] in (3, 7):
            continue
        key = drawing_key(op)
        current = grouped.get(key)
        if current is None or (op["visible_fill_proven"] and not current["visible_fill_proven"]):
            grouped[key] = op
    return list(grouped.values())


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--request",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    args = cli.parse_args()
    old.cid_width = cid_width
    old.raw.font_mapping = font_mapping
    with tempfile.TemporaryDirectory(prefix="adr0025-indirect-font-widths-") as directory:
        generated = Path(directory) / "source.json"
        old.run(args.request,generated)
        proof = json.loads(generated.read_text(encoding="utf-8"))
    for page in proof["evidence"].values():
        page["original_command_count"] = len(page["commands"])
        page["commands"] = fold_drawings(page["commands"])
    proof["scope"] = "development-v11-visible-source"
    proof["methods"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.out.open("x",encoding="utf-8") as archive:
        json.dump(proof,archive,ensure_ascii=False,indent=2)


if __name__ == "__main__":
    main()
