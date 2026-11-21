"""固定画素だけから数えた物理点を図示し、伏せた出典と二読を照合する。"""

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OLD_FILE = HERE.parent / "source-anchored-pilot/run.py"
spec = importlib.util.spec_from_file_location("former_blind_pilot", OLD_FILE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base = old.base
FORMER = old.HERE
OUT = old.OUT.parent / HERE.name
ASSETS, LOCK = OUT / "cards", HERE / "lock.json"
load_material = old.material
GUIDE = (
    "一部のIDには、固定150 DPI画像で小さな点を数えた補助画像もあります。"
    "補助画像の番号は字種の候補を示しません。原画像でも番号が示す点と位置、枠への所属を確かめ、"
    "確認できた点だけを数えてください。判断できない文字や点があれば、その行は未決定としてください。\n"
)


def make_aid(gray, box, items, ident, font):
    x, y, _, _ = box
    intervals = items["ranges"]
    if items["state"] != "measured" or items["points"] != len(intervals):
        raise ValueError("水平走査の独立な物理点の根拠がない")
    midpoint = sorted(items["scan_lines"])[len(items["scan_lines"]) // 2]
    groups = [intervals[i:i + 12] for i in range(0, len(intervals), 12)]
    canvas = Image.new("RGB", (570, 48 + 61 * len(groups)), "#ffffff")
    display = ImageDraw.Draw(canvas)
    display.text((12, 8), f"{ident}   固定150 DPIの点の確認", font=font, fill="#152332")
    for j, group in enumerate(groups):
        left = max(0, x + group[0][0] - 4)
        right = min(gray.width, x + group[-1][1] + 4)
        top = max(0, y + midpoint - 5)
        bottom = min(gray.height, y + midpoint + 6)
        crop = gray.crop((left, top, right, bottom))
        enlarged = crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.NEAREST)
        y0 = 49 + 61 * j
        canvas.paste(enlarged, (10, y0 + 17))
        for i, (l, r) in enumerate(group, 1):
            p = 10 + (x + (l + r) / 2 - left) * 3
            display.line((p, y0 + 12, p, y0 + 16), fill="#276abc", width=2)
            display.text((p - 4, y0 - 4), str(12 * j + i), font=font, fill="#224668")
    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()


def material():
    prev = old.HERE
    old.HERE = FORMER
    try:
        targets, expected, original_images, source = load_material()
    finally:
        old.HERE = prev
    prior = FORMER / "lock.json"
    projection = FORMER / "point-projection.json"
    old_lock = base.load(prior)
    if {k: v for k, v in old_lock.items() if k != "fixed_at"} != source:
        raise ValueError("前回の固定画像、対象または方法が異なる")
    measures = {old.identity(r): r for r in base.load(projection)["rows"]
                if r["matches_component_measurement"]}
    scan_file = FORMER.parent / "dot-layout-v2/result.json"
    targets_with_points = {old.identity(r) for r in base.load(scan_file)["geometries"] if r["runs"]}
    vis = old.v1.REGION
    start, final = base.load(vis / "start.json"), base.load(vis / "final.json")
    entries = {old.identity(r): r for r in start["entries"]}
    # 仮転記と既知対照の本文は後段で照合するため、提示側には入れない。
    stable = [r for r in final["rows"] if r["key"].startswith("disaster-p") and r["status"] == "readable"
              and r["allocation_axis"] == "x" and 85 <= r["box"][2] <= 240
              and old.identity(r) not in targets_with_points]
    control = min(stable, key=lambda r: hashlib.sha256(
        f"{old.SEED}/disaster-control/{r['key']}/{r['line_index']}".encode()).digest())
    control_id, = [i for i, r in expected["disaster"].items() if r["kind"] == "known-control"]
    targets["disaster"][control_id] = {"key": control["key"], "line_index": control["line_index"],
                                        "kind": "known-control"}
    expected["disaster"][control_id] = {"kind": "known-control", "exact": base.normalize(control["text"])}
    fontfile = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(fontfile, size=13)
    cards, frozen_packs = {}, {}
    input_images = {}
    for pub, package in source["packs"].items():
        normal = dict(original_images[pub])
        source_tiles = dict(package["source_tiles"])
        if pub == "disaster":
            card, tiles = old.v2.make_cards(entries[old.identity(control)], start["assets"], control_id, font)
            original_names = [n for n in normal if n.startswith(control_id + "-")]
            normal = {n: data for n, data in normal.items() if n not in original_names}
            normal.update(card)
            source_tiles = {n: detail for n, detail in source_tiles.items() if n not in original_names} | tiles
        additional = {}
        for i, target in targets[pub].items():
            if target["kind"] != "source-backed":
                continue
            identity = old.identity(target)
            raster = base.BENCH / "corpus/probe-v4/png" / (target["key"] + ".png")
            saved = base.load(base.BENCH / "corpus/public/region-v9" / (target["key"] + ".json"))
            sha = base.sha(raster)
            if sha != saved["image_sha256"]:
                raise ValueError("補助に使う固定画像が違う")
            input_images[raster.name] = sha
            with Image.open(raster) as im:
                additional[f"{i}-point-aid.png"] = make_aid(
                    im.convert("RGB"), entries[identity]["box"], measures[identity], i, font)
        cards[pub] = normal | additional
        seq = sorted(normal) + sorted(additional)
        prompt = package["prompt"]
        if prompt.count(base.FORMAT) != 1:
            raise ValueError("転記指示と回答形式を確かめられない")
        frozen_packs[pub] = {"images": seq, "ids": package["ids"],
                             "image_sha256": [hashlib.sha256(cards[pub][n]).hexdigest() for n in seq],
                             "prompt": prompt.replace(base.FORMAT, GUIDE + base.FORMAT, 1),
                             "source_tiles": source_tiles}
    # 旧版に不足していた依存コードと、照合に使う文字列の同一性もハッシュで固定する。
    deps = (OLD_FILE, Path(__file__), old.V3, Path(old.v2.__file__), Path(old.v1.__file__),
            Path(base.__file__), Path(old.pilot.__file__), Path(old.pilot.opus.__file__), fontfile)
    frozen = {"fixed_inputs": source["sources"], "protocol_sha256": base.sha(HERE / "protocol.md"),
              "prior_lock_sha256": base.sha(prior), "projection_sha256": base.sha(projection),
              "dependencies": {p.parent.name + "/" + p.name: base.sha(p) for p in deps},
              "expected_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              "image_inputs": input_images, "targets": targets, "packs": frozen_packs, "models": old.pilot.MODELS}
    return targets, expected, cards, frozen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    p.add_argument("--lock-sha256")
    args = p.parse_args()
    _, expected, images, fixed = material()
    if args.action == "prepare":
        if LOCK.exists() or ASSETS.exists():
            raise FileExistsError("事前固定を上書きしない")
        for pub, cards in images.items():
            dst = ASSETS / pub
            dst.mkdir(parents=True)
            for n, content in cards.items():
                (dst / n).write_bytes(content)
        base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
        print(base.sha(LOCK), {p: len(v) for p, v in images.items()}, flush=True)
    else:
        old.HERE, old.OUT, old.ASSETS, old.LOCK = HERE, OUT, ASSETS, LOCK
        old.material = material
        old.execute(args, expected, images, fixed)


if __name__ == "__main__":
    main()
