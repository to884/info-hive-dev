"""次の監査用の表示を、既存の開発行で確かめる。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v24-physical-transcription-pilot/run.py"
PLANNED = HERE.parent / "v47-reference-audit/run.py"
spec = importlib.util.spec_from_file_location("combined_view_and_transcription", PREVIOUS)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v49-combined-frame-bullets-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
audit = pilot.audit
trial = audit.module("planned_v47_presentation", PLANNED)


def plan():
    initial = audit.load(HERE.parent / "v27-reference-audit/method.json")
    return {"guides": {**initial["guides"], "x": initial["guides"]["x"] + trial.bullet_stage.old.GUIDE},
            "ruler": initial["ruler"]}


def snapshot():
    ancestors = (HERE.parent / "v45-edge-measurement-pilot", HERE.parent / "v46-paragraph-circle-pilot")
    rows, groups, pins = [], [], {}
    for study in ancestors:
        earlier = audit.load(study / "lock.json")
        actual = earlier["mapping"]
        folder = pilot.OUT.with_name("reference-" + study.name)
        dataset = folder / "display/selection.json"
        trials = audit.load(dataset)["selected"]
        if any(audit.sha(Path(p)) != h for p, h in earlier["files"].items()):
            raise ValueError("以前の開発比較の入力が異なる")
        for item in actual.values():
            row = trials[item["entry"]]
            if row["effective"] is None:
                raise ValueError("比較対象の既存正解がない")
            rows.append(row)
            groups.append(item["category"])
        pins.update({str(f): audit.sha(f) for f in (study / "lock.json", dataset)})
    if len({(r["key"], r["line_index"]) for r in rows}) != len(rows):
        raise ValueError("表示の確認対象が重複")
    display = pilot.OUT / "display"
    display.mkdir(parents=True)
    table, selection, lock = display / "method.json", display / "selection.json", display / "population.json"
    audit.save_once(table, audit.encoded(plan()))
    audit.save_once(lock, audit.encoded({"inputs": {}}))
    audit.save_once(selection, audit.encoded({"population_lock_sha256": audit.sha(lock), "selected": rows}))
    trial.core.OUT, trial.core.PLAN, trial.core.LOCK = display, table, lock
    trial.package(audit.sha(selection))
    payload = display / "delivery/packages.json"
    jobs, mapping = {}, {}
    for name, batch in audit.load(payload)["packs"].items():
        (ident, item), = batch["mapping"].items()
        tag = f"case-{len(mapping):02d}"
        mapping[tag] = {**item, "category": groups[item["entry"]]}
        jobs[tag + "/new"] = {"cards": str(display / "delivery/cards" / name), "request": batch["request"]}
    pins.update({str(p): audit.sha(p) for p in (Path(__file__), PREVIOUS, PLANNED, HERE / "protocol.md",
                                                trial.edge_file, trial.bullet_file, table, selection, payload,
                                                HERE.parent / "v22-list-mark-pilot/recover.py")})
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": pins}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
