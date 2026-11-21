"""固定した短い枠で、全文の指示と上下の文脈表示を比べる。"""

import importlib.util
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v50-reading-orientation-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("short_crossing_columns_development", BASE)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
pilot = previous.pilot
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v53-short-column-order-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
SAMPLES = {
    ("kanpo1827-p2-p0001", 119): "columns",
    ("kanpo1827-p2-p0001", 331): "columns",
    ("kanpo1827-p2-p0001", 332): "columns",
    ("kanpo1828-p1-p0001", 104): "single-glyph",
    ("kanpo1828-p3-p0001", 110): "turned-single",
    ("kanpo1826-p5-p0001", 259): "right-to-left",
    ("kanpo1826-p5-p0001", 284): "partial-horizontal-stroke",
    ("kanpo1827-p2-p0001", 337): "control-columns",
    ("kanpo1828-p1-p0001", 155): "control-single",
    ("defense-p0089", 111): "control-parentheses",
    ("wp-summary-p0004", 23): "control-number",
    ("disaster-p0079", 23): "control-horizontal",
}
GUIDE = (
    "元の紙面で横書きの行なら、枠に所属する字を左から右へ写します。"
    "縦書きの複数列を横切る枠なら、別の列の上下の並びを見て、右端の列から左へ進みます。"
    "同じ縦列の中では上から下です。周囲の字は読む順を確かめるだけに使い、元の枠に所属する字だけを写してください。"
    "枠にある字を順に連結した全文をtextに入れ、列の目印と区切り記号を書きません。"
    "字の全体の中心を確認します。上下の二本の横画が一字の画であるとき、片側を別の字として切り離しません。"
)
VISUAL = (
    "『短い枠と上下のつながり』は元と同じ450 DPIの像です。色は枠の外の範囲を指します。"
    "右の枠なしで字の全部を確かめます。横倒しの字だけ、同じ450 DPIを90度回した表示で読みを確認できます。"
    "向きが変わって見えても所属と列の順を元の位置で確認します。"
)


def context(image, rect, ident, font):
    pix, (left, top) = previous.cropped(image, rect, 39, 115)
    factor = 2 if pix.width <= 400 else 1
    display = pix.resize((factor * pix.width, factor * pix.height), Image.Resampling.NEAREST)
    color = np.array(display)
    x, y, right, bottom = rect
    xs = left + (np.arange(display.width) + .5) / factor
    ys = top + (np.arange(display.height) + .5) / factor
    inside = (x <= xs[None, :]) & (xs[None, :] < right) & (y <= ys[:, None]) & (ys[:, None] < bottom)
    color[~inside] = color[~inside] * .53 + np.array([249, 222, 201]) * .47
    wide = Image.new("RGB", (max(320, 2 * display.width + 24), display.height + 57), "white")
    draw = ImageDraw.Draw(wide)
    draw.text((4, 4), f"{ident}　固定450 DPI　短い枠と上下のつながり", font=font, fill="black")
    for k, (cap, part) in enumerate((("元の枠と周囲", Image.fromarray(color)), ("同じ枠なしの画素", display))):
        px = 7 + k * (display.width + 10)
        draw.text((px, 29), cap, font=font, fill="black")
        wide.paste(part, (px, 53))
    return previous.blob(wide)


def snapshot():
    audit = pilot.audit
    sys.path.insert(0, str(HERE.parent / "v47-reference-audit"))
    import official
    core = official.core
    core.verify_methods()
    root = core.OUT / "delivery"
    package_file, selection = root / "packages.json", core.OUT / "selection.json"
    original, selected = core.load(package_file), core.load(selection)["selected"]
    official.audit.verify_delivery(core.sha(package_file))
    font_file = core.previous.packets.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    rows, mapping, jobs = [], {}, {}
    display = pilot.OUT / "display"
    source = HERE.parent / "v47-reference-audit/provisional-before-last-vote.json"
    pins = {str(f): audit.sha(f) for f in (Path(__file__), BASE, HERE / "protocol.md", source, package_file, selection, font_file)}
    for name, packet in original["packs"].items():
        (ident, binding), = packet["mapping"].items()
        row = selected[binding["entry"]]
        key = row["key"], row["line_index"]
        if key not in SAMPLES:
            continue
        targets = {v["text"] for v in row["targets"].values() if v["known"]}
        if len(targets) != 1 or row["allocation_axis"] != "x":
            raise ValueError("横軸の固定比較対照が異なる")
        req, slices = packet["request"], binding["partitions"]
        guide, inset, closing = req["prompt"].partition(audit.packets.FORMAT)
        if not inset:
            raise ValueError("正式の画像票と回答形式が異なる")
        if slices:
            suffix = f"目印は{'、'.join(slices)}。"
            if core.previous.packets.SHORT not in guide or suffix not in guide:
                raise ValueError("列を個別に答える指示を一意に外せない")
            guide = guide.replace(core.previous.packets.SHORT, "", 1).replace(suffix, "", 1)
        tag = f"case-{len(rows):02d}"
        cards = root / "cards" / name
        old = {n: (cards / n).read_bytes() for n in req["images"]}
        if [audit.readers.sha(p) for p in old.values()] != req["image_sha256"]:
            raise ValueError("旧指示で実際に使った原画像がそろわない")
        base = {**req, "prompt": guide + GUIDE + inset + closing}
        jobs[tag + "/plain"] = {"cards": str(cards), "request": base}
        high = binding["image_reference"]["source_view"]["views"][1]
        stem = next(v["image"] for v in high["images"] if v["kind"] == "plain")
        fixed = root / "source-assets" / stem
        if core.sha(fixed) != original["source_assets"][stem]:
            raise ValueError("固定450 DPIの画像が異なる")
        with Image.open(fixed) as im:
            rect = high["target_rectangle"]
            images = old | {f"{ident}-short-context.png": context(im, rect, ident, font)}
            if max(row["box"][2:]) <= 35:
                images[f"{ident}-quarter-turns.png"] = previous.turned(im, rect, ident, font)
        placed = display / "cards" / tag
        placed.mkdir(parents=True)
        for filename, data in images.items():
            audit.save_once(placed / filename, data)
        jobs[tag + "/visual"] = {"cards": str(placed), "request": {**base, "images": list(images),
            "image_sha256": [audit.readers.sha(b) for b in images.values()], "prompt": guide + GUIDE + VISUAL + inset + closing}}
        mapping[tag] = {**binding, "entry": len(rows), "category": SAMPLES[key], "baseline_packet": name}
        rows.append({**row, "effective": targets.pop()})
        pins[str(fixed)] = core.sha(fixed)
    if len(rows) != len(SAMPLES) or any(len(j["request"]["images"]) > 24 for j in jobs.values()):
        raise ValueError("対象の固定画像と対照がそろわない")
    positions = display / "selection.json"
    audit.save_once(positions, audit.encoded({"selected": rows}))
    pins[str(positions)] = core.sha(positions)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        del sys.argv[1]
        helper = BASE.with_name("compare.py")
        spec = importlib.util.spec_from_file_location("compare_short_columns", helper)
        report = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report)
        report.HERE, report.pilot = HERE, pilot
        report.main()
    else:
        pilot.snapshot = snapshot
        pilot.main()
