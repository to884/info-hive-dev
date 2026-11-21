"""過去に扱った行を除き、中立化した画像の表示と従来の表示を固定する。"""

from collections import defaultdict
from contextlib import nullcontext
from hashlib import sha256
from pathlib import Path
import sys

import grade
import neutral

HERE, core, audit, render = neutral.HERE, neutral.core, neutral.audit, neutral.render
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
pilot = neutral.previous.module("neutral_reading_comparison", BASE)
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v67-neutral-transcription-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
GROUPS = ("horizontal-other", "horizontal-short", "vertical-long", "vertical-short")


def key(row):
    return row["key"], row["line_index"]


def exposed(prior_method):
    paths = sorted(set(core.CORPUS.glob("reference-*/selection.json")) |
                   set(core.CORPUS.glob("reference-*/display/selection.json")))
    history = {tuple(item) for item in prior_method["direct_intake"]}
    for path in paths:
        selected = core.load(path)
        for row in selected.get("selected", selected.get("entries", [])):
            page = row.get("key") or row.get("page")
            if page and "line_index" in row:
                history.add((page, row["line_index"]))
    return history, paths


def strata(pools, history):
    agreed, group = {}, defaultdict(list)
    for domain, rows in pools.items():
        for entry in rows:
            k = key(entry)
            if k in history or entry["development_intake"] or entry["previously_audited"]:
                continue
            targets = {f: entry[f] for f in ("cohort", "text", "known", "error")}
            row = agreed.setdefault(k, {f: n for f, n in entry.items() if f not in targets})
            row.setdefault("targets", {})[domain] = targets
    for k, row in agreed.items():
        known = {core.ref.NORMALIZE(t["text"]) for t in row["targets"].values() if t["known"]}
        if len(known) != 1 or not all(t["known"] for t in row["targets"].values()):
            continue
        if row["allocation_axis"] == "y":
            category = "vertical-short" if row["box"][3] <= 120 else "vertical-long"
        else:
            category = "horizontal-short" if render.short_frame(row) else "horizontal-other"
        digest = sha256(f"adr0025-stage2-v67-development\0{k[0]}\0{k[1]}".encode("utf-8")).hexdigest()
        group[category].append((digest, {**row, "effective": known.pop()}))
    if set(group) != set(GROUPS) or any(len(v) < 8 for v in group.values()):
        raise ValueError("未使用の開発行を各群8行ずつ用意できない")
    locked = [(category, row) for category in GROUPS for _, row in sorted(group[category], key=lambda q: q[0])[:8]]
    return locked, {category: [(digest, key(row)) for digest, row in sorted(group[category], key=lambda q: q[0])]
                    for category in GROUPS}


def build(out, rows, plan, use_neutral):
    out.mkdir(parents=True)
    selected, method, guard = (out / f"{f}.json" for f in ("selection", "method", "population"))
    core.save_once(method, core.encoded(plan))
    core.save_once(guard, core.encoded({"inputs": {}}))
    core.save_once(selected, core.encoded({"population_lock_sha256": core.sha(guard), "selected": rows}))
    saved = core.OUT, core.PLAN, core.LOCK
    core.OUT, core.PLAN, core.LOCK = out, method, guard
    manifest = out / "delivery/packages.json"
    omitted = {}
    practice = neutral.active(omitted) if use_neutral else nullcontext()
    try:
        with practice:
            audit.package(core.sha(selected))
            audit.verify_delivery(core.sha(manifest))
            batches = core.load(manifest)["packs"]
            if use_neutral:
                render.verify(rows, batches)
                for packet in batches.values():
                    (_, found), = packet["mapping"].items()
                    row = rows[found["entry"]]
                    proof = omitted[f"{row['key']}/{row['line_index']}"]
                    images = set(packet["request"]["images"])
                    if set(proof["sizes"]) != images or not set(proof["required_close_or_layout"]) <= images:
                        raise ValueError("記録した表示と実際に同じ束で渡す画像が異なる")
        trace = out / "retained.json"
        core.save_once(trace, core.encoded(omitted))
    finally:
        core.OUT, core.PLAN, core.LOCK = saved
    return batches, (selected, method, guard, manifest, trace)


def snapshot():
    core.verify_methods()
    original = core.PLAN
    method = core.load(original)
    history, earlier = exposed(method)
    _, _, label_dir = core.methods()
    texts = label_dir / "public.json"
    _, flags = core.baseline.take_public_rows()
    selection, qualified = strata(core.baseline.populations(core.load(texts), flags), history)
    rows = [row for _, row in selection]
    display = pilot.OUT / "display"
    old, old_inputs = build(display / "old", rows, method, False)
    new, new_inputs = build(display / "new", rows, render.plan(method), True)
    index, frame_index = ({r["entry"]: (n, b, r) for n, b in arm.items() for r in b["mapping"].values()}
                          for arm in (old, new))
    jobs, mapping = {}, {}
    for i, (category, _) in enumerate(selection):
        name, before, raw = index[i]
        updated_name, after, updated_raw = frame_index[i]
        if raw["image_reference"] != updated_raw["image_reference"]:
            raise ValueError("新旧両方で同じ元の固定画素と枠を使っていない")
        key_name = f"case-{i:02d}"
        mapping[key_name] = {"entry": i, "group": category, "arms": {"old": raw, "new": updated_raw}}
        for arm, pack, entry in (("old", name, before), ("new", updated_name, after)):
            jobs[f"{key_name}/{arm}"] = {"cards": str(display / arm / "delivery/cards" / pack),
                                         "request": entry["request"]}
    selection_file, exclusions = (display / f"{f}.json" for f in ("selection", "eligible"))
    core.save_once(selection_file, core.encoded({"selected": rows}))
    core.save_once(exclusions, core.encoded({"excluded": sorted(history), "eligible": qualified}))
    files = (Path(__file__), Path(grade.__file__), Path(neutral.__file__), Path(render.__file__),
             Path(render.orientation.__file__), Path(render.instructions.__file__), Path(render.short.__file__),
             Path(render.horizontal.__file__), BASE, HERE / "protocol.md", original, texts, selection_file, exclusions,
             *old_inputs, *new_inputs, *earlier)
    pins = core.load(core.LOCK)["inputs"] | {str(p): core.sha(p) for p in files}
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
