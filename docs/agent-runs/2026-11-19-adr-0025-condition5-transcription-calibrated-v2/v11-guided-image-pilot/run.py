"""両系統の開発票で固定画素の追加表示を検査する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import math
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SLOT_METHOD = HERE.parent / "v11-column-slot-pilot/run.py"
spec = importlib.util.spec_from_file_location("column_slot_development", SLOT_METHOD)
slots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slots)
old, cards, readers = slots.old, slots.cards, slots.readers
LOAD, SHA, NORMALIZE = old.LOAD, old.SHA, old.NORMALIZE
OUT = cards.CORPUS / "reference-v11-guided-image-pilot"
LOCK = HERE / "lock.json"
VERTICAL = (
    "『450 DPIの区画』で、一字全体の画を確かめます。字の意味から書き換えず、筆画が離れていても一字の全体を見ます。"
    "元の枠に所属し、上下のインクの中心が番号の上の赤い目印と下の赤い目印の間に入る字だけを、その番号に書きます。"
    "境界ちょうどなら次の番号で写します。最後の区画は、元の枠に所属する行末の字を写します。"
    "隣にも表示された同じ字を重ねて書かないでください。空の区画は A: のように空にします。"
    "回答のtextの形式は A:甲乙|B:丙丁 です。示す区画の全てを各一度、上から記録してください。"
)
HORIZONTAL = (
    "『450 DPI 細部』を元の画像と照合し、隣の字、記号、図形と区別します。つながりや意味から足さず、"
    "紛らわしい字と括弧も実際の画で一つずつ確かめてください。textは枠内の該当する全文です。"
)


def framed_context(row, mapping, origin, ident, font):
    """枠の近くで行と列のつながりを150 DPIの画素で示す。"""
    page = cards.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if SHA(page) != mapping["sha"]["150_dpi"]:
        raise ValueError("元の固定150 DPIの画像と違う")
    x, y, width, height = row["box"]
    with Image.open(page) as fixed:
        left, top = max(0, x - 132), max(0, y - 150)
        box = left, top, min(fixed.width, x + width + 132), min(fixed.height, y + height + 150)
        pixels = fixed.crop(box).convert("RGB")
    view = pixels.resize((2 * pixels.width, 2 * pixels.height), Image.Resampling.NEAREST)
    panel = Image.new("RGB", (view.width + 16, view.height + 50), "white")
    panel.paste(view, (8, 42))
    draw = ImageDraw.Draw(panel)
    draw.text((8, 7), f"{ident}  行と列のつながり  固定150 DPI", font=font, fill="#222222")
    lx, ly = 8 + 2 * (x - left), 42 + 2 * (y - top)
    draw.rectangle((lx - 2, ly - 2, lx + 2 * width + 1, ly + 2 * height + 1), outline="#b80d18", width=2)
    return {f"{ident}-layout.png": slots.blob(panel)}


def y_cards(mapping, origin, ident, font):
    view = mapping["source_view"]["views"][1]
    fixed = slots.asset(view, origin, "plain")
    left, top, right, bottom = view["target_rectangle"]
    count = math.ceil((bottom - top) / 240)
    edges = [top + 240 * i for i in range(count)] + [bottom]
    names = [chr(ord("A") + i) for i in range(count)]
    tiles = []
    for i, (a, b) in enumerate(zip(edges, edges[1:])):
        x0, y0 = max(0, math.floor(left) - 60), max(0, math.floor(a) - 58)
        x1, y1 = min(fixed.width, math.ceil(right) + 60), min(fixed.height, math.ceil(b) + 58)
        pixels = fixed.crop((x0, y0, x1, y1))
        tile = Image.new("RGB", (pixels.width + 48, pixels.height + 39), "white")
        tile.paste(pixels, (24, 35))
        draw = ImageDraw.Draw(tile)
        draw.text((24, 4), names[i], font=font, fill="#16345a")
        for y in (a, b):
            offset = 35 + round(y - y0)
            draw.line((5, offset, 22, offset), fill="#b80d18", width=2)
            draw.line((tile.width - 22, offset, tile.width - 5, offset), fill="#b80d18", width=2)
        for x in (left, right):
            offset = 24 + round(x - x0)
            draw.line((offset, 23, offset, 33), fill="#b80d18", width=2)
        tiles.append(tile)
    images = {}
    for n in range(0, count, 3):
        batch = tiles[n:n + 3]
        sheet = Image.new("RGB", (sum(i.width for i in batch), max(i.height for i in batch) + 32), "white")
        ImageDraw.Draw(sheet).text((5, 3), f"{ident}  450 DPIの区画  {names[n]}〜{names[n + len(batch) - 1]}",
                                    font=font, fill="#222222")
        x = 0
        for tile in batch:
            sheet.paste(tile, (x, 30))
            x += tile.width
        images[f"{ident}-y-blocks-{n // 3 + 1:02d}.png"] = slots.blob(sheet)
    return images, names


def selection(rows):
    diagnosis = LOAD(cards.HERE / "diagnosis.json")
    if diagnosis["audit_sha256"] != SHA(cards.HERE / "result.json"):
        raise ValueError("旧監査の診断が異なる")
    ids = {(row["key"], row["line_index"]): i for i, row in enumerate(rows)}
    crop_result = LOAD(slots.HERE / "result.json")["rows"]
    already_reproduced = {(r["key"], r["line_index"]) for r in crop_result.values()
                          if r["kind"] == "columns" and r["outcome"] == "agreed-existing-label"}
    selected = {}
    for case in diagnosis["cases"]:
        key = case["key"], case["line_index"]
        if (case["diagnosis"] not in {"technical-incomplete", "source-location-not-proven", "source-unavailable"}
                and key not in already_reproduced):
            selected[ids[key]] = "diagnosis"
    previous = LOAD(old.LOCK)["packs"]
    selected.update({r["entry"]: "control" for r in previous.values() if r["kind"] == "vertical-control"})
    selected.update({ids[k]: "control" for k in [("kanpo1826-p5-p0001", 469), ("kanpo1827-p2-p0001", 374)]})
    counts = Counter(selected.values())
    if counts != {"diagnosis": 11, "control": 4}:
        raise ValueError(f"先に記録した対象と対照に一致しない: {counts}")
    return selected


def visual_plan(row, mapping, origin, ident, font):
    width, height = row["box"][2:]
    if row["allocation_axis"] == "y":
        extras, names = y_cards(mapping, origin, ident, font)
        return "y-blocks", VERTICAL, names, extras
    if 16 <= width <= 120 and 12 <= height <= 35:
        extras, names, _ = slots.aid(row, mapping, origin, ident, font)
        return "x-slots", slots.GUIDE + "『行と列のつながり』で周囲の字が続く方向も見てください。", names, extras
    extra = old.details(mapping["source_view"], ident, False, font)
    return "x-text", HORIZONTAL + cards.GUIDE, [], extra


def material(rows, selected):
    origin = LOAD(cards.PACKS)
    font_path = cards.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    index = {mapping["entry"]: (pack, ident, mapping["image_reference"])
             for pack, data in origin["packs"].items() for ident, mapping in data["mapping"].items()}
    packs, visuals = {}, {}
    for n, (i, category) in enumerate(sorted(selected.items())):
        row = rows[i]
        source, ident, mapping = index[i]
        job = origin["packs"][source]["request"]
        images = {}
        for filename, digest in zip(job["images"], job["image_sha256"], strict=True):
            if filename.startswith(ident + "-"):
                blob = (cards.OUT / "cards" / source / filename).read_bytes()
                if readers.sha(blob) != digest:
                    raise ValueError("前回の固定画像に一致しない")
                images[filename] = blob
        mode, instructions, names, extra = visual_plan(row, mapping, origin, ident, font)
        images.update(extra)
        if mode == "x-slots" or (mode == "y-blocks" and len(names) <= 2):
            images.update(framed_context(row, mapping, origin, ident, font))
        if not 1 <= len(images) <= 24:
            raise ValueError("一行に渡す画像の数が範囲外")
        request = {"ids": [ident], "images": list(images),
                   "image_sha256": [readers.sha(v) for v in images.values()],
                   "prompt": old.INTRO + instructions + old.FORMAT + ident + "。" +
                             (" 区画は " + "、".join(names) + "。" if names else "")}
        name = f"pack-{n:02d}"
        packs[name] = {"entry": i, "category": category, "mode": mode, "partitions": names, "request": request}
        visuals[name] = images
    pins = (Path(__file__), HERE / "protocol.md", SLOT_METHOD, slots.HERE / "lock.json", slots.HERE / "result.json",
            slots.BASE, old.LOCK, cards.PACKS, cards.SOURCE, cards.HERE / "diagnosis.json",
            cards.HERE / "result.json", Path(readers.__file__), Path(cards.__file__), font_path)
    return {"models": cards.MODELS, "inputs": {str(p): SHA(p) for p in pins}, "packs": packs}, visuals


def decoded(answer, pack):
    if answer is None or answer["status"] == "unreadable":
        return None
    if answer["status"] == "empty":
        return "", (), ""
    mode, names = pack["mode"], pack["partitions"]
    if mode == "x-text":
        return "regular", (), NORMALIZE(answer["text"])
    body = answer["text"].split("|")
    style = body.pop(0) if mode == "x-slots" else "top-down"
    if style not in {"V", "H", "top-down"}:
        return None
    parts = {}
    for token in body:
        match = re.fullmatch(r"([A-Z]):(.*)", token.strip())
        if match is None or match[1] in parts:
            return None
        parts[match[1]] = NORMALIZE(match[2])
    if set(parts) != set(names) or not any(parts.values()):
        return None
    sequence = tuple(parts[k] for k in (reversed(names) if style == "V" else names))
    return style, sequence, "".join(sequence)


def execute(args, manifest, images, rows):
    if SHA(LOCK) != args.lock_sha256 or LOAD(LOCK) != manifest:
        raise ValueError("先に固定した試験と一致しない")
    executables = {"gpt": args.codex, "claude": args.claude}
    runtimes = {}
    for family, path in executables.items():
        version = subprocess.run([str(path), "--version"], capture_output=True, check=True, timeout=20)
        runtimes[family] = {"path": str(path.resolve()), "sha256": SHA(path),
                            "version": version.stdout.decode("utf-8").strip(), "reader_sha256": SHA(Path(readers.__file__))}
    for name, blobs in images.items():
        folder = OUT / "cards" / name
        if set(blobs) != {p.name for p in folder.iterdir()} or any((folder / k).read_bytes() != v for k, v in blobs.items()):
            raise ValueError("固定した画像の配布先にずれがある")
    readers.save_once(OUT / "started.json", readers.encoded({"lock_sha256": args.lock_sha256, "runtime": runtimes}))
    answers, seen = {}, set()
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = {}
        for name, pack in manifest["packs"].items():
            for role, model in manifest["models"].items():
                task = pool.submit(readers.read, runtimes[role], role, model, pack["request"],
                                   OUT / "cards" / name, OUT / "reads" / name / role)
                tasks[task] = name, role
        for task in as_completed(tasks):
            name, role = tasks[task]
            result = task.result()
            session = result.get("session")
            if session is not None:
                if session in seen:
                    raise ValueError("同じセッションを再利用した")
                seen.add(session)
            answers[name, role] = result
    counts, summary = {}, {}
    for name, pack in manifest["packs"].items():
        row = rows[pack["entry"]]
        ident, = pack["request"]["ids"]
        ballots = [answers[name, role] for role in manifest["models"]]
        a, b = (decoded(v.get("answers", {}).get(ident), pack) for v in ballots)
        if a is None or b is None or a != b:
            verdict = "unresolved"
        elif "⟦" in a[-1]:
            verdict = "point-needs-proof"
        elif all(a[-1] == NORMALIZE(label["text"]) for label in row["targets"].values() if label["known"]):
            verdict = "agreed-existing-label"
        else:
            verdict = "agreed-different-label"
        summary[name] = {"key": row["key"], "line_index": row["line_index"], "kind": pack["category"],
                         "mode": pack["mode"], "outcome": verdict,
                         "receipts": {role: {k: v for k, v in answers[name, role].items() if k != "answers"}
                                      for role in manifest["models"]}}
        counts.setdefault(f"{pack['mode']}/{pack['category']}", Counter())[verdict] += 1
    readers.save_once(HERE / "result.json", readers.encoded({"scope": "development-only", "lock_sha256": SHA(LOCK),
                                                            "counts": counts, "rows": summary}))
    print(counts, flush=True)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare", "run"))
    cli.add_argument("--codex", type=Path)
    cli.add_argument("--claude", type=Path)
    cli.add_argument("--lock-sha256")
    args = cli.parse_args()
    rows = LOAD(cards.SOURCE)["selected"]
    manifest, images = material(rows, selection(rows))
    if args.action == "run":
        execute(args, manifest, images, rows)
    else:
        if OUT.exists() or LOCK.exists():
            raise FileExistsError("固定した開発試験がすでにある")
        for name, blobs in images.items():
            folder = OUT / "cards" / name
            folder.mkdir(parents=True, exist_ok=False)
            for k, v in blobs.items():
                (folder / k).write_bytes(v)
        readers.save_once(LOCK, readers.encoded(manifest))
        print(SHA(LOCK), len(images), "行", flush=True)


if __name__ == "__main__":
    main()
