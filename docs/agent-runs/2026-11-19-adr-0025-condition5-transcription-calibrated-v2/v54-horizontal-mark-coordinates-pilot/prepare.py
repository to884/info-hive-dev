"""固定150 DPIの目盛りの数字を上下に分け、横書きの点と丸を比較する。"""

import importlib.util
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v51-reading-physical-instructions-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("horizontal_points_development", BASE)
earlier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(earlier)
pilot = earlier.pilot
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v54-horizontal-mark-coordinates-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
CASES = {
    ("wp-summary-p0008", 4): "coordinate",
    ("wp-summary-p0002", 18): "isolated-large-bullet",
    ("defense-p0042", 36): "letter-and-stop",
    ("wp-summary-p0002", 13): "control-long-dot",
    ("wp-summary-p0010", 5): "control-long-inline",
    ("wp-summary-p0004", 4): "control-colored-items",
    ("defense-p0006", 42): "control-dot-run",
    ("defense-p0500", 64): "control-letters-and-number",
    ("disaster-p0107", 26): "control-open-circle",
}
OLD_RULER = (
    "拡大した横座標の大目盛りに書かれた数字は枠の左からの値で、数字の間隔は10画素です。"
    "番号のない小目盛りは5画素の中間です。"
)
NEW_RULER = (
    "横座標は元の枠の左からの値です。横座標画像の上の番号は10画素ごと、下の番号はその中間の5画素です。"
    "点の真上または真下で最も近い二つの番号を読み、点の中心をその間で確かめます。"
)
GUIDE = (
    "文字の高さの半分以上の塗り円が独立して行頭にあり、円と本文の間が字間より広いと確認できた場合は、"
    "一つの項目を始める「●」です。周囲に同じ項目丸があれば形と位置を比較します。"
    "欧文の文字と数字の底にそろう低い小さい四角い点は、形と位置が見える場合にピリオド「.」です。"
    "本文の中央にある曖昧な点は、横座標で確認した丸印の形式を使います。本文の括弧は閉じ方を形で確認します。"
)


def rulers(row, image, label, segments, font):
    x, y, w, h = row["box"]
    pictures = {}
    for ordinal, (start, end) in enumerate(segments(3 * w), 1):
        l, t = max(0, x + start // 3 - 5), max(0, y - 5)
        r, b = min(image.width, x + math.ceil(end / 3) + 5), min(image.height, y + h + 5)
        cells = image.crop((l, t, r, b)).convert("RGB")
        scale = 6
        width, height = cells.width * scale, cells.height * scale
        panel = Image.new("RGB", (max(270, width + 54), height + 110), "white")
        draw = ImageDraw.Draw(panel)
        px, py = 27, 52
        panel.paste(cells.resize((width, height), Image.Resampling.NEAREST), (px, py))
        draw.text((6, 2), f"{label}　横座標 {ordinal}　固定150 DPI　上は10画素・下は中間の5",
                  font=font, fill="#202020")
        draw.line((px, py-4, px+width, py-4), fill="#b2b2b2")
        draw.line((px, py+height+4, px+width, py+height+4), fill="#b2b2b2")
        for number in range(0, w + 1, 5):
            position = px + scale * (x + number - l)
            if not px <= position <= px + width:
                continue
            color = "#3f4972"
            major = number % 10 == 0
            draw.line((position, py-4, position, py-13 if major else py-9), fill=color)
            draw.line((position, py+height+4, position, py+height+9 if major else py+height+13), fill=color)
            draw.text((position, py-17 if major else py+height+17), str(number), font=font,
                      anchor="mb" if major else "mt", fill=color)
        name = f"{label}-coordinate-{ordinal:02d}.png"
        pictures[name] = earlier.previous.blob(panel)
    return pictures


def snapshot():
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core, audit = official.core, pilot.audit
    core.verify_methods()
    original = core.OUT / "delivery"
    manifest, selection = original / "packages.json", core.OUT / "selection.json"
    data, selected = core.load(manifest), core.load(selection)["selected"]
    margin_path = HERE.parent / "v41-paragraph-bullets-pilot/prepare.py"
    paragraphs = core.previous.module("archived_paragraph_test", margin_path)
    font_path = core.previous.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    ruler_font = ImageFont.truetype(font_path, size=15)
    pins = {str(p): core.sha(p) for p in (Path(__file__), HERE / "protocol.md", BASE, margin_path, manifest, selection,
                                          font_path, HERE.parent / "v47-reference-audit/provisional-before-last-vote.json")}
    samples, mapping, jobs = [], {}, {}
    for pack, item in data["packs"].items():
        (label, bind), = item["mapping"].items()
        row = selected[bind["entry"]]
        key = row["key"], row["line_index"]
        if key not in CASES:
            continue
        answers = {v["text"] for v in row["targets"].values() if v["known"]}
        if len(answers) != 1 or row["allocation_axis"] != "x":
            raise ValueError("既定の横軸の正解が一つに定まらない")
        fixed = core.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        if core.sha(fixed) != bind["image_reference"]["sha"]["150_dpi"]:
            raise ValueError("座標の元になる固定150 DPIが変わった")
        request = item["request"]
        images = {name: (original / "cards" / pack / name).read_bytes() for name in request["images"]}
        if [audit.readers.sha(blob) for blob in images.values()] != request["image_sha256"]:
            raise ValueError("既定の画像と附帯表示が異なる")
        with Image.open(fixed) as img:
            replace = rulers(row, img, label, core.previous.packets.old.original.segments, ruler_font)
        if set(replace) != {n for n in images if "-coordinate-" in n}:
            raise ValueError("座標の全区間を同じ順番で差し替えられない")
        images.update(replace)
        width, height = row["box"][2:]
        if width > 1200 and height <= 35:
            added = paragraphs.margin(fixed, row["box"], label, font)
            if len(images) < 24:
                images[f"{label}-paragraph-margin.png"] = added
            else:
                first = next(iter(replace))
                images[first] = official.audit.combine(images[first], added)
        guide, sep, end = request["prompt"].partition(audit.packets.FORMAT)
        if not sep or guide.count(OLD_RULER) != 1 or guide.count(earlier.OLD_CIRCLE) != 1:
            raise ValueError("固定の指示に未確認の違いがある")
        guide = guide.replace(OLD_RULER, NEW_RULER).replace(earlier.OLD_CIRCLE, earlier.CIRCLE) + GUIDE
        tag = f"case-{len(samples):02d}"
        cards = pilot.OUT / "display/cards" / tag
        cards.mkdir(parents=True)
        for name, image in images.items():
            audit.save_once(cards / name, image)
        mapping[tag] = {**bind, "entry": len(samples), "category": CASES[key], "baseline_packet": pack}
        jobs[tag + "/new"] = {"cards": str(cards), "request": {**request, "images": list(images),
            "image_sha256": [audit.readers.sha(d) for d in images.values()], "prompt": guide + sep + end}}
        samples.append({**row, "effective": answers.pop()})
        pins[str(fixed)] = core.sha(fixed)
    if len(samples) != len(CASES):
        raise ValueError("固定した横軸の開発行が足りない")
    doc = pilot.OUT / "display/selection.json"
    audit.save_once(doc, audit.encoded({"selected": samples}))
    pins[str(doc)] = core.sha(doc)
    pilot.SAMPLES = samples
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        earlier.HERE = HERE
        earlier.compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
