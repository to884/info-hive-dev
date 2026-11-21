"""固定画像の短い枠を拡大し、軸と所属の目盛り付き画像で新規二読する。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "raster-figure-pilot/run.py"
spec = importlib.util.spec_from_file_location("figure", PILOT)
figure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figure)
base, pilot, v2 = figure.base, figure.pilot, figure.v2
OUT, REGION = figure.OUT.parent / HERE.name, figure.REGION
LOCK = HERE / "lock.json"
PAGES = ("kanpo1827-p2-p0001", "kanpo1826-p5-p0001", "kanpo1826-p6-p0001", "disaster-p0092")
SEED = "adr0025-short-x-ownership-20261119"
GUIDE = (
    "固定150 DPIの赤い目印の内側が元の枠の正確な範囲です。補助の目印は元画像の外側にだけ描いています。"
    "枠をまたぐ字は、450 DPIで字全体を見つけてから、固定150 DPIの左右方向の半分以上と上下の中心で所属を判断してください。"
    "縦書きに見えるときは、所属する字だけを右の列から、各列では上から下へ読んでください。"
    "離れた点が同じ字の一部か、独立した記号かを両方の解像度で確認します。"
    "元画像の周囲の文字は所属する場合だけ含めます。全体が読めなければ未決定にしてください。\n"
)


def ruler(entry, ident, index, font):
    view = entry["asset"]["views"][0]
    p = REGION / "assets" / next(x["image"] for x in view["images"] if x["kind"] == "plain")
    if base.sha(p) != index[p.resolve().as_posix()]:
        raise ValueError("補助に使う元画像が固定と違う")
    x, y, r, b = view["target_rectangle"]
    with Image.open(p) as img:
        tile = (max(0, x - 51), max(0, y - 45), min(img.width, r + 51), min(img.height, b + 45))
        patch = img.crop(tile).convert("RGB")
    w, h = patch.width * 2, patch.height * 2
    u, v, z, q = tuple(int(a) for a in (2 * (x - tile[0]), 2 * (y - tile[1]),
                                          2 * (r - tile[0]), 2 * (b - tile[1])))
    card = Image.new("RGB", (w + 44, h + 66), "white")
    draw = ImageDraw.Draw(card)
    draw.text((3, 2), f"{ident}   150 DPI 6倍   所属軸 x", font=font, fill="#252525")
    for a in (u, z):
        draw.line((22 + a, 31, 22 + a, 43), fill="red", width=2)
        draw.line((22 + a, 44 + h, 22 + a, 60 + h), fill="red", width=2)
    for a in (v, q):
        draw.line((3, 44 + a, 21, 44 + a), fill="red", width=2)
        draw.line((22 + w, 44 + a, 38 + w, 44 + a), fill="red", width=2)
    up = patch.resize((w, h), Image.Resampling.NEAREST)
    card.paste(up, (22, 44))
    if card.crop((22, 44, 22 + w, 44 + h)).tobytes() != up.tobytes():
        raise ValueError("元画素を変更した")
    raw = io.BytesIO()
    card.save(raw, "PNG")
    return raw.getvalue()


def pick(rows, page, state, n):
    chosen = sorted((v for v in rows if v["status"] == state),
                    key=lambda r: hashlib.sha256(f"{SEED}/{page}/{state}/{r['line_index']}".encode()).digest())
    if len(chosen) < n:
        raise ValueError(f"事前の行数を満たせない: {page}/{state}")
    return chosen[:n]


def material():
    sp, fp = REGION / "start.json", REGION / "final.json"
    start, final = base.load(sp), base.load(fp)
    if final["start_sha256"] != base.sha(sp):
        raise ValueError("元の補充対象と画像が異なる")
    entries = {(r["key"], r["line_index"]): r for r in start["entries"]}
    font_file = base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_file, size=17)
    cards, packs, expected = {}, {}, {}
    for number, page in enumerate(PAGES):
        source = [r for r in final["rows"] if r["key"] == page and r["allocation_axis"] == "x"
                  and 16 <= r["box"][2] <= 120 and 12 <= r["box"][3] <= 35]
        sample = pick(source, page, "unreadable", 3) + pick(source, page, "readable", 1)
        sample.sort(key=lambda r: hashlib.sha256(f"{SEED}/{page}/order/{r['line_index']}".encode()).digest())
        name = f"pack-{number:02d}"
        main, other, lookup = {}, {}, {}
        for pos, row in enumerate(sample, 1):
            ident, i = f"W{pos:02d}", row["line_index"]
            entry = entries[page, i]
            normal, _ = v2.make_cards(entry, start["assets"], ident, font)
            focus, _ = figure.detailed(entry, ident, start["assets"], font)
            main.update(normal)
            other.update(focus)
            other[f"{ident}-ruler.png"] = ruler(entry, ident, start["assets"], font)
            lookup[ident] = {"key": page, "line_index": i, "previous": row["status"],
                             "text": base.normalize(row["text"]) if row["status"] == "readable" else None}
        cards[name] = main | other
        names, ids = sorted(main) + sorted(other), list(lookup)
        packs[name] = {"images": names, "ids": ids,
                       "image_sha256": [hashlib.sha256(cards[name][f]).hexdigest() for f in names],
                       "prompt": v2.v1.INTRO + v2.NOTICE + figure.old.shared + GUIDE + base.FORMAT + "、".join(ids) + "\n"}
        expected[name] = lookup
    pins = (Path(__file__), HERE / "protocol.md", PILOT, sp, fp, font_file, Path(pilot.opus.__file__),
            Path(base.__file__), Path(v2.__file__))
    material_hashes = {p.parent.name + "/" + p.name: base.sha(p) for p in pins}
    if len(material_hashes) != len(pins):
        raise ValueError("元の複数ファイルを同じ名前で固定した")
    return cards, expected, {"packs": packs, "inputs": material_hashes, "models": pilot.MODELS,
                              "identities": {name: {i: [r["key"], r["line_index"]] for i, r in rows.items()}
                                             for name, rows in expected.items()}}


def outcome(a, b, target):
    if a is None or b is None:
        return "both-unknown" if a is b else "one-unknown"
    if a != b:
        return "disagreement"
    if target["previous"] == "readable":
        return "matches-control" if a == target["text"] else "differs-from-control"
    return "new-agreement" if a else "agreed-empty"


def run(args, cards, expected, manifest):
    paths = {"sol": args.codex, "opus": args.claude}
    if any(p is None or not p.is_file() for p in paths.values()):
        raise ValueError("二つの実行ファイルが必要")
    if manifest != base.load(LOCK) or base.sha(LOCK) != args.lock_sha256:
        raise ValueError("実験の事前固定が違う")
    for name, files in cards.items():
        if any((OUT / "cards" / name / k).read_bytes() != v for k, v in files.items()):
            raise ValueError("添付画像が事前固定と違う")
    with (OUT / "started.json").open("x", encoding="utf-8") as f:
        json.dump({"lock_sha256": args.lock_sha256}, f)
    pilot.OUT = OUT / "reads"
    errors, receipts, votes, sessions = {}, [], {}, set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        work = {}
        for name, pack in manifest["packs"].items():
            info = {"image_order_by_sheet": {"1": pack["images"]},
                    "image_sha256": dict(zip(pack["images"], pack["image_sha256"], strict=True))}
            rows = [{"id": i, "sheet": 1} for i in pack["ids"]]
            for role, exe in paths.items():
                work[pool.submit(pilot.read, exe.resolve(), role, name, pack, rows, OUT / "cards" / name, info)] = name, role
        for task in as_completed(work):
            name, role = work[task]
            try:
                answers, receipt = task.result()
                if answers.keys() != set(expected[name]) or receipt["session"] in sessions or receipt.get("attempt", 1) != 1:
                    raise ValueError("原票の欠落、重複または技術再試行")
                sessions.add(receipt["session"])
                votes[name, role] = answers
                receipts.append(receipt)
            except (ValueError, RuntimeError, OSError) as error:
                errors[f"{name}/{role}"] = type(error).__name__
    total, private = {}, []
    for name, samples in expected.items():
        for ident, sample in samples.items():
            a, b = (votes.get((name, role), {}).get(ident) for role in paths)
            flag = outcome(a, b, sample) if all((name, role) in votes for role in paths) else "technical-unresolved"
            total.setdefault(sample["previous"], Counter())[flag] += 1
            private.append({"key": sample["key"], "line_index": sample["line_index"], "result": flag,
                            "text": a if flag == "new-agreement" else None})
    base.write_json(OUT / "decisions.json", private)
    advance = total["unreadable"]["new-agreement"] >= 6 and not total["readable"]["differs-from-control"] and not errors
    args_out = {"scope": "development-only", "counts": total, "lock_sha256": args.lock_sha256, "advance": advance,
                "decisions_sha256": base.sha(OUT / "decisions.json"), "errors": errors, "receipts": receipts}
    base.write_json(HERE / "result.json", args_out)
    print(json.dumps({"counts": total, "advance": advance}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    cards, expected, manifest = material()
    if args.action == "prepare":
        if OUT.exists() or LOCK.exists():
            raise FileExistsError("固定を上書きしない")
        for name, files in cards.items():
            dst = OUT / "cards" / name
            dst.mkdir(parents=True)
            for k, value in files.items():
                (dst / k).write_bytes(value)
        base.write_json(LOCK, manifest)
        print(base.sha(LOCK), {k: len(v) for k, v in cards.items()}, flush=True)
    else:
        run(args, cards, expected, manifest)
