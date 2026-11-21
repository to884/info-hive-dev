"""既定の枠と固定画素から、本文を含まない監査用の配布記録を作る。"""

import argparse
from collections import defaultdict
from contextlib import closing
import hashlib
import importlib.util
import io
import secrets
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw, ImageFont
from pypdfium2 import PdfDocument

from selection import HERE, MANIFEST, OUT, CORPUS, load, score, sha
import glyph_geometry_v9
import region_images_v9

VISUAL = HERE.parent / "short-mixed-axis-pilot/run.py"
spec = importlib.util.spec_from_file_location("visual_cards", VISUAL)
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)
base, original = layout.base, layout.v2
SOURCE = OUT / "selection.json"
PACKS = OUT / "packages.json"
CARD_LIMIT, ROW_LIMIT = 24, 4
MODELS = {"gpt": "gpt-6.2-sol", "claude": "claude-opus-5-5"}
GUIDE = (
    "固定150 DPIで字の所属を、450 DPIで字形を確かめてください。上下左右の枠は原画と別の位置に描画されています。"
    "所属軸xなら字の全インクの左右長さの半分以上が枠内で、上下のインク中心も枠内のときに所属します。"
    "軸yなら上下長さの半分以上と左右の中心を確認します。縦書きの複数列は右から左、列内は上から下です。"
    "長い行のカードの重なりを一度だけ写してください。隣の字、図形、読めない字を補ってはいけません。"
    "意味や予想から連続する括弧や記号の数を決めず、見える字を一つずつ確認してください。"
    "行頭の小さな丸い印が1個、ほかの字から離れて見える場合は、見た目の位置を⟦round:X-X⟧で記録します。"
    "行中でも、丸い印の符号だけを画像で区別できないときは同じ形式を使います。"
    "点線が見えて符号や字の区切りを区別できないとき、その点線を⟦trail:X-Y⟧に換えます。"
    "XとYは最初の点と最後の点それぞれの中心の横座標です。各IDの『横座標』画像は短い目盛りが5画素ずつです。"
    "本文のどの字とどの字の間に印があるかをその画像で確認し、本文の実際の位置に印を置きます。"
    "枠と点そのものを見た箇所にだけ使います。形から符号を区別できるものは通常どおり写します。"
    "字の所属または他の本文を決められなければ行全体を未決定としてください。"
    "所属する字が一つもないときだけ空文字にしてください。\n"
)


def lookup():
    manifests = load(CORPUS / "probe-v4/manifest.json")
    catalog = {}
    for path in sorted((CORPUS / "public").glob("*.truth.json")):
        publication = load(path)
        for content in publication["pages"]:
            key = f"{publication['name']}-p{content['page']:04d}"
            catalog[key] = (publication["file"], publication["pdf_sha256"], content["page"])
    return manifests, catalog


def inputs():
    immutable = (Path(__file__), HERE / "readers.py", HERE / "runner.py", HERE / "protocol.md", MANIFEST,
                 VISUAL, layout.PILOT, Path(original.__file__), Path(original.v1.__file__), Path(base.__file__),
                 Path(glyph_geometry_v9.__file__), Path(region_images_v9.__file__),
                 base.FONTS / "meiryo.ttc", SOURCE, CORPUS / "probe-v4/manifest.json")
    return {str(p): sha(p) for p in immutable}


