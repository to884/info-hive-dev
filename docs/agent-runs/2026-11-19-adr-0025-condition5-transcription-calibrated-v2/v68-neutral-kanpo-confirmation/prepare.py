"""中立化した固定画像の二票で既存の官報候補を確かめる。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BRIDGE = HERE.parent / "v67-neutral-transcription-pilot/prepare.py"
sys.path.insert(0, str(BRIDGE.parent))
spec = importlib.util.spec_from_file_location("neutral_kanpo_preparation", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
core, pilot = bridge.core, bridge.pilot
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v68-neutral-kanpo-confirmation"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"


def snapshot():
    core.verify_methods()
    method = core.PLAN
    before = core.CORPUS / "reference-v62-combined-reading-pilot/display/selection.json"
    candidates = {144, 164, 190, 201}
    rows = sorted((r for r in core.load(before)["selected"]
                   if r["key"] == "kanpo1828-p3-p0001" and r["line_index"] in candidates), key=lambda r: r["line_index"])
    if {r["line_index"] for r in rows} != candidates:
        raise ValueError("固定した官報の候補と対照の4行が揃わない")
    display = pilot.OUT / "display"
    path = display / "new"
    batches, pins = bridge.build(path, rows, bridge.render.plan(core.load(method)), True)
    selection = display / "selection.json"
    core.save_once(selection, core.encoded({"selected": rows}))
    jobs, mapping = {}, {}
    for name, pack in batches.items():
        (item,) = pack["mapping"].values()
        identity = f"line-{rows[item['entry']]['line_index']}"
        mapping[identity] = {"entry": item["entry"], "group": "kanpo-known-development", "arms": {"new": item}}
        jobs[identity + "/new"] = {"cards": str(path / "delivery/cards" / name), "request": pack["request"]}
    files = (Path(__file__), BRIDGE, Path(bridge.neutral.__file__), Path(bridge.grade.__file__), bridge.BASE,
             Path(bridge.render.__file__), Path(bridge.render.orientation.__file__),
             Path(bridge.render.instructions.__file__), Path(bridge.render.short.__file__),
             Path(bridge.render.horizontal.__file__), HERE / "protocol.md", method, before, selection, *pins)
    pilot.SAMPLES = rows
    return {"jobs": jobs, "mapping": mapping, "files": core.load(core.LOCK)["inputs"] |
            {str(p): core.sha(p) for p in files}}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        bridge.grade.main(core, pilot)
    else:
        pilot.snapshot = snapshot
        pilot.main()
