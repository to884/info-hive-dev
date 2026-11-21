"""同じ固定画像で、数を見せずに点線の位置と本文を確認する。"""

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "source-anchored-pilot-v2/run.py"
spec = importlib.util.spec_from_file_location("numbered_pilot", PREVIOUS)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
base, read = prior.base, prior.old
OUT = prior.OUT.parent / HERE.name
ASSETS = OUT / "cards"
LOCK = HERE / "lock.json"
MARKER = re.compile(r"⟦dotspan:([0-9]{1,2})-([0-9]{1,2})⟧")
TASK = (
    "点線がある場合は、元の枠と字の所属を確認します。点線の字種や符号を画素で区別できず、"
    "同じ行に属する点線の位置を確認できた場合だけ、点線部分を ⟦dotspan:P-Q⟧ に換えてください。"
    "Pは点線が少しでも見える元カードの最初の番号、Qは最後の番号です。両方が同じなら同じ番号を2度書いてください。"
    "『位置の補助』と書いた切り出しはカード番号に含めません。確認できた位置以外に点を足さないでください。"
    "点線の周りの全文をそのまま転記し、所属か他の字を確かめられないときは行全体を未決定にしてください。\n"
)


def position_card(gray, box, measure, ident, font):
    x, y, w, h = box
    ranges = measure["ranges"]
    center = sorted(measure["scan_lines"])[len(measure["scan_lines"]) // 2]
    left, right = max(x, x + ranges[0][0] - 8), min(x + w, x + ranges[-1][1] + 8)
    top, bottom = max(y, y + center - 7), min(y + h, y + center + 8)
    pieces = [(l, min(l + 170, right)) for l in range(left, right, 160)]
    display = Image.new("RGB", (545, 42 + 71 * len(pieces)), "#ffffff")
    titles = ImageDraw.Draw(display)
    titles.text((10, 6), f"{ident}   位置の補助（固定150 DPI）", font=font, fill="#152332")
    for j, (l, r) in enumerate(pieces):
        patch = gray.crop((l, top, r, bottom))
        local = (l - x, r - x, top - y, bottom - y)
        y0 = 41 + j * 71
        titles.text((10, y0 - 3), f"枠内の位置 x {local[0]}–{local[1]}  y {local[2]}–{local[3]}",
                    font=font, fill="#152332")
        display.paste(patch.resize((patch.width * 3, patch.height * 3), Image.Resampling.NEAREST), (10, y0 + 19))
    raw = io.BytesIO()
    display.save(raw, format="PNG")
    return raw.getvalue()


def expected_panels(ident, entry, measure, tiles):
    view = entry["asset"]["views"][0]
    shift_x, shift_y = view["target_rectangle"][:2]
    y = shift_y + 3 * sorted(measure["scan_lines"])[len(measure["scan_lines"]) // 2]
    pos = [shift_x + 1.5 * (l + r) for l, r in measure["ranges"]]
    panels = []
    for name, traced in sorted(tiles.items()):
        if not name.startswith(ident + "-"):
            continue
        l, t, r, b = traced[0]["rectangle"]
        if t <= y < b and any(l <= x < r for x in pos):
            panels.append(int(Path(name).stem.rsplit("-", 1)[1]))
    if not panels:
        raise ValueError("元のカードに点線が写っていない")
    return min(panels), max(panels)


def material():
    targets, expected, all_old, frozen = prior.material()
    lock_path = PREVIOUS.parent / "lock.json"
    if {k: v for k, v in base.load(lock_path).items() if k != "fixed_at"} != frozen:
        raise ValueError("前回の固定画像と方法が変化")
    scan = PREVIOUS.parent.parent / "source-anchored-pilot/point-projection.json"
    measures = {read.identity(r): r for r in base.load(scan)["rows"] if r["matches_component_measurement"]}
    start = base.load(read.v1.REGION / "start.json")
    entries = {read.identity(r): r for r in start["entries"]}
    font = ImageFont.truetype(base.FONTS / "meiryo.ttc", size=13)
    briefs, inputs = {}, {}
    for pub, records in targets.items():
        pack = frozen["packs"][pub]
        normal = {n: all_old[pub][n] for n in pack["images"] if not n.endswith("-point-aid.png")}
        extra = {}
        for i, record in records.items():
            item = expected[pub][i]
            if item["kind"] != "source-backed":
                continue
            key = read.identity(record)
            measure, entry = measures[key], entries[key]
            if measure["points"] != item["dots"]:
                raise ValueError("別実装の画像点数と出典の対応が異なる")
            path = base.BENCH / "corpus/probe-v4/png" / (record["key"] + ".png")
            if base.sha(path) != frozen["image_inputs"][path.name]:
                raise ValueError("補助画像と固定画素が異なる")
            with Image.open(path) as opened:
                extra[f"{i}-position-aux.png"] = position_card(opened.convert("RGB"), entry["box"], measure, i, font)
            p, q = expected_panels(i, entry, measure, pack["source_tiles"])
            item["position_signature"] = read.MARKER.sub(f"⟦dotspan:{p}-{q}⟧", item["signature"])
        images = list(normal) + list(extra)
        inputs[pub] = normal | extra
        prefixes = (read.v1.INTRO + read.v2.NOTICE + read.v3.shared + TASK + base.FORMAT)
        briefs[pub] = {"images": images, "ids": pack["ids"],
                       "image_sha256": [hashlib.sha256(inputs[pub][n]).hexdigest() for n in images],
                       "prompt": prefixes + "、".join(pack["ids"]) + "\n", "source_tiles": pack["source_tiles"]}
    frozen = {"previous_lock_sha256": base.sha(lock_path), "script_sha256": base.sha(Path(__file__)),
              "protocol_sha256": base.sha(HERE / "protocol.md"), "projection_sha256": base.sha(scan),
              "expected_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              "targets": targets, "models": read.pilot.MODELS, "packs": briefs}
    return targets, expected, inputs, frozen


def decision(a, b, anchor):
    if a is None or b is None:
        return "both-unreadable" if a is b else "one-unreadable"
    if anchor["kind"] == "known-control":
        if a != b:
            return "control-disagreement"
        return "matches-control" if a == anchor["exact"] else "differs-from-control"
    if a != b:
        return "different-body" if MARKER.sub("", a) != MARKER.sub("", b) else "different-position"
    if a == anchor["position_signature"] and len(MARKER.findall(a)) == 1:
        return "body-position-plus-image-count-and-source"
    if a == anchor["exact"]:
        return "agreed-source-spelling"
    return "agreement-insufficient"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "run"))
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--lock-sha256")
    args = cli.parse_args()
    _, gold, images, fixed = material()
    if args.action == "prepare":
        if LOCK.exists() or ASSETS.exists():
            raise FileExistsError("固定の情報を上書きしない")
        for pub, pictures in images.items():
            dst = ASSETS / pub
            dst.mkdir(parents=True)
            for n, raw in pictures.items():
                (dst / n).write_bytes(raw)
        base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
        print(base.sha(LOCK), {pub: len(pics) for pub, pics in images.items()}, flush=True)
    else:
        read.HERE, read.OUT, read.ASSETS, read.LOCK = HERE, OUT, ASSETS, LOCK
        read.material, read.decision = material, decision
        read.execute(args, gold, images, fixed)


if __name__ == "__main__":
    main()
