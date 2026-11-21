"""似た字の筆画の小窓と、見えた形から本文へ戻す表記を検査する。"""

import importlib.util
import math
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v52-vertical-ink-size-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("isolated_glyph_shapes", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_OUT, OLD_LOCK = earlier.OLD_ROOT, earlier.OLD_LOCK
pilot.HERE = HERE
pilot.OUT = OLD_OUT.with_name("reference-v59-isolated-glyph-pieces-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
original_decode = pilot.reference.decoded
MARK = re.compile(r"⟦glyph:([a-z-]+)⟧")
GLYPHS = {
    "mountain-stand-mouth": "﨑", "mountain-big-can": "崎",
    "walk-table": "迨", "water-table": "治", "walk-heap": "追", "walk-official": "逭",
    "kana-ni": "ニ", "kanji-two": "二",
    "kana-ro": "ロ", "kanji-mouth": "口",
    "small-tsu": "っ", "full-tsu": "つ",
}
GUIDE = (
    "名前やよくある字から推測する前に、最初の『筆画の小窓』で字の上部・下部を見ます。"
    "小窓は同じ固定画素の一部です。余分な画を本文に入れず、本文全体と順序は主画像で確認してください。"
    "見えた形が左に山、右上に立、右下に可なら ⟦glyph:mountain-stand-mouth⟧、"
    "右上が大で右下が可なら ⟦glyph:mountain-big-can⟧ をその字の位置に書きます。"
    "ム・口の下をしんにょうが回る形は ⟦glyph:walk-table⟧、同じ右側で左に三水なら ⟦glyph:water-table⟧。"
    "しんにょうの中が𠂤なら ⟦glyph:walk-heap⟧、しんにょうの中が宀を持つ官なら ⟦glyph:walk-official⟧。"
    "二画の横線の字は、同じ列の太さ、両端、幅を比べ、ニと読める形は ⟦glyph:kana-ni⟧、二なら ⟦glyph:kanji-two⟧。"
    "四角い仮名のロは ⟦glyph:kana-ro⟧、漢字の口は ⟦glyph:kanji-mouth⟧。"
    "小書きのっは ⟦glyph:small-tsu⟧、通常のつは ⟦glyph:full-tsu⟧。"
    "横画だけの場合も二つの枠端で所属を確認し、棒の長さと太さ、位置からハイフンと長音符を確かめます。"
    "指定に当たらない字は通常の文字で写します。"
)


def decoded(value, partitions):
    text = value["text"]
    tags = [mark[1] for mark in MARK.finditer(text)]
    if any(tag not in GLYPHS for tag in tags) or "⟦glyph:" in MARK.sub("", text):
        return pilot.reference.UNKNOWN
    replaced = MARK.sub(lambda m: GLYPHS[m[1]], text)
    return original_decode({**value, "text": replaced}, partitions)


def chip(image, rect, label, font):
    l, t, r, b = rect
    # 長い列は冒頭と末尾の二つを同じ基準で表示する。
    ranges = ((t, b),) if b - t <= 920 else ((t, t + 600), (b - 320, b))
    samples = []
    for start, stop in ranges:
        left, upper = max(0, math.floor(l)), max(0, math.floor(start))
        right, bottom = min(image.width, math.ceil(r)), min(image.height, math.ceil(stop))
        bit = np.array(image.crop((left, upper, right, bottom)).convert("L"))
        for _, u, _, d in earlier.measured(bit):
            h = d - u
            if not 16 <= h <= 85:
                continue
            square = image.crop((max(0, left - 5), max(0, upper + u - 8),
                                 min(image.width, right + 5), min(image.height, upper + d + 8))).convert("RGB")
            samples.append(square.resize((square.width * 3, square.height * 3), Image.Resampling.NEAREST))
    if not samples:
        # 目の近い範囲を残し、自動で字を判断したように表示しない。
        image_part, _ = earlier.earlier.previous.cropped(image, rect, 6, 6)
        segment = image_part.crop((0, 0, image_part.width, min(190, image_part.height)))
        samples.append(segment.resize((2 * segment.width, 2 * segment.height), Image.Resampling.NEAREST))
    width = max(140, max(a.width for a in samples) + 12)
    height = max(a.height for a in samples) + 26
    piece = Image.new("RGB", (min(6, len(samples)) * width, math.ceil(len(samples) / 6) * height + 36), "white")
    draw = ImageDraw.Draw(piece)
    draw.text((6, 5), f"{label}　筆画の小窓　固定450 DPI", font=font, fill="#252525")
    for i, sample in enumerate(samples):
        px, py = (i % 6) * width + 4, (i // 6) * height + 32
        draw.text((px, py), str(i + 1), font=font, fill="#7a7a7a")
        piece.paste(sample, (px, py + 20))
    return earlier.earlier.previous.blob(piece)


def snapshot():
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core, audit = official.core, pilot.audit
    core.verify_methods()
    root = core.OUT / "delivery"
    manifest = root / "packages.json"
    fixed = core.load(manifest)["source_assets"]
    old = audit.load(OLD_LOCK)
    if any(audit.sha(Path(p)) != h for p, h in old["files"].items()):
        raise ValueError("同じ画像で比較した開発の束が変化")
    prior = OLD_OUT / "display/selection.json"
    selected = audit.load(prior)["selected"]
    typeface = core.previous.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(typeface, size=17)
    pins = {str(p): audit.sha(p) for p in (Path(__file__), HERE / "protocol.md", BASE, OLD_LOCK, prior, manifest, typeface)}
    rows, mapping, jobs = [], {}, {}
    for tag, item in old["mapping"].items():
        row = selected[item["entry"]]
        if row["allocation_axis"] != "y":
            continue
        name = tag + "/new"
        request = old["jobs"][name]
        old_package = request["request"]
        ident, = old_package["ids"]
        high = item["image_reference"]["source_view"]["views"][1]
        basename = next(z["image"] for z in high["images"] if z["kind"] == "plain")
        origin = root / "source-assets" / basename
        if audit.sha(origin) != fixed[basename]:
            raise ValueError("小窓の元の450 DPIが変わった")
        with Image.open(origin) as img:
            added = chip(img, high["target_rectangle"], ident, font)
        old_files = {f: (Path(request["cards"]) / f).read_bytes() for f in old_package["images"]}
        if [audit.readers.sha(x) for x in old_files.values()] != old_package["image_sha256"]:
            raise ValueError("前版と同じ本文・枠の画像が揃わない")
        images = {f"{ident}-glyph-pieces.png": added} | old_files
        if len(images) > 24:
            raise ValueError("元の各区間と字形の小窓が同じ束に入らない")
        dest = pilot.OUT / "display/cards" / tag
        dest.mkdir(parents=True)
        for f, bits in images.items():
            audit.save_once(dest / f, bits)
        prompt, sep, form = old_package["prompt"].partition(audit.packets.FORMAT)
        if not sep:
            raise ValueError("前版の回答形式が異なる")
        jobs[name] = {"cards": str(dest), "request": {**old_package, "images": list(images),
            "image_sha256": [audit.readers.sha(bits) for bits in images.values()], "prompt": prompt + GUIDE + sep + form}}
        pins[str(origin)] = audit.sha(origin)
        mapping[tag] = {**item, "entry": len(rows)}
        rows.append(row)
    if len(rows) != 10:
        raise ValueError("固定された縦軸10行がそろわない")
    doc = pilot.OUT / "display/selection.json"
    audit.save_once(doc, audit.encoded({"selected": rows}))
    pins[str(doc)] = audit.sha(doc)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": old["files"] | pins}


if __name__ == "__main__":
    pilot.reference.decoded = decoded
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.earlier.HERE = HERE
        earlier.earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
