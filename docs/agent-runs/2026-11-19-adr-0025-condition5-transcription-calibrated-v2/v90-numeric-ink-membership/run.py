"""数字の読みと記号の位置を別に答え、固定画素の既存式で枠の所属を判定する。"""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent
BOUNDARY = STAGES / "v88-numeric-outside-controls/run.py"
MEASURE = STAGES / "v86-numeric-boundary-pilot/measure.py"
V86 = MEASURE.parent
V88 = BOUNDARY.parent


def module(name, path):
    spec = spec_from_file_location(name, path)
    loaded = module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


boundary = module("outside_number_frames", BOUNDARY)
ink = module("numeric_ink_measurement", MEASURE).existing
numeric, core, launch, pilot, grade = boundary.numeric, boundary.core, boundary.launch, boundary.pilot, boundary.grade
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v90-numeric-ink-membership"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "pair.json"
RULER = "『150 DPIの横座標』の最初の数字は枠の左端を0として、10画素ごとの横位置を示します。"
FORMAT = (
    "枠の横範囲に見える数字列を画像だけから答えます。数字は元の枠の内側だけを転記します。"
    "小さい点や区切りの記号は、横の範囲にあり、数字の間にはっきり見える場合に記録します。"
    "記号については下端の上下のどちらであるか自分で決めず、下端のすぐ外側に見えるものも含め、形と位置を記録します。"
    "textは数字だけを並べ、見えた記号ごとに |直前までの数字の個数:横位置:種類 を続けます。"
    "横位置は『150 DPIの横座標』で見た記号のインクの中心を整数に丸めます。"
    "種類はコンマ C、点 D、コロン T、横線 H、斜線 S。記号が見えない場合は数字だけです。"
    "空きだけで記号を加えません。画が重なって数字と記号を分けられないときは判読不能とします。"
)
SYMBOL = {"C": ",", "D": ".", "T": ":", "H": "-", "S": "/"}
TOKEN = re.compile(r"([0-9]+):([0-9]+):([CDTHS])")


