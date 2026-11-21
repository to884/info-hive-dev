"""比較元の固定画素、原票、表示を継承し、連続区間を加えた二読を行う。"""

import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
import sys

from PIL import Image, ImageFont

import strips

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v62-combined-reading-pilot"
sys.path.insert(0, str(PREVIOUS))
import compare as old

core, audit, previous = old.core, old.audit, old.previous
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
pilot = previous.module("contiguous_pixel_strips", BASE)
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v63-contiguous-pixel-strips-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"


def additions(images, panels):
    overflow = max(0, len(images) + len(panels) - audit.LIMIT)
    if overflow:
        choices = [n for n in images if "-coordinate-" in n and "+" not in n]
        if len(choices) < 2 * overflow:
            raise ValueError("元の画像と連続区間を同じ束の上限に収められない")
        chosen = choices[-2 * overflow:]
        for i in range(0, len(chosen), 2):
            a, b = chosen[i:i + 2]
            name = a.removesuffix(".png") + "+" + b.rsplit("-", 1)[1]
            if name in images:
                raise ValueError("元の座標の表示と結合した画像の名前が重なる")
            images[name] = audit.combine(images.pop(a), images.pop(b))
    return panels | images


def subset(plan, rows, result):
    due, control = [], {"x": [], "y": []}
    for name, case in result["cases"].items():
        entry = plan["mapping"][name.split("/")[0]]["entry"]
        row = rows[entry]
        grades = case["outcomes"]["after"]
        if not strips.eligible(row):
            if grades["pair"] != "same":
                raise ValueError("前回の未決定行が表示できる寸法にない")
            continue
        if grades["pair"] != "same":
            due.append(name)
        elif all(grades[r] == "same" for r in ("gpt", "claude")):
            p, i = row["key"], row["line_index"]
            ranking = sha256(f"adr0025-stage2-v63-controls\0{p}\0{i}".encode()).hexdigest()
            control[row["allocation_axis"]].append((ranking, name))
    if len(due) != 7 or min(map(len, control.values())) < 3:
        raise ValueError("前の未決定7行と各軸の対照3行をそろえられない")
    return due + [name for axis in ("x", "y") for _, name in sorted(control[axis])[:3]]


def snapshot():
    before = old.pilot.OUT / "display"
    locked = old.pilot.LOCK
    back, grades_file = core.load(locked), PREVIOUS / "comparison.json"
    grades = core.load(grades_file)
    if (grades["lock_sha256"] != core.sha(locked)
            or any(core.sha(Path(f)) != d for f, d in back["files"].items())):
        raise ValueError("比較元の票と固定画像の来歴が異なる")
    selected = before / "selection.json"
    rows = core.load(selected)["selected"]
    manifest = before / "delivery/packages.json"
    assets = core.load(manifest)["source_assets"]
    display = pilot.OUT / "display"
    font_file = old.render.typeface
    font = ImageFont.truetype(font_file, size=17)
    files = {str(f): core.sha(f) for f in (Path(__file__), Path(strips.__file__), BASE, HERE / "protocol.md",
                                          locked, grades_file, selected, manifest, font_file)}
    mapping, jobs, used = {}, {}, []
    for name in subset(back, rows, grades):
        package = back["jobs"][name]
        prior = package["request"]
        ident, = prior["ids"]
        entry = back["mapping"][name.split("/")[0]]
        row = rows[entry["entry"]]
        fixed = entry["image_reference"]["source_view"]["views"][1]
        reference = next(o["image"] for o in fixed["images"] if o["kind"] == "plain")
        raw = before / "delivery/source-assets" / reference
        files[str(raw)] = core.sha(raw)
        if files[str(raw)] != assets[reference]:
            raise ValueError("連続区間の固定450 DPIが異なる")
        with Image.open(raw) as page:
            panels, intervals = strips.strip_images(page, fixed["target_rectangle"], ident, font, row["allocation_axis"])
        ordinary = {f: (Path(package["cards"]) / f).read_bytes() for f in prior["images"]}
        if [sha256(b).hexdigest() for b in ordinary.values()] != prior["image_sha256"]:
            raise ValueError("比較元の画像が変わった")
        images = additions(ordinary, panels)
        tag = name.split("/")[0]
        cards = display / "cards" / tag
        cards.mkdir(parents=True)
        for f, blob in images.items():
            core.save_once(cards / f, blob)
        start, form, ending = prior["prompt"].partition(audit.packets.FORMAT)
        if not form:
            raise ValueError("固定した出力の形式が異なる")
        add = strips.VERTICAL if row["allocation_axis"] == "y" else strips.HORIZONTAL
        mapping[tag] = {**entry, "entry": len(used), "intervals": intervals}
        jobs[name] = {"cards": str(cards), "request": {**prior, "images": list(images),
            "image_sha256": [sha256(b).hexdigest() for b in images.values()],
            "prompt": start + strips.COMMON + add + form + ending}}
        used.append(row)
    selection = display / "selection.json"
    core.save_once(selection, core.encoded({"selected": used}))
    files[str(selection)] = core.sha(selection)
    pilot.SAMPLES = used
    return {"jobs": jobs, "mapping": mapping, "files": files}


def compare():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action")
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    digest, raw = core.sha(pilot.LOCK), core.load(pilot.LOCK)
    result = core.load(pilot.RESULT)
    final = HERE / "comparison.json"
    if (digest != args.sha256 or result["lock_sha256"] != digest or set(result["cases"]) != set(raw["jobs"])
            or any(core.sha(Path(f)) != h for f, h in raw["files"].items())):
        raise ValueError("両二票が事前固定と結び付かない")
    baseline = core.load(PREVIOUS / "comparison.json")["cases"]
    counts, cases = {"before": Counter(), "after": Counter()}, {}
    for name, record in result["cases"].items():
        source, newer, want = baseline[name], record["readings"], record["expected"]
        update = {k: old.verdict(newer[k], want) for k in ("gpt", "claude", "pair")}
        earlier = source["outcomes"]["after"]
        counts["before"][earlier["pair"]] += 1
        counts["after"][update["pair"]] += 1
        cases[name] = {"page": record["page"], "line_index": record["line_index"], "before": earlier, "after": update,
                       "new_votes": {r: newer[r] for r in ("gpt", "claude", "pair")}}
        print(record["page"], record["line_index"], earlier["pair"], update, flush=True)
    old.preserved(final, {"scope": "development-only", "lock_sha256": digest, "counts": counts, "cases": cases})
    print(counts, flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare()
    else:
        pilot.snapshot = snapshot
        pilot.main()
