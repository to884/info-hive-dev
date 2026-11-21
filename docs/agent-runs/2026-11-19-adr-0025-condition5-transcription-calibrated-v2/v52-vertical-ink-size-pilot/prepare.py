"""v51の縦軸画像に、固定450 DPIで測ったインクの寸法を一枚付ける。"""

import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("vertical_glyph_size_development", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
OLD_ROOT, OLD_LOCK = pilot.OUT, pilot.LOCK
pilot.HERE = HERE
pilot.OUT = OLD_ROOT.with_name("reference-v52-vertical-ink-size-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GUIDE = (
    "固定450 DPIの行頭と行末の寸法の画像も確認します。数字は二つの濃さで同じ範囲になったインクの帯です。"
    "一つの字全体に対応する場合に、その幅と高さを同じ列の普通の字と比較します。"
    "字の一部の帯や句読点に数値が付く場合もあるので、帯の数で字数を決めません。"
)


def measured(gray):
    tracks = []
    for threshold in (136, 188):
        ink = gray < threshold
        active = np.flatnonzero(ink.sum(axis=1) > 1)
        groups = np.split(active, np.where(np.diff(active) > 4)[0] + 1)
        spans = []
        for group in groups:
            if len(group) < 5:
                continue
            t, b = int(group[0]), int(group[-1]) + 1
            axis = np.flatnonzero(ink[t:b].any(axis=0))
            spans.append((int(axis[0]), t, int(axis[-1]) + 1, b))
        tracks.append(spans)
    return [box for box in tracks[1] if sum(max(abs(x - y) for x, y in zip(box, other, strict=True)) <= 2
                                            for other in tracks[0]) == 1]


def scaled(image, rect, ident, font):
    x, y, r, b = rect
    spans = ((y, b),) if b - y <= 255 else ((y, y + 212), (b - 250, b))
    panels = []
    for top, bottom in spans:
        swatch, (left, offset) = earlier.previous.cropped(image, (x, top, r, bottom), 7, 7)
        gray = np.array(swatch.convert("L"))
        xl, xr = max(0, math.floor(x - left)), min(swatch.width, math.ceil(r - left))
        yt, yb = max(0, math.floor(top - offset)), min(swatch.height, math.ceil(bottom - offset))
        boxes = measured(gray[yt:yb, xl:xr])
        width = max(255, swatch.width * 2 + 140)
        panel = Image.new("RGB", (width, swatch.height * 2 + 28), "white")
        panel.paste(swatch.resize((swatch.width * 2, swatch.height * 2), Image.Resampling.NEAREST), (6, 26))
        draw = ImageDraw.Draw(panel)
        draw.text((4, 2), "全体" if len(spans) == 1 else ("行頭" if top == y else "行末"),
                  font=font, fill="black")
        edge = 9 + swatch.width * 2
        for l, t, q, d in boxes:
            start, stop = 26 + 2 * (t + yt), 26 + 2 * (d + yt)
            color = "#424d90"
            draw.line((edge, start, edge, stop), width=1, fill=color)
            draw.line((edge - 3, start, edge + 3, start), fill=color)
            draw.line((edge - 3, stop, edge + 3, stop), fill=color)
            draw.text((edge + 9, (start + stop) // 2), f"幅{q-l} 高{d-t}", font=font,
                      anchor="lm", fill=color)
        panels.append(panel)
    out = Image.new("RGB", (sum(p.width + 12 for p in panels), 32 + max(p.height for p in panels)), "white")
    ImageDraw.Draw(out).text((4, 5), f"{ident}　固定450 DPI　インク帯の寸法（画素）", font=font, fill="black")
    left = 4
    for panel in panels:
        out.paste(panel, (left, 29))
        left += panel.width + 12
    return earlier.previous.blob(out)


def snapshot():
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    audit, core = pilot.audit, official.core
    core.verify_methods()
    root = core.OUT / "delivery"
    package_file = root / "packages.json"
    packages = core.load(package_file)
    old = audit.load(OLD_LOCK)
    if any(audit.sha(Path(p)) != h for p, h in old["files"].items()):
        raise ValueError("固定済みの開発比較が変化")
    seed_rows = audit.load(OLD_ROOT / "display/selection.json")["selected"]
    font_path = core.previous.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    files = {str(f): audit.sha(f) for f in (Path(__file__), HERE / "protocol.md", OLD_LOCK, package_file, font_path)}
    rows, jobs, mapping = [], {}, {}
    display = pilot.OUT / "display"
    for key, job in old["jobs"].items():
        tag = key.split("/")[0]
        item = old["mapping"][tag]
        row = seed_rows[item["entry"]]
        if row["allocation_axis"] != "y":
            continue
        label, = job["request"]["ids"]
        image = item["image_reference"]["source_view"]["views"][1]
        visible = next(v["image"] for v in image["images"] if v["kind"] == "plain")
        fixed = root / "source-assets" / visible
        if core.sha(fixed) != packages["source_assets"][visible]:
            raise ValueError("一定の倍率で固定した字形の画像が変わった")
        with Image.open(fixed) as im:
            dimensions = scaled(im, image["target_rectangle"], label, font)
        request = job["request"]
        originals = {name: (Path(job["cards"]) / name).read_bytes() for name in request["images"]}
        if [audit.readers.sha(data) for data in originals.values()] != request["image_sha256"]:
            raise ValueError("旧の画像が固定と異なる")
        cards = originals | {f"{label}-ink-dimensions.png": dimensions}
        if len(cards) > 24:
            raise ValueError("開発で検証した画像が上限を超える")
        place = display / "cards" / tag
        place.mkdir(parents=True)
        for name, data in cards.items():
            audit.save_once(place / name, data)
        guide, form, answer = request["prompt"].partition(audit.packets.FORMAT)
        if not form:
            raise ValueError("開発の回答形式を再現できない")
        jobs[key] = {"cards": str(place), "request": {**request, "images": list(cards),
            "image_sha256": [audit.readers.sha(data) for data in cards.values()], "prompt": guide + GUIDE + form + answer}}
        mapping[tag] = {**item, "entry": len(rows)}
        rows.append(row)
        files[str(fixed)] = core.sha(fixed)
    if len(rows) != 10:
        raise ValueError("同じ縦軸の開発行がそろわない")
    positions = display / "selection.json"
    audit.save_once(positions, audit.encoded({"selected": rows}))
    files[str(positions)] = core.sha(positions)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": old["files"] | files}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.HERE = HERE
        earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
