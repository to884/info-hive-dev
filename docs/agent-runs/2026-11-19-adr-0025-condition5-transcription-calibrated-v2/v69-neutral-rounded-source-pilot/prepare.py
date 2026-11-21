"""固定画像で候補を選んだ小点の二票と出典比較を準備する。"""

import importlib.util
from pathlib import Path
import sys

import verify

HERE = Path(__file__).resolve().parent
BRIDGE = HERE.parent / "v67-neutral-transcription-pilot/prepare.py"
sys.path.insert(0, str(BRIDGE.parent))
spec = importlib.util.spec_from_file_location("neutral_rounded_mark", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
core, pilot = bridge.core, bridge.pilot
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v69-neutral-rounded-source-pilot"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
MARKS = HERE.parent / "v61-vertical-point-command-pilot/run.py"
branches = core.previous.module("vertical_point_component_recheck", MARKS)
CASE = "kanpo1828-p1-p0001", 120
CONTROLS = {("kanpo1828-p1-p0001", 117), ("defense-p0089", 88)}


def snapshot():
    core.verify_methods()
    before_method = core.PLAN
    method = core.load(before_method)
    old_snapshot = core.CORPUS / "reference-v62-combined-reading-pilot/display/selection.json"
    rows = {bridge.key(r): r for r in core.load(old_snapshot)["selected"] if bridge.key(r) in CONTROLS}
    previous_labels = core.methods()[2] / "public.json"
    _, flags = core.baseline.take_public_rows()
    records = core.load(previous_labels)
    match = {}
    for domain, pool in core.baseline.populations(records, flags).items():
        for row in pool:
            if bridge.key(row) != CASE:
                continue
            targets = {k: row[k] for k in ("cohort", "text", "known", "error")}
            match.setdefault("body", {k: v for k, v in row.items() if k not in targets})
            match.setdefault("targets", {})[domain] = targets
    if not match or len(rows) != len(CONTROLS):
        raise ValueError("小点の候補と対照の固定資料が足りない")
    texts = {t["text"] for t in match["targets"].values() if t["known"]}
    if len(texts) > 1:
        raise ValueError("画像の参照本文が同じ候補で矛盾する")
    rows[CASE] = {**match["body"], "targets": match["targets"], "effective": next(iter(texts), "?")}
    items = [rows[k] for k in sorted(rows)]
    display = pilot.OUT / "display"
    fixed = display / "new"
    packets, files = bridge.build(fixed, items, bridge.render.plan(method), True)
    selection = display / "selection.json"
    core.save_once(selection, core.encoded({"selected": items}))
    links, tasks = {}, {}
    for name, packet in packets.items():
        (link,) = packet["mapping"].values()
        row = items[link["entry"]]
        key = f"line-{row['line_index']}"
        group = "new-point" if bridge.key(row) == CASE else "old-control"
        links[key] = {"entry": link["entry"], "group": group, "arms": {"new": link}}
        tasks[key + "/new"] = {"cards": str(fixed / "delivery/cards" / name), "request": packet["request"]}
    requirements = (Path(__file__), Path(verify.__file__), BRIDGE, Path(bridge.neutral.__file__),
                    Path(bridge.grade.__file__), bridge.BASE, Path(bridge.render.__file__),
                    Path(bridge.render.orientation.__file__), Path(bridge.render.instructions.__file__),
                    Path(bridge.render.short.__file__), Path(bridge.render.horizontal.__file__), MARKS,
                    MARKS.parent / "result.json", HERE / "protocol.md", old_snapshot, before_method, previous_labels,
                    selection, *files)
    pilot.SAMPLES = items
    return {"jobs": tasks, "mapping": links, "files": core.load(core.LOCK)["inputs"] |
            {str(p): core.sha(p) for p in requirements}}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    if action == "compare":
        bridge.grade.main(core, pilot)
    elif action == "source":
        verify.collect(core, pilot.OUT, HERE, pilot.LOCK, branches, (MARKS, Path(verify.__file__), Path(__file__)))
    else:
        pilot.snapshot = snapshot
        pilot.main()