def ruler(rgb, row, ident, font):
    x, y, w, h = row["box"]
    l, t = max(x - 6, 0), max(y - 6, 0)
    photo = rgb.crop((l, t, min(rgb.width, x+w+6), min(rgb.height, y+h+8))).convert("RGB")
    scale, margin, top = 5, 25, 46
    photo = photo.resize((photo.width*scale, photo.height*scale), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (photo.width+2*margin, photo.height+top+10), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((7, 2), f"{ident} 150 DPIの横座標", font=font, fill="black")
    canvas.paste(photo, (margin, top))
    for at in range(0, w+1, 10):
        px = margin+(x-l+at)*scale
        draw.text((px, 22), str(at), font=font, anchor="mt", fill="#66182b")
        draw.line((px, 39, px, top-1), fill="#991c31", width=2)
    for edge in (y, y+h):
        py = top+(edge-t)*scale
        draw.line((5, py, margin-2, py), fill="#991c31", width=2)
        draw.line((margin+photo.width+1, py, canvas.width-5, py), fill="#991c31", width=2)
    return launch.render.orientation.blob(canvas)


def components(rgb, row):
    x, y, w, h = row["box"]
    target = (x, y, x+w, y+h)
    window = (max(x-6, 0), max(y-6, 0), min(x+w+6, rgb.width), min(y+h+8, rgb.height))
    gray = np.array(rgb.crop(window).convert("L"))
    all_ink = ink.measure(gray, window, target, 0, int(np.median(gray)), [])["components"]
    records = []
    for item in all_ink:
        l,t,r,b = item["bounds"]
        if (not item["touches_window_edge"] and 2 <= b-t <= .55*h and x < (l+r)/2 < x+w
                and y-.12*h < (t+b)/2 <= y+h+.22*h):
            records.append(item)
    return records


def snapshot():
    core.verify_methods()
    trial = {d: core.load(d/"lock.json") for d in (V86, V88)}
    study = numeric.study
    shipment = core.load(study.delivery/"packages.json")
    archived = core.load(launch.OUT/"selection.json")["selected"]
    selections = {V86: core.CORPUS/"reference-v86-numeric-boundary-pilot/display/selection.json",
                  V88: core.CORPUS/"reference-v88-numeric-outside-controls/display/selection.json"}
    inputs = {Path(__file__), HERE/"protocol.md", BOUNDARY, MEASURE, Path(ink.__file__),
              Path(pilot.__file__), Path(grade.__file__), launch.render.typeface, study.delivery/"packages.json"}
    out = pilot.OUT/"display"
    prepared, jobs, mappings = [], {}, {}
    font = ImageFont.truetype(launch.render.typeface, size=16)
    for version in (V88, V86):
        plan = trial[version]
        if any(core.sha(Path(p)) != h for p, h in plan["files"].items()):
            raise ValueError("前の開発画像の固定資料が変わっている")
        inputs.update((version/"lock.json", selections[version]))
        entries = core.load(selections[version])["selected"]
        for name, binding in plan["mapping"].items():
            group = binding["group"]
            if version == V86 and group == "boundary-target":
                continue
            key = ("88-" if version == V88 else "86-") + name
            row = entries[binding["entry"]]
            original = name[:8]
            original_packet = shipment["packs"][original]
            source, = original_packet["mapping"].values()
            original_row = archived[source["entry"]]
            assets = deepcopy(source["image_reference"])
            low = core.CORPUS/"probe-v4/png"/f"{row['key']}.png"
            view = assets["source_view"]["views"][1]
            high_file = next(v["image"] for v in view["images"] if v["kind"] == "plain")
            high = study.delivery/"source-assets"/high_file
            if core.sha(low) != assets["sha"]["150_dpi"] or core.sha(high) != shipment["source_assets"][high_file]:
                raise ValueError("元の画像が固定した値と異なっている")
            inputs.update((low, high))
            dh = row["box"][3]-original_row["box"][3]
            rect = view["target_rectangle"]
            rect[3] += dh * (rect[3]-rect[1]) / original_row["box"][3]
            ident = f"N{len(prepared)+1:03d}"
            folder = out/"cards"/key
            folder.mkdir(parents=True, exist_ok=True)
            edge, axes = folder/f"{ident}-boundary.png", folder/f"{ident}-axis.png"
            core.save_once(edge, numeric.view_pair(row, assets, (low, high), ident, font))
            with Image.open(low) as pixels:
                core.save_once(axes, ruler(pixels, row, ident, font))
                physical = components(pixels, row)
            inputs.update((edge, axes))
            req = {**plan["jobs"][f"{name}/old"]["request"], "ids": [ident],
                   "images": [edge.name, axes.name], "image_sha256": [core.sha(edge), core.sha(axes)]}
            text = boundary.TASK.format(label=ident)+RULER
            for arm, rule in (("old", launch.neutral.HORIZONTAL+numeric.GUIDE), ("new", FORMAT)):
                jobs[f"{key}/{arm}"] = {"cards": str(folder), "request": {**req, "prompt": text+rule}}
            mappings[key] = {"entry": len(prepared), "category": group, "partitions": [], "ink": physical}
            prepared.append(row)
    if len(prepared)!=12:
        raise ValueError("境界の六枠と対照の六行を固定できない")
    selected = out/"selection.json"
    core.save_once(selected, core.encoded({"selected": prepared}))
    inputs.add(selected)
    pilot.SAMPLES = prepared
    return {"jobs": jobs, "mapping": mappings, "files": core.load(core.LOCK)["inputs"] |
            {str(p): core.sha(p) for p in sorted(inputs)}}


def decompose(vote, geometry, left, width):
    if vote["status"] != "readable":
        return None
    digits, *marks = vote["text"].split("|")
    if not re.fullmatch(r"[0-9]+", digits):
        return None
    found = {}
    previous_x = -1
    for raw in marks:
        match = TOKEN.fullmatch(raw)
        if not match:
            return None
        after, x, glyph = int(match[1]), int(match[2]), SYMBOL[match[3]]
        if not (0 < after < len(digits) and 0 < x < width) or after in found:
            return None
        candidates = [c for c in geometry if abs((c["bounds"][0]+c["bounds"][2])/2-left-x) <= 3]
        if len(candidates)!=1:
            return None
        ink_id = candidates[0]["id"]
        if found and (after <= next(reversed(found)) or x <= previous_x or ink_id in {v[1] for v in found.values()}):
            return None
        previous_x = x
        found[after] = (glyph, ink_id)
    return digits, found


def transcribe(structure, candidates):
    if structure is None:
        return core.ref.UNKNOWN
    digits, found = structure
    measured = {r["id"]: r for r in candidates}
    suffix = {}
    for after, (symbol, component) in found.items():
        tested = measured[component]
        if tested["cross_axis_center_inside"] and 2*tested["axis_overlap"] >= tested["axis_length"]:
            suffix[after] = symbol
    return {"status": "readable", "text": "".join(ch+suffix.get(n, "") for n,ch in enumerate(digits,1))}


def score(args):
    plan = core.load(pilot.LOCK)
    if core.sha(pilot.LOCK)!=args.sha256 or any(core.sha(Path(p))!=h for p,h in plan["files"].items()):
        raise ValueError("固定画像と測定の来歴が異なる")
    records = core.load(pilot.OUT/"display/selection.json")["selected"]
    runtimes = pilot.audit.delivery.runtime({"gpt": args.codex, "claude": args.claude})
    totals = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    seen, results = set(), {}
    for task, job in plan["jobs"].items():
        key, arm = task.split("/")
        row_data = plan["mapping"][key]
        row = records[row_data["entry"]]
        ident, = job["request"]["ids"]
        width = row["box"][2]
        geometry = row_data["ink"]
        votes, sessions = {}, {}
        for model in ("gpt","claude"):
            attempt = pilot.outcome(args.sha256,task,model,job,runtimes[model])[-1]
            if attempt["availability"]!="received" or attempt["session"] in seen:
                raise ValueError("異系統・別セッションの二票がそろわない")
            seen.add(attempt["session"])
            votes[model] = attempt["answers"][ident]
            sessions[model] = attempt["session"]
        if arm=="old":
            derived = {m: core.ref.decoded(v, []) for m,v in votes.items()}
            pair, _ = core.ref.aligned(*derived.values(), width)
            structured = {}
        else:
            structured = {m: decompose(v, geometry, row["box"][0], width) for m,v in votes.items()}
            derived = {m: transcribe(v, geometry) for m,v in structured.items()}
            pair = derived["gpt"] if structured["gpt"] == structured["claude"] else core.ref.UNKNOWN
        target = core.ref.NORMALIZE(row["effective"])
        judged = {m: grade.verdict(core.ref, v, target) for m,v in (derived | {"pair": pair}).items()}
        for model, category in judged.items():
            totals[row_data["category"]][arm][model][category] += 1
        results[task] = {"group":row_data["category"], "line":row["line_index"], "page":row["key"], "expected":target,
                         "votes":votes, "sessions":sessions, "parsed":structured, "ink":geometry, "result":judged}
    core.save_once(HERE/"comparison.json", core.encoded({"scope":"development-only","lock_sha256":args.sha256,
                                                        "counts":totals,"cases":results}))
    print({g:{a:dict(v) for a,v in arms.items()} for g,arms in totals.items()},flush=True)


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action", choices=("compare",))
        parser.add_argument("--sha256", required=True)
        parser.add_argument("--codex", required=True, type=Path)
        parser.add_argument("--claude", required=True, type=Path)
        score(parser.parse_args())
    else:
        pilot.snapshot = snapshot
        pilot.main()
