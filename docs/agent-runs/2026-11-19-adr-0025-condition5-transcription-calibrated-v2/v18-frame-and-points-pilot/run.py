"""固定画像の目盛りと丸い点の指示を、開発用の二読で比較する。"""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v15-reference-audit"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = module("v15_audit_artifacts", PREVIOUS / "run.py")
receipt = module("v17_development_receipt", HERE.parent / "v17-ink-gap-receipt/collect.py")
trial = receipt.trial
load, sha, assets = old.load, old.sha, old.OUT / "delivery"
OUT, LOCK = old.prior.old.CORPUS / "reference-v18-frame-and-points-pilot", HERE / "lock.json"
POINT_GUIDE = (
    "小さな丸は、固定450 DPIで、内側に白い穴のある輪か、塗られた点かを確かめます。"
    "輪に見える句点は元の位置と数のまま「。」と書きます。丸い線や角のある字を点の印に置き換えません。"
    "塗られた小さい点で符号を画像から区別できないものは、行頭でも行の途中でも ⟦round:X-X⟧ にします。"
    "字の区切りが見えない点線には ⟦trail:X-Y⟧ を使います。XとYは枠の左を0とした点の中心です。『横座標』画像の小目盛りは5画素です。"
    "元の字の形として大きい黒丸や句点、図形と区別できた部分はその形を転記し、文字でない図形は写しません。"
)
FRAME_GUIDE = (
    "目盛りの数字は転記しません。赤い枠にかかる字は、隅の断片だけを一字として数えないでください。"
    "『枠への入り方』の左側は枠と目盛り、右側は同じ固定150 DPIの画像だけです。"
    "枠の端をまたぐ字は字全体に対して割当軸の長さを数え、少なくとも半分が枠内にあり、もう一方の軸で字の中心が枠内なら写します。"
    "枠の角で繰り返して写さず、末尾の小さな句点も同じ枠への所属を先に確かめます。"
    "長い行に添えた行頭・行末の拡大は、全文を点検するための画像です。"
)


def magnified(row, flags, ident, font):
    x, y, w, h = row["box"]
    axis = row["allocation_axis"]
    side = "行頭", "行末"
    if w <= 118 and h <= 132:
        ranges = [("全体", (x - 14, y - 14, x + w + 14, y + h + 14))]
    elif axis == "y":
        ranges = [(title, (x - 18, lo, x + w + 18, hi))
                  for title, (lo, hi) in zip(side, ((y - 18, y + 64), (y + h - 65, y + h + 18)), strict=True)]
    else:
        ranges = [(title, (lo, y - 18, hi, y + h + 18))
                  for title, (lo, hi) in zip(side, ((x - 18, x + 68), (x + w - 66, x + w + 18)), strict=True)]
    page = old.prior.old.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if sha(page) != flags["150_dpi"]:
        raise ValueError("固定150 DPIの画像が異なる")
    output = {}
    scale = 5
    with Image.open(page) as fixed:
        for n, (caption, bounds) in enumerate(ranges, 1):
            l, t, r, b = max(0, bounds[0]), max(0, bounds[1]), min(fixed.width, bounds[2]), min(fixed.height, bounds[3])
            pixels = fixed.crop((l, t, r, b)).convert("RGB")
            view = pixels.resize((pixels.width * scale, pixels.height * scale), Image.Resampling.NEAREST)
            width, height = view.size
            tile = Image.new("RGB", (2 * width + 66, height + 95), "white")
            dx, dy = 36, 64
            tile.paste(view, (dx, dy))
            tile.paste(view, (width + 52, dy))
            draw = ImageDraw.Draw(tile)
            draw.text((6, 3), f"{ident}  {caption}の枠への入り方  固定150 DPI", font=font, fill="#222222")
            for pic, label in ((dx, "左右・上下の枠と目盛り"), (width + 52, "同じ元画像")):
                draw.text((pic, 27), label, font=font, fill="#222222")
            ax, bx = dx + scale * (x - l), dx + scale * (x + w - l)
            ay, by = dy + scale * (y - t), dy + scale * (y + h - t)
            ar, ab = dx + width, dy + height
            color = "#aa1521"
            for edge_x in (ax, bx):
                if dx <= edge_x <= ar:
                    draw.line((edge_x, max(dy, ay), edge_x, min(ab, by)), fill=color, width=1)
            for edge_y in (ay, by):
                if dy <= edge_y <= ab:
                    draw.line((max(dx, ax), edge_y, min(ar, bx), edge_y), fill=color, width=1)
            for value in range(l, r + 1):
                start = dx + scale * (value - l)
                interval = value - x
                step = 7 if interval % 5 == 0 else 3
                draw.line((start, dy - 1, start, dy - step), fill="#5b2330")
                if interval % 10 == 0:
                    draw.text((start - 4, dy - 24), str(interval), font=font, fill="#333333")
            for value in range(t, b + 1):
                start = dy + scale * (value - t)
                interval = value - y
                step = 7 if interval % 5 == 0 else 3
                draw.line((dx - 1, start, dx - step, start), fill="#5b2330")
                if interval % 10 == 0:
                    draw.text((0, start - 6), str(interval), font=font, fill="#333333")
            buf = io.BytesIO()
            tile.save(buf, "PNG")
            output[f"{ident}-border-{n}.png"] = buf.getvalue()
    return output


