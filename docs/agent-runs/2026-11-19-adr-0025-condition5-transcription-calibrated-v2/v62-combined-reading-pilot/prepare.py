"""保存済みの監査の23課題行と12対照行を固定し、同じ画素で二読する。"""

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import sys

import render

HERE, core, audit = render.HERE, render.core, render.audit
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
pilot = render.previous.module("combined_appearance_development", BASE)
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v62-combined-reading-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"


def identity(row):
    return row["key"], row["line_index"]


def group(row):
    if row["allocation_axis"] == "y":
        return "vertical-short" if row["box"][3] <= 120 else "vertical-long"
    return "horizontal-short" if render.short_frame(row) else "horizontal-other"


def rank(row):
    page, line = identity(row)
    digest = sha256(f"adr0025-stage2-v62-controls\0{page}\0{line}".encode()).digest()
    return row["previously_audited"], digest


def choose(old, prior_trials, diagnosis):
    issues = {(v["page"], v["line_index"]): v["outcome"] for v in diagnosis["issues"]}
    controls, disputed = defaultdict(list), []
    for row in old:
        key = identity(row)
        texts = {core.ref.NORMALIZE(v["text"]) for v in row["targets"].values() if v["known"]}
        if key in issues:
            if len(texts) != 1:
                raise ValueError("開発の確認対象に一意な既存正解がない")
            disputed.append(({**row, "effective": texts.pop()}, "prior-" + issues[key]))
        elif len(texts) == 1 and not row["development_intake"] and key not in prior_trials:
            controls[group(row)].append({**row, "effective": texts.pop()})
    if len(issues) != 23 or len(disputed) != len(issues) or len(controls) != 4:
        raise ValueError("事前に指定した診断行と対照の群を用意できない")
    chosen = [(row, "control-" + label) for label, items in sorted(controls.items())
              for row in sorted(items, key=rank)[:3]]
    if len(chosen) != 12:
        raise ValueError("各群に3行の対照がそろわない")
    return disputed + chosen


def snapshot():
    core.verify_methods()
    reference = core.OUT / "selection.json"
    archive = core.OUT / "delivery/packages.json"
    received = archive.with_name("received.json")
    diagnosis, result = audit.HERE / "diagnosis.json", audit.HERE / "result.json"
    diagnosis_data, result_data = core.load(diagnosis), core.load(result)
    if diagnosis_data["result_sha256"] != core.sha(result) or result_data["receipts_sha256"] != core.sha(received):
        raise ValueError("以前の監査の診断と二票が結び付かない")
    old = core.load(reference)["selected"]
    if len(old) != 376:
        raise ValueError("前回の固定行がそろわない")
    history = sorted(path for index in range(50, 61)
                     for path in core.CORPUS.glob(f"reference-v{index}-*/display/selection.json"))
    prior_trials = {identity(row) for path in history for row in core.load(path)["selected"]}
    samples = choose(old, prior_trials, diagnosis_data)
    rows = [r for r, _ in samples]
    baseline = {}
    for name, packet in core.load(archive)["packs"].items():
        (label, part), = packet["mapping"].items()
        baseline[identity(old[part["entry"]])] = name, label, part["partitions"]
    display = pilot.OUT / "display"
    display.mkdir(parents=True)
    table, selection, population = (display / f"{name}.json" for name in ("method", "selection", "population"))
    initial = core.PLAN
    core.save_once(table, core.encoded(render.plan(core.load(initial))))
    core.save_once(population, core.encoded({"inputs": {}}))
    core.save_once(selection, core.encoded({"population_lock_sha256": core.sha(population), "selected": rows}))
    original = core.OUT, core.PLAN, core.LOCK
    core.OUT, core.PLAN, core.LOCK = display, table, population
    manifest = display / "delivery/packages.json"
    try:
        with render.active():
            audit.package(core.sha(selection))
            audit.verify_delivery(core.sha(manifest))
            delivered = core.load(manifest)["packs"]
            render.verify(rows, delivered)
    finally:
        core.OUT, core.PLAN, core.LOCK = original
    jobs, mapping = {}, {}
    for name, packet in delivered.items():
        (_, item), = packet["mapping"].items()
        row, category = samples[item["entry"]]
        old_name, label, parts = baseline[identity(row)]
        mapping[name] = {**item, "category": category, "baseline_packet": old_name, "baseline_label": label,
                         "baseline_partitions": parts}
        jobs[name + "/new"] = {"cards": str(display / "delivery/cards" / name), "request": packet["request"]}
    files = (Path(__file__), Path(render.__file__), HERE / "protocol.md", BASE, reference, archive, received, diagnosis,
             result, table, population, selection, manifest, render.typeface, initial,
             *(Path(stage.__file__) for stage in (render.orientation, render.instructions, render.short, render.horizontal)),
             *history)
    pins = {**core.load(core.LOCK)["inputs"], **{str(f): core.sha(f) for f in files}}
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
