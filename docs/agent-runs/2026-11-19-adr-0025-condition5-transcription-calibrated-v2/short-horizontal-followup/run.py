"""短い白書の六つの未決定行を、原画素の拡大によって確認する。"""

import argparse
import hashlib
import importlib.util
import inspect
from pathlib import Path

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "short-mixed-axis-pilot/run.py"
spec = importlib.util.spec_from_file_location("short_mixed", PILOT)
short = importlib.util.module_from_spec(spec)
spec.loader.exec_module(short)
base, pilot, figure, v2 = short.base, short.pilot, short.figure, short.v2
OUT, LOCK = short.OUT.parent / HERE.name, HERE / "lock.json"
SEED = "adr0025-short-whitepaper-followup-20261119"
PAGES = ("disaster-p0092", "defense-p0089")


def material():
    lock, result = short.LOCK, PILOT.parent / "result.json"
    previous, counts = base.load(lock), base.load(result)
    if counts["lock_sha256"] != base.sha(lock):
        raise ValueError("白書の先行結果の固定が違う")
    used = {tuple(item) for r in previous["identities"].values() for item in r.values()}
    region = short.REGION
    start_path, final_path = region / "start.json", region / "final.json"
    start, final = base.load(start_path), base.load(final_path)
    if final["start_sha256"] != base.sha(start_path):
        raise ValueError("固定画像と未決定履歴が違う")
    entry = {(r["key"], r["line_index"]): r for r in start["entries"]}
    font_path = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    cards, packs, expected = {}, {}, {}
    for p, page in enumerate(PAGES):
        pool = [r for r in final["rows"] if r["key"] == page and (page, r["line_index"]) not in used
                and r["allocation_axis"] == "x" and 16 <= r["box"][2] <= 120 and 12 <= r["box"][3] <= 35]
        pending = [r for r in pool if r["status"] == "unreadable"]
        if len(pending) != 3:
            raise ValueError("残りの短い横枠が3行と違う")
        rows = pending + short.pick(pool, page, "readable", 1)
        rows.sort(key=lambda r: hashlib.sha256(f"{SEED}/{page}/{r['line_index']}".encode()).digest())
        name = f"pack-{p:02d}"
        primary, secondary, targets = {}, {}, {}
        for at, row in enumerate(rows, 1):
            identity, label = (page, row["line_index"]), f"W{at:02d}"
            record = entry[identity]
            low = v2.source_views(record)[0]
            if low["display_scale"] != 3 or any(type(a) is not int for a in low["target_rectangle"]):
                raise ValueError("固定150 DPIの倍率か整数の枠が違う")
            pictures, _ = v2.make_cards(record, start["assets"], label, font)
            detailed, _ = figure.detailed(record, label, start["assets"], font)
            primary.update(pictures)
            secondary.update(detailed | {f"{label}-ruler.png": short.ruler(record, label, start["assets"], font)})
            targets[label] = {"key": page, "line_index": identity[1], "previous": row["status"],
                              "text": base.normalize(row["text"]) if row["status"] == "readable" else None}
        cards[name], expected[name] = primary | secondary, targets
        images, ids = sorted(primary) + sorted(secondary), list(targets)
        packs[name] = {"images": images, "ids": ids, "image_sha256": [hashlib.sha256(cards[name][n]).hexdigest() for n in images],
                       "prompt": v2.v1.INTRO + v2.NOTICE + figure.old.shared + short.GUIDE + base.FORMAT + "、".join(ids) + "\n"}
    pins = (Path(__file__), HERE / "protocol.md", PILOT, lock, result, start_path, final_path, font_path, short.PILOT,
            Path(pilot.__file__), Path(pilot.opus.__file__), Path(base.__file__), Path(v2.__file__), Path(v2.v1.__file__),
            Path(figure.old.__file__), Path(inspect.getfile(base.normalize)))
    inputs = {p.as_posix(): base.sha(p) for p in pins}
    if len(inputs) != len(set(pins)):
        raise ValueError("固定資料のパスが衝突した")
    manifest = {"packs": packs, "inputs": inputs, "models": pilot.MODELS,
                "identities": {n: {i: [r["key"], r["line_index"]] for i, r in rr.items()} for n, rr in expected.items()}}
    return cards, expected, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    cards, expected, manifest = material()
    if args.action == "prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("固定を上書きしない")
        for name, files in cards.items():
            dst = OUT / "cards" / name
            dst.mkdir(parents=True)
            for k, value in files.items():
                (dst / k).write_bytes(value)
        base.write_json(LOCK, manifest)
        print(base.sha(LOCK), {n: len(p) for n, p in cards.items()}, flush=True)
    else:
        short.OUT, short.LOCK, short.HERE = OUT, LOCK, HERE
        short.run(args, cards, expected, manifest)