def selection(rows, previous):
    issue_list = load(PREVIOUS / "diagnosis.json")
    if issue_list["audit_sha256"] != sha(PREVIOUS / "result.json"):
        raise ValueError("確定した監査の診断と異なる")
    by_id = {(row["key"], row["line_index"]): i for i, row in enumerate(rows)}
    issues = {(r["key"], r["line_index"]): r for r in issue_list["cases"]}
    include = {by_id[k]: "wrong-membership" for k, r in issues.items() if r["outcome"] == "mismatch"}
    explicit = {("kanpo1828-p1-p0001", 42): "small-frame", ("kanpo1828-p3-p0001", 110): "small-frame",
                ("defense-p0219", 63): "points", ("defense-p0235", 12): "points", ("defense-p0491", 70): "points",
                ("disaster-p0053", 16): "points", ("wp-summary-p0008", 28): "points", ("wp-summary-p0010", 36): "points"}
    if set(explicit) - issues.keys() or len(include) != 2:
        raise ValueError("事前に記録した診断行と異なる")
    include.update({by_id[k]: category for k, category in explicit.items()})
    groups = {}
    for i, row in enumerate(rows):
        key = row["key"], row["line_index"]
        earlier = previous[f"{key[0]}/{key[1]}"]["answer"]
        known = row["targets"].values()
        if key in issues or not all(t["known"] for t in known) or earlier["status"] != "readable":
            continue
        if not all(earlier["text"] == old.reference.NORMALIZE(t["text"]) for t in known):
            continue
        w, h = row["box"][2:]
        axis = row["allocation_axis"]
        if axis == "x" and w < 100:
            groups.setdefault("short-x", i)
        elif axis == "y" and h < 130:
            groups.setdefault("short-y", i)
        elif axis == "y" and h >= 400:
            groups.setdefault("long-y", i)
        elif axis == "x" and w > 500:
            groups.setdefault("long-x", i)
    if len(groups) != 4:
        raise ValueError("寸法ごとの対照4行に不足")
    include.update({i: "control" for i in groups.values()})
    return include


def material():
    records = load(old.OUT / "selection.json")["selected"]
    previous = load(old.OUT / "reference-evidence.json")
    if load(PREVIOUS / "result.json")["reference_sha256"] != sha(old.OUT / "reference-evidence.json"):
        raise ValueError("正式な独立監査の詳細が変化")
    origin = load(assets / "packages.json")
    by_entry = {r["entry"]: (name, label, r, job["request"])
                for name, job in origin["packs"].items() for label, r in job["mapping"].items()}
    font_path = old.prior.old.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, 13)
    arms, all_images = {}, {}
    for n, (i, purpose) in enumerate(sorted(selection(records, previous).items())):
        row = records[i]
        pack, ident, mapping, request = by_entry[i]
        guide = old.prior.INTRO + FRAME_GUIDE
        guide += (POINT_GUIDE if row["allocation_axis"] == "x" else "") + (old.prior.SHORT if mapping["partitions"] else "")
        if mapping["partitions"]:
            guide += "目印は" + "、".join(mapping["partitions"]) + "です。"
        images = {}
        for name, digest in zip(request["images"], request["image_sha256"], strict=True):
            if name.startswith(ident + "-"):
                blob = (assets / "cards" / pack / name).read_bytes()
                if trial.readers.sha(blob) != digest:
                    raise ValueError("同一の監査画像ではない")
                images[name] = blob
        end = magnified(row, mapping["image_reference"]["sha"], ident, font)
        if len(images) + len(end) > 24:
            optional = [n for n in images if "-close-" in n][1:]
            for drop in optional[:len(images) + len(end) - 24]:
                del images[drop]
        images.update(end)
        name = f"pack-{n:02d}"
        if len(images) > 24:
            raise ValueError("一行の画像が24枚を超える")
        arms[name] = {"entry": i, "purpose": purpose, "partitions": mapping["partitions"], "request": {
            "ids": [ident], "images": list(images), "image_sha256": [trial.readers.sha(v) for v in images.values()],
            "prompt": guide + old.prior.FORMAT + ident + "。"}}
        all_images[name] = images
    paths = (Path(__file__), HERE / "protocol.md", PREVIOUS / "result.json", PREVIOUS / "diagnosis.json",
             assets / "packages.json", old.OUT / "selection.json", old.OUT / "reference-evidence.json",
             Path(receipt.__file__), Path(trial.structured.__file__), font_path)
    return {"inputs": {str(p): sha(p) for p in paths}, "packs": arms}, all_images