def render(folder, rows, manifest, catalog):
    """固定画像と、同じ版の元PDFから描画した確認画像をピクセルで照合する。"""
    page_key = rows[0][1]["key"]
    file, digest, number = catalog[page_key]
    png = CORPUS / "probe-v4/png" / (page_key + ".png")
    source = CORPUS / file
    if sha(source) != digest or sha(png) != manifest[page_key]["png_sha256"]:
        raise ValueError("凍結した元PDFか150 DPIの画像が変わった")
    with Image.open(png) as image:
        fixed = image.convert("RGB")
    with closing(PdfDocument(source)) as doc, closing(doc[number - 1]) as page:
        with closing(page.render(scale=150 / 72)) as low, closing(page.render(scale=450 / 72)) as high:
            raw = low.to_pil().convert("RGB")
            detailed = high.to_pil().convert("RGB")
            if fixed.size != raw.size or fixed.tobytes() != raw.tobytes():
                raise ValueError("監査で使う描画と固定150 DPIが変わった")
            a, b = (glyph_geometry_v9.pixel_transform(view, page) for view in (low, high))
            result = {}
            for anon, row in rows:
                asset = region_images_v9.save_views(folder, anon, fixed, detailed, a, b, row["box"], row["allocation_axis"])
                result[anon] = {**row, "asset": asset}
            return result, {"150_dpi": sha(png), "450_dpi_rgb": hashlib.sha256(detailed.tobytes()).hexdigest(),
                            "450_dpi_shape": detailed.size, "pdf_sha256": digest,
                            "150_origin": a[0].tolist(), "150_matrix": a[1].tolist()}


def x_coordinates(entry, ident, hashes, font):
    view = original.source_views(entry)[0]
    source = next(i for i in view["images"] if i["kind"] == "plain")
    path = original.v1.REGION / "assets" / source["image"]
    if hashes[path.resolve().as_posix()] != sha(path):
        raise ValueError("横座標を作る固定画像が違う")
    x, y, right, bottom = view["target_rectangle"]
    if any(type(a) is not int for a in (x, y, right, bottom)):
        raise ValueError("目盛りと元画素の位置が整数で対応しない")
    views = {}
    with Image.open(path) as image:
        for i, (a, b) in enumerate(original.segments(right - x), 1):
            left, top = max(0, x + a - 15), max(0, y - 18)
            piece = image.crop((left, top, min(image.width, x + b + 15), min(image.height, bottom + 18))).convert("RGB")
            card = Image.new("RGB", (max(220, piece.width + 22), piece.height + 64), "white")
            draw = ImageDraw.Draw(card)
            draw.text((4, 0), f"{ident}   横座標 {i}   150 DPI", font=font, fill="#252525")
            for pixel in range(0, entry["box"][2] + 1, 5):
                p = x + 3 * pixel - left
                if 0 <= p <= piece.width:
                    major = pixel % 20 == 0
                    if major:
                        draw.text((9 + p, 18), str(pixel), font=font, fill="#252525")
                    draw.line((10 + p, 38 if major else 44, 10 + p, 48), fill="red", width=1)
                    draw.line((10 + p, 49 + piece.height, 10 + p, (58 if major else 53) + piece.height), fill="red", width=1)
            card.paste(piece, (10, 49))
            raw = io.BytesIO()
            card.save(raw, "PNG")
            views[f"{ident}-coordinate-{i:02d}.png"] = raw.getvalue()
    return views


def made(entry, ident, hashes, font):
    cards, traces = original.make_cards(entry, hashes, ident, font)
    extra = {}
    width, height = entry["box"][2:]
    if entry["allocation_axis"] == "x" and height <= 17:
        detailed, _ = layout.figure.detailed(entry, ident, hashes, font)
        extra.update(detailed)
    if entry["allocation_axis"] == "x" and width <= 120 and 12 <= height <= 35:
        extra[f"{ident}-ruler.png"] = layout.ruler(entry, ident, hashes, font)
    if entry["allocation_axis"] == "x" and height <= 45:
        extra.update(x_coordinates(entry, ident, hashes, font))
    return cards | extra, sorted(cards), sorted(extra), traces


