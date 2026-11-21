"""実資料の未決定と既存確定を、正しい箱寸法と固定画像で比較する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "actual-geometry-pilot/run.py"
spec = importlib.util.spec_from_file_location("actual_v1", V1)
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
base, pilot = v1.base, v1.pilot
OUT = pilot.trial.ROOT / HERE.name
ASSETS = OUT / "cards"
LOCK = HERE / "lock.json"
SIDES = ("evaluation", "evaluation3")
ARMS = v1.ARMS
STRATA = ("x-detail", "x-basic", "y")
SEED = "adr0025-condition5-real-geometry-v2-20261119"
MARGIN = 32
STEP = 448
SPAN = 512
MAX_SOURCE = (800, 120)
NOTICE = (
    "同じIDに複数のカードがあれば、上部の番号順に位置を確認してください。"
    "隣のカードには一部が重複します。同じ字を二度転記しないでください。"
    "一部だけ与えられている場合は全カードを照合してから、行全体を一つの回答にしてください。\n"
)


def source_views(entry):
    views = entry["asset"]["views"]
    low = views[0]["target_rectangle"]
    if views[0]["dpi"] != 150 or views[0]["display_scale"] != 3 or views[1]["dpi"] != 450:
        raise ValueError("150 DPIか450 DPIの表示資料が異なる")
    if [low[2] - low[0], low[3] - low[1]] != [3 * v for v in entry["box"][2:]]:
        raise ValueError("固定150 DPIの枠とOCRの箱寸法が異なる")
    return views


def stratum(row, entry):
    views = source_views(entry)
    if row["allocation_axis"] == "y":
        return "y"
    return "x-detail" if any(i["details"] for v in views for i in v["images"]) else "x-basic"


def choose(final, entries):
    options = {}
    for row in final:
        if row["side"] not in SIDES:
            continue
        entry = entries[v1.canonical(row)]
        width, height = entry["box"][2:]
        bucket = stratum(row, entry)
        if max(width, height) > MAX_SOURCE[0] or min(width, height) > MAX_SOURCE[1]:
            continue
        key = row["side"], bucket, row["status"] == "unreadable"
        digest = hashlib.sha256(f"{SEED}/{row['key']}/{row['line_index']}".encode()).hexdigest()
        options.setdefault(key, []).append((digest, row))
    result = {}
    for side in SIDES:
        picks = [min(options[side, bucket, unknown], key=lambda p: p[0])[1]
                 for bucket in STRATA for unknown in (False, True)]
        random.Random(f"{SEED}/{side}").shuffle(picks)
        result[side] = picks
    return result, {"|".join(str(v) for v in k): len(v) for k, v in options.items()}


def segments(length):
    if length <= SPAN:
        return [(0, length)]
    starts = list(range(0, length - SPAN, STEP)) + [length - SPAN]
    return [(start, start + SPAN) for start in sorted(set(starts))]


def source_crop(view, fractions, path, expected):
    if base.sha(path) != expected:
        raise ValueError("表示元の画像が変わった")
    l, t, r, b = view["target_rectangle"]
    x0, y0, x1, y1 = fractions
    with Image.open(path) as src:
        box = (max(0, math.floor(l + (r - l) * x0) - MARGIN),
               max(0, math.floor(t + (b - t) * y0) - MARGIN),
               min(src.width, math.ceil(l + (r - l) * x1) + MARGIN),
               min(src.height, math.ceil(t + (b - t) * y1) + MARGIN))
        return src.crop(box).convert("RGB"), box


def make_cards(entry, image_index, ident, font):
    views = source_views(entry)
    width, height = (3 * v for v in entry["box"][2:])
    grid = [(l/width, t/height, r/width, b/height)
            for t, b in segments(height) for l, r in segments(width)]
    images, files = {}, {}
    for n, fractions in enumerate(grid, 1):
        tiles, parts = [], []
        for view in views:
            required = [i for i in view["images"] if i["kind"] in ("plain", "framed")]
            if [item["kind"] for item in required] != ["plain", "framed"]:
                raise ValueError("枠あり・なしの順序が異なる")
            for item in required:
                path = v1.REGION / "assets" / item["image"]
                sha = image_index[path.resolve().as_posix()]
                crop, rect = source_crop(view, fractions, path, sha)
                tiles.append((view["dpi"], item["kind"], crop))
                parts.append({"source": item["image"], "sha256": sha, "rectangle": list(rect)})
        w = max(img.width for _, _, img in tiles) + 10
        h = max(img.height for _, _, img in tiles) + 25
        card = Image.new("RGB", (2 * w, 27 + 2 * h), "#fff")
        labels = ImageDraw.Draw(card)
        labels.text((5, 0), f"{ident}   軸{entry['allocation_axis']}   {n}/{len(grid)}",
                    font=font, fill="#151515")
        for i, (dpi, kind, img) in enumerate(tiles):
            x, y = i % 2 * w, 27 + i // 2 * h
            labels.text((x + 5, y), f"{dpi} DPI {'枠なし' if kind == 'plain' else '枠あり'}",
                        font=font, fill="#151515")
            card.paste(img, (x, y + 23))
            if card.crop((x, y + 23, x + img.width, y + 23 + img.height)).tobytes() != img.tobytes():
                raise ValueError("元画像と配布する画素が違う")
        raw = io.BytesIO()
        card.save(raw, format="PNG")
        name = f"{ident}-{n:02d}.png"
        images[name], files[name] = raw.getvalue(), parts
    return images, files


def material():
    start_path, final_path = v1.REGION / "start.json", v1.REGION / "final.json"
    start, final = base.load(start_path), base.load(final_path)
    entries = {v1.canonical(r): r for r in start["entries"]}
    if final["start_sha256"] != base.sha(start_path) or len(entries) != 2865:
        raise ValueError("旧版の正式な入力が異なる")
    if set(entries) != {v1.canonical(r) for r in final["rows"]}:
        raise ValueError("旧版の対象が異なる")
    chosen, counts = choose(final["rows"], entries)
    font_file = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    targets, pictures, packs = {}, {}, {}
    for side, rows in chosen.items():
        targets[side] = {}
        parts, images = {}, {}
        for number, row in enumerate(rows, 1):
            ident = f"G{number:02d}"
            entry = entries[v1.canonical(row)]
            if any(row[k] != entry[k] for k in ("box", "ocr_text_sha256", "allocation_axis")):
                raise ValueError("最終票と元画像で固定した行が異なる")
            blobs, sources = make_cards(entry, start["assets"], ident, font)
            images.update(blobs)
            parts.update(sources)
            targets[side][ident] = row
        pictures[side] = images
        names = list(images)
        ids = list(targets[side])
        packs[side] = {"inputs": parts, "arms": {
            arm: {"images": names, "image_sha256": [hashlib.sha256(images[n]).hexdigest() for n in names],
                  "ids": ids, "prompt": v1.INTRO + NOTICE + extra + base.FORMAT + "、".join(ids) + "\n"}
            for arm, extra in zip(ARMS, ("", v1.GUIDE), strict=True)
        }}
    deps = (V1, v1.GEOMETRY, Path(base.__file__), Path(pilot.opus.__file__), font_file)
    fixed = {"script_sha256": base.sha(Path(__file__)), "protocol_sha256": base.sha(HERE / "protocol.md"),
             "dependencies": {path.name: base.sha(path) for path in deps},
             "source_sha256": {"start": base.sha(start_path), "final": base.sha(final_path)},
             "eligible_counts": counts, "seed": SEED, "packs": packs,
             "models": pilot.MODELS, "effort": "medium",
             "targets": {s: {i: {k: r[k] for k in ("key", "line_index", "box", "status", "allocation_axis")}
                             for i, r in rows.items()} for s, rows in targets.items()}}
    return targets, pictures, fixed


def prepare(pictures, fixed):
    if LOCK.exists() or ASSETS.exists():
        raise FileExistsError("既存の固定を上書きできない")
    for side, images in pictures.items():
        directory = ASSETS / side
        directory.mkdir(parents=True)
        for name, data in images.items():
            (directory / name).write_bytes(data)
    base.write_json(LOCK, dict(fixed, fixed_at=base.utc_now()))
    print(base.sha(LOCK), {s: len(i) for s, i in pictures.items()}, flush=True)


def summarize(targets, ballots):
    results, combined = {}, {g: {a: Counter() for a in ARMS} for g in ("known", "unresolved")}
    for side, rows in targets.items():
        outcomes = {}
        for ident, row in rows.items():
            group = "unresolved" if row["status"] == "unreadable" else "known"
            outcomes[ident] = {"previous": group, "arms": {}}
            for arm in ARMS:
                answer = base.consensus([ballots[side, arm, model][ident] for model in pilot.MODELS])
                label = (
                    "unresolved" if answer is None else
                    "candidate-agreement" if group == "unresolved" else
                    "matches-previous" if answer == base.normalize(row["text"]) else "differs-from-previous"
                )
                outcomes[ident]["arms"][arm] = label
                combined[group][arm][label] += 1
        results[side] = outcomes
    old, new = (combined["known"][a] for a in ARMS)
    old_new = [combined["unresolved"][a]["candidate-agreement"] for a in ARMS]
    passed = (old_new[1] >= old_new[0] + 2 and new["matches-previous"] >= old["matches-previous"]
              and new["differs-from-previous"] <= old["differs-from-previous"])
    return {"rows": results, "counts": combined, "advance": passed}


def run(args, targets, pictures, fixed):
    if base.sha(LOCK) != args.lock_sha256 or {k: v for k, v in base.load(LOCK).items() if k != "fixed_at"} != fixed:
        raise ValueError("指定の固定と一致しない")
    for side, images in pictures.items():
        if any((ASSETS / side / p).read_bytes() != raw for p, raw in images.items()):
            raise ValueError("配布画像が固定と異なる")
    with (OUT / "started.json").open("x", encoding="utf-8") as stream:
        json.dump({"lock_sha256": args.lock_sha256, "started": base.utc_now()}, stream)
    executables = {"sol": args.codex.resolve(), "opus": args.claude.resolve()}
    votes, receipts, failures = {}, [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for side in SIDES:
            pilot.OUT = OUT / "reads" / side
            jobs = {}
            for arm, pack in fixed["packs"][side]["arms"].items():
                rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
                index = {"image_order_by_sheet": {"1": pack["images"]},
                         "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
                for model, exe in executables.items():
                    jobs[pool.submit(pilot.read, exe, model, arm, pack, rows, ASSETS / side, index)] = (arm, model)
            for job in as_completed(jobs):
                arm, model = jobs[job]
                try:
                    ballot, receipt = job.result()
                    votes[side, arm, model] = ballot
                    receipts.append(dict(receipt, side=side))
                except Exception as error:
                    failures.append({"side": side, "arm": arm, "model": model, "error": type(error).__name__})
            base.write_json(OUT / ("execution-" + side + ".json"), {"receipts": receipts, "failures": failures})
    if failures or len({r["session"] for r in receipts}) != 8:
        raise RuntimeError(f"独立セッションの受領がそろわない: {failures}")
    if material()[-1] != fixed or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("読取前後で固定が異なる")
    outcome = summarize(targets, votes)
    with (HERE / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(dict(outcome, receipts=receipts, lock_sha256=args.lock_sha256), stream, ensure_ascii=False, indent=2)
    print(json.dumps({"counts": outcome["counts"], "advance": outcome["advance"]}, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    targets, pictures, fixed = material()
    if args.action == "prepare":
        prepare(pictures, fixed)
    else:
        run(args, targets, pictures, fixed)


if __name__ == "__main__":
    main()
