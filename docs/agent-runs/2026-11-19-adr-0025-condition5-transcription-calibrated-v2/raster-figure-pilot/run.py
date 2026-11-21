"""小さい図表文字の固定450 DPIを整数倍表示し、独立した画像二読を比較する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EXISTING = HERE.parent / "actual-geometry-pilot-v3/run.py"
spec = importlib.util.spec_from_file_location("existing_images", EXISTING)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base, v2, pilot = old.base, old.v2, old.v2.pilot
REGION, OUT = v2.v1.REGION, v2.OUT.parent / HERE.name
LOCK = HERE / "lock.json"
SEED, PAGE = "adr0025-raster-figure-20261119", "disaster-p0107"
GUIDE = (
    "後半の『細部』は同じ450 DPI画像を最近傍で拡大した補助です。番号をつないで左右の重複を1回だけ転記してください。"
    "赤い枠のすぐ外も字形を判断するために見てください。形式や意味から見えない字や点を補わないでください。"
    "色の付いた見本や図表の線を文字に置き換えません。補助の横方向の数字は座標であり、本文ではありません。\n"
)


def ordered(rows, bucket):
    return sorted(rows, key=lambda r: hashlib.sha256(f"{SEED}/{bucket}/{r['line_index']}".encode()).digest())


def detailed(entry, ident, image_index, font):
    view = entry["asset"]["views"][1]
    plain, framed = (next(i for i in view["images"] if i["kind"] == kind) for kind in ("plain", "framed"))
    left, top, right, bottom = view["target_rectangle"]
    assets, source = {}, {}
    for i, (start, end) in enumerate(v2.segments(math.ceil(right - left)), 1):
        parts, traces = [], []
        for item in (plain, framed):
            p = REGION / "assets" / item["image"]
            expected = image_index[p.resolve().as_posix()]
            if base.sha(p) != expected:
                raise ValueError("拡大元の450 DPIが固定と違う")
            with Image.open(p) as image:
                crop = (max(0, math.floor(left + start) - 22), max(0, math.floor(top) - 21),
                        min(image.width, math.ceil(left + end) + 22), min(image.height, math.ceil(bottom) + 21))
                patch = image.crop(crop).convert("RGB")
            parts.append(patch.resize((patch.width * 2, patch.height * 2), Image.Resampling.NEAREST))
            traces.append({"source": item["image"], "sha256": expected, "rectangle": list(crop)})
        w, h = parts[0].size
        card = Image.new("RGB", (w, 2 * h + 62), "white")
        draw = ImageDraw.Draw(card)
        draw.text((4, 0), f"{ident}   細部 {i}   横方向 {start}–{end}", font=font, fill="#252525")
        draw.text((4, 19), "450 DPI fixed   枠なし", font=font, fill="#252525")
        draw.text((4, 41 + h), "450 DPI fixed   枠あり", font=font, fill="#252525")
        for offset, pixels in zip((38, 62 + h), parts, strict=True):
            card.paste(pixels, (0, offset))
            if card.crop((0, offset, w, offset + h)).tobytes() != pixels.tobytes():
                raise ValueError("拡大画像の一部が失われた")
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        name = f"{ident}-focus-{i:02d}.png"
        assets[name], source[name] = buffer.getvalue(), traces
    return assets, source


def material():
    start_path, final_path = REGION / "start.json", REGION / "final.json"
    start, final = base.load(start_path), base.load(final_path)
    if final["start_sha256"] != base.sha(start_path):
        raise ValueError("図表の既存画像と記録が違う")
    entries = {r["line_index"]: r for r in start["entries"] if r["key"] == PAGE}
    actual = [r for r in final["rows"] if r["key"] == PAGE and 138 <= r["box"][0] < 1102
              and 209 <= r["box"][1] < 929]
    if any(r["allocation_axis"] != "x" for r in actual):
        raise ValueError("図表の対象軸が異なる")
    unread = [r for r in actual if r["status"] == "unreadable"]
    controls = ordered([r for r in actual if r["status"] == "readable"], "control")[:4]
    categories = [ordered([r for r in unread if condition(r["box"][3])], n)[:4]
                  for n, condition in enumerate((lambda h: h <= 9, lambda h: h == 10, lambda h: h >= 11))]
    if len(unread) != 41 or len(controls) != 4 or any(len(c) != 4 for c in categories):
        raise ValueError("事前に決めた図表内の群と行数が違う")
    font_path = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    packs, truth, pictures = {}, {}, {}
    for number, pick in enumerate(zip(*categories, controls, strict=True)):
        subject = ordered(pick, f"pack-{number}")
        name = f"pack-{number:02d}"
        crops, focus, record = {}, {}, {}
        for pos, row in enumerate(subject, 1):
            ident = f"Z{pos:02d}"
            idx = row["line_index"]
            entry = entries[idx]
            primary, _ = v2.make_cards(entry, start["assets"], ident, font)
            extra, _ = detailed(entry, ident, start["assets"], font)
            crops.update(primary)
            focus.update(extra)
            record[ident] = {"line_index": idx, "previous": row["status"],
                             "old_normalized": base.normalize(row["text"]) if row["status"] == "readable" else None}
        all_images = crops | focus
        images = sorted(crops) + sorted(focus)
        ids = list(record)
        packs[name] = {"images": images, "ids": ids,
                       "image_sha256": [hashlib.sha256(all_images[k]).hexdigest() for k in images],
                       "prompt": v2.v1.INTRO + v2.NOTICE + old.shared + GUIDE + base.FORMAT + "、".join(ids) + "\n"}
        truth[name], pictures[name] = record, all_images
    bound = {"inputs": {p.name: base.sha(p) for p in (start_path, final_path, Path(__file__), HERE / "protocol.md",
                                                      EXISTING, Path(v2.__file__), Path(base.__file__), font_path)},
             "packs": packs, "targets": {p: {i: r["line_index"] for i, r in v.items()} for p, v in truth.items()},
             "models": pilot.MODELS}
    return bound, truth, pictures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    manifest, truth, images = material()
    if args.action == "prepare":
        if LOCK.exists() or OUT.exists():
            raise FileExistsError("画像と方法を上書きしない")
        for name, files in images.items():
            target = OUT / "cards" / name
            target.mkdir(parents=True)
            for item, pixels in files.items():
                (target / item).write_bytes(pixels)
        base.write_json(LOCK, manifest)
        print(base.sha(LOCK), {k: len(i) for k, i in images.items()}, flush=True)
        return
    if (manifest != base.load(LOCK) or base.sha(LOCK) != args.lock_sha256
            or any((OUT / "cards" / p / name).read_bytes() != raw for p, items in images.items() for name, raw in items.items())):
        raise ValueError("固定画像、手順、対象のSHAが違う")
    with (OUT / "started.json").open("x", encoding="utf-8") as f:
        json.dump({"lock": args.lock_sha256}, f)
    pilot.OUT = OUT / "reads"
    total, rows_out, receipts, sessions = {}, {}, [], set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, pack in manifest["packs"].items():
            study = {"image_order_by_sheet": {"1": pack["images"]},
                     "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            jobs = {r: pool.submit(pilot.read, exe.resolve(), r, name, pack, rows, OUT / "cards" / name, study)
                    for r, exe in (("sol", args.codex), ("opus", args.claude))}
            received = {}
            for role, job in jobs.items():
                votes, receipt = job.result()
                if receipt["session"] in sessions:
                    raise ValueError("同一の会話を再利用した")
                sessions.add(receipt["session"])
                receipts.append(receipt)
                received[role] = votes
            rows_out[name] = {}
            for i, item in truth[name].items():
                a, b = (received[r][i] for r in ("sol", "opus"))
                if a is None or b is None:
                    verdict = "both-unknown" if a is b else "one-unknown"
                elif a != b:
                    verdict = "disagreement"
                elif not a:
                    verdict = "agreed-empty"
                elif item["previous"] == "readable":
                    verdict = "matches-control" if a == item["old_normalized"] else "differs-from-control"
                else:
                    verdict = "new-agreement"
                group = total.setdefault(item["previous"], Counter())
                group[verdict] += 1
                rows_out[name][i] = verdict
    advance = (total["unreadable"]["new-agreement"] >= 6
               and not (total["readable"]["differs-from-control"] or total["readable"]["agreed-empty"]))
    base.write_json(HERE / "result.json", {"lock_sha256": args.lock_sha256, "counts": total, "advance": advance,
                                           "rows": rows_out, "receipts": receipts, "scope": "development-only"})
    print(json.dumps({"counts": total, "advance": advance}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