def collect(plan):
    records = load(old.OUT / "selection.json")["selected"]
    counts, results, sessions = defaultdict(Counter), {}, set()
    for name, data in plan["packs"].items():
        who, = data["request"]["ids"]
        votes = []
        for role, model in trial.MODELS.items():
            root = OUT / "reads" / name / role
            raw = (root / "response.jsonl").read_bytes()
            status = load(root / "process.json")
            if status["response_sha256"] != trial.readers.sha(raw) or status["returncode"]:
                raise ValueError("開発用の回答を正常に受領できていない")
            events = [json.loads(line, object_pairs_hook=trial.readers.json_pairs) for line in raw.splitlines() if line.strip()]
            last = (root / "last-message.json").read_text(encoding="utf-8") if role == "gpt" else None
            session, structured = receipt.validated(events, role, model, last)
            if session in sessions:
                raise ValueError("同じ会話が複数の担当にある")
            sessions.add(session)
            answer = trial.entries(structured, [who])[who]
            votes.append(old.reference.decoded(answer, data["partitions"]))
        row = records[data["entry"]]
        proposed, markers = old.reference.aligned(*votes, row["box"][2])
        known = {old.reference.NORMALIZE(r["text"]) for r in row["targets"].values() if r["known"]}
        if proposed["status"] == "unreadable":
            result = "unresolved"
        elif markers:
            result = "requires-source"
        elif known == {proposed["text"]}:
            result = "agreed-existing-label"
        else:
            result = "agreed-different-label"
        counts[data["purpose"]][result] += 1
        results[name] = {"key": row["key"], "line_index": row["line_index"], "purpose": data["purpose"], "outcome": result}
    trial.readers.save_once(HERE / "result.json", trial.readers.encoded({"scope": "development-only", "lock_sha256": sha(LOCK),
                                                                        "counts": counts, "rows": results}))
    print(dict(counts), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--sha256")
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    args = p.parse_args()
    plan, materials = material()
    if args.action == "prepare":
        OUT.mkdir()
        for name, items in materials.items():
            target = OUT / "cards" / name
            target.mkdir(parents=True)
            for n, v in items.items():
                trial.readers.save_once(target / n, v)
        trial.readers.save_once(LOCK, trial.readers.encoded(plan))
        print(sha(LOCK), len(materials), "行", flush=True)
        return
    if load(LOCK) != plan or sha(LOCK) != args.sha256:
        raise ValueError("事前に固定した開発試験の画像と異なる")
    exe = {"gpt": args.codex.resolve(strict=True), "claude": args.claude.resolve(strict=True)}
    trial.readers.save_once(OUT / "started.json", trial.readers.encoded({"lock_sha256": sha(LOCK)}))
    with ThreadPoolExecutor(max_workers=5) as executor:
        calls = [executor.submit(trial.structured.read, role, model, exe[role], job["request"], OUT / "cards" / name,
                                 OUT / "reads" / name / role) for name, job in plan["packs"].items()
                 for role, model in trial.MODELS.items()]
        for work in calls:
            work.result()
    collect(plan)


if __name__ == "__main__":
    main()