def new_pack(index, group, saved):
    name = f"pack-{index:03d}"
    names_a, names_b, row_ids, image_sha, traces, contents = [], [], [], {}, {}, {}
    destination = OUT / "cards" / name
    destination.mkdir(parents=True)
    for ident, (target, items, original, supplemental, trace) in group.items():
        row_ids.append(ident)
        names_a.extend(original)
        names_b.extend(supplemental)
        traces.update(trace)
        contents[ident] = target
        for label, blob in items.items():
            (destination / label).write_bytes(blob)
            image_sha[label] = hashlib.sha256(blob).hexdigest()
    images = names_a + names_b
    prompt = (layout.v2.v1.INTRO + layout.v2.NOTICE + layout.figure.old.shared + GUIDE
              + base.FORMAT + "、".join(row_ids) + "\n")
    pack = {"images": images, "image_sha256": [image_sha[n] for n in images], "ids": row_ids, "prompt": prompt}
    saved[name] = {"request": pack, "origin": traces, "mapping": contents}


def prepare(expected):
    if PACKS.exists() or (OUT / "cards").exists():
        raise FileExistsError("監査に配る同じ標本を作り直さない")
    if sha(SOURCE) != expected:
        raise ValueError("配布する標本が実行済みの抽出と違う")
    before = inputs()
    saved = load(SOURCE)
    population = load(MANIFEST)
    if any(sha(Path(k)) != digest for k, digest in population["inputs"].items()):
        raise ValueError("抽出時に固定した読取と採点の方法が変化")
    rows = saved["selected"]
    if saved["population_lock_sha256"] != sha(MANIFEST) or len(rows) != len({(r["key"], r["line_index"]) for r in rows}):
        raise ValueError("標本の分母または行に重複がある")
    index, catalog = lookup()
    grouped = defaultdict(list)
    randomized = list(enumerate(rows))
    secrets.SystemRandom().shuffle(randomized)
    for i, row in randomized:
        grouped[row["key"]].append((f"A{i + 1:04d}", row))
    font = ImageFont.truetype(base.FONTS / "meiryo.ttc", size=17)
    package_list, png_inputs = {}, {}
    with tempfile.TemporaryDirectory(dir=OUT, prefix="raw-") as path:
        source_folder = Path(path) / "assets"
        source_folder.mkdir()
        original.v1.REGION = source_folder.parent
        layout.REGION = source_folder.parent
        layout.figure.REGION = source_folder.parent
        points = {}
        for key, values in grouped.items():
            line_images, fingerprints = render(source_folder, values, index, catalog)
            points.update(line_images)
            png_inputs[key] = fingerprints
        hashes = {f.resolve().as_posix(): sha(f) for f in source_folder.iterdir()}
        buffer, image_count = {}, 0
        for i, row in randomized:
            entry = points[f"A{i + 1:04d}"]
            ident = f"G{len(buffer) + 1:02d}"
            bundle, a, b, trace = made(entry, ident, hashes, font)
            if buffer and (len(buffer) == ROW_LIMIT or image_count + len(bundle) > CARD_LIMIT):
                new_pack(len(package_list), buffer, package_list)
                buffer, image_count, ident = {}, 0, "G01"
                bundle, a, b, trace = made(entry, ident, hashes, font)
            target = {"entry": i, "image_reference": {"source_view": entry["asset"], "sha": png_inputs[row["key"]]}}
            buffer[ident] = target, bundle, a, b, trace
            image_count += len(bundle)
        if buffer:
            new_pack(len(package_list), buffer, package_list)
        archive = OUT / "source-assets"
        source_folder.rename(archive)
    if before != inputs() or sum(len(v["mapping"]) for v in package_list.values()) != len(rows):
        raise ValueError("監査の配布内容に欠けた行か変更がある")
    value = {"scope": "independent-audit-image-requests", "models": MODELS, "source_sha256": expected,
             "inputs": before, "sources": png_inputs, "source_assets": {Path(n).name: h for n, h in hashes.items()},
             "packs": package_list}
    score.audit.save(PACKS, value)
    print(sha(PACKS), len(package_list), "束、", len(rows), "行", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--selection-sha256", required=True)
    prepare(cli.parse_args().selection_sha256)
