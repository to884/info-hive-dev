"""画像順と出典を固定して、未読の開発行で補助付きの二読を確かめる。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
AID = HERE.parent / "source-anchored-pilot-v2/run.py"
spec = importlib.util.spec_from_file_location("aid_pilot", AID)
aid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aid)
old, base = aid.old, aid.base
v1, v2, pilot = old.v1, old.v2, old.pilot
OUT = pilot.trial.ROOT / HERE.name
SEED = "adr0025-heldout-source-reference-20261119"
ASSETS, LOCK = OUT / "cards", HERE / "lock.json"


def code(p):
    return base.sha(p)


def deterministic(rows, key, count):
    if len(rows) < count:
        raise ValueError("事前登録の選定数に満たない")
    return sorted(rows, key=lambda r: hashlib.sha256(
        f"{SEED}/{key}/{r['key']}/{r['line_index']}".encode()).digest())[:count]


def inventory():
    parent = HERE.parent
    paths = {"provisional": parent / "provisional-dot-transcriptions/result.json",
             "provisional_text": base.BENCH / "corpus/provisional-dot-transcriptions/full-lines.json",
             "scan": parent / "dot-layout-v2/result.json",
             "source_render": parent / "dot-layout-v2/source-render-objects.json",
             "middle_dot": parent / "dot-layout-v2/source-middle-dot-runs.json",
             "projection": parent / "source-anchored-pilot/point-projection.json",
             "v9_start": v1.REGION / "start.json", "v9_final": v1.REGION / "final.json"}
    read = {k: base.load(p) for k, p in paths.items()}
    manifest = {k: code(p) for k, p in paths.items()}
    if (manifest["v9_start"] != read["v9_final"]["start_sha256"]
            or manifest["provisional_text"] != read["provisional"]["private_full_lines_sha256"]):
        raise ValueError("元の固定画像または仮転記が異なる")
    for name, path in (("first", parent / "source-anchored-pilot/lock.json"),
                       ("aided_first", aid.HERE / "lock.json"),
                       ("geometry", parent / "actual-geometry-pilot-v3/lock.json")):
        read[name], manifest[name] = base.load(path), code(path)
    excluded = {old.identity(r) for name in ("first", "aided_first", "geometry")
                for rows in read[name]["targets"].values() for r in rows.values()}
    evidence = {old.identity(r): r for r in read["scan"]["geometries"]}
    render = {old.identity(r) for r in read["source_render"]["rows"] if r["same_pixel_components"]}
    middle = {old.identity(r) for r in read["middle_dot"]["rows"] if r["covered"] or r["pairwise_covered"]}
    projection = {old.identity(r): r for r in read["projection"]["rows"] if r["matches_component_measurement"]}
    entries = {old.identity(r): r for r in read["v9_start"]["entries"]}
    anchors = {}
    stable = read["v9_final"]["rows"]
    dataset = base.BENCH / "corpus"
    for pub, pages in old.PAGES.items():
        ground_path = dataset / "public" / (pub + ".truth.json")
        manifest[pub + "_truth"] = code(ground_path)
        ground = {f"{pub}-p{p['page']:04d}": p["lines"] for p in base.load(ground_path)["pages"]}
        for page in pages:
            reg_path = dataset / "public/region-v9" / (page + ".json")
            geom_path = dataset / "region-repair-v9/geometry" / (page + ".json")
            reg, geom = base.load(reg_path), base.load(geom_path)
            if code(geom_path) != reg["geometry_sha256"]:
                raise ValueError("保存した字形が固定資料と違う")
            manifest[page + "_region"], manifest[page + "_geometry"] = code(reg_path), code(geom_path)
            for row in read["provisional_text"]:
                ident = old.identity(row)
                if row["key"] != page or ident in excluded or ident not in projection:
                    continue
                expression = old.scalar_proof(row, evidence, render, middle, ground[page], geom, reg)
                if expression:
                    anchors[ident] = (row, expression)
    return stable, evidence, projection, entries, read["v9_start"]["assets"], excluded, anchors, manifest


def compose():
    historical, evidence, projection, entries, source_index, excluded, anchors, manifest = inventory()
    fontfile = base.FONTS / "meiryo.ttc"
    font, small = (ImageFont.truetype(fontfile, size=n) for n in (17, 13))
    expected, inputs, packages, targets = {}, {}, {}, {}
    taken = set()
    for pub, pages in old.PAGES.items():
        positives = [r for r, _ in anchors.values() if r["key"].startswith(pub + "-p")]
        guards = [r for r in historical if r["key"].startswith(pub + "-p") and r["status"] == "readable"
                  and r["allocation_axis"] == "x" and 80 < r["box"][2] <= 235
                  and old.identity(r) not in excluded
                  and not evidence.get(old.identity(r), {}).get("runs")]
        for page in pages:
            name = f"pack-{len(packages):02d}"
            rows = deterministic([r for r in positives if r["key"] == page], page, 3)
            control, = deterministic([r for r in guards if old.identity(r) not in taken], page + "/control", 1)
            chosen = deterministic(rows + [control], name + "/order", 4)
            targets[name], expected[name], tiles, pictures = {}, {}, {}, {}
            for n, r in enumerate(chosen, 1):
                marker = f"S{n:02d}"
                key, line_index = old.identity(r)
                taken.add((key, line_index))
                if r is control:
                    guess = {"kind": "known-control", "exact": base.normalize(r["text"])}
                else:
                    guess = anchors[key, line_index][1]
                targets[name][marker] = {"key": key, "line_index": line_index, "kind": guess["kind"]}
                expected[name][marker] = guess
                card_images, trace = v2.make_cards(entries[key, line_index], source_index, marker, font)
                pictures.update(card_images)
                tiles.update(trace)
                if guess["kind"] == "source-backed":
                    raster = base.BENCH / "corpus/probe-v4/png" / (key + ".png")
                    actual = base.load(base.BENCH / "corpus/public/region-v9" / (key + ".json"))["image_sha256"]
                    if code(raster) != actual:
                        raise ValueError("補助に使う固定画像が異なる")
                    manifest[raster.name] = actual
                    with Image.open(raster) as im:
                        pictures[f"{marker}-point-aid.png"] = aid.make_aid(im.convert("RGB"), entries[key, line_index]["box"],
                                                                          projection[key, line_index], marker, small)
            order = sorted(n for n in pictures if not n.endswith("-point-aid.png")) + sorted(
                n for n in pictures if n.endswith("-point-aid.png"))
            ids = list(targets[name])
            packages[name] = {"images": order, "ids": ids, "source_tiles": tiles,
                              "image_sha256": [hashlib.sha256(pictures[n]).hexdigest() for n in order],
                              "prompt": v1.INTRO + v2.NOTICE + old.v3.shared + old.INSTRUCTIONS +
                                        aid.GUIDE + base.FORMAT + "、".join(ids) + "\n"}
            inputs[name] = pictures
    files = (Path(__file__), HERE / "protocol.md", AID, aid.OLD_FILE, old.V3, Path(v2.__file__), Path(v1.__file__),
             Path(base.__file__), Path(pilot.__file__), Path(pilot.opus.__file__), fontfile)
    manifest.update({p.parent.name + "/" + p.name: code(p) for p in files})
    packed = {"sources": manifest, "expected_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True,
                                                                                ensure_ascii=False).encode()).hexdigest(),
              "seed": SEED, "models": pilot.MODELS, "effort": "medium", "targets": targets,
              "packs": packages, "eligible_unread_rows": len(anchors)}
    return expected, inputs, packed


def outcome(left, right, target):
    decision = old.decision(left, right, target)
    if decision != "unresolved":
        return decision
    if left is None or right is None:
        return "both-unreadable" if left is right else "one-unreadable"
    if old.MARKER.sub("", left) != old.MARKER.sub("", right):
        return "different-body"
    return "different-points-or-position"


def run(args, expected, assets, fixed):
    if args.lock_sha256 != code(LOCK) or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != fixed:
        raise ValueError("固定済みの試料と読みの条件が異なる")
    for pack, cards in assets.items():
        if any((ASSETS / pack / n).read_bytes() != value for n, value in cards.items()):
            raise ValueError("配布画像のハッシュが異なる")
    paths = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    pilot.OUT = OUT / "reads"
    with (OUT / "started.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "started": base.utc_now()}, stream)
    votes, receipts, errors = {}, [], []
    names = list(fixed["packs"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for off in range(0, len(names), 2):
            tasks = {}
            for name in names[off:off + 2]:
                package = {k: v for k, v in fixed["packs"][name].items() if k != "source_tiles"}
                study = {"image_order_by_sheet": {"1": package["images"]},
                         "image_sha256": dict(zip(package["images"], package["image_sha256"], strict=True))}
                rows = [{"id": i, "sheet": 1} for i in package["ids"]]
                for who, exe in paths.items():
                    job = pool.submit(pilot.read, exe, who, name, package, rows, ASSETS / name, study)
                    tasks[job] = name, who
            for job in as_completed(tasks):
                name, who = tasks[job]
                try:
                    values, receipt = job.result()
                    votes[name, who] = values
                    receipts.append(receipt)
                except Exception as error:
                    errors.append({"pack": name, "reader": who, "type": type(error).__name__})
            with (OUT / f"batch-{off//2 + 1}.json").open("x", encoding="utf-8") as stream:
                json.dump({"receipts": receipts, "errors": errors}, stream, ensure_ascii=False)
    if errors or len({r["session"] for r in receipts}) != 2 * len(names):
        raise ValueError(f"規定の独立した全票がそろわない: {errors}")
    if compose()[-1] != fixed or code(LOCK) != args.lock_sha256:
        raise ValueError("読取の前後で固定が変化")
    outcomes = {name: {i: {"kind": target["kind"],
                           "result": outcome(votes[name, "sol"][i], votes[name, "opus"][i], target)}
                       for i, target in truths.items()} for name, truths in expected.items()}
    counts = {kind: Counter(r["result"] for values in outcomes.values() for r in values.values() if r["kind"] == kind)
              for kind in ("source-backed", "known-control")}
    advance = (counts["source-backed"]["physical-agreement-plus-source"] >= 10
               and counts["known-control"]["differs-from-control"] == 0)
    with (HERE / "result.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "outcomes": outcomes, "counts": counts,
                   "advance": advance, "receipts": receipts}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"counts": counts, "advance": advance}, ensure_ascii=False), flush=True)


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
            raise FileExistsError("事前固定を上書きしない")
        for name, pictures in images.items():
            directory = ASSETS / name
            directory.mkdir(parents=True)
            for item, data in pictures.items():
                (directory / item).write_bytes(data)
        base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
        print(code(LOCK), {k: len(v) for k, v in images.items()}, fixed["eligible_unread_rows"], flush=True)
    else:
        run(args, expected, images, fixed)


if __name__ == "__main__":
    main()
