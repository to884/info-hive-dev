"""別に固定した行で、元画像の位置の二読と独立した点数を結合できるか確かめる。"""

import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
FORMER = HERE.parent / "source-anchored-batches/run.py"
POSITION = HERE.parent / "source-anchored-position-pilot/run.py"


def imported(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


old = imported("numbered_confirmation", FORMER)
position = imported("position_pilot", POSITION)
base = old.base
OUT = old.OUT.parent / HERE.name
ASSETS, LOCK = OUT / "cards", HERE / "lock.json"
compose_numbered = old.compose
former_dir = FORMER.parent


def compose():
    holding = old.HERE
    old.HERE = former_dir
    try:
        expected, numbered_assets, numbered = compose_numbered()
    finally:
        old.HERE = holding
    previous = former_dir / "lock.json"
    if {k: v for k, v in base.load(previous).items() if k != "fixed_at"} != numbered:
        raise ValueError("前回の行と画像の固定が変化")
    historical, points, projection, entries, source_index, excluded, anchors, manifest = old.inventory()
    del historical, points, source_index, excluded, anchors
    fontfile = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(fontfile, size=13)
    images_by_pack, packs = {}, {}
    for name, rows in numbered["targets"].items():
        pack = numbered["packs"][name]
        originals = {n: numbered_assets[name][n] for n in pack["images"] if not n.endswith("-point-aid.png")}
        additions = {}
        for i, row in rows.items():
            entry = expected[name][i]
            if entry["kind"] != "source-backed":
                continue
            ident = old.old.identity(row)
            region = entries[ident]
            measured = projection[ident]
            if measured["points"] != entry["dots"]:
                raise ValueError("二つの画像計測と出典の個数が違う")
            page = base.BENCH / "corpus/probe-v4/png" / (row["key"] + ".png")
            if base.sha(page) != numbered["sources"][page.name]:
                raise ValueError("補助画像の原画が固定と異なる")
            with Image.open(page) as source:
                additions[f"{i}-position-aux.png"] = position.position_card(
                    source.convert("RGB"), region["box"], measured, i, font)
            p, q = position.expected_panels(i, region, measured, pack["source_tiles"])
            entry["position_signature"] = old.old.MARKER.sub(f"⟦dotspan:{p}-{q}⟧", entry["signature"])
        assets = originals | additions
        images_by_pack[name] = assets
        ids = pack["ids"]
        text = old.v1.INTRO + old.v2.NOTICE + old.old.v3.shared + position.TASK + base.FORMAT + "、".join(ids) + "\n"
        packs[name] = {"images": list(assets), "ids": ids, "prompt": text, "source_tiles": pack["source_tiles"],
                       "image_sha256": [hashlib.sha256(data).hexdigest() for data in assets.values()]}
    refs = (Path(__file__), HERE / "protocol.md", FORMER, POSITION, previous, Path(inspect.getfile(base.normalize)))
    fused = {"previous_lock_sha256": base.sha(previous), "sources": manifest,
             "dependencies": {p.parent.name + "/" + p.name: base.sha(p) for p in refs},
             "expected_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
             "packs": packs, "models": old.pilot.MODELS, "targets": numbered["targets"]}
    return expected, images_by_pack, fused


def outcome(left, right, expected):
    result = position.decision(left, right, expected)
    return "physical-agreement-plus-source" if result == "body-position-plus-image-count-and-source" else result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    p.add_argument("--lock-sha256")
    args = p.parse_args()
    expected, images, fixed = compose()
    if args.action == "prepare":
        if LOCK.exists() or ASSETS.exists():
            raise FileExistsError("固定した情報を上書きしない")
        for name, items in images.items():
            dst = ASSETS / name
            dst.mkdir(parents=True)
            for n, raw in items.items():
                (dst / n).write_bytes(raw)
        base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
        print(base.sha(LOCK), {name: len(cards) for name, cards in images.items()}, flush=True)
    else:
        old.OUT, old.HERE, old.ASSETS, old.LOCK = OUT, HERE, ASSETS, LOCK
        old.compose, old.outcome = compose, outcome
        old.run(args, expected, images, fixed)


if __name__ == "__main__":
    main()
